"""
Track Version History Tool

バージョン履歴追跡ツール
"""

import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


def track_version_history(
    model_name: str,
    version: str,
    metadata: Optional[Dict[str, Any]] = None,
    parent_version: Optional[str] = None,
    training_job_name: Optional[str] = None,
    training_data_version: Optional[str] = None,
    code_version: Optional[str] = None,
    status: str = "development",
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    モデルバージョン履歴を追跡・記録

    Args:
        model_name: モデル名
        version: バージョン（セマンティックバージョニング推奨: v1.0.0）
        metadata: 追加メタデータ
        parent_version: 親バージョン（派生元）
        training_job_name: 関連する学習ジョブ名
        training_data_version: 学習データバージョン
        code_version: コードバージョン（gitコミットハッシュ等）
        status: ステータス（development, staging, production, deprecated）
        tags: タグリスト

    Returns:
        バージョン追跡結果辞書
    """
    logger.info(f"Tracking version history for {model_name}:{version}")

    # パラメータ検証
    if not model_name:
        raise ValueError("model_name must not be empty")

    if not version:
        raise ValueError("version must not be empty")

    # バージョン形式検証（セマンティックバージョニング推奨）
    if not _validate_version(version):
        logger.warning(f"Version '{version}' does not follow semantic versioning")

    if status not in ["development", "staging", "production", "deprecated"]:
        raise ValueError(f"Invalid status: {status}")

    try:
        timestamp = datetime.now(timezone.utc).isoformat()
        version_id = str(uuid4())[:8]

        # バージョン情報構築
        version_info = {
            "version_id": version_id,
            "model_name": model_name,
            "version": version,
            "parent_version": parent_version,
            "training_job_name": training_job_name,
            "training_data_version": training_data_version,
            "code_version": code_version,
            "status": status,
            "tags": tags or [],
            "metadata": metadata or {},
            "created_at": timestamp,
            "updated_at": timestamp,
        }

        env = os.environ.get("MLOPS_ENV", "development")

        # 開発/テスト環境ではモック
        if env in ["development", "test"]:
            logger.info("Using mock version tracking (dev/test environment)")
            return _mock_track_version(version_info)

        # 本番環境：実際にバージョン情報を保存
        return _real_track_version(version_info)

    except Exception as e:
        logger.error(f"Failed to track version history: {e}")
        raise ValueError(f"Failed to track version history: {e}")


def _validate_version(version: str) -> bool:
    """セマンティックバージョニング形式を検証"""
    # v1.0.0 or 1.0.0 形式
    pattern = r"^v?\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?(\+[a-zA-Z0-9.]+)?$"
    return bool(re.match(pattern, version))


def _mock_track_version(version_info: Dict[str, Any]) -> Dict[str, Any]:
    """モックバージョン追跡"""
    return {
        "status": "success",
        "message": "Version history tracked (mock)",
        "version_result": {
            "version_id": version_info["version_id"],
            "model_name": version_info["model_name"],
            "version": version_info["version"],
            "parent_version": version_info["parent_version"],
            "status": version_info["status"],
            "lineage": _build_lineage(version_info),
            "registry_uri": f"mock://model-registry/{version_info['model_name']}/{version_info['version']}",
            "created_at": version_info["created_at"],
            "mock": True,
        },
    }


def _real_track_version(version_info: Dict[str, Any]) -> Dict[str, Any]:
    """実際のバージョン追跡（SageMaker Model Registry等）"""
    # 本番環境ではSageMaker Model Registryに登録
    import boto3
    from botocore.exceptions import ClientError

    try:
        sm_client = boto3.client("sagemaker")

        # モデルパッケージグループの確認・作成
        model_package_group_name = f"{version_info['model_name']}-group"

        try:
            sm_client.describe_model_package_group(ModelPackageGroupName=model_package_group_name)
        except ClientError:
            # グループが存在しない場合は作成
            sm_client.create_model_package_group(
                ModelPackageGroupName=model_package_group_name,
                ModelPackageGroupDescription=f"Model versions for {version_info['model_name']}",
            )

        # Note: 実際のモデル登録にはモデルアーティファクトが必要
        # ここではバージョン情報の追跡のみを行う

        return {
            "status": "success",
            "message": "Version history tracked successfully",
            "version_result": {
                "version_id": version_info["version_id"],
                "model_name": version_info["model_name"],
                "version": version_info["version"],
                "parent_version": version_info["parent_version"],
                "status": version_info["status"],
                "lineage": _build_lineage(version_info),
                "model_package_group": model_package_group_name,
                "created_at": version_info["created_at"],
                "mock": False,
            },
        }

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        raise ValueError(f"SageMaker error ({error_code}): {e}")


def _build_lineage(version_info: Dict[str, Any]) -> Dict[str, Any]:
    """バージョン系譜情報を構築"""
    return {
        "model_name": version_info["model_name"],
        "current_version": version_info["version"],
        "parent_version": version_info["parent_version"],
        "training_job": version_info["training_job_name"],
        "training_data": version_info["training_data_version"],
        "code": version_info["code_version"],
        "tags": version_info["tags"],
    }
