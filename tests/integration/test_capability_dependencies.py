"""
Capability Dependencies Integration Tests

Capabilityの依存関係をテストする統合テスト
データ準備 → 学習 → 評価 → パッケージング → デプロイ → 監視 → 再学習

TDD: Red Phase - 失敗するテストケースを設計
"""

import io
import json
import os
import pickle
import sys
from datetime import datetime, timezone
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestClassifier

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

# history_managementはMLOpsServerに未登録のため直接インポート
from mcp_server.capabilities.history_management.tools.format_training_history import (
    format_training_history,
)
from mcp_server.capabilities.history_management.tools.post_issue_comment import (
    post_issue_comment,
)
from mcp_server.capabilities.history_management.tools.save_training_history import (
    save_training_history,
)
from mcp_server.capabilities.history_management.tools.track_version_history import (
    track_version_history,
)
from mcp_server.server import MLOpsServer


class TestDataPrepToTrainingFlow:
    """データ準備から学習への依存関係テスト"""

    @pytest.fixture
    def server(self) -> MLOpsServer:
        """テスト用サーバーインスタンス"""
        return MLOpsServer()

    @pytest.fixture
    def sample_data(self) -> pd.DataFrame:
        """テスト用サンプルデータ"""
        np.random.seed(42)
        return pd.DataFrame(
            {
                "feature1": np.random.randn(100),
                "feature2": np.random.randn(100),
                "feature3": np.random.randn(100),
                "target": np.random.randint(0, 2, 100),
            }
        )

    @pytest.fixture
    def mock_s3_client(self, sample_data: pd.DataFrame):
        """モックS3クライアント"""
        with patch("boto3.client") as mock_client:
            csv_buffer = io.StringIO()
            sample_data.to_csv(csv_buffer, index=False)
            csv_bytes = csv_buffer.getvalue().encode("utf-8")

            X = sample_data.drop("target", axis=1).values
            y = sample_data["target"].values
            trained_model = RandomForestClassifier(n_estimators=10, random_state=42)
            trained_model.fit(X, y)
            model_bytes = pickle.dumps(trained_model)

            mock_s3 = Mock()

            def get_object_handler(**kwargs):
                key = kwargs.get("Key", "")
                if key.endswith(".pkl"):
                    return {"Body": io.BytesIO(model_bytes)}
                return {"Body": io.BytesIO(csv_bytes)}

            mock_s3.get_object.side_effect = get_object_handler
            mock_s3.put_object.return_value = {}
            mock_client.return_value = mock_s3

            yield mock_s3

    def test_load_and_preprocess_flow(self, server: MLOpsServer, mock_s3_client):
        """データ読み込みから前処理へのフローテスト"""
        # Step 1: データ読み込み
        load_result = server.call_tool(
            "data_preparation.load_dataset",
            {"s3_uri": "s3://test-bucket/data.csv", "file_format": "csv"},
        )
        assert load_result["success"] is True

        # Step 2: データ読み込み結果を使って前処理
        preprocess_result = server.call_tool(
            "data_preparation.preprocess_supervised",
            {
                "s3_uri": "s3://test-bucket/data.csv",
                "target_column": "target",
                "file_format": "csv",
                "test_size": 0.2,
            },
        )
        assert preprocess_result["success"] is True
        assert "preprocessing_results" in preprocess_result["result"]

    def test_validate_and_preprocess_flow(self, server: MLOpsServer, mock_s3_client):
        """データ検証から前処理へのフローテスト"""
        # Step 1: データ検証
        validate_result = server.call_tool(
            "data_preparation.validate_data",
            {
                "s3_uri": "s3://test-bucket/data.csv",
                "file_format": "csv",
                "required_columns": ["feature1", "feature2", "target"],
            },
        )
        assert validate_result["success"] is True
        assert validate_result["result"]["validation_results"]["is_valid"] is True

        # Step 2: 検証成功後、前処理を実行
        preprocess_result = server.call_tool(
            "data_preparation.preprocess_supervised",
            {
                "s3_uri": "s3://test-bucket/data.csv",
                "target_column": "target",
                "file_format": "csv",
                "test_size": 0.2,
            },
        )
        assert preprocess_result["success"] is True

    def test_preprocess_to_training_flow(self, server: MLOpsServer, mock_s3_client):
        """前処理から学習へのフローテスト"""
        # Step 1: 前処理
        preprocess_result = server.call_tool(
            "data_preparation.preprocess_supervised",
            {
                "s3_uri": "s3://test-bucket/data.csv",
                "target_column": "target",
                "file_format": "csv",
                "test_size": 0.2,
            },
        )
        assert preprocess_result["success"] is True

        # Step 2: 前処理済みデータで学習
        train_result = server.call_tool(
            "ml_training.train_classification",
            {
                "train_data_s3_uri": "s3://test-bucket/train.csv",
                "algorithm": "random_forest",
                "hyperparameters": {"n_estimators": 10},
                "model_output_s3_uri": "s3://test-bucket/models/model.pkl",
                "file_format": "csv",
            },
        )
        assert train_result["success"] is True
        assert "training_results" in train_result["result"]


