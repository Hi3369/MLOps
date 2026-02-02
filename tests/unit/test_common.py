"""
Common モジュールのテスト

対象:
- mcp_server/common/config.py
- mcp_server/common/exceptions.py
- mcp_server/common/logger.py
- mcp_server/common/s3_utils.py
- mcp_server/common/metrics.py
- mcp_server/common/secrets.py
- mcp_server/config.py
- mcp_server/router.py
"""

import json
import logging
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ===== common/__init__.py =====


class TestCommonInit:
    """common パッケージの初期化テスト"""

    def test_import_common(self):
        import mcp_server.common

        assert hasattr(mcp_server.common, "__all__")

    def test_all_exports(self):
        from mcp_server.common import __all__

        assert "logger" in __all__
        assert "s3_utils" in __all__
        assert "config" in __all__


# ===== common/config.py =====


class TestCommonConfig:
    """common/config.py のテスト"""

    def test_default_values(self):
        from mcp_server.common.config import Config

        config = Config()
        assert config.log_level == "INFO"
        assert config.s3_bucket == "mlops-bucket"
        assert config.aws_region == "us-west-2"

    def test_env_override(self):
        from mcp_server.common.config import Config

        with patch.dict(
            os.environ,
            {
                "LOG_LEVEL": "DEBUG",
                "MLOPS_S3_BUCKET": "custom-bucket",
                "AWS_REGION": "ap-northeast-1",
            },
        ):
            config = Config()
            assert config.log_level == "DEBUG"
            assert config.s3_bucket == "custom-bucket"
            assert config.aws_region == "ap-northeast-1"

    def test_to_dict(self):
        from mcp_server.common.config import Config

        config = Config()
        d = config.to_dict()
        assert isinstance(d, dict)
        assert "log_level" in d
        assert "s3_bucket" in d
        assert "aws_region" in d
        assert d["log_level"] == config.log_level


# ===== common/exceptions.py =====


class TestExceptions:
    """custom例外のテスト"""

    def test_base_exception(self):
        from mcp_server.common.exceptions import MCPServerError

        with pytest.raises(MCPServerError):
            raise MCPServerError("test error")

    def test_tool_not_found_error(self):
        from mcp_server.common.exceptions import MCPServerError, ToolNotFoundError

        err = ToolNotFoundError("tool_x")
        assert isinstance(err, MCPServerError)
        assert str(err) == "tool_x"

    def test_configuration_error(self):
        from mcp_server.common.exceptions import ConfigurationError, MCPServerError

        err = ConfigurationError("bad config")
        assert isinstance(err, MCPServerError)

    def test_data_validation_error(self):
        from mcp_server.common.exceptions import DataValidationError, MCPServerError

        err = DataValidationError("invalid data")
        assert isinstance(err, MCPServerError)

    def test_s3_error(self):
        from mcp_server.common.exceptions import MCPServerError, S3Error

        err = S3Error("bucket not found")
        assert isinstance(err, MCPServerError)

    def test_sagemaker_error(self):
        from mcp_server.common.exceptions import MCPServerError, SageMakerError

        err = SageMakerError("training failed")
        assert isinstance(err, MCPServerError)

    def test_github_api_error(self):
        from mcp_server.common.exceptions import GitHubAPIError, MCPServerError

        err = GitHubAPIError("rate limited")
        assert isinstance(err, MCPServerError)

    def test_notification_error(self):
        from mcp_server.common.exceptions import MCPServerError, NotificationError

        err = NotificationError("send failed")
        assert isinstance(err, MCPServerError)

    def test_model_registry_error(self):
        from mcp_server.common.exceptions import MCPServerError, ModelRegistryError

        err = ModelRegistryError("not found")
        assert isinstance(err, MCPServerError)

    def test_gpu_out_of_memory_error(self):
        from mcp_server.common.exceptions import GPUOutOfMemoryError, MCPServerError

        err = GPUOutOfMemoryError("OOM")
        assert isinstance(err, MCPServerError)

    def test_spot_instance_interruption_error(self):
        from mcp_server.common.exceptions import (
            MCPServerError,
            SpotInstanceInterruptionError,
        )

        err = SpotInstanceInterruptionError("interrupted")
        assert isinstance(err, MCPServerError)

    def test_exception_hierarchy(self):
        """全例外がMCPServerError → Exceptionの階層を持つ"""
        from mcp_server.common.exceptions import (
            ConfigurationError,
            DataValidationError,
            GitHubAPIError,
            GPUOutOfMemoryError,
            MCPServerError,
            ModelRegistryError,
            NotificationError,
            S3Error,
            SageMakerError,
            SpotInstanceInterruptionError,
            ToolNotFoundError,
        )

        exception_classes = [
            ToolNotFoundError,
            ConfigurationError,
            DataValidationError,
            S3Error,
            SageMakerError,
            GitHubAPIError,
            NotificationError,
            ModelRegistryError,
            GPUOutOfMemoryError,
            SpotInstanceInterruptionError,
        ]
        for cls in exception_classes:
            assert issubclass(cls, MCPServerError)
            assert issubclass(cls, Exception)


