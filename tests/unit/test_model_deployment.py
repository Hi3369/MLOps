"""
Model Deployment Capability Unit Tests

Model Deployment toolsのユニットテスト
"""

import json
import os
import sys
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

# Add mcp_server to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "mcp_server"))

from capabilities.model_deployment.tools import (
    configure_autoscaling,
    delete_autoscaling,
    delete_endpoint,
    deploy_to_sagemaker,
    health_check_endpoint,
    monitor_endpoint,
    rollback_deployment,
    update_endpoint_capacity,
    update_endpoint_traffic,
)


class TestDeployToSageMaker:
    """
    deploy_to_sagemaker関数のユニットテスト
    """

    @pytest.fixture
    def mock_sagemaker_deploy(self):
        """デプロイ用モックSageMakerクライアント"""
        with patch("boto3.client") as mock_client:
            mock_sagemaker = Mock()

            # create_model: モデル作成
            mock_sagemaker.create_model.return_value = {
                "ModelArn": "arn:aws:sagemaker:us-east-1:123456789012:model/test-model"
            }

            # create_endpoint_config: エンドポイント設定作成
            mock_sagemaker.create_endpoint_config.return_value = {
                "EndpointConfigArn": "arn:aws:sagemaker:us-east-1:123456789012:endpoint-config/test-config"
            }

            # describe_endpoint: 既存エンドポイントの確認（存在しない）
            from botocore.exceptions import ClientError

            mock_sagemaker.describe_endpoint.side_effect = ClientError(
                {"Error": {"Code": "ValidationException", "Message": "Not Found"}},
                "describe_endpoint",
            )

            # create_endpoint: エンドポイント作成
            mock_sagemaker.create_endpoint.return_value = {
                "EndpointArn": "arn:aws:sagemaker:us-east-1:123456789012:endpoint/test-endpoint"
            }

            mock_client.return_value = mock_sagemaker

            yield mock_sagemaker

    def test_deploy_to_sagemaker_success(self, mock_sagemaker_deploy):
        """
        SageMakerへのデプロイ成功テスト
        """
        result = deploy_to_sagemaker(
            model_s3_uri="s3://test-bucket/models/model.tar.gz",
            endpoint_name="test-endpoint",
            instance_type="ml.t3.medium",
            instance_count=1,
            wait_for_completion=False,
        )

        # 実行結果の確認
        assert result["status"] == "success"
        assert "deployment_info" in result

        # デプロイ情報の確認
        info = result["deployment_info"]
        assert info["endpoint_name"] == "test-endpoint"
        assert info["instance_type"] == "ml.t3.medium"
        assert info["instance_count"] == 1
        assert info["is_new_endpoint"] is True
        assert "model_name" in info
        assert "model_arn" in info
        assert "endpoint_arn" in info

        # SageMaker API呼び出しの確認
        mock_sagemaker_deploy.create_model.assert_called_once()
        mock_sagemaker_deploy.create_endpoint_config.assert_called_once()
        mock_sagemaker_deploy.create_endpoint.assert_called_once()

    def test_deploy_to_sagemaker_with_model_name(self, mock_sagemaker_deploy):
        """
        カスタムモデル名指定のテスト
        """
        result = deploy_to_sagemaker(
            model_s3_uri="s3://test-bucket/models/model.tar.gz",
            endpoint_name="test-endpoint",
            model_name="my-custom-model",
            wait_for_completion=False,
        )

        assert result["status"] == "success"
        assert result["deployment_info"]["model_name"] == "my-custom-model"

    def test_deploy_to_sagemaker_update_existing(self):
        """
        既存エンドポイントの更新テスト
        """
        with patch("boto3.client") as mock_client:
            mock_sagemaker = Mock()

            # モデル作成
            mock_sagemaker.create_model.return_value = {
                "ModelArn": "arn:aws:sagemaker:us-east-1:123456789012:model/test-model"
            }

            # エンドポイント設定作成
            mock_sagemaker.create_endpoint_config.return_value = {
                "EndpointConfigArn": "arn:aws:sagemaker:us-east-1:123456789012:endpoint-config/test-config"
            }

            # 既存エンドポイントが存在する
            mock_sagemaker.describe_endpoint.return_value = {
                "EndpointName": "test-endpoint",
                "EndpointStatus": "InService",
            }

            # エンドポイントを更新
            mock_sagemaker.update_endpoint.return_value = {
                "EndpointArn": "arn:aws:sagemaker:us-east-1:123456789012:endpoint/test-endpoint"
            }

            mock_client.return_value = mock_sagemaker

            result = deploy_to_sagemaker(
                model_s3_uri="s3://test-bucket/models/model.tar.gz",
                endpoint_name="test-endpoint",
                wait_for_completion=False,
            )

            # 更新フラグの確認
            assert result["status"] == "success"
            assert result["deployment_info"]["is_new_endpoint"] is False

            # update_endpointが呼ばれたことを確認
            mock_sagemaker.update_endpoint.assert_called_once()

    def test_deploy_to_sagemaker_invalid_uri(self):
        """
        無効なS3 URIのエラーハンドリングテスト
        """
        with pytest.raises(ValueError, match="Invalid S3 URI"):
            deploy_to_sagemaker(
                model_s3_uri="invalid://bucket/model.tar.gz",
                endpoint_name="test-endpoint",
            )


