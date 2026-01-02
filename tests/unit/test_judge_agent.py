import os
import sys

import pytest

# Add agents/judge_agent to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "agents", "judge_agent"))

from lambda_function import JudgeAgent


class TestJudgeAgent:
    """
    Judge Agentのユニットテスト
    """

    @pytest.fixture
    def judge_agent(self):
        return JudgeAgent()

    def test_judge_acceptable_classification(self, judge_agent):
        """
        分類タスクで合格判定のテスト
        """
        event = {
            "training_id": "train-001",
            "model_type": "supervised_learning",
            "task_type": "classification",
            "evaluation_results": {
                "accuracy": 0.92,
                "precision": 0.90,
                "recall": 0.94,
                "f1_score": 0.92,
                "auc_roc": 0.95,
            },
            "acceptance_criteria": {
                "min_accuracy": 0.85,
                "min_precision": 0.80,
                "min_recall": 0.80,
                "min_f1_score": 0.80,
                "min_auc_roc": 0.85,
            },
            "retry_count": 0,
            "max_retries": 3,
        }

        result = judge_agent.judge_model(event)

        assert result["judgment"]["is_acceptable"] is True
        assert result["next_action"]["action"] == "deploy"
        assert result["next_action"]["notify_operator"] is False
        assert len(result["judgment"]["failed_criteria"]) == 0

    def test_judge_unacceptable_classification(self, judge_agent):
        """
        分類タスクで不合格判定のテスト
        """
        event = {
            "training_id": "train-002",
            "model_type": "supervised_learning",
            "task_type": "classification",
            "evaluation_results": {
                "accuracy": 0.78,
                "precision": 0.82,
                "recall": 0.88,
                "f1_score": 0.75,
                "auc_roc": 0.80,
            },
            "acceptance_criteria": {
                "min_accuracy": 0.85,
                "min_precision": 0.80,
                "min_recall": 0.80,
                "min_f1_score": 0.80,
                "min_auc_roc": 0.85,
            },
            "retry_count": 0,
            "max_retries": 3,
        }

        result = judge_agent.judge_model(event)

        assert result["judgment"]["is_acceptable"] is False
        assert result["next_action"]["action"] == "retry"
        assert result["next_action"]["notify_operator"] is True
        assert len(result["judgment"]["failed_criteria"]) == 3  # accuracy, f1_score, auc_roc

    def test_judge_max_retries_exceeded(self, judge_agent):
        """
        最大リトライ回数超過時のテスト
        """
        event = {
            "training_id": "train-003",
            "model_type": "supervised_learning",
            "task_type": "classification",
            "evaluation_results": {
                "accuracy": 0.75,
                "precision": 0.70,
                "recall": 0.80,
                "f1_score": 0.70,
            },
            "acceptance_criteria": {
                "min_accuracy": 0.85,
                "min_precision": 0.80,
                "min_recall": 0.80,
                "min_f1_score": 0.80,
            },
            "retry_count": 3,
            "max_retries": 3,
        }

        result = judge_agent.judge_model(event)

        assert result["judgment"]["is_acceptable"] is False
        assert result["next_action"]["action"] == "abort"
        assert result["next_action"]["notify_operator"] is True

    def test_judge_regression_task(self, judge_agent):
        """
        回帰タスクの判定テスト
        """
        event = {
            "training_id": "train-004",
            "model_type": "supervised_learning",
            "task_type": "regression",
            "evaluation_results": {"rmse": 8.5, "mae": 4.2, "r2_score": 0.88},
            "acceptance_criteria": {"max_rmse": 10.0, "max_mae": 5.0, "min_r2_score": 0.80},
            "retry_count": 0,
            "max_retries": 3,
        }

        result = judge_agent.judge_model(event)

        assert result["judgment"]["is_acceptable"] is True
        assert result["next_action"]["action"] == "deploy"

    def test_judge_clustering_task(self, judge_agent):
        """
        クラスタリングタスクの判定テスト
        """
        event = {
            "training_id": "train-005",
            "model_type": "unsupervised_learning",
            "task_type": "clustering",
            "evaluation_results": {"silhouette_score": 0.65},
            "acceptance_criteria": {"min_silhouette_score": 0.50},
            "retry_count": 0,
            "max_retries": 3,
        }

        result = judge_agent.judge_model(event)

        assert result["judgment"]["is_acceptable"] is True
        assert result["next_action"]["action"] == "deploy"
        assert len(result["judgment"]["passed_criteria"]) == 1

    def test_judge_reinforcement_learning_task(self, judge_agent):
        """
        強化学習タスクの判定テスト
        """
        event = {
            "training_id": "train-006",
            "model_type": "reinforcement_learning",
            "task_type": "reinforcement_learning",
            "evaluation_results": {"avg_reward": 150.5, "success_rate": 0.85},
            "acceptance_criteria": {"min_avg_reward": 100, "min_success_rate": 0.70},
            "retry_count": 0,
            "max_retries": 3,
        }

        result = judge_agent.judge_model(event)

        assert result["judgment"]["is_acceptable"] is True
        assert result["next_action"]["action"] == "deploy"
        assert len(result["judgment"]["passed_criteria"]) == 2

    def test_judge_partial_metrics(self, judge_agent):
        """
        一部の指標のみ存在する場合のテスト（auc_rocなし）
        """
        event = {
            "training_id": "train-007",
            "model_type": "supervised_learning",
            "task_type": "classification",
            "evaluation_results": {
                "accuracy": 0.90,
                "precision": 0.88,
                "recall": 0.92,
                "f1_score": 0.90
                # auc_roc is missing
            },
            "acceptance_criteria": {
                "min_accuracy": 0.85,
                "min_precision": 0.80,
                "min_recall": 0.80,
                "min_f1_score": 0.80,
                "min_auc_roc": 0.85,
            },
            "retry_count": 0,
            "max_retries": 3,
        }

        result = judge_agent.judge_model(event)

        # auc_rocがなくても他の指標が合格なら全体として合格
        assert result["judgment"]["is_acceptable"] is True
        assert result["next_action"]["action"] == "deploy"
        assert len(result["judgment"]["passed_criteria"]) == 4

    def test_notification_message_format(self, judge_agent):
        """
        通知メッセージフォーマットのテスト
        """
        event = {
            "training_id": "train-008",
            "model_type": "supervised_learning",
            "task_type": "classification",
            "evaluation_results": {
                "accuracy": 0.78,
                "precision": 0.82,
                "recall": 0.88,
                "f1_score": 0.75,
                "auc_roc": 0.80,
            },
            "acceptance_criteria": {
                "min_accuracy": 0.85,
                "min_precision": 0.80,
                "min_recall": 0.80,
                "min_f1_score": 0.80,
                "min_auc_roc": 0.85,
            },
            "retry_count": 0,
            "max_retries": 3,
            "github_issue_url": "https://github.com/user/repo/issues/42",
            "notification_channels": ["slack", "github"],
        }

        result = judge_agent.judge_model(event)

        # 通知メッセージの存在確認
        assert "operator_notification" in result
        notification = result["operator_notification"]

        # メッセージフォーマット検証
        assert "message" in notification
        assert "channels" in notification
        assert "モデル評価結果: 不合格" in notification["message"]
        assert "train-008" in notification["message"]
        assert "accuracy" in notification["message"]
        assert "https://github.com/user/repo/issues/42" in notification["message"]
        assert notification["channels"] == ["slack", "github"]

    def test_github_url_validation_valid(self, judge_agent):
        """
        有効なGitHub Issue URLの検証テスト
        """
        assert judge_agent._validate_github_url("https://github.com/user/repo/issues/123") is True
        assert (
            judge_agent._validate_github_url("https://github.com/my-org/my-repo/issues/1") is True
        )
        assert judge_agent._validate_github_url("") is True  # 空URLは許可

    def test_github_url_validation_invalid(self, judge_agent):
        """
        無効なGitHub Issue URLの検証テスト
        """
        # 無効なURL形式
        # http
        assert judge_agent._validate_github_url("http://github.com/user/repo/issues/123") is False
        # pull request
        assert judge_agent._validate_github_url("https://github.com/user/repo/pull/123") is False
        # issueなし
        assert judge_agent._validate_github_url("https://github.com/user/repo") is False
        # 悪意あるURL
        assert (
            judge_agent._validate_github_url("https://evil.com/github.com/user/repo/issues/123")
            is False
        )
        assert judge_agent._validate_github_url("javascript:alert(1)") is False  # XSS攻撃

    def test_judge_with_invalid_github_url(self, judge_agent):
        """
        無効なGitHub Issue URLでエラーが発生することのテスト
        """
        event = {
            "training_id": "train-009",
            "model_type": "supervised_learning",
            "task_type": "classification",
            "evaluation_results": {"accuracy": 0.78},
            "acceptance_criteria": {"min_accuracy": 0.85},
            "retry_count": 0,
            "max_retries": 3,
            "github_issue_url": "https://evil.com/malicious",  # 無効なURL
        }

        with pytest.raises(ValueError) as exc_info:
            judge_agent.judge_model(event)

        assert "Invalid GitHub Issue URL" in str(exc_info.value)
