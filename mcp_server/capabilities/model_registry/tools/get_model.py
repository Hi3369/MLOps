"""
Get Model Tool

モデル取得ツール
"""

import json
import logging
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def get_model(
    model_s3_uri: str,
) -> Dict[str, Any]:
    """
    モデル情報を取得

    Args:
        model_s3_uri: モデルのS3 URI (.pkl)

    Returns:
        モデル情報辞書
    """
    logger.info(f"Getting model information from {model_s3_uri}")

    # S3 URIのバリデーション
    if not model_s3_uri.startswith("s3://"):
        raise ValueError("Invalid S3 URI: must start with 's3://'")

    model_parts = model_s3_uri[5:].split("/", 1)
    if len(model_parts) != 2:
        raise ValueError("Invalid S3 URI format: s3://bucket/key required")

    # S3クライアント
    s3_client = boto3.client("s3")

    model_bucket, model_key = model_parts

    # モデルの存在確認
    try:
        model_response = s3_client.head_object(Bucket=model_bucket, Key=model_key)
        model_size = model_response["ContentLength"]
        model_last_modified = model_response["LastModified"].isoformat()
        logger.info(f"Model exists: {model_size} bytes")

    except ClientError as e:
        logger.error(f"S3 access error for model: {e}")
        raise ValueError(f"Model not found at S3 URI: {model_s3_uri}")

    # レジストリメタデータの取得
    metadata_key = f"{model_key.rsplit('.', 1)[0]}_registry.json"
    registry_metadata = None

    try:
        metadata_response = s3_client.get_object(Bucket=model_bucket, Key=metadata_key)
        metadata_content = metadata_response["Body"].read()
        registry_metadata = json.loads(metadata_content.decode("utf-8"))
        logger.info("Found registry metadata")

    except ClientError as e:
        logger.warning(f"Registry metadata not found: {e}")
        # メタデータがない場合はデフォルト値
        registry_metadata = {
            "model_name": "unknown",
            "model_version": "unknown",
            "status": "unregistered",
        }

    # モデル情報の統合
    model_info = {
        "model_s3_uri": model_s3_uri,
        "model_size_bytes": model_size,
        "model_last_modified": model_last_modified,
        "registry_metadata": registry_metadata,
    }

    logger.info("Model information retrieved successfully")

    return {
        "status": "success",
        "message": "Model information retrieved successfully",
        "model_info": model_info,
    }