class TestUpdateEndpointTraffic:
    """
    update_endpoint_traffic関数のユニットテスト
    """

    @pytest.fixture
    def mock_sagemaker_traffic(self):
        """トラフィック更新用モックSageMakerクライアント"""
        with patch("boto3.client") as mock_client:
            mock_sagemaker = Mock()

            # describe_endpoint: エンドポイント情報
            mock_sagemaker.describe_endpoint.return_value = {
                "EndpointName": "test-endpoint",
                "ProductionVariants": [
                    {"VariantName": "VariantA", "CurrentWeight": 1.0},
                    {"VariantName": "VariantB", "CurrentWeight": 0.0},
                ],
            }

            # update_endpoint_weights_and_capacities: トラフィック更新
            mock_sagemaker.update_endpoint_weights_and_capacities.return_value = {}

            mock_client.return_value = mock_sagemaker

            yield mock_sagemaker

    def test_update_endpoint_traffic_success(self, mock_sagemaker_traffic):
        """
        トラフィック配分更新の成功テスト
        """
        result = update_endpoint_traffic(
            endpoint_name="test-endpoint",
            variant_weights={"VariantA": 0.7, "VariantB": 0.3},
        )

        # 実行結果の確認
        assert result["status"] == "success"
        assert "traffic_info" in result

        # トラフィック情報の確認
        info = result["traffic_info"]
        assert info["endpoint_name"] == "test-endpoint"
        assert info["variant_weights"] == {"VariantA": 0.7, "VariantB": 0.3}
        assert abs(info["total_weight"] - 1.0) < 0.001

        # SageMaker API呼び出しの確認
        mock_sagemaker_traffic.update_endpoint_weights_and_capacities.assert_called_once()

    def test_update_endpoint_traffic_canary_deployment(self, mock_sagemaker_traffic):
        """
        カナリアデプロイメント（10%トラフィック）のテスト
        """
        result = update_endpoint_traffic(
            endpoint_name="test-endpoint",
            variant_weights={"VariantA": 0.9, "VariantB": 0.1},
        )

        assert result["status"] == "success"
        assert result["traffic_info"]["variant_weights"]["VariantB"] == 0.1

    def test_update_endpoint_traffic_invalid_weights(self, mock_sagemaker_traffic):
        """
        無効な重み（合計が1.0でない）のエラーハンドリングテスト
        """
        with pytest.raises(ValueError, match="must sum to 1.0"):
            update_endpoint_traffic(
                endpoint_name="test-endpoint",
                variant_weights={"VariantA": 0.5, "VariantB": 0.3},
            )

    def test_update_endpoint_traffic_not_found(self):
        """
        エンドポイントが存在しない場合のエラーハンドリングテスト
        """
        with patch("boto3.client") as mock_client:
            mock_sagemaker = Mock()
            from botocore.exceptions import ClientError

            mock_sagemaker.describe_endpoint.side_effect = ClientError(
                {"Error": {"Code": "ValidationException", "Message": "Not Found"}},
                "describe_endpoint",
            )

            mock_client.return_value = mock_sagemaker

            with pytest.raises(ValueError, match="Endpoint not found"):
                update_endpoint_traffic(
                    endpoint_name="nonexistent-endpoint",
                    variant_weights={"VariantA": 1.0},
                )


