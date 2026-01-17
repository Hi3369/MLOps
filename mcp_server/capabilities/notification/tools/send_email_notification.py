"""
Send Email Notification Tool

Email通知送信ツール（AWS SES使用）
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


def send_email_notification(
    to_addresses: List[str],
    subject: str,
    body: str,
    from_address: Optional[str] = None,
    cc_addresses: Optional[List[str]] = None,
    bcc_addresses: Optional[List[str]] = None,
    html_body: Optional[str] = None,
    reply_to: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Email通知を送信（AWS SES使用）

    Args:
        to_addresses: 宛先メールアドレスリスト
        subject: 件名
        body: 本文（プレーンテキスト）
        from_address: 送信元アドレス（省略時は環境変数から取得）
        cc_addresses: CCアドレスリスト
        bcc_addresses: BCCアドレスリスト
        html_body: HTML本文（オプション）
        reply_to: Reply-Toアドレスリスト

    Returns:
        送信結果辞書
    """
    logger.info(f"Sending email notification to {len(to_addresses)} recipients")

    # パラメータ検証
    if not to_addresses:
        raise ValueError("to_addresses must not be empty")

    if not isinstance(to_addresses, list):
        raise ValueError("to_addresses must be a list")

    if not subject:
        raise ValueError("subject must not be empty")

    if not body:
        raise ValueError("body must not be empty")

    # メールアドレス形式の簡易検証
    all_addresses = to_addresses + (cc_addresses or []) + (bcc_addresses or [])
    for addr in all_addresses:
        if "@" not in addr:
            raise ValueError(f"Invalid email address: {addr}")

    try:
        env = os.environ.get("MLOPS_ENV", "development")
        sender = from_address or os.environ.get("SES_FROM_ADDRESS", "mlops@example.com")

        # 開発/テスト環境ではモックデータを返す
        if env in ["development", "test"]:
            logger.info("Using mock email notification (dev/test environment)")
            return _mock_email_notification(
                to_addresses=to_addresses,
                subject=subject,
                body=body,
                from_address=sender,
                cc_addresses=cc_addresses,
                bcc_addresses=bcc_addresses,
                html_body=html_body,
            )

        # 本番環境：AWS SESを使用
        return _send_real_email_notification(
            to_addresses=to_addresses,
            subject=subject,
            body=body,
            from_address=sender,
            cc_addresses=cc_addresses,
            bcc_addresses=bcc_addresses,
            html_body=html_body,
            reply_to=reply_to,
        )

    except Exception as e:
        logger.error(f"Email notification error: {e}")
        raise ValueError(f"Failed to send email notification: {e}")


def _mock_email_notification(
    to_addresses: List[str],
    subject: str,
    body: str,
    from_address: str,
    cc_addresses: Optional[List[str]],
    bcc_addresses: Optional[List[str]],
    html_body: Optional[str],
) -> Dict[str, Any]:
    """モックEmail通知"""
    message_id = str(uuid4())

    return {
        "status": "success",
        "message": "Email notification sent (mock)",
        "notification_result": {
            "message_id": f"mock-email-{message_id}",
            "from_address": from_address,
            "to_addresses": to_addresses,
            "cc_addresses": cc_addresses or [],
            "bcc_addresses": bcc_addresses or [],
            "subject": subject,
            "body_preview": body[:100] + "..." if len(body) > 100 else body,
            "has_html_body": html_body is not None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mock": True,
        },
    }


def _send_real_email_notification(
    to_addresses: List[str],
    subject: str,
    body: str,
    from_address: str,
    cc_addresses: Optional[List[str]],
    bcc_addresses: Optional[List[str]],
    html_body: Optional[str],
    reply_to: Optional[List[str]],
) -> Dict[str, Any]:
    """AWS SESを使用した実際のEmail送信"""
    import boto3

    ses_client = boto3.client("ses")

    # 宛先設定
    destination = {"ToAddresses": to_addresses}
    if cc_addresses:
        destination["CcAddresses"] = cc_addresses
    if bcc_addresses:
        destination["BccAddresses"] = bcc_addresses

    # メッセージ設定
    message_body = {"Text": {"Data": body, "Charset": "UTF-8"}}
    if html_body:
        message_body["Html"] = {"Data": html_body, "Charset": "UTF-8"}

    message = {
        "Subject": {"Data": subject, "Charset": "UTF-8"},
        "Body": message_body,
    }

    # 送信パラメータ
    send_params = {
        "Source": from_address,
        "Destination": destination,
        "Message": message,
    }

    if reply_to:
        send_params["ReplyToAddresses"] = reply_to

    # SES API呼び出し
    response = ses_client.send_email(**send_params)

    return {
        "status": "success",
        "message": "Email notification sent successfully",
        "notification_result": {
            "message_id": response["MessageId"],
            "from_address": from_address,
            "to_addresses": to_addresses,
            "cc_addresses": cc_addresses or [],
            "subject": subject,
            "body_preview": body[:100] + "..." if len(body) > 100 else body,
            "has_html_body": html_body is not None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": response.get("ResponseMetadata", {}).get("RequestId"),
        },
    }
