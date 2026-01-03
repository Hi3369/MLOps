"""ML Evaluation Capability実装"""
import logging
from typing import Any, Callable, Dict

from .tools import evaluate_classification, evaluate_clustering, evaluate_regression

logger = logging.getLogger(__name__)


class MLEvaluationCapability:
    """機械学習モデル評価"""

    def __init__(self):
        """Capabilityの初期化"""
        logger.info("Initializing ML Evaluation Capability")
        self._tools = self._register_tools()

    def _register_tools(self) -> Dict[str, Callable]:
        """ツールの登録"""
        return {
            "evaluate_classification": evaluate_classification,
            "evaluate_regression": evaluate_regression,
            "evaluate_clustering": evaluate_clustering,
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
            "evaluate_classification": {
                "name": "evaluate_classification",
                "description": "分類モデルを評価 (accuracy, precision, recall, F1, confusion matrix)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "model_s3_uri": {
                            "type": "string",
                            "description": "モデルのS3 URI (.pkl)",
                        },
                        "test_data_s3_uri": {
                            "type": "string",
                            "description": "テストデータのS3 URI (前処理済みデータ)",
                        },
                        "file_format": {
                            "type": "string",
                            "description": "ファイルフォーマット (csv, parquet)",
                        },
                        "average": {
                            "type": "string",
                            "description": "マルチクラス評価の平均方法",
                            "enum": ["weighted", "macro", "micro"],
                        },
                    },
                    "required": ["model_s3_uri", "test_data_s3_uri"],
                },
            },
            "evaluate_regression": {
                "name": "evaluate_regression",
                "description": "回帰モデルを評価 (R², MAE, MSE, RMSE)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "model_s3_uri": {
                            "type": "string",
                            "description": "モデルのS3 URI (.pkl)",
                        },
                        "test_data_s3_uri": {
                            "type": "string",
                            "description": "テストデータのS3 URI (前処理済みデータ)",
                        },
                        "file_format": {
                            "type": "string",
                            "description": "ファイルフォーマット (csv, parquet)",
                        },
                    },
                    "required": ["model_s3_uri", "test_data_s3_uri"],
                },
            },
            "evaluate_clustering": {
                "name": "evaluate_clustering",
                "description": "クラスタリングモデルを評価 (silhouette score, Davies-Bouldin index)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "model_s3_uri": {
                            "type": "string",
                            "description": "モデルのS3 URI (.pkl)",
                        },
                        "test_data_s3_uri": {
                            "type": "string",
                            "description": "テストデータのS3 URI",
                        },
                        "file_format": {
                            "type": "string",
                            "description": "ファイルフォーマット (csv, parquet)",
                        },
                    },
                    "required": ["model_s3_uri", "test_data_s3_uri"],
                },
            },
        }
