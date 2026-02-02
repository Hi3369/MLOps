"""
Dashboard Templates テスト

dashboard_templates.py のユニットテスト
"""

import os
from unittest.mock import patch

import pytest


class TestListDashboardTemplates:
    """list_dashboard_templates のテスト"""

    def test_list_templates_returns_all(self):
        from mcp_server.capabilities.model_monitoring.tools.dashboard_templates import (
            list_dashboard_templates,
        )

        result = list_dashboard_templates()
        assert result["status"] == "success"
        assert result["total_count"] == 4
        assert "pipeline_overview" in result["templates"]
        assert "model_performance" in result["templates"]
        assert "drift_monitoring" in result["templates"]
        assert "training_metrics" in result["templates"]

    def test_list_templates_structure(self):
        from mcp_server.capabilities.model_monitoring.tools.dashboard_templates import (
            list_dashboard_templates,
        )

        result = list_dashboard_templates()
        for name, info in result["templates"].items():
            assert "name" in info
            assert "description" in info
            assert "widgets_count" in info
            assert info["name"] == name
            assert isinstance(info["widgets_count"], int)
            assert info["widgets_count"] > 0


class TestCreateDashboardFromTemplate:
    """create_dashboard_from_template のテスト"""

    @patch.dict(os.environ, {"MLOPS_ENV": "test"})
    def test_pipeline_overview_template(self):
        from mcp_server.capabilities.model_monitoring.tools.dashboard_templates import (
            create_dashboard_from_template,
        )

        result = create_dashboard_from_template(
            template_name="pipeline_overview",
            dashboard_name="test-pipeline-dashboard",
            endpoint_name="test-endpoint",
        )
        assert result["status"] == "success"
        assert result["template_name"] == "pipeline_overview"
        assert result["dashboard_name"] == "test-pipeline-dashboard"
        assert result["endpoint_name"] == "test-endpoint"
        assert result["widgets_count"] == 8
        assert result["mock"] is True

    @patch.dict(os.environ, {"MLOPS_ENV": "test"})
    def test_model_performance_template(self):
        from mcp_server.capabilities.model_monitoring.tools.dashboard_templates import (
            create_dashboard_from_template,
        )

        result = create_dashboard_from_template(
            template_name="model_performance",
            dashboard_name="test-perf-dashboard",
            endpoint_name="test-endpoint",
        )
        assert result["status"] == "success"
        assert result["template_name"] == "model_performance"
        assert result["widgets_count"] == 6

    @patch.dict(os.environ, {"MLOPS_ENV": "test"})
    def test_drift_monitoring_template(self):
        from mcp_server.capabilities.model_monitoring.tools.dashboard_templates import (
            create_dashboard_from_template,
        )

        result = create_dashboard_from_template(
            template_name="drift_monitoring",
            dashboard_name="test-drift-dashboard",
            endpoint_name="test-endpoint",
        )
        assert result["status"] == "success"
        assert result["template_name"] == "drift_monitoring"
        assert result["widgets_count"] == 6

    @patch.dict(os.environ, {"MLOPS_ENV": "test"})
    def test_training_metrics_template(self):
        from mcp_server.capabilities.model_monitoring.tools.dashboard_templates import (
            create_dashboard_from_template,
        )

        result = create_dashboard_from_template(
            template_name="training_metrics",
            dashboard_name="test-training-dashboard",
            endpoint_name="test-endpoint",
        )
        assert result["status"] == "success"
        assert result["template_name"] == "training_metrics"
        assert result["widgets_count"] == 6

    @patch.dict(os.environ, {"MLOPS_ENV": "test"})
    def test_custom_region_and_namespace(self):
        from mcp_server.capabilities.model_monitoring.tools.dashboard_templates import (
            create_dashboard_from_template,
        )

        result = create_dashboard_from_template(
            template_name="pipeline_overview",
            dashboard_name="custom-dashboard",
            endpoint_name="custom-endpoint",
            region="ap-northeast-1",
            namespace="MLOps/Custom",
        )
        assert result["status"] == "success"
        assert result["region"] == "ap-northeast-1"
        assert result["namespace"] == "MLOps/Custom"

    @patch.dict(os.environ, {"MLOPS_ENV": "test"})
    def test_custom_widgets_added(self):
        from mcp_server.capabilities.model_monitoring.tools.dashboard_templates import (
            create_dashboard_from_template,
        )

        custom = [{"type": "text", "x": 0, "y": 20, "width": 24, "height": 1}]
        result = create_dashboard_from_template(
            template_name="pipeline_overview",
            dashboard_name="with-custom",
            endpoint_name="ep",
            custom_widgets=custom,
        )
        assert result["status"] == "success"
        assert result["custom_widgets_count"] == 1
        # 8 base + 1 custom
        assert result["widgets_count"] == 9

    def test_empty_template_name_raises(self):
        from mcp_server.capabilities.model_monitoring.tools.dashboard_templates import (
            create_dashboard_from_template,
        )

        with pytest.raises(ValueError, match="template_name must not be empty"):
            create_dashboard_from_template(
                template_name="",
                dashboard_name="dash",
                endpoint_name="ep",
            )

    def test_empty_dashboard_name_raises(self):
        from mcp_server.capabilities.model_monitoring.tools.dashboard_templates import (
            create_dashboard_from_template,
        )

        with pytest.raises(ValueError, match="dashboard_name must not be empty"):
            create_dashboard_from_template(
                template_name="pipeline_overview",
                dashboard_name="",
                endpoint_name="ep",
            )

    def test_empty_endpoint_name_raises(self):
        from mcp_server.capabilities.model_monitoring.tools.dashboard_templates import (
            create_dashboard_from_template,
        )

        with pytest.raises(ValueError, match="endpoint_name must not be empty"):
            create_dashboard_from_template(
                template_name="pipeline_overview",
                dashboard_name="dash",
                endpoint_name="",
            )

    def test_unknown_template_raises(self):
        from mcp_server.capabilities.model_monitoring.tools.dashboard_templates import (
            create_dashboard_from_template,
        )

        with pytest.raises(ValueError, match="Unknown template"):
            create_dashboard_from_template(
                template_name="nonexistent",
                dashboard_name="dash",
                endpoint_name="ep",
            )

    @patch.dict(os.environ, {"MLOPS_ENV": "test"})
    def test_dashboard_id_generated(self):
        from mcp_server.capabilities.model_monitoring.tools.dashboard_templates import (
            create_dashboard_from_template,
        )

        result = create_dashboard_from_template(
            template_name="pipeline_overview",
            dashboard_name="id-test",
            endpoint_name="ep",
        )
        assert "dashboard_id" in result
        assert len(result["dashboard_id"]) == 8

    @patch.dict(os.environ, {"MLOPS_ENV": "test"})
    def test_created_at_timestamp(self):
        from mcp_server.capabilities.model_monitoring.tools.dashboard_templates import (
            create_dashboard_from_template,
        )

        result = create_dashboard_from_template(
            template_name="pipeline_overview",
            dashboard_name="ts-test",
            endpoint_name="ep",
        )
        assert "created_at" in result
        assert "T" in result["created_at"]


