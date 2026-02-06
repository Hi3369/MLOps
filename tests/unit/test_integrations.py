"""
外部ツール統合テスト

MLflow, W&B, DVC アダプタのユニットテスト
"""

import os
from unittest.mock import patch

import pytest

# ===== MLflowAdapter =====


class TestMLflowAdapter:
    """MLflowAdapter のテスト"""

    def test_init_default(self):
        from mcp_server.integrations.mlflow_adapter import MLflowAdapter

        adapter = MLflowAdapter()
        assert adapter.tracking_uri == "http://localhost:5000"
        assert adapter.experiment_name == "mlops-default"

    def test_init_custom(self):
        from mcp_server.integrations.mlflow_adapter import MLflowAdapter

        adapter = MLflowAdapter(
            tracking_uri="http://mlflow:5001",
            experiment_name="custom-exp",
        )
        assert adapter.tracking_uri == "http://mlflow:5001"
        assert adapter.experiment_name == "custom-exp"

    @patch.dict(
        os.environ,
        {"MLFLOW_TRACKING_URI": "http://env-uri:5000", "MLFLOW_EXPERIMENT_NAME": "env-exp"},
    )
    def test_init_from_env(self):
        from mcp_server.integrations.mlflow_adapter import MLflowAdapter

        adapter = MLflowAdapter()
        assert adapter.tracking_uri == "http://env-uri:5000"
        assert adapter.experiment_name == "env-exp"

    @patch.dict(os.environ, {"MLOPS_ENV": "test"})
    def test_sync_experiment_mock(self):
        from mcp_server.integrations.mlflow_adapter import MLflowAdapter

        adapter = MLflowAdapter()
        result = adapter.sync_experiment(
            experiment_id="exp-001",
            parameters={"lr": 0.01, "epochs": 10},
            metrics={"accuracy": 0.95, "f1": 0.92},
            tags={"team": "ml"},
        )
        assert result["status"] == "success"
        assert result["mcp_experiment_id"] == "exp-001"
        assert result["parameters_synced"] == 2
        assert result["metrics_synced"] == 2
        assert result["mock"] is True

    def test_sync_experiment_empty_id_raises(self):
        from mcp_server.integrations.mlflow_adapter import MLflowAdapter

        adapter = MLflowAdapter()
        with pytest.raises(ValueError, match="experiment_id must not be empty"):
            adapter.sync_experiment(
                experiment_id="",
                parameters={},
                metrics={},
            )

    @patch.dict(os.environ, {"MLOPS_ENV": "test"})
    def test_sync_model_mock(self):
        from mcp_server.integrations.mlflow_adapter import MLflowAdapter

        adapter = MLflowAdapter()
        result = adapter.sync_model(
            model_name="classifier",
            model_version="1.0.0",
            model_uri="s3://bucket/models/classifier/1.0.0/",
            metrics={"accuracy": 0.95},
        )
        assert result["status"] == "success"
        assert result["model_name"] == "classifier"
        assert result["model_version"] == "1.0.0"
        assert result["mock"] is True

    def test_sync_model_empty_name_raises(self):
        from mcp_server.integrations.mlflow_adapter import MLflowAdapter

        adapter = MLflowAdapter()
        with pytest.raises(ValueError, match="model_name must not be empty"):
            adapter.sync_model(
                model_name="",
                model_version="1.0.0",
                model_uri="s3://bucket/models/",
            )

    def test_sync_model_empty_uri_raises(self):
        from mcp_server.integrations.mlflow_adapter import MLflowAdapter

        adapter = MLflowAdapter()
        with pytest.raises(ValueError, match="model_uri must not be empty"):
            adapter.sync_model(
                model_name="model",
                model_version="1.0.0",
                model_uri="",
            )

    def test_get_config(self):
        from mcp_server.integrations.mlflow_adapter import MLflowAdapter

        adapter = MLflowAdapter(
            tracking_uri="http://test:5000",
            experiment_name="test-exp",
        )
        config = adapter.get_config()
        assert config["tracking_uri"] == "http://test:5000"
        assert config["experiment_name"] == "test-exp"
        assert config["status"] == "configured"


# ===== WandbAdapter =====