class TestUpdateEndpointCapacity:
    """
    update_endpoint_capacity関数のユニットテスト
    """

    @pytest.fixture
    def mock_sagemaker_capacity(self):
        """容量更新用モックSageMakerクライアント"""
        with patch("boto3.client") as mock_client:
            mock_sagemaker = Mock()

            # update_endpoint_weights_and_capacities: 容量更新
            mock_sagemaker.update_endpoint_weights_and_capacities.return_value = {}

            mock_client.return_value = mock_sagemaker

            yield mock_sagemaker

    def test_update_endpoint_capacity_success(self, mock_sagemaker_capacity):
        """
        エンドポイント容量更新の成功テスト
        """
        result = update_endpoint_capacity(
            endpoint_name="test-endpoint",
            variant_name="AllTraffic",
            instance_count=3,
        )

        # 実行結果の確認
        assert result["status"] == "success"
        assert "capacity_info" in result

        # 容量情報の確認
        info = result["capacity_info"]
        assert info["endpoint_name"] == "test-endpoint"
        assert info["variant_name"] == "AllTraffic"
        assert info["instance_count"] == 3

        # SageMaker API呼び出しの確認
        mock_sagemaker_capacity.update_endpoint_weights_and_capacities.assert_called_once()

    def test_update_endpoint_capacity_scale_up(self, mock_sagemaker_capacity):
        """
        スケールアップ（インスタンス数増加）のテスト
        """
        result = update_endpoint_capacity(
            endpoint_name="test-endpoint",
            variant_name="AllTraffic",
            instance_count=5,
        )

        assert result["status"] == "success"
        assert result["capacity_info"]["instance_count"] == 5

    def test_update_endpoint_capacity_invalid_count(self):
        """
        無効なインスタンス数（0以下）のエラーハンドリングテスト
        """
        with pytest.raises(ValueError, match="must be at least 1"):
            update_endpoint_capacity(
                endpoint_name="test-endpoint",
                variant_name="AllTraffic",
                instance_count=0,
            )


class TestConfigureAutoscaling:
    """
    configure_autoscaling関数のユニットテスト
    """

    @pytest.fixture
    def mock_autoscaling(self):
        """オートスケーリング設定用モッククライアント"""
        with patch("boto3.client") as mock_client:
            mock_as = Mock()

            # register_scalable_target: スケーラブルターゲット登録
            mock_as.register_scalable_target.return_value = {}

            # put_scaling_policy: スケーリングポリシー設定
            mock_as.put_scaling_policy.return_value = {
                "PolicyARN": "arn:aws:autoscaling:us-east-1:123456789012:scalingPolicy:test-policy"
            }

            mock_client.return_value = mock_as

            yield mock_as

    def test_configure_autoscaling_success(self, mock_autoscaling):
        """
        オートスケーリング設定の成功テスト
        """
        result = configure_autoscaling(
            endpoint_name="test-endpoint",
            variant_name="AllTraffic",
            min_capacity=1,
            max_capacity=4,
            target_metric="SageMakerVariantInvocationsPerInstance",
            target_value=70.0,
        )

        # 実行結果の確認
        assert result["status"] == "success"
        assert "autoscaling_info" in result

        # オートスケーリング情報の確認
        info = result["autoscaling_info"]
        assert info["endpoint_name"] == "test-endpoint"
        assert info["variant_name"] == "AllTraffic"
        assert info["min_capacity"] == 1
        assert info["max_capacity"] == 4
        assert info["target_metric"] == "SageMakerVariantInvocationsPerInstance"
        assert info["target_value"] == 70.0
        assert "policy_arn" in info

        # API呼び出しの確認
        mock_autoscaling.register_scalable_target.assert_called_once()
        mock_autoscaling.put_scaling_policy.assert_called_once()

    def test_configure_autoscaling_cpu_metric(self, mock_autoscaling):
        """
        CPU使用率メトリクスを使用したオートスケーリング設定のテスト
        """
        result = configure_autoscaling(
            endpoint_name="test-endpoint",
            target_metric="CPUUtilization",
            target_value=75.0,
        )

        assert result["status"] == "success"
        assert result["autoscaling_info"]["target_metric"] == "CPUUtilization"

    def test_configure_autoscaling_invalid_min_capacity(self):
        """
        無効な最小容量（0以下）のエラーハンドリングテスト
        """
        with pytest.raises(ValueError, match="min_capacity must be at least 1"):
            configure_autoscaling(
                endpoint_name="test-endpoint",
                min_capacity=0,
                max_capacity=4,
            )

    def test_configure_autoscaling_invalid_max_capacity(self):
        """
        無効な最大容量（最小容量より小さい）のエラーハンドリングテスト
        """
        with pytest.raises(ValueError, match="max_capacity must be >= min_capacity"):
            configure_autoscaling(
                endpoint_name="test-endpoint",
                min_capacity=4,
                max_capacity=2,
            )

    def test_configure_autoscaling_invalid_metric(self):
        """
        無効なメトリクスタイプのエラーハンドリングテスト
        """
        with pytest.raises(ValueError, match="Invalid target_metric"):
            configure_autoscaling(
                endpoint_name="test-endpoint",
                target_metric="InvalidMetric",
            )


