"""GitHub Integration Capability実装"""

import logging
from typing import Any, Callable, Dict

from .tools import (
    detect_mlops_issue,
    parse_issue_config,
    start_workflow,
    validate_training_params,
)

logger = logging.getLogger(__name__)


class GitHubIntegrationCapability:
    """GitHub統合・Issue管理・ワークフロー起動"""

    def __init__(self):
        """Capabilityの初期化"""
        logger.info("Initializing GitHub Integration Capability")
        self._tools = self._register_tools()

    def _register_tools(self) -> Dict[str, Callable]:
        """ツールの登録"""
        return {
            "detect_mlops_issue": detect_mlops_issue,
            "parse_issue_config": parse_issue_config,
            "validate_training_params": validate_training_params,
            "start_workflow": start_workflow,
        }

    def get_tools(self) -> Dict[str, Callable]:
        """登録されているツールを返す"""
        return dict(self._tools)

    def get_tool_schemas(self) -> Dict[str, Dict[str, Any]]:
        """
        各ツールのスキーマを返す

        Returns:
            ツールスキーマ辞書
        """
        return {
            "detect_mlops_issue": {
                "name": "detect_mlops_issue",
                "description": "MLOps用Issueを検知",
                "parameters": {
                    "repo_owner": "リポジトリオーナー",
                    "repo_name": "リポジトリ名",
                    "issue_number": "Issue番号（指定時は単一Issue取得）",
                    "labels": "フィルタリングするラベル（mlops, training等）",
                },
            },
            "parse_issue_config": {
                "name": "parse_issue_config",
                "description": "Issue本文からYAML/JSON設定をパース",
                "parameters": {
                    "issue_body": "Issue本文",
                    "config_format": "設定フォーマット（auto, yaml, json）",
                },
            },
            "validate_training_params": {
                "name": "validate_training_params",
                "description": "学習パラメータをバリデーション",
                "parameters": {
                    "training_config": "学習設定（model_type, hyperparameters, dataset等）",
                    "strict": "厳密モード（True: 不明なパラメータをエラーに）",
                },
            },
            "start_workflow": {
                "name": "start_workflow",
                "description": "Step Functionsワークフローを起動",
                "parameters": {
                    "workflow_type": "ワークフロータイプ（training, inference等）",
                    "input_params": "ワークフロー入力パラメータ",
                    "execution_name": "実行名（オプション、未指定時は自動生成）",
                },
            },
        }
