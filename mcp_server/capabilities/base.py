"""基底Capabilityクラス"""
from abc import ABC, abstractmethod
from typing import Any, List

from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource


class BaseCapability(ABC):
    """すべてのCapabilityの基底クラス"""

    def __init__(self, config):
        """
        Args:
            config: 設定オブジェクト
        """
        self.config = config

    @abstractmethod
    def list_tools(self) -> List[Tool]:
        """
        このCapabilityが提供するツールの一覧を返す

        Returns:
            ツール定義のリスト
        """
        pass

    @abstractmethod
    async def execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any]
    ) -> List[TextContent | ImageContent | EmbeddedResource]:
        """
        ツールを実行

        Args:
            tool_name: ツール名
            arguments: ツール引数

        Returns:
            実行結果（TextContent, ImageContent, EmbeddedResourceのリスト）
        """
        pass
