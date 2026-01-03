"""
List Models Tool

モデル一覧ツール
"""

import json
import logging
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def list_models(
    registry_s3_uri: str,
    status_filter: str = None,
) -> Dict[str, Any]:
    """
    登録されているモデルを一覧表示

    Args:
        registry_s3_uri: レジストリのS3 URI (s3://bucket/path/)
        status_filter: ステータスフィルタ (registered, staging, production, archived)

    Returns:
        モデル一覧辞書
    """
    logger.info(f"Listing models from registry: {registry_s3_uri}")

    # S3 URIのバリデーション
    if not registry_s3_uri.startswith("s3://"):
        raise ValueError("Invalid S3 URI: must start with 's3://'")

    parts = registry_s3_uri[5:].split("/", 1)
    if len(parts) != 2:
        raise ValueError("Invalid S3 URI format: s3://bucket/prefix required")

    bucket, prefix = parts

    # S3クライアント
    s3_client = boto3.client("s3")

    # レジストリメタデータファイルを検索
    models = []

    try:
        # registry.jsonで終わるファイルを検索
        paginator = s3_client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=bucket, Prefix=prefix)

        for page in pages:
            if "Contents" not in page:
                continue

            for obj in page["Contents"]:
                if obj["Key"].endswith("_registry.json"):
                    # メタデータを読み込み
                    try:
                        response = s3_client.get_object(Bucket=bucket, Key=obj["Key"])
                        metadata_content = response["Body"].read()
                        metadata = json.loads(metadata_content.decode("utf-8"))

                        # ステータスフィルタを適用
                        if status_filter is None or metadata.get("status") == status_filter:
                            models.append(metadata)

                    except (ClientError, json.JSONDecodeError) as e:
                        logger.warning(f"Failed to read metadata from {obj['Key']}: {e}")
                        continue

        logger.info(f"Found {len(models)} models")

    except ClientError as e:
        logger.error(f"S3 access error: {e}")
        raise ValueError(f"Failed to list models from S3: {e}")

    # 登録日時でソート（新しい順）
    models.sort(key=lambda x: x.get("registered_at", ""), reverse=True)

    return {
        "status": "success",
        "message": f"Found {len(models)} models",
        "models": models,
        "total_count": len(models),
    }
