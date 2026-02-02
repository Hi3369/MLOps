# MLOps Integrated MCP Server

統合MLOps MCPサーバーは、MLOpsパイプラインの全専門機能を単一のMCPサーバーとして提供します。

## 概要

このMCPサーバーは、14個のCapability（60ツール）を統合し、Claude Desktop/Claude APIから利用可能にします。

| # | Capability | ツール数 | 説明 |
|---|-----------|---------|------|
| 1 | data_preparation | 3 | データ前処理・特徴量エンジニアリング |
| 2 | ml_training | 3 | モデル学習（分類・回帰・クラスタリング） |
| 3 | ml_evaluation | 5 | モデル評価・SHAP/LIME解釈性分析 |
| 4 | model_registry | 5 | モデル登録・バージョン管理 |
| 5 | model_packaging | 5 | コンテナ化・ECR登録 |
| 6 | model_deployment | 9 | エンドポイントデプロイ・オートスケーリング |
| 7 | model_monitoring | 10 | メトリクス収集・ドリフト検出・アラーム |
| 8 | workflow_optimization | 5 | モデル特性分析・最適化提案 |
| 9 | github_integration | 4 | Issue検知・ワークフロー起動 |
| 10 | notification | 4 | 通知管理（Slack/Email/GitHub） |
| 11 | retrain_management | 5 | 再学習トリガー判定・ワークフロー管理 |
| 12 | history_management | 4 | 学習履歴記録・GitHub連携 |
| 13 | experiment_tracking | 4 | 実験追跡・パラメータ/メトリクス管理 |
| 14 | data_versioning | 3 | データセットバージョニング・系譜追跡 |

## ディレクトリ構造

```text
mcp_server/
├── __init__.py              # パッケージ初期化
├── __main__.py              # エントリーポイント
├── server.py                # MLOpsServer本体
├── common/                  # 共通ユーティリティ
│   ├── __init__.py
│   ├── logger.py            # ロギング設定
│   ├── s3_utils.py          # S3操作ユーティリティ
│   └── config.py            # 設定管理
└── capabilities/            # 14 Capability実装
    ├── data_preparation/
    ├── ml_training/
    ├── ml_evaluation/
    ├── model_registry/
    ├── model_packaging/
    ├── model_deployment/
    ├── model_monitoring/
    ├── workflow_optimization/
    ├── github_integration/
    ├── notification/
    ├── retrain_management/
    ├── history_management/
    ├── experiment_tracking/
    └── data_versioning/
```

## セットアップ

### 必要要件

- Python 3.12+
- AWS認証情報（本番環境のみ。開発環境ではモック動作）

### インストール

```bash
pip install -e ".[dev]"
```

### 環境変数

```bash
# 環境設定（development / test / production）
export MLOPS_ENV=development    # モック動作（デフォルト）

# AWS設定（本番環境のみ）
export MLOPS_S3_BUCKET=your-mlops-bucket
export AWS_REGION=us-west-2
```

## 使用方法

### サーバーの起動

```bash
python -m mcp_server
```

### ツールの利用

```python
import os
os.environ["MLOPS_ENV"] = "development"

from mcp_server.server import MLOpsServer

server = MLOpsServer()

# サーバー情報の取得
info = server.get_server_info()
print(f"Capabilities: {len(info['capabilities'])}, Tools: {info['total_tools']}")

# ツールの実行
result = server.call_tool(
    "data_preparation.load_dataset",
    {"s3_uri": "s3://my-bucket/data/train.csv", "file_format": "csv"}
)
```

## 開発

### コード品質チェック

```bash
# フォーマット
black mcp_server/ tests/
isort --profile black mcp_server/ tests/

# リント
flake8 mcp_server/ tests/ --max-line-length=100

# 型チェック
mypy mcp_server/ --ignore-missing-imports

# セキュリティ
bandit -r mcp_server/ -c pyproject.toml
```

### テスト

```bash
# テスト実行
pytest tests/ -v

# カバレッジ付き
pytest tests/ --cov=mcp_server --cov-report=html
```

## アーキテクチャ

### Unified MCP Server方式

単一のMCPサーバーが複数のCapabilityをホストし、ツール名を`{capability}.{tool}`形式で提供します。

**利点:**

- 単一プロセスで全機能を管理
- Capability間のコード共有が容易
- 統一されたログ・監視
- デプロイ・運用がシンプル

### Tool Naming Convention

```text
{capability_name}.{tool_name}

例:
- data_preparation.load_dataset
- ml_training.train_classification
- ml_evaluation.calculate_shap_values
- model_registry.register_model
- experiment_tracking.start_experiment
```

### 環境別動作

| 環境 | `MLOPS_ENV` | 動作 |
|------|------------|------|
| 開発 | `development` | モックデータを返却（AWSサービス不要） |
| テスト | `test` | モックデータを返却 |
| 本番 | `production` | 実際のAWSサービスを呼び出し |

## ライセンス

内部プロジェクト用
