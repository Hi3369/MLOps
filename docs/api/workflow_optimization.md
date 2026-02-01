# Workflow Optimization Capability

モデル特性分析・最適化提案を担当する Capability。

## ツール一覧

| ツール名 | 説明 |
|---------|------|
| `analyze_model_characteristics` | モデル特性を分析 |
| `generate_optimization_proposal` | 最適化提案を生成 |
| `retrieve_similar_model_history` | 類似モデルの履歴を取得 |
| `apply_optimizations` | 最適化を適用 |
| `track_optimization_history` | 最適化履歴を記録 |

## ツール詳細

### analyze_model_characteristics

```python
analyze_model_characteristics(
    model_config: Dict[str, Any],
    dataset_info: Dict[str, Any] = None,
) -> Dict[str, Any]
```

### generate_optimization_proposal

```python
generate_optimization_proposal(
    model_characteristics: Dict[str, Any],
    constraints: Dict[str, Any] = None,
) -> Dict[str, Any]
```

### retrieve_similar_model_history

```python
retrieve_similar_model_history(
    model_type: str,
    dataset_size: int = None,
    limit: int = 10,
) -> Dict[str, Any]
```

### apply_optimizations

```python
apply_optimizations(
    optimization_proposal: Dict[str, Any],
    target_config: Dict[str, Any],
) -> Dict[str, Any]
```

### track_optimization_history

```python
track_optimization_history(
    optimization_id: str,
    results: Dict[str, Any],
) -> Dict[str, Any]
```
