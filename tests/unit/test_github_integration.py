"""
GitHub Integration Capability Unit Tests

GitHub統合機能の単体テスト
"""

import pytest

from mcp_server.capabilities.github_integration.capability import (
    GitHubIntegrationCapability,
)
from mcp_server.capabilities.github_integration.tools import (
    detect_mlops_issue,
    parse_issue_config,
    start_workflow,
    validate_training_params,
)


class TestGitHubIntegrationCapability:
    """GitHubIntegrationCapability クラスのテスト"""

    def test_initialization(self):
        """初期化テスト"""
        capability = GitHubIntegrationCapability()
        assert capability is not None
        assert capability._tools is not None
        assert len(capability._tools) == 4

    def test_get_tools(self):
        """ツール取得テスト"""
        capability = GitHubIntegrationCapability()
        tools = capability.get_tools()

        assert "detect_mlops_issue" in tools
        assert "parse_issue_config" in tools
        assert "validate_training_params" in tools
        assert "start_workflow" in tools

    def test_get_tool_schemas(self):
        """ツールスキーマ取得テスト"""
        capability = GitHubIntegrationCapability()
        schemas = capability.get_tool_schemas()

        assert len(schemas) == 4
        for tool_name, schema in schemas.items():
            assert "name" in schema
            assert "description" in schema
            assert "parameters" in schema


class TestDetectMLOpsIssue:
    """detect_mlops_issue ツールのテスト"""

    def test_detect_issue_mock_data(self):
        """モックデータでのIssue検知テスト"""
        result = detect_mlops_issue(
            repo_owner="test-owner",
            repo_name="test-repo",
        )

        assert result["status"] == "success"
        assert "detection_result" in result
        assert result["detection_result"]["repo_owner"] == "test-owner"
        assert result["detection_result"]["repo_name"] == "test-repo"
        assert result["detection_result"]["total_issues"] > 0

    def test_detect_single_issue(self):
        """単一Issue検知テスト"""
        result = detect_mlops_issue(
            repo_owner="test-owner",
            repo_name="test-repo",
            issue_number=123,
        )

        assert result["status"] == "success"
        assert "detection_result" in result
        issues = result["detection_result"]["issues"]
        assert len(issues) >= 1
        assert issues[0]["issue_number"] == 123

    def test_detect_with_labels(self):
        """ラベルフィルタリング付きIssue検知テスト"""
        result = detect_mlops_issue(
            repo_owner="test-owner",
            repo_name="test-repo",
            labels=["mlops", "training"],
        )

        assert result["status"] == "success"
        assert "detection_result" in result

    def test_detect_issue_empty_repo_owner(self):
        """空のrepo_ownerでエラーテスト"""
        with pytest.raises(ValueError, match="repo_owner must not be empty"):
            detect_mlops_issue(repo_owner="", repo_name="test-repo")

    def test_detect_issue_empty_repo_name(self):
        """空のrepo_nameでエラーテスト"""
        with pytest.raises(ValueError, match="repo_name must not be empty"):
            detect_mlops_issue(repo_owner="test-owner", repo_name="")


class TestParseIssueConfig:
    """parse_issue_config ツールのテスト"""

    def test_parse_yaml_config(self):
        """YAML設定パーステスト"""
        issue_body = """
## Training Request

```yaml
training_config:
  model_type: xgboost
  dataset:
    s3_path: s3://my-bucket/data/
    target_column: label
  hyperparameters:
    n_estimators: 100
    max_depth: 6
```

Please train a model.
"""
        result = parse_issue_config(issue_body)

        assert result["status"] == "success"
        assert result["config"] is not None
        assert "parse_result" in result
        assert result["parse_result"]["found_blocks"] > 0

    def test_parse_json_config(self):
        """JSON設定パーステスト"""
        issue_body = """
## Training Request

```json
{
  "model_type": "random_forest",
  "dataset": {
    "s3_path": "s3://my-bucket/data/",
    "target_column": "target"
  }
}
```

Train a model please.
"""
        result = parse_issue_config(issue_body)

        assert result["status"] == "success"
        assert result["config"] is not None

    def test_parse_no_config_block(self):
        """設定ブロックなしテスト"""
        issue_body = "This is just a regular issue without config."

        result = parse_issue_config(issue_body)

        assert result["status"] == "warning"
        assert result["config"] is None
        assert result["parse_result"]["found_blocks"] == 0

    def test_parse_empty_body(self):
        """空のIssue本文でエラーテスト"""
        with pytest.raises(ValueError, match="issue_body must not be empty"):
            parse_issue_config("")

    def test_parse_with_format_specification(self):
        """フォーマット指定付きパーステスト"""
        issue_body = """
```yaml
model_type: xgboost
```

```json
{"model_type": "random_forest"}
```
"""
        # YAML指定
        result = parse_issue_config(issue_body, config_format="yaml")
        assert result["status"] == "success"

        # JSON指定
        result = parse_issue_config(issue_body, config_format="json")
        assert result["status"] == "success"

    def test_parse_invalid_format(self):
        """無効なフォーマット指定テスト"""
        with pytest.raises(ValueError, match="config_format must be"):
            parse_issue_config("body", config_format="invalid")


