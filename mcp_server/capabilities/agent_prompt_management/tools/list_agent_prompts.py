"""
List Agent Prompts Tool

利用可能なエージェントプロンプト一覧を取得するツール
"""

import logging
import re
from typing import Any, Dict, List, Optional

from .agent_prompts import BUILTIN_AGENT_PROMPTS

logger = logging.getLogger(__name__)


def list_agent_prompts(
    agent_type: Optional[str] = None,
    include_variables: bool = True,
) -> Dict[str, Any]:
    """
    利用可能なエージェントプロンプト一覧を取得

    Args:
        agent_type: エージェントタイプでフィルタ（judge, issue_detector, orchestrator）
        include_variables: 変数情報を含めるか

    Returns:
        プロンプト一覧辞書
    """
    logger.info(f"Listing agent prompts (agent_type={agent_type})")

    try:
        prompts: List[Dict[str, Any]] = []

        for name, template in BUILTIN_AGENT_PROMPTS.items():
            # agent_typeフィルタ
            if agent_type and template.get("agent_type") != agent_type:
                continue

            prompt_info: Dict[str, Any] = {
                "name": name,
                "display_name": template.get("name", name),
                "description": template.get("description", ""),
                "agent_type": template.get("agent_type", "unknown"),
                "has_defaults": "default_values" in template,
            }

            if include_variables:
                # 定義された変数リスト
                defined_vars = template.get("variables", [])

                # プロンプト本文から実際に使用されている変数を抽出
                prompt_text = template.get("prompt", "")
                used_vars = _extract_variables(prompt_text)

                # デフォルト値を持つ変数
                default_vars = list(template.get("default_values", {}).keys())

                # 必須変数（デフォルト値がない変数）
                required_vars = [v for v in defined_vars if v not in default_vars]

                prompt_info["variables"] = {
                    "defined": sorted(defined_vars),
                    "required": sorted(required_vars),
                    "optional": sorted(default_vars),
                    "used_in_prompt": sorted(list(used_vars)),
                }

            prompts.append(prompt_info)

        # エージェントタイプ別のサマリ
        agent_types = list(set(p["agent_type"] for p in prompts))

        return {
            "status": "success",
            "prompts": prompts,
            "total": len(prompts),
            "agent_types": sorted(agent_types),
            "filter_applied": agent_type,
        }

    except Exception as e:
        logger.error(f"Failed to list agent prompts: {e}")
        raise ValueError(f"Failed to list agent prompts: {e}")


def _extract_variables(text: str) -> set:
    """
    テキストからテンプレート変数を抽出

    二重波括弧{{}}内の変数は除外する。

    Args:
        text: プロンプトテキスト

    Returns:
        変数名のセット
    """
    # 二重波括弧を除去してから変数を抽出
    cleaned = text.replace("{{", "").replace("}}", "")
    pattern = r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}"
    return set(re.findall(pattern, cleaned))
