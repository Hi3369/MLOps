"""
Generate Optimization Proposal Tool

最適化提案生成ツール
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def generate_optimization_proposal(
    model_characteristics: Dict[str, Any],
    constraints: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    最適化提案を生成

    Args:
        model_characteristics: モデル特性（analyze_model_characteristicsの出力）
        constraints: 制約条件（budget, max_training_time等）

    Returns:
        最適化提案辞書
    """
    logger.info("Generating optimization proposal")

    # パラメータ検証
    if not model_characteristics:
        raise ValueError("model_characteristics must not be empty")

    if not isinstance(model_characteristics, dict):
        raise ValueError("model_characteristics must be a dictionary")

    try:
        # 制約条件の抽出
        constraints = constraints or {}
        max_training_time = constraints.get("max_training_time_minutes", float("inf"))
        max_cost = constraints.get("max_cost_usd", float("inf"))
        require_gpu = constraints.get("require_gpu", None)

        # モデル特性の抽出
        algorithm = model_characteristics.get("algorithm", "unknown")
        resource_requirements = model_characteristics.get("resource_requirements", {})
        estimated_time = model_characteristics.get("estimated_training_time_minutes", 0)

        # 最適化提案の生成
        proposals = []

        # 1. ハイパーパラメータチューニング提案
        hyperparameter_proposal = _generate_hyperparameter_proposal(
            algorithm, estimated_time, max_training_time
        )
        if hyperparameter_proposal:
            proposals.append(hyperparameter_proposal)

        # 2. リソース最適化提案
        resource_proposal = _generate_resource_proposal(
            resource_requirements, require_gpu, max_cost
        )
        if resource_proposal:
            proposals.append(resource_proposal)

        # 3. データ最適化提案
        data_proposal = _generate_data_proposal(model_characteristics)
        if data_proposal:
            proposals.append(data_proposal)

        # 4. アルゴリズム選択提案
        algorithm_proposal = _generate_algorithm_proposal(
            algorithm, model_characteristics
        )
        if algorithm_proposal:
            proposals.append(algorithm_proposal)

        # 優先度付け
        ranked_proposals = _rank_proposals(proposals, constraints)

        # コスト・時間の推定
        total_cost_estimate = _estimate_total_cost(ranked_proposals)
        total_time_estimate = _estimate_total_time(ranked_proposals, estimated_time)

        logger.info(f"Generated {len(ranked_proposals)} optimization proposals")

        return {
            "status": "success",
            "message": "Optimization proposal generated successfully",
            "proposal": {
                "optimization_proposals": ranked_proposals,
                "total_cost_estimate_usd": total_cost_estimate,
                "total_time_estimate_minutes": total_time_estimate,
                "expected_performance_improvement": _estimate_performance_improvement(
                    ranked_proposals
                ),
                "constraints_satisfied": _check_constraints(
                    total_cost_estimate, total_time_estimate, constraints
                ),
            },
        }

    except Exception as e:
        logger.error(f"Optimization proposal generation error: {e}")
        raise ValueError(f"Failed to generate optimization proposal: {e}")


def _generate_hyperparameter_proposal(
    algorithm: str, estimated_time: float, max_time: float
) -> Dict[str, Any]:
    """ハイパーパラメータチューニング提案を生成"""
    if estimated_time > max_time:
        return None

    # アルゴリズム別の推奨ハイパーパラメータ
    hyperparameter_suggestions = {
        "random_forest": {
            "n_estimators": [100, 200, 300],
            "max_depth": [10, 20, 30, None],
            "min_samples_split": [2, 5, 10],
        },
        "xgboost": {
            "n_estimators": [100, 200, 500],
            "max_depth": [3, 6, 9],
            "learning_rate": [0.01, 0.1, 0.3],
            "subsample": [0.8, 0.9, 1.0],
        },
        "neural_network": {
            "hidden_layers": [[64, 32], [128, 64, 32], [256, 128, 64]],
            "learning_rate": [0.001, 0.01, 0.1],
            "batch_size": [32, 64, 128],
            "epochs": [50, 100, 200],
        },
    }

    suggestions = hyperparameter_suggestions.get(algorithm, {})

    if not suggestions:
        return None

    return {
        "type": "hyperparameter_tuning",
        "priority": "high",
        "description": f"{algorithm}のハイパーパラメータチューニング",
        "suggestions": suggestions,
        "tuning_strategy": "grid_search"
        if estimated_time < max_time * 0.5
        else "random_search",
        "expected_improvement": "5-15%",
    }


