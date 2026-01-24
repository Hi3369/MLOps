"""
Evaluate Trigger Conditions Tool

トリガー条件評価ツール
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4

logger = logging.getLogger(__name__)


def evaluate_trigger_conditions(
    conditions: List[Dict[str, Any]],
    current_metrics: Dict[str, Any],
) -> Dict[str, Any]:
    """
    トリガー条件を評価

    Args:
        conditions: 条件配列
            - type: "drift_threshold" | "schedule" | "performance_threshold" | "data_volume"
            - threshold: float (数値条件の場合)
            - metric: str (メトリクス名)
            - expression: str (スケジュール条件の場合)
            - comparison: "gt" | "lt" | "eq" | "gte" | "lte"
        current_metrics: 現在のメトリクス
            - drift_score: float
            - accuracy: float
            - data_sample_count: int
            - last_retrain_time: str (ISO形式)

    Returns:
        評価結果辞書
    """
    logger.info(f"Evaluating {len(conditions)} trigger conditions")

    # パラメータ検証
    if not conditions:
        raise ValueError("conditions must not be empty")

    if not current_metrics:
        raise ValueError("current_metrics must not be empty")

    try:
        timestamp = datetime.now(timezone.utc).isoformat()
        evaluation_id = str(uuid4())[:8]

        # 各条件を評価
        evaluated_conditions = []
        for i, condition in enumerate(conditions):
            result = _evaluate_single_condition(condition, current_metrics)
            evaluated_conditions.append(
                {
                    "index": i,
                    "condition": condition,
                    **result,
                }
            )

        # いずれかの条件がトリガーされたか
        any_triggered = any(c["triggered"] for c in evaluated_conditions)

        # トリガーされた条件の数
        triggered_count = sum(1 for c in evaluated_conditions if c["triggered"])

        logger.info(
            f"Evaluation complete: {triggered_count}/{len(conditions)} conditions triggered"
        )

        return {
            "status": "success",
            "message": f"Evaluated {len(conditions)} conditions",
            "evaluation_result": {
                "evaluation_id": evaluation_id,
                "conditions": evaluated_conditions,
                "any_triggered": any_triggered,
                "triggered_count": triggered_count,
                "total_conditions": len(conditions),
                "timestamp": timestamp,
            },
        }

    except Exception as e:
        logger.error(f"Failed to evaluate trigger conditions: {e}")
        raise ValueError(f"Failed to evaluate trigger conditions: {e}")


def _evaluate_single_condition(
    condition: Dict[str, Any],
    metrics: Dict[str, Any],
) -> Dict[str, Any]:
    """単一の条件を評価"""
    condition_type = condition.get("type", "unknown")

    if condition_type == "drift_threshold":
        return _evaluate_drift_threshold(condition, metrics)
    elif condition_type == "performance_threshold":
        return _evaluate_performance_threshold(condition, metrics)
    elif condition_type == "schedule":
        return _evaluate_schedule(condition, metrics)
    elif condition_type == "data_volume":
        return _evaluate_data_volume(condition, metrics)
    else:
        return {
            "triggered": False,
            "reason": f"Unknown condition type: {condition_type}",
        }


def _evaluate_drift_threshold(
    condition: Dict[str, Any],
    metrics: Dict[str, Any],
) -> Dict[str, Any]:
    """ドリフト閾値条件を評価"""
    threshold = condition.get("threshold", 0.1)
    comparison = condition.get("comparison", "gt")
    drift_score = metrics.get("drift_score", 0.0)

    triggered = _compare_values(drift_score, threshold, comparison)

    return {
        "triggered": triggered,
        "reason": (
            f"drift_score ({drift_score}) {comparison} threshold ({threshold})"
            if triggered
            else "Drift score within threshold"
        ),
        "details": {
            "current_value": drift_score,
            "threshold": threshold,
            "comparison": comparison,
        },
    }


def _evaluate_performance_threshold(
    condition: Dict[str, Any],
    metrics: Dict[str, Any],
) -> Dict[str, Any]:
    """パフォーマンス閾値条件を評価"""
    metric_name = condition.get("metric", "accuracy")
    threshold = condition.get("threshold", 0.9)
    comparison = condition.get("comparison", "lt")
    current_value = metrics.get(metric_name, 1.0)

    triggered = _compare_values(current_value, threshold, comparison)

    return {
        "triggered": triggered,
        "reason": (
            f"{metric_name} ({current_value}) {comparison} threshold ({threshold})"
            if triggered
            else f"{metric_name} within acceptable range"
        ),
        "details": {
            "metric": metric_name,
            "current_value": current_value,
            "threshold": threshold,
            "comparison": comparison,
        },
    }


def _evaluate_schedule(
    condition: Dict[str, Any],
    metrics: Dict[str, Any],
) -> Dict[str, Any]:
    """スケジュール条件を評価"""
    expression = condition.get("expression", "")
    last_retrain_time = metrics.get("last_retrain_time", "")

    # シンプルな日数ベースの評価
    if not last_retrain_time:
        return {
            "triggered": True,
            "reason": "No previous retraining recorded",
            "details": {"expression": expression},
        }

    try:
        last_time = datetime.fromisoformat(last_retrain_time.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        days_since = (now - last_time).days

        # デフォルト: 7日以上経過でトリガー
        threshold_days = condition.get("threshold_days", 7)
        triggered = days_since >= threshold_days

        return {
            "triggered": triggered,
            "reason": (
                f"Days since last retrain: {days_since} (threshold: {threshold_days})"
                if triggered
                else f"Only {days_since} days since last retrain"
            ),
            "details": {
                "days_since_retrain": days_since,
                "threshold_days": threshold_days,
                "last_retrain_time": last_retrain_time,
            },
        }
    except (ValueError, TypeError):
        return {
            "triggered": False,
            "reason": "Invalid last_retrain_time format",
            "details": {"expression": expression},
        }


def _evaluate_data_volume(
    condition: Dict[str, Any],
    metrics: Dict[str, Any],
) -> Dict[str, Any]:
    """データ量条件を評価"""
    threshold = condition.get("threshold", 1000)
    comparison = condition.get("comparison", "gte")
    sample_count = metrics.get("data_sample_count", 0)

    triggered = _compare_values(sample_count, threshold, comparison)

    return {
        "triggered": triggered,
        "reason": (
            f"data_sample_count ({sample_count}) {comparison} threshold ({threshold})"
            if triggered
            else "Insufficient data volume"
        ),
        "details": {
            "current_count": sample_count,
            "threshold": threshold,
            "comparison": comparison,
        },
    }


def _compare_values(value: float, threshold: float, comparison: str) -> bool:
    """値を比較"""
    if comparison == "gt":
        return value > threshold
    elif comparison == "lt":
        return value < threshold
    elif comparison == "gte":
        return value >= threshold
    elif comparison == "lte":
        return value <= threshold
    elif comparison == "eq":
        return value == threshold
    else:
        return False
