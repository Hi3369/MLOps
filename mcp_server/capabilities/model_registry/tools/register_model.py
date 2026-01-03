"""
Register Model Tool

モデル登録ツール
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def register_model(
    model_s3_uri: str,
    model_name: str,
    model_version: str = None,
    metadata: Dict[str, Any] = None,
    tags: Dict[str, str] = None,
) -> Dict[str, Any]:
    """
    モデルをレジストリに登録

    Args:
        model_s3_uri: モデルのS3 URI (.pkl)
        model_name: モデル名
        model_version: モデルバージョン (省略時は自動生成)
        metadata: モデルメタデータ (algorithm, hyperparameters, metrics等)
        tags: モデルタグ

    Returns:
        登録結果辞書
    """
    logger.info(f"Registering model: {model_name}")

    # S3 URIのバリデーション（先に全てチェック）
    if not model_s3_uri.startswith("s3://"):
        raise ValueError("Invalid S3 URI: must start with 's3://'")

    model_parts = model_s3_uri[5:].split("/", 1)
    if len(model_parts) != 2:
        raise ValueError("Invalid S3 URI format: s3://bucket/key required")

    # デフォルト値の設定
    if model_version is None:
        model_version = datetime.utcnow().strftime("%Y%m%d-%H%M%S")

    if metadata is None:
        metadata = {}

    if tags is None:
        tags = {}

    # S3クライアント
    s3_client = boto3.client("s3")

    # モデルの存在確認
    model_bucket, model_key = model_parts

    try:
        s3_client.head_object(Bucket=model_bucket, Key=model_key)
        logger.info(f"Verified model exists at {model_s3_uri}")

    except ClientError as e:
        logger.error(f"S3 access error for model: {e}")
        raise ValueError(f"Model not found at S3 URI: {model_s3_uri}")

    # レジストリメタデータの作成
    registry_metadata = {
        "model_name": model_name,
        "model_version": model_version,
        "model_s3_uri": model_s3_uri,
        "registered_at": datetime.utcnow().isoformat(),
        "status": "registered",
        "metadata": metadata,
        "tags": tags,
    }

    # メタデータをS3に保存（モデルと同じバケット内）
    metadata_key = f"{model_key.rsplit('.', 1)[0]}_registry.json"

    try:
        metadata_json = json.dumps(registry_metadata, indent=2)
        s3_client.put_object(
            Bucket=model_bucket, Key=metadata_key, Body=metadata_json.encode("utf-8")
        )
        logger.info(f"Saved registry metadata to s3://{model_bucket}/{metadata_key}")

    except ClientError as e:
        logger.error(f"Failed to save registry metadata: {e}")
        raise ValueError(f"Failed to save registry metadata: {e}")

    logger.info(f"Model registered successfully: {model_name} v{model_version}")

    return {
        "status": "success",
        "message": "Model registered successfully",
        "registration_info": {
            "model_name": model_name,
            "model_version": model_version,
            "model_s3_uri": model_s3_uri,
            "metadata_s3_uri": f"s3://{model_bucket}/{metadata_key}",
            "registered_at": registry_metadata["registered_at"],
        },
    }
