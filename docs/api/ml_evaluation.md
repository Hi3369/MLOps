# ML Evaluation Capability

モデル評価・SHAP/LIME解釈性分析を担当する Capability。

## ツール一覧

| ツール名 | 説明 |
|---------|------|
| `evaluate_classification` | 分類モデルを評価 |
| `evaluate_regression` | 回帰モデルを評価 |
| `evaluate_clustering` | クラスタリングモデルを評価 |
| `calculate_shap_values` | SHAP値を計算 |
| `calculate_lime_explanation` | LIME説明を計算 |

## ツール詳細

### evaluate_classification

分類モデルを評価する（Accuracy, Precision, Recall, F1, AUC-ROC）。

```python
evaluate_classification(
    model_s3_uri: str,
    test_data_s3_uri: str,
    file_format: str = "csv",
    average: str = "weighted",
) -> Dict[str, Any]
```

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|---|:---:|----------|------|
| model_s3_uri | str | o | - | モデルのS3 URI |
| test_data_s3_uri | str | o | - | テストデータのS3 URI |
| file_format | str | | "csv" | データ形式 |
| average | str | | "weighted" | 平均方法（weighted/macro/micro） |

---

### evaluate_regression

回帰モデルを評価する（RMSE, MAE, R2, MAPE）。

```python
evaluate_regression(
    model_s3_uri: str,
    test_data_s3_uri: str,
    file_format: str = "csv",
) -> Dict[str, Any]
```

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|---|:---:|----------|------|
| model_s3_uri | str | o | - | モデルのS3 URI |
| test_data_s3_uri | str | o | - | テストデータのS3 URI |
| file_format | str | | "csv" | データ形式 |

---

### evaluate_clustering

クラスタリングモデルを評価する（Silhouette Score, Davies-Bouldin Index）。

```python
evaluate_clustering(
    model_s3_uri: str,
    test_data_s3_uri: str,
    file_format: str = "csv",
) -> Dict[str, Any]
```

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|---|:---:|----------|------|
| model_s3_uri | str | o | - | モデルのS3 URI |
| test_data_s3_uri | str | o | - | テストデータのS3 URI |
| file_format | str | | "csv" | データ形式 |

---

### calculate_shap_values

SHAP値を計算してモデルの予測を説明する。

```python
calculate_shap_values(
    model_s3_uri: str,
    data_s3_uri: str,
    explainer_type: str = "auto",
    background_samples: int = 100,
    max_samples: Optional[int] = None,
    file_format: str = "csv",
) -> Dict[str, Any]
```

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|---|:---:|----------|------|
| model_s3_uri | str | o | - | モデルのS3 URI |
| data_s3_uri | str | o | - | 説明対象データのS3 URI |
| explainer_type | str | | "auto" | Explainerタイプ（auto/tree/kernel/deep） |
| background_samples | int | | 100 | バックグラウンドサンプル数 |
| max_samples | int | | None | 最大サンプル数 |
| file_format | str | | "csv" | データ形式 |

---

### calculate_lime_explanation

LIMEによる局所的説明を計算する。

```python
calculate_lime_explanation(
    model_s3_uri: str,
    data_s3_uri: str,
    instance_index: int = 0,
    num_features: int = 10,
    num_samples: int = 5000,
    file_format: str = "csv",
) -> Dict[str, Any]
```

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|---|:---:|----------|------|
| model_s3_uri | str | o | - | モデルのS3 URI |
| data_s3_uri | str | o | - | 説明対象データのS3 URI |
| instance_index | int | | 0 | 説明対象インスタンスのインデックス |
| num_features | int | | 10 | 表示する特徴量数 |
| num_samples | int | | 5000 | 摂動サンプル数 |
| file_format | str | | "csv" | データ形式 |
