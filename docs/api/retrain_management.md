# Retrain Management Capability

再学習トリガー管理を担当する Capability。

## ツール一覧

| ツール名 | 説明 |
|---------|------|
| `check_retrain_triggers` | 再学習トリガーをチェック |
| `evaluate_trigger_conditions` | トリガー条件を評価 |
| `create_retrain_issue` | 再学習Issueを作成 |
| `start_retrain_workflow` | 再学習ワークフローを起動 |
| `schedule_periodic_retrain` | 定期再学習をスケジュール |

## ツール詳細

### check_retrain_triggers

```python
check_retrain_triggers(
    model_name: str,
    trigger_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]
```

### evaluate_trigger_conditions

```python
evaluate_trigger_conditions(
    conditions: List[Dict[str, Any]],
    current_metrics: Dict[str, Any],
) -> Dict[str, Any]
```

### create_retrain_issue

```python
create_retrain_issue(
    model_name: str,
    reason: str,
    trigger_details: Optional[Dict[str, Any]] = None,
    repo_owner: Optional[str] = None,
    repo_name: Optional[str] = None,
) -> Dict[str, Any]
```

### start_retrain_workflow

```python
start_retrain_workflow(
    workflow_name: str,
    model_config: Dict[str, Any],
    dataset_uri: Optional[str] = None,
    comparison_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]
```

### schedule_periodic_retrain

```python
schedule_periodic_retrain(
    model_name: str,
    schedule_expression: str,  # cron式 or rate式
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]
```
