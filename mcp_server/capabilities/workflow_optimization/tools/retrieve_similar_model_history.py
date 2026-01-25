"""
Retrieve Similar Model History Tool

類似モデルの履歴取得ツール
"""

import logging
from typing import Any, Dict, List

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def retrieve_similar_model_history(
    model_type: str,
    dataset_size: int = None,
    limit: int = 10,
) -> Dict[str, Any]:
    """
    類似モデルの履歴を取得

    Args:
        model_type: モデルタイプ（algorithm名）
        dataset_size: データセットサイズ（オプション）
        limit: 取得する履歴の最大数

    Returns:
        類似モデル履歴辞書
    """
    logger.info(f"Retrieving similar model history: type={model_type}")

    # パラメータ検証
    if not model_type:
        raise ValueError("model_type must not be empty")

    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100")

    try:
        # DynamoDBクライアント
        dynamodb = boto3.resource("dynamodb")
        table_name = "mlops-model-history"

        # テーブルが存在するか確認（開発環境では作成）
        try:
            table = dynamodb.Table(table_name)
            table.load()
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                logger.warning(f"Table {table_name} not found, returning mock data")
                return _get_mock_history(model_type, dataset_size, limit)
            raise

        # クエリ実行
        response = table.query(
            IndexName="ModelTypeIndex",
            KeyConditionExpression="model_type = :model_type",
            ExpressionAttributeValues={":model_type": model_type},
            Limit=limit,
            ScanIndexForward=False,  # 最新順
        )

        items = response.get("Items", [])

        # データセットサイズでフィルタリング
        if dataset_size is not None:
            items = _filter_by_dataset_size(items, dataset_size)

        # 統計情報を計算
        statistics = _calculate_statistics(items)

        logger.info(f"Retrieved {len(items)} similar model history records")

        return {
            "status": "success",
            "message": f"Retrieved {len(items)} similar model history records",
            "history": {
                "model_type": model_type,
                "total_records": len(items),
                "records": items[:limit],
                "statistics": statistics,
            },
        }

    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        # エラー時はモックデータを返す
        logger.warning("Returning mock data due to DynamoDB error")
        return _get_mock_history(model_type, dataset_size, limit)

    except Exception as e:
        logger.error(f"Similar model history retrieval error: {e}")
        raise ValueError(f"Failed to retrieve similar model history: {e}")


def _filter_by_dataset_size(items: List[Dict], target_size: int) -> List[Dict]:
    """データセットサイズでフィルタリング（±50%範囲）"""
    min_size = target_size * 0.5
    max_size = target_size * 1.5

    filtered = []
    for item in items:
        size = item.get("dataset_size", 0)
        if min_size <= size <= max_size:
            filtered.append(item)

    return filtered if filtered else items  # フィルタ結果が空なら全件返す


def _calculate_statistics(items: List[Dict]) -> Dict[str, Any]:
    """統計情報を計算"""
    if not items:
        return {
            "avg_training_time_minutes": 0,
            "avg_accuracy": 0,
            "avg_cost_usd": 0,
            "most_common_hyperparameters": {},
        }

    # トレーニング時間の平均
    training_times = [item.get("training_time_minutes", 0) for item in items]
    avg_training_time = sum(training_times) / len(training_times) if training_times else 0

    # 精度の平均
    accuracies = [item.get("accuracy", 0) for item in items]
    avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0

    # コストの平均
    costs = [item.get("cost_usd", 0) for item in items]
    avg_cost = sum(costs) / len(costs) if costs else 0

    # 最頻ハイパーパラメータ
    hyperparameter_counts = {}
    for item in items:
        hyperparams = item.get("hyperparameters", {})
        for key, value in hyperparams.items():
            if key not in hyperparameter_counts:
                hyperparameter_counts[key] = {}
            value_str = str(value)
            hyperparameter_counts[key][value_str] = hyperparameter_counts[key].get(value_str, 0) + 1

    most_common_hyperparameters = {}
    for key, value_counts in hyperparameter_counts.items():
        if value_counts:
            most_common_value = max(value_counts, key=value_counts.get)
            most_common_hyperparameters[key] = most_common_value

    return {
        "avg_training_time_minutes": round(avg_training_time, 2),
        "avg_accuracy": round(avg_accuracy, 4),
        "avg_cost_usd": round(avg_cost, 2),
        "most_common_hyperparameters": most_common_hyperparameters,
        "best_performing_model": _find_best_model(items),
    }


def _find_best_model(items: List[Dict]) -> Dict[str, Any]:
    """最高性能のモデルを見つける"""
    if not items:
        return {}

    best_model = max(items, key=lambda x: x.get("accuracy", 0))

    return {
        "model_id": best_model.get("model_id", "unknown"),
        "accuracy": best_model.get("accuracy", 0),
        "training_time_minutes": best_model.get("training_time_minutes", 0),
        "hyperparameters": best_model.get("hyperparameters", {}),
    }


def _get_mock_history(model_type: str, dataset_size: int, limit: int) -> Dict[str, Any]:
    """モックデータを返す（開発・テスト用）"""
    logger.info("Returning mock similar model history")

    # モックデータの生成
    mock_records = []

    # model_typeに応じたモックデータ
    base_accuracy = {
        "random_forest": 0.85,
        "xgboost": 0.88,
        "neural_network": 0.90,
        "logistic_regression": 0.80,
    }.get(model_type, 0.85)

    for i in range(min(limit, 5)):
        mock_records.append(
            {
                "model_id": f"mock-{model_type}-{i + 1}",
                "model_type": model_type,
                "dataset_size": dataset_size or 10000 * (i + 1),
                "training_time_minutes": 10 + i * 5,
                "accuracy": base_accuracy + (i * 0.01),
                "cost_usd": 2.5 + i * 0.5,
                "hyperparameters": {
                    "n_estimators": 100 + i * 50,
                    "max_depth": 10 + i * 5,
                },
                "created_at": f"2025-01-{i + 1:02d}T10:00:00Z",
            }
        )

    statistics = _calculate_statistics(mock_records)

    return {
        "status": "success",
        "message": f"Retrieved {len(mock_records)} similar model history records (mock data)",
        "history": {
            "model_type": model_type,
            "total_records": len(mock_records),
            "records": mock_records,
            "statistics": statistics,
            "is_mock_data": True,
        },
    }