# ===== common/logger.py =====


class TestLogger:
    """logger.py のテスト"""

    def test_setup_logger_returns_logger(self):
        from mcp_server.common.logger import setup_logger

        logger = setup_logger("test_logger_1")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger_1"

    def test_setup_logger_default_level(self):
        from mcp_server.common.logger import setup_logger

        logger = setup_logger("test_logger_2")
        assert logger.level == logging.INFO

    def test_setup_logger_custom_level(self):
        from mcp_server.common.logger import setup_logger

        logger = setup_logger("test_logger_3", level=logging.DEBUG)
        assert logger.level == logging.DEBUG

    def test_setup_logger_adds_handler(self):
        from mcp_server.common.logger import setup_logger

        name = "test_logger_handler_check"
        # 既存ハンドラーをクリア
        existing = logging.getLogger(name)
        existing.handlers.clear()

        logger = setup_logger(name)
        assert len(logger.handlers) >= 1
        assert isinstance(logger.handlers[0], logging.StreamHandler)

    def test_setup_logger_no_duplicate_handlers(self):
        from mcp_server.common.logger import setup_logger

        name = "test_logger_no_dup"
        existing = logging.getLogger(name)
        existing.handlers.clear()

        logger1 = setup_logger(name)
        handler_count = len(logger1.handlers)
        logger2 = setup_logger(name)
        assert len(logger2.handlers) == handler_count

    def test_get_logger_alias(self):
        from mcp_server.common.logger import get_logger, setup_logger

        assert get_logger is setup_logger


# ===== common/s3_utils.py =====


class TestS3Utils:
    """s3_utils.py のテスト"""

    def test_load_from_s3_not_implemented(self):
        from mcp_server.common.s3_utils import load_from_s3

        with pytest.raises(NotImplementedError, match="S3 load not implemented"):
            load_from_s3("bucket", "key")

    def test_save_to_s3_not_implemented(self):
        from mcp_server.common.s3_utils import save_to_s3

        with pytest.raises(NotImplementedError, match="S3 save not implemented"):
            save_to_s3("bucket", "key", {"data": 1})


# ===== common/metrics.py =====


class TestMetricsPublisher:
    """metrics.py のテスト"""

    def _create_publisher(self):
        from mcp_server.common.metrics import MetricsPublisher

        mock_config = MagicMock()
        mock_config.aws_region = "us-east-1"
        with patch("mcp_server.common.metrics.boto3") as mock_boto3:
            mock_client = MagicMock()
            mock_boto3.client.return_value = mock_client
            publisher = MetricsPublisher(mock_config)
        publisher.cloudwatch = mock_client
        return publisher, mock_client

    def test_init(self):
        publisher, _ = self._create_publisher()
        assert publisher.namespace == "MLOps/UnifiedMCPServer"

    def test_put_metric(self):
        publisher, mock_client = self._create_publisher()
        publisher.put_metric("TestMetric", 42.0, unit="Count")
        mock_client.put_metric_data.assert_called_once()
        call_kwargs = mock_client.put_metric_data.call_args
        assert call_kwargs.kwargs["Namespace"] == "MLOps/UnifiedMCPServer"

    def test_put_metric_with_dimensions(self):
        publisher, mock_client = self._create_publisher()
        dims = [{"Name": "Env", "Value": "test"}]
        publisher.put_metric("DimMetric", 1.0, dimensions=dims)
        call_kwargs = mock_client.put_metric_data.call_args
        metric_data = call_kwargs.kwargs["MetricData"][0]
        assert "Dimensions" in metric_data

    def test_put_metric_error_handling(self):
        publisher, mock_client = self._create_publisher()
        mock_client.put_metric_data.side_effect = Exception("API error")
        # エラーでも例外は投げない（ログのみ）
        publisher.put_metric("FailMetric", 0.0)

    def test_record_tool_execution(self):
        publisher, mock_client = self._create_publisher()
        publisher.record_tool_execution("test_tool", 150.0, True)
        mock_client.put_metric_data.assert_called_once()

    def test_record_training_job(self):
        publisher, mock_client = self._create_publisher()
        publisher.record_training_job("classification", 3600.0)
        mock_client.put_metric_data.assert_called_once()

    def test_record_model_evaluation(self):
        publisher, mock_client = self._create_publisher()
        publisher.record_model_evaluation("accuracy", 0.95, "classification")
        mock_client.put_metric_data.assert_called_once()


