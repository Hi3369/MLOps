"""CloudWatch Metrics統合"""
from datetime import datetime
from typing import Dict, List

import boto3

from .logger import get_logger

logger = get_logger(__name__)


class MetricsPublisher:
    """CloudWatch Metricsへのメトリクス送信"""

    def __init__(self, config):
        self.config = config
        self.cloudwatch = boto3.client("cloudwatch", region_name=config.aws_region)
        self.namespace = "MLOps/UnifiedMCPServer"

    def put_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = "None",
        dimensions: List[Dict[str, str]] = None,
    ):
        """メトリクスを送信"""
        try:
            metric_data = {
                "MetricName": metric_name,
                "Value": value,
                "Unit": unit,
                "Timestamp": datetime.utcnow(),
            }

            if dimensions:
                metric_data["Dimensions"] = dimensions

            self.cloudwatch.put_metric_data(Namespace=self.namespace, MetricData=[metric_data])

            logger.debug(f"Published metric: {metric_name}={value}")

        except Exception:
            logger.error(f"Failed to publish metric: {metric_name}", exc_info=True)

    def record_tool_execution(self, tool_name: str, duration_ms: float, success: bool):
        """ツール実行メトリクスを記録"""
        self.put_metric(
            metric_name="ToolExecutionDuration",
            value=duration_ms,
            unit="Milliseconds",
            dimensions=[
                {"Name": "ToolName", "Value": tool_name},
                {"Name": "Success", "Value": str(success)},
            ],
        )

    def record_training_job(self, learning_type: str, duration_seconds: float):
        """学習ジョブメトリクスを記録"""
        self.put_metric(
            metric_name="TrainingJobDuration",
            value=duration_seconds,
            unit="Seconds",
            dimensions=[{"Name": "LearningType", "Value": learning_type}],
        )

    def record_model_evaluation(self, metric_name: str, metric_value: float, task_type: str):
        """モデル評価メトリクスを記録"""
        self.put_metric(
            metric_name=f"Model_{metric_name}",
            value=metric_value,
            unit="None",
            dimensions=[{"Name": "TaskType", "Value": task_type}],
        )
