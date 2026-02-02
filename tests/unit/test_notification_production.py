"""
Notification Capability 本番パステスト

本番環境（MLOPS_ENV=production）でのSlack/GitHub/Email通知の
実送信パスをモックを使ってテスト
"""

import json
import os
import urllib.error
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

# ===== Slack 本番パス =====


class TestSlackProductionPath:
    """send_slack_notification の本番パステスト"""

    @patch.dict(
        os.environ,
        {"MLOPS_ENV": "production", "SLACK_WEBHOOK_URL": "https://hooks.slack.com/test"},
    )
    @patch("urllib.request.urlopen")
    def test_send_real_slack_success(self, mock_urlopen):
        from mcp_server.capabilities.notification.tools.send_slack_notification import (
            send_slack_notification,
        )

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b"ok"
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = send_slack_notification(message="Hello", channel="#test")
        assert result["status"] == "success"
        assert "notification_result" in result
        assert result["notification_result"]["channel"] == "#test"
        assert "response" in result["notification_result"]

    @patch.dict(
        os.environ,
        {"MLOPS_ENV": "production", "SLACK_WEBHOOK_URL": "https://hooks.slack.com/test"},
    )
    @patch("urllib.request.urlopen")
    def test_send_real_slack_with_attachments(self, mock_urlopen):
        from mcp_server.capabilities.notification.tools.send_slack_notification import (
            send_slack_notification,
        )

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b"ok"
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = send_slack_notification(
            message="With attachments",
            channel="#test",
            attachments=[{"text": "detail"}],
        )
        assert result["status"] == "success"

    @patch.dict(
        os.environ,
        {"MLOPS_ENV": "production", "SLACK_WEBHOOK_URL": "https://hooks.slack.com/test"},
    )
    @patch("urllib.request.urlopen")
    def test_send_real_slack_with_blocks(self, mock_urlopen):
        from mcp_server.capabilities.notification.tools.send_slack_notification import (
            send_slack_notification,
        )

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b"ok"
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = send_slack_notification(
            message="With blocks",
            channel="#test",
            blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": "block"}}],
        )
        assert result["status"] == "success"

    @patch.dict(
        os.environ,
        {"MLOPS_ENV": "production", "SLACK_WEBHOOK_URL": "http://insecure.example.com"},
    )
    def test_send_real_slack_non_https_rejected(self):
        from mcp_server.capabilities.notification.tools.send_slack_notification import (
            send_slack_notification,
        )

        with pytest.raises(ValueError, match="Webhook URL must use HTTPS"):
            send_slack_notification(message="bad url", channel="#test")

    @patch.dict(
        os.environ,
        {"MLOPS_ENV": "production", "SLACK_WEBHOOK_URL": "https://hooks.slack.com/test"},
    )
    @patch("urllib.request.urlopen")
    def test_send_real_slack_url_error(self, mock_urlopen):
        from mcp_server.capabilities.notification.tools.send_slack_notification import (
            send_slack_notification,
        )

        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
        with pytest.raises(ValueError, match="Failed to send Slack notification"):
            send_slack_notification(message="fail", channel="#test")

    @patch.dict(
        os.environ,
        {"MLOPS_ENV": "production", "SLACK_WEBHOOK_URL": "https://hooks.slack.com/test"},
    )
    @patch("urllib.request.urlopen")
    def test_send_real_slack_non_200(self, mock_urlopen):
        from mcp_server.capabilities.notification.tools.send_slack_notification import (
            send_slack_notification,
        )

        mock_response = MagicMock()
        mock_response.status = 500
        mock_response.read.return_value = b"error"
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        with pytest.raises(ValueError, match="Slack API returned status"):
            send_slack_notification(message="500", channel="#test")

    @patch.dict(
        os.environ,
        {"MLOPS_ENV": "production", "SLACK_WEBHOOK_URL": "https://hooks.slack.com/test"},
    )
    @patch("urllib.request.urlopen")
    def test_send_real_slack_long_message_preview(self, mock_urlopen):
        from mcp_server.capabilities.notification.tools.send_slack_notification import (
            send_slack_notification,
        )

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b"ok"
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        long_msg = "a" * 200
        result = send_slack_notification(message=long_msg, channel="#test")
        preview = result["notification_result"]["message_preview"]
        assert preview.endswith("...")
        assert len(preview) == 103  # 100 + "..."


