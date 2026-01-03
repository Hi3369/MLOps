"""
Delete Endpoint Tool

エンドポイント削除ツール
"""

import logging
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def delete_endpoint(
    endpoint_name: str,
    delete_endpoint_config: bool = True,
    delete_model: bool = False,
) -> Dict[str, Any]:
    """
    エンドポイントを削除

    Args:
        endpoint_name: エンドポイント名
        delete_endpoint_config: エンドポイント設定も削除するか
        delete_model: モデルも削除するか

    Returns:
        削除結果辞書
    """
    logger.info(f"Deleting endpoint: {endpoint_name}")

    # SageMakerクライアント
    sagemaker_client = boto3.client("sagemaker")

    deleted_resources = []

    try:
        # エンドポイント情報を取得（設定名とモデル名の取得用）
        endpoint_info = sagemaker_client.describe_endpoint(EndpointName=endpoint_name)
        endpoint_config_name = endpoint_info["EndpointConfigName"]

        # モデル名を取得（オプション）
        model_names = []
        if delete_model:
            config_info = sagemaker_client.describe_endpoint_config(
                EndpointConfigName=endpoint_config_name
            )
            for variant in config_info["ProductionVariants"]:
                model_names.append(variant["ModelName"])

        # 1. エンドポイントを削除
        sagemaker_client.delete_endpoint(EndpointName=endpoint_name)
        deleted_resources.append(f"endpoint:{endpoint_name}")
        logger.info(f"Endpoint deleted: {endpoint_name}")

        # 2. エンドポイント設定を削除（オプション）
        if delete_endpoint_config:
            try:
                sagemaker_client.delete_endpoint_config(EndpointConfigName=endpoint_config_name)
                deleted_resources.append(f"endpoint_config:{endpoint_config_name}")
                logger.info(f"Endpoint config deleted: {endpoint_config_name}")
            except ClientError as e:
                logger.warning(f"Failed to delete endpoint config: {e}")

        # 3. モデルを削除（オプション）
        if delete_model:
            for model_name in model_names:
                try:
                    sagemaker_client.delete_model(ModelName=model_name)
                    deleted_resources.append(f"model:{model_name}")
                    logger.info(f"Model deleted: {model_name}")
                except ClientError as e:
                    logger.warning(f"Failed to delete model {model_name}: {e}")

        return {
            "status": "success",
            "message": f"Endpoint deleted: {endpoint_name}",
            "deletion_info": {
                "endpoint_name": endpoint_name,
                "deleted_resources": deleted_resources,
                "endpoint_config_name": endpoint_config_name if delete_endpoint_config else None,
                "model_names": model_names if delete_model else [],
            },
        }

    except ClientError as e:
        logger.error(f"Endpoint deletion error: {e}")
        if e.response["Error"]["Code"] == "ValidationException":
            raise ValueError(f"Endpoint not found: {endpoint_name}")
        raise ValueError(f"Failed to delete endpoint: {e}")


def rollback_deployment(
    endpoint_name: str,
    previous_config_name: str = None,
) -> Dict[str, Any]:
    """
    デプロイメントをロールバック

    Args:
        endpoint_name: エンドポイント名
        previous_config_name: ロールバック先の設定名（省略時は自動検出を試行）

    Returns:
        ロールバック結果辞書
    """
    logger.info(f"Rolling back deployment for endpoint: {endpoint_name}")

    # SageMakerクライアント
    sagemaker_client = boto3.client("sagemaker")

    try:
        # 現在のエンドポイント情報を取得
        current_endpoint = sagemaker_client.describe_endpoint(EndpointName=endpoint_name)
        current_config_name = current_endpoint["EndpointConfigName"]

        # ロールバック先の設定名が指定されていない場合
        if previous_config_name is None:
            # エンドポイント設定の履歴を取得
            configs_response = sagemaker_client.list_endpoint_configs(
                NameContains=endpoint_name,
                SortBy="CreationTime",
                SortOrder="Descending",
                MaxResults=10,
            )

            configs = configs_response.get("EndpointConfigs", [])

            # 現在の設定以外で最新のものを選択
            previous_configs = [
                c for c in configs if c["EndpointConfigName"] != current_config_name
            ]

            if not previous_configs:
                raise ValueError(
                    "No previous endpoint config found for rollback. "
                    "Please specify previous_config_name explicitly."
                )

            previous_config_name = previous_configs[0]["EndpointConfigName"]
            logger.info(f"Auto-detected previous config: {previous_config_name}")

        # エンドポイントを更新（ロールバック）
        sagemaker_client.update_endpoint(
            EndpointName=endpoint_name,
            EndpointConfigName=previous_config_name,
        )

        logger.info(f"Rollback initiated for endpoint: {endpoint_name}")

        return {
            "status": "success",
            "message": f"Deployment rollback initiated for endpoint: {endpoint_name}",
            "rollback_info": {
                "endpoint_name": endpoint_name,
                "current_config_name": current_config_name,
                "previous_config_name": previous_config_name,
                "rollback_status": "InProgress",
            },
        }

    except ClientError as e:
        logger.error(f"Rollback error: {e}")
        raise ValueError(f"Failed to rollback deployment: {e}")
