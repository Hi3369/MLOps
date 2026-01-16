"""
Notification Capability Unit Tests

通知機能の単体テスト
"""

import pytest

from mcp_server.capabilities.notification.capability import NotificationCapability
from mcp_server.capabilities.notification.tools import (
    apply_notification_template,
    list_available_templates,
    send_email_notification,
    send_github_notification,
    send_slack_notification,
)


class TestNotificationCapability:
    """NotificationCapability クラスのテスト"""

    def test_initialization(self):
        """初期化テスト"""
        capability = NotificationCapability()
        assert capability is not None
        assert capability._tools is not None
        assert len(capability._tools) == 4

    def test_get_tools(self):
        """ツール取得テスト"""
        capability = NotificationCapability()
        tools = capability.get_tools()

        assert "send_slack_notification" in tools
        assert "send_email_notification" in tools
        assert "send_github_notification" in tools
        assert "apply_notification_template" in tools

    def test_get_tool_schemas(self):
        """ツールスキーマ取得テスト"""
        capability = NotificationCapability()
        schemas = capability.get_tool_schemas()

        assert len(schemas) == 4
        for tool_name, schema in schemas.items():
            assert "name" in schema
            assert "description" in schema
            assert "parameters" in schema


class TestSendSlackNotification:
    """send_slack_notification ツールのテスト"""

    def test_send_basic_notification(self):
        """基本的な通知送信テスト"""
        result = send_slack_notification(
            message="Test notification message",
        )

        assert result["status"] == "success"
        assert "notification_result" in result
        assert result["notification_result"]["channel"] == "#mlops-notifications"
        assert result["notification_result"]["mock"] is True

    def test_send_with_custom_channel(self):
        """カスタムチャンネル指定テスト"""
        result = send_slack_notification(
            message="Test message",
            channel="#custom-channel",
        )

        assert result["status"] == "success"
        assert result["notification_result"]["channel"] == "#custom-channel"

    def test_send_with_custom_username(self):
        """カスタムユーザー名指定テスト"""
        result = send_slack_notification(
            message="Test message",
            username="Custom Bot",
            icon_emoji=":tada:",
        )

        assert result["status"] == "success"
        assert result["notification_result"]["username"] == "Custom Bot"
        assert result["notification_result"]["icon_emoji"] == ":tada:"

    def test_send_with_attachments(self):
        """attachments付き通知テスト"""
        attachments = [
            {
                "color": "#36a64f",
                "title": "Test Attachment",
                "text": "This is attachment text",
            }
        ]
        result = send_slack_notification(
            message="Test message",
            attachments=attachments,
        )

        assert result["status"] == "success"
        assert result["notification_result"]["has_attachments"] is True

    def test_send_with_blocks(self):
        """Block Kit付き通知テスト"""
        blocks = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*Bold text*"},
            }
        ]
        result = send_slack_notification(
            message="Test message",
            blocks=blocks,
        )

        assert result["status"] == "success"
        assert result["notification_result"]["has_blocks"] is True

    def test_send_empty_message_error(self):
        """空メッセージでエラーテスト"""
        with pytest.raises(ValueError, match="message must not be empty"):
            send_slack_notification(message="")

    def test_send_empty_channel_error(self):
        """空チャンネルでエラーテスト"""
        with pytest.raises(ValueError, match="channel must not be empty"):
            send_slack_notification(message="Test", channel="")