# ===== GitHub 本番パス =====


class TestGitHubProductionPath:
    """send_github_notification の本番パステスト"""

    @patch.dict(os.environ, {"MLOPS_ENV": "production", "GITHUB_TOKEN": "ghp_testtoken123"})
    @patch("urllib.request.urlopen")
    def test_send_real_github_issue_comment(self, mock_urlopen):
        from mcp_server.capabilities.notification.tools.send_github_notification import (
            send_github_notification,
        )

        response_data = json.dumps(
            {"id": 12345, "html_url": "https://github.com/o/r/issues/1#issuecomment-12345"}
        ).encode("utf-8")
        mock_response = MagicMock()
        mock_response.status = 201
        mock_response.read.return_value = response_data
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = send_github_notification(
            repo_owner="owner",
            repo_name="repo",
            message="Test comment",
            notification_type="issue_comment",
            target_number=1,
        )
        assert result["status"] == "success"
        assert result["notification_result"]["comment_id"] == 12345

    @patch.dict(os.environ, {"MLOPS_ENV": "production", "GITHUB_TOKEN": "ghp_testtoken123"})
    @patch("urllib.request.urlopen")
    def test_send_real_github_issue_create(self, mock_urlopen):
        from mcp_server.capabilities.notification.tools.send_github_notification import (
            send_github_notification,
        )

        response_data = json.dumps(
            {"number": 42, "html_url": "https://github.com/o/r/issues/42"}
        ).encode("utf-8")
        mock_response = MagicMock()
        mock_response.status = 201
        mock_response.read.return_value = response_data
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = send_github_notification(
            repo_owner="owner",
            repo_name="repo",
            message="Title\nBody content",
            notification_type="issue_create",
            target_number=0,
        )
        assert result["status"] == "success"
        assert result["notification_result"]["issue_number"] == 42

    @patch.dict(os.environ, {"MLOPS_ENV": "production", "GITHUB_TOKEN": "ghp_testtoken123"})
    @patch("urllib.request.urlopen")
    def test_send_real_github_http_error(self, mock_urlopen):
        from mcp_server.capabilities.notification.tools.send_github_notification import (
            send_github_notification,
        )

        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://api.github.com",
            code=403,
            msg="Forbidden",
            hdrs={},
            fp=BytesIO(b'{"message": "rate limit exceeded"}'),
        )
        with pytest.raises(ValueError, match="Failed to send GitHub notification"):
            send_github_notification(
                repo_owner="owner",
                repo_name="repo",
                message="Error test",
                notification_type="issue_comment",
                target_number=1,
            )

    @patch.dict(os.environ, {"MLOPS_ENV": "production", "GITHUB_TOKEN": "ghp_testtoken123"})
    @patch("urllib.request.urlopen")
    def test_send_real_github_url_error(self, mock_urlopen):
        from mcp_server.capabilities.notification.tools.send_github_notification import (
            send_github_notification,
        )

        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
        with pytest.raises(ValueError, match="Failed to send GitHub notification"):
            send_github_notification(
                repo_owner="owner",
                repo_name="repo",
                message="URL error",
                notification_type="issue_comment",
                target_number=1,
            )

    @patch.dict(os.environ, {"MLOPS_ENV": "production", "GITHUB_TOKEN": "ghp_testtoken123"})
    @patch("urllib.request.urlopen")
    def test_send_real_github_issue_create_with_labels(self, mock_urlopen):
        from mcp_server.capabilities.notification.tools.send_github_notification import (
            send_github_notification,
        )

        response_data = json.dumps(
            {"number": 99, "html_url": "https://github.com/o/r/issues/99"}
        ).encode("utf-8")
        mock_response = MagicMock()
        mock_response.status = 201
        mock_response.read.return_value = response_data
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = send_github_notification(
            repo_owner="owner",
            repo_name="repo",
            message="Bug report",
            notification_type="issue_create",
            target_number=0,
            labels=["bug", "urgent"],
            assignees=["dev1"],
        )
        assert result["status"] == "success"


