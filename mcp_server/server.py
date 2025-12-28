"""統合MLOps MCPサーバーのメイン実装"""
import asyncio
from typing import Any

from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

from .config import Config
from .router import ToolRouter
from .common.logger import get_logger
from .common.exceptions import MCPServerError

logger = get_logger(__name__)


class UnifiedMLOpsMCPServer:
    """統合MLOps MCPサーバー"""

    def __init__(self, config: Config):
        self.config = config
        self.server = Server("unified-mlops-mcp-server")

        # Capabilityの初期化（遅延インポート）
        self.capabilities = self._initialize_capabilities()

        # ツールルーター初期化
        self.router = ToolRouter(self.capabilities)

        # MCPハンドラー登録
        self._register_handlers()

        logger.info("Unified MLOps MCP Server initialized")

    def _initialize_capabilities(self) -> dict:
        """Capabilityを初期化"""
        # 遅延インポートで循環参照を回避
        from .capabilities.data_preparation.capability import DataPreparationCapability
        from .capabilities.ml_training.capability import MLTrainingCapability
        from .capabilities.ml_evaluation.capability import MLEvaluationCapability
        from .capabilities.github_integration.capability import GitHubIntegrationCapability
        from .capabilities.model_registry.capability import ModelRegistryCapability
        from .capabilities.notification.capability import NotificationCapability

        return {
            "data_preparation": DataPreparationCapability(self.config),
            "ml_training": MLTrainingCapability(self.config),
            "ml_evaluation": MLEvaluationCapability(self.config),
            "github_integration": GitHubIntegrationCapability(self.config),
            "model_registry": ModelRegistryCapability(self.config),
            "notification": NotificationCapability(self.config),
        }

    def _register_handlers(self):
        """MCPハンドラーを登録"""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """全Capabilityのツール一覧を返す"""
            tools = []
            for capability in self.capabilities.values():
                tools.extend(capability.list_tools())
            logger.info(f"Listed {len(tools)} tools")
            return tools

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent | ImageContent | EmbeddedResource]:
            """ツールを実行（適切なCapabilityにルーティング）"""
            try:
                logger.info(f"Tool call: {name}", extra={
                    "tool_name": name,
                    "arguments": self._mask_secrets(arguments),
                })

                # ツールルーターで適切なCapabilityに振り分け
                result = await self.router.route_tool_call(name, arguments)

                logger.info(f"Tool call succeeded: {name}")
                return result

            except Exception as e:
                logger.error(f"Tool call failed: {name}", exc_info=True)
                raise MCPServerError(f"Tool execution failed: {name}") from e

    def _mask_secrets(self, arguments: dict) -> dict:
        """引数内のシークレットをマスク"""
        masked = arguments.copy()
        secret_keys = ["token", "password", "secret", "key", "credential"]

        for key in masked:
            if any(secret in key.lower() for secret in secret_keys):
                masked[key] = "***masked***"

        return masked

    async def run(self):
        """サーバーを起動"""
        from mcp.server.stdio import stdio_server

        logger.info("Starting Unified MLOps MCP Server")
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )
