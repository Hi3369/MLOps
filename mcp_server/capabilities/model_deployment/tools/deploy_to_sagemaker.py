"""
Deploy to SageMaker Tool

SageMakerエンドポイントへのデプロイツール
"""

import logging
from datetime import datetime
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def deploy_to_sagemaker(
    model_s3_uri: str,
    endpoint_name: str,
    instance_type: str = "ml.t3.medium",
    instance_count: int = 1,
    model_name: str = None,
    wait_for_completion: bool = True,
) -> Dict[str, Any]:
    """
    SageMakerエンドポイントにモデルをデプロイ

    Args:
        model_s3_uri: モデルデータのS3 URI
        endpoint_name: エンドポイント名
        instance_type: インスタンスタイプ
        instance_count: インスタンス数
        model_name: モデル名（省略時は自動生成）
        wait_for_completion: デプロイ完了まで待機するか

    Returns:
        デプロイ結果辞書
    """
    logger.info(f"Deploying model to SageMaker endpoint: {endpoint_name}")

    # S3 URIのバリデーション
    if not model_s3_uri.startswith("s3://"):
        raise ValueError("Invalid S3 URI: must start with 's3://'")

    # SageMakerクライアント
    sagemaker_client = boto3.client("sagemaker")

    # モデル名の生成
    if model_name is None:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        model_name = f"model-{timestamp}"

    try:
        # 1. モデル作成
        model_arn = _create_model(sagemaker_client, model_name, model_s3_uri)
        logger.info(f"Model created: {model_arn}")

        # 2. エンドポイント設定作成
        endpoint_config_name = f"{endpoint_name}-config"
        endpoint_config_arn = _create_endpoint_config(
            sagemaker_client,
            endpoint_config_name,
            model_name,
            instance_type,
            instance_count,
        )
        logger.info(f"Endpoint config created: {endpoint_config_arn}")

        # 3. エンドポイント作成または更新
        endpoint_arn, is_new = _create_or_update_endpoint(
            sagemaker_client, endpoint_name, endpoint_config_name
        )
        logger.info(f"Endpoint {'created' if is_new else 'updated'}: {endpoint_arn}")

        # 4. デプロイ完了待機（オプション）
        if wait_for_completion:
            _wait_for_endpoint(sagemaker_client, endpoint_name)
            logger.info(f"Endpoint is in service: {endpoint_name}")

        return {
            "status": "success",
            "message": f"Model deployed to endpoint: {endpoint_name}",
            "deployment_info": {
                "endpoint_name": endpoint_name,
                "endpoint_arn": endpoint_arn,
                "model_name": model_name,
                "model_arn": model_arn,
                "endpoint_config_name": endpoint_config_name,
                "endpoint_config_arn": endpoint_config_arn,
                "instance_type": instance_type,
                "instance_count": instance_count,
                "is_new_endpoint": is_new,
                "wait_for_completion": wait_for_completion,
            },
        }

    except ClientError as e:
        logger.error(f"SageMaker deployment error: {e}")
        raise ValueError(f"Failed to deploy model: {e}")


def _create_model(
    sagemaker_client,
    model_name: str,
    model_s3_uri: str,
) -> str:
    """SageMakerモデルを作成"""
    # 実行ロールARN（環境変数から取得することを想定）
    import os

    execution_role = os.environ.get(
        "SAGEMAKER_EXECUTION_ROLE_ARN",
        "arn:aws:iam::123456789012:role/SageMakerExecutionRole",
    )

    # デフォルトコンテナイメージ（sklearn用）
    # 本番環境では適切なイメージを選択
    container_image = "382416733822.dkr.ecr.us-east-1.amazonaws.com/sklearn:latest"

    response = sagemaker_client.create_model(
        ModelName=model_name,
        PrimaryContainer={
            "Image": container_image,
            "ModelDataUrl": model_s3_uri,
        },
        ExecutionRoleArn=execution_role,
    )

    return response["ModelArn"]


def _create_endpoint_config(
    sagemaker_client,
    endpoint_config_name: str,
    model_name: str,
    instance_type: str,
    instance_count: int,
) -> str:
    """エンドポイント設定を作成"""
    response = sagemaker_client.create_endpoint_config(
        EndpointConfigName=endpoint_config_name,
        ProductionVariants=[
            {
                "VariantName": "AllTraffic",
                "ModelName": model_name,
                "InstanceType": instance_type,
                "InitialInstanceCount": instance_count,
                "InitialVariantWeight": 1,
            }
        ],
    )

    return response["EndpointConfigArn"]


def _create_or_update_endpoint(
    sagemaker_client,
    endpoint_name: str,
    endpoint_config_name: str,
) -> tuple[str, bool]:
    """エンドポイントを作成または更新"""
    try:
        # 既存エンドポイントの確認
        sagemaker_client.describe_endpoint(EndpointName=endpoint_name)

        # 存在する場合は更新
        response = sagemaker_client.update_endpoint(
            EndpointName=endpoint_name,
            EndpointConfigName=endpoint_config_name,
        )
        return response["EndpointArn"], False

    except ClientError as e:
        if e.response["Error"]["Code"] == "ValidationException":
            # 存在しない場合は新規作成
            response = sagemaker_client.create_endpoint(
                EndpointName=endpoint_name,
                EndpointConfigName=endpoint_config_name,
            )
            return response["EndpointArn"], True
        else:
            raise


def _wait_for_endpoint(sagemaker_client, endpoint_name: str, timeout: int = 600):
    """エンドポイントが稼働状態になるまで待機"""
    import time

    start_time = time.time()

    while time.time() - start_time < timeout:
        response = sagemaker_client.describe_endpoint(EndpointName=endpoint_name)
        status = response["EndpointStatus"]

        if status == "InService":
            return
        elif status in ["Failed", "RollingBack"]:
            raise ValueError(f"Endpoint deployment failed with status: {status}")

        logger.info(f"Endpoint status: {status}, waiting...")
        time.sleep(10)

    raise TimeoutError(f"Endpoint deployment timeout after {timeout} seconds")