class TestTrainingToEvaluationFlow:
    """学習から評価への依存関係テスト"""

    @pytest.fixture
    def server(self) -> MLOpsServer:
        """テスト用サーバーインスタンス"""
        return MLOpsServer()

    @pytest.fixture
    def classification_data(self) -> pd.DataFrame:
        """分類用テストデータ"""
        np.random.seed(42)
        return pd.DataFrame(
            {
                "feature1": np.random.randn(100),
                "feature2": np.random.randn(100),
                "feature3": np.random.randn(100),
                "target": np.random.randint(0, 2, 100),
            }
        )

    @pytest.fixture
    def mock_s3_client(self, classification_data: pd.DataFrame):
        """モックS3クライアント"""
        with patch("boto3.client") as mock_client:
            csv_buffer = io.StringIO()
            classification_data.to_csv(csv_buffer, index=False)
            csv_bytes = csv_buffer.getvalue().encode("utf-8")

            X = classification_data.drop("target", axis=1).values
            y = classification_data["target"].values
            trained_model = RandomForestClassifier(n_estimators=10, random_state=42)
            trained_model.fit(X, y)
            model_bytes = pickle.dumps(trained_model)

            mock_s3 = Mock()

            def get_object_handler(**kwargs):
                key = kwargs.get("Key", "")
                if key.endswith(".pkl"):
                    return {"Body": io.BytesIO(model_bytes)}
                return {"Body": io.BytesIO(csv_bytes)}

            mock_s3.get_object.side_effect = get_object_handler
            mock_s3.put_object.return_value = {}
            mock_client.return_value = mock_s3

            yield mock_s3

    def test_train_classification_to_evaluate_flow(self, server: MLOpsServer, mock_s3_client):
        """分類学習から評価へのフローテスト"""
        # Step 1: モデル学習
        train_result = server.call_tool(
            "ml_training.train_classification",
            {
                "train_data_s3_uri": "s3://test-bucket/train.csv",
                "algorithm": "random_forest",
                "hyperparameters": {"n_estimators": 10},
                "model_output_s3_uri": "s3://test-bucket/models/model.pkl",
                "file_format": "csv",
            },
        )
        assert train_result["success"] is True

        # Step 2: 学習済みモデルで評価
        eval_result = server.call_tool(
            "ml_evaluation.evaluate_classification",
            {
                "model_s3_uri": "s3://test-bucket/models/model.pkl",
                "test_data_s3_uri": "s3://test-bucket/test.csv",
                "file_format": "csv",
            },
        )
        assert eval_result["success"] is True
        assert "evaluation_results" in eval_result["result"]
        assert "accuracy" in eval_result["result"]["evaluation_results"]

    def test_train_regression_to_evaluate_flow(self, server: MLOpsServer, mock_s3_client):
        """回帰学習から評価へのフローテスト"""
        # Step 1: モデル学習
        train_result = server.call_tool(
            "ml_training.train_regression",
            {
                "train_data_s3_uri": "s3://test-bucket/train.csv",
                "algorithm": "random_forest",
                "hyperparameters": {"n_estimators": 10},
                "model_output_s3_uri": "s3://test-bucket/models/model.pkl",
                "file_format": "csv",
            },
        )
        assert train_result["success"] is True

        # Step 2: 学習済みモデルで評価
        eval_result = server.call_tool(
            "ml_evaluation.evaluate_regression",
            {
                "model_s3_uri": "s3://test-bucket/models/model.pkl",
                "test_data_s3_uri": "s3://test-bucket/test.csv",
                "file_format": "csv",
            },
        )
        assert eval_result["success"] is True
        assert "evaluation_results" in eval_result["result"]

    def test_evaluation_to_shap_flow(self, server: MLOpsServer, mock_s3_client):
        """評価からSHAP分析へのフローテスト"""
        # Step 1: モデル評価
        eval_result = server.call_tool(
            "ml_evaluation.evaluate_classification",
            {
                "model_s3_uri": "s3://test-bucket/models/model.pkl",
                "test_data_s3_uri": "s3://test-bucket/test.csv",
                "file_format": "csv",
            },
        )
        assert eval_result["success"] is True

        # Step 2: SHAP分析
        shap_result = server.call_tool(
            "ml_evaluation.calculate_shap_values",
            {
                "model_s3_uri": "s3://test-bucket/models/model.pkl",
                "data_s3_uri": "s3://test-bucket/test.csv",
                "file_format": "csv",
            },
        )
        assert shap_result["success"] is True
        # 実際のAPIはshap_valuesとfeature_importanceを直接返す
        assert "shap_values" in shap_result["result"]
        assert "feature_importance" in shap_result["result"]


