"""
Detect MLOps Issue Tool

MLOps用Issue検知ツール
"""

import logging
import re
from typing import Any, Dict, List

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def detect_mlops_issue(
    repo_owner: str,
    repo_name: str,
    issue_number: int = None,
    labels: List[str] = None,
) -> Dict[str, Any]:
    """
    MLOps用Issueを検知

    Args:
        repo_owner: リポジトリオーナー
        repo_name: リポジトリ名
        issue_number: Issue番号（指定時は単一Issue取得）
        labels: フィルタリングするラベル（mlops, training等）

    Returns:
        検知されたIssue情報辞書
    """
    logger.info(f"Detecting MLOps issue: {repo_owner}/{repo_name}")

    # パラメータ検証
    if not repo_owner:
        raise ValueError("repo_owner must not be empty")

    if not repo_name:
        raise ValueError("repo_name must not be empty")

    try:
        # SSMからGitHub tokenを取得試行
        github_token = _get_github_token()

        if github_token:
            return _detect_via_github_api(repo_owner, repo_name, issue_number, labels, github_token)
        else:
            # トークンがない場合はモックデータを返す
            logger.warning("GitHub token not available, returning mock data")
            return _get_mock_issue_data(repo_owner, repo_name, issue_number, labels)

    except Exception as e:
        logger.error(f"MLOps issue detection error: {e}")
        # エラー時はモックデータを返す
        logger.warning("Returning mock data due to error")
        return _get_mock_issue_data(repo_owner, repo_name, issue_number, labels)


def _get_github_token() -> str:
    """SSMからGitHub tokenを取得"""
    try:
        ssm = boto3.client("ssm")
        response = ssm.get_parameter(
            Name="/mlops/github/token",
            WithDecryption=True,
        )
        return response["Parameter"]["Value"]
    except ClientError as e:
        logger.warning(f"Failed to get GitHub token from SSM: {e}")
        return None
    except Exception as e:
        logger.warning(f"GitHub token retrieval error: {e}")
        return None


def _detect_via_github_api(
    repo_owner: str,
    repo_name: str,
    issue_number: int,
    labels: List[str],
    github_token: str,
) -> Dict[str, Any]:
    """GitHub APIを使用してIssueを検知"""
    import urllib.request
    import json

    base_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues"

    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "MLOps-MCP-Server",
    }

    try:
        if issue_number:
            # 単一Issue取得
            url = f"{base_url}/{issue_number}"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                issue_data = json.loads(response.read().decode())
                issues = [_parse_github_issue(issue_data)]
        else:
            # Issue一覧取得
            url = base_url
            if labels:
                url += f"?labels={','.join(labels)}&state=open"
            else:
                url += "?state=open"

            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                issues_data = json.loads(response.read().decode())
                issues = [_parse_github_issue(issue) for issue in issues_data]

        # MLOpsラベルでフィルタリング
        mlops_issues = _filter_mlops_issues(issues, labels)

        return {
            "status": "success",
            "message": f"Detected {len(mlops_issues)} MLOps issues",
            "detection_result": {
                "repo_owner": repo_owner,
                "repo_name": repo_name,
                "total_issues": len(mlops_issues),
                "issues": mlops_issues,
            },
        }

    except urllib.error.HTTPError as e:
        logger.error(f"GitHub API error: {e}")
        raise ValueError(f"GitHub API error: {e}")


def _parse_github_issue(issue_data: Dict[str, Any]) -> Dict[str, Any]:
    """GitHub Issue データをパース"""
    return {
        "issue_number": issue_data.get("number"),
        "title": issue_data.get("title"),
        "body": issue_data.get("body", ""),
        "state": issue_data.get("state"),
        "labels": [label.get("name") for label in issue_data.get("labels", [])],
        "created_at": issue_data.get("created_at"),
        "updated_at": issue_data.get("updated_at"),
        "user": issue_data.get("user", {}).get("login"),
        "html_url": issue_data.get("html_url"),
    }


