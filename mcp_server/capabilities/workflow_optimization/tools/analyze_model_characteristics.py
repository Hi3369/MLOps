"""
Analyze Model Characteristics Tool

モデル特性分析ツール（データサイズ、アルゴリズム等）
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def analyze_model_characteristics(
    model_config: Dict[str, Any],
    dataset_info: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    モデル特性を分析

    Args:
        model_config: モデル設定（algorithm, hyperparameters等）
        dataset_info: データセット情報（size, features等）

    Returns:
        モデル特性分析結果辞書
    """
    logger.info("Analyzing model characteristics")

    # パラメータ検証
    if not model_config:
        raise ValueError("model_config must not be empty")

    if not isinstance(model_config, dict):
        raise ValueError("model_config must be a dictionary")

    try:
        # モデルアルゴリズムの抽出
        algorithm = model_config.get("algorithm", "unknown")
        hyperparameters = model_config.get("hyperparameters", {})

        # データセット情報の分析
        dataset_characteristics = {}
        if dataset_info:
            dataset_size = dataset_info.get("size", 0)
            num_features = dataset_info.get("num_features", 0)
            num_classes = dataset_info.get("num_classes", None)

            dataset_characteristics = {
                "size": dataset_size,
                "num_features": num_features,
                "num_classes": num_classes,
                "size_category": _categorize_dataset_size(dataset_size),
                "complexity": _calculate_complexity(num_features, dataset_size),
            }

        # 計算リソース要件の推定
        resource_requirements = _estimate_resource_requirements(
            algorithm, dataset_characteristics.get("size", 0), hyperparameters
        )

        # トレーニング時間の推定
        estimated_training_time = _estimate_training_time(
            algorithm, dataset_characteristics.get("size", 0), resource_requirements
        )

        # モデル特性のカテゴリ化
        model_category = _categorize_model(algorithm, dataset_characteristics)

        logger.info(
            f"Model characteristics analyzed: algorithm={algorithm}, category={model_category}"
        )

        return {
            "status": "success",
            "message": "Model characteristics analyzed successfully",
            "characteristics": {
                "algorithm": algorithm,
                "hyperparameters": hyperparameters,
                "model_category": model_category,
                "dataset_characteristics": dataset_characteristics,
                "resource_requirements": resource_requirements,
                "estimated_training_time_minutes": estimated_training_time,
                "optimization_opportunities": _identify_optimization_opportunities(
                    algorithm, dataset_characteristics, hyperparameters
                ),
            },
        }

    except Exception as e:
        logger.error(f"Model characteristics analysis error: {e}")
        raise ValueError(f"Failed to analyze model characteristics: {e}")


def _categorize_dataset_size(size: int) -> str:
    """データセットサイズをカテゴリ化"""
    if size < 1000:
        return "small"
    elif size < 100000:
        return "medium"
    elif size < 1000000:
        return "large"
    else:
        return "very_large"


def _calculate_complexity(num_features: int, dataset_size: int) -> str:
    """データセットの複雑度を計算"""
    if num_features == 0 or dataset_size == 0:
        return "unknown"

    complexity_score = num_features * dataset_size

    if complexity_score < 10000:
        return "low"
    elif complexity_score < 1000000:
        return "medium"
    else:
        return "high"


