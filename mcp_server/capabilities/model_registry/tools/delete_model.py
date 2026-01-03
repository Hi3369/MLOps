"""
Delete Model Tool

モデル削除ツール
"""

import logging
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def delete_model(
    model_s3_uri: str,
    delete_metadata: bool = True,
) -> Dict[str, Any]:
    """
    モデルを削除

    Args:
        model_s3_uri: モデルのS3 URI (.pkl)
        delete_metadata: メタデータも削除するか (デフォルト: True)

    Returns:
        削除結果辞書
    """
    logger.info(f"Deleting model: {model_s3_uri}")

    # S3 URIのバリデーション
    if not model_s3_uri.startswith("s3://"):
        raise ValueError("Invalid S3 URI: must start with 's3://'")

    model_parts = model_s3_uri[5:].split("/", 1)
    if len(model_parts) != 2:
        raise ValueError("Invalid S3 URI format: s3://bucket/key required")

    # S3クライアント
    s3_client = boto3.client("s3")

    model_bucket, model_key = model_parts

    deleted_objects = []

    # モデルファイルの削除
    try:
        s3_client.delete_object(Bucket=model_bucket, Key=model_key)
        deleted_objects.append(model_s3_uri)
        logger.info(f"Deleted model file: {model_key}")

    except ClientError as e:
        logger.error(f"Failed to delete model file: {e}")
        raise ValueError(f"Failed to delete model: {e}")

    # メタデータの削除
    if delete_metadata:
        # レジストリメタデータ
        metadata_key = f"{model_key.rsplit('.', 1)[0]}_registry.json"

        try:
            s3_client.delete_object(Bucket=model_bucket, Key=metadata_key)
            deleted_objects.append(f"s3://{model_bucket}/{metadata_key}")
            logger.info(f"Deleted registry metadata: {metadata_key}")

        except ClientError as e:
            logger.warning(f"Failed to delete registry metadata: {e}")

        # 学習メタデータ（あれば）
        training_metadata_key = f"{model_key.rsplit('.', 1)[0]}_metadata.json"

        try:
            # 存在確認
            s3_client.head_object(Bucket=model_bucket, Key=training_metadata_key)
            s3_client.delete_object(Bucket=model_bucket, Key=training_metadata_key)
            deleted_objects.append(f"s3://{model_bucket}/{training_metadata_key}")
            logger.info(f"Deleted training metadata: {training_metadata_key}")

        except ClientError:
            # 学習メタデータは存在しない場合がある
            pass

    logger.info(f"Model deletion completed: {len(deleted_objects)} objects deleted")

    return {
        "status": "success",
        "message": "Model deleted successfully",
        "deletion_info": {
            "model_s3_uri": model_s3_uri,
            "deleted_objects": deleted_objects,
            "total_deleted": len(deleted_objects),
        },
    }
