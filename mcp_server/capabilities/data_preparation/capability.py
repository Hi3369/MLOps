"""Data Preparation Capability実装"""
from typing import Any, List

from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

from ..base import BaseCapability


class DataPreparationCapability(BaseCapability):
    """データ前処理・特徴量エンジニアリング"""

    def list_tools(self) -> List[Tool]:
        """提供ツール一覧"""
        return [
            Tool(
                name="load_dataset",
                description="S3からデータセットを読み込む",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "s3_uri": {"type": "string", "description": "S3 URI (s3://bucket/key)"},
                        "file_format": {"type": "string", "enum": ["csv", "parquet", "json"], "default": "csv"},
                    },
                    "required": ["s3_uri"],
                },
            ),
            Tool(
                name="validate_data",
                description="データのバリデーション（欠損値、型チェック等）",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "data_s3_uri": {"type": "string"},
                        "schema": {"type": "object", "description": "期待されるスキーマ"},
                    },
                    "required": ["data_s3_uri"],
                },
            ),
            Tool(
                name="preprocess_supervised",
                description="教師あり学習用の前処理",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "dataset_s3_uri": {"type": "string"},
                        "target_column": {"type": "string"},
                        "task_type": {"type": "string", "enum": ["classification", "regression"]},
                        "preprocessing_config": {
                            "type": "object",
                            "properties": {
                                "normalize": {"type": "boolean", "default": True},
                                "handle_missing": {"type": "string", "enum": ["drop", "mean", "median", "mode"], "default": "mean"},
                                "encode_categorical": {"type": "boolean", "default": True},
                            },
                        },
                    },
                    "required": ["dataset_s3_uri", "target_column", "task_type"],
                },
            ),
            Tool(
                name="preprocess_unsupervised",
                description="教師なし学習用の前処理",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "dataset_s3_uri": {"type": "string"},
                        "preprocessing_config": {"type": "object"},
                    },
                    "required": ["dataset_s3_uri"],
                },
            ),
            Tool(
                name="preprocess_reinforcement",
                description="強化学習用の環境データ準備",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "env_name": {"type": "string"},
                        "env_config": {"type": "object"},
                    },
                    "required": ["env_name"],
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
                text=f"Data Preparation tool '{tool_name}' executed (stub implementation)"
            )
        ]