class TestSendEmailNotification:
    """send_email_notification ツールのテスト"""

    def test_send_basic_email(self):
        """基本的なEmail送信テスト"""
        result = send_email_notification(
            to_addresses=["test@example.com"],
            subject="Test Subject",
            body="Test body content",
        )

        assert result["status"] == "success"
        assert "notification_result" in result
        assert result["notification_result"]["to_addresses"] == ["test@example.com"]
        assert result["notification_result"]["subject"] == "Test Subject"
        assert result["notification_result"]["mock"] is True

    def test_send_to_multiple_recipients(self):
        """複数宛先への送信テスト"""
        result = send_email_notification(
            to_addresses=["user1@example.com", "user2@example.com"],
            subject="Test Subject",
            body="Test body",
        )

        assert result["status"] == "success"
        assert len(result["notification_result"]["to_addresses"]) == 2

    def test_send_with_cc_bcc(self):
        """CC/BCC付き送信テスト"""
        result = send_email_notification(
            to_addresses=["to@example.com"],
            subject="Test Subject",
            body="Test body",
            cc_addresses=["cc@example.com"],
            bcc_addresses=["bcc@example.com"],
        )

        assert result["status"] == "success"
        assert result["notification_result"]["cc_addresses"] == ["cc@example.com"]
        assert result["notification_result"]["bcc_addresses"] == ["bcc@example.com"]

    def test_send_with_html_body(self):
        """HTML本文付き送信テスト"""
        result = send_email_notification(
            to_addresses=["test@example.com"],
            subject="Test Subject",
            body="Plain text body",
            html_body="<h1>HTML Body</h1>",
        )

        assert result["status"] == "success"
        assert result["notification_result"]["has_html_body"] is True

    def test_send_empty_to_addresses_error(self):
        """空の宛先でエラーテスト"""
        with pytest.raises(ValueError, match="to_addresses must not be empty"):
            send_email_notification(
                to_addresses=[],
                subject="Test",
                body="Test",
            )

    def test_send_invalid_to_addresses_type_error(self):
        """無効な宛先型でエラーテスト"""
        with pytest.raises(ValueError, match="to_addresses must be a list"):
            send_email_notification(
                to_addresses="test@example.com",
                subject="Test",
                body="Test",
            )

    def test_send_empty_subject_error(self):
        """空の件名でエラーテスト"""
        with pytest.raises(ValueError, match="subject must not be empty"):
            send_email_notification(
                to_addresses=["test@example.com"],
                subject="",
                body="Test",
            )

    def test_send_empty_body_error(self):
        """空の本文でエラーテスト"""
        with pytest.raises(ValueError, match="body must not be empty"):
            send_email_notification(
                to_addresses=["test@example.com"],
                subject="Test",
                body="",
            )

    def test_send_invalid_email_address_error(self):
        """無効なメールアドレスでエラーテスト"""
        with pytest.raises(ValueError, match="Invalid email address"):
            send_email_notification(
                to_addresses=["invalid-email"],
                subject="Test",
                body="Test",
            )


class TestSendGitHubNotification:
    """send_github_notification ツールのテスト"""

    def test_send_issue_comment(self):
        """Issueコメント送信テスト"""
        result = send_github_notification(
            repo_owner="test-owner",
            repo_name="test-repo",
            notification_type="issue_comment",
            target_number=123,
            message="Test comment message",
        )

        assert result["status"] == "success"
        assert result["notification_result"]["notification_type"] == "issue_comment"
        assert result["notification_result"]["target_number"] == 123
        assert result["notification_result"]["mock"] is True

    def test_send_pr_comment(self):
        """PRコメント送信テスト"""
        result = send_github_notification(
            repo_owner="test-owner",
            repo_name="test-repo",
            notification_type="pr_comment",
            target_number=456,
            message="Test PR comment",
        )

        assert result["status"] == "success"
        assert result["notification_result"]["notification_type"] == "pr_comment"
        assert result["notification_result"]["target_number"] == 456

    def test_create_issue(self):
        """Issue作成テスト"""
        result = send_github_notification(
            repo_owner="test-owner",
            repo_name="test-repo",
            notification_type="issue_create",
            target_number=0,
            message="New Issue Title\n\nThis is the issue body.",
            labels=["bug", "mlops"],
            assignees=["developer1"],
        )

        assert result["status"] == "success"
        assert result["notification_result"]["notification_type"] == "issue_create"
        assert "issue_number" in result["notification_result"]
        assert result["notification_result"]["labels"] == ["bug", "mlops"]
        assert result["notification_result"]["assignees"] == ["developer1"]

    def test_send_empty_repo_owner_error(self):
        """空のrepo_ownerでエラーテスト"""
        with pytest.raises(ValueError, match="repo_owner must not be empty"):
            send_github_notification(
                repo_owner="",
                repo_name="test-repo",
                notification_type="issue_comment",
                target_number=1,
                message="Test",
            )

    def test_send_empty_repo_name_error(self):
        """空のrepo_nameでエラーテスト"""
        with pytest.raises(ValueError, match="repo_name must not be empty"):
            send_github_notification(
                repo_owner="test-owner",
                repo_name="",
                notification_type="issue_comment",
                target_number=1,
                message="Test",
            )

    def test_send_empty_message_error(self):
        """空のmessageでエラーテスト"""
        with pytest.raises(ValueError, match="message must not be empty"):
            send_github_notification(
                repo_owner="test-owner",
                repo_name="test-repo",
                notification_type="issue_comment",
                target_number=1,
                message="",
            )

    def test_send_invalid_notification_type_error(self):
        """無効なnotification_typeでエラーテスト"""
        with pytest.raises(ValueError, match="notification_type must be one of"):
            send_github_notification(
                repo_owner="test-owner",
                repo_name="test-repo",
                notification_type="invalid_type",
                target_number=1,
                message="Test",
            )

    def test_send_invalid_target_number_for_comment(self):
        """コメントで無効なtarget_numberでエラーテスト"""
        with pytest.raises(ValueError, match="target_number must be positive"):
            send_github_notification(
                repo_owner="test-owner",
                repo_name="test-repo",
                notification_type="issue_comment",
                target_number=0,
                message="Test",
            )


