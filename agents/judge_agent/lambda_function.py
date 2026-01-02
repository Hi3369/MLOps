import json
import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class JudgeAgent:
    """
    評価結果の判定と次アクションの決定を行うエージェント
    """

    def __init__(self):
        self.logger = logger
        # デフォルト閾値の読み込み（環境変数または設定ファイルから）
        self.default_thresholds = self._load_default_thresholds()

    def _load_default_thresholds(self) -> Dict[str, Dict[str, float]]:
        """
        デフォルト閾値を環境変数またはS3設定ファイルから読み込み

        環境変数が設定されていない場合はハードコーディング値を使用
        """
        # 環境変数からの読み込み（JSON形式）
        thresholds_json = os.getenv("DEFAULT_THRESHOLDS")

        if thresholds_json:
            try:
                return json.loads(thresholds_json)
            except json.JSONDecodeError:
                self.logger.warning(
                    "Failed to parse DEFAULT_THRESHOLDS from env, " "using hardcoded defaults"
                )

        # フォールバック: ハードコーディング値
        return {
            "classification": {
                "min_accuracy": 0.85,
                "min_precision": 0.80,
                "min_recall": 0.80,
                "min_f1_score": 0.80,
                "min_auc_roc": 0.85,
            },
            "regression": {"max_rmse": 10.0, "max_mae": 5.0, "min_r2_score": 0.80},
            "clustering": {"min_silhouette_score": 0.50},
            "reinforcement_learning": {"min_avg_reward": 100, "min_success_rate": 0.70},
        }

    def _validate_github_url(self, url: str) -> bool:
        """
        GitHub IssueのURL検証（URLインジェクション対策）

        Args:
            url: 検証するURL

        Returns:
            True: 有効なGitHub Issue URL
            False: 無効なURL
        """
        if not url:
            return True  # URLが空の場合は検証スキップ

        pattern = r"^https://github\.com/[\w-]+/[\w-]+/issues/\d+$"
        return re.match(pattern, url) is not None

    def judge_model(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        モデル評価結果を判定し、次アクションを決定

        Args:
            event: Step Functionsからの入力データ

        Returns:
            判定結果と次アクション
        """
        training_id = event["training_id"]
        task_type = event["task_type"]
        evaluation_results = event["evaluation_results"]
        acceptance_criteria = event["acceptance_criteria"]
        retry_count = event.get("retry_count", 0)
        max_retries = event.get("max_retries", 3)

        # GitHub Issue URL検証（セキュリティ対策）
        github_issue_url = event.get("github_issue_url", "")
        if github_issue_url and not self._validate_github_url(github_issue_url):
            raise ValueError(f"Invalid GitHub Issue URL: {github_issue_url}")

        self.logger.info(f"Judging model: {training_id}, task_type: {task_type}")

        # 判定実行
        is_acceptable, passed_criteria, failed_criteria = self._evaluate_criteria(
            task_type, evaluation_results, acceptance_criteria
        )

        # 次アクション決定
        next_action = self._determine_next_action(is_acceptable, retry_count, max_retries)

        # 結果構築
        result = {
            "training_id": training_id,
            "judgment": {
                "is_acceptable": is_acceptable,
                "passed_criteria": passed_criteria,
                "failed_criteria": failed_criteria,
            },
            "next_action": next_action,
            "retry_count": retry_count if not is_acceptable else 0,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        # オペレータ通知が必要な場合
        if next_action["notify_operator"]:
            result["operator_notification"] = self._create_notification_message(
                training_id, failed_criteria, retry_count, max_retries, event
            )

        self.logger.info(f"Judgment result: {json.dumps(result, indent=2)}")
        return result

    def _evaluate_criteria(
        self,
        task_type: str,
        evaluation_results: Dict[str, float],
        acceptance_criteria: Dict[str, float],
    ) -> tuple[bool, List[str], List[str]]:
        """
        受入基準の評価

        Returns:
            (is_acceptable, passed_criteria, failed_criteria)
        """
        passed = []
        failed = []

        # デフォルト閾値を取得（環境変数または設定ファイルから）
        default_thresholds = self.default_thresholds.get(task_type, {})

        if task_type == "classification":
            criteria_map = {
                "accuracy": ("min_accuracy", default_thresholds.get("min_accuracy", 0.85), ">="),
                "precision": ("min_precision", default_thresholds.get("min_precision", 0.80), ">="),
                "recall": ("min_recall", default_thresholds.get("min_recall", 0.80), ">="),
                "f1_score": ("min_f1_score", default_thresholds.get("min_f1_score", 0.80), ">="),
                "auc_roc": ("min_auc_roc", default_thresholds.get("min_auc_roc", 0.85), ">="),
            }
        elif task_type == "regression":
            criteria_map = {
                "rmse": ("max_rmse", default_thresholds.get("max_rmse", 10.0), "<="),
                "mae": ("max_mae", default_thresholds.get("max_mae", 5.0), "<="),
                "r2_score": ("min_r2_score", default_thresholds.get("min_r2_score", 0.80), ">="),
            }
        elif task_type == "clustering":
            criteria_map = {
                "silhouette_score": (
                    "min_silhouette_score",
                    default_thresholds.get("min_silhouette_score", 0.50),
                    ">=",
                )
            }
        elif task_type == "reinforcement_learning":
            criteria_map = {
                "avg_reward": (
                    "min_avg_reward",
                    default_thresholds.get("min_avg_reward", 100),
                    ">=",
                ),
                "success_rate": (
                    "min_success_rate",
                    default_thresholds.get("min_success_rate", 0.70),
                    ">=",
                ),
            }
        else:
            raise ValueError(f"Unknown task_type: {task_type}")

        for metric_name, (criteria_key, default_threshold, operator) in criteria_map.items():
            if metric_name not in evaluation_results:
                continue

            actual_value = evaluation_results[metric_name]
            threshold = acceptance_criteria.get(criteria_key, default_threshold)

            if operator == ">=":
                is_passed = actual_value >= threshold
            else:  # "<="
                is_passed = actual_value <= threshold

            criterion_text = f"{metric_name} {operator} {threshold} (actual: {actual_value:.4f})"

            if is_passed:
                passed.append(criterion_text)
            else:
                failed.append(criterion_text)

        is_acceptable = len(failed) == 0
        return is_acceptable, passed, failed

    def _determine_next_action(
        self, is_acceptable: bool, retry_count: int, max_retries: int
    ) -> Dict[str, Any]:
        """
        次アクションの決定
        """
        if is_acceptable:
            return {
                "action": "deploy",
                "reason": "Model meets all acceptance criteria",
                "notify_operator": False,
            }

        if retry_count < max_retries:
            return {
                "action": "retry",
                "reason": f"Model does not meet criteria. Retry {retry_count + 1}/{max_retries}",
                "notify_operator": True,
            }

        return {
            "action": "abort",
            "reason": f"Model failed after {max_retries} retries. Manual intervention required.",
            "notify_operator": True,
        }

    def _create_notification_message(
        self,
        training_id: str,
        failed_criteria: List[str],
        retry_count: int,
        max_retries: int,
        event: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        オペレータ向け通知メッセージの生成
        """
        message_lines = [
            "🚨 **モデル評価結果: 不合格**",
            "",
            f"**Training ID**: `{training_id}`",
            f"**リトライ回数**: {retry_count + 1}/{max_retries}",
            "",
            "**失敗した基準**:",
        ]

        for criterion in failed_criteria:
            message_lines.append(f"- {criterion}")

        message_lines.extend(
            [
                "",
                "**推奨アクション**:",
                "1. ハイパーパラメータの調整（学習率、正則化パラメータ等）",
                "2. データ拡張の追加",
                "3. クラス不均衡対策の強化（SMOTE、クラスウェイト調整等）",
                "4. 特徴量エンジニアリングの見直し",
                "",
                "GitHub Issueにコメントして調整内容を指示してください:",
                f"{event.get('github_issue_url', 'N/A')}",
            ]
        )

        return {
            "message": "\n".join(message_lines),
            "channels": event.get("notification_channels", ["slack", "github"]),
        }


def lambda_handler(event, context):
    """
    Lambda関数のエントリーポイント
    """
    try:
        judge_agent = JudgeAgent()
        result = judge_agent.judge_model(event)

        return {"statusCode": 200, "body": result}

    except Exception as e:
        logger.error(f"Error in Judge Agent: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "body": {"error": str(e), "training_id": event.get("training_id", "unknown")},
        }
