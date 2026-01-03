"""Model Packaging Capability実装"""
import logging
from typing import Any, Callable, Dict

from .tools import (
    create_dockerfile,
    create_model_package,
    extract_model_metadata,
    generate_deployment_config,
    validate_package,
)

logger = logging.getLogger(__name__)


class ModelPackagingCapability:
    """モデルパッケージング管理"""

    def __init__(self):
        """Capabilityの初期化"""
        logger.info("Initializing Model Packaging Capability")
        self._tools = self._register_tools()

    def _register_tools(self) -> Dict[str, Callable]:
        """ツールの登録"""
        return {
            "create_model_package": create_model_package,
            "create_dockerfile": create_dockerfile,
            "validate_package": validate_package,
            "generate_deployment_config": generate_deployment_config,
            "extract_model_metadata": extract_model_metadata,
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
            "create_model_package": {
                "name": "create_model_package",
                "description": "モデルをデプロイ可能なパッケージに変換 (tar.gz)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "model_s3_uri": {
                            "type": "string",
                            "description": "モデルのS3 URI (.pkl)",
                        },
                        "package_name": {
                            "type": "string",
                            "description": "パッケージ名",
                        },
                        "framework": {
                            "type": "string",
                            "description": "フレームワーク",
                            "enum": ["sklearn", "tensorflow", "pytorch"],
                        },
                        "python_version": {
                            "type": "string",
                            "description": "Pythonバージョン",
                        },
                        "dependencies": {
                            "type": "object",
                            "description": "依存パッケージ辞書",
                        },
                        "output_s3_uri": {
                            "type": "string",
                            "description": "出力先S3 URI",
                        },
                    },
                    "required": ["model_s3_uri", "package_name"],
                },
            },
            "create_dockerfile": {
                "name": "create_dockerfile",
                "description": "モデル用のDockerfileを生成",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "model_s3_uri": {
                            "type": "string",
                            "description": "モデルのS3 URI",
                        },
                        "framework": {
                            "type": "string",
                            "description": "フレームワーク",
                            "enum": ["sklearn", "tensorflow", "pytorch"],
                        },
                        "python_version": {
                            "type": "string",
                            "description": "Pythonバージョン",
                        },
                        "base_image": {
                            "type": "string",
                            "description": "ベースイメージ",
                        },
                        "optimize": {
                            "type": "boolean",
                            "description": "最適化を有効にするか",
                        },
                    },
                    "required": ["model_s3_uri"],
                },
            },
            "validate_package": {
                "name": "validate_package",
                "description": "モデルパッケージを検証",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "package_s3_uri": {
                            "type": "string",
                            "description": "パッケージのS3 URI (.tar.gz)",
                        },
                    },
                    "required": ["package_s3_uri"],
                },
            },
            "generate_deployment_config": {
                "name": "generate_deployment_config",
                "description": "デプロイ設定を生成 (SageMaker, ECS, Lambda)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "model_s3_uri": {
                            "type": "string",
                            "description": "モデルのS3 URI",
                        },
                        "deployment_type": {
                            "type": "string",
                            "description": "デプロイタイプ",
                            "enum": ["sagemaker", "ecs", "lambda"],
                        },
                        "instance_type": {
                            "type": "string",
                            "description": "インスタンスタイプ",
                        },
                        "instance_count": {
                            "type": "integer",
                            "description": "インスタンス数",
                        },
                        "auto_scaling": {
                            "type": "boolean",
                            "description": "オートスケーリングを有効にするか",
                        },
                    },
                    "required": ["model_s3_uri"],
                },
            },
            "extract_model_metadata": {
                "name": "extract_model_metadata",
                "description": "モデルからメタデータを抽出",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "model_s3_uri": {
                            "type": "string",
                            "description": "モデルのS3 URI (.pkl)",
                        },
                    },
                    "required": ["model_s3_uri"],
                },
            },
        }
