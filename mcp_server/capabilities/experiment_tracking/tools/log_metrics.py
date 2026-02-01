"""
Log Metrics Tool

実験メトリクス記録ツール
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def log_metrics(
    experiment_id: str,
    metrics: Dict[str, float],
    run_name: Optional[str] = None,
    step: Optional[int] = None,
    epoch: Optional[int] = None,
) -> Dict[str, Any]:
    """
    実験にメトリクスを記録する

    Args:
        experiment_id: 実験ID
        metrics: 記録するメトリクス辞書（キー: メトリクス名、値: 数値）
        run_name: 実行名（省略時は自動生成）
        step: ステップ番号
        epoch: エポック番号

    Returns:
        メトリクス記録結果辞書
    """
    logger.info(f"Logging metrics for experiment: {experiment_id}")

    # パラメータ検証
    if not experiment_id:
        raise ValueError("experiment_id must not be empty")

    if not metrics:
        raise ValueError("metrics must not be empty")

    if not isinstance(metrics, dict):
        raise ValueError("metrics must be a dictionary")

    # メトリクス値の型検証
    for key, value in metrics.items():
        if not isinstance(key, str):
            raise ValueError(f"Metric key must be a string, got {type(key)}")
        if not isinstance(value, (int, float)):
            raise ValueError(
                f"Metric value for '{key}' must be numeric (int or float), " f"got {type(value)}"
            )

    if step is not None and step < 0:
        raise ValueError("step must be a non-negative integer")

    if epoch is not None and epoch < 0:
        raise ValueError("epoch must be a non-negative integer")

    try:
        env = os.environ.get("MLOPS_ENV", "development")
        timestamp = datetime.now(timezone.utc).isoformat()
        log_id = str(uuid4())[:8]

        if run_name is None:
            run_name = f"run-{log_id}"

        # メトリクスサマリーを計算
        summary = _compute_metrics_summary(metrics)

        # 開発/テスト環境ではモック
        if env in ["development", "test"]:
            return _mock_log_metrics(
                experiment_id=experiment_id,
                metrics=metrics,
                run_name=run_name,
                step=step,
                epoch=epoch,
                log_id=log_id,
                timestamp=timestamp,
                summary=summary,
            )

        # 本番環境: S3 + CloudWatch
        return _real_log_metrics(
            experiment_id=experiment_id,
            metrics=metrics,
            run_name=run_name,
            step=step,
            epoch=epoch,
            log_id=log_id,
            timestamp=timestamp,
            summary=summary,
        )

    except ClientError as e:
        logger.error(f"AWS error logging metrics: {e}")
        raise ValueError(f"Failed to log metrics: {e}")
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Failed to log metrics: {e}")
        raise ValueError(f"Failed to log metrics: {e}")


def _compute_metrics_summary(metrics: Dict[str, float]) -> Dict[str, Any]:
    """メトリクスサマリーを計算"""
    values = list(metrics.values())
    return {
        "metric_count": len(metrics),
        "metric_names": list(metrics.keys()),
        "min_value": min(values),
        "max_value": max(values),
        "mean_value": sum(values) / len(values),
    }


def _mock_log_metrics(
    experiment_id: str,
    metrics: Dict[str, float],
    run_name: str,
    step: Optional[int],
    epoch: Optional[int],
    log_id: str,
    timestamp: str,
    summary: Dict[str, Any],
) -> Dict[str, Any]:
    """モックメトリクス記録（開発・テスト用）"""
    logger.info("Using mock metrics logging")

    return {
        "status": "success",
        "message": f"Metrics logged for experiment: {experiment_id}",
        "metrics_info": {
            "log_id": f"metric-{log_id}",
            "experiment_id": experiment_id,
            "run_name": run_name,
            "metrics": metrics,
            "step": step,
            "epoch": epoch,
            "summary": summary,
            "logged_at": timestamp,
            "mock": True,
        },
    }


def _real_log_metrics(
    experiment_id: str,
    metrics: Dict[str, float],
    run_name: str,
    step: Optional[int],
    epoch: Optional[int],
    log_id: str,
    timestamp: str,
    summary: Dict[str, Any],
) -> Dict[str, Any]:
    """本番メトリクス記録（S3 + CloudWatch）"""
    import json

    s3_client = boto3.client("s3")
    bucket = os.environ.get("MLOPS_EXPERIMENT_BUCKET", "mlops-experiments")

    # メトリクスデータ
    metrics_data = {
        "log_id": f"metric-{log_id}",
        "experiment_id": experiment_id,
        "run_name": run_name,
        "metrics": metrics,
        "step": step,
        "epoch": epoch,
        "summary": summary,
        "logged_at": timestamp,
    }

    # S3に保存
    s3_key = f"experiments/{experiment_id}/metrics/{run_name}/{log_id}.json"
    s3_client.put_object(
        Bucket=bucket,
        Key=s3_key,
        Body=json.dumps(metrics_data),
        ContentType="application/json",
    )

    # CloudWatchにメトリクスを送信
    cw_client = boto3.client("cloudwatch")
    metric_data = []
    for metric_name, metric_value in metrics.items():
        metric_data.append(
            {
                "MetricName": f"{experiment_id}/{metric_name}",
                "Value": metric_value,
                "Unit": "None",
                "Dimensions": [
                    {"Name": "ExperimentId", "Value": experiment_id},
                    {"Name": "RunName", "Value": run_name},
                ],
            }
        )

    if metric_data:
        cw_client.put_metric_data(
            Namespace="MLOps/Experiments",
            MetricData=metric_data,
        )

    return {
        "status": "success",
        "message": f"Metrics logged for experiment: {experiment_id}",
        "metrics_info": {
            "log_id": f"metric-{log_id}",
            "experiment_id": experiment_id,
            "run_name": run_name,
            "metrics": metrics,
            "step": step,
            "epoch": epoch,
            "summary": summary,
            "s3_uri": f"s3://{bucket}/{s3_key}",
            "logged_at": timestamp,
        },
    }
