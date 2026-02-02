"""
Send GitHub Notification Tool

GitHub Issue/PRコメント通知ツール
"""

import json
import logging
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


def send_github_notification(
    repo_owner: str,
    repo_name: str,
    notification_type: str,
    target_number: int,
    message: str,
    labels: Optional[list] = None,
    assignees: Optional[list] = None,
) -> Dict[str, Any]:
    """
    GitHub Issue/PRに通知（コメント）を送信

    Args:
        repo_owner: リポジトリオーナー
        repo_name: リポジトリ名
        notification_type: 通知タイプ（issue_comment, pr_comment, issue_create）
        target_number: Issue/PR番号（issue_createの場合は0）
        message: 通知メッセージ
        labels: ラベルリスト（issue_createの場合）
        assignees: アサイニーリスト（issue_createの場合）

    Returns:
        送信結果辞書
    """
    logger.info(f"Sending GitHub notification: {notification_type} to {repo_owner}/{repo_name}")

    # パラメータ検証
    if not repo_owner:
        raise ValueError("repo_owner must not be empty")

    if not repo_name:
        raise ValueError("repo_name must not be empty")

    if not message:
        raise ValueError("message must not be empty")

    valid_types = ["issue_comment", "pr_comment", "issue_create"]
    if notification_type not in valid_types:
        raise ValueError(
            f"notification_type must be one of {valid_types}, got: {notification_type}"
        )

    if notification_type in ["issue_comment", "pr_comment"] and target_number <= 0:
        raise ValueError(
            f"target_number must be positive for {notification_type}, got: {target_number}"
        )

    try:
        env = os.environ.get("MLOPS_ENV", "development")
        github_token = os.environ.get("GITHUB_TOKEN")

        # 開発/テスト環境ではモックデータを返す
        if env in ["development", "test"] or not github_token:
            logger.info("Using mock GitHub notification (dev/test environment)")
            return _mock_github_notification(
                repo_owner=repo_owner,
                repo_name=repo_name,
                notification_type=notification_type,
                target_number=target_number,
                message=message,
                labels=labels,
                assignees=assignees,
            )

        # 本番環境：GitHub APIを呼び出す
        return _send_real_github_notification(
            github_token=github_token,
            repo_owner=repo_owner,
            repo_name=repo_name,
            notification_type=notification_type,
            target_number=target_number,
            message=message,
            labels=labels,
            assignees=assignees,
        )

    except Exception as e:
        logger.error(f"GitHub notification error: {e}")
        raise ValueError(f"Failed to send GitHub notification: {e}")


def _mock_github_notification(
    repo_owner: str,
    repo_name: str,
    notification_type: str,
    target_number: int,
    message: str,
    labels: Optional[list],
    assignees: Optional[list],
) -> Dict[str, Any]:
    """モックGitHub通知"""
    notification_id = str(uuid4())[:8]

    notification_result: Dict[str, Any] = {
        "notification_id": f"mock-gh-{notification_id}",
        "repo": f"{repo_owner}/{repo_name}",
        "notification_type": notification_type,
        "message_preview": message[:100] + "..." if len(message) > 100 else message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mock": True,
    }

    if notification_type == "issue_create":
        notification_result["issue_number"] = 999  # mock issue number
        notification_result["issue_url"] = f"https://github.com/{repo_owner}/{repo_name}/issues/999"
        if labels:
            notification_result["labels"] = labels
        if assignees:
            notification_result["assignees"] = assignees
    else:
        notification_result["target_number"] = target_number
        notification_result["comment_url"] = (
            f"https://github.com/{repo_owner}/{repo_name}/issues/{target_number}#issuecomment-mock"
        )

    return {
        "status": "success",
        "message": f"GitHub {notification_type} sent (mock)",
        "notification_result": notification_result,
    }


def _send_real_github_notification(
    github_token: str,
    repo_owner: str,
    repo_name: str,
    notification_type: str,
    target_number: int,
    message: str,
    labels: Optional[list],
    assignees: Optional[list],
) -> Dict[str, Any]:
    """GitHub APIを使用した実際の通知送信"""
    base_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    }

    if notification_type == "issue_comment":
        url = f"{base_url}/issues/{target_number}/comments"
        payload: Dict[str, Any] = {"body": message}
    elif notification_type == "pr_comment":
        url = f"{base_url}/issues/{target_number}/comments"  # PRコメントもissues APIを使用
        payload = {"body": message}
    elif notification_type == "issue_create":
        url = f"{base_url}/issues"
        # message をタイトルと本文に分割（最初の行がタイトル）
        lines = message.strip().split("\n", 1)
        title = lines[0]
        body = lines[1].strip() if len(lines) > 1 else ""
        payload = {"title": title, "body": body}
        if labels:
            payload["labels"] = labels
        if assignees:
            payload["assignees"] = assignees
    else:
        raise ValueError(f"Unknown notification type: {notification_type}")

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        assert url.startswith("https://"), "URL must use HTTPS"  # nosec B310
        with urllib.request.urlopen(req, timeout=30) as response:  # nosec B310
            response_data = json.loads(response.read().decode("utf-8"))

            notification_result: Dict[str, Any] = {
                "repo": f"{repo_owner}/{repo_name}",
                "notification_type": notification_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            if notification_type == "issue_create":
                notification_result["issue_number"] = response_data["number"]
                notification_result["issue_url"] = response_data["html_url"]
            else:
                notification_result["comment_id"] = response_data["id"]
                notification_result["comment_url"] = response_data["html_url"]
                notification_result["target_number"] = target_number

            return {
                "status": "success",
                "message": f"GitHub {notification_type} sent successfully",
                "notification_result": notification_result,
            }

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise ValueError(f"GitHub API error ({e.code}): {error_body}")
    except urllib.error.URLError as e:
        raise ValueError(f"Failed to connect to GitHub: {e}")