class TestEvaluationToPackagingFlow:
    """評価からパッケージングへの依存関係テスト"""

    @pytest.fixture
    def server(self) -> MLOpsServer:
        """テスト用サーバーインスタンス"""
        return MLOpsServer()

    @pytest.fixture
    def sample_data(self) -> pd.DataFrame:
        """テスト用サンプルデータ"""
        np.random.seed(42)
        return pd.DataFrame(
            {
                "feature1": np.random.randn(100),
                "feature2": np.random.randn(100),
                "feature3": np.random.randn(100),
                "target": np.random.randint(0, 2, 100),
            }
        )

    @pytest.fixture
    def mock_s3_client(self, sample_data: pd.DataFrame):
        """モックS3クライアント"""
        with patch("boto3.client") as mock_client:
            csv_buffer = io.StringIO()
            sample_data.to_csv(csv_buffer, index=False)
            csv_bytes = csv_buffer.getvalue().encode("utf-8")

            X = sample_data.drop("target", axis=1).values
            y = sample_data["target"].values
            trained_model = RandomForestClassifier(n_estimators=10, random_state=42)
            trained_model.fit(X, y)
            model_bytes = pickle.dumps(trained_model)

            mock_s3 = Mock()

            def get_object_handler(**kwargs):
                key = kwargs.get("Key", "")
                if key.endswith(".pkl"):
                    return {"Body": io.BytesIO(model_bytes)}
                return {"Body": io.BytesIO(csv_bytes)}

            mock_s3.get_object.side_effect = get_object_handler
            mock_s3.put_object.return_value = {}
            mock_client.return_value = mock_s3

            yield mock_s3

    def test_evaluate_to_registry_flow(self, server: MLOpsServer, mock_s3_client):
        """評価からモデルレジストリ登録へのフローテスト"""
        # Step 1: モデル評価
        eval_result = server.call_tool(
            "ml_evaluation.evaluate_classification",
            {
                "model_s3_uri": "s3://test-bucket/models/model.pkl",
                "test_data_s3_uri": "s3://test-bucket/test.csv",
                "file_format": "csv",
            },
        )
        assert eval_result["success"] is True
        metrics = eval_result["result"]["evaluation_results"]

        # Step 2: 評価結果を含めてモデルレジストリに登録
        register_result = server.call_tool(
            "model_registry.register_model",
            {
                "model_name": "test-classification-model",
                "model_s3_uri": "s3://test-bucket/models/model.pkl",
                "model_version": "1.0.0",
                "metadata": {
                    "algorithm": "random_forest",
                    "metrics": metrics,
                },
            },
        )
        assert register_result["success"] is True
        # 実際のAPIはregistration_infoを返す
        assert "registration_info" in register_result["result"]

    def test_evaluate_and_decide_deploy(self, server: MLOpsServer, mock_s3_client):
        """評価結果に基づくデプロイ判定フローテスト"""
        # Step 1: モデル評価
        eval_result = server.call_tool(
            "ml_evaluation.evaluate_classification",
            {
                "model_s3_uri": "s3://test-bucket/models/model.pkl",
                "test_data_s3_uri": "s3://test-bucket/test.csv",
                "file_format": "csv",
            },
        )
        assert eval_result["success"] is True
        metrics = eval_result["result"]["evaluation_results"]

        # Step 2: 閾値チェック（accuracy > 0.7）
        accuracy = metrics.get("accuracy", 0)
        should_deploy = accuracy > 0.7

        # Step 3: 条件を満たす場合のみデプロイ設定を生成
        if should_deploy:
            deploy_config_result = server.call_tool(
                "workflow_optimization.generate_optimization_proposal",
                {
                    "model_characteristics": {
                        "algorithm": "random_forest",
                        "resource_requirements": {"cpu": 4, "memory_gb": 8, "gpu": False},
                        "estimated_training_time_minutes": 10,
                    },
                    "constraints": {"max_training_time_minutes": 60},
                },
            )
            assert deploy_config_result["success"] is True


class TestDeploymentToMonitoringFlow:
    """デプロイから監視への依存関係テスト"""

    @pytest.fixture
    def server(self) -> MLOpsServer:
        """テスト用サーバーインスタンス"""
        return MLOpsServer()

    def test_deploy_to_health_check_flow(self, server: MLOpsServer):
        """デプロイからヘルスチェックへのフローテスト"""
        with patch("boto3.client") as mock_client:
            mock_runtime = Mock()
            mock_runtime.invoke_endpoint.return_value = {
                "Body": io.BytesIO(b'{"predictions": [1]}'),
                "ResponseMetadata": {"HTTPStatusCode": 200},
            }
            mock_client.return_value = mock_runtime

            # ヘルスチェック
            health_result = server.call_tool(
                "model_deployment.health_check_endpoint",
                {"endpoint_name": "test-endpoint"},
            )
            assert health_result["success"] is True
            assert "health_check_info" in health_result["result"]

    def test_endpoint_monitoring_flow(self, server: MLOpsServer):
        """エンドポイント監視フローテスト"""
        from datetime import datetime, timezone

        with patch("boto3.client") as mock_client:
            mock_sagemaker = Mock()
            mock_sagemaker.describe_endpoint.return_value = {
                "EndpointStatus": "InService",
                "EndpointName": "test-endpoint",
                "EndpointArn": "arn:aws:sagemaker:test-endpoint",
                "CreationTime": datetime.now(timezone.utc),
                "LastModifiedTime": datetime.now(timezone.utc),
                "ProductionVariants": [
                    {
                        "VariantName": "AllTraffic",
                        "CurrentWeight": 1.0,
                        "DesiredWeight": 1.0,
                        "CurrentInstanceCount": 1,
                        "DesiredInstanceCount": 1,
                    }
                ],
            }
            mock_client.return_value = mock_sagemaker

            # エンドポイント監視
            monitor_result = server.call_tool(
                "model_deployment.monitor_endpoint",
                {"endpoint_name": "test-endpoint", "include_metrics": False},
            )
            assert monitor_result["success"] is True
            assert "monitoring_info" in monitor_result["result"]


