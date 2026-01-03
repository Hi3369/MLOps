"""Model Registry Capability実装"""
import logging
from typing import Any, Callable, Dict

from .tools import delete_model, get_model, list_models, register_model, update_model_status

logger = logging.getLogger(__name__)


class ModelRegistryCapability:
    """モデルレジストリ管理"""

    def __init__(self):
        """Capabilityの初期化"""
        logger.info("Initializing Model Registry Capability")
        self._tools = self._register_tools()

    def _register_tools(self) -> Dict[str, Callable]:
        """ツールの登録"""
        return {
            "register_model": register_model,
            "list_models": list_models,
            "get_model": get_model,
            "update_model_status": update_model_status,
            "delete_model": delete_model,
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
            "register_model": {
                "name": "register_model",
                "description": "モデルをレジストリに登録 (metadata, tags付き)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "model_s3_uri": {
                            "type": "string",
                            "description": "モデルのS3 URI (.pkl)",
                        },
                        "model_name": {
                            "type": "string",
                            "description": "モデル名",
                        },
                        "model_version": {
                            "type": "string",
                            "description": "モデルバージョン (省略時は自動生成)",
                        },
                        "metadata": {
                            "type": "object",
                            "description": "モデルメタデータ (algorithm, hyperparameters, metrics等)",
                        },
                        "tags": {
                            "type": "object",
                            "description": "モデルタグ",
                        },
                    },
                    "required": ["model_s3_uri", "model_name"],
                },
            },
            "list_models": {
                "name": "list_models",
                "description": "登録されているモデルを一覧表示",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "registry_s3_uri": {
                            "type": "string",
                            "description": "レジストリのS3 URI (s3://bucket/path/)",
                        },
                        "status_filter": {
                            "type": "string",
                            "description": "ステータスフィルタ",
                            "enum": ["registered", "staging", "production", "archived"],
                        },
                    },
                    "required": ["registry_s3_uri"],
                },
            },
            "get_model": {
                "name": "get_model",
                "description": "モデル情報を取得",
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
            "update_model_status": {
                "name": "update_model_status",
                "description": "モデルのステータスを更新 (registered, staging, production, archived)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "model_s3_uri": {
                            "type": "string",
                            "description": "モデルのS3 URI (.pkl)",
                        },
                        "status": {
                            "type": "string",
                            "description": "新しいステータス",
                            "enum": ["registered", "staging", "production", "archived"],
                        },
                    },
                    "required": ["model_s3_uri", "status"],
                },
            },
            "delete_model": {
                "name": "delete_model",
                "description": "モデルを削除",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "model_s3_uri": {
                            "type": "string",
                            "description": "モデルのS3 URI (.pkl)",
                        },
                        "delete_metadata": {
                            "type": "boolean",
                            "description": "メタデータも削除するか",
                        },
                    },
                    "required": ["model_s3_uri"],
                },
            },
        }
