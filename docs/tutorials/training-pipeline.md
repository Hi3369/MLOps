# 学習パイプラインチュートリアル

データ準備から学習・評価・モデル登録までの完全なMLパイプラインを構築する。

## パイプライン概要

```
データ読込 → バリデーション → 前処理 → 学習 → 評価 → SHAP分析 → レジストリ登録
```

## Step 1: サーバー初期化

```python
import os
os.environ["MLOPS_ENV"] = "development"

from mcp_server.server import MLOpsServer
server = MLOpsServer()
```

## Step 2: データ準備

### 2.1 データ読み込み

```python
load_result = server.call_tool(
    "data_preparation.load_dataset",
    {"s3_uri": "s3://mlops-data/iris/raw.csv", "file_format": "csv"}
)
dataset_info = load_result["result"]["dataset_info"]
print(f"行数: {dataset_info['row_count']}, 列数: {dataset_info['column_count']}")
```

### 2.2 バリデーション

```python
val_result = server.call_tool(
    "data_preparation.validate_data",
    {
        "s3_uri": "s3://mlops-data/iris/raw.csv",
        "required_columns": ["sepal_length", "sepal_width", "petal_length", "petal_width", "species"],
        "max_missing_ratio": 0.1,
    }
)
print(f"バリデーション: {val_result['result']['status']}")
```

### 2.3 前処理

```python
prep_result = server.call_tool(
    "data_preparation.preprocess_supervised",
    {
        "s3_uri": "s3://mlops-data/iris/raw.csv",
        "target_column": "species",
        "task_type": "classification",
        "test_size": 0.2,
        "normalize": True,
        "handle_missing": "drop",
        "random_state": 42,
    }
)
prep_info = prep_result["result"]["preprocessing_info"]
print(f"学習データ: {prep_info['train_samples']}件")
print(f"テストデータ: {prep_info['test_samples']}件")

train_uri = prep_info["output_s3_uris"]["train"]
test_uri = prep_info["output_s3_uris"]["test"]
```

## Step 3: モデル学習

### 3.1 分類モデル学習

```python
train_result = server.call_tool(
    "ml_training.train_classification",
    {
        "train_data_s3_uri": train_uri,
        "algorithm": "random_forest",
        "hyperparameters": {
            "n_estimators": 100,
            "max_depth": 10,
            "random_state": 42,
        },
    }
)
model_uri = train_result["result"]["training_info"]["model_s3_uri"]
print(f"モデル保存先: {model_uri}")
```

### 3.2 複数アルゴリズム比較

```python
algorithms = ["random_forest", "logistic_regression"]
results = {}

for algo in algorithms:
    r = server.call_tool(
        "ml_training.train_classification",
        {"train_data_s3_uri": train_uri, "algorithm": algo}
    )
    results[algo] = r["result"]["training_info"]
    print(f"{algo}: 学習完了")
```

## Step 4: モデル評価

### 4.1 メトリクス計算

```python
eval_result = server.call_tool(
    "ml_evaluation.evaluate_classification",
    {"model_s3_uri": model_uri, "test_data_s3_uri": test_uri}
)
metrics = eval_result["result"]["evaluation_info"]["metrics"]
print(f"Accuracy:  {metrics['accuracy']:.4f}")
print(f"Precision: {metrics['precision']:.4f}")
print(f"Recall:    {metrics['recall']:.4f}")
print(f"F1 Score:  {metrics['f1_score']:.4f}")
```

### 4.2 SHAP値による解釈性分析

```python
shap_result = server.call_tool(
    "ml_evaluation.calculate_shap_values",
    {
        "model_s3_uri": model_uri,
        "data_s3_uri": test_uri,
        "explainer_type": "tree",
    }
)
shap_info = shap_result["result"]["shap_info"]
print("特徴量重要度:")
for feat in shap_info["feature_importance"][:5]:
    print(f"  {feat['feature']}: {feat['importance']:.4f}")
```

## Step 5: 実験追跡

### 5.1 実験開始

```python
exp_result = server.call_tool(
    "experiment_tracking.start_experiment",
    {
        "experiment_name": "iris-classification-v1",
        "description": "Iris分類モデルの初回実験",
        "tags": ["classification", "iris"],
    }
)
experiment_id = exp_result["result"]["experiment_info"]["experiment_id"]
```

### 5.2 パラメータ・メトリクス記録

```python
server.call_tool(
    "experiment_tracking.log_parameters",
    {
        "experiment_id": experiment_id,
        "parameters": {"algorithm": "random_forest", "n_estimators": 100},
    }
)

server.call_tool(
    "experiment_tracking.log_metrics",
    {
        "experiment_id": experiment_id,
        "metrics": metrics,  # Step 4で取得した評価メトリクス
    }
)
```

## Step 6: モデルレジストリ登録

```python
reg_result = server.call_tool(
    "model_registry.register_model",
    {
        "model_s3_uri": model_uri,
        "model_name": "iris-classifier",
        "model_version": "1.0.0",
        "metadata": {
            "algorithm": "random_forest",
            "metrics": metrics,
            "experiment_id": experiment_id,
        },
    }
)
print(f"登録完了: {reg_result['result']['registry_info']['model_name']}")
```

## Step 7: データバージョニング

```python
server.call_tool(
    "data_versioning.version_dataset",
    {
        "dataset_name": "iris-dataset",
        "s3_uri": "s3://mlops-data/iris/raw.csv",
        "version": "v1.0.0",
        "description": "Iris初回データセット",
        "file_format": "csv",
        "row_count": 150,
        "tags": ["iris", "classification"],
    }
)
```

## まとめ

このチュートリアルで使用した Capability:

| # | Capability | 使用ツール |
|---|-----------|-----------|
| 1 | data_preparation | load_dataset, validate_data, preprocess_supervised |
| 2 | ml_training | train_classification |
| 3 | ml_evaluation | evaluate_classification, calculate_shap_values |
| 4 | experiment_tracking | start_experiment, log_parameters, log_metrics |
| 5 | model_registry | register_model |
| 6 | data_versioning | version_dataset |

## 次のステップ

- [監視・運用チュートリアル](monitoring-operations.md) - デプロイ後の監視設定
- [API仕様書](../api/README.md) - 全ツールの詳細仕様