class TestDeleteAutoscaling:
    """
    delete_autoscaling関数のユニットテスト
    """

    @pytest.fixture
    def mock_autoscaling_delete(self):
        """オートスケーリング削除用モッククライアント"""
        with patch("boto3.client") as mock_client:
            mock_as = Mock()

            # delete_scaling_policy: スケーリングポリシー削除
            mock_as.delete_scaling_policy.return_value = {}

            # deregister_scalable_target: スケーラブルターゲット解除
            mock_as.deregister_scalable_target.return_value = {}

            mock_client.return_value = mock_as

            yield mock_as

    def test_delete_autoscaling_success(self, mock_autoscaling_delete):
        """
        オートスケーリング削除の成功テスト
        """
        result = delete_autoscaling(
            endpoint_name="test-endpoint",
            variant_name="AllTraffic",
        )

        # 実行結果の確認
        assert result["status"] == "success"
        assert "deletion_info" in result

        # 削除情報の確認
        info = result["deletion_info"]
        assert info["endpoint_name"] == "test-endpoint"
        assert info["variant_name"] == "AllTraffic"
        assert "deleted_policy" in info

        # API呼び出しの確認
        mock_autoscaling_delete.delete_scaling_policy.assert_called_once()
        mock_autoscaling_delete.deregister_scalable_target.assert_called_once()


