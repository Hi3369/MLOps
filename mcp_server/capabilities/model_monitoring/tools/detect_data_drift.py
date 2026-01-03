"""
Detect Data Drift Tool

データドリフト検出ツール
"""

import logging
from typing import Any, Dict, List

import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


def detect_data_drift(
    baseline_data: Dict[str, List[float]],
    current_data: Dict[str, List[float]],
    drift_threshold: float = 0.05,
    method: str = "ks_test",
) -> Dict[str, Any]:
    """
    データドリフトを検出

    Args:
        baseline_data: ベースラインデータ（特徴量名: 値のリスト）
        current_data: 現在のデータ（特徴量名: 値のリスト）
        drift_threshold: ドリフト検出閾値（p値）
        method: 検定方法（'ks_test', 'chi_square'）

    Returns:
        ドリフト検出結果辞書
    """
    logger.info("Detecting data drift")

    # パラメータ検証
    if not baseline_data or not current_data:
        raise ValueError("baseline_data and current_data must not be empty")

    if drift_threshold <= 0 or drift_threshold >= 1:
        raise ValueError("drift_threshold must be between 0 and 1")

    if method not in ["ks_test", "chi_square"]:
        raise ValueError("method must be 'ks_test' or 'chi_square'")

    try:
        drift_results = {}
        drifted_features = []
        total_features = 0

        # 両方のデータセットに存在する特徴量のみ検証
        common_features = set(baseline_data.keys()) & set(current_data.keys())

        if not common_features:
            raise ValueError("No common features found between baseline and current data")

        for feature_name in common_features:
            total_features += 1
            baseline_values = np.array(baseline_data[feature_name])
            current_values = np.array(current_data[feature_name])

            # データ検証
            if len(baseline_values) == 0 or len(current_values) == 0:
                drift_results[feature_name] = {
                    "is_drifted": False,
                    "p_value": None,
                    "statistic": None,
                    "error": "Empty data",
                }
                continue

            # ドリフト検定
            if method == "ks_test":
                result = _kolmogorov_smirnov_test(baseline_values, current_values, drift_threshold)
            else:  # chi_square
                result = _chi_square_test(baseline_values, current_values, drift_threshold)

            drift_results[feature_name] = result

            if result["is_drifted"]:
                drifted_features.append(feature_name)

        # 全体のドリフト評価
        drift_percentage = (
            (len(drifted_features) / total_features * 100) if total_features > 0 else 0
        )
        overall_drift_detected = len(drifted_features) > 0

        logger.info(
            f"Data drift detection completed: {len(drifted_features)}/{total_features} features drifted"
        )

        return {
            "status": "success",
            "message": "Data drift detection completed",
            "drift_info": {
                "overall_drift_detected": overall_drift_detected,
                "total_features": total_features,
                "drifted_features_count": len(drifted_features),
                "drift_percentage": drift_percentage,
                "drifted_features": drifted_features,
                "drift_threshold": drift_threshold,
                "method": method,
                "feature_results": drift_results,
            },
        }

    except Exception as e:
        logger.error(f"Data drift detection error: {e}")
        raise ValueError(f"Failed to detect data drift: {e}")


def _kolmogorov_smirnov_test(
    baseline: np.ndarray, current: np.ndarray, threshold: float
) -> Dict[str, Any]:
    """Kolmogorov-Smirnov検定を実行"""
    try:
        statistic, p_value = stats.ks_2samp(baseline, current)

        is_drifted = p_value < threshold

        return {
            "is_drifted": is_drifted,
            "p_value": float(p_value),
            "statistic": float(statistic),
            "test": "kolmogorov_smirnov",
            "interpretation": (
                "Significant drift detected" if is_drifted else "No significant drift"
            ),
        }

    except Exception as e:
        logger.warning(f"KS test failed: {e}")
        return {
            "is_drifted": False,
            "p_value": None,
            "statistic": None,
            "error": str(e),
        }


def _chi_square_test(baseline: np.ndarray, current: np.ndarray, threshold: float) -> Dict[str, Any]:
    """カイ二乗検定を実行（カテゴリカルデータ向け）"""
    try:
        # ヒストグラムを作成
        bins = min(10, int(np.sqrt(len(baseline))))
        baseline_hist, bin_edges = np.histogram(baseline, bins=bins)
        current_hist, _ = np.histogram(current, bins=bin_edges)

        # ゼロ頻度を避けるため、小さな値を追加
        baseline_hist = baseline_hist + 1
        current_hist = current_hist + 1

        # カイ二乗検定
        statistic, p_value = stats.chisquare(current_hist, baseline_hist)

        is_drifted = p_value < threshold

        return {
            "is_drifted": is_drifted,
            "p_value": float(p_value),
            "statistic": float(statistic),
            "test": "chi_square",
            "interpretation": (
                "Significant drift detected" if is_drifted else "No significant drift"
            ),
        }

    except Exception as e:
        logger.warning(f"Chi-square test failed: {e}")
        return {
            "is_drifted": False,
            "p_value": None,
            "statistic": None,
            "error": str(e),
        }
