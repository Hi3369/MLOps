"""
Create CloudWatch Alarm Tool

CloudWatchアラーム作成ツール
"""

import logging
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def create_cloudwatch_alarm(
    alarm_name: str,
    endpoint_name: str,
    metric_name: str,
    threshold: float,
    comparison_operator: str = "GreaterThanThreshold",
    evaluation_periods: int = 2,
    period_seconds: int = 300,
    statistic: str = "Average",
    actions_enabled: bool = True,
    alarm_actions: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    CloudWatchアラームを作成

    Args:
        alarm_name: アラーム名
        endpoint_name: エンドポイント名
        metric_name: メトリクス名
        threshold: 閾値
        comparison_operator: 比較演算子
        evaluation_periods: 評価期間数
        period_seconds: 期間（秒）
        statistic: 統計値（Average, Sum, Minimum, Maximum）
        actions_enabled: アクション有効化
        alarm_actions: アラームアクション（SNS ARNのリスト）

    Returns:
        アラーム作成結果辞書
    """
    logger.info(f"Creating CloudWatch alarm: {alarm_name}")

    # パラメータ検証
    valid_operators = [
        "GreaterThanThreshold",
        "GreaterThanOrEqualToThreshold",
        "LessThanThreshold",
        "LessThanOrEqualToThreshold",
    ]

    if comparison_operator not in valid_operators:
        raise ValueError(
            f"Invalid comparison_operator: {comparison_operator}. "
            f"Must be one of {valid_operators}"
        )

    valid_statistics = ["Average", "Sum", "Minimum", "Maximum", "SampleCount"]
    if statistic not in valid_statistics:
        raise ValueError(f"Invalid statistic: {statistic}. Must be one of {valid_statistics}")

    if evaluation_periods < 1:
        raise ValueError("evaluation_periods must be at least 1")

    if period_seconds < 60:
        raise ValueError("period_seconds must be at least 60")

    # CloudWatchクライアント
    cloudwatch_client = boto3.client("cloudwatch")

    try:
        # アラーム設定
        alarm_config = {
            "AlarmName": alarm_name,
            "ComparisonOperator": comparison_operator,
            "EvaluationPeriods": evaluation_periods,
            "MetricName": metric_name,
            "Namespace": "AWS/SageMaker",
            "Period": period_seconds,
            "Statistic": statistic,
            "Threshold": threshold,
            "ActionsEnabled": actions_enabled,
            "AlarmDescription": f"Alarm for {metric_name} on endpoint {endpoint_name}",
            "Dimensions": [
                {"Name": "EndpointName", "Value": endpoint_name},
                {"Name": "VariantName", "Value": "AllTraffic"},
            ],
        }

        # アラームアクションを追加
        if alarm_actions:
            alarm_config["AlarmActions"] = alarm_actions

        # アラームを作成
        cloudwatch_client.put_metric_alarm(**alarm_config)

        logger.info(f"CloudWatch alarm created: {alarm_name}")

        return {
            "status": "success",
            "message": f"CloudWatch alarm created: {alarm_name}",
            "alarm_info": {
                "alarm_name": alarm_name,
                "endpoint_name": endpoint_name,
                "metric_name": metric_name,
                "threshold": threshold,
                "comparison_operator": comparison_operator,
                "evaluation_periods": evaluation_periods,
                "period_seconds": period_seconds,
                "statistic": statistic,
                "actions_enabled": actions_enabled,
                "alarm_actions_count": len(alarm_actions) if alarm_actions else 0,
            },
        }

    except ClientError as e:
        logger.error(f"CloudWatch alarm creation error: {e}")
        raise ValueError(f"Failed to create CloudWatch alarm: {e}")


def delete_cloudwatch_alarm(alarm_name: str) -> Dict[str, Any]:
    """
    CloudWatchアラームを削除

    Args:
        alarm_name: アラーム名

    Returns:
        アラーム削除結果辞書
    """
    logger.info(f"Deleting CloudWatch alarm: {alarm_name}")

    # CloudWatchクライアント
    cloudwatch_client = boto3.client("cloudwatch")

    try:
        # アラームを削除
        cloudwatch_client.delete_alarms(AlarmNames=[alarm_name])

        logger.info(f"CloudWatch alarm deleted: {alarm_name}")

        return {
            "status": "success",
            "message": f"CloudWatch alarm deleted: {alarm_name}",
            "deletion_info": {
                "alarm_name": alarm_name,
            },
        }

    except ClientError as e:
        logger.error(f"CloudWatch alarm deletion error: {e}")
        raise ValueError(f"Failed to delete CloudWatch alarm: {e}")


def get_alarm_state(alarm_name: str) -> Dict[str, Any]:
    """
    CloudWatchアラームの状態を取得

    Args:
        alarm_name: アラーム名

    Returns:
        アラーム状態辞書
    """
    logger.info(f"Getting CloudWatch alarm state: {alarm_name}")

    # CloudWatchクライアント
    cloudwatch_client = boto3.client("cloudwatch")

    try:
        # アラーム情報を取得
        response = cloudwatch_client.describe_alarms(AlarmNames=[alarm_name])

        alarms = response.get("MetricAlarms", [])

        if not alarms:
            raise ValueError(f"Alarm not found: {alarm_name}")

        alarm = alarms[0]

        logger.info(f"CloudWatch alarm state retrieved: {alarm_name}")

        return {
            "status": "success",
            "message": f"Alarm state retrieved: {alarm_name}",
            "alarm_state": {
                "alarm_name": alarm["AlarmName"],
                "state_value": alarm["StateValue"],
                "state_reason": alarm.get("StateReason", ""),
                "state_updated_timestamp": (
                    alarm["StateUpdatedTimestamp"].isoformat()
                    if "StateUpdatedTimestamp" in alarm
                    else None
                ),
                "actions_enabled": alarm.get("ActionsEnabled", False),
                "alarm_arn": alarm.get("AlarmArn", ""),
            },
        }

    except ClientError as e:
        logger.error(f"CloudWatch alarm state retrieval error: {e}")
        raise ValueError(f"Failed to get alarm state: {e}")
