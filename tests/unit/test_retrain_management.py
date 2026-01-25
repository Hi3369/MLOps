"""
Retrain Management Capability Unit Tests

再学習管理機能の単体テスト
"""

import pytest

from mcp_server.capabilities.retrain_management.capability import (
    RetrainManagementCapability,
)
from mcp_server.capabilities.retrain_management.tools import (
    check_retrain_triggers,
    create_retrain_issue,
    evaluate_trigger_conditions,
    schedule_periodic_retrain,
    start_retrain_workflow,
)


class TestRetrainManagementCapability:
    """RetrainManagementCapability クラスのテスト"""

    def test_initialization(self):
        """初期化テスト"""
        capability = RetrainManagementCapability()
        assert capability is not None
        assert capability._tools is not None
        assert len(capability._tools) == 5

    def test_get_tools(self):
        """ツール取得テスト"""
        capability = RetrainManagementCapability()
        tools = capability.get_tools()

        assert "check_retrain_triggers" in tools
        assert "evaluate_trigger_conditions" in tools
        assert "create_retrain_issue" in tools
        assert "start_retrain_workflow" in tools
        assert "schedule_periodic_retrain" in tools

    def test_get_tool_schemas(self):
        """ツールスキーマ取得テスト"""
        capability = RetrainManagementCapability()
        schemas = capability.get_tool_schemas()

        assert len(schemas) == 5
        for tool_name, schema in schemas.items():
            assert "name" in schema
            assert "description" in schema
            assert "parameters" in schema


class TestCheckRetrainTriggers:
    """check_retrain_triggers ツールのテスト"""

    def test_check_basic_triggers(self):
        """基本的なトリガーチェックテスト"""
        result = check_retrain_triggers(model_name="test-model")

        assert result["status"] == "success"
        assert "trigger_result" in result
        assert result["trigger_result"]["model_name"] == "test-model"
        assert result["trigger_result"]["mock"] is True

    def test_check_with_custom_config(self):
        """カスタム設定でのトリガーチェックテスト"""
        config = {
            "data_change": {"enabled": True, "s3_path": "s3://bucket/data"},
            "drift_detection": {"enabled": True, "threshold": 0.2},
        }
        result = check_retrain_triggers(
            model_name="test-model",
            trigger_config=config,
        )

        assert result["status"] == "success"

    def test_check_all_trigger_types(self):
        """全5種類のトリガーがチェックされるテスト"""
        result = check_retrain_triggers(model_name="test-model")
        triggers = result["trigger_result"]["triggers"]

        expected_types = [
            "data_change",
            "code_change",
            "schedule",
            "metrics_degradation",
            "drift_detection",
        ]
        for trigger_type in expected_types:
            assert trigger_type in triggers
            assert "enabled" in triggers[trigger_type]
            assert "triggered" in triggers[trigger_type]

    def test_check_any_triggered_flag(self):
        """any_triggered フラグのテスト"""
        result = check_retrain_triggers(model_name="test-model")
        assert "any_triggered" in result["trigger_result"]

    def test_check_empty_model_name_error(self):
        """空モデル名でエラーテスト"""
        with pytest.raises(ValueError, match="model_name must not be empty"):
            check_retrain_triggers(model_name="")


