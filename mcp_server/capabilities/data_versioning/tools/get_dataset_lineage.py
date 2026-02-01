"""
Get Dataset Lineage Tool

データ系譜取得ツール
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def get_dataset_lineage(
    dataset_name: str,
    version: Optional[str] = None,
    depth: int = 5,
    include_transformations: bool = True,
) -> Dict[str, Any]:
    """
    データセットの系譜（リネージ）を取得する

    Args:
        dataset_name: データセット名
        version: 特定バージョン（省略時は最新）
        depth: 遡る深さ（デフォルト: 5世代）
        include_transformations: 変換処理情報を含めるか

    Returns:
        データ系譜情報辞書
    """
    logger.info(f"Getting lineage for dataset: {dataset_name}")

    # パラメータ検証
    if not dataset_name:
        raise ValueError("dataset_name must not be empty")

    if depth < 1:
        raise ValueError("depth must be at least 1")

    if depth > 20:
        raise ValueError("depth must be 20 or less")

    try:
        env = os.environ.get("MLOPS_ENV", "development")
        timestamp = datetime.now(timezone.utc).isoformat()
        lineage_id = str(uuid4())[:8]

        # 開発/テスト環境ではモック
        if env in ["development", "test"]:
            return _mock_get_lineage(
                dataset_name=dataset_name,
                version=version,
                depth=depth,
                include_transformations=include_transformations,
                lineage_id=lineage_id,
                timestamp=timestamp,
            )

        # 本番環境: S3からリネージ情報取得
        return _real_get_lineage(
            dataset_name=dataset_name,
            version=version,
            depth=depth,
            include_transformations=include_transformations,
            lineage_id=lineage_id,
            timestamp=timestamp,
        )

    except ClientError as e:
        logger.error(f"AWS error getting lineage: {e}")
        raise ValueError(f"Failed to get dataset lineage: {e}")
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Failed to get dataset lineage: {e}")
        raise ValueError(f"Failed to get dataset lineage: {e}")


def _build_mock_lineage_chain(
    dataset_name: str,
    version: Optional[str],
    depth: int,
    include_transformations: bool,
) -> List[Dict[str, Any]]:
    """モックリネージチェーンを構築"""
    chain = []
    current_version = version or "v1.2.0"

    for i in range(min(depth, 3)):
        node = {
            "dataset_name": dataset_name,
            "version": current_version,
            "s3_uri": f"s3://mlops-data/{dataset_name}/{current_version}/data.csv",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "parent_version": None,
        }

        if include_transformations and i > 0:
            node["transformations"] = [
                {
                    "type": "feature_engineering",
                    "description": f"Added derived features (step {i})",
                    "applied_at": datetime.now(timezone.utc).isoformat(),
                },
            ]

        if i < 2:
            # 親バージョンを設定
            parts = current_version.replace("v", "").split(".")
            major, minor = int(parts[0]), int(parts[1])
            if minor > 0:
                parent_ver = f"v{major}.{minor - 1}.0"
            elif major > 0:
                parent_ver = f"v{major - 1}.0.0"
            else:
                parent_ver = None

            node["parent_version"] = parent_ver
            current_version = parent_ver if parent_ver else current_version

        chain.append(node)

        if node["parent_version"] is None:
            break

    return chain


def _mock_get_lineage(
    dataset_name: str,
    version: Optional[str],
    depth: int,
    include_transformations: bool,
    lineage_id: str,
    timestamp: str,
) -> Dict[str, Any]:
    """モックリネージ取得（開発・テスト用）"""
    logger.info("Using mock lineage retrieval")

    chain = _build_mock_lineage_chain(dataset_name, version, depth, include_transformations)

    return {
        "status": "success",
        "message": f"Lineage retrieved for dataset: {dataset_name}",
        "lineage_info": {
            "lineage_id": f"lin-{lineage_id}",
            "dataset_name": dataset_name,
            "requested_version": version or "latest",
            "depth": len(chain),
            "chain": chain,
            "root_dataset": chain[-1] if chain else None,
            "include_transformations": include_transformations,
            "retrieved_at": timestamp,
            "mock": True,
        },
    }


def _real_get_lineage(
    dataset_name: str,
    version: Optional[str],
    depth: int,
    include_transformations: bool,
    lineage_id: str,
    timestamp: str,
) -> Dict[str, Any]:
    """本番リネージ取得（S3からデータ取得）"""
    import json

    s3_client = boto3.client("s3")
    bucket = os.environ.get("MLOPS_DATA_VERSION_BUCKET", "mlops-data-versions")

    chain = []
    current_version = version

    # 最新バージョンを取得
    if current_version is None:
        prefix = f"datasets/{dataset_name}/versions/"
        paginator = s3_client.get_paginator("list_objects_v2")
        versions = []
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix, Delimiter="/"):
            for cp in page.get("CommonPrefixes", []):
                ver = cp["Prefix"].rstrip("/").split("/")[-1]
                versions.append(ver)
        if versions:
            versions.sort()
            current_version = versions[-1]
        else:
            return {
                "status": "success",
                "message": f"No versions found for dataset: {dataset_name}",
                "lineage_info": {
                    "lineage_id": f"lin-{lineage_id}",
                    "dataset_name": dataset_name,
                    "requested_version": "latest",
                    "depth": 0,
                    "chain": [],
                    "root_dataset": None,
                    "retrieved_at": timestamp,
                },
            }

    # リネージチェーンを構築
    for _ in range(depth):
        if current_version is None:
            break

        s3_key = f"datasets/{dataset_name}/versions/{current_version}/metadata.json"
        try:
            response = s3_client.get_object(Bucket=bucket, Key=s3_key)
            version_data = json.loads(response["Body"].read().decode("utf-8"))

            node = {
                "dataset_name": dataset_name,
                "version": current_version,
                "s3_uri": version_data.get("s3_uri", ""),
                "created_at": version_data.get("registered_at", ""),
                "parent_version": version_data.get("lineage", {}).get("parent_version"),
            }

            if include_transformations:
                node["transformations"] = version_data.get("transformations", [])

            chain.append(node)
            current_version = node["parent_version"]

        except ClientError:
            logger.warning(f"Version metadata not found: {current_version}")
            break

    return {
        "status": "success",
        "message": f"Lineage retrieved for dataset: {dataset_name}",
        "lineage_info": {
            "lineage_id": f"lin-{lineage_id}",
            "dataset_name": dataset_name,
            "requested_version": version or "latest",
            "depth": len(chain),
            "chain": chain,
            "root_dataset": chain[-1] if chain else None,
            "include_transformations": include_transformations,
            "retrieved_at": timestamp,
        },
    }
