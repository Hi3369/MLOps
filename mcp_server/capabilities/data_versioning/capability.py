"""Data Versioning Capability実装"""

import logging
from typing import Any, Callable, Dict

from .tools import compare_datasets, get_dataset_lineage, version_dataset

logger = logging.getLogger(__name__)


class DataVersioningCapability:
    """データバージョニング管理"""

    def __init__(self):
        """Capabilityの初期化"""
        logger.info("Initializing Data Versioning Capability")
        self._tools: Dict[str, Callable] = {
            "version_dataset": version_dataset,
            "get_dataset_lineage": get_dataset_lineage,
            "compare_datasets": compare_datasets,
        }
        self._tool_schemas = self._build_tool_schemas()
        logger.info(f"DataVersioningCapability initialized with " f"{len(self._tools)} tools")

    def _build_tool_schemas(self) -> Dict[str, Dict[str, Any]]:
        """ツールスキーマを構築"""
        return {
            "version_dataset": {
                "name": "version_dataset",
                "description": "データセットのバージョンを登録する",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "dataset_name": {
                            "type": "string",
                            "description": "データセット名",
                        },
                        "s3_uri": {
                            "type": "string",
                            "description": "データセットのS3 URI",
                        },
                        "version": {
                            "type": "string",
                            "description": "バージョン文字列",
                        },
                        "description": {
                            "type": "string",
                            "description": "バージョンの説明",
                        },
                        "schema": {
                            "type": "object",
                            "description": "スキーマ定義",
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "タグリスト",
                        },
                        "parent_version": {
                            "type": "string",
                            "description": "親バージョン",
                        },
                        "row_count": {
                            "type": "integer",
                            "description": "行数",
                        },
                        "file_format": {
                            "type": "string",
                            "description": "ファイル形式",
                            "enum": ["csv", "parquet", "json", "orc", "avro"],
                        },
                        "metadata": {
                            "type": "object",
                            "description": "追加メタデータ",
                        },
                    },
                    "required": ["dataset_name", "s3_uri", "version"],
                },
            },
            "get_dataset_lineage": {
                "name": "get_dataset_lineage",
                "description": "データセットの系譜（リネージ）を取得する",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "dataset_name": {
                            "type": "string",
                            "description": "データセット名",
                        },
                        "version": {
                            "type": "string",
                            "description": "特定バージョン",
                        },
                        "depth": {
                            "type": "integer",
                            "description": "遡る深さ",
                        },
                        "include_transformations": {
                            "type": "boolean",
                            "description": "変換処理情報を含めるか",
                        },
                    },
                    "required": ["dataset_name"],
                },
            },
            "compare_datasets": {
                "name": "compare_datasets",
                "description": "2つのデータセットバージョンを比較する",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "dataset_name": {
                            "type": "string",
                            "description": "データセット名",
                        },
                        "version_a": {
                            "type": "string",
                            "description": "比較元バージョン",
                        },
                        "version_b": {
                            "type": "string",
                            "description": "比較先バージョン",
                        },
                        "compare_schema": {
                            "type": "boolean",
                            "description": "スキーマ比較を行うか",
                        },
                        "compare_statistics": {
                            "type": "boolean",
                            "description": "統計情報比較を行うか",
                        },
                        "compare_sample": {
                            "type": "boolean",
                            "description": "サンプルデータ比較を行うか",
                        },
                        "sample_size": {
                            "type": "integer",
                            "description": "サンプルサイズ",
                        },
                    },
                    "required": ["dataset_name", "version_a", "version_b"],
                },
            },
        }

    def get_tools(self) -> Dict[str, Callable]:
        """登録されているツールを返す"""
        return self._tools

    def get_tool_schemas(self) -> Dict[str, Dict[str, Any]]:
        """各ツールのスキーマを返す"""
        return self._tool_schemas
