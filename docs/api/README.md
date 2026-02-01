# MLOps MCP Server API Reference

## Overview

MLOps MCP Server は 14 の Capability、57 のツールを提供する統合 MCP サーバーです。
各ツールは `Dict[str, Any]` を返し、`status`, `message`, 結果データを含みます。

## 環境設定

| 環境変数 | 値 | 動作 |
|---------|---|------|
| `MLOPS_ENV` | `development` / `test` | モック動作（AWSサービス不要） |
| `MLOPS_ENV` | `production` | 実際のAWSサービス呼び出し |

## Capability 一覧

| # | Capability | ツール数 | 説明 |
|---|-----------|---------|------|
| 1 | [github_integration](github_integration.md) | 4 | Issue検知・ワークフロー起動 |
| 2 | [workflow_optimization](workflow_optimization.md) | 5 | モデル特性分析・最適化提案 |
| 3 | [data_preparation](data_preparation.md) | 3 | データ前処理・特徴量エンジニアリング |
| 4 | [ml_training](ml_training.md) | 3 | モデル学習・HP最適化 |
| 5 | [ml_evaluation](ml_evaluation.md) | 5 | モデル評価・SHAP/LIME |
| 6 | [model_packaging](model_packaging.md) | 5 | コンテナ化・ECR登録 |
| 7 | [model_deployment](model_deployment.md) | 9 | エンドポイントデプロイ |
| 8 | [model_monitoring](model_monitoring.md) | 10 | ドリフト検出・アラート |
| 9 | [retrain_management](retrain_management.md) | 5 | 再学習トリガー管理 |
| 10 | [notification](notification.md) | 5 | 通知送信 |
| 11 | [history_management](history_management.md) | 4 | 学習履歴記録 |
| 12 | [model_registry](model_registry.md) | 5 | モデルバージョン管理 |
| 13 | [experiment_tracking](experiment_tracking.md) | 4 | 実験追跡・比較 |
| 14 | [data_versioning](data_versioning.md) | 3 | データバージョニング |

## 共通レスポンス形式

```python
{
    "status": "success",       # "success" or "error"
    "message": "説明メッセージ",
    "<result_key>": { ... }    # ツール固有の結果データ
}
```

## ツール呼び出し方法

```python
from mcp_server.server import MLOpsServer

server = MLOpsServer()
result = server.call_tool(
    "capability_name.tool_name",
    {"param1": "value1", "param2": "value2"}
)
```

## AWSサービス依存

| Capability | S3 | SageMaker | CloudWatch | Step Functions | SES | SSM |
|-----------|:--:|:---------:|:----------:|:--------------:|:---:|:---:|
| data_preparation | o | | | | | |
| ml_training | o | o | | | | |
| ml_evaluation | o | o | | | | |
| model_packaging | o | | | | | |
| model_deployment | | o | | | | |
| model_monitoring | | o | o | | | |
| retrain_management | | | | o | | |
| notification | | | | | o | o |
| history_management | o | | | | | |
| model_registry | o | o | | | | |
| experiment_tracking | o | o | o | | | |
| data_versioning | o | | | | | |
| github_integration | | | | o | | o |
| workflow_optimization | o | | | | | |