class TestMonitorEndpoint:
    """
    monitor_endpoint関数のユニットテスト
    """

    @pytest.fixture
    def mock_sagemaker_monitor(self):
        """エンドポイント監視用モッククライアント"""
        with patch("boto3.client") as mock_client:

            def client_factory(service_name):
                if service_name == "sagemaker":
                    mock_sagemaker = Mock()
                    mock_sagemaker.describe_endpoint.return_value = {
                        "EndpointName": "test-endpoint",
                        "EndpointArn": "arn:aws:sagemaker:us-east-1:123456789012:endpoint/test-endpoint",
                        "EndpointStatus": "InService",
                        "CreationTime": datetime(2024, 1, 1, 0, 0, 0),
                        "LastModifiedTime": datetime(2024, 1, 2, 0, 0, 0),
                        "ProductionVariants": [
                            {
                                "VariantName": "AllTraffic",
                                "CurrentWeight": 1.0,
                                "DesiredWeight": 1.0,
                                "CurrentInstanceCount": 2,
                                "DesiredInstanceCount": 2,
                            }
                        ],
                    }
                    return mock_sagemaker
                elif service_name == "cloudwatch":
                    mock_cw = Mock()
                    mock_cw.get_metric_statistics.return_value = {
                        "Datapoints": [
                            {
                                "Timestamp": datetime.utcnow(),
                                "Sum": 100,
                                "Average": 50,
                                "Maximum": 150,
                            }
                        ]
                    }
                    return mock_cw

            mock_client.side_effect = client_factory

            yield mock_client

    def test_monitor_endpoint_success(self, mock_sagemaker_monitor):
        """
        エンドポイント監視の成功テスト
        """
        result = monitor_endpoint(
            endpoint_name="test-endpoint",
            include_metrics=True,
            metric_period_minutes=60,
        )

        # 実行結果の確認
        assert result["status"] == "success"
        assert "monitoring_info" in result

        # 監視情報の確認
        info = result["monitoring_info"]
        assert info["endpoint_name"] == "test-endpoint"
        assert info["endpoint_status"] == "InService"
        assert "production_variants" in info
        assert len(info["production_variants"]) == 1
        assert info["production_variants"][0]["variant_name"] == "AllTraffic"
        assert "metrics" in info

    def test_monitor_endpoint_without_metrics(self):
        """
        メトリクスなしのエンドポイント監視テスト
        """
        with patch("boto3.client") as mock_client:
            mock_sagemaker = Mock()
            mock_sagemaker.describe_endpoint.return_value = {
                "EndpointName": "test-endpoint",
                "EndpointArn": "arn:aws:sagemaker:us-east-1:123456789012:endpoint/test-endpoint",
                "EndpointStatus": "InService",
                "CreationTime": datetime(2024, 1, 1, 0, 0, 0),
                "LastModifiedTime": datetime(2024, 1, 2, 0, 0, 0),
                "ProductionVariants": [],
            }

            mock_client.return_value = mock_sagemaker

            result = monitor_endpoint(
                endpoint_name="test-endpoint",
                include_metrics=False,
            )

            # メトリクスが含まれていないことを確認
            assert result["status"] == "success"
            assert result["monitoring_info"]["metrics"] == {}

    def test_monitor_endpoint_not_found(self):
        """
        エンドポイントが存在しない場合のエラーハンドリングテスト
        """
        with patch("boto3.client") as mock_client:
            mock_sagemaker = Mock()
            from botocore.exceptions import ClientError

            mock_sagemaker.describe_endpoint.side_effect = ClientError(
                {"Error": {"Code": "ValidationException", "Message": "Not Found"}},
                "describe_endpoint",
            )

            mock_client.return_value = mock_sagemaker

            with pytest.raises(ValueError, match="Endpoint not found"):
                monitor_endpoint(endpoint_name="nonexistent-endpoint")


class TestHealthCheckEndpoint:
    """
    health_check_endpoint関数のユニットテスト
    """

    @pytest.fixture
    def mock_runtime(self):
        """SageMakerランタイム用モッククライアント"""
        with patch("boto3.client") as mock_client:
            mock_runtime = Mock()

            # invoke_endpoint: エンドポイント呼び出し
            import io

            response_body = json.dumps({"predictions": [0.9, 0.1]})
            mock_runtime.invoke_endpoint.return_value = {
                "Body": io.BytesIO(response_body.encode("utf-8")),
                "ResponseMetadata": {"HTTPStatusCode": 200},
            }

            mock_client.return_value = mock_runtime

            yield mock_runtime

    def test_health_check_endpoint_success(self, mock_runtime):
        """
        ヘルスチェック成功テスト
        """
        result = health_check_endpoint(endpoint_name="test-endpoint")

        # 実行結果の確認
        assert result["status"] == "success"
        assert "health_check_info" in result

        # ヘルスチェック情報の確認
        info = result["health_check_info"]
        assert info["endpoint_name"] == "test-endpoint"
        assert info["is_healthy"] is True
        assert "latency_ms" in info
        assert info["latency_ms"] > 0
        assert info["response_status_code"] == 200

        # SageMaker Runtime API呼び出しの確認
        mock_runtime.invoke_endpoint.assert_called_once()

    def test_health_check_endpoint_with_custom_payload(self, mock_runtime):
        """
        カスタムペイロード指定のヘルスチェックテスト
        """
        custom_payload = {"data": [[5, 6, 7, 8]]}

        result = health_check_endpoint(
            endpoint_name="test-endpoint",
            test_payload=custom_payload,
        )

        assert result["status"] == "success"
        assert result["health_check_info"]["test_payload"] == custom_payload

    def test_health_check_endpoint_failure(self):
        """
        ヘルスチェック失敗のテスト
        """
        with patch("boto3.client") as mock_client:
            mock_runtime = Mock()
            from botocore.exceptions import ClientError

            mock_runtime.invoke_endpoint.side_effect = ClientError(
                {"Error": {"Code": "ModelError", "Message": "Model failed"}},
                "invoke_endpoint",
            )

            mock_client.return_value = mock_runtime

            result = health_check_endpoint(endpoint_name="test-endpoint")

            # エラーステータスの確認
            assert result["status"] == "error"
            assert result["health_check_info"]["is_healthy"] is False
            assert "error" in result["health_check_info"]