class TestApplyNotificationTemplate:
    """apply_notification_template ツールのテスト"""

    def test_apply_training_started_template(self):
        """training_startedテンプレート適用テスト"""
        result = apply_notification_template(
            template_name="training_started",
            variables={
                "model_name": "xgboost-classifier",
                "job_id": "job-12345",
                "start_time": "2024-01-15T10:00:00Z",
                "model_type": "xgboost",
                "dataset_path": "s3://bucket/data/",
                "instance_type": "ml.m5.large",
            },
        )

        assert result["status"] == "success"
        assert "template_result" in result
        assert result["template_result"]["template_name"] == "training_started"
        assert "email" in result["template_result"]
        assert "slack" in result["template_result"]
        assert "github" in result["template_result"]

    def test_apply_training_completed_template(self):
        """training_completedテンプレート適用テスト"""
        result = apply_notification_template(
            template_name="training_completed",
            variables={
                "model_name": "random-forest",
                "job_id": "job-67890",
                "duration": "45 minutes",
                "accuracy": "0.95",
                "loss": "0.05",
                "model_arn": "arn:aws:sagemaker:...",
            },
        )

        assert result["status"] == "success"
        email_subject = result["template_result"]["email"]["subject"]
        assert "Training Completed" in email_subject
        assert "random-forest" in email_subject

    def test_apply_training_failed_template(self):
        """training_failedテンプレート適用テスト"""
        result = apply_notification_template(
            template_name="training_failed",
            variables={
                "model_name": "nn-model",
                "job_id": "job-failed",
                "failed_time": "2024-01-15T12:00:00Z",
                "error_message": "OutOfMemoryError: CUDA out of memory",
            },
        )

        assert result["status"] == "success"
        email_body = result["template_result"]["email"]["body"]
        assert "OutOfMemoryError" in email_body

    def test_apply_drift_detected_template(self):
        """drift_detectedテンプレート適用テスト"""
        result = apply_notification_template(
            template_name="drift_detected",
            variables={
                "model_name": "production-model",
                "endpoint_name": "prod-endpoint",
                "detected_time": "2024-01-15T14:00:00Z",
                "drift_score": "0.85",
                "affected_features": "age, income, location",
                "threshold": "0.7",
            },
        )

        assert result["status"] == "success"
        assert "Data Drift Detected" in result["template_result"]["email"]["subject"]

    def test_apply_email_only_format(self):
        """emailのみの出力フォーマットテスト"""
        result = apply_notification_template(
            template_name="training_started",
            variables={"model_name": "test-model"},
            output_format="email",
        )

        assert result["status"] == "success"
        assert "email" in result["template_result"]
        assert "slack" not in result["template_result"]
        assert "github" not in result["template_result"]

    def test_apply_slack_only_format(self):
        """slackのみの出力フォーマットテスト"""
        result = apply_notification_template(
            template_name="training_started",
            variables={"model_name": "test-model"},
            output_format="slack",
        )

        assert result["status"] == "success"
        assert "slack" in result["template_result"]
        assert "email" not in result["template_result"]

    def test_apply_custom_template(self):
        """カスタムテンプレート適用テスト"""
        custom = {
            "subject": "Custom: {event_type}",
            "body": "Event {event_type} occurred for {resource_name}",
        }
        result = apply_notification_template(
            template_name="custom",
            variables={
                "event_type": "deployment",
                "resource_name": "api-server",
            },
            custom_template=custom,
        )

        assert result["status"] == "success"
        assert "deployment" in result["template_result"]["email"]["subject"]

    def test_apply_empty_template_name_error(self):
        """空のtemplate_nameでエラーテスト"""
        with pytest.raises(ValueError, match="template_name must not be empty"):
            apply_notification_template(
                template_name="",
                variables={"key": "value"},
            )

    def test_apply_empty_variables_error(self):
        """空のvariablesでエラーテスト"""
        with pytest.raises(ValueError, match="variables must not be empty"):
            apply_notification_template(
                template_name="training_started",
                variables={},
            )

    def test_apply_invalid_variables_type_error(self):
        """無効なvariables型でエラーテスト"""
        with pytest.raises(ValueError, match="variables must be a dictionary"):
            apply_notification_template(
                template_name="training_started",
                variables="invalid",
            )

    def test_apply_unknown_template_error(self):
        """不明なテンプレート名でエラーテスト"""
        with pytest.raises(ValueError, match="Unknown template"):
            apply_notification_template(
                template_name="unknown_template",
                variables={"key": "value"},
            )

    def test_apply_invalid_output_format_error(self):
        """無効なoutput_formatでエラーテスト"""
        with pytest.raises(ValueError, match="output_format must be one of"):
            apply_notification_template(
                template_name="training_started",
                variables={"model_name": "test"},
                output_format="invalid",
            )


