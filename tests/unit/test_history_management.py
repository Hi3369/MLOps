"""
History Management Capability Unit Tests

履歴管理機能の単体テスト
"""

import pytest

from mcp_server.capabilities.history_management.capability import (
    HistoryManagementCapability,
)
from mcp_server.capabilities.history_management.tools import (
    format_training_history,
    post_issue_comment,
    save_training_history,
    track_version_history,
)


class TestHistoryManagementCapability:
    """HistoryManagementCapability クラスのテスト"""

    def test_initialization(self):
        """初期化テスト"""
        capability = HistoryManagementCapability()
        assert capability is not None
        assert capability._tools is not None
        assert len(capability._tools) == 4

    def test_get_tools(self):
        """ツール取得テスト"""
        capability = HistoryManagementCapability()
        tools = capability.get_tools()

        assert "format_training_history" in tools
        assert "save_training_history" in tools
        assert "post_issue_comment" in tools
        assert "track_version_history" in tools

    def test_get_tool_schemas(self):
        """ツールスキーマ取得テスト"""
        capability = HistoryManagementCapability()
        schemas = capability.get_tool_schemas()

        assert len(schemas) == 4
        for tool_name, schema in schemas.items():
            assert "name" in schema
            assert "description" in schema
            assert "parameters" in schema


class TestFormatTrainingHistory:
    """format_training_history ツールのテスト"""

    def test_format_basic_history(self):
        """基本的な履歴フォーマットテスト"""
        result = format_training_history(
            training_job_name="test-job-001",
            metrics={"accuracy": 0.95, "loss": 0.05},
        )

        assert result["status"] == "success"
        assert "history_result" in result
        assert result["history_result"]["training_job_name"] == "test-job-001"
        assert result["history_result"]["output_format"] == "markdown"
        assert "formatted_content" in result["history_result"]

    def test_format_with_hyperparameters(self):
        """ハイパーパラメータ付きフォーマットテスト"""
        result = format_training_history(
            training_job_name="test-job-002",
            metrics={"accuracy": 0.92},
            hyperparameters={"learning_rate": 0.001, "batch_size": 32},
        )

        assert result["status"] == "success"
        content = result["history_result"]["formatted_content"]
        assert "Hyperparameters" in content
        assert "learning_rate" in content

    def test_format_with_model_info(self):
        """モデル情報付きフォーマットテスト"""
        result = format_training_history(
            training_job_name="test-job-003",
            metrics={"accuracy": 0.90},
            model_name="my-model",
            model_version="v1.0.0",
            training_time_seconds=3600.0,
            instance_type="ml.p3.2xlarge",
        )

        assert result["status"] == "success"
        content = result["history_result"]["formatted_content"]
        assert "my-model" in content
        assert "v1.0.0" in content
        assert "60.00 minutes" in content
        assert "ml.p3.2xlarge" in content

    def test_format_as_json(self):
        """JSON形式フォーマットテスト"""
        result = format_training_history(
            training_job_name="test-job-json",
            metrics={"f1_score": 0.88},
            output_format="json",
        )

        assert result["status"] == "success"
        assert result["history_result"]["output_format"] == "json"
        content = result["history_result"]["formatted_content"]
        assert '"training_job_name"' in content
        assert '"f1_score"' in content

    def test_format_as_text(self):
        """テキスト形式フォーマットテスト"""
        result = format_training_history(
            training_job_name="test-job-text",
            metrics={"precision": 0.91},
            output_format="text",
        )

        assert result["status"] == "success"
        assert result["history_result"]["output_format"] == "text"

    def test_format_empty_job_name_error(self):
        """空ジョブ名でエラーテスト"""
        with pytest.raises(ValueError, match="training_job_name must not be empty"):
            format_training_history(
                training_job_name="",
                metrics={"accuracy": 0.9},
            )

    def test_format_empty_metrics_error(self):
        """空メトリクスでエラーテスト"""
        with pytest.raises(ValueError, match="metrics must not be empty"):
            format_training_history(
                training_job_name="test-job",
                metrics={},
            )

    def test_format_invalid_output_format_error(self):
        """無効な出力形式でエラーテスト"""
        with pytest.raises(ValueError, match="Invalid output_format"):
            format_training_history(
                training_job_name="test-job",
                metrics={"accuracy": 0.9},
                output_format="invalid",
            )


