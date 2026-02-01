# Notification Capability

Slack/Email/GitHub への通知送信を担当する Capability。

## ツール一覧

| ツール名 | 説明 |
|---------|------|
| `send_slack_notification` | Slackに通知を送信 |
| `send_email_notification` | Email通知を送信（SES） |
| `send_github_notification` | GitHub Issue/PRに通知 |
| `apply_notification_template` | 通知テンプレートを適用 |
| `list_available_templates` | テンプレート一覧を取得 |

## ツール詳細

### send_slack_notification

```python
send_slack_notification(
    message: str,
    channel: str = "#mlops-notifications",
    username: str = "MLOps Bot",
    icon_emoji: str = ":robot_face:",
    attachments: Optional[list] = None,
    blocks: Optional[list] = None,
) -> Dict[str, Any]
```

### send_email_notification

```python
send_email_notification(
    to_addresses: List[str],
    subject: str,
    body: str,
    from_address: Optional[str] = None,
    cc_addresses: Optional[List[str]] = None,
    bcc_addresses: Optional[List[str]] = None,
    html_body: Optional[str] = None,
    reply_to: Optional[List[str]] = None,
) -> Dict[str, Any]
```

### send_github_notification

```python
send_github_notification(
    repo_owner: str,
    repo_name: str,
    notification_type: str,  # issue_comment/pr_comment
    target_number: int,
    message: str,
    labels: Optional[list] = None,
    assignees: Optional[list] = None,
) -> Dict[str, Any]
```

### apply_notification_template

```python
apply_notification_template(
    template_name: str,
    variables: Dict[str, Any],
    custom_template: Optional[Dict[str, str]] = None,
    output_format: str = "all",
) -> Dict[str, Any]
```

### list_available_templates

```python
list_available_templates() -> Dict[str, Any]
```
