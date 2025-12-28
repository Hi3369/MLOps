"""ML Evaluation Capability実装"""
from typing import Any, List

from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

from ..base import BaseCapability


class MLEvaluationCapability(BaseCapability):
    """機械学習モデル評価"""

    def list_tools(self) -> List[Tool]:
        """提供ツール一覧"""
        return [
            Tool(
                name="evaluate_classifier",
                description="分類モデルを評価",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "model_s3_uri": {"type": "string"},
                        "test_data_s3_uri": {"type": "string"},
                        "target_column": {"type": "string"},
                    },
                    "required": ["model_s3_uri", "test_data_s3_uri", "target_column"],
                },
            ),
            Tool(
                name="evaluate_regressor",
                description="回帰モデルを評価",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "model_s3_uri": {"type": "string"},
                        "test_data_s3_uri": {"type": "string"},
                        "target_column": {"type": "string"},
                    },
                    "required": ["model_s3_uri", "test_data_s3_uri", "target_column"],
                },
            ),
            Tool(
                name="evaluate_clustering",
                description="クラスタリングモデルを評価",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "model_s3_uri": {"type": "string"},
                        "test_data_s3_uri": {"type": "string"},
                    },
                    "required": ["model_s3_uri", "test_data_s3_uri"],
                },
            ),
            Tool(
                name="evaluate_reinforcement",
                description="強化学習モデルを評価",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "model_s3_uri": {"type": "string"},
                        "env_name": {"type": "string"},
                        "num_episodes": {"type": "integer", "default": 100},
                    },
                    "required": ["model_s3_uri", "env_name"],
                },
            ),
        ]

    async def execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any]
    ) -> List[TextContent | ImageContent | EmbeddedResource]:
        """ツール実行"""
        # TODO: 実装
        return [
            TextContent(
                type="text",
                text=f"ML Evaluation tool '{tool_name}' executed (stub implementation)"
            )
        ]