def _estimate_resource_requirements(
    algorithm: str, dataset_size: int, hyperparameters: Dict[str, Any]
) -> Dict[str, Any]:
    """計算リソース要件を推定"""
    # アルゴリズムベースのリソース要件
    base_requirements = {
        "linear_regression": {"cpu": 2, "memory_gb": 4, "gpu": False},
        "logistic_regression": {"cpu": 2, "memory_gb": 4, "gpu": False},
        "random_forest": {"cpu": 4, "memory_gb": 8, "gpu": False},
        "gradient_boosting": {"cpu": 4, "memory_gb": 8, "gpu": False},
        "xgboost": {"cpu": 4, "memory_gb": 16, "gpu": True},
        "neural_network": {"cpu": 8, "memory_gb": 32, "gpu": True},
        "deep_learning": {"cpu": 8, "memory_gb": 64, "gpu": True},
        "unknown": {"cpu": 2, "memory_gb": 8, "gpu": False},
    }

    requirements = base_requirements.get(algorithm, base_requirements["unknown"]).copy()

    # データサイズに応じてスケール
    if dataset_size > 100000:
        requirements["cpu"] *= 2
        requirements["memory_gb"] *= 2

    if dataset_size > 1000000:
        requirements["cpu"] *= 2
        requirements["memory_gb"] *= 2

    # ハイパーパラメータに応じて調整
    if "n_estimators" in hyperparameters and hyperparameters["n_estimators"] > 100:
        requirements["cpu"] = min(requirements["cpu"] * 1.5, 16)

    return requirements


def _estimate_training_time(
    algorithm: str, dataset_size: int, resource_requirements: Dict[str, Any]
) -> float:
    """トレーニング時間を推定（分）"""
    # アルゴリズムベースの基本時間（小データセット）
    base_time_minutes = {
        "linear_regression": 1,
        "logistic_regression": 2,
        "random_forest": 10,
        "gradient_boosting": 15,
        "xgboost": 20,
        "neural_network": 30,
        "deep_learning": 60,
        "unknown": 10,
    }

    base_time = base_time_minutes.get(algorithm, base_time_minutes["unknown"])

    # データサイズに応じてスケール
    if dataset_size > 1000:
        base_time *= (dataset_size / 1000) ** 0.5

    # GPU使用時は高速化
    if resource_requirements.get("gpu", False):
        base_time *= 0.3

    return round(base_time, 2)


def _categorize_model(algorithm: str, dataset_characteristics: Dict[str, Any]) -> str:
    """モデルをカテゴリ化"""
    # ディープラーニング系
    if algorithm in ["neural_network", "deep_learning", "cnn", "rnn", "transformer"]:
        return "deep_learning"

    # アンサンブル系
    if algorithm in ["random_forest", "gradient_boosting", "xgboost", "lightgbm"]:
        return "ensemble"

    # 線形系
    if algorithm in ["linear_regression", "logistic_regression", "svm"]:
        return "linear"

    return "other"


def _identify_optimization_opportunities(
    algorithm: str,
    dataset_characteristics: Dict[str, Any],
    hyperparameters: Dict[str, Any],
) -> list:
    """最適化機会を特定"""
    opportunities = []

    # データサイズに基づく最適化
    size_category = dataset_characteristics.get("size_category", "unknown")
    if size_category == "very_large":
        opportunities.append(
            {
                "type": "data_sampling",
                "description": "大規模データセット向けサンプリング戦略の適用",
                "expected_speedup": "2-5x",
            }
        )

    # アルゴリズム別最適化
    if algorithm in ["xgboost", "lightgbm", "gradient_boosting"]:
        if not hyperparameters.get("early_stopping_rounds"):
            opportunities.append(
                {
                    "type": "early_stopping",
                    "description": "Early Stoppingの有効化",
                    "expected_speedup": "1.5-2x",
                }
            )

    if algorithm in ["neural_network", "deep_learning"]:
        if not hyperparameters.get("batch_size"):
            opportunities.append(
                {
                    "type": "batch_optimization",
                    "description": "バッチサイズの最適化",
                    "expected_speedup": "1.2-1.5x",
                }
            )

    # GPU活用機会
    complexity = dataset_characteristics.get("complexity", "unknown")
    if complexity in ["medium", "high"] and algorithm in [
        "xgboost",
        "neural_network",
        "deep_learning",
    ]:
        opportunities.append(
            {
                "type": "gpu_acceleration",
                "description": "GPU活用による高速化",
                "expected_speedup": "3-10x",
            }
        )

    return opportunities
