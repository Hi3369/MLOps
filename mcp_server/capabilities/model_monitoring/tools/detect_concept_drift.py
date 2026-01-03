"""
Detect Concept Drift Tool

コンセプトドリフト検出ツール
"""

import logging
from typing import Any, Dict, List

import numpy as np
from sklearn.metrics import accuracy_score, f1_score

logger = logging.getLogger(__name__)


def detect_concept_drift(
    predictions: List[Any],
    actual_labels: List[Any],
    window_size: int = 100,
    drift_threshold: float = 0.1,
) -> Dict[str, Any]:
    """
    コンセプトドリフトを検出

    Args:
        predictions: 予測値のリスト
        actual_labels: 実際のラベルのリスト
        window_size: ドリフト検出のウィンドウサイズ
        drift_threshold: 精度低下の閾値（0-1）

    Returns:
        コンセプトドリフト検出結果辞書
    """
    logger.info("Detecting concept drift")

    # パラメータ検証
    if not predictions or not actual_labels:
        raise ValueError("predictions and actual_labels must not be empty")

    if len(predictions) != len(actual_labels):
        raise ValueError("predictions and actual_labels must have the same length")

    if window_size < 2:
        raise ValueError("window_size must be at least 2")

    if drift_threshold <= 0 or drift_threshold >= 1:
        raise ValueError("drift_threshold must be between 0 and 1")

    try:
        predictions_array = np.array(predictions)
        actual_array = np.array(actual_labels)

        # ウィンドウごとの精度を計算
        window_accuracies = []
        window_f1_scores = []
        drift_detected_windows = []

        total_windows = len(predictions) // window_size

        if total_windows < 2:
            raise ValueError(
                f"Insufficient data: need at least {window_size * 2} samples, got {len(predictions)}"
            )

        # 最初のウィンドウをベースラインとして使用
        baseline_start = 0
        baseline_end = window_size
        baseline_preds = predictions_array[baseline_start:baseline_end]
        baseline_actual = actual_array[baseline_start:baseline_end]

        baseline_accuracy = accuracy_score(baseline_actual, baseline_preds)

        # 分類問題かどうか判定（ユニーク値が少ない場合は分類）
        is_classification = len(np.unique(actual_array)) < 100

        if is_classification:
            baseline_f1 = f1_score(
                baseline_actual, baseline_preds, average="weighted", zero_division=0
            )
        else:
            baseline_f1 = None

        # 各ウィンドウで精度を計算
        for i in range(1, total_windows):
            window_start = i * window_size
            window_end = window_start + window_size

            window_preds = predictions_array[window_start:window_end]
            window_actual = actual_array[window_start:window_end]

            window_accuracy = accuracy_score(window_actual, window_preds)
            window_accuracies.append(window_accuracy)

            if is_classification:
                window_f1 = f1_score(
                    window_actual, window_preds, average="weighted", zero_division=0
                )
                window_f1_scores.append(window_f1)

            # ドリフト検出: ベースラインから指定閾値以上低下
            accuracy_degradation = baseline_accuracy - window_accuracy

            if accuracy_degradation > drift_threshold:
                drift_detected_windows.append(
                    {
                        "window_index": i,
                        "window_range": f"{window_start}-{window_end}",
                        "accuracy": window_accuracy,
                        "baseline_accuracy": baseline_accuracy,
                        "degradation": accuracy_degradation,
                    }
                )

        # 全体の統計
        overall_drift_detected = len(drift_detected_windows) > 0
        avg_accuracy = np.mean(window_accuracies) if window_accuracies else baseline_accuracy
        min_accuracy = np.min(window_accuracies) if window_accuracies else baseline_accuracy
        max_accuracy = np.max(window_accuracies) if window_accuracies else baseline_accuracy

        result = {
            "status": "success",
            "message": "Concept drift detection completed",
            "drift_info": {
                "overall_drift_detected": overall_drift_detected,
                "total_samples": len(predictions),
                "window_size": window_size,
                "total_windows": total_windows,
                "drift_threshold": drift_threshold,
                "drifted_windows_count": len(drift_detected_windows),
                "baseline": {
                    "accuracy": baseline_accuracy,
                    "f1_score": baseline_f1,
                    "sample_count": window_size,
                },
                "overall_statistics": {
                    "average_accuracy": avg_accuracy,
                    "min_accuracy": min_accuracy,
                    "max_accuracy": max_accuracy,
                    "accuracy_variance": np.var(window_accuracies) if window_accuracies else 0,
                },
                "drifted_windows": drift_detected_windows,
                "window_accuracies": window_accuracies,
            },
        }

        if is_classification:
            result["drift_info"]["overall_statistics"]["average_f1_score"] = (
                np.mean(window_f1_scores) if window_f1_scores else baseline_f1
            )
            result["drift_info"]["window_f1_scores"] = window_f1_scores

        logger.info(
            f"Concept drift detection completed: {len(drift_detected_windows)}/{total_windows - 1} windows drifted"
        )

        return result

    except Exception as e:
        logger.error(f"Concept drift detection error: {e}")
        raise ValueError(f"Failed to detect concept drift: {e}")
