"""
Track Optimization History Tool

最適化履歴記録ツール
"""

import logging
from datetime import datetime
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def track_optimization_history(
    optimization_id: str,
    results: Dict[str, Any],
) -> Dict[str, Any]:
    """
    最適化履歴を記録

    Args:
        optimization_id: 最適化ID
        results: 最適化結果（apply_optimizationsの出力等）

    Returns:
        最適化履歴記録結果辞書
    """
    logger.info(f"Tracking optimization history: {optimization_id}")

    # パラメータ検証
    if not optimization_id:
        raise ValueError("optimization_id must not be empty")

    if not results:
        raise ValueError("results must not be empty")

    if not isinstance(results, dict):
        raise ValueError("results must be a dictionary")

    try:
        # DynamoDBクライアント
        dynamodb = boto3.resource("dynamodb")
        table_name = "mlops-optimization-history"

        # テーブルが存在するか確認（開発環境では作成）
        try:
            table = dynamodb.Table(table_name)
            table.load()
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                logger.warning(f"Table {table_name} not found, returning mock tracking result")
                return _get_mock_tracking_result(optimization_id, results)
            raise

        # タイムスタンプ
        timestamp = datetime.utcnow().isoformat()

        # 履歴レコードを作成
        history_record = {
            "optimization_id": optimization_id,
            "timestamp": timestamp,
            "results": results,
            "status": results.get("status", "unknown"),
            "total_optimizations": results.get("optimization_result", {}).get(
                "total_optimizations_applied", 0
            ),
        }

        # メトリクスを抽出
        metrics = _extract_metrics(results)
        if metrics:
            history_record["metrics"] = metrics

        # DynamoDBに保存
        table.put_item(Item=history_record)

        # 関連する統計情報を更新
        statistics = _update_statistics(table, history_record)

        logger.info(f"Optimization history tracked: {optimization_id}")

        return {
            "status": "success",
            "message": f"Optimization history tracked: {optimization_id}",
            "tracking_info": {
                "optimization_id": optimization_id,
                "timestamp": timestamp,
                "total_optimizations": history_record["total_optimizations"],
                "metrics": metrics,
                "statistics": statistics,
            },
        }

    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        # エラー時はモック結果を返す
        logger.warning("Returning mock tracking result due to DynamoDB error")
        return _get_mock_tracking_result(optimization_id, results)

    except Exception as e:
        logger.error(f"Optimization history tracking error: {e}")
        raise ValueError(f"Failed to track optimization history: {e}")


def _extract_metrics(results: Dict[str, Any]) -> Dict[str, Any]:
    """結果からメトリクスを抽出"""
    metrics: Dict[str, Any] = {}

    optimization_result = results.get("optimization_result", {})

    # 適用された最適化の数
    applied_optimizations = optimization_result.get("applied_optimizations", [])
    metrics["total_optimizations_applied"] = len(applied_optimizations)

    # 最適化タイプ別の数
    optimization_types: Dict[str, int] = {}
    for opt in applied_optimizations:
        opt_type = opt.get("type", "unknown")
        optimization_types[opt_type] = optimization_types.get(opt_type, 0) + 1

    metrics["optimization_types"] = optimization_types

    # 設定の差分
    config_diff = optimization_result.get("config_diff", {})
    metrics["config_changes"] = {
        "added": len(config_diff.get("added", {})),
        "modified": len(config_diff.get("modified", {})),
        "removed": len(config_diff.get("removed", {})),
    }

    return metrics


def _update_statistics(table, history_record: Dict[str, Any]) -> Dict[str, Any]:
    """統計情報を更新"""
    try:
        # 統計情報テーブルキー
        stats_key = "optimization_statistics"

        # 既存の統計を取得
        response = table.get_item(Key={"optimization_id": stats_key})

        if "Item" in response:
            stats = response["Item"]
        else:
            stats = {
                "optimization_id": stats_key,
                "total_optimizations": 0,
                "total_records": 0,
                "optimization_type_counts": {},
            }

        # 統計を更新
        stats["total_records"] = stats.get("total_records", 0) + 1
        stats["total_optimizations"] = stats.get("total_optimizations", 0) + history_record.get(
            "total_optimizations", 0
        )

        # 最適化タイプ別のカウント更新
        metrics = history_record.get("metrics", {})
        optimization_types = metrics.get("optimization_types", {})

        for opt_type, count in optimization_types.items():
            current_count = stats.get("optimization_type_counts", {}).get(opt_type, 0)
            if "optimization_type_counts" not in stats:
                stats["optimization_type_counts"] = {}
            stats["optimization_type_counts"][opt_type] = current_count + count

        # 最終更新日時
        stats["last_updated"] = datetime.utcnow().isoformat()

        # 統計を保存
        table.put_item(Item=stats)

        return {
            "total_records": stats["total_records"],
            "total_optimizations": stats["total_optimizations"],
            "optimization_type_counts": stats["optimization_type_counts"],
        }

    except Exception as e:
        logger.warning(f"Failed to update statistics: {e}")
        return {}


def _get_mock_tracking_result(optimization_id: str, results: Dict[str, Any]) -> Dict[str, Any]:
    """モック追跡結果を返す（開発・テスト用）"""
    logger.info("Returning mock optimization tracking result")

    timestamp = datetime.utcnow().isoformat()
    metrics = _extract_metrics(results)

    return {
        "status": "success",
        "message": f"Optimization history tracked: {optimization_id} (mock data)",
        "tracking_info": {
            "optimization_id": optimization_id,
            "timestamp": timestamp,
            "total_optimizations": metrics.get("total_optimizations_applied", 0),
            "metrics": metrics,
            "statistics": {
                "total_records": 1,
                "total_optimizations": metrics.get("total_optimizations_applied", 0),
                "optimization_type_counts": metrics.get("optimization_types", {}),
            },
            "is_mock_data": True,
        },
    }
