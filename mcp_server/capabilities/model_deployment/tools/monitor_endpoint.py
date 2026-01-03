"""
Monitor Endpoint Tool

エンドポイント監視・ヘルスチェックツール
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def monitor_endpoint(
    endpoint_name: str,
    include_metrics: bool = True,
    metric_period_minutes: int = 60,
) -> Dict[str, Any]:
    """
    エンドポイントのステータスとメトリクスを監視

    Args:
        endpoint_name: エンドポイント名
        include_metrics: メトリクスを含めるか
        metric_period_minutes: メトリクス取得期間（分）

    Returns:
        監視結果辞書
    """
    logger.info(f"Monitoring endpoint: {endpoint_name}")

    # SageMakerクライアント
    sagemaker_client = boto3.client("sagemaker")

    try:
        # エンドポイント情報を取得
        response = sagemaker_client.describe_endpoint(EndpointName=endpoint_name)

        endpoint_info = {
            "endpoint_name": response["EndpointName"],
            "endpoint_arn": response["EndpointArn"],
            "endpoint_status": response["EndpointStatus"],
            "creation_time": response["CreationTime"].isoformat(),
            "last_modified_time": response["LastModifiedTime"].isoformat(),
        }

        # プロダクションバリアント情報
        variants_info = []
        for variant in response.get("ProductionVariants", []):
            variants_info.append(
                {
                    "variant_name": variant["VariantName"],
                    "current_weight": variant.get("CurrentWeight", 0),
                    "desired_weight": variant.get("DesiredWeight", 0),
                    "current_instance_count": variant.get("CurrentInstanceCount", 0),
                    "desired_instance_count": variant.get("DesiredInstanceCount", 0),
                }
            )

        endpoint_info["production_variants"] = variants_info

        # メトリクス取得
        metrics_info = {}
        if include_metrics:
            metrics_info = _get_endpoint_metrics(endpoint_name, metric_period_minutes)

        logger.info(f"Endpoint monitoring completed: {endpoint_name}")

        return {
            "status": "success",
            "message": f"Endpoint monitoring completed: {endpoint_name}",
            "monitoring_info": {
                **endpoint_info,
                "metrics": metrics_info,
            },
        }

    except ClientError as e:
        logger.error(f"Endpoint monitoring error: {e}")
        if e.response["Error"]["Code"] == "ValidationException":
            raise ValueError(f"Endpoint not found: {endpoint_name}")
        raise ValueError(f"Failed to monitor endpoint: {e}")


def health_check_endpoint(
    endpoint_name: str,
    test_payload: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    エンドポイントのヘルスチェックを実行

    Args:
        endpoint_name: エンドポイント名
        test_payload: テストペイロード（省略時はダミーデータ）

    Returns:
        ヘルスチェック結果辞書
    """
    logger.info(f"Health check for endpoint: {endpoint_name}")

    # SageMakerランタイムクライアント
    runtime_client = boto3.client("sagemaker-runtime")

    # テストペイロードの準備
    if test_payload is None:
        # デフォルトのダミーデータ
        test_payload = {"data": [[1, 2, 3, 4]]}

    try:
        # エンドポイントを呼び出し
        start_time = datetime.now()

        response = runtime_client.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType="application/json",
            Body=json.dumps(test_payload),
        )

        end_time = datetime.now()
        latency_ms = (end_time - start_time).total_seconds() * 1000

        # レスポンスを読み取り
        response_body = response["Body"].read().decode("utf-8")

        logger.info(f"Health check passed for endpoint: {endpoint_name}")

        return {
            "status": "success",
            "message": f"Health check passed for endpoint: {endpoint_name}",
            "health_check_info": {
                "endpoint_name": endpoint_name,
                "is_healthy": True,
                "latency_ms": latency_ms,
                "response_status_code": response["ResponseMetadata"]["HTTPStatusCode"],
                "test_payload": test_payload,
                "response_preview": response_body[:200],  # 最初の200文字
            },
        }

    except ClientError as e:
        logger.error(f"Health check failed for endpoint: {endpoint_name}: {e}")

        return {
            "status": "error",
            "message": f"Health check failed for endpoint: {endpoint_name}",
            "health_check_info": {
                "endpoint_name": endpoint_name,
                "is_healthy": False,
                "error": str(e),
                "test_payload": test_payload,
            },
        }


def _get_endpoint_metrics(
    endpoint_name: str,
    period_minutes: int,
) -> Dict[str, Any]:
    """エンドポイントのCloudWatchメトリクスを取得"""
    # CloudWatchクライアント
    cloudwatch_client = boto3.client("cloudwatch")

    # メトリクス取得期間
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=period_minutes)

    metrics_to_fetch = [
        "Invocations",
        "ModelLatency",
        "Invocation4XXErrors",
        "Invocation5XXErrors",
    ]

    metrics_data = {}

    for metric_name in metrics_to_fetch:
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
                Period=300,  # 5分間隔
                Statistics=["Sum", "Average", "Maximum"],
            )

            datapoints = response.get("Datapoints", [])
            if datapoints:
                # 最新のデータポイント
                latest = max(datapoints, key=lambda x: x["Timestamp"])
                metrics_data[metric_name] = {
                    "sum": latest.get("Sum", 0),
                    "average": latest.get("Average", 0),
                    "maximum": latest.get("Maximum", 0),
                    "timestamp": latest["Timestamp"].isoformat(),
                }
            else:
                metrics_data[metric_name] = {
                    "sum": 0,
                    "average": 0,
                    "maximum": 0,
                    "timestamp": None,
                }

        except ClientError as e:
            logger.warning(f"Failed to fetch metric {metric_name}: {e}")
            metrics_data[metric_name] = {"error": str(e)}

    return {
        "period_minutes": period_minutes,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "metrics": metrics_data,
    }
