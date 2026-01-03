"""Model Monitoring Capability実装"""
import logging
from typing import Any, Callable, Dict

from .tools import (
    collect_model_metrics,
    collect_system_metrics,
    create_cloudwatch_alarm,
    create_monitoring_dashboard,
    delete_cloudwatch_alarm,
    delete_dashboard,
    detect_concept_drift,
    detect_data_drift,
    get_alarm_state,
    update_dashboard,
)

logger = logging.getLogger(__name__)


class ModelMonitoringCapability:
    """モデル監視・ドリフト検出"""

    def __init__(self):
        """Capabilityの初期化"""
        logger.info("Initializing Model Monitoring Capability")
        self._tools = self._register_tools()

    def _register_tools(self) -> Dict[str, Callable]:
        """ツールの登録"""
        return {
            "collect_system_metrics": collect_system_metrics,
            "collect_model_metrics": collect_model_metrics,
            "detect_data_drift": detect_data_drift,
            "detect_concept_drift": detect_concept_drift,
            "create_cloudwatch_alarm": create_cloudwatch_alarm,
            "delete_cloudwatch_alarm": delete_cloudwatch_alarm,
            "get_alarm_state": get_alarm_state,
            "update_dashboard": update_dashboard,
            "create_monitoring_dashboard": create_monitoring_dashboard,
            "delete_dashboard": delete_dashboard,
        }

    def get_tools(self) -> Dict[str, Callable]:
        """登録されているツールを返す"""
        return self._tools

    def get_tool_schemas(self) -> Dict[str, Dict[str, Any]]:
        """
        各ツールのスキーマを返す

        Returns:
            ツールスキーマ辞書
        """
        return {
            "collect_system_metrics": {
                "name": "collect_system_metrics",
                "description": "システムメトリクスを収集（CPU/Memory/Latency）",
                "parameters": {
                    "endpoint_name": "エンドポイント名",
                    "time_range_minutes": "メトリクス取得期間（分）",
                    "metric_period_seconds": "メトリクス集計期間（秒）",
                },
            },
            "collect_model_metrics": {
                "name": "collect_model_metrics",
                "description": "モデルメトリクスを収集（精度、予測分布等）",
                "parameters": {
                    "endpoint_name": "エンドポイント名",
                    "time_range_minutes": "メトリクス取得期間（分）",
                    "metric_period_seconds": "メトリクス集計期間（秒）",
                },
            },
            "detect_data_drift": {
                "name": "detect_data_drift",
                "description": "データドリフトを検出",
                "parameters": {
                    "baseline_data": "ベースラインデータ（特徴量名: 値のリスト）",
                    "current_data": "現在のデータ（特徴量名: 値のリスト）",
                    "drift_threshold": "ドリフト検出閾値（p値）",
                    "method": "検定方法（ks_test, chi_square）",
                },
            },
            "detect_concept_drift": {
                "name": "detect_concept_drift",
                "description": "コンセプトドリフトを検出",
                "parameters": {
                    "predictions": "予測値のリスト",
                    "actual_labels": "実際のラベルのリスト",
                    "window_size": "ドリフト検出のウィンドウサイズ",
                    "drift_threshold": "精度低下の閾値",
                },
            },
            "create_cloudwatch_alarm": {
                "name": "create_cloudwatch_alarm",
                "description": "CloudWatchアラームを作成",
                "parameters": {
                    "alarm_name": "アラーム名",
                    "endpoint_name": "エンドポイント名",
                    "metric_name": "メトリクス名",
                    "threshold": "閾値",
                    "comparison_operator": "比較演算子",
                    "evaluation_periods": "評価期間数",
                    "period_seconds": "期間（秒）",
                    "statistic": "統計値",
                },
            },
            "delete_cloudwatch_alarm": {
                "name": "delete_cloudwatch_alarm",
                "description": "CloudWatchアラームを削除",
                "parameters": {
                    "alarm_name": "アラーム名",
                },
            },
            "get_alarm_state": {
                "name": "get_alarm_state",
                "description": "CloudWatchアラームの状態を取得",
                "parameters": {
                    "alarm_name": "アラーム名",
                },
            },
            "update_dashboard": {
                "name": "update_dashboard",
                "description": "CloudWatchダッシュボードを更新",
                "parameters": {
                    "dashboard_name": "ダッシュボード名",
                    "dashboard_body": "ダッシュボード本体（ウィジェット定義）",
                },
            },
            "create_monitoring_dashboard": {
                "name": "create_monitoring_dashboard",
                "description": "モデル監視用ダッシュボードを作成",
                "parameters": {
                    "dashboard_name": "ダッシュボード名",
                    "endpoint_name": "エンドポイント名",
                    "region": "AWSリージョン",
                },
            },
            "delete_dashboard": {
                "name": "delete_dashboard",
                "description": "CloudWatchダッシュボードを削除",
                "parameters": {
                    "dashboard_name": "ダッシュボード名",
                },
            },
        }
