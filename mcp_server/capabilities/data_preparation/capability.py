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
        return dict(self._tools)

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
                        "s3_uri": {
                            "type": "string",
                            "description": "S3 URI (例: s3://bucket-name/path/to/file.csv)",
                        },
                        "file_format": {
                            "type": "string",
                            "enum": ["csv", "parquet", "json"],
                            "description": "ファイルフォーマット",
                            "default": "csv",
                        },
                    },
                    "required": ["s3_uri"],
                },
            },
            "validate_data": {
                "name": "validate_data",
                "description": "データのバリデーションを実行",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "s3_uri": {
                            "type": "string",
                            "description": "S3 URI (例: s3://bucket-name/path/to/file.csv)",
                        },
                        "file_format": {
                            "type": "string",
                            "enum": ["csv", "parquet", "json"],
                            "description": "ファイルフォーマット",
                            "default": "csv",
                        },
                        "required_columns": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "必須カラムのリスト",
                        },
                        "max_missing_ratio": {
                            "type": "number",
                            "description": "許容する欠損値の割合 (0.0-1.0)",
                            "default": 0.5,
                        },
                    },
                    "required": ["s3_uri"],
                },
            },
            "preprocess_supervised": {
                "name": "preprocess_supervised",
                "description": "教師あり学習用のデータ前処理",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "s3_uri": {
                            "type": "string",
                            "description": "S3 URI (例: s3://bucket-name/path/to/file.csv)",
                        },
                        "target_column": {
                            "type": "string",
                            "description": "ターゲット列名",
                        },
                        "task_type": {
                            "type": "string",
                            "enum": ["classification", "regression"],
                            "description": "タスクタイプ",
                            "default": "classification",
                        },
                        "file_format": {
                            "type": "string",
                            "enum": ["csv", "parquet", "json"],
                            "description": "入力ファイルフォーマット",
                            "default": "csv",
                        },
                        "test_size": {
                            "type": "number",
                            "description": "テストデータの割合 (0.0-1.0)",
                            "default": 0.2,
                        },
                        "normalize": {
                            "type": "boolean",
                            "description": "数値変数を正規化するか",
                            "default": True,
                        },
                        "handle_missing": {
                            "type": "string",
                            "enum": ["drop", "mean", "median", "mode"],
                            "description": "欠損値の処理方法",
                            "default": "drop",
                        },
                        "encode_categorical": {
                            "type": "boolean",
                            "description": "カテゴリ変数をエンコードするか",
                            "default": True,
                        },
                        "output_s3_uri": {
                            "type": "string",
                            "description": "出力先S3 URI (省略時は自動生成)",
                        },
                        "output_format": {
                            "type": "string",
                            "enum": ["csv", "parquet"],
                            "description": "出力ファイルフォーマット",
                            "default": "csv",
                        },
                        "random_state": {
                            "type": "integer",
                            "description": "乱数シード（再現性確保用）",
                            "default": 42,
                        },
                    },
                    "required": ["s3_uri", "target_column"],
                },
            },
        }
