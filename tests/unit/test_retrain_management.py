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


class TestCheckRetrainTriggersExtended:
    """check_retrain_triggers の拡張テスト（カバレッジ向上）"""

    def test_trigger_details_data_change(self):
        """data_changeトリガーの詳細確認テスト"""
        result = check_retrain_triggers(model_name="detail-model")
        trigger = result["trigger_result"]["triggers"]["data_change"]
        assert trigger["enabled"] is True
        assert "details" in trigger
        assert "last_data_update" in trigger["details"]

    def test_trigger_details_metrics_degradation(self):
        """metrics_degradationトリガーの閾値確認テスト"""
        config = {"metrics_degradation": {"enabled": True, "threshold": 0.8}}
        result = check_retrain_triggers(model_name="threshold-model", trigger_config=config)
        trigger = result["trigger_result"]["triggers"]["metrics_degradation"]
        assert trigger["details"]["threshold"] == 0.8

    def test_trigger_details_drift_detection(self):
        """drift_detectionトリガーの閾値確認テスト"""
        config = {"drift_detection": {"enabled": True, "threshold": 0.05}}
        result = check_retrain_triggers(model_name="drift-model", trigger_config=config)
        trigger = result["trigger_result"]["triggers"]["drift_detection"]
        assert trigger["details"]["threshold"] == 0.05
        assert trigger["details"]["drift_score"] == 0.05

    def test_trigger_disabled_trigger(self):
        """無効化されたトリガーのテスト"""
        config = {"data_change": {"enabled": False}}
        result = check_retrain_triggers(model_name="disabled-model", trigger_config=config)
        trigger = result["trigger_result"]["triggers"]["data_change"]
        assert trigger["enabled"] is False

    def test_trigger_check_id_generated(self):
        """check_idが生成されるテスト"""
        result = check_retrain_triggers(model_name="id-model")
        assert "check_id" in result["trigger_result"]
        assert len(result["trigger_result"]["check_id"]) == 8

    def test_trigger_timestamp_present(self):
        """タイムスタンプが含まれるテスト"""
        result = check_retrain_triggers(model_name="ts-model")
        assert "timestamp" in result["trigger_result"]
        assert "T" in result["trigger_result"]["timestamp"]

    def test_real_trigger_helper_functions(self):
        """ヘルパー関数の直接テスト"""
        from mcp_server.capabilities.retrain_management.tools.check_retrain_triggers import (
            _check_code_change_trigger,
            _check_data_change_trigger,
            _check_drift_detection_trigger,
            _check_metrics_degradation_trigger,
            _check_schedule_trigger,
        )

        # data_change
        result = _check_data_change_trigger("model", {})
        assert result["enabled"] is True
        assert result["triggered"] is False

        # code_change
        result = _check_code_change_trigger("model", {})
        assert result["enabled"] is True
        assert "message" in result["details"]

        # schedule
        result = _check_schedule_trigger("model", {})
        assert result["enabled"] is True

        # metrics_degradation
        result = _check_metrics_degradation_trigger("model", {"threshold": 0.85})
        assert result["details"]["threshold"] == 0.85

        # drift_detection
        result = _check_drift_detection_trigger("model", {"threshold": 0.15})
        assert result["details"]["threshold"] == 0.15
        assert result["details"]["drift_score"] == 0.05