class TestMonitoringToRetrainFlow:
    """監視から再学習への依存関係テスト"""

    @pytest.fixture
    def server(self) -> MLOpsServer:
        """テスト用サーバーインスタンス"""
        return MLOpsServer()

    def test_drift_detection_to_alert_flow(self, server: MLOpsServer):
        """ドリフト検出からアラートへのフローテスト"""
        # Step 1: データドリフト検出
        drift_result = server.call_tool(
            "model_monitoring.detect_data_drift",
            {
                "baseline_data": {
                    "feature1": [1, 2, 3, 4, 5],
                    "feature2": [10, 20, 30, 40, 50],
                },
                "current_data": {
                    "feature1": [10, 20, 30, 40, 50],  # ドリフトあり
                    "feature2": [100, 200, 300, 400, 500],
                },
                "drift_threshold": 0.05,
                "method": "ks_test",
            },
        )
        assert drift_result["success"] is True
        drift_info = drift_result["result"]["drift_info"]

        # Step 2: ドリフト検出された場合、アラーム作成
        if drift_info.get("overall_drift_detected", False):
            with patch("boto3.client") as mock_client:
                mock_cw = Mock()
                mock_cw.put_metric_alarm.return_value = {}
                mock_client.return_value = mock_cw

                alarm_result = server.call_tool(
                    "model_monitoring.create_cloudwatch_alarm",
                    {
                        "alarm_name": "drift-detected-alarm",
                        "endpoint_name": "test-endpoint",
                        "metric_name": "ModelLatency",
                        "threshold": 1000,
                        "comparison_operator": "GreaterThanThreshold",
                        "evaluation_periods": 3,
                        "period_seconds": 300,
                    },
                )
                assert alarm_result["success"] is True

    def test_concept_drift_to_notification_flow(self, server: MLOpsServer):
        """コンセプトドリフトから通知へのフローテスト"""
        # Step 1: コンセプトドリフト検出
        drift_result = server.call_tool(
            "model_monitoring.detect_concept_drift",
            {
                "predictions": [0, 1, 0, 1, 0, 1, 0, 1],
                "actual_labels": [1, 0, 1, 0, 1, 0, 1, 0],  # 逆転（ドリフト）
                "window_size": 4,
                "drift_threshold": 0.1,
            },
        )
        assert drift_result["success"] is True
        drift_info = drift_result["result"]["drift_info"]

        # Step 2: ドリフト検出された場合、通知
        if drift_info.get("overall_drift_detected", False):
            notification_result = server.call_tool(
                "notification.send_slack_notification",
                {
                    "channel": "#mlops-alerts",
                    "message": "Concept drift detected! Retraining may be required.",
                },
            )
            assert notification_result["success"] is True


class TestGitHubIntegrationToWorkflow:
    """GitHub統合からワークフローへの依存関係テスト"""

    @pytest.fixture
    def server(self) -> MLOpsServer:
        """テスト用サーバーインスタンス"""
        return MLOpsServer()

    def test_issue_detection_to_workflow_start(self, server: MLOpsServer):
        """Issue検知からワークフロー開始へのフローテスト"""
        with patch("boto3.client") as mock_client:
            mock_ssm = Mock()
            mock_ssm.get_parameter.side_effect = Exception("Token not found")
            mock_client.return_value = mock_ssm

            # Step 1: Issue検知
            detect_result = server.call_tool(
                "github_integration.detect_mlops_issue",
                {
                    "repo_owner": "owner",
                    "repo_name": "repo",
                    "issue_number": 123,
                },
            )
            assert detect_result["success"] is True

            # Step 2: 検知されたIssue数を確認
            detection_result = detect_result["result"]["detection_result"]
            total_issues = detection_result.get("total_issues", 0)

            # Step 3: MLOps Issueがある場合、ワークフロー開始
            if total_issues > 0:
                workflow_result = server.call_tool(
                    "github_integration.start_workflow",
                    {
                        "workflow_type": "training",
                        "input_params": {
                            "algorithm": "random_forest",
                            "data_s3_uri": "s3://bucket/data.csv",
                        },
                    },
                )
                assert workflow_result["success"] is True

    def test_issue_config_parsing_to_validation_flow(self, server: MLOpsServer):
        """Issue設定パースからバリデーションへのフローテスト"""
        # Step 1: Issue設定パース
        parse_result = server.call_tool(
            "github_integration.parse_issue_config",
            {
                "issue_body": """
## Training Request

```yaml
algorithm: xgboost
hyperparameters:
  n_estimators: 100
  max_depth: 10
dataset:
  s3_path: s3://bucket/data.csv
```
"""
            },
        )
        assert parse_result["success"] is True

        # Step 2: パース結果を使ってバリデーション
        config = parse_result["result"]["config"]
        validate_result = server.call_tool(
            "github_integration.validate_training_params",
            {
                "training_config": {
                    "model_type": config.get("algorithm", "unknown"),
                    "hyperparameters": config.get("hyperparameters", {}),
                    "dataset": config.get("dataset", {}),
                }
            },
        )
        assert validate_result["success"] is True
        assert "validation_result" in validate_result["result"]


