"""
Dashboard Templates Library

CloudWatchダッシュボードのテンプレートライブラリ。
用途別に事前定義されたダッシュボードテンプレートを提供します。
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)

# テンプレート定義
DASHBOARD_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "pipeline_overview": {
        "description": "MLOpsパイプライン全体の概要ダッシュボード",
        "widgets_count": 8,
    },
    "model_performance": {
        "description": "モデルパフォーマンス詳細ダッシュボード",
        "widgets_count": 6,
    },
    "drift_monitoring": {
        "description": "データドリフト・コンセプトドリフト監視ダッシュボード",
        "widgets_count": 6,
    },
    "training_metrics": {
        "description": "学習ジョブメトリクスダッシュボード",
        "widgets_count": 6,
    },
}


def _build_pipeline_overview(
    endpoint_name: str,
    region: str,
    namespace: str,
) -> Dict[str, Any]:
    """パイプライン概要ダッシュボード"""
    return {
        "widgets": [
            # ヘッダー
            {
                "type": "text",
                "x": 0,
                "y": 0,
                "width": 24,
                "height": 1,
                "properties": {
                    "markdown": f"# MLOps Pipeline Overview - {endpoint_name}",
                },
            },
            # Invocations
            {
                "type": "metric",
                "x": 0,
                "y": 1,
                "width": 8,
                "height": 6,
                "properties": {
                    "metrics": [
                        [
                            "AWS/SageMaker",
                            "Invocations",
                            "EndpointName",
                            endpoint_name,
                            "VariantName",
                            "AllTraffic",
                            {"stat": "Sum"},
                        ],
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": region,
                    "title": "Invocations",
                    "period": 300,
                },
            },
            # Latency (avg + p99)
            {
                "type": "metric",
                "x": 8,
                "y": 1,
                "width": 8,
                "height": 6,
                "properties": {
                    "metrics": [
                        [
                            "AWS/SageMaker",
                            "ModelLatency",
                            "EndpointName",
                            endpoint_name,
                            "VariantName",
                            "AllTraffic",
                            {"stat": "Average", "label": "Average"},
                        ],
                        ["...", {"stat": "p99", "label": "p99"}],
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": region,
                    "title": "Model Latency (ms)",
                    "period": 300,
                },
            },
            # Error Rates
            {
                "type": "metric",
                "x": 16,
                "y": 1,
                "width": 8,
                "height": 6,
                "properties": {
                    "metrics": [
                        [
                            "AWS/SageMaker",
                            "Invocation4XXErrors",
                            "EndpointName",
                            endpoint_name,
                            "VariantName",
                            "AllTraffic",
                            {"stat": "Sum", "label": "4XX"},
                        ],
                        [
                            ".",
                            "Invocation5XXErrors",
                            ".",
                            ".",
                            ".",
                            ".",
                            {"stat": "Sum", "label": "5XX"},
                        ],
                    ],
                    "view": "timeSeries",
                    "stacked": True,
                    "region": region,
                    "title": "Error Rates",
                    "period": 300,
                },
            },
            # CPU / Memory
            {
                "type": "metric",
                "x": 0,
                "y": 7,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [
                            "AWS/SageMaker",
                            "CPUUtilization",
                            "EndpointName",
                            endpoint_name,
                            "VariantName",
                            "AllTraffic",
                            {"stat": "Average", "label": "CPU"},
                        ],
                        [
                            ".",
                            "MemoryUtilization",
                            ".",
                            ".",
                            ".",
                            ".",
                            {"stat": "Average", "label": "Memory"},
                        ],
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": region,
                    "title": "Resource Utilization (%)",
                    "period": 300,
                    "yAxis": {"left": {"min": 0, "max": 100}},
                },
            },
            # Disk Utilization
            {
                "type": "metric",
                "x": 12,
                "y": 7,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [
                            "AWS/SageMaker",
                            "DiskUtilization",
                            "EndpointName",
                            endpoint_name,
                            "VariantName",
                            "AllTraffic",
                            {"stat": "Average"},
                        ],
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": region,
                    "title": "Disk Utilization (%)",
                    "period": 300,
                    "yAxis": {"left": {"min": 0, "max": 100}},
                },
            },
            # Custom MLOps Metrics
            {
                "type": "metric",
                "x": 0,
                "y": 13,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [namespace, "prediction_count", {"stat": "Sum"}],
                        [namespace, "error_count", {"stat": "Sum"}],
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": region,
                    "title": "MLOps Custom Metrics",
                    "period": 300,
                },
            },
            # Pipeline Execution Status
            {
                "type": "metric",
                "x": 12,
                "y": 13,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [namespace, "pipeline_succeeded", {"stat": "Sum"}],
                        [namespace, "pipeline_failed", {"stat": "Sum"}],
                    ],
                    "view": "timeSeries",
                    "stacked": True,
                    "region": region,
                    "title": "Pipeline Executions",
                    "period": 3600,
                },
            },
        ],
    }


def _build_model_performance(
    endpoint_name: str,
    region: str,
    namespace: str,
) -> Dict[str, Any]:
    """モデルパフォーマンス詳細ダッシュボード"""
    return {
        "widgets": [
            {
                "type": "text",
                "x": 0,
                "y": 0,
                "width": 24,
                "height": 1,
                "properties": {
                    "markdown": f"# Model Performance - {endpoint_name}",
                },
            },
            # Accuracy
            {
                "type": "metric",
                "x": 0,
                "y": 1,
                "width": 8,
                "height": 6,
                "properties": {
                    "metrics": [
                        [namespace, "accuracy", {"stat": "Average"}],
                        [namespace, "f1_score", {"stat": "Average"}],
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": region,
                    "title": "Model Accuracy & F1",
                    "period": 3600,
                    "yAxis": {"left": {"min": 0, "max": 1}},
                },
            },
            # Precision / Recall
            {
                "type": "metric",
                "x": 8,
                "y": 1,
                "width": 8,
                "height": 6,
                "properties": {
                    "metrics": [
                        [namespace, "precision", {"stat": "Average"}],
                        [namespace, "recall", {"stat": "Average"}],
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": region,
                    "title": "Precision & Recall",
                    "period": 3600,
                    "yAxis": {"left": {"min": 0, "max": 1}},
                },
            },
            # Prediction Distribution
            {
                "type": "metric",
                "x": 16,
                "y": 1,
                "width": 8,
                "height": 6,
                "properties": {
                    "metrics": [
                        [namespace, "prediction_positive", {"stat": "Sum"}],
                        [namespace, "prediction_negative", {"stat": "Sum"}],
                    ],
                    "view": "timeSeries",
                    "stacked": True,
                    "region": region,
                    "title": "Prediction Distribution",
                    "period": 3600,
                },
            },
            # Latency Percentiles
            {
                "type": "metric",
                "x": 0,
                "y": 7,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [
                            "AWS/SageMaker",
                            "ModelLatency",
                            "EndpointName",
                            endpoint_name,
                            "VariantName",
                            "AllTraffic",
                            {"stat": "p50", "label": "p50"},
                        ],
                        ["...", {"stat": "p90", "label": "p90"}],
                        ["...", {"stat": "p99", "label": "p99"}],
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": region,
                    "title": "Latency Percentiles (ms)",
                    "period": 300,
                },
            },
            # Throughput
            {
                "type": "metric",
                "x": 12,
                "y": 7,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [
                            "AWS/SageMaker",
                            "Invocations",
                            "EndpointName",
                            endpoint_name,
                            "VariantName",
                            "AllTraffic",
                            {"stat": "Sum", "label": "Invocations/period"},
                        ],
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": region,
                    "title": "Throughput",
                    "period": 60,
                },
            },
        ],
    }


def _build_drift_monitoring(
    endpoint_name: str,
    region: str,
    namespace: str,
) -> Dict[str, Any]:
    """ドリフト監視ダッシュボード"""
    return {
        "widgets": [
            {
                "type": "text",
                "x": 0,
                "y": 0,
                "width": 24,
                "height": 1,
                "properties": {
                    "markdown": f"# Drift Monitoring - {endpoint_name}",
                },
            },
            # Data Drift Score
            {
                "type": "metric",
                "x": 0,
                "y": 1,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [namespace, "data_drift_score", {"stat": "Average"}],
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": region,
                    "title": "Data Drift Score",
                    "period": 3600,
                    "yAxis": {"left": {"min": 0, "max": 1}},
                    "annotations": {
                        "horizontal": [
                            {
                                "label": "Threshold",
                                "value": 0.05,
                                "color": "#d62728",
                            },
                        ],
                    },
                },
            },
            # Concept Drift (Accuracy Over Time)
            {
                "type": "metric",
                "x": 12,
                "y": 1,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [namespace, "concept_drift_score", {"stat": "Average"}],
                        [namespace, "accuracy", {"stat": "Average"}],
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": region,
                    "title": "Concept Drift & Accuracy",
                    "period": 3600,
                    "yAxis": {"left": {"min": 0, "max": 1}},
                },
            },
            # Feature Distribution Shift
            {
                "type": "metric",
                "x": 0,
                "y": 7,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [namespace, "feature_drift_count", {"stat": "Sum"}],
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": region,
                    "title": "Features with Drift Detected",
                    "period": 3600,
                },
            },
            # Prediction Stability
            {
                "type": "metric",
                "x": 12,
                "y": 7,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [namespace, "prediction_mean", {"stat": "Average"}],
                        [namespace, "prediction_stddev", {"stat": "Average"}],
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": region,
                    "title": "Prediction Stability",
                    "period": 3600,
                },
            },
            # Alarm Status
            {
                "type": "alarm",
                "x": 0,
                "y": 13,
                "width": 24,
                "height": 3,
                "properties": {
                    "alarms": [],
                    "title": "Drift Alarms",
                },
            },
        ],
    }


def _build_training_metrics(
    endpoint_name: str,
    region: str,
    namespace: str,
) -> Dict[str, Any]:
    """学習メトリクスダッシュボード"""
    return {
        "widgets": [
            {
                "type": "text",
                "x": 0,
                "y": 0,
                "width": 24,
                "height": 1,
                "properties": {
                    "markdown": "# Training Metrics Dashboard",
                },
            },
            # Training Loss
            {
                "type": "metric",
                "x": 0,
                "y": 1,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [namespace, "training_loss", {"stat": "Average"}],
                        [namespace, "validation_loss", {"stat": "Average"}],
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": region,
                    "title": "Training & Validation Loss",
                    "period": 60,
                },
            },
            # Learning Rate
            {
                "type": "metric",
                "x": 12,
                "y": 1,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [namespace, "learning_rate", {"stat": "Average"}],
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": region,
                    "title": "Learning Rate",
                    "period": 60,
                },
            },
            # Training Job Duration
            {
                "type": "metric",
                "x": 0,
                "y": 7,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [namespace, "training_duration_seconds", {"stat": "Average"}],
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": region,
                    "title": "Training Job Duration (s)",
                    "period": 3600,
                },
            },
            # GPU/Instance Utilization
            {
                "type": "metric",
                "x": 12,
                "y": 7,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [
                            "/aws/sagemaker/TrainingJobs",
                            "CPUUtilization",
                            {"stat": "Average", "label": "CPU"},
                        ],
                        [
                            ".",
                            "MemoryUtilization",
                            {"stat": "Average", "label": "Memory"},
                        ],
                        [
                            ".",
                            "GPUUtilization",
                            {"stat": "Average", "label": "GPU"},
                        ],
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": region,
                    "title": "Training Resource Utilization (%)",
                    "period": 60,
                    "yAxis": {"left": {"min": 0, "max": 100}},
                },
            },
            # Epoch Metrics
            {
                "type": "metric",
                "x": 0,
                "y": 13,
                "width": 24,
                "height": 6,
                "properties": {
                    "metrics": [
                        [
                            namespace,
                            "epoch_accuracy",
                            {"stat": "Average", "label": "Accuracy"},
                        ],
                        [
                            namespace,
                            "epoch_loss",
                            {"stat": "Average", "label": "Loss"},
                        ],
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": region,
                    "title": "Per-Epoch Metrics",
                    "period": 60,
                },
            },
        ],
    }


# テンプレートビルダーのマッピング
_TEMPLATE_BUILDERS = {
    "pipeline_overview": _build_pipeline_overview,
    "model_performance": _build_model_performance,
    "drift_monitoring": _build_drift_monitoring,
    "training_metrics": _build_training_metrics,
}


def list_dashboard_templates() -> Dict[str, Any]:
    """
    利用可能なダッシュボードテンプレート一覧を返す

    Returns:
        テンプレート一覧辞書
    """
    logger.info("Listing dashboard templates")

    return {
        "status": "success",
        "templates": {
            name: {
                "name": name,
                "description": info["description"],
                "widgets_count": info["widgets_count"],
            }
            for name, info in DASHBOARD_TEMPLATES.items()
        },
        "total_count": len(DASHBOARD_TEMPLATES),
    }


def create_dashboard_from_template(
    template_name: str,
    dashboard_name: str,
    endpoint_name: str,
    region: Optional[str] = None,
    namespace: Optional[str] = None,
    custom_widgets: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    テンプレートからCloudWatchダッシュボードを作成

    Args:
        template_name: テンプレート名
        dashboard_name: 作成するダッシュボード名
        endpoint_name: SageMakerエンドポイント名
        region: AWSリージョン
        namespace: CloudWatchカスタム名前空間
        custom_widgets: 追加カスタムウィジェット

    Returns:
        ダッシュボード作成結果辞書
    """
    if not template_name:
        raise ValueError("template_name must not be empty")
    if not dashboard_name:
        raise ValueError("dashboard_name must not be empty")
    if not endpoint_name:
        raise ValueError("endpoint_name must not be empty")
    if template_name not in DASHBOARD_TEMPLATES:
        available = ", ".join(DASHBOARD_TEMPLATES.keys())
        raise ValueError(f"Unknown template: {template_name}. Available: {available}")

    logger.info(
        f"Creating dashboard '{dashboard_name}' "
        f"from template '{template_name}' "
        f"for endpoint '{endpoint_name}'"
    )

    env = os.environ.get("MLOPS_ENV", "development")
    resolved_region = region or os.environ.get("AWS_DEFAULT_REGION", "ap-northeast-1")
    resolved_namespace = namespace or f"MLOps/{env.capitalize()}"

    timestamp = datetime.now(timezone.utc).isoformat()
    dashboard_id = str(uuid4())[:8]

    if env in ["development", "test"]:
        return _mock_create_dashboard(
            template_name=template_name,
            dashboard_name=dashboard_name,
            endpoint_name=endpoint_name,
            region=resolved_region,
            namespace=resolved_namespace,
            custom_widgets=custom_widgets,
            dashboard_id=dashboard_id,
            timestamp=timestamp,
        )

    # 本番環境: テンプレートをビルドしてCloudWatchに反映
    builder = _TEMPLATE_BUILDERS[template_name]
    dashboard_body = builder(
        endpoint_name=endpoint_name,
        region=resolved_region,
        namespace=resolved_namespace,
    )

    # カスタムウィジェットを追加
    if custom_widgets:
        dashboard_body["widgets"].extend(custom_widgets)

    import boto3
    from botocore.exceptions import ClientError

    try:
        cloudwatch = boto3.client("cloudwatch", region_name=resolved_region)
        cloudwatch.put_dashboard(
            DashboardName=dashboard_name,
            DashboardBody=json.dumps(dashboard_body),
        )

        return {
            "status": "success",
            "dashboard_id": dashboard_id,
            "dashboard_name": dashboard_name,
            "template_name": template_name,
            "endpoint_name": endpoint_name,
            "region": resolved_region,
            "namespace": resolved_namespace,
            "widgets_count": len(dashboard_body["widgets"]),
            "custom_widgets_count": len(custom_widgets) if custom_widgets else 0,
            "created_at": timestamp,
        }

    except ClientError as e:
        logger.error(f"Failed to create dashboard from template: {e}")
        raise ValueError(f"Failed to create dashboard from template: {e}")


def _mock_create_dashboard(
    template_name: str,
    dashboard_name: str,
    endpoint_name: str,
    region: str,
    namespace: str,
    custom_widgets: Optional[List[Dict[str, Any]]],
    dashboard_id: str,
    timestamp: str,
) -> Dict[str, Any]:
    """モック: テンプレートからダッシュボード作成"""
    template_info = DASHBOARD_TEMPLATES[template_name]
    widgets_count = template_info["widgets_count"]
    custom_count = len(custom_widgets) if custom_widgets else 0

    return {
        "status": "success",
        "dashboard_id": dashboard_id,
        "dashboard_name": dashboard_name,
        "template_name": template_name,
        "endpoint_name": endpoint_name,
        "region": region,
        "namespace": namespace,
        "widgets_count": widgets_count + custom_count,
        "custom_widgets_count": custom_count,
        "created_at": timestamp,
        "mock": True,
    }
