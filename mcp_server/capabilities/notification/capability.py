"""Notification Capability実装"""
from typing import Any, List

from mcp.types import EmbeddedResource, ImageContent, TextContent, Tool

from ..base import BaseCapability


class NotificationCapability(BaseCapability):
    """外部通知チャネル（Slack, Email, Teams, Discord）"""

    def list_tools(self) -> List[Tool]:
        """提供ツール一覧"""
        return [
            Tool(
                name="send_slack_notification",
                description="Slackに通知を送信",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message": {"type": "string"},
                        "channel": {
                            "type": "string",
                            "default": "#mlops-notifications",
                        },
                        "username": {"type": "string", "default": "MLOps Bot"},
                    },
                    "required": ["message"],
                },
            ),
            Tool(
                name="send_email_notification",
                description="メールで通知を送信",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "to_addresses": {"type": "array", "items": {"type": "string"}},
                        "subject": {"type": "string"},
                        "body": {"type": "string"},
                    },
                    "required": ["to_addresses", "subject", "body"],
                },
            ),
            Tool(
                name="send_teams_notification",
                description="Microsoft Teamsに通知を送信",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message": {"type": "string"},
                    },
                    "required": ["message"],
                },
            ),
            Tool(
                name="send_discord_notification",
                description="Discordに通知を送信",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message": {"type": "string"},
                    },
                    "required": ["message"],
                },
            ),
        ]

    async def execute_tool(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> List[TextContent | ImageContent | EmbeddedResource]:
        """ツール実行"""
        # TODO: 実装
        return [
            TextContent(
                type="text",
                text=f"Notification tool '{tool_name}' executed (stub implementation)",
            )
        ]
