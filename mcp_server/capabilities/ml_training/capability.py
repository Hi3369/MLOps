"""ML Training Capability実装"""
import logging
from typing import Any, Callable, Dict

from .tools import train_classification, train_clustering, train_regression

logger = logging.getLogger(__name__)


class MLTrainingCapability:
    """機械学習モデル学習"""

    def __init__(self):
        """Capabilityの初期化"""
        logger.info("Initializing ML Training Capability")
        self._tools = self._register_tools()

    def _register_tools(self) -> Dict[str, Callable]:
        """ツールの登録"""
        return {
            "train_classification": train_classification,
            "train_regression": train_regression,
            "train_clustering": train_clustering,
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
            "train_classification": {
                "name": "train_classification",
                "description": "分類モデルを学習 (Random Forest, Logistic Regression, Neural Network)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "train_data_s3_uri": {
                            "type": "string",
                            "description": "学習データのS3 URI (前処理済みデータ)",
                        },
                        "algorithm": {
                            "type": "string",
                            "description": "アルゴリズム",
                            "enum": [
                                "random_forest",
                                "logistic_regression",
                                "neural_network",
                            ],
                        },
                        "hyperparameters": {
                            "type": "object",
                            "description": "ハイパーパラメータ辞書",
                        },
                        "model_output_s3_uri": {
                            "type": "string",
                            "description": "モデル保存先S3 URI",
                        },
                        "file_format": {
                            "type": "string",
                            "description": "ファイルフォーマット (csv, parquet)",
                        },
                    },
                    "required": ["train_data_s3_uri", "model_output_s3_uri"],
                },
            },
            "train_regression": {
                "name": "train_regression",
                "description": "回帰モデルを学習 (Random Forest, Linear Regression, Ridge, Neural Network)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "train_data_s3_uri": {
                            "type": "string",
                            "description": "学習データのS3 URI (前処理済みデータ)",
                        },
                        "algorithm": {
                            "type": "string",
                            "description": "アルゴリズム",
                            "enum": [
                                "random_forest",
                                "linear_regression",
                                "ridge",
                                "neural_network",
                            ],
                        },
                        "hyperparameters": {
                            "type": "object",
                            "description": "ハイパーパラメータ辞書",
                        },
                        "model_output_s3_uri": {
                            "type": "string",
                            "description": "モデル保存先S3 URI",
                        },
                        "file_format": {
                            "type": "string",
                            "description": "ファイルフォーマット (csv, parquet)",
                        },
                    },
                    "required": ["train_data_s3_uri", "model_output_s3_uri"],
                },
            },
            "train_clustering": {
                "name": "train_clustering",
                "description": "クラスタリングモデルを学習 (KMeans, DBSCAN, PCA)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "train_data_s3_uri": {
                            "type": "string",
                            "description": "学習データのS3 URI",
                        },
                        "algorithm": {
                            "type": "string",
                            "description": "アルゴリズム",
                            "enum": ["kmeans", "dbscan", "pca"],
                        },
                        "hyperparameters": {
                            "type": "object",
                            "description": "ハイパーパラメータ辞書",
                        },
                        "model_output_s3_uri": {
                            "type": "string",
                            "description": "モデル保存先S3 URI",
                        },
                        "file_format": {
                            "type": "string",
                            "description": "ファイルフォーマット (csv, parquet)",
                        },
                    },
                    "required": ["train_data_s3_uri", "model_output_s3_uri"],
                },
            },
        }