class TestValidateTrainingParams:
    """validate_training_params ツールのテスト"""

    def test_validate_valid_xgboost_config(self):
        """有効なXGBoost設定バリデーションテスト"""
        config = {
            "model_type": "xgboost",
            "dataset": {
                "s3_path": "s3://bucket/data/",
                "target_column": "label",
            },
            "hyperparameters": {
                "n_estimators": 100,
                "max_depth": 6,
                "learning_rate": 0.1,
            },
        }

        result = validate_training_params(config)

        assert result["status"] == "success"
        assert result["validation_result"]["is_valid"] is True
        assert len(result["validation_result"]["errors"]) == 0

    def test_validate_valid_random_forest_config(self):
        """有効なRandomForest設定バリデーションテスト"""
        config = {
            "model_type": "random_forest",
            "dataset": {
                "s3_path": "s3://bucket/data/",
                "target_column": "target",
            },
            "hyperparameters": {
                "n_estimators": 200,
                "max_depth": 10,
            },
        }

        result = validate_training_params(config)

        assert result["status"] == "success"
        assert result["validation_result"]["is_valid"] is True

    def test_validate_valid_neural_network_config(self):
        """有効なNeuralNetwork設定バリデーションテスト"""
        config = {
            "model_type": "neural_network",
            "dataset": {
                "s3_path": "s3://bucket/data/",
                "target_column": "label",
            },
            "hyperparameters": {
                "hidden_layers": [64, 32],
                "learning_rate": 0.001,
                "epochs": 100,
            },
        }

        result = validate_training_params(config)

        assert result["status"] == "success"
        assert result["validation_result"]["is_valid"] is True

    def test_validate_missing_model_type(self):
        """model_type欠落バリデーションテスト"""
        config = {
            "dataset": {
                "s3_path": "s3://bucket/data/",
                "target_column": "label",
            },
        }

        result = validate_training_params(config)

        assert result["status"] == "failed"
        assert result["validation_result"]["is_valid"] is False
        errors = result["validation_result"]["errors"]
        assert any("model_type" in e["field"] for e in errors)

    def test_validate_unsupported_model_type(self):
        """非サポートmodel_typeバリデーションテスト"""
        config = {
            "model_type": "unsupported_algorithm",
            "dataset": {
                "s3_path": "s3://bucket/data/",
                "target_column": "label",
            },
        }

        result = validate_training_params(config)

        assert result["status"] == "failed"
        errors = result["validation_result"]["errors"]
        assert any("Unsupported model_type" in e["message"] for e in errors)

    def test_validate_missing_dataset(self):
        """dataset欠落バリデーションテスト"""
        config = {
            "model_type": "xgboost",
        }

        result = validate_training_params(config)

        assert result["status"] == "failed"
        errors = result["validation_result"]["errors"]
        assert any("dataset" in e["field"] for e in errors)

    def test_validate_invalid_s3_path(self):
        """無効なS3パスバリデーションテスト"""
        config = {
            "model_type": "xgboost",
            "dataset": {
                "s3_path": "invalid/path",
                "target_column": "label",
            },
        }

        result = validate_training_params(config)

        assert result["status"] == "failed"
        errors = result["validation_result"]["errors"]
        assert any("s3://" in e["message"] for e in errors)

    def test_validate_hyperparameter_out_of_range(self):
        """ハイパーパラメータ範囲外バリデーションテスト"""
        config = {
            "model_type": "xgboost",
            "dataset": {
                "s3_path": "s3://bucket/data/",
                "target_column": "label",
            },
            "hyperparameters": {
                "n_estimators": -1,  # 無効値
                "learning_rate": 2.0,  # 範囲外
            },
        }

        result = validate_training_params(config)

        assert result["status"] == "failed"
        errors = result["validation_result"]["errors"]
        assert len(errors) > 0

    def test_validate_strict_mode(self):
        """厳密モードバリデーションテスト"""
        config = {
            "model_type": "xgboost",
            "dataset": {
                "s3_path": "s3://bucket/data/",
                "target_column": "label",
            },
            "hyperparameters": {
                "unknown_param": "value",  # 不明なパラメータ
            },
        }

        # 非厳密モード（警告のみ）
        result = validate_training_params(config, strict=False)
        assert result["status"] == "success"
        assert len(result["validation_result"]["warnings"]) > 0

        # 厳密モード（エラー）
        result = validate_training_params(config, strict=True)
        assert result["status"] == "failed"
        assert any(
            "Unknown parameter" in e["message"] for e in result["validation_result"]["errors"]
        )

    def test_validate_empty_config(self):
        """空の設定でエラーテスト"""
        with pytest.raises(ValueError, match="training_config must not be empty"):
            validate_training_params({})

    def test_validate_invalid_config_type(self):
        """無効な設定型でエラーテスト"""
        with pytest.raises(ValueError, match="training_config must be a dictionary"):
            validate_training_params("invalid")


