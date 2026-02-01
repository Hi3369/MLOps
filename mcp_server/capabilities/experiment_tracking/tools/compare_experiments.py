"""
Compare Experiments Tool

実験比較ツール
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def compare_experiments(
    experiment_ids: List[str],
    metric_names: Optional[List[str]] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "descending",
) -> Dict[str, Any]:
    """
    複数の実験を比較する

    Args:
        experiment_ids: 比較する実験IDのリスト（2つ以上）
        metric_names: 比較するメトリクス名のリスト（省略時は全メトリクス）
        sort_by: ソート基準のメトリクス名
        sort_order: ソート順序（ascending/descending）

    Returns:
        実験比較結果辞書
    """
    logger.info(f"Comparing experiments: {experiment_ids}")

    # パラメータ検証
    if not experiment_ids:
        raise ValueError("experiment_ids must not be empty")

    if not isinstance(experiment_ids, list):
        raise ValueError("experiment_ids must be a list")

    if len(experiment_ids) < 2:
        raise ValueError("At least 2 experiment_ids are required for comparison")

    if len(experiment_ids) > 10:
        raise ValueError("Maximum 10 experiments can be compared at once")

    if sort_order not in ["ascending", "descending"]:
        raise ValueError("sort_order must be 'ascending' or 'descending'")

    # 重複チェック
    if len(experiment_ids) != len(set(experiment_ids)):
        raise ValueError("experiment_ids must not contain duplicates")

    try:
        env = os.environ.get("MLOPS_ENV", "development")
        timestamp = datetime.now(timezone.utc).isoformat()
        comparison_id = str(uuid4())[:8]

        # 開発/テスト環境ではモック
        if env in ["development", "test"]:
            return _mock_compare_experiments(
                experiment_ids=experiment_ids,
                metric_names=metric_names,
                sort_by=sort_by,
                sort_order=sort_order,
                comparison_id=comparison_id,
                timestamp=timestamp,
            )

        # 本番環境: S3からデータ取得して比較
        return _real_compare_experiments(
            experiment_ids=experiment_ids,
            metric_names=metric_names,
            sort_by=sort_by,
            sort_order=sort_order,
            comparison_id=comparison_id,
            timestamp=timestamp,
        )

    except ClientError as e:
        logger.error(f"AWS error comparing experiments: {e}")
        raise ValueError(f"Failed to compare experiments: {e}")
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Failed to compare experiments: {e}")
        raise ValueError(f"Failed to compare experiments: {e}")


def _generate_mock_experiment_data(
    experiment_id: str,
    metric_names: Optional[List[str]],
) -> Dict[str, Any]:
    """モック実験データを生成"""
    import hashlib

    # 実験IDからシード値を生成（再現性のため）
    seed = int(hashlib.md5(experiment_id.encode()).hexdigest()[:8], 16)

    # デフォルトメトリクス
    default_metrics = ["accuracy", "f1_score", "precision", "recall", "loss"]
    target_metrics = metric_names if metric_names else default_metrics

    metrics = {}
    for i, name in enumerate(target_metrics):
        # シード値ベースで擬似的な値を生成
        base = ((seed + i * 7) % 100) / 100.0
        if name == "loss":
            metrics[name] = round(1.0 - base * 0.8, 4)
        else:
            metrics[name] = round(0.5 + base * 0.5, 4)

    return {
        "experiment_id": experiment_id,
        "status": "completed",
        "metrics": metrics,
        "parameters": {
            "learning_rate": round(0.001 + (seed % 10) * 0.001, 4),
            "batch_size": 32 * (1 + seed % 4),
            "epochs": 10 + seed % 90,
        },
    }


def _compute_comparison_summary(
    experiments_data: List[Dict[str, Any]],
    sort_by: Optional[str],
    sort_order: str,
) -> Dict[str, Any]:
    """比較サマリーを計算"""
    if not experiments_data:
        return {}

    # 全メトリクス名を収集
    all_metrics = set()
    for exp in experiments_data:
        all_metrics.update(exp.get("metrics", {}).keys())

    # メトリクスごとのベスト実験を特定
    best_by_metric = {}
    for metric_name in all_metrics:
        values = []
        for exp in experiments_data:
            val = exp.get("metrics", {}).get(metric_name)
            if val is not None:
                values.append((exp["experiment_id"], val))

        if values:
            # lossは低いほうが良い、その他は高いほうが良い
            is_lower_better = "loss" in metric_name.lower()
            best = (
                min(values, key=lambda x: x[1])
                if is_lower_better
                else max(values, key=lambda x: x[1])
            )
            best_by_metric[metric_name] = {
                "best_experiment_id": best[0],
                "best_value": best[1],
                "is_lower_better": is_lower_better,
            }

    # ソート
    sorted_experiments = list(experiments_data)
    if sort_by and any(sort_by in exp.get("metrics", {}) for exp in experiments_data):
        reverse = sort_order == "descending"
        sorted_experiments.sort(
            key=lambda x: x.get("metrics", {}).get(sort_by, 0),
            reverse=reverse,
        )

    ranking = [
        {
            "rank": i + 1,
            "experiment_id": exp["experiment_id"],
            "sort_metric_value": exp.get("metrics", {}).get(sort_by) if sort_by else None,
        }
        for i, exp in enumerate(sorted_experiments)
    ]

    return {
        "total_experiments": len(experiments_data),
        "metrics_compared": list(all_metrics),
        "best_by_metric": best_by_metric,
        "ranking": ranking,
    }


def _mock_compare_experiments(
    experiment_ids: List[str],
    metric_names: Optional[List[str]],
    sort_by: Optional[str],
    sort_order: str,
    comparison_id: str,
    timestamp: str,
) -> Dict[str, Any]:
    """モック実験比較（開発・テスト用）"""
    logger.info("Using mock experiment comparison")

    # モック実験データを生成
    experiments_data = [
        _generate_mock_experiment_data(exp_id, metric_names) for exp_id in experiment_ids
    ]

    # 比較サマリー
    summary = _compute_comparison_summary(experiments_data, sort_by, sort_order)

    return {
        "status": "success",
        "message": f"Compared {len(experiment_ids)} experiments",
        "comparison_info": {
            "comparison_id": f"cmp-{comparison_id}",
            "experiments": experiments_data,
            "summary": summary,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "compared_at": timestamp,
            "mock": True,
        },
    }


def _real_compare_experiments(
    experiment_ids: List[str],
    metric_names: Optional[List[str]],
    sort_by: Optional[str],
    sort_order: str,
    comparison_id: str,
    timestamp: str,
) -> Dict[str, Any]:
    """本番実験比較（S3からデータ取得）"""
    import json

    s3_client = boto3.client("s3")
    bucket = os.environ.get("MLOPS_EXPERIMENT_BUCKET", "mlops-experiments")

    experiments_data = []
    for exp_id in experiment_ids:
        try:
            # メタデータ取得
            paginator = s3_client.get_paginator("list_objects_v2")
            metrics_prefix = f"experiments/{exp_id}/metrics/"
            pages = paginator.paginate(Bucket=bucket, Prefix=metrics_prefix)

            aggregated_metrics = {}
            parameters = {}

            for page in pages:
                for obj in page.get("Contents", []):
                    response = s3_client.get_object(Bucket=bucket, Key=obj["Key"])
                    data = json.loads(response["Body"].read().decode("utf-8"))
                    if "metrics" in data:
                        aggregated_metrics.update(data["metrics"])
                    if "parameters" in data:
                        parameters.update(data["parameters"])

            # メトリクスフィルタ
            if metric_names:
                aggregated_metrics = {
                    k: v for k, v in aggregated_metrics.items() if k in metric_names
                }

            experiments_data.append(
                {
                    "experiment_id": exp_id,
                    "status": "completed",
                    "metrics": aggregated_metrics,
                    "parameters": parameters,
                }
            )

        except ClientError as e:
            logger.warning(f"Failed to fetch experiment {exp_id}: {e}")
            experiments_data.append(
                {
                    "experiment_id": exp_id,
                    "status": "not_found",
                    "metrics": {},
                    "parameters": {},
                }
            )

    # 比較サマリー
    summary = _compute_comparison_summary(experiments_data, sort_by, sort_order)

    # 比較結果をS3に保存
    comparison_data = {
        "comparison_id": f"cmp-{comparison_id}",
        "experiments": experiments_data,
        "summary": summary,
        "compared_at": timestamp,
    }

    s3_client.put_object(
        Bucket=bucket,
        Key=f"comparisons/{comparison_id}.json",
        Body=json.dumps(comparison_data),
        ContentType="application/json",
    )

    return {
        "status": "success",
        "message": f"Compared {len(experiment_ids)} experiments",
        "comparison_info": {
            "comparison_id": f"cmp-{comparison_id}",
            "experiments": experiments_data,
            "summary": summary,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "s3_uri": f"s3://{bucket}/comparisons/{comparison_id}.json",
            "compared_at": timestamp,
        },
    }
