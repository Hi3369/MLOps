"""ツールルーティング機構"""
from typing import Any

from mcp.types import EmbeddedResource, ImageContent, TextContent

from .common.exceptions import ToolNotFoundError
from .common.logger import get_logger

logger = get_logger(__name__)


class ToolRouter:
    """ツールを適切なCapabilityにルーティング"""

    def __init__(self, capabilities: dict):
        self.capabilities = capabilities
        self._tool_mapping = self._build_tool_mapping()

    def _build_tool_mapping(self) -> dict[str, str]:
        """ツール名 → Capability名のマッピングを構築"""
        mapping = {}

        for capability_name, capability in self.capabilities.items():
            for tool in capability.list_tools():
                if tool.name in mapping:
                    raise ValueError(
                        f"Tool name collision: {tool.name} is defined in multiple capabilities"
                    )
                mapping[tool.name] = capability_name

        logger.info(f"Built tool mapping: {len(mapping)} tools")
        return mapping

    async def route_tool_call(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> list[TextContent | ImageContent | EmbeddedResource]:
        """ツール呼び出しを適切なCapabilityにルーティング"""

        # ツール名からCapabilityを特定
        capability_name = self._tool_mapping.get(tool_name)

        if not capability_name:
            raise ToolNotFoundError(f"Tool not found: {tool_name}")

        # Capabilityを取得
        capability = self.capabilities[capability_name]

        # ツールを実行
        logger.debug(f"Routing {tool_name} to {capability_name}")
        return await capability.execute_tool(tool_name, arguments)
