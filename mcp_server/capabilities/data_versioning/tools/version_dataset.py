"""
Version Dataset Tool

データセットバージョン登録ツール
"""

import hashlib
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def version_dataset(
    dataset_name: str,
    s3_uri: str,
    version: str,
    description: str = "",
    schema: Optional[Dict[str, str]] = None,
    tags: Optional[List[str]] = None,
    parent_version: Optional[str] = None,
    row_count: Optional[int] = None,
    file_format: str = "csv",
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    データセットのバージョンを登録する

    Args:
        dataset_name: データセット名
        s3_uri: データセットのS3 URI
        version: バージョン文字列（例: "v1.0.0"）
        description: バージョンの説明
        schema: スキーマ定義（カラム名→型のマッピング）
        tags: タグリスト
        parent_version: 親バージョン（派生元）
        row_count: 行数
        file_format: ファイル形式（csv, parquet, json）
        metadata: 追加メタデータ

    Returns:
        バージョン登録結果辞書
    """
    logger.info(f"Versioning dataset: {dataset_name} {version}")

    # パラメータ検証
    if not dataset_name:
        raise ValueError("dataset_name must not be empty")

    if not s3_uri:
        raise ValueError("s3_uri must not be empty")

    if not s3_uri.startswith("s3://"):
        raise ValueError("s3_uri must start with 's3://'")

    if not version:
        raise ValueError("version must not be empty")

    valid_formats = ["csv", "parquet", "json", "orc", "avro"]
    if file_format not in valid_formats:
        raise ValueError(f"file_format must be one of {valid_formats}")

    if row_count is not None and row_count < 0:
        raise ValueError("row_count must be a non-negative integer")

    try:
        env = os.environ.get("MLOPS_ENV", "development")
        timestamp = datetime.now(timezone.utc).isoformat()
        version_id = str(uuid4())[:8]

        # データセットのフィンガープリント生成
        fingerprint = _compute_fingerprint(dataset_name, version, s3_uri)

        # リネージ情報
        lineage = {
            "parent_version": parent_version,
            "created_from": s3_uri,
            "created_at": timestamp,
        }

        # 開発/テスト環境ではモック
        if env in ["development", "test"]:
            return _mock_version_dataset(
                dataset_name=dataset_name,
                s3_uri=s3_uri,
                version=version,
                version_id=version_id,
                description=description,
                schema=schema,
                tags=tags,
                lineage=lineage,
                row_count=row_count,
                file_format=file_format,
                metadata=metadata,
                fingerprint=fingerprint,
                timestamp=timestamp,
            )

        # 本番環境: S3にバージョンメタデータ保存
        return _real_version_dataset(
            dataset_name=dataset_name,
            s3_uri=s3_uri,
            version=version,
            version_id=version_id,
            description=description,
            schema=schema,
            tags=tags,
            lineage=lineage,
            row_count=row_count,
            file_format=file_format,
            metadata=metadata,
            fingerprint=fingerprint,
            timestamp=timestamp,
        )

    except ClientError as e:
        logger.error(f"AWS error versioning dataset: {e}")
        raise ValueError(f"Failed to version dataset: {e}")
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Failed to version dataset: {e}")
        raise ValueError(f"Failed to version dataset: {e}")


def _compute_fingerprint(dataset_name: str, version: str, s3_uri: str) -> str:
    """データセットフィンガープリントを計算"""
    content = f"{dataset_name}:{version}:{s3_uri}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def _mock_version_dataset(
    dataset_name: str,
    s3_uri: str,
    version: str,
    version_id: str,
    description: str,
    schema: Optional[Dict[str, str]],
    tags: Optional[List[str]],
    lineage: Dict[str, Any],
    row_count: Optional[int],
    file_format: str,
    metadata: Optional[Dict[str, Any]],
    fingerprint: str,
    timestamp: str,
) -> Dict[str, Any]:
    """モックバージョン登録（開発・テスト用）"""
    logger.info("Using mock dataset versioning")

    return {
        "status": "success",
        "message": f"Dataset versioned: {dataset_name} {version}",
        "version_info": {
            "version_id": f"dv-{version_id}",
            "dataset_name": dataset_name,
            "version": version,
            "s3_uri": s3_uri,
            "description": description,
            "schema": schema or {},
            "tags": tags or [],
            "lineage": lineage,
            "row_count": row_count,
            "file_format": file_format,
            "metadata": metadata or {},
            "fingerprint": fingerprint,
            "registered_at": timestamp,
            "mock": True,
        },
    }


def _real_version_dataset(
    dataset_name: str,
    s3_uri: str,
    version: str,
    version_id: str,
    description: str,
    schema: Optional[Dict[str, str]],
    tags: Optional[List[str]],
    lineage: Dict[str, Any],
    row_count: Optional[int],
    file_format: str,
    metadata: Optional[Dict[str, Any]],
    fingerprint: str,
    timestamp: str,
) -> Dict[str, Any]:
    """本番バージョン登録（S3にメタデータ保存）"""
    import json

    s3_client = boto3.client("s3")
    bucket = os.environ.get("MLOPS_DATA_VERSION_BUCKET", "mlops-data-versions")

    version_data = {
        "version_id": f"dv-{version_id}",
        "dataset_name": dataset_name,
        "version": version,
        "s3_uri": s3_uri,
        "description": description,
        "schema": schema or {},
        "tags": tags or [],
        "lineage": lineage,
        "row_count": row_count,
        "file_format": file_format,
        "metadata": metadata or {},
        "fingerprint": fingerprint,
        "registered_at": timestamp,
    }

    # S3に保存
    s3_key = f"datasets/{dataset_name}/versions/{version}/metadata.json"
    s3_client.put_object(
        Bucket=bucket,
        Key=s3_key,
        Body=json.dumps(version_data),
        ContentType="application/json",
    )

    version_data["s3_metadata_uri"] = f"s3://{bucket}/{s3_key}"

    return {
        "status": "success",
        "message": f"Dataset versioned: {dataset_name} {version}",
        "version_info": version_data,
    }