class TestWandbAdapter:
    """WandbAdapter のテスト"""

    def test_init_default(self):
        from mcp_server.integrations.mlflow_adapter import WandbAdapter

        adapter = WandbAdapter()
        assert adapter.project == "mlops-pipeline"

    def test_init_custom(self):
        from mcp_server.integrations.mlflow_adapter import WandbAdapter

        adapter = WandbAdapter(project="custom-proj", entity="my-team")
        assert adapter.project == "custom-proj"
        assert adapter.entity == "my-team"

    @patch.dict(
        os.environ,
        {"WANDB_PROJECT": "env-proj", "WANDB_ENTITY": "env-entity"},
    )
    def test_init_from_env(self):
        from mcp_server.integrations.mlflow_adapter import WandbAdapter

        adapter = WandbAdapter()
        assert adapter.project == "env-proj"
        assert adapter.entity == "env-entity"

    @patch.dict(os.environ, {"MLOPS_ENV": "test"})
    def test_sync_experiment_mock(self):
        from mcp_server.integrations.mlflow_adapter import WandbAdapter

        adapter = WandbAdapter(project="test-proj", entity="test-team")
        result = adapter.sync_experiment(
            experiment_id="exp-002",
            parameters={"lr": 0.001},
            metrics={"loss": 0.05},
            tags=["baseline", "v2"],
        )
        assert result["status"] == "success"
        assert result["mcp_experiment_id"] == "exp-002"
        assert result["project"] == "test-proj"
        assert result["parameters_synced"] == 1
        assert result["metrics_synced"] == 1
        assert result["mock"] is True
        assert "wandb_run_url" in result

    def test_sync_experiment_empty_id_raises(self):
        from mcp_server.integrations.mlflow_adapter import WandbAdapter

        adapter = WandbAdapter()
        with pytest.raises(ValueError, match="experiment_id must not be empty"):
            adapter.sync_experiment(
                experiment_id="",
                parameters={},
                metrics={},
            )

    def test_get_config(self):
        from mcp_server.integrations.mlflow_adapter import WandbAdapter

        adapter = WandbAdapter(project="p", entity="e")
        config = adapter.get_config()
        assert config["project"] == "p"
        assert config["entity"] == "e"
        assert config["status"] == "configured"


# ===== DVCAdapter =====


class TestDVCAdapter:
    """DVCAdapter のテスト"""

    def test_init_default(self):
        from mcp_server.integrations.mlflow_adapter import DVCAdapter

        adapter = DVCAdapter()
        assert adapter.remote_name == "s3remote"

    def test_init_custom(self):
        from mcp_server.integrations.mlflow_adapter import DVCAdapter

        adapter = DVCAdapter(
            remote_name="myremote",
            remote_url="s3://my-bucket/dvc",
        )
        assert adapter.remote_name == "myremote"
        assert adapter.remote_url == "s3://my-bucket/dvc"

    @patch.dict(
        os.environ,
        {"DVC_REMOTE": "env-remote", "DVC_REMOTE_URL": "s3://env-bucket"},
    )
    def test_init_from_env(self):
        from mcp_server.integrations.mlflow_adapter import DVCAdapter

        adapter = DVCAdapter()
        assert adapter.remote_name == "env-remote"
        assert adapter.remote_url == "s3://env-bucket"

    @patch.dict(os.environ, {"MLOPS_ENV": "test"})
    def test_sync_dataset_version_mock(self):
        from mcp_server.integrations.mlflow_adapter import DVCAdapter

        adapter = DVCAdapter()
        result = adapter.sync_dataset_version(
            dataset_name="training-data",
            version="1.2.0",
            s3_uri="s3://bucket/datasets/training-data/1.2.0/",
            metadata={"records": 10000},
        )
        assert result["status"] == "success"
        assert result["dataset_name"] == "training-data"
        assert result["version"] == "1.2.0"
        assert result["mock"] is True

    def test_sync_dataset_empty_name_raises(self):
        from mcp_server.integrations.mlflow_adapter import DVCAdapter

        adapter = DVCAdapter()
        with pytest.raises(ValueError, match="dataset_name must not be empty"):
            adapter.sync_dataset_version(
                dataset_name="",
                version="1.0.0",
                s3_uri="s3://bucket/data",
            )

    def test_sync_dataset_empty_uri_raises(self):
        from mcp_server.integrations.mlflow_adapter import DVCAdapter

        adapter = DVCAdapter()
        with pytest.raises(ValueError, match="s3_uri must not be empty"):
            adapter.sync_dataset_version(
                dataset_name="data",
                version="1.0.0",
                s3_uri="",
            )

    def test_get_config(self):
        from mcp_server.integrations.mlflow_adapter import DVCAdapter

        adapter = DVCAdapter(remote_name="r", remote_url="s3://b")
        config = adapter.get_config()
        assert config["remote_name"] == "r"
        assert config["remote_url"] == "s3://b"
        assert config["status"] == "configured"


