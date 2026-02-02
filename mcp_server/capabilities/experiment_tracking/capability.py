"""Experiment Tracking Capability実装"""

import logging
from typing import Any, Callable, Dict

from .tools import (
    compare_experiments,
    log_metrics,
    log_parameters,
    start_experiment,
)

logger = logging.getLogger(__name__)


class ExperimentTrackingCapability:
    """実験追跡管理"""

    def __init__(self):
        """Capabilityの初期化"""
        logger.info("Initializing Experiment Tracking Capability")
        self._tools: Dict[str, Callable] = {
            "start_experiment": start_experiment,
            "log_parameters": log_parameters,
            "log_metrics": log_metrics,
            "compare_experiments": compare_experiments,
        }
        self._tool_schemas = self._build_tool_schemas()
        logger.info(f"ExperimentTrackingCapability initialized with " f"{len(self._tools)} tools")

    def _build_tool_schemas(self) -> Dict[str, Dict[str, Any]]:
        """ツールスキーマを構築"""
        return {
            "start_experiment": {
                "name": "start_experiment",
                "description": "新しい実験を開始する",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "experiment_name": {
                            "type": "string",
                            "description": "実験名",
                        },
                        "description": {
                            "type": "string",
                            "description": "実験の説明",
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "タグリスト",
                        },
                        "metadata": {
                            "type": "object",
                            "description": "メタデータ辞書",
                        },
                        "s3_bucket": {
                            "type": "string",
                            "description": "実験データ保存先S3バケット",
                        },
                    },
                    "required": ["experiment_name"],
                },
            },
            "log_parameters": {
                "name": "log_parameters",
                "description": "実験にパラメータを記録する",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "experiment_id": {
                            "type": "string",
                            "description": "実験ID",
                        },
                        "parameters": {
                            "type": "object",
                            "description": "記録するパラメータ辞書",
                        },
                        "run_name": {
                            "type": "string",
                            "description": "実行名",
                        },
                        "step": {
                            "type": "integer",
                            "description": "ステップ番号",
                        },
                    },
                    "required": ["experiment_id", "parameters"],
                },
            },
            "log_metrics": {
                "name": "log_metrics",
                "description": "実験にメトリクスを記録する",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "experiment_id": {
                            "type": "string",
                            "description": "実験ID",
                        },
                        "metrics": {
                            "type": "object",
                            "description": "記録するメトリクス辞書",
                        },
                        "run_name": {
                            "type": "string",
                            "description": "実行名",
                        },
                        "step": {
                            "type": "integer",
                            "description": "ステップ番号",
                        },
                        "epoch": {
                            "type": "integer",
                            "description": "エポック番号",
                        },
                    },
                    "required": ["experiment_id", "metrics"],
                },
            },
            "compare_experiments": {
                "name": "compare_experiments",
                "description": "複数の実験を比較する",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "experiment_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "比較する実験IDのリスト",
                        },
                        "metric_names": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "比較するメトリクス名のリスト",
                        },
                        "sort_by": {
                            "type": "string",
                            "description": "ソート基準のメトリクス名",
                        },
                        "sort_order": {
                            "type": "string",
                            "description": "ソート順序",
                            "enum": ["ascending", "descending"],
                        },
                    },
                    "required": ["experiment_ids"],
                },
            },
        }

    def get_tools(self) -> Dict[str, Callable]:
        """登録されているツールを返す"""
        return dict(self._tools)

    def get_tool_schemas(self) -> Dict[str, Dict[str, Any]]:
        """各ツールのスキーマを返す"""
        return dict(self._tool_schemas)