def _filter_mlops_issues(
    issues: List[Dict[str, Any]], labels: List[str] = None
) -> List[Dict[str, Any]]:
    """MLOps関連のIssueをフィルタリング"""
    mlops_labels = labels or ["mlops", "training", "model", "ml-training"]
    mlops_keywords = ["training", "model", "dataset", "hyperparameter", "mlops"]

    filtered = []
    for issue in issues:
        issue_labels = issue.get("labels", [])
        title = issue.get("title", "").lower()
        body = issue.get("body", "").lower()

        # ラベルマッチ
        has_mlops_label = any(
            label.lower() in [lbl.lower() for lbl in mlops_labels] for label in issue_labels
        )

        # キーワードマッチ
        has_mlops_keyword = any(keyword in title or keyword in body for keyword in mlops_keywords)

        # MLOps設定ブロック検出
        has_config_block = _detect_config_block(issue.get("body", ""))

        if has_mlops_label or has_mlops_keyword or has_config_block:
            issue["is_mlops_issue"] = True
            issue["detection_reason"] = []
            if has_mlops_label:
                issue["detection_reason"].append("mlops_label")
            if has_mlops_keyword:
                issue["detection_reason"].append("mlops_keyword")
            if has_config_block:
                issue["detection_reason"].append("config_block")
            filtered.append(issue)

    return filtered


def _detect_config_block(body: str) -> bool:
    """Issue本文からMLOps設定ブロックを検出"""
    if not body:
        return False

    # YAML/JSON設定ブロックのパターン
    yaml_pattern = r"```ya?ml\s*\n.*?(training|model|dataset).*?```"
    json_pattern = r"```json\s*\n.*?(training|model|dataset).*?```"

    yaml_match = re.search(yaml_pattern, body, re.DOTALL | re.IGNORECASE)
    json_match = re.search(json_pattern, body, re.DOTALL | re.IGNORECASE)

    return bool(yaml_match or json_match)


def _get_mock_issue_data(
    repo_owner: str,
    repo_name: str,
    issue_number: int,
    labels: List[str],
) -> Dict[str, Any]:
    """モックデータを返す（開発・テスト用）"""
    logger.info("Returning mock MLOps issue data")

    mock_issues = [
        {
            "issue_number": issue_number or 123,
            "title": "Request ML Training: Customer Churn Prediction Model",
            "body": """## Training Request

```yaml
training_config:
  model_type: xgboost
  dataset:
    s3_path: s3://mlops-data/churn-prediction/
    target_column: churned
  hyperparameters:
    n_estimators: 100
    max_depth: 6
    learning_rate: 0.1
```

Please train a customer churn prediction model using the above configuration.
""",
            "state": "open",
            "labels": ["mlops", "training", "high-priority"],
            "created_at": "2025-01-10T10:00:00Z",
            "updated_at": "2025-01-10T10:00:00Z",
            "user": "ml-engineer",
            "html_url": f"https://github.com/{repo_owner}/{repo_name}/issues/{issue_number or 123}",
            "is_mlops_issue": True,
            "detection_reason": ["mlops_label", "config_block"],
        },
    ]

    if not issue_number:
        # 追加のモックIssue
        mock_issues.append(
            {
                "issue_number": 124,
                "title": "Update model hyperparameters for better accuracy",
                "body": "Need to tune hyperparameters for the recommendation model.",
                "state": "open",
                "labels": ["model", "optimization"],
                "created_at": "2025-01-09T15:30:00Z",
                "updated_at": "2025-01-09T16:00:00Z",
                "user": "data-scientist",
                "html_url": f"https://github.com/{repo_owner}/{repo_name}/issues/124",
                "is_mlops_issue": True,
                "detection_reason": ["mlops_keyword"],
            }
        )

    return {
        "status": "success",
        "message": f"Detected {len(mock_issues)} MLOps issues (mock data)",
        "detection_result": {
            "repo_owner": repo_owner,
            "repo_name": repo_name,
            "total_issues": len(mock_issues),
            "issues": mock_issues,
            "is_mock_data": True,
        },
    }
