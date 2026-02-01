# クイックスタート

MLOps MCP Serverの基本的な使い方を学ぶチュートリアル。

## 1. サーバー起動

```python
from mcp_server.server import MLOpsServer

server = MLOpsServer()
print(server.get_server_info())
# => {'name': 'MLOps Integrated MCP Server', 'version': '0.1.0',
#     'capabilities': [...], 'total_tools': 57}
```

## 2. ツール一覧確認

```python
tools = server.list_tools()
for tool in tools:
    print(f"  {tool['name']}")
```

## 3. 基本的なツール呼び出し

### データ読み込み

```python
result = server.call_tool(
    "data_preparation.load_dataset",
    {"s3_uri": "s3://my-bucket/data/train.csv"}
)
print(result["result"]["status"])  # "success"
print(result["result"]["dataset_info"])
```

### データバリデーション

```python
result = server.call_tool(
    "data_preparation.validate_data",
    {
        "s3_uri": "s3://my-bucket/data/train.csv",
        "required_columns": ["feature1", "feature2", "target"],
        "max_missing_ratio": 0.3,
    }
)
print(result["result"]["validation_result"])
```

### 分類モデル学習

```python
result = server.call_tool(
    "ml_training.train_classification",
    {
        "train_data_s3_uri": "s3://my-bucket/data/train.csv",
        "algorithm": "random_forest",
        "hyperparameters": {"n_estimators": 100, "max_depth": 10},
    }
)
print(result["result"]["training_info"]["model_s3_uri"])
```

### モデル評価

```python
result = server.call_tool(
    "ml_evaluation.evaluate_classification",
    {
        "model_s3_uri": "s3://my-bucket/models/model.tar.gz",
        "test_data_s3_uri": "s3://my-bucket/data/test.csv",
    }
)
metrics = result["result"]["evaluation_info"]["metrics"]
print(f"Accuracy: {metrics['accuracy']}")
print(f"F1 Score: {metrics['f1_score']}")
```

## 4. 環境について

| 環境 | MLOPS_ENV | 動作 |
|------|-----------|------|
| 開発 | `development` | モックデータを返す（デフォルト） |
| テスト | `test` | モックデータを返す |
| 本番 | `production` | 実際のAWSサービスを呼び出す |

開発環境ではAWSアカウント不要で全ツールを試すことができます。

## 次のステップ

- [学習パイプラインチュートリアル](training-pipeline.md) - 完全なMLパイプラインを構築
- [監視・運用チュートリアル](monitoring-operations.md) - デプロイと監視の設定
- [API仕様書](../api/README.md) - 全ツールの詳細リファレンス
