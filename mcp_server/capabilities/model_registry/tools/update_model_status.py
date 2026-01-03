"""
Update Model Status Tool

モデルステータス更新ツール
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def update_model_status(
    model_s3_uri: str,
    status: str,
) -> Dict[str, Any]:
    """
    モデルのステータスを更新

    Args:
        model_s3_uri: モデルのS3 URI (.pkl)
        status: 新しいステータス (registered, staging, production, archived)

    Returns:
        更新結果辞書
    """
    logger.info(f"Updating model status to: {status}")

    # ステータスのバリデーション
    valid_statuses = ["registered", "staging", "production", "archived"]
    if status not in valid_statuses:
        raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")

    # S3 URIのバリデーション
    if not model_s3_uri.startswith("s3://"):
        raise ValueError("Invalid S3 URI: must start with 's3://'")

    model_parts = model_s3_uri[5:].split("/", 1)
    if len(model_parts) != 2:
        raise ValueError("Invalid S3 URI format: s3://bucket/key required")

    # S3クライアント
    s3_client = boto3.client("s3")

    model_bucket, model_key = model_parts

    # レジストリメタデータの取得
    metadata_key = f"{model_key.rsplit('.', 1)[0]}_registry.json"

    try:
        metadata_response = s3_client.get_object(Bucket=model_bucket, Key=metadata_key)
        metadata_content = metadata_response["Body"].read()
        registry_metadata = json.loads(metadata_content.decode("utf-8"))
        logger.info("Retrieved registry metadata")

    except ClientError as e:
        logger.error(f"Failed to retrieve registry metadata: {e}")
        raise ValueError(f"Registry metadata not found for model: {model_s3_uri}")

    # ステータス履歴の記録
    if "status_history" not in registry_metadata:
        registry_metadata["status_history"] = []

    old_status = registry_metadata.get("status")
    registry_metadata["status_history"].append(
        {
            "from_status": old_status,
            "to_status": status,
            "updated_at": datetime.utcnow().isoformat(),
        }
    )

    # ステータスの更新
    registry_metadata["status"] = status
    registry_metadata["last_updated"] = datetime.utcnow().isoformat()

    # メタデータの保存
    try:
        metadata_json = json.dumps(registry_metadata, indent=2)
        s3_client.put_object(
            Bucket=model_bucket, Key=metadata_key, Body=metadata_json.encode("utf-8")
        )
        logger.info(f"Updated model status from {old_status} to {status}")

    except ClientError as e:
        logger.error(f"Failed to save updated metadata: {e}")
        raise ValueError(f"Failed to update model status: {e}")

    return {
        "status": "success",
        "message": f"Model status updated from {old_status} to {status}",
        "update_info": {
            "model_s3_uri": model_s3_uri,
            "old_status": old_status,
            "new_status": status,
            "updated_at": registry_metadata["last_updated"],
        },
    }