class TestSaveTrainingHistory:
    """save_training_history ツールのテスト"""

    def test_save_to_s3_mock(self):
        """S3保存（モック）テスト"""
        result = save_training_history(
            training_job_name="test-job-001",
            formatted_history="# Test History\n\nContent here",
            storage_type="s3",
        )

        assert result["status"] == "success"
        assert "save_result" in result
        assert result["save_result"]["storage_type"] == "s3"
        assert result["save_result"]["mock"] is True
        assert "s3://" in result["save_result"]["location"]

    def test_save_to_local_mock(self):
        """ローカル保存（モック）テスト"""
        result = save_training_history(
            training_job_name="test-job-002",
            formatted_history="# Test History",
            storage_type="local",
        )

        assert result["status"] == "success"
        assert result["save_result"]["storage_type"] == "local"
        assert result["save_result"]["mock"] is True

    def test_save_with_custom_bucket(self):
        """カスタムバケット指定テスト"""
        result = save_training_history(
            training_job_name="test-job-003",
            formatted_history="# Test",
            s3_bucket="custom-bucket",
            s3_prefix="custom/prefix/",
        )

        assert result["status"] == "success"
        assert "custom-bucket" in result["save_result"]["location"]
        assert "custom/prefix/" in result["save_result"]["location"]

    def test_save_with_json_format(self):
        """JSON形式保存テスト"""
        result = save_training_history(
            training_job_name="test-job-json",
            formatted_history='{"key": "value"}',
            file_format="json",
        )

        assert result["status"] == "success"
        assert result["save_result"]["filename"].endswith(".json")

    def test_save_empty_job_name_error(self):
        """空ジョブ名でエラーテスト"""
        with pytest.raises(ValueError, match="training_job_name must not be empty"):
            save_training_history(
                training_job_name="",
                formatted_history="content",
            )

    def test_save_empty_content_error(self):
        """空コンテンツでエラーテスト"""
        with pytest.raises(ValueError, match="formatted_history must not be empty"):
            save_training_history(
                training_job_name="test-job",
                formatted_history="",
            )

    def test_save_invalid_storage_type_error(self):
        """無効なストレージタイプでエラーテスト"""
        with pytest.raises(ValueError, match="Invalid storage_type"):
            save_training_history(
                training_job_name="test-job",
                formatted_history="content",
                storage_type="invalid",
            )


class TestPostIssueComment:
    """post_issue_comment ツールのテスト"""

    def test_post_basic_comment(self):
        """基本的なコメント投稿テスト"""
        result = post_issue_comment(
            repository="owner/repo",
            issue_number=1,
            comment="Test comment content",
        )

        assert result["status"] == "success"
        assert "comment_result" in result
        assert result["comment_result"]["repository"] == "owner/repo"
        assert result["comment_result"]["issue_number"] == 1
        assert result["comment_result"]["mock"] is True

    def test_post_progress_comment(self):
        """進捗コメント投稿テスト"""
        result = post_issue_comment(
            repository="owner/repo",
            issue_number=2,
            comment="Training in progress...",
            comment_type="progress",
        )

        assert result["status"] == "success"
        assert result["comment_result"]["comment_type"] == "progress"

    def test_post_result_comment(self):
        """結果コメント投稿テスト"""
        result = post_issue_comment(
            repository="owner/repo",
            issue_number=3,
            comment="Training completed!",
            comment_type="result",
        )

        assert result["status"] == "success"
        assert result["comment_result"]["comment_type"] == "result"

    def test_post_error_comment(self):
        """エラーコメント投稿テスト"""
        result = post_issue_comment(
            repository="owner/repo",
            issue_number=4,
            comment="Training failed: Out of memory",
            comment_type="error",
        )

        assert result["status"] == "success"
        assert result["comment_result"]["comment_type"] == "error"

    def test_post_without_timestamp(self):
        """タイムスタンプなしコメントテスト"""
        result = post_issue_comment(
            repository="owner/repo",
            issue_number=5,
            comment="Simple comment",
            include_timestamp=False,
        )

        assert result["status"] == "success"

    def test_post_empty_repository_error(self):
        """空リポジトリでエラーテスト"""
        with pytest.raises(ValueError, match="repository must not be empty"):
            post_issue_comment(
                repository="",
                issue_number=1,
                comment="Test",
            )

    def test_post_invalid_repository_format_error(self):
        """無効なリポジトリ形式でエラーテスト"""
        with pytest.raises(ValueError, match="owner/repo"):
            post_issue_comment(
                repository="invalid-format",
                issue_number=1,
                comment="Test",
            )

    def test_post_invalid_issue_number_error(self):
        """無効なIssue番号でエラーテスト"""
        with pytest.raises(ValueError, match="issue_number must be positive"):
            post_issue_comment(
                repository="owner/repo",
                issue_number=0,
                comment="Test",
            )

    def test_post_empty_comment_error(self):
        """空コメントでエラーテスト"""
        with pytest.raises(ValueError, match="comment must not be empty"):
            post_issue_comment(
                repository="owner/repo",
                issue_number=1,
                comment="",
            )

    def test_post_invalid_comment_type_error(self):
        """無効なコメントタイプでエラーテスト"""
        with pytest.raises(ValueError, match="Invalid comment_type"):
            post_issue_comment(
                repository="owner/repo",
                issue_number=1,
                comment="Test",
                comment_type="invalid",
            )