class TestDeleteEndpoint:
    """
    delete_endpoint関数のユニットテスト
    """

    @pytest.fixture
    def mock_sagemaker_delete(self):
        """エンドポイント削除用モックSageMakerクライアント"""
        with patch("boto3.client") as mock_client:
            mock_sagemaker = Mock()

            # describe_endpoint: エンドポイント情報取得
            mock_sagemaker.describe_endpoint.return_value = {
                "EndpointName": "test-endpoint",
                "EndpointConfigName": "test-endpoint-config",
            }

            # describe_endpoint_config: エンドポイント設定情報取得
            mock_sagemaker.describe_endpoint_config.return_value = {
                "EndpointConfigName": "test-endpoint-config",
                "ProductionVariants": [
                    {"ModelName": "test-model-1"},
                    {"ModelName": "test-model-2"},
                ],
            }

            # delete_endpoint: エンドポイント削除
            mock_sagemaker.delete_endpoint.return_value = {}

            # delete_endpoint_config: エンドポイント設定削除
            mock_sagemaker.delete_endpoint_config.return_value = {}

            # delete_model: モデル削除
            mock_sagemaker.delete_model.return_value = {}

            mock_client.return_value = mock_sagemaker

            yield mock_sagemaker

    def test_delete_endpoint_success(self, mock_sagemaker_delete):
        """
        エンドポイント削除の成功テスト
        """
        result = delete_endpoint(
            endpoint_name="test-endpoint",
            delete_endpoint_config=True,
            delete_model=False,
        )

        # 実行結果の確認
        assert result["status"] == "success"
        assert "deletion_info" in result

        # 削除情報の確認
        info = result["deletion_info"]
        assert info["endpoint_name"] == "test-endpoint"
        assert "endpoint:test-endpoint" in info["deleted_resources"]
        assert "endpoint_config:test-endpoint-config" in info["deleted_resources"]
        assert len(info["model_names"]) == 0

        # API呼び出しの確認
        mock_sagemaker_delete.delete_endpoint.assert_called_once()
        mock_sagemaker_delete.delete_endpoint_config.assert_called_once()

    def test_delete_endpoint_with_model(self, mock_sagemaker_delete):
        """
        モデルも含めて削除するテスト
        """
        result = delete_endpoint(
            endpoint_name="test-endpoint",
            delete_endpoint_config=True,
            delete_model=True,
        )

        assert result["status"] == "success"
        info = result["deletion_info"]

        # モデルも削除されたことを確認
        assert len(info["model_names"]) == 2
        assert "model:test-model-1" in info["deleted_resources"]
        assert "model:test-model-2" in info["deleted_resources"]

        # delete_modelが2回呼ばれたことを確認
        assert mock_sagemaker_delete.delete_model.call_count == 2

    def test_delete_endpoint_only_endpoint(self, mock_sagemaker_delete):
        """
        エンドポイントのみ削除するテスト
        """
        result = delete_endpoint(
            endpoint_name="test-endpoint",
            delete_endpoint_config=False,
            delete_model=False,
        )

        assert result["status"] == "success"
        info = result["deletion_info"]

        # エンドポイントのみ削除
        assert "endpoint:test-endpoint" in info["deleted_resources"]
        assert len(info["deleted_resources"]) == 1

        # delete_endpoint_configは呼ばれない
        mock_sagemaker_delete.delete_endpoint_config.assert_not_called()

    def test_delete_endpoint_not_found(self):
        """
        エンドポイントが存在しない場合のエラーハンドリングテスト
        """
        with patch("boto3.client") as mock_client:
            mock_sagemaker = Mock()
            from botocore.exceptions import ClientError

            mock_sagemaker.describe_endpoint.side_effect = ClientError(
                {"Error": {"Code": "ValidationException", "Message": "Not Found"}},
                "describe_endpoint",
            )

            mock_client.return_value = mock_sagemaker

            with pytest.raises(ValueError, match="Endpoint not found"):
                delete_endpoint(endpoint_name="nonexistent-endpoint")


