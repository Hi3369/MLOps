"""
Start Experiment Tool

実験開始・管理ツール
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def start_experiment(
    experiment_name: str,
    description: str = "",
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    s3_bucket: Optional[str] = None,
) -> Dict[str, Any]:
    """
    新しい実験を開始する

    Args:
        experiment_name: 実験名
        description: 実験の説明
        tags: タグリスト
        metadata: メタデータ辞書
        s3_bucket: 実験データ保存先S3バケット

    Returns:
        実験情報辞書
    """
    logger.info(f"Starting experiment: {experiment_name}")

    # パラメータ検証
    if not experiment_name:
        raise ValueError("experiment_name must not be empty")

    if not experiment_name.replace("-", "").replace("_", "").replace(".", "").isalnum():
        raise ValueError(
            "experiment_name must contain only alphanumeric characters, "
            "hyphens, underscores, and dots"
        )

    if len(experiment_name) > 256:
        raise ValueError("experiment_name must be 256 characters or less")

    try:
        env = os.environ.get("MLOPS_ENV", "development")
        timestamp = datetime.now(timezone.utc).isoformat()
        experiment_id = str(uuid4())[:8]

        # 開発/テスト環境ではモック
        if env in ["development", "test"]:
            return _mock_start_experiment(
                experiment_name=experiment_name,
                experiment_id=experiment_id,
                description=description,
                tags=tags,
                metadata=metadata,
                s3_bucket=s3_bucket,
                timestamp=timestamp,
            )

        # 本番環境: SageMaker Experiments
        return _real_start_experiment(
            experiment_name=experiment_name,
            experiment_id=experiment_id,
            description=description,
            tags=tags,
            metadata=metadata,
            s3_bucket=s3_bucket,
            timestamp=timestamp,
        )

    except ClientError as e:
        logger.error(f"AWS error starting experiment: {e}")
        raise ValueError(f"Failed to start experiment: {e}")
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Failed to start experiment: {e}")
        raise ValueError(f"Failed to start experiment: {e}")


def _mock_start_experiment(
    experiment_name: str,
    experiment_id: str,
    description: str,
    tags: Optional[List[str]],
    metadata: Optional[Dict[str, Any]],
    s3_bucket: Optional[str],
    timestamp: str,
) -> Dict[str, Any]:
    """モック実験開始（開発・テスト用）"""
    logger.info("Using mock experiment start")

    return {
        "status": "success",
        "message": f"Experiment started: {experiment_name}",
        "experiment_info": {
            "experiment_id": f"exp-{experiment_id}",
            "experiment_name": experiment_name,
            "description": description,
            "status": "running",
            "tags": tags or [],
            "metadata": metadata or {},
            "s3_bucket": s3_bucket or "mlops-experiments",
            "s3_prefix": f"experiments/{experiment_name}/{experiment_id}/",
            "created_at": timestamp,
            "updated_at": timestamp,
            "mock": True,
        },
    }


def _real_start_experiment(
    experiment_name: str,
    experiment_id: str,
    description: str,
    tags: Optional[List[str]],
    metadata: Optional[Dict[str, Any]],
    s3_bucket: Optional[str],
    timestamp: str,
) -> Dict[str, Any]:
    """本番実験開始（SageMaker Experiments）"""
    sagemaker_client = boto3.client("sagemaker")

    # SageMaker Experiment作成
    create_params: Dict[str, Any] = {
        "ExperimentName": f"{experiment_name}-{experiment_id}",
        "Description": description or f"MLOps experiment: {experiment_name}",
    }

    if tags:
        create_params["Tags"] = [{"Key": "mlops-tag", "Value": tag} for tag in tags]

    response = sagemaker_client.create_experiment(**create_params)

    # S3にメタデータ保存
    if s3_bucket:
        import json

        s3_client = boto3.client("s3")
        experiment_metadata = {
            "experiment_id": f"exp-{experiment_id}",
            "experiment_name": experiment_name,
            "description": description,
            "tags": tags or [],
            "metadata": metadata or {},
            "created_at": timestamp,
        }
        s3_client.put_object(
            Bucket=s3_bucket,
            Key=f"experiments/{experiment_name}/{experiment_id}/metadata.json",
            Body=json.dumps(experiment_metadata),
            ContentType="application/json",
        )

    return {
        "status": "success",
        "message": f"Experiment started: {experiment_name}",
        "experiment_info": {
            "experiment_id": f"exp-{experiment_id}",
            "experiment_name": experiment_name,
            "experiment_arn": response["ExperimentArn"],
            "description": description,
            "status": "running",
            "tags": tags or [],
            "metadata": metadata or {},
            "s3_bucket": s3_bucket or "mlops-experiments",
            "s3_prefix": f"experiments/{experiment_name}/{experiment_id}/",
            "created_at": timestamp,
            "updated_at": timestamp,
        },
    }
