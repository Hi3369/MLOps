# Model Registry Capability

モデルバージョン管理を担当する Capability。

## ツール一覧

| ツール名 | 説明 |
|---------|------|
| `register_model` | モデルをレジストリに登録 |
| `list_models` | 登録モデルを一覧表示 |
| `get_model` | モデル情報を取得 |
| `update_model_status` | モデルステータスを更新 |
| `delete_model` | モデルを削除 |

## ツール詳細

### register_model

```python
register_model(
    model_s3_uri: str,
    model_name: str,
    model_version: str = None,
    metadata: Dict[str, Any] = None,
    tags: Dict[str, str] = None,
) -> Dict[str, Any]
```

### list_models

```python
list_models(
    registry_s3_uri: str,
    status_filter: str = None,
) -> Dict[str, Any]
```

### get_model

```python
get_model(model_s3_uri: str) -> Dict[str, Any]
```

### update_model_status

```python
update_model_status(
    model_s3_uri: str,
    status: str,  # registered/approved/deployed/archived/rejected
) -> Dict[str, Any]
```

### delete_model

```python
delete_model(
    model_s3_uri: str,
    delete_metadata: bool = True,
) -> Dict[str, Any]
```
