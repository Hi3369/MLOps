"""
AWS Integration Tests

AWSサービス統合テスト
各AWSサービスとの連携をモックベースでテスト

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
from botocore.exceptions import ClientError
from sklearn.ensemble import RandomForestClassifier

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from mcp_server.server import MLOpsServer


class TestS3DataOperations:
    """S3データ操作の統合テスト"""

    @pytest.fixture
    def server(self) -> MLOpsServer:
        return MLOpsServer()

    @pytest.fixture
    def sample_csv_data(self) -> bytes:
        np.random.seed(42)
        df = pd.DataFrame(
            {
                "feature1": np.random.randn(50),
                "feature2": np.random.randn(50),
                "target": np.random.randint(0, 2, 50),
            }
        )
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        return buf.getvalue().encode("utf-8")

    @pytest.fixture
    def trained_model_bytes(self) -> bytes:
        np.random.seed(42)
        X = np.random.randn(50, 2)
        y = np.random.randint(0, 2, 50)
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X, y)
        return pickle.dumps(model)

    def test_s3_upload_and_download_data(self, server: MLOpsServer, sample_csv_data: bytes):
        """S3へのデータアップロードとダウンロードテスト"""
        with patch("boto3.client") as mock_client:
            mock_s3 = Mock()
            mock_s3.get_object.return_value = {"Body": io.BytesIO(sample_csv_data)}
            mock_s3.put_object.return_value = {
                "ETag": '"abc123"',
                "VersionId": "v1",
            }
            mock_client.return_value = mock_s3

            # データ読み込み
            result = server.call_tool(
                "data_preparation.load_dataset",
                {"s3_uri": "s3://test-bucket/data/train.csv", "file_format": "csv"},
            )
            assert result["success"] is True
            mock_s3.get_object.assert_called_once()

    def test_s3_data_validation(self, server: MLOpsServer, sample_csv_data: bytes):
        """S3からのデータバリデーションテスト"""
        with patch("boto3.client") as mock_client:
            mock_s3 = Mock()
            mock_s3.get_object.return_value = {"Body": io.BytesIO(sample_csv_data)}
            mock_client.return_value = mock_s3

            result = server.call_tool(
                "data_preparation.validate_data",
                {
                    "s3_uri": "s3://test-bucket/data/train.csv",
                    "file_format": "csv",
                    "required_columns": ["feature1", "feature2", "target"],
                },
            )
            assert result["success"] is True
            assert result["result"]["validation_results"]["is_valid"] is True

    def test_s3_model_upload(
        self,
        server: MLOpsServer,
        sample_csv_data: bytes,
        trained_model_bytes: bytes,
    ):
        """S3へのモデルアップロードテスト"""
        with patch("boto3.client") as mock_client:
            mock_s3 = Mock()

            def get_object_handler(**kwargs):
                key = kwargs.get("Key", "")
                if key.endswith(".pkl"):
                    return {"Body": io.BytesIO(trained_model_bytes)}
                return {"Body": io.BytesIO(sample_csv_data)}

            mock_s3.get_object.side_effect = get_object_handler
            mock_s3.put_object.return_value = {}
            mock_client.return_value = mock_s3

            result = server.call_tool(
                "ml_training.train_classification",
                {
                    "train_data_s3_uri": "s3://test-bucket/data/train.csv",
                    "algorithm": "random_forest",
                    "hyperparameters": {"n_estimators": 10},
                    "model_output_s3_uri": "s3://test-bucket/models/rf_model.pkl",
                    "file_format": "csv",
                },
            )
            assert result["success"] is True
            assert mock_s3.put_object.called

    def test_s3_access_error_handling(self, server: MLOpsServer):
        """S3アクセスエラーハンドリングテスト"""
        with patch("boto3.client") as mock_client:
            mock_s3 = Mock()
            mock_s3.get_object.side_effect = ClientError(
                {
                    "Error": {
                        "Code": "NoSuchBucket",
                        "Message": "The specified bucket does not exist",
                    }
                },
                "GetObject",
            )
            mock_client.return_value = mock_s3

            result = server.call_tool(
                "data_preparation.load_dataset",
                {
                    "s3_uri": "s3://nonexistent-bucket/data.csv",
                    "file_format": "csv",
                },
            )
            assert result["success"] is False

    def test_s3_model_registry_operations(self, server: MLOpsServer, trained_model_bytes: bytes):
        """S3モデルレジストリ操作テスト"""
        with patch("boto3.client") as mock_client:
            mock_s3 = Mock()
            mock_s3.head_object.return_value = {
                "ContentLength": len(trained_model_bytes),
                "LastModified": datetime.now(timezone.utc),
            }
            mock_s3.put_object.return_value = {}

            registry_data = json.dumps(
                {
                    "model_name": "test-model",
                    "model_version": "1.0.0",
                    "status": "registered",
                }
            ).encode("utf-8")
            mock_s3.get_object.return_value = {"Body": io.BytesIO(registry_data)}

            mock_client.return_value = mock_s3

            # モデル登録
            result = server.call_tool(
                "model_registry.register_model",
                {
                    "model_name": "s3-test-model",
                    "model_s3_uri": "s3://test-bucket/models/model.pkl",
                    "model_version": "1.0.0",
                },
            )
            assert result["success"] is True
            mock_s3.head_object.assert_called()
            mock_s3.put_object.assert_called()


class TestSageMakerEndpoints:
    """SageMakerエンドポイントの統合テスト"""

    @pytest.fixture
    def server(self) -> MLOpsServer:
        return MLOpsServer()

    @pytest.fixture(autouse=True)
    def mock_env(self):
        with patch.dict(
            os.environ,
            {"SAGEMAKER_EXECUTION_ROLE_ARN": "arn:aws:iam::123456789012:role/SageMakerRole"},
        ):
            yield

    def test_create_endpoint(self, server: MLOpsServer):
        """SageMakerエンドポイント作成テスト"""
        with patch("boto3.client") as mock_client:
            mock_sm = Mock()
            # 1回目: 未存在（ClientError）、2回目: 作成完了（InService）
            not_found_error = ClientError(
                {"Error": {"Code": "ValidationException", "Message": "Not found"}},
                "DescribeEndpoint",
            )
            in_service_response = {
                "EndpointName": "test-endpoint",
                "EndpointStatus": "InService",
                "EndpointArn": "arn:aws:sagemaker:us-east-1:123:endpoint/test",
            }
            mock_sm.describe_endpoint.side_effect = [
                not_found_error,
                in_service_response,
            ]
            mock_sm.create_model.return_value = {
                "ModelArn": "arn:aws:sagemaker:us-east-1:123456789012:model/test-model"
            }
            mock_sm.create_endpoint_config.return_value = {
                "EndpointConfigArn": "arn:aws:sagemaker:us-east-1:123456789012:endpoint-config/cfg"
            }
            mock_sm.create_endpoint.return_value = {
                "EndpointArn": "arn:aws:sagemaker:us-east-1:123456789012:endpoint/ep"
            }
            mock_client.return_value = mock_sm

            result = server.call_tool(
                "model_deployment.deploy_to_sagemaker",
                {
                    "model_s3_uri": "s3://test-bucket/models/model.tar.gz",
                    "endpoint_name": "test-endpoint",
                    "instance_type": "ml.m5.large",
                    "instance_count": 1,
                },
            )
            assert result["success"] is True
            assert "deployment_info" in result["result"]
            mock_sm.create_model.assert_called_once()

    def test_describe_endpoint_in_service(self, server: MLOpsServer):
        """エンドポイントステータス確認テスト"""
        with patch("boto3.client") as mock_client:
            mock_sm = Mock()
            mock_sm.describe_endpoint.return_value = {
                "EndpointName": "test-endpoint",
                "EndpointStatus": "InService",
                "EndpointArn": "arn:aws:sagemaker:us-east-1:123:endpoint/test",
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
            mock_client.return_value = mock_sm

            result = server.call_tool(
                "model_deployment.monitor_endpoint",
                {"endpoint_name": "test-endpoint", "include_metrics": False},
            )
            assert result["success"] is True
            assert "monitoring_info" in result["result"]

    def test_endpoint_health_check(self, server: MLOpsServer):
        """エンドポイントヘルスチェックテスト"""
        with patch("boto3.client") as mock_client:
            mock_runtime = Mock()
            mock_runtime.invoke_endpoint.return_value = {
                "Body": io.BytesIO(b'{"predictions": [1]}'),
                "ResponseMetadata": {"HTTPStatusCode": 200},
            }
            mock_client.return_value = mock_runtime

            result = server.call_tool(
                "model_deployment.health_check_endpoint",
                {"endpoint_name": "test-endpoint"},
            )
            assert result["success"] is True
            assert "health_check_info" in result["result"]

    def test_endpoint_rollback(self, server: MLOpsServer):
        """エンドポイントロールバックテスト"""
        with patch("boto3.client") as mock_client:
            mock_sm = Mock()
            mock_sm.describe_endpoint.return_value = {
                "EndpointName": "rollback-endpoint",
                "EndpointStatus": "InService",
                "EndpointConfigName": "current-config",
            }
            mock_sm.update_endpoint.return_value = {
                "EndpointArn": "arn:aws:sagemaker:us-east-1:123:endpoint/rollback"
            }
            mock_client.return_value = mock_sm

            result = server.call_tool(
                "model_deployment.rollback_deployment",
                {
                    "endpoint_name": "rollback-endpoint",
                    "previous_config_name": "previous-config-v1",
                },
            )
            assert result["success"] is True
            assert "rollback_info" in result["result"]
            mock_sm.update_endpoint.assert_called_once()

    def test_autoscaling_configuration(self, server: MLOpsServer):
        """オートスケーリング設定テスト"""
        with patch("boto3.client") as mock_client:
            mock_as = Mock()
            mock_as.register_scalable_target.return_value = {}
            mock_as.put_scaling_policy.return_value = {
                "PolicyARN": "arn:aws:autoscaling:us-east-1:123:policy/test"
            }
            mock_client.return_value = mock_as

            result = server.call_tool(
                "model_deployment.configure_autoscaling",
                {
                    "endpoint_name": "autoscale-endpoint",
                    "variant_name": "AllTraffic",
                    "min_capacity": 1,
                    "max_capacity": 4,
                    "target_value": 70.0,
                },
            )
            assert result["success"] is True
            assert "autoscaling_info" in result["result"]
            mock_as.register_scalable_target.assert_called_once()
            mock_as.put_scaling_policy.assert_called_once()

    def test_traffic_update(self, server: MLOpsServer):
        """トラフィック更新テスト"""
        with patch("boto3.client") as mock_client:
            mock_sm = Mock()
            mock_sm.describe_endpoint.return_value = {
                "EndpointName": "traffic-endpoint",
                "EndpointStatus": "InService",
                "ProductionVariants": [
                    {
                        "VariantName": "VariantA",
                        "CurrentWeight": 1.0,
                        "CurrentInstanceCount": 1,
                    },
                    {
                        "VariantName": "VariantB",
                        "CurrentWeight": 0.0,
                        "CurrentInstanceCount": 1,
                    },
                ],
            }
            mock_sm.update_endpoint_weights_and_capacities.return_value = {
                "EndpointArn": "arn:aws:sagemaker:us-east-1:123:endpoint/traffic"
            }
            mock_client.return_value = mock_sm

            result = server.call_tool(
                "model_deployment.update_endpoint_traffic",
                {
                    "endpoint_name": "traffic-endpoint",
                    "variant_weights": {
                        "VariantA": 0.5,
                        "VariantB": 0.5,
                    },
                },
            )
            assert result["success"] is True
            assert "traffic_info" in result["result"]


class TestCloudWatchMetrics:
    """CloudWatchメトリクスの統合テスト"""

    @pytest.fixture
    def server(self) -> MLOpsServer:
        return MLOpsServer()

    def test_create_cloudwatch_alarm(self, server: MLOpsServer):
        """CloudWatchアラーム作成テスト"""
        with patch("boto3.client") as mock_client:
            mock_cw = Mock()
            mock_cw.put_metric_alarm.return_value = {}
            mock_client.return_value = mock_cw

            result = server.call_tool(
                "model_monitoring.create_cloudwatch_alarm",
                {
                    "alarm_name": "test-latency-alarm",
                    "endpoint_name": "test-endpoint",
                    "metric_name": "ModelLatency",
                    "threshold": 500.0,
                    "comparison_operator": "GreaterThanThreshold",
                    "evaluation_periods": 3,
                    "period_seconds": 300,
                },
            )
            assert result["success"] is True
            mock_cw.put_metric_alarm.assert_called_once()

    def test_collect_system_metrics(self, server: MLOpsServer):
        """システムメトリクス収集テスト"""
        with patch("boto3.client") as mock_client:
            mock_cw = Mock()
            mock_cw.get_metric_statistics.return_value = {
                "Datapoints": [
                    {
                        "Timestamp": datetime.now(timezone.utc),
                        "Average": 42.5,
                        "Minimum": 10.0,
                        "Maximum": 80.0,
                        "Sum": 425.0,
                        "SampleCount": 10.0,
                        "Unit": "Percent",
                    }
                ],
                "Label": "CPUUtilization",
            }
            mock_client.return_value = mock_cw

            result = server.call_tool(
                "model_monitoring.collect_system_metrics",
                {
                    "endpoint_name": "test-endpoint",
                    "time_range_minutes": 60,
                },
            )
            assert result["success"] is True
            assert "metrics_info" in result["result"]

    def test_detect_data_drift(self, server: MLOpsServer):
        """データドリフト検出テスト"""
        result = server.call_tool(
            "model_monitoring.detect_data_drift",
            {
                "baseline_data": {
                    "feature1": [1.0, 2.0, 3.0, 4.0, 5.0],
                    "feature2": [10.0, 20.0, 30.0, 40.0, 50.0],
                },
                "current_data": {
                    "feature1": [10.0, 20.0, 30.0, 40.0, 50.0],
                    "feature2": [100.0, 200.0, 300.0, 400.0, 500.0],
                },
                "drift_threshold": 0.05,
                "method": "ks_test",
            },
        )
        assert result["success"] is True
        drift_info = result["result"]["drift_info"]
        assert "overall_drift_detected" in drift_info

    def test_concept_drift_detection(self, server: MLOpsServer):
        """コンセプトドリフト検出テスト"""
        result = server.call_tool(
            "model_monitoring.detect_concept_drift",
            {
                "predictions": [0, 1, 0, 1, 0, 1, 0, 1],
                "actual_labels": [1, 0, 1, 0, 1, 0, 1, 0],
                "window_size": 4,
                "drift_threshold": 0.1,
            },
        )
        assert result["success"] is True
        assert "drift_info" in result["result"]


class TestStepFunctionsWorkflow:
    """Step Functionsワークフローの統合テスト"""

    @pytest.fixture
    def server(self) -> MLOpsServer:
        return MLOpsServer()

    def test_start_training_workflow(self, server: MLOpsServer):
        """学習ワークフロー開始テスト"""
        with patch("boto3.client") as mock_client:
            mock_ssm = Mock()
            mock_ssm.get_parameter.side_effect = Exception("Not found")
            mock_client.return_value = mock_ssm

            result = server.call_tool(
                "github_integration.start_workflow",
                {
                    "workflow_type": "training",
                    "input_params": {
                        "algorithm": "random_forest",
                        "data_s3_uri": "s3://bucket/data.csv",
                        "hyperparameters": {"n_estimators": 100},
                    },
                },
            )
            assert result["success"] is True
            assert "workflow_result" in result["result"]

    def test_start_inference_workflow(self, server: MLOpsServer):
        """推論ワークフロー開始テスト"""
        with patch("boto3.client") as mock_client:
            mock_ssm = Mock()
            mock_ssm.get_parameter.side_effect = Exception("Not found")
            mock_client.return_value = mock_ssm

            result = server.call_tool(
                "github_integration.start_workflow",
                {
                    "workflow_type": "inference",
                    "input_params": {
                        "model_s3_uri": "s3://bucket/models/model.tar.gz",
                        "endpoint_name": "production-endpoint",
                    },
                },
            )
            assert result["success"] is True

    def test_start_evaluation_workflow(self, server: MLOpsServer):
        """評価ワークフロー開始テスト"""
        with patch("boto3.client") as mock_client:
            mock_ssm = Mock()
            mock_ssm.get_parameter.side_effect = Exception("Not found")
            mock_client.return_value = mock_ssm

            result = server.call_tool(
                "github_integration.start_workflow",
                {
                    "workflow_type": "evaluation",
                    "input_params": {
                        "model_s3_uri": "s3://bucket/models/model.pkl",
                        "test_data_s3_uri": "s3://bucket/test.csv",
                    },
                },
            )
            assert result["success"] is True

    def test_validate_training_params(self, server: MLOpsServer):
        """学習パラメータバリデーションテスト"""
        result = server.call_tool(
            "github_integration.validate_training_params",
            {
                "training_config": {
                    "model_type": "random_forest",
                    "hyperparameters": {"n_estimators": 100, "max_depth": 10},
                    "dataset": {"s3_path": "s3://bucket/data.csv"},
                }
            },
        )
        assert result["success"] is True
        assert "validation_result" in result["result"]


class TestSESNotifications:
    """SES通知の統合テスト"""

    @pytest.fixture
    def server(self) -> MLOpsServer:
        return MLOpsServer()

    def test_send_email_notification(self, server: MLOpsServer):
        """メール通知送信テスト"""
        with patch("boto3.client") as mock_client:
            mock_ses = Mock()
            mock_ses.send_email.return_value = {"MessageId": "mock-message-id"}
            mock_client.return_value = mock_ses

            result = server.call_tool(
                "notification.send_email_notification",
                {
                    "to_addresses": ["team@example.com"],
                    "subject": "MLOps Alert: Model Training Completed",
                    "body": "The model training job has completed successfully.",
                },
            )
            assert result["success"] is True

    def test_send_slack_notification(self, server: MLOpsServer):
        """Slack通知送信テスト"""
        result = server.call_tool(
            "notification.send_slack_notification",
            {
                "channel": "#mlops-alerts",
                "message": "Model deployed to production endpoint",
            },
        )
        assert result["success"] is True

    def test_send_github_notification(self, server: MLOpsServer):
        """GitHub通知送信テスト"""
        result = server.call_tool(
            "notification.send_github_notification",
            {
                "repo_owner": "test-org",
                "repo_name": "mlops-repo",
                "notification_type": "issue_comment",
                "target_number": 42,
                "message": "Training job completed with accuracy: 0.95",
            },
        )
        assert result["success"] is True

    def test_multiple_notification_channels(self, server: MLOpsServer):
        """複数チャネル通知テスト"""
        # Slack
        slack_result = server.call_tool(
            "notification.send_slack_notification",
            {
                "channel": "#mlops-alerts",
                "message": "Deployment started",
            },
        )
        assert slack_result["success"] is True

        # GitHub
        github_result = server.call_tool(
            "notification.send_github_notification",
            {
                "repo_owner": "org",
                "repo_name": "repo",
                "notification_type": "issue_comment",
                "target_number": 10,
                "message": "Deployment started",
            },
        )
        assert github_result["success"] is True

        # Email
        with patch("boto3.client") as mock_client:
            mock_ses = Mock()
            mock_ses.send_email.return_value = {"MessageId": "id"}
            mock_client.return_value = mock_ses

            email_result = server.call_tool(
                "notification.send_email_notification",
                {
                    "to_addresses": ["admin@example.com"],
                    "subject": "Deployment Started",
                    "body": "A new deployment has been initiated.",
                },
            )
            assert email_result["success"] is True


class TestSSMParameterStore:
    """SSMパラメータストアの統合テスト"""

    @pytest.fixture
    def server(self) -> MLOpsServer:
        return MLOpsServer()

    def test_github_token_retrieval_failure(self, server: MLOpsServer):
        """GitHubトークン取得失敗時のハンドリングテスト"""
        with patch("boto3.client") as mock_client:
            mock_ssm = Mock()
            mock_ssm.get_parameter.side_effect = ClientError(
                {
                    "Error": {
                        "Code": "ParameterNotFound",
                        "Message": "Token not found",
                    }
                },
                "GetParameter",
            )
            mock_client.return_value = mock_ssm

            # SSMからトークン取得失敗→Issue検知はモック動作
            result = server.call_tool(
                "github_integration.detect_mlops_issue",
                {
                    "repo_owner": "owner",
                    "repo_name": "repo",
                    "issue_number": 1,
                },
            )
            assert result["success"] is True

    def test_issue_config_parsing(self, server: MLOpsServer):
        """Issue設定パーステスト"""
        result = server.call_tool(
            "github_integration.parse_issue_config",
            {
                "issue_body": """
