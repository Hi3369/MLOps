# Model Monitoring Capability

パフォーマンス監視・ドリフト検出・アラート管理を担当する Capability。

## ツール一覧

| ツール名 | 説明 |
|---------|------|
| `collect_system_metrics` | システムメトリクスを収集 |
| `collect_model_metrics` | モデルメトリクスを収集 |
| `detect_data_drift` | データドリフトを検出 |
| `detect_concept_drift` | コンセプトドリフトを検出 |
| `create_cloudwatch_alarm` | CloudWatchアラームを作成 |
| `delete_cloudwatch_alarm` | アラームを削除 |
| `get_alarm_state` | アラーム状態を取得 |
| `create_monitoring_dashboard` | 監視ダッシュボードを作成 |
| `update_dashboard` | ダッシュボードを更新 |
| `delete_dashboard` | ダッシュボードを削除 |

## ツール詳細

### detect_data_drift

データドリフトを検出する（KS検定/PSI）。

```python
detect_data_drift(
    baseline_data: Dict[str, List[float]],
    current_data: Dict[str, List[float]],
    drift_threshold: float = 0.05,
    method: str = "ks_test",
) -> Dict[str, Any]
```

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|---|:---:|----------|------|
| baseline_data | Dict[str, List[float]] | o | - | ベースラインデータ（特徴量名→値リスト） |
| current_data | Dict[str, List[float]] | o | - | 現在のデータ |
| drift_threshold | float | | 0.05 | ドリフト検出閾値 |
| method | str | | "ks_test" | 検定手法（ks_test/psi） |

---

### detect_concept_drift

コンセプトドリフトを検出する（予測精度の経時変化）。

```python
detect_concept_drift(
    predictions: List[Any],
    actual_labels: List[Any],
    window_size: int = 100,
    drift_threshold: float = 0.1,
) -> Dict[str, Any]
```

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|---|:---:|----------|------|
| predictions | List[Any] | o | - | 予測値リスト |
| actual_labels | List[Any] | o | - | 正解ラベルリスト |
| window_size | int | | 100 | ウィンドウサイズ |
| drift_threshold | float | | 0.1 | ドリフト検出閾値 |

---

### collect_system_metrics / collect_model_metrics

SageMakerエンドポイントのメトリクスを収集する。

```python
collect_system_metrics(
    endpoint_name: str,
    time_range_minutes: int = 60,
    metric_period_seconds: int = 300,
) -> Dict[str, Any]

collect_model_metrics(
    endpoint_name: str,
    time_range_minutes: int = 60,
    metric_period_seconds: int = 300,
) -> Dict[str, Any]
```

---

### create_cloudwatch_alarm

CloudWatchアラームを作成する。

```python
create_cloudwatch_alarm(
    alarm_name: str,
    endpoint_name: str,
    metric_name: str,
    threshold: float,
    comparison_operator: str = "GreaterThanThreshold",
    evaluation_periods: int = 2,
    period_seconds: int = 300,
    statistic: str = "Average",
    actions_enabled: bool = True,
    alarm_actions: Optional[List[str]] = None,
) -> Dict[str, Any]
```

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|---|:---:|----------|------|
| alarm_name | str | o | - | アラーム名 |
| endpoint_name | str | o | - | 対象エンドポイント |
| metric_name | str | o | - | メトリクス名 |
| threshold | float | o | - | 閾値 |
| comparison_operator | str | | "GreaterThanThreshold" | 比較演算子 |
| evaluation_periods | int | | 2 | 評価期間数 |
| period_seconds | int | | 300 | 期間（秒） |
| statistic | str | | "Average" | 統計量 |
| actions_enabled | bool | | True | アクション有効化 |
| alarm_actions | List[str] | | None | アクションARNリスト |

---

### delete_cloudwatch_alarm / get_alarm_state

```python
delete_cloudwatch_alarm(alarm_name: str) -> Dict[str, Any]
get_alarm_state(alarm_name: str) -> Dict[str, Any]
```

---

### create_monitoring_dashboard

モデル監視用ダッシュボードを作成する。

```python
create_monitoring_dashboard(
    dashboard_name: str,
    endpoint_name: str,
    region: str = "us-east-1",
) -> Dict[str, Any]
```

---

### update_dashboard / delete_dashboard

```python
update_dashboard(
    dashboard_name: str,
    dashboard_body: Dict[str, Any],
) -> Dict[str, Any]

delete_dashboard(dashboard_name: str) -> Dict[str, Any]
```