class TestNotificationChain:
    """通知チェーンの依存関係テスト"""

    @pytest.fixture
    def server(self) -> MLOpsServer:
        """テスト用サーバーインスタンス"""
        return MLOpsServer()

    def test_slack_to_email_notification_chain(self, server: MLOpsServer):
        """Slack通知からメール通知へのチェーンテスト"""
        # Step 1: Slack通知
        slack_result = server.call_tool(
            "notification.send_slack_notification",
            {
                "channel": "#mlops-alerts",
                "message": "Model training completed successfully",
            },
        )
        assert slack_result["success"] is True

        # Step 2: 重要なイベントの場合、メール通知も送信
        with patch("boto3.client") as mock_client:
            mock_ses = Mock()
            mock_ses.send_email.return_value = {"MessageId": "mock-id"}
            mock_client.return_value = mock_ses

            email_result = server.call_tool(
                "notification.send_email_notification",
                {
                    "to_addresses": ["team@example.com"],
                    "subject": "MLOps Alert: Training Completed",
                    "body": "Model training completed successfully",
                },
            )
            assert email_result["success"] is True

    def test_github_notification_chain(self, server: MLOpsServer):
        """GitHub通知チェーンテスト"""
        # Step 1: Issue コメント通知
        comment_result = server.call_tool(
            "notification.send_github_notification",
            {
                "repo_owner": "owner",
                "repo_name": "repo",
                "notification_type": "issue_comment",
                "target_number": 123,
                "message": "Training started for this request",
            },
        )
        assert comment_result["success"] is True

        # Step 2: 完了後、ラベル更新通知
        label_result = server.call_tool(
            "notification.send_github_notification",
            {
                "repo_owner": "owner",
                "repo_name": "repo",
                "notification_type": "issue_comment",
                "target_number": 123,
                "message": "Training completed! Adding 'completed' label.",
            },
        )
        assert label_result["success"] is True


class TestModelRegistryIntegration:
    """モデルレジストリ統合テスト"""

    @pytest.fixture
    def server(self) -> MLOpsServer:
        """テスト用サーバーインスタンス"""
        return MLOpsServer()

    @pytest.fixture
    def mock_s3_for_registry(self):
        """モックS3クライアント（レジストリ用）"""
        with patch("boto3.client") as mock_client:
            mock_s3 = Mock()

            # モデルファイル存在確認
            mock_s3.head_object.return_value = {
                "ContentLength": 1024,
                "LastModified": datetime.now(timezone.utc),
            }
            mock_s3.put_object.return_value = {}

            # get_object: 毎回新しいBytesIOを返す
            registry_metadata_dict = {
                "model_name": "test-model",
                "model_version": "1.0.0",
                "status": "registered",
                "registered_at": datetime.now(timezone.utc).isoformat(),
            }

            def get_object_handler(**kwargs):
                return {"Body": io.BytesIO(json.dumps(registry_metadata_dict).encode("utf-8"))}

            mock_s3.get_object.side_effect = get_object_handler

            # list_models用: paginator モック
            mock_paginator = Mock()
            mock_page = {"Contents": [{"Key": "models/test-model_registry.json"}]}
            mock_paginator.paginate.return_value = [mock_page]
            mock_s3.get_paginator.return_value = mock_paginator

            mock_client.return_value = mock_s3
            yield mock_s3

    def test_register_list_get_model_flow(self, server: MLOpsServer, mock_s3_for_registry):
        """モデル登録→一覧→取得のフローテスト"""
        # Step 1: モデル登録
        register_result = server.call_tool(
            "model_registry.register_model",
            {
                "model_name": "test-model",
                "model_s3_uri": "s3://test-bucket/models/model.pkl",
                "model_version": "1.0.0",
                "metadata": {"algorithm": "random_forest"},
            },
        )
        assert register_result["success"] is True

        # Step 2: モデル一覧取得（registry_s3_uri + status_filter）
        list_result = server.call_tool(
            "model_registry.list_models",
            {
                "registry_s3_uri": "s3://test-bucket/models/",
                "status_filter": "registered",
            },
        )
        assert list_result["success"] is True

        # Step 3: 特定モデル取得（model_s3_uri）
        get_result = server.call_tool(
            "model_registry.get_model",
            {
                "model_s3_uri": "s3://test-bucket/models/model.pkl",
            },
        )
        assert get_result["success"] is True
        assert "model_info" in get_result["result"]

    def test_model_status_update_flow(self, server: MLOpsServer, mock_s3_for_registry):
        """モデルステータス更新フローテスト"""
        # Step 1: モデル登録
        register_result = server.call_tool(
            "model_registry.register_model",
            {
                "model_name": "status-test-model",
                "model_s3_uri": "s3://test-bucket/models/model.pkl",
                "model_version": "1.0.0",
            },
        )
        assert register_result["success"] is True

        # Step 2: ステータスを「staging」に更新（model_s3_uri + status）
        update_result = server.call_tool(
            "model_registry.update_model_status",
            {
                "model_s3_uri": "s3://test-bucket/models/model.pkl",
                "status": "staging",
            },
        )
        assert update_result["success"] is True
        assert "update_info" in update_result["result"]

        # Step 3: ステータスを「production」に更新
        approve_result = server.call_tool(
            "model_registry.update_model_status",
            {
                "model_s3_uri": "s3://test-bucket/models/model.pkl",
                "status": "production",
            },
        )
        assert approve_result["success"] is True
        assert "update_info" in approve_result["result"]


