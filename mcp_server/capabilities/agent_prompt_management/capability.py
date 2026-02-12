"""
Agent Prompt Management Capability

エージェンティック動作のためのLLMプロンプト管理Capability
プロンプトテンプレートの適用・一覧取得・変数検証を提供する
"""

import logging
from typing import Any, Callable, Dict

from .tools import (
    apply_agent_prompt,
    list_agent_prompts,
    validate_prompt_variables,
)

logger = logging.getLogger(__name__)


class AgentPromptManagementCapability:
    """
    エージェントプロンプト管理Capability

    以下のツールを提供:
    - apply_agent_prompt: プロンプトに変数を適用してLLM用テキストを生成
    - list_agent_prompts: 利用可能なプロンプト一覧と必要変数を取得
    - validate_prompt_variables: プロンプト適用前に変数の妥当性を検証
    """

    def __init__(self):
        """Capabilityの初期化"""
        self._tools: Dict[str, Callable] = {
            "apply_agent_prompt": apply_agent_prompt,
            "list_agent_prompts": list_agent_prompts,
            "validate_prompt_variables": validate_prompt_variables,
        }

        self._tool_schemas: Dict[str, Dict[str, Any]] = {
            "apply_agent_prompt": {
                "name": "apply_agent_prompt",
                "description": (
                    "エージェント用LLMプロンプトに変数を適用し、"
                    "レンダリング済みプロンプト文字列を生成します"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt_name": {
                            "type": "string",
                            "description": (
                                "プロンプト名（例: judge_agent_system, "
                                "issue_detector_system, "
                                "training_orchestrator_system）"
                            ),
                        },
                        "variables": {
                            "type": "object",
                            "description": "テンプレート変数の辞書",
                        },
                        "include_defaults": {
                            "type": "boolean",
                            "description": "デフォルト値を使用するか",
                            "default": True,
                        },
                        "agent_context": {
                            "type": "object",
                            "description": ("追加コンテキスト情報" "（実行時メタデータ等）"),
                        },
                    },
                    "required": ["prompt_name", "variables"],
                },
            },
            "list_agent_prompts": {
                "name": "list_agent_prompts",
                "description": (
                    "利用可能なエージェントプロンプト一覧と" "必要変数情報を取得します"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "agent_type": {
                            "type": "string",
                            "enum": [
                                "judge",
                                "issue_detector",
                                "orchestrator",
                            ],
                            "description": ("エージェントタイプでフィルタ"),
                        },
                        "include_variables": {
                            "type": "boolean",
                            "description": "変数情報を含めるか",
                            "default": True,
                        },
                    },
                },
            },
            "validate_prompt_variables": {
                "name": "validate_prompt_variables",
                "description": ("プロンプト適用前に変数の妥当性を検証します"),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt_name": {
                            "type": "string",
                            "description": "プロンプト名",
                        },
                        "variables": {
                            "type": "object",
                            "description": "検証する変数辞書",
                        },
                        "strict": {
                            "type": "boolean",
                            "description": ("厳密モード（デフォルト値がある" "変数も必須とする）"),
                            "default": False,
                        },
                    },
                    "required": ["prompt_name", "variables"],
                },
            },
        }

        logger.info("AgentPromptManagementCapability initialized with 3 tools")

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
