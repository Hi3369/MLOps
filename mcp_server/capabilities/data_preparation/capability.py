"""
Data Preparation Capability Implementation

データ前処理・特徴量エンジニアリングのツールを提供します。
"""

import logging
from typing import Any, Callable, Dict

logger = logging.getLogger(__name__)


class DataPreparationCapability:
    """
    Data Preparation Capability

    提供ツール:
    - load_dataset: S3からデータセット読み込み
    - validate_data: データバリデーション
    - preprocess_supervised: 教師あり学習用前処理
    """

    def __init__(self):
        """Capabilityの初期化"""
        logger.info("Initializing Data Preparation Capability")
        self._tools = self._register_tools()

    def _register_tools(self) -> Dict[str, Callable]:
        """ツールの登録"""
        from .tools import load_dataset, preprocess_supervised, validate_data

        return {
            "load_dataset": load_dataset.load_dataset,
            "validate_data": validate_data.validate_data,
            "preprocess_supervised": preprocess_supervised.preprocess_supervised,
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
            "load_dataset": {
                "name": "load_dataset",
                "description": "S3からデータセットを読み込む",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "bucket": {"type": "string", "description": "S3バケット名"},
                        "key": {"type": "string", "description": "S3オブジェクトキー"},
                    },
                    "required": ["bucket", "key"],
                },
            },
            "validate_data": {
                "name": "validate_data",
                "description": "データのバリデーションを実行",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "object",
                            "description": "検証するデータ",
                        },
                    },
                    "required": ["data"],
                },
            },
            "preprocess_supervised": {
                "name": "preprocess_supervised",
                "description": "教師あり学習用のデータ前処理",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "data": {"type": "object", "description": "前処理するデータ"},
                        "target_column": {
                            "type": "string",
                            "description": "ターゲット列名",
                        },
                    },
                    "required": ["data", "target_column"],
                },
            },
        }
