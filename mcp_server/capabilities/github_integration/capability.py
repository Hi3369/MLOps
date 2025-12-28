"""GitHub Integration Capability実装"""
from typing import Any, List

from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

from ..base import BaseCapability


class GitHubIntegrationCapability(BaseCapability):
    """GitHub統合・Issue管理"""

    def list_tools(self) -> List[Tool]:
        """提供ツール一覧"""
        return [
            Tool(
                name="create_issue_comment",
                description="GitHub Issueにコメントを作成",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "repo_owner": {"type": "string"},
                        "repo_name": {"type": "string"},
                        "issue_number": {"type": "integer"},
                        "comment_body": {"type": "string"},
                    },
                    "required": ["repo_owner", "repo_name", "issue_number", "comment_body"],
                },
            ),
            Tool(
                name="update_issue_labels",
                description="GitHub Issueのラベルを更新",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "repo_owner": {"type": "string"},
                        "repo_name": {"type": "string"},
                        "issue_number": {"type": "integer"},
                        "labels": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["repo_owner", "repo_name", "issue_number", "labels"],
                },
            ),
            Tool(
                name="create_training_history_file",
                description="学習履歴ファイルをリポジトリに作成",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "repo_owner": {"type": "string"},
                        "repo_name": {"type": "string"},
                        "training_results": {"type": "object"},
                    },
                    "required": ["repo_owner", "repo_name", "training_results"],
                },
            ),
        ]

    async def execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any]
    ) -> List[TextContent | ImageContent | EmbeddedResource]:
        """ツール実行"""
        # TODO: 実装
        return [
            TextContent(
                type="text",
                text=f"GitHub Integration tool '{tool_name}' executed (stub implementation)"
            )
        ]