# ===== common/secrets.py =====


class TestSecretsManager:
    """secrets.py のテスト"""

    def _create_manager(self):
        from mcp_server.common.secrets import SecretsManager

        mock_config = MagicMock()
        mock_config.aws_region = "us-east-1"
        mock_config.secrets_prefix = "mlops/"
        with patch("mcp_server.common.secrets.boto3") as mock_boto3:
            mock_client = MagicMock()
            mock_boto3.client.return_value = mock_client
            manager = SecretsManager(mock_config)
        manager.client = mock_client
        # lru_cacheをクリア
        manager.get_secret.cache_clear()
        return manager, mock_client

    def test_get_secret_success(self):
        manager, mock_client = self._create_manager()
        mock_client.get_secret_value.return_value = {"SecretString": json.dumps({"key": "value"})}
        result = manager.get_secret("test")
        assert result == {"key": "value"}
        mock_client.get_secret_value.assert_called_once_with(SecretId="mlops/test")

    def test_get_secret_not_found(self):
        from botocore.exceptions import ClientError

        manager, mock_client = self._create_manager()
        mock_client.get_secret_value.side_effect = ClientError(
            {"Error": {"Code": "ResourceNotFoundException", "Message": "not found"}},
            "GetSecretValue",
        )
        with pytest.raises(ClientError):
            manager.get_secret("missing")

    def test_get_secret_invalid_request(self):
        from botocore.exceptions import ClientError

        manager, mock_client = self._create_manager()
        mock_client.get_secret_value.side_effect = ClientError(
            {"Error": {"Code": "InvalidRequestException", "Message": "bad request"}},
            "GetSecretValue",
        )
        with pytest.raises(ClientError):
            manager.get_secret("bad")

    def test_get_secret_invalid_parameter(self):
        from botocore.exceptions import ClientError

        manager, mock_client = self._create_manager()
        mock_client.get_secret_value.side_effect = ClientError(
            {"Error": {"Code": "InvalidParameterException", "Message": "bad param"}},
            "GetSecretValue",
        )
        with pytest.raises(ClientError):
            manager.get_secret("param_err")

    def test_get_secret_unknown_error(self):
        from botocore.exceptions import ClientError

        manager, mock_client = self._create_manager()
        mock_client.get_secret_value.side_effect = ClientError(
            {"Error": {"Code": "InternalServiceError", "Message": "internal"}},
            "GetSecretValue",
        )
        with pytest.raises(ClientError):
            manager.get_secret("internal")

    def test_get_github_token(self):
        manager, mock_client = self._create_manager()
        mock_client.get_secret_value.return_value = {
            "SecretString": json.dumps({"token": "ghp_xxx"})
        }
        token = manager.get_github_token()
        assert token == "ghp_xxx"

    def test_get_slack_webhook_url(self):
        manager, mock_client = self._create_manager()
        mock_client.get_secret_value.return_value = {
            "SecretString": json.dumps({"webhook_url": "https://hooks.slack.com/xxx"})
        }
        url = manager.get_slack_webhook_url()
        assert url == "https://hooks.slack.com/xxx"

    def test_get_email_credentials(self):
        manager, mock_client = self._create_manager()
        mock_client.get_secret_value.return_value = {
            "SecretString": json.dumps({"user": "admin", "pass": "secret"})
        }
        creds = manager.get_email_credentials()
        assert creds["user"] == "admin"


# ===== mcp_server/config.py =====