## ML Training Request

```yaml
algorithm: xgboost
hyperparameters:
  n_estimators: 200
  max_depth: 8
  learning_rate: 0.1
dataset:
  s3_path: s3://ml-data/training/v2.csv
  validation_split: 0.2
```
"""
            },
        )
        assert result["success"] is True
        config = result["result"]["config"]
        assert config["algorithm"] == "xgboost"


class TestModelRegistryAWS:
    """モデルレジストリAWS操作テスト"""

    @pytest.fixture
    def server(self) -> MLOpsServer:
        return MLOpsServer()

    @pytest.fixture
    def mock_s3_registry(self):
        with patch("boto3.client") as mock_client:
            mock_s3 = Mock()
            mock_s3.head_object.return_value = {
                "ContentLength": 2048,
                "LastModified": datetime.now(timezone.utc),
            }
            mock_s3.put_object.return_value = {}

            registry_data = {
                "model_name": "aws-model",
                "model_version": "1.0.0",
                "status": "registered",
                "registered_at": datetime.now(timezone.utc).isoformat(),
            }

            def get_object_handler(**kwargs):
                return {"Body": io.BytesIO(json.dumps(registry_data).encode("utf-8"))}

            mock_s3.get_object.side_effect = get_object_handler

            mock_paginator = Mock()
            mock_paginator.paginate.return_value = [
                {
                    "Contents": [
                        {"Key": "models/aws-model_registry.json"},
                        {"Key": "models/v2-model_registry.json"},
                    ]
                }
            ]
            mock_s3.get_paginator.return_value = mock_paginator

            mock_client.return_value = mock_s3
            yield mock_s3

    def test_register_model(self, server: MLOpsServer, mock_s3_registry):
        """モデル登録テスト"""
        result = server.call_tool(
            "model_registry.register_model",
            {
                "model_name": "aws-model",
                "model_s3_uri": "s3://test-bucket/models/model.pkl",
                "model_version": "1.0.0",
                "metadata": {
                    "algorithm": "xgboost",
                    "metrics": {"accuracy": 0.95},
                },
            },
        )
        assert result["success"] is True
        assert "registration_info" in result["result"]

    def test_list_models(self, server: MLOpsServer, mock_s3_registry):
        """モデル一覧取得テスト"""
        result = server.call_tool(
            "model_registry.list_models",
            {
                "registry_s3_uri": "s3://test-bucket/models/",
            },
        )
        assert result["success"] is True
        assert "models" in result["result"]

    def test_get_model_info(self, server: MLOpsServer, mock_s3_registry):
        """モデル情報取得テスト"""
        result = server.call_tool(
            "model_registry.get_model",
            {"model_s3_uri": "s3://test-bucket/models/model.pkl"},
        )
        assert result["success"] is True
        assert "model_info" in result["result"]

    def test_update_model_status(self, server: MLOpsServer, mock_s3_registry):
        """モデルステータス更新テスト"""
        result = server.call_tool(
            "model_registry.update_model_status",
            {
                "model_s3_uri": "s3://test-bucket/models/model.pkl",
                "status": "production",
            },
        )
        assert result["success"] is True
        assert "update_info" in result["result"]


class TestEndpointCreation:
    """エンドポイント作成の統合テスト"""

    @pytest.fixture
    def server(self) -> MLOpsServer:
        return MLOpsServer()

    @pytest.fixture(autouse=True)
    def mock_env(self):
        with patch.dict(
            os.environ,
            {"SAGEMAKER_EXECUTION_ROLE_ARN": "arn:aws:iam::123456789012:role/SageMakerRole"},
        ):
            yield

    def test_full_endpoint_lifecycle(self, server: MLOpsServer):
        """エンドポイントの完全ライフサイクルテスト（作成→確認→削除）"""
        with patch("boto3.client") as mock_client:
            mock_sm = Mock()

            # Step 1: エンドポイント作成（未存在→作成完了）
            not_found_error = ClientError(
                {"Error": {"Code": "ValidationException", "Message": "Not found"}},
                "DescribeEndpoint",
            )
            in_service_response = {
                "EndpointName": "lifecycle-ep",
                "EndpointStatus": "InService",
                "EndpointArn": "arn:aws:sagemaker:us-east-1:123:endpoint/lifecycle-ep",
            }
            mock_sm.describe_endpoint.side_effect = [
                not_found_error,
                in_service_response,
            ]
            mock_sm.create_model.return_value = {
                "ModelArn": "arn:aws:sagemaker:us-east-1:123:model/lifecycle-model"
            }
            mock_sm.create_endpoint_config.return_value = {
                "EndpointConfigArn": "arn:aws:sagemaker:us-east-1:123:endpoint-config/cfg"
            }
            mock_sm.create_endpoint.return_value = {
                "EndpointArn": "arn:aws:sagemaker:us-east-1:123:endpoint/lifecycle-ep"
            }
            mock_client.return_value = mock_sm

            create_result = server.call_tool(
                "model_deployment.deploy_to_sagemaker",
                {
                    "model_s3_uri": "s3://bucket/models/model.tar.gz",
                    "endpoint_name": "lifecycle-ep",
                    "instance_type": "ml.m5.xlarge",
                    "instance_count": 1,
                },
            )
            assert create_result["success"] is True

        # Step 2: エンドポイント状態確認
        with patch("boto3.client") as mock_client:
            mock_sm = Mock()
            mock_sm.describe_endpoint.return_value = {
                "EndpointName": "lifecycle-ep",
                "EndpointStatus": "InService",
                "EndpointArn": "arn:aws:sagemaker:us-east-1:123:endpoint/lifecycle-ep",
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
            mock_client.return_value = mock_sm

            monitor_result = server.call_tool(
                "model_deployment.monitor_endpoint",
                {"endpoint_name": "lifecycle-ep", "include_metrics": False},
            )
            assert monitor_result["success"] is True

        # Step 3: エンドポイントロールバック
        with patch("boto3.client") as mock_client:
            mock_sm = Mock()
            mock_sm.describe_endpoint.return_value = {
                "EndpointName": "lifecycle-ep",
                "EndpointStatus": "InService",
                "EndpointConfigName": "lifecycle-config-v2",
            }
            mock_sm.update_endpoint.return_value = {
                "EndpointArn": "arn:aws:sagemaker:us-east-1:123:endpoint/lifecycle-ep"
            }
            mock_client.return_value = mock_sm

            rollback_result = server.call_tool(
                "model_deployment.rollback_deployment",
                {
                    "endpoint_name": "lifecycle-ep",
                    "previous_config_name": "lifecycle-config-v1",
                },
            )
            assert rollback_result["success"] is True

    def test_ab_testing_endpoint(self, server: MLOpsServer):
        """A/Bテストエンドポイント設定テスト"""
        with patch("boto3.client") as mock_client:
            mock_sm = Mock()
            mock_sm.describe_endpoint.return_value = {
                "EndpointName": "ab-test-endpoint",
                "EndpointStatus": "InService",
                "ProductionVariants": [
                    {
                        "VariantName": "ModelA",
                        "CurrentWeight": 1.0,
                        "CurrentInstanceCount": 1,
                    },
                    {
                        "VariantName": "ModelB",
                        "CurrentWeight": 0.0,
                        "CurrentInstanceCount": 1,
                    },
                ],
            }
            mock_sm.update_endpoint_weights_and_capacities.return_value = {
                "EndpointArn": "arn:aws:sagemaker:us-east-1:123:endpoint/ab-test"
            }
            mock_client.return_value = mock_sm

            # A/Bテスト: 50/50のトラフィック分割
            result = server.call_tool(
                "model_deployment.update_endpoint_traffic",
                {
                    "endpoint_name": "ab-test-endpoint",
                    "variant_weights": {
                        "ModelA": 0.5,
                        "ModelB": 0.5,
                    },
                },
            )
            assert result["success"] is True
            assert "traffic_info" in result["result"]


class TestWorkflowOptimizationAWS:
    """ワークフロー最適化のAWS統合テスト"""

    @pytest.fixture
    def server(self) -> MLOpsServer:
        return MLOpsServer()

    def test_analyze_model_for_aws_deployment(self, server: MLOpsServer):
        """AWSデプロイ用モデル分析テスト"""
        result = server.call_tool(
            "workflow_optimization.analyze_model_characteristics",
            {
                "model_config": {
                    "algorithm": "xgboost",
                    "hyperparameters": {
                        "n_estimators": 500,
                        "max_depth": 12,
                        "learning_rate": 0.05,
                    },
                },
                "dataset_info": {
                    "size": 500000,
                    "num_features": 100,
                    "num_classes": 5,
                },
            },
        )
        assert result["success"] is True
        assert "characteristics" in result["result"]

    def test_generate_aws_optimization_proposal(self, server: MLOpsServer):
        """AWS最適化提案生成テスト"""
        result = server.call_tool(
            "workflow_optimization.generate_optimization_proposal",
            {
                "model_characteristics": {
                    "algorithm": "xgboost",
                    "resource_requirements": {
                        "cpu": 8,
                        "memory_gb": 32,
                        "gpu": True,
                    },
                    "estimated_training_time_minutes": 120,
                },
                "constraints": {
                    "max_training_time_minutes": 60,
                    "max_cost_usd": 50,
                },
            },
        )
        assert result["success"] is True
        assert "proposal" in result["result"]

    def test_track_optimization_history(self, server: MLOpsServer):
        """最適化履歴追跡テスト"""
        result = server.call_tool(
            "workflow_optimization.track_optimization_history",
            {
                "optimization_id": "aws-opt-001",
                "results": {
                    "status": "success",
                    "optimization_result": {
                        "total_optimizations_applied": 2,
                        "applied_optimizations": [
                            {"type": "instance_type_optimization"},
                            {"type": "hyperparameter_tuning"},
                        ],
                    },
                },
            },
        )
        assert result["success"] is True
