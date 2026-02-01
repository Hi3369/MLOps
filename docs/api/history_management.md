# History Management Capability

学習履歴記録・GitHub連携を担当する Capability。

## ツール一覧

| ツール名 | 説明 |
|---------|------|
| `format_training_history` | 学習結果をフォーマット |
| `save_training_history` | 履歴をストレージに保存 |
| `post_issue_comment` | GitHub Issueに進捗コメントを投稿 |
| `track_version_history` | モデルバージョン履歴を追跡 |

## ツール詳細

### format_training_history

```python
format_training_history(
    training_job_name: str,
    metrics: Dict[str, Any],
    hyperparameters: Optional[Dict[str, Any]] = None,
    model_name: Optional[str] = None,
    model_version: Optional[str] = None,
    dataset_info: Optional[Dict[str, Any]] = None,
    training_time_seconds: Optional[float] = None,
    instance_type: Optional[str] = None,
    output_format: str = "markdown",  # markdown/json/html
) -> Dict[str, Any]
```

### save_training_history

```python
save_training_history(
    training_job_name: str,
    formatted_history: str,
    storage_type: str = "s3",
    s3_bucket: Optional[str] = None,
    s3_prefix: str = "training_history/",
    local_path: Optional[str] = None,
    file_format: str = "md",
) -> Dict[str, Any]
```

### post_issue_comment

```python
post_issue_comment(
    repository: str,
    issue_number: int,
    comment: str,
    comment_type: str = "progress",  # progress/result/error
    include_timestamp: bool = True,
) -> Dict[str, Any]
```

### track_version_history

```python
track_version_history(
    model_name: str,
    version: str,
    metadata: Optional[Dict[str, Any]] = None,
    parent_version: Optional[str] = None,
    training_job_name: Optional[str] = None,
    training_data_version: Optional[str] = None,
    code_version: Optional[str] = None,
    status: str = "development",
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]
```