class TestListAvailableTemplates:
    """list_available_templates 関数のテスト"""

    def test_list_templates(self):
        """テンプレート一覧取得テスト"""
        result = list_available_templates()

        assert result["status"] == "success"
        assert "templates" in result
        assert result["total"] >= 6  # 少なくとも6つのテンプレート

        # 各テンプレートの構造確認
        for template in result["templates"]:
            assert "name" in template
            assert "has_subject" in template
            assert "has_body" in template
            assert "variables" in template

    def test_known_templates_exist(self):
        """既知のテンプレートが存在することを確認"""
        result = list_available_templates()
        template_names = [t["name"] for t in result["templates"]]

        expected_templates = [
            "training_started",
            "training_completed",
            "training_failed",
            "deployment_started",
            "deployment_completed",
            "drift_detected",
        ]

        for expected in expected_templates:
            assert expected in template_names


class TestIntegration:
    """統合テスト"""

    def test_template_to_slack_notification(self):
        """テンプレート適用からSlack通知送信までの流れテスト"""
        # 1. テンプレート適用
        template_result = apply_notification_template(
            template_name="training_completed",
            variables={
                "model_name": "test-model",
                "job_id": "job-123",
                "duration": "30 minutes",
                "accuracy": "0.92",
                "loss": "0.08",
                "model_arn": "arn:aws:sagemaker:...",
            },
            output_format="slack",
        )

        assert template_result["status"] == "success"

        # 2. Slack通知送信
        slack_text = template_result["template_result"]["slack"]["text"]
        slack_result = send_slack_notification(
            message=slack_text,
            channel="#ml-notifications",
        )

        assert slack_result["status"] == "success"

    def test_template_to_email_notification(self):
        """テンプレート適用からEmail通知送信までの流れテスト"""
        # 1. テンプレート適用
        template_result = apply_notification_template(
            template_name="drift_detected",
            variables={
                "model_name": "prod-model",
                "endpoint_name": "prod-endpoint",
                "detected_time": "2024-01-15T14:00:00Z",
                "drift_score": "0.85",
                "affected_features": "feature1, feature2",
                "threshold": "0.7",
            },
            output_format="email",
        )

        assert template_result["status"] == "success"

        # 2. Email送信
        email_data = template_result["template_result"]["email"]
        email_result = send_email_notification(
            to_addresses=["team@example.com"],
            subject=email_data["subject"],
            body=email_data["body"],
        )

        assert email_result["status"] == "success"

    def test_template_to_github_notification(self):
        """テンプレート適用からGitHub通知送信までの流れテスト"""
        # 1. テンプレート適用
        template_result = apply_notification_template(
            template_name="training_failed",
            variables={
                "model_name": "failed-model",
                "job_id": "job-fail-001",
                "failed_time": "2024-01-15T16:00:00Z",
                "error_message": "Training timeout exceeded",
            },
            output_format="github",
        )

        assert template_result["status"] == "success"

        # 2. GitHub Issue作成
        github_data = template_result["template_result"]["github"]
        github_result = send_github_notification(
            repo_owner="mlops-team",
            repo_name="ml-project",
            notification_type="issue_create",
            target_number=0,
            message=f"{github_data['title']}\n\n{github_data['body']}",
            labels=["training-failure", "automated"],
        )

        assert github_result["status"] == "success"