# ===== Email 本番パス =====


class TestEmailProductionPath:
    """send_email_notification の本番パステスト"""

    @patch.dict(os.environ, {"MLOPS_ENV": "production"})
    @patch("boto3.client")
    def test_send_real_email_success(self, mock_boto3_client):
        from mcp_server.capabilities.notification.tools.send_email_notification import (
            send_email_notification,
        )

        mock_ses = MagicMock()
        mock_boto3_client.return_value = mock_ses
        mock_ses.send_email.return_value = {
            "MessageId": "ses-msg-123",
            "ResponseMetadata": {"RequestId": "req-456", "HTTPStatusCode": 200},
        }

        result = send_email_notification(
            to_addresses=["user@example.com"],
            subject="Test Subject",
            body="Test body",
        )
        assert result["status"] == "success"
        assert result["notification_result"]["message_id"] == "ses-msg-123"
        mock_ses.send_email.assert_called_once()

    @patch.dict(os.environ, {"MLOPS_ENV": "production"})
    @patch("boto3.client")
    def test_send_real_email_with_cc_bcc(self, mock_boto3_client):
        from mcp_server.capabilities.notification.tools.send_email_notification import (
            send_email_notification,
        )

        mock_ses = MagicMock()
        mock_boto3_client.return_value = mock_ses
        mock_ses.send_email.return_value = {
            "MessageId": "ses-msg-789",
            "ResponseMetadata": {"RequestId": "req-101", "HTTPStatusCode": 200},
        }

        result = send_email_notification(
            to_addresses=["user@example.com"],
            subject="CC Test",
            body="Body",
            cc_addresses=["cc@example.com"],
            bcc_addresses=["bcc@example.com"],
        )
        assert result["status"] == "success"

    @patch.dict(os.environ, {"MLOPS_ENV": "production"})
    @patch("boto3.client")
    def test_send_real_email_with_html(self, mock_boto3_client):
        from mcp_server.capabilities.notification.tools.send_email_notification import (
            send_email_notification,
        )

        mock_ses = MagicMock()
        mock_boto3_client.return_value = mock_ses
        mock_ses.send_email.return_value = {
            "MessageId": "ses-html-1",
            "ResponseMetadata": {"RequestId": "req-html", "HTTPStatusCode": 200},
        }

        result = send_email_notification(
            to_addresses=["user@example.com"],
            subject="HTML",
            body="text body",
            html_body="<h1>HTML</h1>",
        )
        assert result["status"] == "success"

    @patch.dict(os.environ, {"MLOPS_ENV": "production"})
    @patch("boto3.client")
    def test_send_real_email_with_reply_to(self, mock_boto3_client):
        from mcp_server.capabilities.notification.tools.send_email_notification import (
            send_email_notification,
        )

        mock_ses = MagicMock()
        mock_boto3_client.return_value = mock_ses
        mock_ses.send_email.return_value = {
            "MessageId": "ses-reply-1",
            "ResponseMetadata": {"RequestId": "req-reply", "HTTPStatusCode": 200},
        }

        result = send_email_notification(
            to_addresses=["user@example.com"],
            subject="Reply",
            body="body",
            reply_to=["reply@example.com"],
        )
        assert result["status"] == "success"

    @patch.dict(os.environ, {"MLOPS_ENV": "production"})
    @patch("boto3.client")
    def test_send_real_email_ses_error(self, mock_boto3_client):
        from botocore.exceptions import ClientError

        from mcp_server.capabilities.notification.tools.send_email_notification import (
            send_email_notification,
        )

        mock_ses = MagicMock()
        mock_boto3_client.return_value = mock_ses
        mock_ses.send_email.side_effect = ClientError(
            {"Error": {"Code": "MessageRejected", "Message": "rejected"}},
            "SendEmail",
        )

        with pytest.raises(ValueError, match="Failed to send email notification"):
            send_email_notification(
                to_addresses=["user@example.com"],
                subject="Fail",
                body="body",
            )