class TestWorkflowOptimizationFlow:
    """ワークフロー最適化フローテスト"""

    @pytest.fixture
    def server(self) -> MLOpsServer:
        """テスト用サーバーインスタンス"""
        return MLOpsServer()

    def test_analyze_to_optimize_flow(self, server: MLOpsServer):
        """分析から最適化へのフローテスト"""
        # Step 1: モデル特性分析
        analyze_result = server.call_tool(
            "workflow_optimization.analyze_model_characteristics",
            {
                "model_config": {
                    "algorithm": "random_forest",
                    "hyperparameters": {"n_estimators": 100, "max_depth": 10},
                },
                "dataset_info": {
                    "size": 100000,
                    "num_features": 50,
                    "num_classes": 2,
                },
            },
        )
        assert analyze_result["success"] is True
        characteristics = analyze_result["result"]["characteristics"]

        # Step 2: 分析結果を使って最適化提案生成
        optimize_result = server.call_tool(
            "workflow_optimization.generate_optimization_proposal",
            {
                "model_characteristics": characteristics,
                "constraints": {
                    "max_training_time_minutes": 60,
                    "max_cost_usd": 100,
                },
            },
        )
        assert optimize_result["success"] is True
        assert "proposal" in optimize_result["result"]

    def test_retrieve_history_to_apply_flow(self, server: MLOpsServer):
        """履歴取得から適用へのフローテスト"""
        # Step 1: 類似モデル履歴取得
        history_result = server.call_tool(
            "workflow_optimization.retrieve_similar_model_history",
            {
                "model_type": "random_forest",
                "dataset_size": 50000,
                "limit": 5,
            },
        )
        assert history_result["success"] is True
        history = history_result["result"]["history"]

        # Step 2: 履歴を参考に最適化適用
        if history.get("total_records", 0) > 0:
            apply_result = server.call_tool(
                "workflow_optimization.apply_optimizations",
                {
                    "optimization_proposal": {
                        "type": "hyperparameter_tuning",
                        "suggestions": {"n_estimators": 200, "max_depth": 15},
                    },
                    "target_config": {
                        "model_name": "test-model",
                        "current_hyperparameters": {"n_estimators": 100, "max_depth": 10},
                    },
                },
            )
            assert apply_result["success"] is True


class TestHistoryRecordingFlow:
    """履歴記録フローの依存関係テスト
    注: history_managementはMLOpsServerに未登録のため直接呼び出し
    """

    def test_format_and_save_history_flow(self):
        """学習履歴フォーマット→保存のフローテスト"""
        # Step 1: 学習履歴をフォーマット
        format_result = format_training_history(
            training_job_name="test-training-job-001",
            metrics={"accuracy": 0.95, "loss": 0.05},
            hyperparameters={"n_estimators": 100, "max_depth": 10},
            model_name="test-model",
            model_version="1.0.0",
            output_format="markdown",
        )
        assert format_result["status"] == "success"
        assert "history_result" in format_result
        formatted_content = format_result["history_result"]["formatted_content"]

        # Step 2: フォーマットした履歴をS3に保存
        save_result = save_training_history(
            training_job_name="test-training-job-001",
            formatted_history=formatted_content,
            storage_type="s3",
            s3_bucket="mlops-history-bucket",
            s3_prefix="training_history/",
        )
        assert save_result["status"] == "success"
        assert "save_result" in save_result

    def test_format_history_to_github_comment_flow(self):
        """学習履歴フォーマット→GitHubコメント投稿のフローテスト"""
        # Step 1: 学習履歴をフォーマット
        format_result = format_training_history(
            training_job_name="github-report-job",
            metrics={"accuracy": 0.92, "f1_score": 0.90},
            model_name="github-report-model",
            output_format="markdown",
        )
        assert format_result["status"] == "success"
        formatted_content = format_result["history_result"]["formatted_content"]

        # Step 2: GitHubにコメント投稿
        comment_result = post_issue_comment(
            repository="owner/repo",
            issue_number=42,
            comment=formatted_content,
            comment_type="result",
        )
        assert comment_result["status"] == "success"
        assert "comment_result" in comment_result

    def test_version_tracking_flow(self):
        """バージョン追跡フローテスト"""
        # Step 1: 初期バージョン登録
        v1_result = track_version_history(
            model_name="version-test-model",
            version="v1.0.0",
            status="production",
            training_job_name="initial-training",
            tags=["baseline"],
        )
        assert v1_result["status"] == "success"
        assert "version_result" in v1_result

        # Step 2: 新バージョン登録（親バージョン指定）
        v2_result = track_version_history(
            model_name="version-test-model",
            version="v1.1.0",
            parent_version="v1.0.0",
            status="staging",
            training_job_name="retrain-job",
            code_version="abc1234",
            tags=["retrained", "drift-fix"],
        )
        assert v2_result["status"] == "success"
        lineage = v2_result["version_result"]["lineage"]
        assert lineage["parent_version"] == "v1.0.0"

    def test_format_history_multiple_formats(self):
        """複数フォーマットでの履歴フォーマットテスト"""
        metrics = {"accuracy": 0.88, "loss": 0.12, "precision": 0.87}

        for output_format in ["markdown", "json", "text"]:
            result = format_training_history(
                training_job_name=f"format-test-{output_format}",
                metrics=metrics,
                output_format=output_format,
            )
            assert result["status"] == "success"
            assert result["history_result"]["output_format"] == output_format


