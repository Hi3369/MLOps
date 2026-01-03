"""
Collect System Metrics Tool

システムメトリクス収集ツール（CPU/Memory/Latency）
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def collect_system_metrics(
    endpoint_name: str,
    time_range_minutes: int = 60,
    metric_period_seconds: int = 300,
) -> Dict[str, Any]:
    """
    SageMakerエンドポイントのシステムメトリクスを収集

    Args:
        endpoint_name: エンドポイント名
        time_range_minutes: メトリクス取得期間（分）
        metric_period_seconds: メトリクス集計期間（秒）

    Returns:
        システムメトリクス辞書
    """
    logger.info(f"Collecting system metrics for endpoint: {endpoint_name}")

    # CloudWatchクライアント
    cloudwatch_client = boto3.client("cloudwatch")

    # メトリクス取得期間
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=time_range_minutes)

    # 収集するシステムメトリクス
    system_metrics = [
        "CPUUtilization",
        "MemoryUtilization",
        "DiskUtilization",
        "ModelLatency",
        "OverheadLatency",
    ]

    try:
        metrics_data = {}

        for metric_name in system_metrics:
            metrics_data[metric_name] = _get_metric_statistics(
                cloudwatch_client,
                endpoint_name,
                metric_name,
                start_time,
                end_time,
                metric_period_seconds,
            )

        logger.info(f"System metrics collected for endpoint: {endpoint_name}")

        return {
            "status": "success",
            "message": f"System metrics collected for endpoint: {endpoint_name}",
            "metrics_info": {
                "endpoint_name": endpoint_name,
                "time_range": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "duration_minutes": time_range_minutes,
                },
                "period_seconds": metric_period_seconds,
                "metrics": metrics_data,
            },
        }

    except ClientError as e:
        logger.error(f"System metrics collection error: {e}")
        raise ValueError(f"Failed to collect system metrics: {e}")


def _get_metric_statistics(
    cloudwatch_client,
    endpoint_name: str,
    metric_name: str,
    start_time: datetime,
    end_time: datetime,
    period: int,
) -> Dict[str, Any]:
    """CloudWatchメトリクス統計を取得"""
    try:
        response = cloudwatch_client.get_metric_statistics(
            Namespace="AWS/SageMaker",
            MetricName=metric_name,
            Dimensions=[
                {"Name": "EndpointName", "Value": endpoint_name},
                {"Name": "VariantName", "Value": "AllTraffic"},
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=period,
            Statistics=["Average", "Minimum", "Maximum", "Sum", "SampleCount"],
        )

        datapoints = response.get("Datapoints", [])

        if not datapoints:
            return {
                "available": False,
                "datapoints_count": 0,
                "message": "No data available for this metric",
            }

        # タイムスタンプでソート
        sorted_datapoints = sorted(datapoints, key=lambda x: x["Timestamp"])

        # 最新のデータポイント
        latest = sorted_datapoints[-1]

        # 統計情報を計算
        averages = [dp.get("Average", 0) for dp in sorted_datapoints if "Average" in dp]
        avg_of_averages = sum(averages) / len(averages) if averages else 0

        return {
            "available": True,
            "datapoints_count": len(datapoints),
            "latest": {
                "timestamp": latest["Timestamp"].isoformat(),
                "average": latest.get("Average", 0),
                "minimum": latest.get("Minimum", 0),
                "maximum": latest.get("Maximum", 0),
                "sum": latest.get("Sum", 0),
                "sample_count": latest.get("SampleCount", 0),
            },
            "aggregated": {
                "average": avg_of_averages,
                "min": min([dp.get("Minimum", 0) for dp in sorted_datapoints]),
                "max": max([dp.get("Maximum", 0) for dp in sorted_datapoints]),
            },
            "datapoints": [
                {
                    "timestamp": dp["Timestamp"].isoformat(),
                    "average": dp.get("Average", 0),
                    "minimum": dp.get("Minimum", 0),
                    "maximum": dp.get("Maximum", 0),
                }
                for dp in sorted_datapoints
            ],
        }

    except ClientError as e:
        logger.warning(f"Failed to fetch metric {metric_name}: {e}")
        return {
            "available": False,
            "error": str(e),
            "message": f"Failed to fetch metric: {metric_name}",
        }
