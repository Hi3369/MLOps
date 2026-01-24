"""
Retrain Management Capability

再学習管理機能のCapability実装
再学習トリガー判定・ワークフロー起動・スケジュール設定を提供
"""

import logging
from typing import Any, Callable, Dict

from .tools import (
    check_retrain_triggers,
    create_retrain_issue,
    evaluate_trigger_conditions,
    schedule_periodic_retrain,
    start_retrain_workflow,
)

logger = logging.getLogger(__name__)


class RetrainManagementCapability:
    """
    再学習管理Capability

    以下のツールを提供:
    - check_retrain_triggers: 再学習トリガーチェック
    - evaluate_trigger_conditions: トリガー条件評価
    - create_retrain_issue: 再学習Issue作成
    - start_retrain_workflow: 再学習ワークフロー起動
    - schedule_periodic_retrain: 定期再学習スケジュール設定
    """

    def __init__(self):
        """Capabilityの初期化"""
        self._tools: Dict[str, Callable] = {
            "check_retrain_triggers": check_retrain_triggers,
            "evaluate_trigger_conditions": evaluate_trigger_conditions,
            "create_retrain_issue": create_retrain_issue,
            "start_retrain_workflow": start_retrain_workflow,
            "schedule_periodic_retrain": schedule_periodic_retrain,
        }

        self._tool_schemas: Dict[str, Dict[str, Any]] = {
            "check_retrain_triggers": {
                "name": "check_retrain_triggers",
                "description": "再学習トリガーをチェック（データ変更、コード変更、スケジュール、メトリクス劣化、ドリフト検知）",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "model_name": {
                            "type": "string",
                            "description": "チェック対象のモデル名",
                        },
                        "trigger_config": {
                            "type": "object",
                            "description": "トリガー設定（省略時はデフォルト設定を使用）",
                        },
                    },
                    "required": ["model_name"],
                },
            },
            "evaluate_trigger_conditions": {
                "name": "evaluate_trigger_conditions",
                "description": "トリガー条件を評価（ドリフト閾値、スケジュール式、パフォーマンス閾値）",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "conditions": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "評価する条件のリスト",
                        },
                        "current_metrics": {
                            "type": "object",
                            "description": "現在のメトリクス値",
                        },
                    },
                    "required": ["conditions", "current_metrics"],
                },
            },
            "create_retrain_issue": {
                "name": "create_retrain_issue",
                "description": "再学習リクエストのGitHub Issueを作成",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "model_name": {
                            "type": "string",
                            "description": "モデル名",
                        },
                        "reason": {
                            "type": "string",
                            "enum": [
                                "data_change",
                                "code_change",
                                "schedule",
                                "metrics_degradation",
                                "drift_detection",
                                "manual",
                            ],
                            "description": "再学習理由",
                        },
                        "trigger_details": {
                            "type": "object",
                            "description": "トリガー詳細情報",
                        },
                        "repo_owner": {
                            "type": "string",
                            "description": "リポジトリオーナー（省略時は環境変数から取得）",
                        },
                        "repo_name": {
                            "type": "string",
                            "description": "リポジトリ名（省略時は環境変数から取得）",
                        },
                    },
                    "required": ["model_name", "reason"],
                },
            },
            "start_retrain_workflow": {
                "name": "start_retrain_workflow",
                "description": "再学習ワークフローをStep Functionsで起動",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "workflow_name": {
                            "type": "string",
                            "description": "ワークフロー名",
                        },
                        "model_config": {
                            "type": "object",
                            "description": "モデル設定（model_name, model_type, hyperparameters等）",
                        },
                        "dataset_uri": {
                            "type": "string",
                            "description": "データセットURI（S3パス）",
                        },
                        "comparison_config": {
                            "type": "object",
                            "description": "新旧モデル比較設定（metrics_to_compare, improvement_threshold等）",
                        },
                    },
                    "required": ["workflow_name", "model_config"],
                },
            },
            "schedule_periodic_retrain": {
                "name": "schedule_periodic_retrain",
                "description": "定期再学習スケジュールをEventBridgeで設定",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "model_name": {
                            "type": "string",
                            "description": "モデル名",
                        },
                        "schedule_expression": {
                            "type": "string",
                            "description": "cron式またはrate式（例: cron(0 0 * * ? *), rate(7 days)）",
                        },
                        "config": {
                            "type": "object",
                            "description": "再学習設定（workflow_name, model_config, dataset_uri等）",
                        },
                    },
                    "required": ["model_name", "schedule_expression"],
                },
            },
        }

        logger.info("RetrainManagementCapability initialized with 5 tools")

    def get_tools(self) -> Dict[str, Callable]:
        """
        ツール関数のマッピングを返す

        Returns:
            ツール名から関数へのマッピング辞書
        """
        return self._tools

    def get_tool_schemas(self) -> Dict[str, Dict[str, Any]]:
        """
        ツールスキーマのマッピングを返す

        Returns:
            ツール名からスキーマ辞書へのマッピング
        """
        return self._tool_schemas