class TestTrainingToHistoryFlow:
    """学習から履歴記録への依存関係テスト"""

    @pytest.fixture
    def server(self) -> MLOpsServer:
        """テスト用サーバーインスタンス"""
        return MLOpsServer()

    @pytest.fixture
    def mock_s3_client(self):
        """モックS3クライアント"""
        with patch("boto3.client") as mock_client:
            np.random.seed(42)
            data = pd.DataFrame(
                {
                    "feature1": np.random.randn(100),
                    "feature2": np.random.randn(100),
                    "target": np.random.randint(0, 2, 100),
                }
            )
            csv_buffer = io.StringIO()
            data.to_csv(csv_buffer, index=False)
            csv_bytes = csv_buffer.getvalue().encode("utf-8")

            X = data.drop("target", axis=1).values
            y = data["target"].values
            model = RandomForestClassifier(n_estimators=10, random_state=42)
            model.fit(X, y)
            model_bytes = pickle.dumps(model)

            mock_s3 = Mock()

            def get_object_handler(**kwargs):
                key = kwargs.get("Key", "")
                if key.endswith(".pkl"):
                    return {"Body": io.BytesIO(model_bytes)}
                return {"Body": io.BytesIO(csv_bytes)}

            mock_s3.get_object.side_effect = get_object_handler
            mock_s3.put_object.return_value = {}
            mock_client.return_value = mock_s3
            yield mock_s3

    def test_train_evaluate_to_history_flow(self, server: MLOpsServer, mock_s3_client):
        """学習→評価→履歴記録の完全フローテスト"""
        # Step 1: モデル学習
        train_result = server.call_tool(
            "ml_training.train_classification",
            {
                "train_data_s3_uri": "s3://test-bucket/train.csv",
                "algorithm": "random_forest",
                "hyperparameters": {"n_estimators": 10},
                "model_output_s3_uri": "s3://test-bucket/models/model.pkl",
                "file_format": "csv",
            },
        )
        assert train_result["success"] is True

        # Step 2: モデル評価
        eval_result = server.call_tool(
            "ml_evaluation.evaluate_classification",
            {
                "model_s3_uri": "s3://test-bucket/models/model.pkl",
                "test_data_s3_uri": "s3://test-bucket/test.csv",
                "file_format": "csv",
            },
        )
        assert eval_result["success"] is True
        metrics = eval_result["result"]["evaluation_results"]

        # Step 3: 評価結果を履歴として記録（直接呼び出し）
        history_result = format_training_history(
            training_job_name="pipeline-train-001",
            metrics=metrics,
            model_name="pipeline-model",
            model_version="v1.0.0",
        )
        assert history_result["status"] == "success"
        assert "history_result" in history_result

    def test_train_to_version_tracking_flow(self, server: MLOpsServer, mock_s3_client):
        """学習→バージョン追跡フローテスト"""
        # Step 1: モデル学習
        train_result = server.call_tool(
            "ml_training.train_classification",
            {
                "train_data_s3_uri": "s3://test-bucket/train.csv",
                "algorithm": "random_forest",
                "hyperparameters": {"n_estimators": 10},
                "model_output_s3_uri": "s3://test-bucket/models/model.pkl",
                "file_format": "csv",
            },
        )
        assert train_result["success"] is True

        # Step 2: バージョン追跡（直接呼び出し）
        version_result = track_version_history(
            model_name="trained-model",
            version="v1.0.0",
            training_job_name="pipeline-train-001",
            training_data_version="dataset-v2",
            status="development",
            metadata={"algorithm": "random_forest", "n_estimators": 10},
        )
        assert version_result["status"] == "success"
        assert version_result["version_result"]["model_name"] == "trained-model"


class TestDriftToRetrainToNotifyFlow:
    """ドリフト検出→再学習→通知の完全フローテスト"""

    @pytest.fixture
    def server(self) -> MLOpsServer:
        """テスト用サーバーインスタンス"""
        return MLOpsServer()

    def test_drift_to_notification_to_history_flow(self, server: MLOpsServer):
        """ドリフト→通知→履歴記録のフローテスト"""
        # Step 1: ドリフト検出
        drift_result = server.call_tool(
            "model_monitoring.detect_data_drift",
            {
                "baseline_data": {
                    "feature1": [1, 2, 3, 4, 5],
                    "feature2": [10, 20, 30, 40, 50],
                },
                "current_data": {
                    "feature1": [10, 20, 30, 40, 50],
                    "feature2": [100, 200, 300, 400, 500],
                },
                "drift_threshold": 0.05,
                "method": "ks_test",
            },
        )
        assert drift_result["success"] is True

        # Step 2: ドリフト検出通知
        notify_result = server.call_tool(
            "notification.send_slack_notification",
            {
                "channel": "#mlops-alerts",
                "message": "Data drift detected! Automated retraining recommended.",
            },
        )
        assert notify_result["success"] is True

        # Step 3: 履歴に記録（直接呼び出し）
        history_result = post_issue_comment(
            repository="owner/mlops-repo",
            issue_number=100,
            comment="Data drift detected. Retraining triggered.",
            comment_type="progress",
        )
        assert history_result["status"] == "success"

    def test_concept_drift_to_retrain_trigger_flow(self, server: MLOpsServer):
        """コンセプトドリフト→GitHub通知→バージョン追跡のフローテスト"""
        # Step 1: コンセプトドリフト検出
        drift_result = server.call_tool(
            "model_monitoring.detect_concept_drift",
            {
                "predictions": [0, 1, 0, 1, 0, 1, 0, 1],
                "actual_labels": [1, 0, 1, 0, 1, 0, 1, 0],
                "window_size": 4,
                "drift_threshold": 0.1,
            },
        )
        assert drift_result["success"] is True

        # Step 2: GitHub通知でチームに報告
        github_notify_result = server.call_tool(
            "notification.send_github_notification",
            {
                "repo_owner": "owner",
                "repo_name": "repo",
                "notification_type": "issue_comment",
                "target_number": 50,
                "message": "Concept drift detected. Model accuracy degraded.",
            },
        )
        assert github_notify_result["success"] is True

        # Step 3: バージョン追跡に記録（直接呼び出し）
        track_result = track_version_history(
            model_name="drift-affected-model",
            version="v1.0.0",
            status="deprecated",
            tags=["concept-drift-detected"],
        )
        assert track_result["status"] == "success"


