"""
Configure Auto Scaling Tool

オートスケーリング設定ツール
"""

import logging
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def configure_autoscaling(
    endpoint_name: str,
    variant_name: str = "AllTraffic",
    min_capacity: int = 1,
    max_capacity: int = 4,
    target_metric: str = "SageMakerVariantInvocationsPerInstance",
    target_value: float = 70.0,
) -> Dict[str, Any]:
    """
    エンドポイントのオートスケーリングを設定

    Args:
        endpoint_name: エンドポイント名
        variant_name: バリアント名
        min_capacity: 最小インスタンス数
        max_capacity: 最大インスタンス数
        target_metric: ターゲットメトリクス
        target_value: ターゲット値

    Returns:
        設定結果辞書
    """
    logger.info(f"Configuring autoscaling for endpoint: {endpoint_name}")

    # パラメータの検証
    if min_capacity < 1:
        raise ValueError("min_capacity must be at least 1")
    if max_capacity < min_capacity:
        raise ValueError("max_capacity must be >= min_capacity")
    if target_value <= 0:
        raise ValueError("target_value must be positive")

    # メトリクスタイプの検証
    valid_metrics = {
        "SageMakerVariantInvocationsPerInstance": "InvocationsPerInstance",
        "CPUUtilization": "CPUUtilization",
        "ModelLatency": "ModelLatency",
    }

    if target_metric not in valid_metrics:
        raise ValueError(
            f"Invalid target_metric: {target_metric}. "
            f"Must be one of {list(valid_metrics.keys())}"
        )

    # Application Auto Scalingクライアント
    autoscaling_client = boto3.client("application-autoscaling")

    # リソースID
    resource_id = f"endpoint/{endpoint_name}/variant/{variant_name}"

    try:
        # 1. スケーラブルターゲットを登録
        autoscaling_client.register_scalable_target(
            ServiceNamespace="sagemaker",
            ResourceId=resource_id,
            ScalableDimension="sagemaker:variant:DesiredInstanceCount",
            MinCapacity=min_capacity,
            MaxCapacity=max_capacity,
        )
        logger.info(f"Scalable target registered: {resource_id}")

        # 2. スケーリングポリシーを設定
        policy_name = f"{endpoint_name}-{variant_name}-scaling-policy"

        predefined_metric_type = f"SageMakerVariant{valid_metrics[target_metric]}"

        response = autoscaling_client.put_scaling_policy(
            PolicyName=policy_name,
            ServiceNamespace="sagemaker",
            ResourceId=resource_id,
            ScalableDimension="sagemaker:variant:DesiredInstanceCount",
            PolicyType="TargetTrackingScaling",
            TargetTrackingScalingPolicyConfiguration={
                "TargetValue": target_value,
                "PredefinedMetricSpecification": {
                    "PredefinedMetricType": predefined_metric_type,
                },
                "ScaleInCooldown": 300,  # 5分
                "ScaleOutCooldown": 60,  # 1分
            },
        )

        policy_arn = response["PolicyARN"]
        logger.info(f"Scaling policy created: {policy_arn}")

        return {
            "status": "success",
            "message": f"Autoscaling configured for endpoint: {endpoint_name}",
            "autoscaling_info": {
                "endpoint_name": endpoint_name,
                "variant_name": variant_name,
                "resource_id": resource_id,
                "min_capacity": min_capacity,
                "max_capacity": max_capacity,
                "target_metric": target_metric,
                "target_value": target_value,
                "policy_name": policy_name,
                "policy_arn": policy_arn,
            },
        }

    except ClientError as e:
        logger.error(f"Autoscaling configuration error: {e}")
        raise ValueError(f"Failed to configure autoscaling: {e}")


def delete_autoscaling(
    endpoint_name: str,
    variant_name: str = "AllTraffic",
) -> Dict[str, Any]:
    """
    エンドポイントのオートスケーリング設定を削除

    Args:
        endpoint_name: エンドポイント名
        variant_name: バリアント名

    Returns:
        削除結果辞書
    """
    logger.info(f"Deleting autoscaling for endpoint: {endpoint_name}")

    # Application Auto Scalingクライアント
    autoscaling_client = boto3.client("application-autoscaling")

    # リソースID
    resource_id = f"endpoint/{endpoint_name}/variant/{variant_name}"

    try:
        # スケーリングポリシーを削除
        policy_name = f"{endpoint_name}-{variant_name}-scaling-policy"

        autoscaling_client.delete_scaling_policy(
            PolicyName=policy_name,
            ServiceNamespace="sagemaker",
            ResourceId=resource_id,
            ScalableDimension="sagemaker:variant:DesiredInstanceCount",
        )
        logger.info(f"Scaling policy deleted: {policy_name}")

        # スケーラブルターゲットを解除
        autoscaling_client.deregister_scalable_target(
            ServiceNamespace="sagemaker",
            ResourceId=resource_id,
            ScalableDimension="sagemaker:variant:DesiredInstanceCount",
        )
        logger.info(f"Scalable target deregistered: {resource_id}")

        return {
            "status": "success",
            "message": f"Autoscaling deleted for endpoint: {endpoint_name}",
            "deletion_info": {
                "endpoint_name": endpoint_name,
                "variant_name": variant_name,
                "resource_id": resource_id,
                "deleted_policy": policy_name,
            },
        }

    except ClientError as e:
        logger.error(f"Autoscaling deletion error: {e}")
        raise ValueError(f"Failed to delete autoscaling: {e}")