class TestTemplateBuilders:
    """テンプレートビルダーの構造テスト"""

    def test_pipeline_overview_widgets_structure(self):
        from mcp_server.capabilities.model_monitoring.tools.dashboard_templates import (
            _build_pipeline_overview,
        )

        body = _build_pipeline_overview("ep", "us-east-1", "MLOps/Test")
        assert "widgets" in body
        assert len(body["widgets"]) == 8
        # ヘッダーはtextタイプ
        assert body["widgets"][0]["type"] == "text"

    def test_model_performance_widgets_structure(self):
        from mcp_server.capabilities.model_monitoring.tools.dashboard_templates import (
            _build_model_performance,
        )

        body = _build_model_performance("ep", "us-east-1", "MLOps/Test")
        assert "widgets" in body
        assert len(body["widgets"]) == 6

    def test_drift_monitoring_has_alarm_widget(self):
        from mcp_server.capabilities.model_monitoring.tools.dashboard_templates import (
            _build_drift_monitoring,
        )

        body = _build_drift_monitoring("ep", "us-east-1", "MLOps/Test")
        alarm_widgets = [w for w in body["widgets"] if w["type"] == "alarm"]
        assert len(alarm_widgets) == 1

    def test_training_metrics_widgets_structure(self):
        from mcp_server.capabilities.model_monitoring.tools.dashboard_templates import (
            _build_training_metrics,
        )

        body = _build_training_metrics("ep", "us-east-1", "MLOps/Test")
        assert "widgets" in body
        assert len(body["widgets"]) == 6

    def test_all_widgets_have_position(self):
        from mcp_server.capabilities.model_monitoring.tools.dashboard_templates import (
            _build_pipeline_overview,
        )

        body = _build_pipeline_overview("ep", "us-east-1", "MLOps/Test")
        for widget in body["widgets"]:
            assert "x" in widget
            assert "y" in widget
            assert "width" in widget
            assert "height" in widget
