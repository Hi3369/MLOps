"""
Experiment Tracking Unit Tests

実験追跡管理Capabilityのユニットテスト
TDD: Red → Green → Refactor
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from mcp_server.capabilities.experiment_tracking.capability import (
    ExperimentTrackingCapability,
)
from mcp_server.capabilities.experiment_tracking.tools import (
    compare_experiments,
    log_metrics,
    log_parameters,
    start_experiment,
)
from mcp_server.server import MLOpsServer


# =============================================================================
# Capability クラステスト
# =============================================================================
class TestExperimentTrackingCapability:
    """ExperimentTrackingCapabilityクラスのテスト"""

    def test_initialization(self):
        """Capability初期化テスト"""
        capability = ExperimentTrackingCapability()
        assert capability is not None
        assert capability._tools is not None
        assert len(capability._tools) == 4

    def test_get_tools(self):
        """ツール取得テスト"""
        capability = ExperimentTrackingCapability()
        tools = capability.get_tools()
        assert "start_experiment" in tools
        assert "log_parameters" in tools
        assert "log_metrics" in tools
        assert "compare_experiments" in tools

    def test_get_tool_schemas(self):
        """ツールスキーマ取得テスト"""
        capability = ExperimentTrackingCapability()
        schemas = capability.get_tool_schemas()
        assert len(schemas) == 4
        for name, schema in schemas.items():
            assert "name" in schema
            assert "description" in schema
            assert "parameters" in schema
            assert schema["parameters"]["type"] == "object"

    def test_server_registration(self):
        """サーバー登録テスト"""
        server = MLOpsServer()
        assert "experiment_tracking" in server.capabilities
        assert "experiment_tracking.start_experiment" in server.tools
        assert "experiment_tracking.log_parameters" in server.tools
        assert "experiment_tracking.log_metrics" in server.tools
        assert "experiment_tracking.compare_experiments" in server.tools


# =============================================================================
# start_experiment テスト
# =============================================================================
class TestStartExperiment:
    """start_experimentツールのテスト"""

    def test_start_experiment_basic(self):
        """基本的な実験開始テスト"""
        result = start_experiment(experiment_name="test-experiment")
        assert result["status"] == "success"
        assert "experiment_info" in result
        info = result["experiment_info"]
        assert info["experiment_name"] == "test-experiment"
        assert info["status"] == "running"
        assert info["experiment_id"].startswith("exp-")
        assert info["mock"] is True

    def test_start_experiment_with_description(self):
        """説明付き実験開始テスト"""
        result = start_experiment(
            experiment_name="described-experiment",
            description="Testing model performance with new features",
        )
        assert result["status"] == "success"
        assert result["experiment_info"]["description"] == (
            "Testing model performance with new features"
        )

    def test_start_experiment_with_tags(self):
        """タグ付き実験開始テスト"""
        result = start_experiment(
            experiment_name="tagged-experiment",
            tags=["classification", "v2", "production"],
        )
        assert result["status"] == "success"
        assert result["experiment_info"]["tags"] == [
            "classification",
            "v2",
            "production",
        ]

    def test_start_experiment_with_metadata(self):
        """メタデータ付き実験開始テスト"""
        metadata = {
            "algorithm": "random_forest",
            "dataset": "iris",
            "version": "1.0.0",
        }
        result = start_experiment(
            experiment_name="metadata-experiment",
            metadata=metadata,
        )
        assert result["status"] == "success"
        assert result["experiment_info"]["metadata"] == metadata

    def test_start_experiment_with_s3_bucket(self):
        """S3バケット指定の実験開始テスト"""
        result = start_experiment(
            experiment_name="s3-experiment",
            s3_bucket="my-experiment-bucket",
        )
        assert result["status"] == "success"
        assert result["experiment_info"]["s3_bucket"] == "my-experiment-bucket"

    def test_start_experiment_full_params(self):
        """全パラメータ指定の実験開始テスト"""
        result = start_experiment(
            experiment_name="full-experiment",
            description="Complete experiment test",
            tags=["test", "full"],
            metadata={"key": "value"},
            s3_bucket="custom-bucket",
        )
        assert result["status"] == "success"
        info = result["experiment_info"]
        assert info["experiment_name"] == "full-experiment"
        assert info["description"] == "Complete experiment test"
        assert info["tags"] == ["test", "full"]
        assert info["metadata"] == {"key": "value"}
        assert info["s3_bucket"] == "custom-bucket"

    def test_start_experiment_empty_name_error(self):
        """空の実験名エラーテスト"""
        with pytest.raises(ValueError, match="experiment_name must not be empty"):
            start_experiment(experiment_name="")

    def test_start_experiment_invalid_name_chars(self):
        """不正な文字を含む実験名エラーテスト"""
        with pytest.raises(ValueError, match="must contain only alphanumeric"):
            start_experiment(experiment_name="invalid name with spaces")

    def test_start_experiment_name_too_long(self):
        """長すぎる実験名エラーテスト"""
        with pytest.raises(ValueError, match="256 characters or less"):
            start_experiment(experiment_name="a" * 257)

    def test_start_experiment_valid_name_formats(self):
        """有効な実験名フォーマットテスト"""
        valid_names = [
            "simple",
            "with-hyphens",
            "with_underscores",
            "with.dots",
            "Mix-123_test.v2",
        ]
        for name in valid_names:
            result = start_experiment(experiment_name=name)
            assert result["status"] == "success"

    def test_start_experiment_s3_prefix_format(self):
        """S3プレフィックスのフォーマット確認テスト"""
        result = start_experiment(experiment_name="prefix-test")
        info = result["experiment_info"]
        assert info["s3_prefix"].startswith("experiments/prefix-test/")

    def test_start_experiment_timestamp_present(self):
        """タイムスタンプの存在確認テスト"""
        result = start_experiment(experiment_name="timestamp-test")
        info = result["experiment_info"]
        assert "created_at" in info
        assert "updated_at" in info

    def test_start_experiment_via_server(self):
        """サーバー経由の実験開始テスト"""
        server = MLOpsServer()
        result = server.call_tool(
            "experiment_tracking.start_experiment",
            {"experiment_name": "server-test-experiment"},
        )
        assert result["success"] is True
        assert result["result"]["status"] == "success"


# =============================================================================
# log_parameters テスト
# =============================================================================
class TestLogParameters:
    """log_parametersツールのテスト"""

    def test_log_parameters_basic(self):
        """基本的なパラメータ記録テスト"""
        result = log_parameters(
            experiment_id="exp-12345678",
            parameters={"learning_rate": 0.001, "batch_size": 32},
        )
        assert result["status"] == "success"
        assert "parameter_info" in result
        info = result["parameter_info"]
        assert info["experiment_id"] == "exp-12345678"
        assert info["parameters"]["learning_rate"] == 0.001
        assert info["parameter_count"] == 2

    def test_log_parameters_with_run_name(self):
        """実行名指定のパラメータ記録テスト"""
        result = log_parameters(
            experiment_id="exp-test",
            parameters={"epochs": 100},
            run_name="training-run-01",
        )
        assert result["status"] == "success"
        assert result["parameter_info"]["run_name"] == "training-run-01"

    def test_log_parameters_with_step(self):
        """ステップ指定のパラメータ記録テスト"""
        result = log_parameters(
            experiment_id="exp-test",
            parameters={"lr": 0.01},
            step=5,
        )
        assert result["status"] == "success"
        assert result["parameter_info"]["step"] == 5

    def test_log_parameters_various_types(self):
        """様々な型のパラメータ記録テスト"""
        params = {
            "string_param": "value",
            "int_param": 42,
            "float_param": 3.14,
            "bool_param": True,
            "list_param": [1, 2, 3],
        }
        result = log_parameters(
            experiment_id="exp-types",
            parameters=params,
        )
        assert result["status"] == "success"
        assert result["parameter_info"]["parameter_count"] == 5

    def test_log_parameters_empty_id_error(self):
        """空の実験IDエラーテスト"""
        with pytest.raises(ValueError, match="experiment_id must not be empty"):
            log_parameters(experiment_id="", parameters={"key": "value"})

    def test_log_parameters_empty_params_error(self):
        """空のパラメータエラーテスト"""
        with pytest.raises(ValueError, match="parameters must not be empty"):
            log_parameters(experiment_id="exp-test", parameters={})

    def test_log_parameters_invalid_params_type(self):
        """不正なパラメータ型エラーテスト"""
        with pytest.raises(ValueError, match="parameters must be a dictionary"):
            log_parameters(experiment_id="exp-test", parameters="not a dict")

    def test_log_parameters_invalid_value_type(self):
        """不正なパラメータ値型エラーテスト"""
        with pytest.raises(ValueError, match="must be str, int, float"):
            log_parameters(
                experiment_id="exp-test",
                parameters={"key": {"nested": "dict"}},
            )

    def test_log_parameters_negative_step_error(self):
        """負のステップエラーテスト"""
        with pytest.raises(ValueError, match="step must be a non-negative"):
            log_parameters(
                experiment_id="exp-test",
                parameters={"key": "value"},
                step=-1,
            )

    def test_log_parameters_auto_run_name(self):
        """自動実行名生成テスト"""
        result = log_parameters(
            experiment_id="exp-auto",
            parameters={"key": "value"},
        )
        assert result["status"] == "success"
        assert result["parameter_info"]["run_name"].startswith("run-")

    def test_log_parameters_via_server(self):
        """サーバー経由のパラメータ記録テスト"""
        server = MLOpsServer()
        result = server.call_tool(
            "experiment_tracking.log_parameters",
            {
                "experiment_id": "exp-server",
                "parameters": {"n_estimators": 100, "max_depth": 10},
            },
        )
        assert result["success"] is True
        assert result["result"]["status"] == "success"


# =============================================================================
# log_metrics テスト
# =============================================================================
class TestLogMetrics:
    """log_metricsツールのテスト"""

    def test_log_metrics_basic(self):
        """基本的なメトリクス記録テスト"""
        result = log_metrics(
            experiment_id="exp-metrics",
            metrics={"accuracy": 0.95, "loss": 0.05},
        )
        assert result["status"] == "success"
        assert "metrics_info" in result
        info = result["metrics_info"]
        assert info["experiment_id"] == "exp-metrics"
        assert info["metrics"]["accuracy"] == 0.95
        assert info["metrics"]["loss"] == 0.05

    def test_log_metrics_with_step_and_epoch(self):
        """ステップ・エポック指定のメトリクス記録テスト"""
        result = log_metrics(
            experiment_id="exp-step",
            metrics={"accuracy": 0.92},
            step=100,
            epoch=5,
        )
        assert result["status"] == "success"
        assert result["metrics_info"]["step"] == 100
        assert result["metrics_info"]["epoch"] == 5

    def test_log_metrics_with_run_name(self):
        """実行名指定のメトリクス記録テスト"""
        result = log_metrics(
            experiment_id="exp-run",
            metrics={"f1_score": 0.88},
            run_name="eval-run-01",
        )
        assert result["status"] == "success"
        assert result["metrics_info"]["run_name"] == "eval-run-01"

    def test_log_metrics_summary(self):
        """メトリクスサマリーテスト"""
        result = log_metrics(
            experiment_id="exp-summary",
            metrics={
                "accuracy": 0.95,
                "precision": 0.93,
                "recall": 0.91,
                "f1_score": 0.92,
            },
        )
        assert result["status"] == "success"
        summary = result["metrics_info"]["summary"]
        assert summary["metric_count"] == 4
        assert summary["min_value"] == 0.91
        assert summary["max_value"] == 0.95
        assert len(summary["metric_names"]) == 4

    def test_log_metrics_integer_values(self):
        """整数メトリクステスト"""
        result = log_metrics(
            experiment_id="exp-int",
            metrics={"total_samples": 1000, "correct_predictions": 950},
        )
        assert result["status"] == "success"
        assert result["metrics_info"]["metrics"]["total_samples"] == 1000

    def test_log_metrics_empty_id_error(self):
        """空の実験IDエラーテスト"""
        with pytest.raises(ValueError, match="experiment_id must not be empty"):
            log_metrics(experiment_id="", metrics={"accuracy": 0.9})

    def test_log_metrics_empty_metrics_error(self):
        """空のメトリクスエラーテスト"""
        with pytest.raises(ValueError, match="metrics must not be empty"):
            log_metrics(experiment_id="exp-test", metrics={})

    def test_log_metrics_invalid_metrics_type(self):
        """不正なメトリクス型エラーテスト"""
        with pytest.raises(ValueError, match="metrics must be a dictionary"):
            log_metrics(experiment_id="exp-test", metrics="not a dict")

    def test_log_metrics_non_numeric_value(self):
        """非数値メトリクスエラーテスト"""
        with pytest.raises(ValueError, match="must be numeric"):
            log_metrics(
                experiment_id="exp-test",
                metrics={"accuracy": "high"},
            )

    def test_log_metrics_negative_step_error(self):
        """負のステップエラーテスト"""
        with pytest.raises(ValueError, match="step must be a non-negative"):
            log_metrics(
                experiment_id="exp-test",
                metrics={"accuracy": 0.9},
                step=-1,
            )

    def test_log_metrics_negative_epoch_error(self):
        """負のエポックエラーテスト"""
        with pytest.raises(ValueError, match="epoch must be a non-negative"):
            log_metrics(
                experiment_id="exp-test",
                metrics={"accuracy": 0.9},
                epoch=-1,
            )

    def test_log_metrics_via_server(self):
        """サーバー経由のメトリクス記録テスト"""
        server = MLOpsServer()
        result = server.call_tool(
            "experiment_tracking.log_metrics",
            {
                "experiment_id": "exp-server-metrics",
                "metrics": {"accuracy": 0.95, "loss": 0.05},
            },
        )
        assert result["success"] is True
        assert result["result"]["status"] == "success"


# =============================================================================
# compare_experiments テスト
# =============================================================================
class TestCompareExperiments:
    """compare_experimentsツールのテスト"""

    def test_compare_two_experiments(self):
        """2つの実験比較テスト"""
        result = compare_experiments(
            experiment_ids=["exp-001", "exp-002"],
        )
        assert result["status"] == "success"
        assert "comparison_info" in result
        info = result["comparison_info"]
        assert len(info["experiments"]) == 2
        assert info["comparison_id"].startswith("cmp-")

    def test_compare_multiple_experiments(self):
        """複数実験比較テスト"""
        result = compare_experiments(
            experiment_ids=["exp-a", "exp-b", "exp-c", "exp-d"],
        )
        assert result["status"] == "success"
        assert len(result["comparison_info"]["experiments"]) == 4

    def test_compare_with_metric_names(self):
        """メトリクス名指定の比較テスト"""
        result = compare_experiments(
            experiment_ids=["exp-001", "exp-002"],
            metric_names=["accuracy", "f1_score"],
        )
        assert result["status"] == "success"
        for exp in result["comparison_info"]["experiments"]:
            metric_keys = set(exp["metrics"].keys())
            assert metric_keys.issubset({"accuracy", "f1_score"})

    def test_compare_with_sort_ascending(self):
        """昇順ソートの比較テスト"""
        result = compare_experiments(
            experiment_ids=["exp-001", "exp-002"],
            sort_by="loss",
            sort_order="ascending",
        )
        assert result["status"] == "success"
        assert result["comparison_info"]["sort_by"] == "loss"
        assert result["comparison_info"]["sort_order"] == "ascending"

    def test_compare_with_sort_descending(self):
        """降順ソートの比較テスト"""
        result = compare_experiments(
            experiment_ids=["exp-001", "exp-002"],
            sort_by="accuracy",
            sort_order="descending",
        )
        assert result["status"] == "success"
        assert result["comparison_info"]["sort_order"] == "descending"

    def test_compare_summary_best_by_metric(self):
        """サマリーのベストメトリクステスト"""
        result = compare_experiments(
            experiment_ids=["exp-001", "exp-002", "exp-003"],
        )
        assert result["status"] == "success"
        summary = result["comparison_info"]["summary"]
        assert "best_by_metric" in summary
        assert summary["total_experiments"] == 3

    def test_compare_summary_ranking(self):
        """サマリーのランキングテスト"""
        result = compare_experiments(
            experiment_ids=["exp-a", "exp-b"],
            sort_by="accuracy",
        )
        assert result["status"] == "success"
        ranking = result["comparison_info"]["summary"]["ranking"]
        assert len(ranking) == 2
        assert ranking[0]["rank"] == 1
        assert ranking[1]["rank"] == 2

    def test_compare_empty_ids_error(self):
        """空の実験IDリストエラーテスト"""
        with pytest.raises(ValueError, match="experiment_ids must not be empty"):
            compare_experiments(experiment_ids=[])

    def test_compare_single_id_error(self):
        """1つだけの実験IDエラーテスト"""
        with pytest.raises(ValueError, match="At least 2 experiment_ids"):
            compare_experiments(experiment_ids=["exp-only-one"])

    def test_compare_too_many_ids_error(self):
        """多すぎる実験IDエラーテスト"""
        ids = [f"exp-{i:03d}" for i in range(11)]
        with pytest.raises(ValueError, match="Maximum 10 experiments"):
            compare_experiments(experiment_ids=ids)

    def test_compare_invalid_sort_order_error(self):
        """不正なソート順エラーテスト"""
        with pytest.raises(ValueError, match="sort_order must be"):
            compare_experiments(
                experiment_ids=["exp-001", "exp-002"],
                sort_order="invalid",
            )

    def test_compare_duplicate_ids_error(self):
        """重複実験IDエラーテスト"""
        with pytest.raises(ValueError, match="must not contain duplicates"):
            compare_experiments(experiment_ids=["exp-001", "exp-001"])

    def test_compare_invalid_ids_type_error(self):
        """不正な実験IDリスト型エラーテスト"""
        with pytest.raises(ValueError, match="experiment_ids must be a list"):
            compare_experiments(experiment_ids="not-a-list")

    def test_compare_experiments_deterministic(self):
        """決定的なモックデータ生成テスト"""
        result1 = compare_experiments(
            experiment_ids=["exp-deterministic-a", "exp-deterministic-b"],
        )
        result2 = compare_experiments(
            experiment_ids=["exp-deterministic-a", "exp-deterministic-b"],
        )
        # 同じ実験IDなら同じメトリクス値
        for i in range(2):
            assert (
                result1["comparison_info"]["experiments"][i]["metrics"]
                == result2["comparison_info"]["experiments"][i]["metrics"]
            )

    def test_compare_via_server(self):
        """サーバー経由の実験比較テスト"""
        server = MLOpsServer()
        result = server.call_tool(
            "experiment_tracking.compare_experiments",
            {"experiment_ids": ["exp-server-a", "exp-server-b"]},
        )
        assert result["success"] is True
        assert result["result"]["status"] == "success"


# =============================================================================
# 統合テスト
# =============================================================================
class TestExperimentTrackingIntegration:
    """実験追跡の統合テスト"""

    @pytest.fixture
    def server(self) -> MLOpsServer:
        """テスト用サーバーインスタンス"""
        return MLOpsServer()

    def test_full_experiment_workflow(self, server: MLOpsServer):
        """実験の完全ワークフローテスト（開始→パラメータ→メトリクス）"""
        # Step 1: 実験開始
        start_result = server.call_tool(
            "experiment_tracking.start_experiment",
            {
                "experiment_name": "workflow-test",
                "description": "Full workflow integration test",
                "tags": ["integration", "test"],
            },
        )
        assert start_result["success"] is True
        exp_id = start_result["result"]["experiment_info"]["experiment_id"]

        # Step 2: パラメータ記録
        param_result = server.call_tool(
            "experiment_tracking.log_parameters",
            {
                "experiment_id": exp_id,
                "parameters": {
                    "algorithm": "random_forest",
                    "n_estimators": 100,
                    "max_depth": 10,
                },
                "run_name": "training-run",
            },
        )
        assert param_result["success"] is True

        # Step 3: メトリクス記録（エポック1）
        metrics_result_1 = server.call_tool(
            "experiment_tracking.log_metrics",
            {
                "experiment_id": exp_id,
                "metrics": {"accuracy": 0.85, "loss": 0.35},
                "run_name": "training-run",
                "epoch": 1,
            },
        )
        assert metrics_result_1["success"] is True

        # Step 4: メトリクス記録（エポック2）
        metrics_result_2 = server.call_tool(
            "experiment_tracking.log_metrics",
            {
                "experiment_id": exp_id,
                "metrics": {"accuracy": 0.92, "loss": 0.15},
                "run_name": "training-run",
                "epoch": 2,
            },
        )
        assert metrics_result_2["success"] is True

    def test_multiple_experiments_comparison_workflow(self, server: MLOpsServer):
        """複数実験の比較ワークフローテスト"""
        experiment_ids = []

        # 3つの実験を開始
        for i in range(3):
            result = server.call_tool(
                "experiment_tracking.start_experiment",
                {
                    "experiment_name": f"comparison-test-{i}",
                    "tags": ["comparison"],
                },
            )
            assert result["success"] is True
            experiment_ids.append(result["result"]["experiment_info"]["experiment_id"])

        # 各実験にメトリクスを記録
        for exp_id in experiment_ids:
            result = server.call_tool(
                "experiment_tracking.log_metrics",
                {
                    "experiment_id": exp_id,
                    "metrics": {"accuracy": 0.9, "f1_score": 0.88},
                },
            )
            assert result["success"] is True

        # 実験比較
        compare_result = server.call_tool(
            "experiment_tracking.compare_experiments",
            {
                "experiment_ids": experiment_ids,
                "sort_by": "accuracy",
                "sort_order": "descending",
            },
        )
        assert compare_result["success"] is True
        summary = compare_result["result"]["comparison_info"]["summary"]
        assert summary["total_experiments"] == 3

    def test_hyperparameter_search_tracking(self, server: MLOpsServer):
        """ハイパーパラメータ探索の追跡テスト"""
        # 実験開始
        start_result = server.call_tool(
            "experiment_tracking.start_experiment",
            {
                "experiment_name": "hp-search",
                "metadata": {"search_method": "grid_search"},
            },
        )
        assert start_result["success"] is True
        exp_id = start_result["result"]["experiment_info"]["experiment_id"]

        # Grid Search: 複数パラメータ組み合わせ
        param_sets = [
            {"n_estimators": 50, "max_depth": 5},
            {"n_estimators": 100, "max_depth": 10},
            {"n_estimators": 200, "max_depth": 15},
        ]

        for i, params in enumerate(param_sets):
            # パラメータ記録
            param_result = server.call_tool(
                "experiment_tracking.log_parameters",
                {
                    "experiment_id": exp_id,
                    "parameters": params,
                    "run_name": f"hp-trial-{i}",
                    "step": i,
                },
            )
            assert param_result["success"] is True

            # メトリクス記録
            metric_result = server.call_tool(
                "experiment_tracking.log_metrics",
                {
                    "experiment_id": exp_id,
                    "metrics": {"accuracy": 0.85 + i * 0.03},
                    "run_name": f"hp-trial-{i}",
                    "step": i,
                },
            )
            assert metric_result["success"] is True