class TestStartWorkflow:
    """start_workflow ツールのテスト"""

    def test_start_training_workflow(self):
        """トレーニングワークフロー起動テスト"""
        result = start_workflow(
            workflow_type="training",
            input_params={
                "model_type": "xgboost",
                "dataset": {"s3_path": "s3://bucket/data/"},
            },
        )

        assert result["status"] == "success"
        assert "workflow_result" in result
        assert result["workflow_result"]["workflow_type"] == "training"
        assert result["workflow_result"]["execution_status"] == "RUNNING"

    def test_start_inference_workflow(self):
        """推論ワークフロー起動テスト"""
        result = start_workflow(
            workflow_type="inference",
            input_params={
                "model_arn": "arn:aws:sagemaker:...",
                "input_data": {},
            },
        )

        assert result["status"] == "success"
        assert result["workflow_result"]["workflow_type"] == "inference"

    def test_start_batch_transform_workflow(self):
        """バッチ変換ワークフロー起動テスト"""
        result = start_workflow(
            workflow_type="batch_transform",
            input_params={
                "model_arn": "arn:aws:sagemaker:...",
                "input_data": {},
            },
        )

        assert result["status"] == "success"
        assert result["workflow_result"]["workflow_type"] == "batch_transform"

    def test_start_retraining_workflow(self):
        """再学習ワークフロー起動テスト"""
        result = start_workflow(
            workflow_type="retraining",
            input_params={
                "trigger_reason": "drift_detected",
                "original_model": {"model_id": "model-123"},
            },
        )

        assert result["status"] == "success"
        assert result["workflow_result"]["workflow_type"] == "retraining"

    def test_start_evaluation_workflow(self):
        """評価ワークフロー起動テスト"""
        result = start_workflow(
            workflow_type="evaluation",
            input_params={
                "model_arn": "arn:aws:sagemaker:...",
                "test_dataset": {"s3_path": "s3://test-data/"},
            },
        )

        assert result["status"] == "success"
        assert result["workflow_result"]["workflow_type"] == "evaluation"

    def test_start_with_custom_execution_name(self):
        """カスタム実行名でワークフロー起動テスト"""
        result = start_workflow(
            workflow_type="training",
            input_params={"model_type": "xgboost"},
            execution_name="custom-execution-name",
        )

        assert result["status"] == "success"
        assert result["workflow_result"]["execution_name"] == "custom-execution-name"

    def test_start_unsupported_workflow_type(self):
        """非サポートワークフロータイプでエラーテスト"""
        with pytest.raises(ValueError, match="Unsupported workflow_type"):
            start_workflow(
                workflow_type="unsupported",
                input_params={"model_type": "test"},
            )

    def test_start_empty_workflow_type(self):
        """空のワークフロータイプでエラーテスト"""
        with pytest.raises(ValueError, match="workflow_type must not be empty"):
            start_workflow(workflow_type="", input_params={})

    def test_start_empty_input_params(self):
        """空のinput_paramsでエラーテスト"""
        with pytest.raises(ValueError, match="input_params must not be empty"):
            start_workflow(workflow_type="training", input_params={})

    def test_start_invalid_input_params_type(self):
        """無効なinput_params型でエラーテスト"""
        with pytest.raises(ValueError, match="input_params must be a dictionary"):
            start_workflow(workflow_type="training", input_params="invalid")

    def test_workflow_result_contains_execution_arn(self):
        """ワークフロー結果にexecution_arnが含まれることをテスト"""
        result = start_workflow(
            workflow_type="training",
            input_params={"model_type": "xgboost"},
        )

        assert "execution_arn" in result["workflow_result"]
        assert "state_machine_arn" in result["workflow_result"]
        assert "start_time" in result["workflow_result"]


class TestIntegration:
    """統合テスト"""

    def test_issue_detection_to_workflow_start(self):
        """Issue検知からワークフロー起動までの流れテスト"""
        # 1. Issue検知
        detect_result = detect_mlops_issue(
            repo_owner="test-owner",
            repo_name="test-repo",
            issue_number=123,
        )
        assert detect_result["status"] == "success"

        # 2. 設定パース
        issue_body = detect_result["detection_result"]["issues"][0]["body"]
        parse_result = parse_issue_config(issue_body)

        # モックデータにはYAML設定ブロックが含まれているはず
        if parse_result["config"]:
            # 3. バリデーション
            # モックデータの設定を使用
            config = {
                "model_type": "xgboost",
                "dataset": {
                    "s3_path": "s3://mlops-data/churn-prediction/",
                    "target_column": "churned",
                },
                "hyperparameters": {
                    "n_estimators": 100,
                    "max_depth": 6,
                    "learning_rate": 0.1,
                },
            }
            validate_result = validate_training_params(config)
            assert validate_result["validation_result"]["is_valid"] is True

            # 4. ワークフロー起動
            workflow_result = start_workflow(
                workflow_type="training",
                input_params=config,
            )
            assert workflow_result["status"] == "success"
