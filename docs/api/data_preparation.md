# Data Preparation Capability

データ前処理・特徴量エンジニアリングを担当する Capability。

## ツール一覧

| ツール名 | 説明 |
|---------|------|
| `load_dataset` | S3からデータセットを読み込む |
| `validate_data` | データのバリデーションを実行 |
| `preprocess_supervised` | 教師あり学習用のデータ前処理を実行 |

## ツール詳細

### load_dataset

S3からデータセットを読み込む。

```python
load_dataset(
    s3_uri: str,
    file_format: str = "csv",
) -> Dict[str, Any]
```

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|---|:---:|----------|------|
| s3_uri | str | o | - | S3 URI（s3://bucket/key） |
| file_format | str | | "csv" | ファイル形式（csv/parquet） |

---

### validate_data

データのバリデーションを実行する。

```python
validate_data(
    s3_uri: str,
    file_format: str = "csv",
    required_columns: List[str] = None,
    max_missing_ratio: float = 0.5,
) -> Dict[str, Any]
```

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|---|:---:|----------|------|
| s3_uri | str | o | - | データのS3 URI |
| file_format | str | | "csv" | ファイル形式 |
| required_columns | List[str] | | None | 必須カラムリスト |
| max_missing_ratio | float | | 0.5 | 許容する最大欠損率 |

---

### preprocess_supervised

教師あり学習用のデータ前処理を実行する。

```python
preprocess_supervised(
    s3_uri: str,
    target_column: str,
    task_type: Literal["classification", "regression"] = "classification",
    file_format: str = "csv",
    test_size: float = 0.2,
    normalize: bool = True,
    handle_missing: str = "drop",
    encode_categorical: bool = True,
    output_s3_uri: Optional[str] = None,
    output_format: Literal["csv", "parquet"] = "csv",
    random_state: int = 42,
) -> Dict[str, Any]
```

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|---|:---:|----------|------|
| s3_uri | str | o | - | 入力データのS3 URI |
| target_column | str | o | - | 目的変数カラム名 |
| task_type | str | | "classification" | タスク種別 |
| file_format | str | | "csv" | 入力ファイル形式 |
| test_size | float | | 0.2 | テストデータ割合 |
| normalize | bool | | True | 正規化実行 |
| handle_missing | str | | "drop" | 欠損値処理方法 |
| encode_categorical | bool | | True | カテゴリエンコーディング |
| output_s3_uri | str | | None | 出力先S3 URI |
| output_format | str | | "csv" | 出力形式 |
| random_state | int | | 42 | 乱数シード |