class TestEvaluateTriggerConditions:
    """evaluate_trigger_conditions ツールのテスト"""

    def test_evaluate_drift_threshold_triggered(self):
        """ドリフト閾値条件（トリガー発火）テスト"""
        conditions = [{"type": "drift_threshold", "threshold": 0.1, "comparison": "gt"}]
        metrics = {"drift_score": 0.15}
        result = evaluate_trigger_conditions(conditions, metrics)

        assert result["status"] == "success"
        assert result["evaluation_result"]["conditions"][0]["triggered"] is True
        assert result["evaluation_result"]["any_triggered"] is True

    def test_evaluate_drift_threshold_not_triggered(self):
        """ドリフト閾値条件（トリガー非発火）テスト"""
        conditions = [{"type": "drift_threshold", "threshold": 0.1, "comparison": "gt"}]
        metrics = {"drift_score": 0.05}
        result = evaluate_trigger_conditions(conditions, metrics)

        assert result["status"] == "success"
        assert result["evaluation_result"]["conditions"][0]["triggered"] is False

    def test_evaluate_performance_threshold(self):
        """パフォーマンス閾値条件テスト"""
        conditions = [
            {
                "type": "performance_threshold",
                "metric": "accuracy",
                "threshold": 0.9,
                "comparison": "lt",
            }
        ]
        metrics = {"accuracy": 0.85}
        result = evaluate_trigger_conditions(conditions, metrics)

        assert result["status"] == "success"
        assert result["evaluation_result"]["conditions"][0]["triggered"] is True

    def test_evaluate_schedule_condition(self):
        """スケジュール条件テスト"""
        conditions = [{"type": "schedule", "threshold_days": 7}]
        metrics = {"last_retrain_time": "2024-01-01T00:00:00Z"}
        result = evaluate_trigger_conditions(conditions, metrics)

        assert result["status"] == "success"

    def test_evaluate_data_volume_condition(self):
        """データ量条件テスト"""
        conditions = [{"type": "data_volume", "threshold": 1000, "comparison": "gte"}]
        metrics = {"data_sample_count": 1500}
        result = evaluate_trigger_conditions(conditions, metrics)

        assert result["status"] == "success"
        assert result["evaluation_result"]["conditions"][0]["triggered"] is True

    def test_evaluate_multiple_conditions(self):
        """複数条件テスト"""
        conditions = [
            {"type": "drift_threshold", "threshold": 0.1, "comparison": "gt"},
            {
                "type": "performance_threshold",
                "metric": "accuracy",
                "threshold": 0.9,
                "comparison": "lt",
            },
        ]
        metrics = {"drift_score": 0.05, "accuracy": 0.95}
        result = evaluate_trigger_conditions(conditions, metrics)

        assert result["status"] == "success"
        assert result["evaluation_result"]["total_conditions"] == 2
        assert result["evaluation_result"]["triggered_count"] == 0

    def test_evaluate_empty_conditions_error(self):
        """空条件でエラーテスト"""
        with pytest.raises(ValueError, match="conditions must not be empty"):
            evaluate_trigger_conditions([], {"drift_score": 0.1})

    def test_evaluate_empty_metrics_error(self):
        """空メトリクスでエラーテスト"""
        with pytest.raises(ValueError, match="current_metrics must not be empty"):
            evaluate_trigger_conditions([{"type": "drift_threshold", "threshold": 0.1}], {})


class TestCreateRetrainIssue:
    """create_retrain_issue ツールのテスト"""

    def test_create_basic_issue(self):
        """基本的なIssue作成テスト"""
        result = create_retrain_issue(
            model_name="test-model",
            reason="drift_detection",
        )

        assert result["status"] == "success"
        assert "issue_result" in result
        assert result["issue_result"]["model_name"] == "test-model"
        assert result["issue_result"]["reason"] == "drift_detection"
        assert result["issue_result"]["mock"] is True

    def test_create_issue_with_trigger_details(self):
        """トリガー詳細付きIssue作成テスト"""
        trigger_details = {
            "drift_score": 0.15,
            "threshold": 0.1,
            "affected_features": ["feature1", "feature2"],
        }
        result = create_retrain_issue(
            model_name="test-model",
            reason="drift_detection",
            trigger_details=trigger_details,
        )

        assert result["status"] == "success"

    def test_create_issue_all_valid_reasons(self):
        """全有効理由でのIssue作成テスト"""
        valid_reasons = [
            "data_change",
            "code_change",
            "schedule",
            "metrics_degradation",
            "drift_detection",
            "manual",
        ]
        for reason in valid_reasons:
            result = create_retrain_issue(
                model_name="test-model",
                reason=reason,
            )
            assert result["status"] == "success"
            assert result["issue_result"]["reason"] == reason

    def test_create_issue_has_labels(self):
        """Issueラベルテスト"""
        result = create_retrain_issue(
            model_name="test-model",
            reason="drift_detection",
        )

        assert "labels" in result["issue_result"]
        assert "retrain" in result["issue_result"]["labels"]
        assert "mlops" in result["issue_result"]["labels"]

    def test_create_issue_empty_model_name_error(self):
        """空モデル名でエラーテスト"""
        with pytest.raises(ValueError, match="model_name must not be empty"):
            create_retrain_issue(model_name="", reason="drift_detection")

    def test_create_issue_empty_reason_error(self):
        """空理由でエラーテスト"""
        with pytest.raises(ValueError, match="reason must not be empty"):
            create_retrain_issue(model_name="test-model", reason="")

    def test_create_issue_invalid_reason_error(self):
        """無効な理由でエラーテスト"""
        with pytest.raises(ValueError, match="Invalid reason"):
            create_retrain_issue(model_name="test-model", reason="invalid_reason")


