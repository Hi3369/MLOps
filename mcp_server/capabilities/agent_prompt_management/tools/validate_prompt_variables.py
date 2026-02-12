"""
Validate Prompt Variables Tool

プロンプト適用前に変数の妥当性を検証するツール
"""

import logging
from typing import Any, Dict, List

from .agent_prompts import BUILTIN_AGENT_PROMPTS

logger = logging.getLogger(__name__)


def validate_prompt_variables(
    prompt_name: str,
    variables: Dict[str, Any],
    strict: bool = False,
) -> Dict[str, Any]:
    """
    プロンプト適用前に変数の妥当性を検証

    Args:
        prompt_name: プロンプト名
        variables: 検証する変数辞書
        strict: 厳密モード（デフォルト値がある変数も必須とする）

    Returns:
        検証結果辞書
    """
    logger.info(f"Validating variables for prompt: {prompt_name}")

    if not prompt_name:
        raise ValueError("prompt_name must not be empty")

    if not isinstance(variables, dict):
        raise ValueError("variables must be a dictionary")

    try:
        # プロンプト存在確認
        if prompt_name not in BUILTIN_AGENT_PROMPTS:
            available = list(BUILTIN_AGENT_PROMPTS.keys())
            raise ValueError(f"Unknown prompt: {prompt_name}. " f"Available prompts: {available}")

        template = BUILTIN_AGENT_PROMPTS[prompt_name]
        defined_vars = template.get("variables", [])
        default_values = template.get("default_values", {})

        # 検証実行
        errors: List[Dict[str, str]] = []
        warnings: List[Dict[str, str]] = []

        # 1. 必須変数チェック
        missing_required = _check_missing_required(defined_vars, default_values, variables, strict)
        for var_name in missing_required:
            errors.append(
                {
                    "type": "missing_required",
                    "variable": var_name,
                    "message": f"Required variable '{var_name}' is missing",
                }
            )

        # 2. 未定義変数チェック（定義にない変数が渡された場合）
        undefined_vars = _check_undefined_variables(defined_vars, variables)
        for var_name in undefined_vars:
            warnings.append(
                {
                    "type": "undefined_variable",
                    "variable": var_name,
                    "message": (f"Variable '{var_name}' is not defined " f"in prompt template"),
                }
            )

        # 3. 空値チェック
        empty_vars = _check_empty_values(variables)
        for var_name in empty_vars:
            warnings.append(
                {
                    "type": "empty_value",
                    "variable": var_name,
                    "message": f"Variable '{var_name}' has an empty value",
                }
            )

        is_valid = len(errors) == 0

        # デフォルト値で補完される変数のリスト
        auto_filled: List[str] = []
        if not strict:
            for var_name in defined_vars:
                if var_name not in variables and var_name in default_values:
                    auto_filled.append(var_name)

        return {
            "status": "success",
            "prompt_name": prompt_name,
            "agent_type": template.get("agent_type", "unknown"),
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "variables_provided": sorted(list(variables.keys())),
            "variables_required": sorted([v for v in defined_vars if v not in default_values]),
            "auto_filled_from_defaults": sorted(auto_filled),
            "strict_mode": strict,
        }

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Failed to validate prompt variables: {e}")
        raise ValueError(f"Failed to validate prompt variables: {e}")


def _check_missing_required(
    defined_vars: List[str],
    default_values: Dict[str, Any],
    provided_vars: Dict[str, Any],
    strict: bool,
) -> List[str]:
    """
    不足している必須変数を検出

    Args:
        defined_vars: 定義された変数リスト
        default_values: デフォルト値辞書
        provided_vars: 提供された変数辞書
        strict: 厳密モード

    Returns:
        不足している変数名のリスト
    """
    missing = []
    for var_name in defined_vars:
        if var_name not in provided_vars:
            if strict or var_name not in default_values:
                missing.append(var_name)
    return sorted(missing)


def _check_undefined_variables(
    defined_vars: List[str],
    provided_vars: Dict[str, Any],
) -> List[str]:
    """
    テンプレートに定義されていない変数を検出

    Args:
        defined_vars: 定義された変数リスト
        provided_vars: 提供された変数辞書

    Returns:
        未定義変数名のリスト
    """
    undefined = []
    for var_name in provided_vars:
        if var_name not in defined_vars:
            undefined.append(var_name)
    return sorted(undefined)


def _check_empty_values(
    variables: Dict[str, Any],
) -> List[str]:
    """
    空値の変数を検出

    Args:
        variables: 変数辞書

    Returns:
        空値の変数名リスト
    """
    empty = []
    for var_name, value in variables.items():
        if value is None or (isinstance(value, str) and not value.strip()):
            empty.append(var_name)
    return sorted(empty)