class TestTrackVersionHistory:
    """track_version_history ツールのテスト"""

    def test_track_basic_version(self):
        """基本的なバージョン追跡テスト"""
        result = track_version_history(
            model_name="my-model",
            version="v1.0.0",
        )

        assert result["status"] == "success"
        assert "version_result" in result
        assert result["version_result"]["model_name"] == "my-model"
        assert result["version_result"]["version"] == "v1.0.0"
        assert result["version_result"]["mock"] is True

    def test_track_with_parent_version(self):
        """親バージョン指定テスト"""
        result = track_version_history(
            model_name="my-model",
            version="v1.1.0",
            parent_version="v1.0.0",
        )

        assert result["status"] == "success"
        assert result["version_result"]["parent_version"] == "v1.0.0"

    def test_track_with_full_metadata(self):
        """完全なメタデータ付き追跡テスト"""
        result = track_version_history(
            model_name="production-model",
            version="v2.0.0",
            parent_version="v1.5.0",
            training_job_name="training-job-xyz",
            training_data_version="dataset-v3",
            code_version="abc123def",
            status="staging",
            tags=["bert", "nlp", "classification"],
            metadata={"framework": "pytorch", "custom_key": "custom_value"},
        )

        assert result["status"] == "success"
        assert result["version_result"]["status"] == "staging"
        lineage = result["version_result"]["lineage"]
        assert lineage["training_job"] == "training-job-xyz"
        assert lineage["training_data"] == "dataset-v3"
        assert lineage["code"] == "abc123def"

    def test_track_production_status(self):
        """本番ステータステスト"""
        result = track_version_history(
            model_name="model",
            version="v1.0.0",
            status="production",
        )

        assert result["status"] == "success"
        assert result["version_result"]["status"] == "production"

    def test_track_deprecated_status(self):
        """非推奨ステータステスト"""
        result = track_version_history(
            model_name="old-model",
            version="v0.1.0",
            status="deprecated",
        )

        assert result["status"] == "success"
        assert result["version_result"]["status"] == "deprecated"

    def test_track_empty_model_name_error(self):
        """空モデル名でエラーテスト"""
        with pytest.raises(ValueError, match="model_name must not be empty"):
            track_version_history(
                model_name="",
                version="v1.0.0",
            )

    def test_track_empty_version_error(self):
        """空バージョンでエラーテスト"""
        with pytest.raises(ValueError, match="version must not be empty"):
            track_version_history(
                model_name="model",
                version="",
            )

    def test_track_invalid_status_error(self):
        """無効なステータスでエラーテスト"""
        with pytest.raises(ValueError, match="Invalid status"):
            track_version_history(
                model_name="model",
                version="v1.0.0",
                status="invalid",
            )

    def test_track_non_semver_warning(self):
        """非セマンティックバージョンでも動作するテスト"""
        # 警告は出るが、エラーにはならない
        result = track_version_history(
            model_name="model",
            version="custom-version-123",
        )
        assert result["status"] == "success"


class TestIntegration:
    """統合テスト"""

    def test_format_and_save_workflow(self):
        """フォーマット→保存のワークフローテスト"""
        # Step 1: フォーマット
        format_result = format_training_history(
            training_job_name="integration-test-job",
            metrics={"accuracy": 0.95, "f1_score": 0.93},
            hyperparameters={"epochs": 100},
            model_name="integration-model",
            model_version="v1.0.0",
        )
        assert format_result["status"] == "success"

        # Step 2: 保存
        formatted_content = format_result["history_result"]["formatted_content"]
        save_result = save_training_history(
            training_job_name="integration-test-job",
            formatted_history=formatted_content,
            storage_type="s3",
        )
        assert save_result["status"] == "success"

    def test_format_and_post_workflow(self):
        """フォーマット→Issue投稿のワークフローテスト"""
        # Step 1: フォーマット
        format_result = format_training_history(
            training_job_name="workflow-job",
            metrics={"accuracy": 0.88},
            output_format="text",
        )
        assert format_result["status"] == "success"

        # Step 2: Issue投稿
        comment_result = post_issue_comment(
            repository="owner/repo",
            issue_number=10,
            comment=format_result["history_result"]["formatted_content"],
            comment_type="result",
        )
        assert comment_result["status"] == "success"

    def test_full_workflow(self):
        """完全なワークフローテスト"""
        # Step 1: バージョン追跡
        version_result = track_version_history(
            model_name="full-workflow-model",
            version="v1.0.0",
            training_job_name="full-workflow-job",
            status="development",
        )
        assert version_result["status"] == "success"

        # Step 2: フォーマット
        format_result = format_training_history(
            training_job_name="full-workflow-job",
            metrics={"accuracy": 0.96},
            model_name="full-workflow-model",
            model_version="v1.0.0",
        )
        assert format_result["status"] == "success"

        # Step 3: 保存
        save_result = save_training_history(
            training_job_name="full-workflow-job",
            formatted_history=format_result["history_result"]["formatted_content"],
        )
        assert save_result["status"] == "success"

        # Step 4: Issue投稿
        comment_result = post_issue_comment(
            repository="owner/repo",
            issue_number=100,
            comment="Training completed! See attached results.",
            comment_type="result",
        )
        assert comment_result["status"] == "success"
