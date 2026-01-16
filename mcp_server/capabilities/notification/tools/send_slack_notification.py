"""
Send Slack Notification Tool

Slack通知送信ツール
"""

import json
import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def send_slack_notification(
    message: str,
    channel: str = "#mlops-notifications",
    username: str = "MLOps Bot",
    icon_emoji: str = ":robot_face:",
    attachments: Optional[list] = None,
    blocks: Optional[list] = None,
) -> Dict[str, Any]:
    """
    Slackに通知を送信

    Args:
        message: 通知メッセージ
        channel: 送信先チャンネル
        username: 表示名
        icon_emoji: アイコン絵文字
        attachments: Slack attachments（リッチメッセージ用）
        blocks: Slack blocks（Block Kit用）

    Returns:
        送信結果辞書
    """
    logger.info(f"Sending Slack notification to {channel}")

    # パラメータ検証
    if not message:
        raise ValueError("message must not be empty")

    if not channel:
        raise ValueError("channel must not be empty")

    try:
        # 環境変数からWebhook URLを取得
        webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
        env = os.environ.get("MLOPS_ENV", "development")

        # 開発/テスト環境ではモックデータを返す
        if env in ["development", "test"] or not webhook_url:
            logger.info("Using mock Slack notification (dev/test environment)")
            return _mock_slack_notification(
                message=message,
                channel=channel,
                username=username,
                icon_emoji=icon_emoji,
                attachments=attachments,
                blocks=blocks,
            )

        # 本番環境：実際にSlack APIを呼び出す
        return _send_real_slack_notification(
            webhook_url=webhook_url,
            message=message,
            channel=channel,
            username=username,
            icon_emoji=icon_emoji,
            attachments=attachments,
            blocks=blocks,
        )

    except Exception as e:
        logger.error(f"Slack notification error: {e}")
        raise ValueError(f"Failed to send Slack notification: {e}")


def _mock_slack_notification(
    message: str,
    channel: str,
    username: str,
    icon_emoji: str,
    attachments: Optional[list],
    blocks: Optional[list],
) -> Dict[str, Any]:
    """モックSlack通知"""
    import uuid
    from datetime import datetime

    message_id = str(uuid.uuid4())[:8]

    return {
        "status": "success",
        "message": "Slack notification sent (mock)",
        "notification_result": {
            "message_id": f"mock-slack-{message_id}",
            "channel": channel,
            "username": username,
            "icon_emoji": icon_emoji,
            "message_preview": message[:100] + "..." if len(message) > 100 else message,
            "has_attachments": attachments is not None and len(attachments) > 0,
            "has_blocks": blocks is not None and len(blocks) > 0,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "mock": True,
        },
    }


def _send_real_slack_notification(
    webhook_url: str,
    message: str,
    channel: str,
    username: str,
    icon_emoji: str,
    attachments: Optional[list],
    blocks: Optional[list],
) -> Dict[str, Any]:
    """実際のSlack通知送信"""
    import urllib.request
    import uuid
    from datetime import datetime

    # ペイロード構築
    payload = {
        "text": message,
        "channel": channel,
        "username": username,
        "icon_emoji": icon_emoji,
    }

    if attachments:
        payload["attachments"] = attachments

    if blocks:
        payload["blocks"] = blocks

    # リクエスト送信
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            response_body = response.read().decode("utf-8")

            if response.status == 200:
                message_id = str(uuid.uuid4())[:8]
                return {
                    "status": "success",
                    "message": "Slack notification sent successfully",
                    "notification_result": {
                        "message_id": f"slack-{message_id}",
                        "channel": channel,
                        "username": username,
                        "message_preview": (
                            message[:100] + "..." if len(message) > 100 else message
                        ),
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "response": response_body,
                    },
                }
            else:
                raise ValueError(f"Slack API returned status {response.status}")

    except urllib.error.URLError as e:
        raise ValueError(f"Failed to connect to Slack: {e}")
