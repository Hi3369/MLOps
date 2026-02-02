"""
Apply Optimizations Tool

最適化適用ツール
"""

import copy
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def apply_optimizations(
    optimization_proposal: Dict[str, Any],
    target_config: Dict[str, Any],
) -> Dict[str, Any]:
    """
    最適化を適用

    Args:
        optimization_proposal: 最適化提案（generate_optimization_proposalの出力）
        target_config: 適用対象の設定

    Returns:
        最適化適用結果辞書
    """
    logger.info("Applying optimizations")

    # パラメータ検証
    if not optimization_proposal:
        raise ValueError("optimization_proposal must not be empty")

    if not target_config:
        raise ValueError("target_config must not be empty")

    if not isinstance(optimization_proposal, dict):
        raise ValueError("optimization_proposal must be a dictionary")

    if not isinstance(target_config, dict):
        raise ValueError("target_config must be a dictionary")

    try:
        # 元の設定をコピー
        optimized_config = copy.deepcopy(target_config)

        # 適用された最適化のリスト
        applied_optimizations = []

        # 提案から最適化を抽出
        proposals = optimization_proposal.get("optimization_proposals", [])

        for proposal in proposals:
            optimization_type = proposal.get("type", "unknown")
            suggestions = proposal.get("suggestions", {})

            # 最適化タイプ別の適用
            if optimization_type == "hyperparameter_tuning":
                applied = _apply_hyperparameter_tuning(optimized_config, suggestions)
                if applied:
                    applied_optimizations.append(
                        {
                            "type": optimization_type,
                            "description": proposal.get("description", ""),
                            "changes": applied,
                        }
                    )

            elif optimization_type == "resource_optimization":
                applied = _apply_resource_optimization(optimized_config, suggestions)
                if applied:
                    applied_optimizations.append(
                        {
                            "type": optimization_type,
                            "description": proposal.get("description", ""),
                            "changes": applied,
                        }
                    )

            elif optimization_type == "data_optimization":
                applied = _apply_data_optimization(optimized_config, suggestions)
                if applied:
                    applied_optimizations.append(
                        {
                            "type": optimization_type,
                            "description": proposal.get("description", ""),
                            "changes": applied,
                        }
                    )

            elif optimization_type == "algorithm_optimization":
                applied = _apply_algorithm_optimization(optimized_config, suggestions)
                if applied:
                    applied_optimizations.append(
                        {
                            "type": optimization_type,
                            "description": proposal.get("description", ""),
                            "changes": applied,
                        }
                    )

        # 設定の差分を計算
        config_diff = _calculate_config_diff(target_config, optimized_config)

        logger.info(f"Applied {len(applied_optimizations)} optimizations")

        return {
            "status": "success",
            "message": f"Applied {len(applied_optimizations)} optimizations successfully",
            "optimization_result": {
                "original_config": target_config,
                "optimized_config": optimized_config,
                "applied_optimizations": applied_optimizations,
                "config_diff": config_diff,
                "total_optimizations_applied": len(applied_optimizations),
            },
        }

    except Exception as e:
        logger.error(f"Optimization application error: {e}")
        raise ValueError(f"Failed to apply optimizations: {e}")


def _apply_hyperparameter_tuning(
    config: Dict[str, Any], suggestions: Dict[str, Any]
) -> Dict[str, Any]:
    """ハイパーパラメータチューニングを適用"""
    changes = {}

    if "hyperparameters" not in config:
        config["hyperparameters"] = {}

    for param_name, param_values in suggestions.items():
        if isinstance(param_values, list) and param_values:
            # リストの中央値を選択
            mid_index = len(param_values) // 2
            selected_value = param_values[mid_index]

            old_value = config["hyperparameters"].get(param_name, "not_set")
            config["hyperparameters"][param_name] = selected_value

            changes[param_name] = {
                "old": old_value,
                "new": selected_value,
            }

    return changes


def _apply_resource_optimization(
    config: Dict[str, Any], suggestions: Dict[str, Any]
) -> Dict[str, Any]:
    """リソース最適化を適用"""
    changes = {}

    if "resource_config" not in config:
        config["resource_config"] = {}

    for key, value in suggestions.items():
        old_value = config["resource_config"].get(key, "not_set")
        config["resource_config"][key] = value

        changes[key] = {
            "old": old_value,
            "new": value,
        }

    return changes


def _apply_data_optimization(config: Dict[str, Any], suggestions: Dict[str, Any]) -> Dict[str, Any]:
    """データ最適化を適用"""
    changes = {}

    if "data_config" not in config:
        config["data_config"] = {}

    for key, value in suggestions.items():
        old_value = config["data_config"].get(key, "not_set")
        config["data_config"][key] = value

        changes[key] = {
            "old": old_value,
            "new": value,
        }

    return changes


def _apply_algorithm_optimization(
    config: Dict[str, Any], suggestions: Dict[str, Any]
) -> Dict[str, Any]:
    """アルゴリズム最適化を適用"""
    changes = {}

    # 代替アルゴリズムの提案がある場合
    if "alternative_algorithms" in suggestions and suggestions["alternative_algorithms"]:
        alternative_algorithms = suggestions["alternative_algorithms"]
        # 最初の代替アルゴリズムを選択
        selected_algorithm = alternative_algorithms[0]

        old_algorithm = config.get("algorithm", "not_set")
        config["algorithm"] = selected_algorithm

        changes["algorithm"] = {
            "old": old_algorithm,
            "new": selected_algorithm,
        }

    return changes


def _calculate_config_diff(original: Dict[str, Any], optimized: Dict[str, Any]) -> Dict[str, Any]:
    """設定の差分を計算"""
    diff: Dict[str, Any] = {
        "added": {},
        "modified": {},
        "removed": {},
    }

    # 最適化された設定のキーをチェック
    for key in optimized:
        if key not in original:
            diff["added"][key] = optimized[key]
        elif original[key] != optimized[key]:
            diff["modified"][key] = {
                "old": original[key],
                "new": optimized[key],
            }

    # 削除されたキーをチェック
    for key in original:
        if key not in optimized:
            diff["removed"][key] = original[key]

    return diff
