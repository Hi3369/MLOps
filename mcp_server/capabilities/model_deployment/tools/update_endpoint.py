"""
Update Endpoint Tool

エンドポイント更新・トラフィック制御ツール
"""

import logging
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def update_endpoint_traffic(
    endpoint_name: str,
    variant_weights: Dict[str, float],
) -> Dict[str, Any]:
    """
    エンドポイントのトラフィック配分を更新（カナリアデプロイ）

    Args:
        endpoint_name: エンドポイント名
        variant_weights: バリアント名と重みの辞書 (例: {"VariantA": 0.9, "VariantB": 0.1})

    Returns:
        更新結果辞書
    """
    logger.info(f"Updating traffic for endpoint: {endpoint_name}")

    # SageMakerクライアント
    sagemaker_client = boto3.client("sagemaker")

    try:
        # エンドポイント情報を取得
        response = sagemaker_client.describe_endpoint(EndpointName=endpoint_name)

        # 既存のバリアント設定を取得
        current_variants = response["ProductionVariants"]

        # トラフィック配分を更新
        updated_variants = []
        for variant in current_variants:
            variant_name = variant["VariantName"]
            if variant_name in variant_weights:
                updated_variants.append(
                    {
                        "VariantName": variant_name,
                        "DesiredWeight": variant_weights[variant_name],
                    }
                )
            else:
                # 指定されていないバリアントは0%に
                updated_variants.append(
                    {
                        "VariantName": variant_name,
                        "DesiredWeight": 0.0,
                    }
                )

        # 合計が1.0（100%）であることを確認
        total_weight = sum(v["DesiredWeight"] for v in updated_variants)
        if abs(total_weight - 1.0) > 0.001:
            raise ValueError(
                f"Variant weights must sum to 1.0, got {total_weight}. "
                f"Weights: {variant_weights}"
            )

        # トラフィック配分を更新
        sagemaker_client.update_endpoint_weights_and_capacities(
            EndpointName=endpoint_name,
            DesiredWeightsAndCapacities=updated_variants,
        )

        logger.info(f"Traffic updated for endpoint: {endpoint_name}")

        return {
            "status": "success",
            "message": f"Traffic distribution updated for endpoint: {endpoint_name}",
            "traffic_info": {
                "endpoint_name": endpoint_name,
                "variant_weights": variant_weights,
                "total_weight": total_weight,
                "updated_variants": updated_variants,
            },
        }

    except ClientError as e:
        logger.error(f"SageMaker traffic update error: {e}")
        if e.response["Error"]["Code"] == "ValidationException":
            raise ValueError(f"Endpoint not found: {endpoint_name}")
        raise ValueError(f"Failed to update traffic: {e}")


def update_endpoint_capacity(
    endpoint_name: str,
    variant_name: str,
    instance_count: int,
) -> Dict[str, Any]:
    """
    エンドポイントのインスタンス数を更新

    Args:
        endpoint_name: エンドポイント名
        variant_name: バリアント名
        instance_count: インスタンス数

    Returns:
        更新結果辞書
    """
    logger.info(f"Updating capacity for endpoint: {endpoint_name}, variant: {variant_name}")

    # インスタンス数の検証
    if instance_count < 1:
        raise ValueError("Instance count must be at least 1")

    # SageMakerクライアント
    sagemaker_client = boto3.client("sagemaker")

    try:
        # 容量を更新
        sagemaker_client.update_endpoint_weights_and_capacities(
            EndpointName=endpoint_name,
            DesiredWeightsAndCapacities=[
                {
                    "VariantName": variant_name,
                    "DesiredInstanceCount": instance_count,
                }
            ],
        )

        logger.info(f"Capacity updated for endpoint: {endpoint_name}")

        return {
            "status": "success",
            "message": f"Capacity updated for endpoint: {endpoint_name}",
            "capacity_info": {
                "endpoint_name": endpoint_name,
                "variant_name": variant_name,
                "instance_count": instance_count,
            },
        }

    except ClientError as e:
        logger.error(f"SageMaker capacity update error: {e}")
        raise ValueError(f"Failed to update capacity: {e}")