class TestRollbackDeployment:
    """
    rollback_deployment関数のユニットテスト
    """

    @pytest.fixture
    def mock_sagemaker_rollback(self):
        """ロールバック用モックSageMakerクライアント"""
        with patch("boto3.client") as mock_client:
            mock_sagemaker = Mock()

            # describe_endpoint: 現在のエンドポイント情報
            mock_sagemaker.describe_endpoint.return_value = {
                "EndpointName": "test-endpoint",
                "EndpointConfigName": "test-endpoint-config-v2",
            }

            # list_endpoint_configs: エンドポイント設定一覧
            mock_sagemaker.list_endpoint_configs.return_value = {
                "EndpointConfigs": [
                    {
                        "EndpointConfigName": "test-endpoint-config-v2",
                        "CreationTime": datetime(2024, 1, 2, 0, 0, 0),
                    },
                    {
                        "EndpointConfigName": "test-endpoint-config-v1",
                        "CreationTime": datetime(2024, 1, 1, 0, 0, 0),
                    },
                ]
            }

            # update_endpoint: エンドポイント更新（ロールバック）
            mock_sagemaker.update_endpoint.return_value = {}

            mock_client.return_value = mock_sagemaker

            yield mock_sagemaker

    def test_rollback_deployment_auto_detect(self, mock_sagemaker_rollback):
        """
        自動検出によるロールバックのテスト
        """
        result = rollback_deployment(endpoint_name="test-endpoint")

        # 実行結果の確認
        assert result["status"] == "success"
        assert "rollback_info" in result

        # ロールバック情報の確認
        info = result["rollback_info"]
        assert info["endpoint_name"] == "test-endpoint"
        assert info["current_config_name"] == "test-endpoint-config-v2"
        assert info["previous_config_name"] == "test-endpoint-config-v1"
        assert info["rollback_status"] == "InProgress"

        # API呼び出しの確認
        mock_sagemaker_rollback.update_endpoint.assert_called_once()

    def test_rollback_deployment_explicit_config(self, mock_sagemaker_rollback):
        """
        明示的な設定名指定によるロールバックのテスト
        """
        result = rollback_deployment(
            endpoint_name="test-endpoint",
            previous_config_name="test-endpoint-config-v1",
        )

        assert result["status"] == "success"
        assert result["rollback_info"]["previous_config_name"] == "test-endpoint-config-v1"

    def test_rollback_deployment_no_previous_config(self):
        """
        前の設定が存在しない場合のエラーハンドリングテスト
        """
        with patch("boto3.client") as mock_client:
            mock_sagemaker = Mock()

            # 現在のエンドポイント情報
            mock_sagemaker.describe_endpoint.return_value = {
                "EndpointName": "test-endpoint",
                "EndpointConfigName": "test-endpoint-config-v1",
            }

            # エンドポイント設定一覧（現在の設定のみ）
            mock_sagemaker.list_endpoint_configs.return_value = {
                "EndpointConfigs": [
                    {
                        "EndpointConfigName": "test-endpoint-config-v1",
                        "CreationTime": datetime(2024, 1, 1, 0, 0, 0),
                    }
                ]
            }

            mock_client.return_value = mock_sagemaker

            with pytest.raises(ValueError, match="No previous endpoint config found"):
                rollback_deployment(endpoint_name="test-endpoint")