class TestSchedulePeriodicRetrainExtended:
    """schedule_periodic_retrain の拡張テスト（カバレッジ向上）"""

    def test_validate_schedule_expression_cron_variants(self):
        """様々なcron式のバリデーションテスト"""
        from mcp_server.capabilities.retrain_management.tools.schedule_periodic_retrain import (
            _validate_schedule_expression,
        )

        assert _validate_schedule_expression("cron(0 0 * * ? *)") is True
        assert _validate_schedule_expression("cron(30 8 ? * MON-FRI *)") is True
        assert _validate_schedule_expression("invalid") is False
        assert _validate_schedule_expression("") is False

    def test_validate_schedule_expression_rate_variants(self):
        """様々なrate式のバリデーションテスト"""
        from mcp_server.capabilities.retrain_management.tools.schedule_periodic_retrain import (
            _validate_schedule_expression,
        )

        assert _validate_schedule_expression("rate(1 day)") is True
        assert _validate_schedule_expression("rate(7 days)") is True
        assert _validate_schedule_expression("rate(1 hour)") is True
        assert _validate_schedule_expression("rate(24 hours)") is True
        assert _validate_schedule_expression("rate(30 minutes)") is True
        assert _validate_schedule_expression("rate(1 minute)") is True

    def test_estimate_next_run_rate_days(self):
        """rate式（日）の次回実行推定テスト"""
        from mcp_server.capabilities.retrain_management.tools.schedule_periodic_retrain import (
            _estimate_next_run,
        )

        next_run = _estimate_next_run("rate(7 days)", "2025-01-01T00:00:00+00:00")
        assert next_run != "unknown"
        assert "2025-01-08" in next_run

    def test_estimate_next_run_rate_hours(self):
        """rate式（時間）の次回実行推定テスト"""
        from mcp_server.capabilities.retrain_management.tools.schedule_periodic_retrain import (
            _estimate_next_run,
        )

        next_run = _estimate_next_run("rate(1 hour)", "2025-01-01T00:00:00+00:00")
        assert next_run != "unknown"
        assert "01:00" in next_run

    def test_estimate_next_run_rate_minutes(self):
        """rate式（分）の次回実行推定テスト"""
        from mcp_server.capabilities.retrain_management.tools.schedule_periodic_retrain import (
            _estimate_next_run,
        )

        next_run = _estimate_next_run("rate(30 minutes)", "2025-01-01T00:00:00+00:00")
        assert next_run != "unknown"
        assert "00:30" in next_run

    def test_estimate_next_run_cron(self):
        """cron式の次回実行推定テスト（翌日0時概算）"""
        from mcp_server.capabilities.retrain_management.tools.schedule_periodic_retrain import (
            _estimate_next_run,
        )

        next_run = _estimate_next_run("cron(0 0 * * ? *)", "2025-01-01T12:00:00+00:00")
        assert next_run != "unknown"
        assert "2025-01-02" in next_run

    def test_schedule_rule_name_format(self):
        """ルール名フォーマットテスト"""
        result = schedule_periodic_retrain(
            model_name="my-model",
            schedule_expression="rate(1 day)",
        )

        rule_name = result["schedule_result"]["rule_name"]
        assert rule_name.startswith("mlops-retrain-my-model-")

    def test_schedule_config_merged(self):
        """スケジュール設定のマージテスト"""
        config = {
            "workflow_name": "custom-wf",
            "dataset_uri": "s3://bucket/data",
            "notification_enabled": False,
        }
        result = schedule_periodic_retrain(
            model_name="config-model",
            schedule_expression="rate(1 day)",
            config=config,
        )

        sched_config = result["schedule_result"]["schedule_config"]
        assert sched_config["workflow_name"] == "custom-wf"
        assert sched_config["dataset_uri"] == "s3://bucket/data"
        assert sched_config["notification_enabled"] is False


class TestStartRetrainWorkflowExtended:
    """start_retrain_workflow の拡張テスト（カバレッジ向上）"""

    def test_version_increment_function(self):
        """_increment_version関数の直接テスト"""
        from mcp_server.capabilities.retrain_management.tools.start_retrain_workflow import (
            _increment_version,
        )

        assert _increment_version("v1.0.0") == "v1.1.0"
        assert _increment_version("v2.3.5") == "v2.4.0"
        assert _increment_version("1.0.0") == "1.1.0"
        assert _increment_version("v0.0.1") == "v0.1.0"
        assert _increment_version("invalid") == "invalid-new"

    def test_workflow_default_version(self):
        """デフォルトバージョンテスト"""
        result = start_retrain_workflow(
            workflow_name="test-wf",
            model_config={"model_name": "no-version-model"},
        )

        assert result["workflow_result"]["next_version"] == "v1.1.0"

    def test_workflow_execution_id_is_uuid(self):
        """実行IDがUUID形式であるテスト"""
        result = start_retrain_workflow(
            workflow_name="test-wf",
            model_config={"model_name": "uuid-model"},
        )

        execution_id = result["workflow_result"]["execution_id"]
        assert len(execution_id) == 36  # UUID4 format: 8-4-4-4-12

    def test_workflow_execution_arn_format(self):
        """実行ARNフォーマットテスト"""
        result = start_retrain_workflow(
            workflow_name="test-wf",
            model_config={"model_name": "arn-model"},
        )

        arn = result["workflow_result"]["execution_arn"]
        assert "arn:aws:states:" in arn
        assert "test-wf" in arn

    def test_workflow_input_contains_versioning(self):
        """ワークフロー入力にバージョニング情報が含まれるテスト"""
        result = start_retrain_workflow(
            workflow_name="test-wf",
            model_config={"model_name": "versioned-model", "current_version": "v2.0.0"},
        )

        input_params = result["workflow_result"]["input_params"]
        assert "versioning" in input_params
        assert input_params["versioning"]["current_version"] == "v2.0.0"
        assert input_params["versioning"]["next_version"] == "v2.1.0"

    def test_workflow_comparison_config_defaults(self):
        """比較設定のデフォルト値テスト"""
        result = start_retrain_workflow(
            workflow_name="test-wf",
            model_config={"model_name": "compare-model"},
            comparison_config={"metrics_to_compare": ["f1"]},
        )

        comp = result["workflow_result"]["input_params"]["comparison_config"]
        assert comp["metrics_to_compare"] == ["f1"]
        assert comp["improvement_threshold"] == 0.01
        assert comp["auto_deploy_on_improvement"] is False

    def test_workflow_model_name_fallback(self):
        """model_nameがない場合のフォールバックテスト"""
        result = start_retrain_workflow(
            workflow_name="test-wf",
            model_config={"model_type": "xgboost"},
        )

        assert result["workflow_result"]["model_name"] == "unknown-model"


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
