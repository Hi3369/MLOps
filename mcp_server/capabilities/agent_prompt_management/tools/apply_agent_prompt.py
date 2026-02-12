"""
Apply Agent Prompt Tool

エージェント用LLMプロンプトの適用ツール
テンプレート変数を置換し、LLMに渡すプロンプト文字列を生成する
"""

import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .agent_prompts import BUILTIN_AGENT_PROMPTS

logger = logging.getLogger(__name__)


def apply_agent_prompt(
    prompt_name: str,
    variables: Dict[str, Any],
    include_defaults: bool = True,
    agent_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    エージェント用LLMプロンプトを適用

    テンプレート変数を置換し、LLMに渡すプロンプト文字列を生成する。
    デフォルト値が定義されている変数は自動的に補完される。

    Args:
        prompt_name: プロンプト名（judge_agent_system等）
        variables: テンプレート変数の辞書
        include_defaults: デフォルト値を使用するか（デフォルト: True）
        agent_context: 追加コンテキスト情報（実行時メタデータ等）

    Returns:
        適用済みプロンプト辞書
    """
    logger.info(f"Applying agent prompt: {prompt_name}")

    if not prompt_name:
        raise ValueError("prompt_name must not be empty")

    if not isinstance(variables, dict):
        raise ValueError("variables must be a dictionary")

    try:
        # プロンプトテンプレート取得
        if prompt_name not in BUILTIN_AGENT_PROMPTS:
            available = list(BUILTIN_AGENT_PROMPTS.keys())
            raise ValueError(f"Unknown prompt: {prompt_name}. " f"Available prompts: {available}")

        template = BUILTIN_AGENT_PROMPTS[prompt_name]
        prompt_text = template["prompt"]

        # デフォルト値を適用
        merged_variables = {}
        if include_defaults and "default_values" in template:
            merged_variables.update(template["default_values"])
        merged_variables.update(variables)

        # 変数を文字列に変換
        str_variables = {k: str(v) for k, v in merged_variables.items()}

        # プロンプトテキストに変数を適用
        rendered_prompt = _substitute_variables(prompt_text, str_variables)

        # 未置換の変数を検出
        missing_variables = _find_unresolved_variables(rendered_prompt)

        # コンテキスト情報を追加
        context_section = ""
        if agent_context:
            context_section = _build_context_section(agent_context)
            rendered_prompt = rendered_prompt + "\n\n" + context_section

        timestamp = datetime.now(timezone.utc).isoformat()
        request_id = str(uuid4())[:8]

        result: Dict[str, Any] = {
            "status": "success",
            "request_id": request_id,
            "prompt_name": prompt_name,
            "agent_type": template.get("agent_type", "unknown"),
            "rendered_prompt": rendered_prompt,
            "variables_used": sorted(list(str_variables.keys())),
            "missing_variables": missing_variables,
            "defaults_applied": include_defaults and "default_values" in template,
            "context_added": bool(agent_context),
            "rendered_at": timestamp,
        }

        logger.info(
            f"Prompt '{prompt_name}' rendered with "
            f"{len(str_variables)} variables, "
            f"{len(missing_variables)} missing"
        )
        return result

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Failed to apply agent prompt: {e}")
        raise ValueError(f"Failed to apply agent prompt: {e}")


def _substitute_variables(text: str, variables: Dict[str, str]) -> str:
    """
    テキスト内の{variable_name}形式の変数を置換

    二重波括弧{{}}はJSONリテラルとして保持する。

    Args:
        text: テンプレートテキスト
        variables: 変数名→値のマッピング

    Returns:
        置換後のテキスト
    """
    # 二重波括弧を一時プレースホルダーに置換
    text = text.replace("{{", "\x00LBRACE\x00")
    text = text.replace("}}", "\x00RBRACE\x00")

    # 単一波括弧の変数を置換
    def replace_var(match: re.Match) -> str:
        var_name = match.group(1)
        if var_name in variables:
            return str(variables[var_name])
        return str(match.group(0))

    pattern = r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}"
    text = re.sub(pattern, replace_var, text)

    # プレースホルダーを波括弧に戻す
    text = text.replace("\x00LBRACE\x00", "{")
    text = text.replace("\x00RBRACE\x00", "}")

    return text


def _find_unresolved_variables(text: str) -> List[str]:
    """
    テキスト内の未置換変数を検出

    JSONリテラルの波括弧は除外する。

    Args:
        text: 置換後のテキスト

    Returns:
        未置換変数名のリスト
    """
    # JSON文字列キー（"key":）は除外するため、単純な変数パターンのみ検出
    pattern = r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}"
    matches = re.findall(pattern, text)

    # JSON内のキー名は通常ダブルクォートで囲まれているため、
    # 行頭やMarkdownコンテキスト内の未置換変数のみ返す
    unresolved = []
    for match in matches:
        # JSONスキーマのキー名ではなく、実際のテンプレート変数として
        # 残っているものだけを抽出
        # パターン: 変数名が英単語で、json出力形式例のキーでないもの
        if not _is_json_example_key(match, text):
            if match not in unresolved:
                unresolved.append(match)

    return sorted(unresolved)


def _is_json_example_key(var_name: str, text: str) -> bool:
    """
    変数名がJSON出力例のキー名かどうかを判定

    Args:
        var_name: 変数名
        text: テキスト全体

    Returns:
        JSON出力例のキーの場合True
    """
    # "key": の形式でテキスト内に存在する場合はJSONキー
    json_key_pattern = f'"{var_name}"\\s*:'
    if re.search(json_key_pattern, text):
        return True
    return False


def _build_context_section(context: Dict[str, Any]) -> str:
    """
    エージェントコンテキスト情報をMarkdownセクションとして構築

    Args:
        context: コンテキスト辞書

    Returns:
        Markdownフォーマットのコンテキスト文字列
    """
    lines = ["## 実行コンテキスト"]
    for key, value in context.items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines)
