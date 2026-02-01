# ML Training Capability

モデル学習・ハイパーパラメータ最適化を担当する Capability。

## ツール一覧

| ツール名 | 説明 |
|---------|------|
| `train_classification` | 分類モデルを学習 |
| `train_regression` | 回帰モデルを学習 |
| `train_clustering` | クラスタリングモデルを学習 |

## ツール詳細

### train_classification

分類モデルを学習する。

```python
train_classification(
    train_data_s3_uri: str,
    algorithm: str = "random_forest",
    hyperparameters: Dict[str, Any] = None,
    model_output_s3_uri: str = None,
    file_format: str = "csv",
    validation_data_s3_uri: str = None,
) -> Dict[str, Any]
```

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|---|:---:|----------|------|
| train_data_s3_uri | str | o | - | 学習データのS3 URI |
| algorithm | str | | "random_forest" | アルゴリズム（random_forest/logistic_regression/neural_network） |
| hyperparameters | Dict | | None | ハイパーパラメータ |
| model_output_s3_uri | str | | None | モデル出力先S3 URI |
| file_format | str | | "csv" | データ形式 |
| validation_data_s3_uri | str | | None | バリデーションデータS3 URI |

---

### train_regression

回帰モデルを学習する。

```python
train_regression(
    train_data_s3_uri: str,
    algorithm: str = "random_forest",
    hyperparameters: Dict[str, Any] = None,
    model_output_s3_uri: str = None,
    file_format: str = "csv",
    validation_data_s3_uri: str = None,
) -> Dict[str, Any]
```

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|---|:---:|----------|------|
| train_data_s3_uri | str | o | - | 学習データのS3 URI |
| algorithm | str | | "random_forest" | アルゴリズム（random_forest/linear_regression/ridge） |
| hyperparameters | Dict | | None | ハイパーパラメータ |
| model_output_s3_uri | str | | None | モデル出力先S3 URI |
| file_format | str | | "csv" | データ形式 |
| validation_data_s3_uri | str | | None | バリデーションデータS3 URI |

---

### train_clustering

クラスタリングモデルを学習する。

```python
train_clustering(
    train_data_s3_uri: str,
    algorithm: str = "kmeans",
    hyperparameters: Dict[str, Any] = None,
    model_output_s3_uri: str = None,
    file_format: str = "csv",
) -> Dict[str, Any]
```

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|---|:---:|----------|------|
| train_data_s3_uri | str | o | - | 学習データのS3 URI |
| algorithm | str | | "kmeans" | アルゴリズム（kmeans/dbscan） |
| hyperparameters | Dict | | None | ハイパーパラメータ |
| model_output_s3_uri | str | | None | モデル出力先S3 URI |
| file_format | str | | "csv" | データ形式 |
