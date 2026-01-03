"""Model Deployment Capability実装"""
import logging
from typing import Any, Callable, Dict

from .tools import (
    configure_autoscaling,
    delete_autoscaling,
    delete_endpoint,
    deploy_to_sagemaker,
    health_check_endpoint,
    monitor_endpoint,
    rollback_deployment,
    update_endpoint_capacity,
    update_endpoint_traffic,
)

logger = logging.getLogger(__name__)


class ModelDeploymentCapability:
    """モデルデプロイメント管理"""

    def __init__(self):
        """Capabilityの初期化"""
        logger.info("Initializing Model Deployment Capability")
        self._tools = self._register_tools()

    def _register_tools(self) -> Dict[str, Callable]:
        """ツールの登録"""
        return {
            "deploy_to_sagemaker": deploy_to_sagemaker,
            "update_endpoint_traffic": update_endpoint_traffic,
            "update_endpoint_capacity": update_endpoint_capacity,
            "configure_autoscaling": configure_autoscaling,
            "delete_autoscaling": delete_autoscaling,
            "monitor_endpoint": monitor_endpoint,
            "health_check_endpoint": health_check_endpoint,
            "delete_endpoint": delete_endpoint,
            "rollback_deployment": rollback_deployment,
        }

    def get_tools(self) -> Dict[str, Callable]:
        """登録されているツールを返す"""
        return self._tools

    def get_tool_schemas(self) -> Dict[str, Dict[str, Any]]:
        """
        各ツールのスキーマを返す

        Returns:
            ツール名をキーとしたスキーマ辞書
        """
        return {
            "deploy_to_sagemaker": {
                "name": "deploy_to_sagemaker",
                "description": "SageMakerエンドポイントにモデルをデプロイ",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "model_s3_uri": {
                            "type": "string",
                            "description": "モデルデータのS3 URI",
                        },
                        "endpoint_name": {
                            "type": "string",
                            "description": "エンドポイント名",
                        },
                        "instance_type": {
                            "type": "string",
                            "description": "インスタンスタイプ",
                        },
                        "instance_count": {
                            "type": "integer",
                            "description": "インスタンス数",
                        },
                        "model_name": {
                            "type": "string",
                            "description": "モデル名",
                        },
                        "wait_for_completion": {
                            "type": "boolean",
                            "description": "デプロイ完了まで待機するか",
                        },
                    },
                    "required": ["model_s3_uri", "endpoint_name"],
                },
            },
            "update_endpoint_traffic": {
                "name": "update_endpoint_traffic",
                "description": "エンドポイントのトラフィック配分を更新（カナリアデプロイ）",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "endpoint_name": {
                            "type": "string",
                            "description": "エンドポイント名",
                        },
                        "variant_weights": {
                            "type": "object",
                            "description": "バリアント名と重みの辞書",
                        },
                    },
                    "required": ["endpoint_name", "variant_weights"],
                },
            },
            "update_endpoint_capacity": {
                "name": "update_endpoint_capacity",
                "description": "エンドポイントのインスタンス数を更新",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "endpoint_name": {
                            "type": "string",
                            "description": "エンドポイント名",
                        },
                        "variant_name": {
                            "type": "string",
                            "description": "バリアント名",
                        },
                        "instance_count": {
                            "type": "integer",
                            "description": "インスタンス数",
                        },
                    },
                    "required": ["endpoint_name", "variant_name", "instance_count"],
                },
            },
            "configure_autoscaling": {
                "name": "configure_autoscaling",
                "description": "エンドポイントのオートスケーリングを設定",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "endpoint_name": {
                            "type": "string",
                            "description": "エンドポイント名",
                        },
                        "variant_name": {
                            "type": "string",
                            "description": "バリアント名",
                        },
                        "min_capacity": {
                            "type": "integer",
                            "description": "最小インスタンス数",
                        },
                        "max_capacity": {
                            "type": "integer",
                            "description": "最大インスタンス数",
                        },
                        "target_metric": {
                            "type": "string",
                            "description": "ターゲットメトリクス",
                        },
                        "target_value": {
                            "type": "number",
                            "description": "ターゲット値",
                        },
                    },
                    "required": ["endpoint_name", "min_capacity", "max_capacity"],
                },
            },
            "delete_autoscaling": {
                "name": "delete_autoscaling",
                "description": "エンドポイントのオートスケーリング設定を削除",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "endpoint_name": {
                            "type": "string",
                            "description": "エンドポイント名",
                        },
                        "variant_name": {
                            "type": "string",
                            "description": "バリアント名",
                        },
                    },
                    "required": ["endpoint_name"],
                },
            },
            "monitor_endpoint": {
                "name": "monitor_endpoint",
                "description": "エンドポイントのステータスとメトリクスを監視",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "endpoint_name": {
                            "type": "string",
                            "description": "エンドポイント名",
                        },
                        "include_metrics": {
                            "type": "boolean",
                            "description": "メトリクスを含めるか",
                        },
                        "metric_period_minutes": {
                            "type": "integer",
                            "description": "メトリクス取得期間（分）",
                        },
                    },
                    "required": ["endpoint_name"],
                },
            },
            "health_check_endpoint": {
                "name": "health_check_endpoint",
                "description": "エンドポイントのヘルスチェックを実行",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "endpoint_name": {
                            "type": "string",
                            "description": "エンドポイント名",
                        },
                        "test_payload": {
                            "type": "object",
                            "description": "テストペイロード",
                        },
                    },
                    "required": ["endpoint_name"],
                },
            },
            "delete_endpoint": {
                "name": "delete_endpoint",
                "description": "エンドポイントを削除",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "endpoint_name": {
                            "type": "string",
                            "description": "エンドポイント名",
                        },
                        "delete_endpoint_config": {
                            "type": "boolean",
                            "description": "エンドポイント設定も削除するか",
                        },
                        "delete_model": {
                            "type": "boolean",
                            "description": "モデルも削除するか",
                        },
                    },
                    "required": ["endpoint_name"],
                },
            },
            "rollback_deployment": {
                "name": "rollback_deployment",
                "description": "デプロイメントをロールバック",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "endpoint_name": {
                            "type": "string",
                            "description": "エンドポイント名",
                        },
                        "previous_config_name": {
                            "type": "string",
                            "description": "ロールバック先の設定名",
                        },
                    },
                    "required": ["endpoint_name"],
                },
            },
        }