def _generate_resource_proposal(
    resource_requirements: Dict[str, Any], require_gpu: bool, max_cost: float
) -> Dict[str, Any]:
    """リソース最適化提案を生成"""
    current_gpu = resource_requirements.get("gpu", False)

    # GPU活用提案
    if require_gpu is None and not current_gpu:
        return {
            "type": "resource_optimization",
            "priority": "medium",
            "description": "GPU活用による高速化",
            "suggestions": {
                "instance_type": "ml.p3.2xlarge",
                "gpu_enabled": True,
            },
            "cost_increase_usd": 2.5,
            "expected_speedup": "3-5x",
        }

    # コスト制約がある場合のスポットインスタンス提案
    if max_cost < float("inf"):
        return {
            "type": "resource_optimization",
            "priority": "medium",
            "description": "スポットインスタンス活用によるコスト削減",
            "suggestions": {
                "use_spot_instances": True,
                "spot_max_price": 0.5,
            },
            "cost_reduction_percentage": 70,
            "expected_speedup": "1x",
        }

    return None


def _generate_data_proposal(model_characteristics: Dict[str, Any]) -> Dict[str, Any]:
    """データ最適化提案を生成"""
    dataset_chars = model_characteristics.get("dataset_characteristics", {})
    size_category = dataset_chars.get("size_category", "unknown")

    if size_category == "very_large":
        return {
            "type": "data_optimization",
            "priority": "high",
            "description": "大規模データセット向け最適化",
            "suggestions": {
                "use_sampling": True,
                "sample_ratio": 0.7,
                "use_data_caching": True,
                "use_prefetching": True,
            },
            "expected_speedup": "2-3x",
        }

    return None


def _generate_algorithm_proposal(
    algorithm: str, model_characteristics: Dict[str, Any]
) -> Dict[str, Any]:
    """アルゴリズム選択提案を生成"""
    dataset_chars = model_characteristics.get("dataset_characteristics", {})
    size_category = dataset_chars.get("size_category", "unknown")

    # 大規模データセットでランダムフォレストを使っている場合
    if algorithm == "random_forest" and size_category in ["large", "very_large"]:
        return {
            "type": "algorithm_optimization",
            "priority": "medium",
            "description": "より高速なアルゴリズムへの変更提案",
            "suggestions": {
                "alternative_algorithms": ["xgboost", "lightgbm"],
                "expected_performance": "similar",
            },
            "expected_speedup": "2-4x",
        }

    return None


def _rank_proposals(proposals: list, constraints: Dict[str, Any]) -> list:
    """提案に優先度を付けてランク付け"""
    priority_order = {"high": 3, "medium": 2, "low": 1}

    # 優先度でソート
    ranked = sorted(
        proposals,
        key=lambda p: priority_order.get(p.get("priority", "low"), 0),
        reverse=True,
    )

    return ranked


def _estimate_total_cost(proposals: list) -> float:
    """総コストを推定"""
    total_cost = 0.0

    for proposal in proposals:
        if "cost_increase_usd" in proposal:
            total_cost += proposal["cost_increase_usd"]

    return round(total_cost, 2)


def _estimate_total_time(proposals: list, base_time: float) -> float:
    """総時間を推定"""
    speedup_factor = 1.0

    for proposal in proposals:
        if "expected_speedup" in proposal:
            speedup_str = proposal["expected_speedup"]
            # "3-5x" -> 平均値 4.0
            if "-" in speedup_str:
                parts = speedup_str.replace("x", "").split("-")
                speedup = (float(parts[0]) + float(parts[1])) / 2
                speedup_factor *= speedup

    estimated_time = base_time / speedup_factor if speedup_factor > 0 else base_time

    return round(estimated_time, 2)


def _estimate_performance_improvement(proposals: list) -> str:
    """パフォーマンス向上を推定"""
    total_improvement = 0.0

    for proposal in proposals:
        if "expected_improvement" in proposal:
            improvement_str = proposal["expected_improvement"]
            # "5-15%" -> 平均値 10%
            if "-" in improvement_str:
                parts = improvement_str.replace("%", "").split("-")
                improvement = (float(parts[0]) + float(parts[1])) / 2
                total_improvement += improvement

    if total_improvement == 0:
        return "No significant improvement expected"

    return f"{int(total_improvement)}% improvement expected"


def _check_constraints(
    total_cost: float, total_time: float, constraints: Dict[str, Any]
) -> bool:
    """制約条件を満たしているかチェック"""
    max_cost = constraints.get("max_cost_usd", float("inf"))
    max_time = constraints.get("max_training_time_minutes", float("inf"))

    return total_cost <= max_cost and total_time <= max_time
