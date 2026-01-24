"""
Post Issue Comment Tool

GitHub Issue コメント投稿ツール
"""

import json
import logging
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4

logger = logging.getLogger(__name__)


def post_issue_comment(
    repository: str,
    issue_number: int,
    comment: str,
    comment_type: str = "progress",
    include_timestamp: bool = True,
) -> Dict[str, Any]:
    """
    GitHub Issueに進捗コメントを投稿

    Args:
        repository: リポジトリ（owner/repo形式）
        issue_number: Issue番号
        comment: コメント本文
        comment_type: コメントタイプ（progress, result, error, info）
        include_timestamp: タイムスタンプを含めるか

    Returns:
        投稿結果辞書
    """
    logger.info(f"Posting comment to {repository}#{issue_number}")

    # パラメータ検証
    if not repository:
        raise ValueError("repository must not be empty")

    if "/" not in repository:
        raise ValueError("repository must be in 'owner/repo' format")

    if issue_number <= 0:
        raise ValueError("issue_number must be positive")

    if not comment:
        raise ValueError("comment must not be empty")

    if comment_type not in ["progress", "result", "error", "info"]:
        raise ValueError(f"Invalid comment_type: {comment_type}")

    try:
        timestamp = datetime.now(timezone.utc).isoformat()
        comment_id = str(uuid4())[:8]

        # コメント本文を構築
        formatted_comment = _format_comment(
            comment=comment,
            comment_type=comment_type,
            include_timestamp=include_timestamp,
            timestamp=timestamp,
        )

        env = os.environ.get("MLOPS_ENV", "development")
        github_token = os.environ.get("GITHUB_TOKEN")

        # 開発/テスト環境ではモック
        if env in ["development", "test"] or not github_token:
            logger.info("Using mock GitHub comment (dev/test environment)")
            return _mock_post_comment(
                repository=repository,
                issue_number=issue_number,
                formatted_comment=formatted_comment,
                comment_type=comment_type,
                comment_id=comment_id,
                timestamp=timestamp,
            )

        # 本番環境：実際にGitHub APIを呼び出す
        return _real_post_comment(
            repository=repository,
            issue_number=issue_number,
            formatted_comment=formatted_comment,
            comment_type=comment_type,
            comment_id=comment_id,
            timestamp=timestamp,
            github_token=github_token,
        )

    except Exception as e:
        logger.error(f"Failed to post issue comment: {e}")
        raise ValueError(f"Failed to post issue comment: {e}")


def _format_comment(
    comment: str,
    comment_type: str,
    include_timestamp: bool,
    timestamp: str,
) -> str:
    """コメントをフォーマット"""
    # タイプ別のアイコン
    type_icons = {
        "progress": "🔄",
        "result": "✅",
        "error": "❌",
        "info": "ℹ️",
    }

    icon = type_icons.get(comment_type, "📝")
    lines = [f"{icon} **{comment_type.upper()}**", ""]

    if include_timestamp:
        lines.append(f"*Timestamp: {timestamp}*")
        lines.append("")

    lines.append(comment)

    return "\n".join(lines)


def _mock_post_comment(
    repository: str,
    issue_number: int,
    formatted_comment: str,
    comment_type: str,
    comment_id: str,
    timestamp: str,
) -> Dict[str, Any]:
    """モックコメント投稿"""
    return {
        "status": "success",
        "message": "Issue comment posted (mock)",
        "comment_result": {
            "comment_id": f"mock-comment-{comment_id}",
            "repository": repository,
            "issue_number": issue_number,
            "comment_type": comment_type,
            "comment_preview": (
                formatted_comment[:200] + "..."
                if len(formatted_comment) > 200
                else formatted_comment
            ),
            "html_url": f"https://github.com/{repository}/issues/{issue_number}#issuecomment-mock-{comment_id}",
            "timestamp": timestamp,
            "mock": True,
        },
    }


def _real_post_comment(
    repository: str,
    issue_number: int,
    formatted_comment: str,
    comment_type: str,
    comment_id: str,
    timestamp: str,
    github_token: str,
) -> Dict[str, Any]:
    """実際のGitHub APIでコメント投稿"""
    api_url = f"https://api.github.com/repos/{repository}/issues/{issue_number}/comments"

    payload = {"body": formatted_comment}
    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        api_url,
        data=data,
        headers={
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {github_token}",
            "Content-Type": "application/json",
            "User-Agent": "MLOps-MCP-Server",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            response_data = json.loads(response.read().decode("utf-8"))

            return {
                "status": "success",
                "message": "Issue comment posted successfully",
                "comment_result": {
                    "comment_id": str(response_data.get("id", comment_id)),
                    "repository": repository,
                    "issue_number": issue_number,
                    "comment_type": comment_type,
                    "html_url": response_data.get("html_url", ""),
                    "timestamp": timestamp,
                    "mock": False,
                },
            }

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        raise ValueError(f"GitHub API error ({e.code}): {error_body}")
    except urllib.error.URLError as e:
        raise ValueError(f"Failed to connect to GitHub: {e}")