# ===== モック関数の直接テスト =====


class TestMockFunctions:
    """モック関数の直接テスト"""

    def test_mock_sync_experiment(self):
        from mcp_server.integrations.mlflow_adapter import _mock_sync_experiment

        result = _mock_sync_experiment(
            experiment_id="exp-1",
            parameters={"a": 1},
            metrics={"b": 0.5},
            tags={"c": "d"},
            sync_id="abcd1234",
            timestamp="2025-01-01T00:00:00Z",
        )
        assert result["sync_id"] == "abcd1234"
        assert result["mlflow_run_id"].startswith("mock-run-")

    def test_mock_sync_model(self):
        from mcp_server.integrations.mlflow_adapter import _mock_sync_model

        result = _mock_sync_model(
            model_name="model",
            model_version="1.0.0",
            model_uri="s3://test",
            metrics=None,
            sync_id="abcd1234",
            timestamp="2025-01-01T00:00:00Z",
        )
        assert result["mlflow_model_version"] == "1"

    def test_mock_wandb_sync(self):
        from mcp_server.integrations.mlflow_adapter import _mock_wandb_sync

        result = _mock_wandb_sync(
            experiment_id="exp-1",
            parameters={"a": 1},
            metrics={"b": 0.5},
            tags=["tag1"],
            sync_id="abcd1234",
            timestamp="2025-01-01T00:00:00Z",
            project="proj",
            entity="team",
        )
        assert "wandb.ai" in result["wandb_run_url"]

    def test_mock_dvc_sync(self):
        from mcp_server.integrations.mlflow_adapter import _mock_dvc_sync

        result = _mock_dvc_sync(
            dataset_name="data",
            version="1.0",
            s3_uri="s3://test",
            metadata=None,
            sync_id="abcd1234",
            timestamp="2025-01-01T00:00:00Z",
            remote_name="remote",
        )
        assert "Importing" in result["dvc_output"]


class TestMLflowAdapterExtended:
    """MLflowAdapter の拡張テスト（カバレッジ向上）"""

    @patch.dict(os.environ, {"MLOPS_ENV": "test"})
    def test_sync_experiment_with_tags(self):
        from mcp_server.integrations.mlflow_adapter import MLflowAdapter

        adapter = MLflowAdapter()
        result = adapter.sync_experiment(
            experiment_id="exp-tags",
            parameters={"lr": 0.01},
            metrics={"acc": 0.95},
            tags={"team": "ml", "version": "v2"},
        )
        assert result["status"] == "success"
        assert result["parameters_synced"] == 1
        assert result["metrics_synced"] == 1
        assert result["mock"] is True

    @patch.dict(os.environ, {"MLOPS_ENV": "test"})
    def test_sync_experiment_without_tags(self):
        from mcp_server.integrations.mlflow_adapter import MLflowAdapter

        adapter = MLflowAdapter()
        result = adapter.sync_experiment(
            experiment_id="exp-notags",
            parameters={},
            metrics={},
        )
        assert result["status"] == "success"
        assert result["parameters_synced"] == 0
        assert result["metrics_synced"] == 0

    @patch.dict(os.environ, {"MLOPS_ENV": "test"})
    def test_sync_model_with_metrics(self):
        from mcp_server.integrations.mlflow_adapter import MLflowAdapter

        adapter = MLflowAdapter()
        result = adapter.sync_model(
            model_name="model-with-metrics",
            model_version="2.0.0",
            model_uri="s3://bucket/models/v2/",
            metrics={"accuracy": 0.98, "f1": 0.96, "recall": 0.97},
        )
        assert result["status"] == "success"
        assert result["model_name"] == "model-with-metrics"
        assert result["model_version"] == "2.0.0"

    @patch.dict(os.environ, {"MLOPS_ENV": "test"})
    def test_sync_model_without_metrics(self):
        from mcp_server.integrations.mlflow_adapter import MLflowAdapter

        adapter = MLflowAdapter()
        result = adapter.sync_model(
            model_name="model-no-metrics",
            model_version="1.0.0",
            model_uri="s3://bucket/models/v1/",
        )
        assert result["status"] == "success"
        assert result["mock"] is True

    @patch.dict(os.environ, {"MLOPS_ENV": "test"})
    def test_sync_experiment_has_sync_id(self):
        from mcp_server.integrations.mlflow_adapter import MLflowAdapter

        adapter = MLflowAdapter()
        result = adapter.sync_experiment(
            experiment_id="exp-id",
            parameters={"lr": 0.01},
            metrics={"acc": 0.9},
        )
        assert "sync_id" in result
        assert len(result["sync_id"]) == 8

    @patch.dict(os.environ, {"MLOPS_ENV": "test"})
    def test_sync_model_has_mlflow_version(self):
        from mcp_server.integrations.mlflow_adapter import MLflowAdapter

        adapter = MLflowAdapter()
        result = adapter.sync_model(
            model_name="versioned",
            model_version="3.0.0",
            model_uri="s3://bucket/models/v3/",
        )
        assert result["mlflow_model_version"] == "1"


