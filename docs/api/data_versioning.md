# Data Versioning Capability

データバージョニング・リネージ追跡を担当する Capability。

## ツール一覧

| ツール名 | 説明 |
|---------|------|
| `version_dataset` | データセットバージョンを登録 |
| `get_dataset_lineage` | データセットリネージを追跡 |
| `compare_datasets` | データセットを比較 |

## ツール詳細

### version_dataset

データセットのバージョンを登録する。SHA256フィンガープリントを自動生成。

```python
version_dataset(
    dataset_name: str,
    s3_uri: str,
    version: str,
    description: str = "",
    schema: Optional[Dict[str, Any]] = None,
    tags: Optional[List[str]] = None,
    parent_version: Optional[str] = None,
    row_count: Optional[int] = None,
    file_format: str = "csv",
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]
```

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|---|:---:|----------|------|
| dataset_name | str | o | - | データセット名 |
| s3_uri | str | o | - | S3 URI（s3://で始まる） |
| version | str | o | - | バージョン文字列 |
| description | str | | "" | 説明 |
| schema | Dict | | None | スキーマ定義 |
| tags | List[str] | | None | タグリスト |
| parent_version | str | | None | 親バージョン |
| row_count | int | | None | 行数（0以上） |
| file_format | str | | "csv" | 形式（csv/parquet/json/orc/avro） |
| metadata | Dict | | None | メタデータ |

**レスポンス例:**

```python
{
    "status": "success",
    "message": "Dataset versioned: my-data v1.0.0",
    "version_info": {
        "version_id": "dv-a1b2c3d4",
        "dataset_name": "my-data",
        "version": "v1.0.0",
        "fingerprint": "a1b2c3d4e5f6g7h8",
        "lineage": {
            "parent_version": None,
            "created_from": "manual"
        }
    }
}
```

---

### get_dataset_lineage

データセットのリネージ（系譜）を追跡する。

```python
get_dataset_lineage(
    dataset_name: str,
    version: Optional[str] = None,
    depth: int = 5,
    include_transformations: bool = True,
) -> Dict[str, Any]
```

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|---|:---:|----------|------|
| dataset_name | str | o | - | データセット名 |
| version | str | | None | バージョン（省略時: latest） |
| depth | int | | 5 | 追跡の深さ（1〜20） |
| include_transformations | bool | | True | 変換履歴を含める |

---

### compare_datasets

2つのデータセットバージョンを比較する（スキーマ差分・統計差分・サンプル比較）。

```python
compare_datasets(
    dataset_name: str,
    version_a: str,
    version_b: str,
    compare_schema: bool = True,
    compare_statistics: bool = True,
    compare_sample: bool = False,
    sample_size: int = 100,
) -> Dict[str, Any]
```

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|---|:---:|----------|------|
| dataset_name | str | o | - | データセット名 |
| version_a | str | o | - | 比較元バージョン |
| version_b | str | o | - | 比較先バージョン（version_aと異なる必要あり） |
| compare_schema | bool | | True | スキーマ比較を実行 |
| compare_statistics | bool | | True | 統計比較を実行 |
| compare_sample | bool | | False | サンプル比較を実行 |
| sample_size | int | | 100 | サンプルサイズ（1〜10000） |