class TestStartRetrainWorkflow:
    """start_retrain_workflow ツールのテスト"""

    def test_start_basic_workflow(self):
        """基本的なワークフロー起動テスト"""
        model_config = {
            "model_name": "test-model",
            "model_type": "xgboost",
        }
        result = start_retrain_workflow(
            workflow_name="mlops-retraining-workflow",
            model_config=model_config,
        )

        assert result["status"] == "success"
        assert "workflow_result" in result
        assert result["workflow_result"]["execution_status"] == "RUNNING"
        assert result["workflow_result"]["mock"] is True

    def test_start_workflow_with_dataset_uri(self):
        """データセットURI付きワークフロー起動テスト"""
        result = start_retrain_workflow(
            workflow_name="mlops-retraining-workflow",
            model_config={"model_name": "test-model"},
            dataset_uri="s3://bucket/data/train.csv",
        )

        assert result["status"] == "success"

    def test_start_workflow_with_comparison_config(self):
        """比較設定付きワークフロー起動テスト（FR-026対応）"""
        comparison_config = {
            "metrics_to_compare": ["accuracy", "f1_score"],
            "improvement_threshold": 0.01,
            "auto_deploy_on_improvement": True,
        }
        result = start_retrain_workflow(
            workflow_name="mlops-retraining-workflow",
            model_config={"model_name": "test-model"},
            comparison_config=comparison_config,
        )

        assert result["status"] == "success"
        assert "comparison_config" in result["workflow_result"]["input_params"]

    def test_start_workflow_version_increment(self):
        """バージョンインクリメントテスト（FR-027対応）"""
        model_config = {
            "model_name": "test-model",
            "current_version": "v1.2.3",
        }
        result = start_retrain_workflow(
            workflow_name="mlops-retraining-workflow",
            model_config=model_config,
        )

        assert result["status"] == "success"
        assert result["workflow_result"]["next_version"] == "v1.3.0"

    def test_start_workflow_empty_workflow_name_error(self):
        """空ワークフロー名でエラーテスト"""
        with pytest.raises(ValueError, match="workflow_name must not be empty"):
            start_retrain_workflow(
                workflow_name="",
                model_config={"model_name": "test"},
            )

    def test_start_workflow_empty_model_config_error(self):
        """空モデル設定でエラーテスト"""
        with pytest.raises(ValueError, match="model_config must not be empty"):
            start_retrain_workflow(
                workflow_name="test-workflow",
                model_config={},
            )