class TestRegistryToHistoryFlow:
    """モデルレジストリから履歴記録への依存関係テスト"""

    @pytest.fixture
    def server(self) -> MLOpsServer:
        """テスト用サーバーインスタンス"""
        return MLOpsServer()

    @pytest.fixture
    def mock_s3_for_registry(self):
        """モックS3クライアント（レジストリ用）"""
        with patch("boto3.client") as mock_client:
            mock_s3 = Mock()
            mock_s3.head_object.return_value = {
                "ContentLength": 1024,
                "LastModified": datetime.now(timezone.utc),
            }
            mock_s3.put_object.return_value = {}

            registry_metadata_dict = {
                "model_name": "registry-model",
                "model_version": "1.0.0",
                "status": "registered",
                "registered_at": datetime.now(timezone.utc).isoformat(),
            }

            def get_object_handler(**kwargs):
                return {"Body": io.BytesIO(json.dumps(registry_metadata_dict).encode("utf-8"))}

            mock_s3.get_object.side_effect = get_object_handler
            mock_client.return_value = mock_s3
            yield mock_s3

    def test_register_to_version_tracking_flow(self, server: MLOpsServer, mock_s3_for_registry):
        """モデル登録→バージョン追跡のフローテスト"""
        # Step 1: モデルレジストリに登録
        register_result = server.call_tool(
            "model_registry.register_model",
            {
                "model_name": "registry-model",
                "model_s3_uri": "s3://test-bucket/models/model.pkl",
                "model_version": "1.0.0",
                "metadata": {"algorithm": "xgboost"},
            },
        )
        assert register_result["success"] is True

        # Step 2: バージョン履歴に追跡（直接呼び出し）
        track_result = track_version_history(
            model_name="registry-model",
            version="v1.0.0",
            status="staging",
            training_job_name="xgboost-training-001",
            metadata={"registry_status": "registered"},
        )
        assert track_result["status"] == "success"
        assert track_result["version_result"]["status"] == "staging"

    def test_register_to_github_notification_flow(self, server: MLOpsServer, mock_s3_for_registry):
        """モデル登録→GitHub通知のフローテスト"""
        # Step 1: モデルレジストリに登録
        register_result = server.call_tool(
            "model_registry.register_model",
            {
                "model_name": "notify-model",
                "model_s3_uri": "s3://test-bucket/models/model.pkl",
                "model_version": "2.0.0",
            },
        )
        assert register_result["success"] is True

        # Step 2: GitHubに登録結果をコメント（直接呼び出し）
        comment_result = post_issue_comment(
            repository="owner/mlops-repo",
            issue_number=200,
            comment="Model notify-model v2.0.0 registered successfully.",
            comment_type="result",
        )
        assert comment_result["status"] == "success"
        assert "comment_result" in comment_result


class TestGitHubToHistoryFlow:
    """GitHub統合から履歴管理への依存関係テスト"""

    @pytest.fixture
    def server(self) -> MLOpsServer:
        """テスト用サーバーインスタンス"""
        return MLOpsServer()

    def test_issue_to_workflow_to_history_flow(self, server: MLOpsServer):
        """Issue検知→ワークフロー→履歴記録の完全フローテスト"""
        with patch("boto3.client") as mock_client:
            mock_ssm = Mock()
            mock_ssm.get_parameter.side_effect = Exception("Not found")
            mock_client.return_value = mock_ssm

            # Step 1: Issue設定パース
            parse_result = server.call_tool(
                "github_integration.parse_issue_config",
                {
                    "issue_body": """
## Training Request
```yaml
algorithm: random_forest
dataset:
  s3_path: s3://bucket/data.csv
```
"""
                },
            )
            assert parse_result["success"] is True

            # Step 2: ワークフロー開始
            workflow_result = server.call_tool(
                "github_integration.start_workflow",
                {
                    "workflow_type": "training",
                    "input_params": {
                        "algorithm": "random_forest",
                        "data_s3_uri": "s3://bucket/data.csv",
                    },
                },
            )
            assert workflow_result["success"] is True

        # Step 3: 実行履歴をGitHubに投稿（直接呼び出し）
        comment_result = post_issue_comment(
            repository="owner/repo",
            issue_number=77,
            comment="Workflow started for training request.",
            comment_type="progress",
        )
        assert comment_result["status"] == "success"

    def test_workflow_optimization_to_history_flow(self, server: MLOpsServer):
        """ワークフロー最適化→履歴追跡のフローテスト"""
        # Step 1: 最適化履歴を追跡（正しいパラメータ: optimization_id + results）
        track_result = server.call_tool(
            "workflow_optimization.track_optimization_history",
            {
                "optimization_id": "opt-001",
                "results": {
                    "status": "success",
                    "optimization_result": {
                        "total_optimizations_applied": 3,
                        "applied_optimizations": [
                            {"type": "hyperparameter_tuning"},
                            {"type": "resource_optimization"},
                            {"type": "pipeline_optimization"},
                        ],
                    },
                },
            },
        )
        assert track_result["success"] is True

        # Step 2: 最適化結果をバージョン追跡（直接呼び出し）
        version_result = track_version_history(
            model_name="optimized-model",
            version="v1.1.0",
            parent_version="v1.0.0",
            status="staging",
            tags=["optimized", "hyperparameter-tuned"],
        )
        assert version_result["status"] == "success"
