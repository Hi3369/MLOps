"""Model Registry Capability実装"""
from typing import Any, List

from mcp.types import EmbeddedResource, ImageContent, TextContent, Tool

from ..base import BaseCapability


class ModelRegistryCapability(BaseCapability):
    """モデルレジストリ管理"""

    def list_tools(self) -> List[Tool]:
        """提供ツール一覧"""
        return [
            Tool(
                name="register_model",
                description="モデルをSageMaker Model Registryに登録",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "model_package_group_name": {"type": "string"},
                        "model_s3_uri": {"type": "string"},
                        "evaluation_metrics": {"type": "object"},
                        "model_approval_status": {
                            "type": "string",
                            "enum": ["PendingManualApproval", "Approved", "Rejected"],
                            "default": "PendingManualApproval",
                        },
                    },
                    "required": [
                        "model_package_group_name",
                        "model_s3_uri",
                        "evaluation_metrics",
                    ],
                },
            ),
            Tool(
                name="update_model_approval_status",
                description="モデルの承認ステータスを更新",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "model_package_arn": {"type": "string"},
                        "approval_status": {
                            "type": "string",
                            "enum": ["Approved", "Rejected"],
                        },
                    },
                    "required": ["model_package_arn", "approval_status"],
                },
            ),
            Tool(
                name="rollback_model",
                description="前バージョンのモデルにロールバック",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "model_package_group_name": {"type": "string"},
                        "rollback_to_version": {"type": "integer"},
                    },
                    "required": ["model_package_group_name", "rollback_to_version"],
                },
            ),
            Tool(
                name="list_models",
                description="登録されているモデルを一覧表示",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "model_package_group_name": {"type": "string"},
                    },
                    "required": ["model_package_group_name"],
                },
            ),
        ]

    async def execute_tool(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> List[TextContent | ImageContent | EmbeddedResource]:
        """ツール実行"""
        # TODO: 実装
        return [
            TextContent(
                type="text",
                text=f"Model Registry tool '{tool_name}' executed (stub implementation)",
            )
        ]