class TestSchedulePeriodicRetrain:
    """schedule_periodic_retrain ツールのテスト"""

    def test_schedule_basic_cron(self):
        """基本的なcronスケジュール設定テスト"""
        result = schedule_periodic_retrain(
            model_name="test-model",
            schedule_expression="cron(0 0 * * ? *)",
        )

        assert result["status"] == "success"
        assert "schedule_result" in result
        assert result["schedule_result"]["schedule_status"] == "ENABLED"
        assert result["schedule_result"]["mock"] is True

    def test_schedule_rate_expression(self):
        """rateスケジュール設定テスト"""
        result = schedule_periodic_retrain(
            model_name="test-model",
            schedule_expression="rate(7 days)",
        )

        assert result["status"] == "success"

    def test_schedule_with_config(self):
        """設定付きスケジュール設定テスト"""
        config = {
            "workflow_name": "custom-workflow",
            "notification_enabled": True,
        }
        result = schedule_periodic_retrain(
            model_name="test-model",
            schedule_expression="cron(0 0 * * ? *)",
            config=config,
        )

        assert result["status"] == "success"

    def test_schedule_has_rule_arn(self):
        """ルールARN生成テスト"""
        result = schedule_periodic_retrain(
            model_name="test-model",
            schedule_expression="cron(0 0 * * ? *)",
        )

        assert "rule_arn" in result["schedule_result"]

    def test_schedule_next_run_estimation(self):
        """次回実行時間推定テスト"""
        result = schedule_periodic_retrain(
            model_name="test-model",
            schedule_expression="rate(1 day)",
        )

        assert "next_scheduled_run" in result["schedule_result"]

    def test_schedule_empty_model_name_error(self):
        """空モデル名でエラーテスト"""
        with pytest.raises(ValueError, match="model_name must not be empty"):
            schedule_periodic_retrain(
                model_name="",
                schedule_expression="cron(0 0 * * ? *)",
            )

    def test_schedule_empty_expression_error(self):
        """空スケジュール式でエラーテスト"""
        with pytest.raises(ValueError, match="schedule_expression must not be empty"):
            schedule_periodic_retrain(
                model_name="test-model",
                schedule_expression="",
            )

    def test_schedule_invalid_expression_error(self):
        """無効なスケジュール式でエラーテスト"""
        with pytest.raises(ValueError, match="Invalid schedule expression"):
            schedule_periodic_retrain(
                model_name="test-model",
                schedule_expression="invalid-expression",
            )


class TestIntegration:
    """統合テスト"""

    def test_trigger_check_to_issue_creation(self):
        """トリガーチェック→Issue作成のワークフローテスト"""
        # 1. トリガーチェック
        trigger_result = check_retrain_triggers(model_name="integration-model")
        assert trigger_result["status"] == "success"

        # 2. Issue作成
        issue_result = create_retrain_issue(
            model_name="integration-model",
            reason="drift_detection",
            trigger_details=trigger_result["trigger_result"],
        )
        assert issue_result["status"] == "success"

    def test_condition_evaluation_to_workflow_start(self):
        """条件評価→ワークフロー起動のワークフローテスト"""
        # 1. 条件評価
        conditions = [{"type": "drift_threshold", "threshold": 0.1, "comparison": "gt"}]
        metrics = {"drift_score": 0.15}
        eval_result = evaluate_trigger_conditions(conditions, metrics)
        assert eval_result["status"] == "success"
        assert eval_result["evaluation_result"]["any_triggered"] is True

        # 2. ワークフロー起動
        workflow_result = start_retrain_workflow(
            workflow_name="mlops-retraining-workflow",
            model_config={"model_name": "integration-model"},
        )
        assert workflow_result["status"] == "success"

    def test_full_retrain_workflow(self):
        """完全な再学習ワークフローテスト"""
        model_name = "full-workflow-model"

        # 1. トリガーチェック
        trigger_result = check_retrain_triggers(model_name=model_name)
        assert trigger_result["status"] == "success"

        # 2. 条件評価
        conditions = [{"type": "drift_threshold", "threshold": 0.1, "comparison": "gt"}]
        metrics = {"drift_score": 0.15}
        eval_result = evaluate_trigger_conditions(conditions, metrics)
        assert eval_result["status"] == "success"

        # 3. Issue作成
        issue_result = create_retrain_issue(
            model_name=model_name,
            reason="drift_detection",
        )
        assert issue_result["status"] == "success"

        # 4. ワークフロー起動
        workflow_result = start_retrain_workflow(
            workflow_name="mlops-retraining-workflow",
            model_config={"model_name": model_name},
        )
        assert workflow_result["status"] == "success"

    def test_schedule_and_trigger_check(self):
        """スケジュール設定→トリガーチェックのワークフローテスト"""
        model_name = "schedule-workflow-model"

        # 1. スケジュール設定
        schedule_result = schedule_periodic_retrain(
            model_name=model_name,
            schedule_expression="rate(7 days)",
        )
        assert schedule_result["status"] == "success"

        # 2. トリガーチェック（スケジュール設定後）
        trigger_result = check_retrain_triggers(model_name=model_name)
        assert trigger_result["status"] == "success"
