# Experiment Tracking Capability

実験追跡・比較を担当する Capability。

## ツール一覧

| ツール名 | 説明 |
|---------|------|
| `start_experiment` | 実験を開始 |
| `log_parameters` | パラメータを記録 |
| `log_metrics` | メトリクスを記録 |
| `compare_experiments` | 実験を比較 |

## ツール詳細

### start_experiment

新しい実験を開始する。

```python
start_experiment(
    experiment_name: str,
    description: str = "",
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    s3_bucket: Optional[str] = None,
) -> Dict[str, Any]
```

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|---|:---:|----------|------|
| experiment_name | str | o | - | 実験名（英数字・ハイフン・アンダースコア・ドット、256文字以内） |
| description | str | | "" | 実験の説明 |
| tags | List[str] | | None | タグリスト |
| metadata | Dict | | None | メタデータ |
| s3_bucket | str | | None | データ保存先S3バケット |

**レスポンス例:**

```python
{
    "status": "success",
    "message": "Experiment started: my-experiment",
    "experiment_info": {
        "experiment_id": "exp-a1b2c3d4",
        "experiment_name": "my-experiment",
        "status": "running",
        "tags": ["classification"],
        "created_at": "2026-01-31T00:00:00+00:00"
    }
}
```

---

### log_parameters

実験にパラメータを記録する。

```python
log_parameters(
    experiment_id: str,
    parameters: Dict[str, Any],
    run_name: Optional[str] = None,
    step: Optional[int] = None,
) -> Dict[str, Any]
```

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|---|:---:|----------|------|
| experiment_id | str | o | - | 実験ID |
| parameters | Dict[str, Any] | o | - | パラメータ辞書（値: str/int/float/bool/list） |
| run_name | str | | None | ラン名（自動生成可） |
| step | int | | None | ステップ番号 |

---

### log_metrics

実験にメトリクスを記録する。

```python
log_metrics(
    experiment_id: str,
    metrics: Dict[str, Any],
    run_name: Optional[str] = None,
    step: Optional[int] = None,
    epoch: Optional[int] = None,
) -> Dict[str, Any]
```

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|---|:---:|----------|------|
| experiment_id | str | o | - | 実験ID |
| metrics | Dict[str, Any] | o | - | メトリクス辞書（値: int/float のみ） |
| run_name | str | | None | ラン名 |
| step | int | | None | ステップ番号 |
| epoch | int | | None | エポック番号 |

---

### compare_experiments

複数の実験を比較する。

```python
compare_experiments(
    experiment_ids: List[str],
    metric_names: Optional[List[str]] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "descending",
) -> Dict[str, Any]
```

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|---|:---:|----------|------|
| experiment_ids | List[str] | o | - | 実験IDリスト（2〜10個） |
| metric_names | List[str] | | None | 比較するメトリクス名 |
| sort_by | str | | None | ソートキー（メトリクス名） |
| sort_order | str | | "descending" | ソート順（ascending/descending） |