class TestMainConfig:
    """mcp_server/config.py のテスト"""

    def test_config_defaults(self):
        from mcp_server.config import Config

        config = Config(aws_region="us-east-1", s3_bucket="test-bucket")
        assert config.aws_region == "us-east-1"
        assert config.s3_bucket == "test-bucket"
        assert config.secrets_prefix == "mlops/"
        assert config.log_level == "INFO"
        assert config.cloudwatch_log_group is None
        assert config.cloudwatch_log_stream is None
        assert config.sagemaker_role_arn is None

    def test_config_custom_values(self):
        from mcp_server.config import Config

        config = Config(
            aws_region="ap-northeast-1",
            s3_bucket="custom",
            secrets_prefix="custom/",
            log_level="DEBUG",
            cloudwatch_log_group="/mlops/logs",
            cloudwatch_log_stream="stream-1",
            sagemaker_role_arn="arn:aws:iam::role/SageMaker",
        )
        assert config.log_level == "DEBUG"
        assert config.cloudwatch_log_group == "/mlops/logs"

    def test_config_from_env(self):
        from mcp_server.config import Config

        with patch.dict(
            os.environ,
            {
                "AWS_REGION": "eu-west-1",
                "MLOPS_S3_BUCKET": "env-bucket",
                "MLOPS_SECRETS_PREFIX": "prod/",
                "LOG_LEVEL": "WARNING",
            },
        ):
            config = Config.from_env()
            assert config.aws_region == "eu-west-1"
            assert config.s3_bucket == "env-bucket"
            assert config.secrets_prefix == "prod/"
            assert config.log_level == "WARNING"

    def test_config_from_env_missing_required(self):
        from mcp_server.config import Config

        with patch.dict(os.environ, {}, clear=True):
            # MLOPS_S3_BUCKET は必須
            with pytest.raises(KeyError):
                Config.from_env()


# ===== mcp_server/router.py =====

# router.pyはmcpパッケージに依存するため、インストールされていない場合はスキップ
try:
    from mcp_server.router import ToolRouter  # noqa: F401

    HAS_MCP = True
except ImportError:
    HAS_MCP = False


@pytest.mark.skipif(not HAS_MCP, reason="mcp package not installed")
class TestToolRouter:
    """router.py のテスト"""

    def test_build_tool_mapping(self):
        mock_tool_1 = MagicMock()
        mock_tool_1.name = "tool_a"
        mock_tool_2 = MagicMock()
        mock_tool_2.name = "tool_b"

        mock_cap_1 = MagicMock()
        mock_cap_1.list_tools.return_value = [mock_tool_1]
        mock_cap_2 = MagicMock()
        mock_cap_2.list_tools.return_value = [mock_tool_2]

        router = ToolRouter({"cap1": mock_cap_1, "cap2": mock_cap_2})
        assert router._tool_mapping == {"tool_a": "cap1", "tool_b": "cap2"}

    def test_tool_name_collision(self):
        mock_tool = MagicMock()
        mock_tool.name = "duplicate_tool"

        mock_cap_1 = MagicMock()
        mock_cap_1.list_tools.return_value = [mock_tool]
        mock_cap_2 = MagicMock()
        mock_cap_2.list_tools.return_value = [mock_tool]

        with pytest.raises(ValueError, match="Tool name collision"):
            ToolRouter({"cap1": mock_cap_1, "cap2": mock_cap_2})

    @pytest.mark.asyncio
    async def test_route_tool_call_success(self):
        mock_tool = MagicMock()
        mock_tool.name = "test_tool"

        mock_cap = MagicMock()
        mock_cap.list_tools.return_value = [mock_tool]
        mock_cap.execute_tool = AsyncMock(return_value=[{"result": "ok"}])

        router = ToolRouter({"test_cap": mock_cap})
        result = await router.route_tool_call("test_tool", {"arg": "val"})
        assert result == [{"result": "ok"}]
        mock_cap.execute_tool.assert_called_once_with("test_tool", {"arg": "val"})

    @pytest.mark.asyncio
    async def test_route_tool_call_not_found(self):
        from mcp_server.common.exceptions import ToolNotFoundError

        mock_cap = MagicMock()
        mock_cap.list_tools.return_value = []

        router = ToolRouter({"empty": mock_cap})
        with pytest.raises(ToolNotFoundError, match="Tool not found"):
            await router.route_tool_call("nonexistent", {})

    def test_empty_capabilities(self):
        router = ToolRouter({})
        assert router._tool_mapping == {}
