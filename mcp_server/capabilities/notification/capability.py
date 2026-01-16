"""
Notification Capability

通知機能のCapability実装
Slack、Email、GitHub通知およびテンプレート管理を提供
"""

import logging
from typing import Any, Callable, Dict

from .tools import (
    apply_notification_template,
    send_email_notification,
    send_github_notification,
    send_slack_notification,
)

logger = logging.getLogger(__name__)


class NotificationCapability:
    """
    通知機能Capability

    以下のツールを提供:
    - send_slack_notification: Slack通知送信
    - send_email_notification: Email通知送信（AWS SES）
    - send_github_notification: GitHub Issue/PRコメント
    - apply_notification_template: 通知テンプレート適用
    """

    def __init__(self):
        """Capabilityの初期化"""
        self._tools: Dict[str, Callable] = {
            "send_slack_notification": send_slack_notification,
            "send_email_notification": send_email_notification,
            "send_github_notification": send_github_notification,
            "apply_notification_template": apply_notification_template,
        }

        self._tool_schemas: Dict[str, Dict[str, Any]] = {
            "send_slack_notification": {
                "name": "send_slack_notification",
                "description": "Slackに通知を送信します",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "通知メッセージ",
                        },
                        "channel": {
                            "type": "string",
                            "description": "送信先チャンネル",
                            "default": "#mlops-notifications",
                        },
                        "username": {
                            "type": "string",
                            "description": "表示名",
                            "default": "MLOps Bot",
                        },
                        "icon_emoji": {
                            "type": "string",
                            "description": "アイコン絵文字",
                            "default": ":robot_face:",
                        },
                        "attachments": {
                            "type": "array",
                            "description": "Slack attachments（リッチメッセージ用）",
                        },
                        "blocks": {
                            "type": "array",
                            "description": "Slack blocks（Block Kit用）",
                        },
                    },
                    "required": ["message"],
                },
            },
            "send_email_notification": {
                "name": "send_email_notification",
                "description": "Email通知を送信します（AWS SES使用）",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "to_addresses": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "宛先メールアドレスリスト",
                        },
                        "subject": {
                            "type": "string",
                            "description": "件名",
                        },
                        "body": {
                            "type": "string",
                            "description": "本文（プレーンテキスト）",
                        },
                        "from_address": {
                            "type": "string",
                            "description": "送信元アドレス（省略時は環境変数から取得）",
                        },
                        "cc_addresses": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "CCアドレスリスト",
                        },
                        "bcc_addresses": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "BCCアドレスリスト",
                        },
                        "html_body": {
                            "type": "string",
                            "description": "HTML本文（オプション）",
                        },
                        "reply_to": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Reply-Toアドレスリスト",
                        },
                    },
                    "required": ["to_addresses", "subject", "body"],
                },
            },
            "send_github_notification": {
                "name": "send_github_notification",
                "description": "GitHub Issue/PRに通知（コメント）を送信します",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "repo_owner": {
                            "type": "string",
                            "description": "リポジトリオーナー",
                        },
                        "repo_name": {
                            "type": "string",
                            "description": "リポジトリ名",
                        },
                        "notification_type": {
                            "type": "string",
                            "enum": ["issue_comment", "pr_comment", "issue_create"],
                            "description": "通知タイプ",
                        },
                        "target_number": {
                            "type": "integer",
                            "description": "Issue/PR番号（issue_createの場合は0）",
                        },
                        "message": {
                            "type": "string",
                            "description": "通知メッセージ",
                        },
                        "labels": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "ラベルリスト（issue_createの場合）",
                        },
                        "assignees": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "アサイニーリスト（issue_createの場合）",
                        },
                    },
                    "required": [
                        "repo_owner",
                        "repo_name",
                        "notification_type",
                        "target_number",
                        "message",
                    ],
                },
            },
            "apply_notification_template": {
                "name": "apply_notification_template",
                "description": "通知テンプレートを適用します",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "template_name": {
                            "type": "string",
                            "description": "テンプレート名（training_started, training_completed, training_failed, deployment_started, deployment_completed, drift_detected, alert_triggered）",
                        },
                        "variables": {
                            "type": "object",
                            "description": "テンプレート変数",
                        },
                        "custom_template": {
                            "type": "object",
                            "description": "カスタムテンプレート（subject, body, slack_blocksを含む辞書）",
                        },
                        "output_format": {
                            "type": "string",
                            "enum": ["all", "email", "slack", "github"],
                            "description": "出力フォーマット",
                            "default": "all",
                        },
                    },
                    "required": ["template_name", "variables"],
                },
            },
        }

        logger.info("NotificationCapability initialized with 4 tools")

    def get_tools(self) -> Dict[str, Callable]:
        """
        ツール関数のマッピングを返す

        Returns:
            ツール名から関数へのマッピング辞書
        """
        return self._tools

    def get_tool_schemas(self) -> Dict[str, Dict[str, Any]]:
        """
        ツールスキーマのマッピングを返す

        Returns:
            ツール名からスキーマ辞書へのマッピング
        """
        return self._tool_schemas