class TestWandbAdapterExtended:
    """WandbAdapter の拡張テスト（カバレッジ向上）"""

    @patch.dict(os.environ, {"MLOPS_ENV": "test"})
    def test_sync_experiment_with_tags_list(self):
        from mcp_server.integrations.mlflow_adapter import WandbAdapter

        adapter = WandbAdapter(project="test-proj")
        result = adapter.sync_experiment(
            experiment_id="exp-wandb",
            parameters={"batch_size": 32, "epochs": 100},
            metrics={"loss": 0.01, "val_loss": 0.02},
            tags=["production", "v3", "optimized"],
        )
        assert result["status"] == "success"
        assert result["parameters_synced"] == 2
        assert result["metrics_synced"] == 2
        assert result["project"] == "test-proj"

    @patch.dict(os.environ, {"MLOPS_ENV": "test"})
    def test_sync_experiment_without_tags(self):
        from mcp_server.integrations.mlflow_adapter import WandbAdapter

        adapter = WandbAdapter()
        result = adapter.sync_experiment(
            experiment_id="exp-notags",
            parameters={},
            metrics={},
        )
        assert result["status"] == "success"
        assert result["parameters_synced"] == 0

    @patch.dict(os.environ, {"MLOPS_ENV": "test"})
    def test_sync_experiment_wandb_run_url(self):
        from mcp_server.integrations.mlflow_adapter import WandbAdapter

        adapter = WandbAdapter(project="url-proj", entity="url-team")
        result = adapter.sync_experiment(
            experiment_id="exp-url",
            parameters={},
            metrics={},
        )
        assert "wandb.ai" in result["wandb_run_url"]
        assert "url-team" in result["wandb_run_url"]
        assert "url-proj" in result["wandb_run_url"]


class TestDVCAdapterExtended:
    """DVCAdapter の拡張テスト（カバレッジ向上）"""

    @patch.dict(os.environ, {"MLOPS_ENV": "test"})
    def test_sync_dataset_with_metadata(self):
        from mcp_server.integrations.mlflow_adapter import DVCAdapter

        adapter = DVCAdapter()
        result = adapter.sync_dataset_version(
            dataset_name="images",
            version="2.1.0",
            s3_uri="s3://bucket/datasets/images/v2/",
            metadata={"records": 50000, "format": "parquet", "size_gb": 2.5},
        )
        assert result["status"] == "success"
        assert result["dataset_name"] == "images"
        assert result["version"] == "2.1.0"

    @patch.dict(os.environ, {"MLOPS_ENV": "test"})
    def test_sync_dataset_without_metadata(self):
        from mcp_server.integrations.mlflow_adapter import DVCAdapter

        adapter = DVCAdapter()
        result = adapter.sync_dataset_version(
            dataset_name="text",
            version="1.0.0",
            s3_uri="s3://bucket/datasets/text/v1/",
        )
        assert result["status"] == "success"
        assert result["mock"] is True

    @patch.dict(os.environ, {"MLOPS_ENV": "test"})
    def test_sync_dataset_dvc_output_format(self):
        from mcp_server.integrations.mlflow_adapter import DVCAdapter

        adapter = DVCAdapter(remote_name="custom-remote")
        result = adapter.sync_dataset_version(
            dataset_name="data",
            version="1.0.0",
            s3_uri="s3://bucket/data/v1/",
        )
        assert "Importing" in result["dvc_output"]
        assert result["remote_name"] == "custom-remote"
