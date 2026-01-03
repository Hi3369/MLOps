"""
Generate Deployment Config Tool

デプロイ設定生成ツール
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def generate_deployment_config(
    model_s3_uri: str,
    deployment_type: str = "sagemaker",
    instance_type: str = "ml.t3.medium",
    instance_count: int = 1,
    auto_scaling: bool = False,
) -> Dict[str, Any]:
    """
    デプロイ設定を生成

    Args:
        model_s3_uri: モデルのS3 URI
        deployment_type: デプロイタイプ (sagemaker, ecs, lambda)
        instance_type: インスタンスタイプ
        instance_count: インスタンス数
        auto_scaling: オートスケーリングを有効にするか

    Returns:
        デプロイ設定辞書
    """
    logger.info(f"Generating deployment config for {deployment_type}")

    # S3 URIのバリデーション
    if not model_s3_uri.startswith("s3://"):
        raise ValueError("Invalid S3 URI: must start with 's3://'")

    # デプロイタイプの検証
    valid_deployment_types = ["sagemaker", "ecs", "lambda"]
    if deployment_type not in valid_deployment_types:
        raise ValueError(
            f"Invalid deployment_type: {deployment_type}. "
            f"Must be one of {valid_deployment_types}"
        )

    # デプロイタイプに応じた設定を生成
    if deployment_type == "sagemaker":
        config = _generate_sagemaker_config(
            model_s3_uri, instance_type, instance_count, auto_scaling
        )
    elif deployment_type == "ecs":
        config = _generate_ecs_config(model_s3_uri, instance_type, instance_count, auto_scaling)
    else:  # lambda
        config = _generate_lambda_config(model_s3_uri)

    logger.info("Deployment config generated successfully")

    return {
        "status": "success",
        "message": "Deployment config generated successfully",
        "deployment_config": config,
    }


def _generate_sagemaker_config(
    model_s3_uri: str,
    instance_type: str,
    instance_count: int,
    auto_scaling: bool,
) -> Dict[str, Any]:
    """SageMakerデプロイ設定を生成"""
    config = {
        "deployment_type": "sagemaker",
        "model_data": model_s3_uri,
        "instance_type": instance_type,
        "initial_instance_count": instance_count,
        "endpoint_config": {
            "variant_name": "AllTraffic",
            "initial_variant_weight": 1,
        },
    }

    if auto_scaling:
        config["auto_scaling"] = {
            "enabled": True,
            "min_capacity": instance_count,
            "max_capacity": instance_count * 4,
            "target_value": 70.0,  # Target CPU utilization %
            "scale_in_cooldown": 300,  # seconds
            "scale_out_cooldown": 60,  # seconds
        }

    return config


def _generate_ecs_config(
    model_s3_uri: str,
    instance_type: str,
    instance_count: int,
    auto_scaling: bool,
) -> Dict[str, Any]:
    """ECSデプロイ設定を生成"""
    # インスタンスタイプからCPU/メモリを推定
    cpu, memory = _parse_instance_type(instance_type)

    config = {
        "deployment_type": "ecs",
        "model_data": model_s3_uri,
        "task_definition": {
            "cpu": cpu,
            "memory": memory,
            "container_definitions": [
                {
                    "name": "model-inference",
                    "environment": [
                        {"name": "MODEL_S3_URI", "value": model_s3_uri},
                    ],
                    "port_mappings": [{"container_port": 8080, "host_port": 8080}],
                }
            ],
        },
        "service": {
            "desired_count": instance_count,
            "launch_type": "FARGATE",
        },
    }

    if auto_scaling:
        config["auto_scaling"] = {
            "enabled": True,
            "min_capacity": instance_count,
            "max_capacity": instance_count * 4,
            "target_tracking_scaling_policies": [
                {
                    "target_value": 70.0,
                    "predefined_metric_type": "ECSServiceAverageCPUUtilization",
                }
            ],
        }

    return config


def _generate_lambda_config(model_s3_uri: str) -> Dict[str, Any]:
    """Lambdaデプロイ設定を生成"""
    config = {
        "deployment_type": "lambda",
        "model_data": model_s3_uri,
        "function_config": {
            "runtime": "python3.11",
            "handler": "inference.handler",
            "memory_size": 3008,  # MB (max for Lambda)
            "timeout": 900,  # seconds (max for Lambda)
            "environment": {
                "MODEL_S3_URI": model_s3_uri,
            },
        },
        "notes": [
            "Lambda has a 250MB deployment package limit (unzipped)",
            "Consider using Lambda Layers for large dependencies",
            "For models > 250MB, use EFS or load from S3 at runtime",
        ],
    }

    return config


def _parse_instance_type(instance_type: str) -> tuple:
    """インスタンスタイプからCPU/メモリを推定"""
    # 簡易的な推定（実際にはより詳細なマッピングが必要）
    size_map = {
        "small": (512, 1024),
        "medium": (1024, 2048),
        "large": (2048, 4096),
        "xlarge": (4096, 8192),
    }

    # instance_typeから size を抽出
    for size_key in size_map.keys():
        if size_key in instance_type.lower():
            return size_map[size_key]

    # デフォルト
    return (1024, 2048)
