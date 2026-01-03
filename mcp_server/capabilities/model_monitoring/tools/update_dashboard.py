"""
Update Dashboard Tool

ダッシュボード更新ツール
"""

import json
import logging
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def update_dashboard(
    dashboard_name: str,
    dashboard_body: Dict[str, Any],
) -> Dict[str, Any]:
    """
    CloudWatchダッシュボードを更新

    Args:
        dashboard_name: ダッシュボード名
        dashboard_body: ダッシュボード本体（ウィジェット定義）

    Returns:
        ダッシュボード更新結果辞書
    """
    logger.info(f"Updating CloudWatch dashboard: {dashboard_name}")

    # CloudWatchクライアント
    cloudwatch_client = boto3.client("cloudwatch")

    try:
        # ダッシュボード本体をJSON文字列に変換
        dashboard_body_json = json.dumps(dashboard_body)

        # ダッシュボードを作成/更新
        cloudwatch_client.put_dashboard(
            DashboardName=dashboard_name,
            DashboardBody=dashboard_body_json,
        )

        logger.info(f"CloudWatch dashboard updated: {dashboard_name}")

        return {
            "status": "success",
            "message": f"Dashboard updated: {dashboard_name}",
            "dashboard_info": {
                "dashboard_name": dashboard_name,
                "widgets_count": len(dashboard_body.get("widgets", [])),
            },
        }

    except ClientError as e:
        logger.error(f"Dashboard update error: {e}")
        raise ValueError(f"Failed to update dashboard: {e}")


def create_monitoring_dashboard(
    dashboard_name: str,
    endpoint_name: str,
    region: str = "us-east-1",
) -> Dict[str, Any]:
    """
    モデル監視用ダッシュボードを作成

    Args:
        dashboard_name: ダッシュボード名
        endpoint_name: エンドポイント名
        region: AWSリージョン

    Returns:
        ダッシュボード作成結果辞書
    """
    logger.info(f"Creating monitoring dashboard: {dashboard_name} for endpoint: {endpoint_name}")

    # ダッシュボード定義を作成
    dashboard_body = {
        "widgets": [
            # Invocationsウィジェット
            {
                "type": "metric",
                "x": 0,
                "y": 0,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/SageMaker", "Invocations", {"stat": "Sum"}],
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": region,
                    "title": f"Invocations - {endpoint_name}",
                    "period": 300,
                    "yAxis": {"left": {"min": 0}},
                },
            },
            # Model Latencyウィジェット
            {
                "type": "metric",
                "x": 12,
                "y": 0,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/SageMaker", "ModelLatency", {"stat": "Average"}],
                        [".", ".", {"stat": "p99"}],
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": region,
                    "title": f"Model Latency - {endpoint_name}",
                    "period": 300,
                    "yAxis": {"left": {"min": 0}},
                },
            },
            # Errorsウィジェット
            {
                "type": "metric",
                "x": 0,
                "y": 6,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/SageMaker", "Invocation4XXErrors", {"stat": "Sum"}],
                        [".", "Invocation5XXErrors", {"stat": "Sum"}],
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": region,
                    "title": f"Errors - {endpoint_name}",
                    "period": 300,
                    "yAxis": {"left": {"min": 0}},
                },
            },
            # CPU Utilizationウィジェット
            {
                "type": "metric",
                "x": 12,
                "y": 6,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/SageMaker", "CPUUtilization", {"stat": "Average"}],
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": region,
                    "title": f"CPU Utilization - {endpoint_name}",
                    "period": 300,
                    "yAxis": {"left": {"min": 0, "max": 100}},
                },
            },
            # Memory Utilizationウィジェット
            {
                "type": "metric",
                "x": 0,
                "y": 12,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/SageMaker", "MemoryUtilization", {"stat": "Average"}],
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": region,
                    "title": f"Memory Utilization - {endpoint_name}",
                    "period": 300,
                    "yAxis": {"left": {"min": 0, "max": 100}},
                },
            },
        ]
    }

    # 各ウィジェットにディメンションを追加
    for widget in dashboard_body["widgets"]:
        if widget["type"] == "metric":
            for metric in widget["properties"]["metrics"]:
                if len(metric) > 2 and isinstance(metric[2], dict):
                    metric[2]["dimensions"] = {
                        "EndpointName": endpoint_name,
                        "VariantName": "AllTraffic",
                    }

    # ダッシュボードを更新
    return update_dashboard(dashboard_name, dashboard_body)


def delete_dashboard(dashboard_name: str) -> Dict[str, Any]:
    """
    CloudWatchダッシュボードを削除

    Args:
        dashboard_name: ダッシュボード名

    Returns:
        ダッシュボード削除結果辞書
    """
    logger.info(f"Deleting CloudWatch dashboard: {dashboard_name}")

    # CloudWatchクライアント
    cloudwatch_client = boto3.client("cloudwatch")

    try:
        # ダッシュボードを削除
        cloudwatch_client.delete_dashboards(DashboardNames=[dashboard_name])

        logger.info(f"CloudWatch dashboard deleted: {dashboard_name}")

        return {
            "status": "success",
            "message": f"Dashboard deleted: {dashboard_name}",
            "deletion_info": {
                "dashboard_name": dashboard_name,
            },
        }

    except ClientError as e:
        logger.error(f"Dashboard deletion error: {e}")
        raise ValueError(f"Failed to delete dashboard: {e}")
