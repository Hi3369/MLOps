# MCP Servers: MLOps専門機能

このディレクトリには、MLOps システムの専門機能を提供する Model Context Protocol (MCP) サーバーが含まれています。

## 概要

MCPサーバーは、データ前処理・モデル学習・モデル評価などの機械学習専門機能を標準化されたプロトコルで提供します。これにより、以下のメリットを実現します:

- ✅ **再利用性**: 他プロジェクトでも利用可能
- ✅ **保守性**: 独立したサーバーとして機能追加・変更が容易
- ✅ **テスト容易性**: ローカル環境で単体テスト可能
- ✅ **拡張性**: 新しいアルゴリズムや評価指標を容易に追加
- ✅ **ベンダーニュートラル**: クラウドプロバイダーに非依存

## MCPサーバー一覧（6つのコアMCPサーバー）

### Phase 1: MLOps コア機能（Week 1-6）

#### 1. Data Preparation Server

**ディレクトリ**: `data_preparation/`

**責務**: データ前処理・特徴量エンジニアリング

**提供ツール**:
- `load_dataset` - S3からデータセットを読み込む
- `validate_data` - データのバリデーション
- `preprocess_supervised` - 教師あり学習用の前処理
- `preprocess_unsupervised` - 教師なし学習用の前処理
- `preprocess_reinforcement` - 強化学習用の前処理
- `split_dataset` - データセットの分割
- `feature_engineering` - 特徴量エンジニアリング
- `save_processed_data` - 処理済みデータをS3に保存

#### 2. ML Training Server

**ディレクトリ**: `ml_training/`

**責務**: 機械学習モデルの学習

**提供ツール**:

**教師あり学習**:
- `train_supervised_classifier` - 分類モデルの学習
  - Random Forest
  - XGBoost
  - Neural Network
- `train_supervised_regressor` - 回帰モデルの学習
  - Linear Regression
  - XGBoost
  - Neural Network

**教師なし学習**:
- `train_unsupervised_clustering` - クラスタリング
  - K-Means
  - DBSCAN
  - Autoencoder
- `train_unsupervised_dimension_reduction` - 次元削減
  - PCA
  - t-SNE

**強化学習**:
- `train_reinforcement` - 強化学習モデルの学習
  - PPO (Proximal Policy Optimization)
  - DQN (Deep Q-Network)
  - A3C (Asynchronous Advantage Actor-Critic)

**共通**:
- `get_training_metrics` - 学習中のメトリクスを取得
- `save_model` - 学習済みモデルをS3に保存

#### 3. ML Evaluation Server

**ディレクトリ**: `ml_evaluation/`

**責務**: モデルの評価・可視化

**提供ツール**:
- `load_model` - S3からモデルをロード
- `evaluate_classifier` - 分類モデルの評価
- `evaluate_regressor` - 回帰モデルの評価
- `evaluate_clustering` - クラスタリングモデルの評価
- `evaluate_reinforcement` - 強化学習モデルの評価
- `compare_models` - 複数モデルの比較
- `generate_evaluation_report` - 評価レポートの生成
- `save_evaluation_results` - 評価結果をS3に保存

### Phase 2: 統合機能（Week 7-12）

#### 4. GitHub Integration Server ⭐ 新規追加

**ディレクトリ**: `github_integration/`

**責務**: GitHub連携機能の統合

**提供ツール**:

**Issue管理**:
- `get_issue` - Issueの取得
- `create_issue` - Issueの作成
- `update_issue` - Issueの更新
- `add_issue_comment` - Issueにコメント追加
- `get_issue_comments` - Issueのコメント一覧取得
- `parse_issue_body` - Issue本文のYAML/JSONパース

**ラベル管理**:
- `get_issue_labels` - Issueのラベル取得
- `add_label` - ラベル追加
- `remove_label` - ラベル削除

**リポジトリ操作**:
- `create_file` - ファイル作成（履歴保存用）
- `update_file` - ファイル更新
- `commit_changes` - 変更のコミット
- `create_pull_request` - プルリクエスト作成

**Webhook**:
- `validate_webhook_signature` - Webhook署名の検証
- `parse_webhook_payload` - Webhookペイロードのパース

**影響を受けるエージェント**:
- Issue Detector Agent → MCPクライアント化
- History Writer Agent → MCPクライアント化

#### 5. Model Registry Server ⭐ 新規追加

**ディレクトリ**: `model_registry/`

**責務**: モデルバージョン管理・レジストリ操作

**提供ツール**:

**モデル登録**:
- `register_model` - モデルの登録
- `update_model_metadata` - モデルメタデータの更新
- `delete_model` - モデルの削除

**モデルバージョン管理**:
- `list_model_versions` - モデルバージョン一覧取得
- `get_model_version` - 特定バージョンの取得
- `promote_model_version` - モデルバージョンの昇格（Staging → Production）
- `archive_model_version` - モデルバージョンのアーカイブ

**モデルステータス管理**:
- `approve_model` - モデルの承認
- `reject_model` - モデルの却下
- `get_model_status` - モデルステータスの取得

**ロールバック**:
- `rollback_model` - 前バージョンへのロールバック
- `get_rollback_history` - ロールバック履歴の取得

**モデル検索**:
- `search_models` - モデル検索
- `filter_models_by_metrics` - メトリクスでフィルタリング
- `get_best_model` - 最良モデルの取得

**影響を受けるエージェント**:
- Training Agent → MCPクライアント化（モデル登録部分）
- Rollback Agent → MCPクライアント化

#### 6. Notification Server ⭐ 新規追加

**ディレクトリ**: `notification/`

**責務**: 通知チャネルの統合管理

**提供ツール**:

**GitHub通知**:
- `notify_github_issue` - GitHub Issueにコメント投稿
- `update_github_issue_status` - Issueのステータス更新

**Slack通知**:
- `send_slack_message` - Slackメッセージ送信
- `send_slack_thread_reply` - スレッド返信
- `send_slack_dm` - DM送信

**Email通知**:
- `send_email` - Email送信
- `send_email_with_attachment` - 添付ファイル付きEmail送信

**Microsoft Teams通知**:
- `send_teams_message` - Teamsメッセージ送信

**Discord通知**:
- `send_discord_message` - Discordメッセージ送信

**通知テンプレート**:
- `render_notification_template` - テンプレートレンダリング
- `get_notification_templates` - テンプレート一覧取得

**影響を受けるエージェント**:
- Notification Agent → MCPクライアント化（通知チャネル部分）

## ディレクトリ構造

```
mcp_servers/
├── README.md                              # このファイル
├── __init__.py
│
├── data_preparation/                      # Data Preparation MCP Server
│   ├── __init__.py
│   ├── server.py                         # MCPサーバーメイン
│   ├── tools/                            # ツール実装
│   │   ├── __init__.py
│   │   ├── load_dataset.py
│   │   ├── validate_data.py
│   │   ├── preprocess_supervised.py
│   │   ├── preprocess_unsupervised.py
│   │   ├── preprocess_reinforcement.py
│   │   ├── feature_engineering.py
│   │   ├── split_dataset.py
│   │   └── save_processed_data.py
│   ├── Dockerfile                        # ECS用Dockerイメージ
│   └── requirements.txt                  # Python依存関係
│
├── ml_training/                           # ML Training MCP Server
│   ├── __init__.py
│   ├── server.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── supervised/
│   │   │   ├── __init__.py
│   │   │   ├── random_forest.py
│   │   │   ├── xgboost.py
│   │   │   └── neural_network.py
│   │   ├── unsupervised/
│   │   │   ├── __init__.py
│   │   │   ├── kmeans.py
│   │   │   ├── dbscan.py
│   │   │   ├── pca.py
│   │   │   └── tsne.py
│   │   └── reinforcement/
│   │       ├── __init__.py
│   │       ├── ppo.py
│   │       ├── dqn.py
│   │       └── a3c.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── ml_evaluation/                         # 3. ML Evaluation MCP Server
│   ├── __init__.py
│   ├── server.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── load_model.py
│   │   ├── evaluate_classifier.py
│   │   ├── evaluate_regressor.py
│   │   ├── evaluate_clustering.py
│   │   ├── evaluate_reinforcement.py
│   │   ├── compare_models.py
│   │   ├── generate_report.py
│   │   └── visualization.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── github_integration/                    # 4. GitHub Integration MCP Server ⭐ NEW
│   ├── __init__.py
│   ├── server.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── issue_management.py           # Issue CRUD操作
│   │   ├── label_management.py           # ラベル管理
│   │   ├── repository_operations.py      # ファイル作成・コミット
│   │   ├── webhook_handler.py            # Webhook処理
│   │   └── parser.py                     # YAML/JSONパーサー
│   ├── Dockerfile
│   └── requirements.txt
│
├── model_registry/                        # 5. Model Registry MCP Server ⭐ NEW
│   ├── __init__.py
│   ├── server.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── model_registration.py         # モデル登録
│   │   ├── version_management.py         # バージョン管理
│   │   ├── status_management.py          # ステータス管理
│   │   ├── rollback.py                   # ロールバック
│   │   └── search.py                     # モデル検索
│   ├── Dockerfile
│   └── requirements.txt
│
└── notification/                          # 6. Notification MCP Server ⭐ NEW
    ├── __init__.py
    ├── server.py
    ├── tools/
    │   ├── __init__.py
    │   ├── github_notifier.py            # GitHub通知
    │   ├── slack_notifier.py             # Slack通知
    │   ├── email_notifier.py             # Email通知
    │   ├── teams_notifier.py             # Teams通知
    │   ├── discord_notifier.py           # Discord通知
    │   └── template_manager.py           # テンプレート管理
    ├── Dockerfile
    └── requirements.txt
```

## ローカル開発

### 前提条件
- Python 3.9以上
- MCP SDK (`pip install mcp`)

### MCPサーバーの起動

```bash
# Phase 1: コアMLOps MCPサーバー
cd mcp_servers/data_preparation && python -m server
cd mcp_servers/ml_training && python -m server
cd mcp_servers/ml_evaluation && python -m server

# Phase 2: 統合MCPサーバー
cd mcp_servers/github_integration && python -m server
cd mcp_servers/model_registry && python -m server
cd mcp_servers/notification && python -m server
```

### MCPサーバーのテスト

```bash
# 単体テスト (Phase 1)
pytest tests/mcp_servers/test_data_preparation.py
pytest tests/mcp_servers/test_ml_training.py
pytest tests/mcp_servers/test_ml_evaluation.py

# 単体テスト (Phase 2) ⭐ NEW
pytest tests/mcp_servers/test_github_integration.py
pytest tests/mcp_servers/test_model_registry.py
pytest tests/mcp_servers/test_notification.py

# 統合テスト
pytest tests/integration/test_agent_mcp_integration.py
```

## デプロイメント

### ECS Fargate デプロイ

```bash
# Dockerイメージのビルド
cd mcp_servers/data_preparation
docker build -t mlops-data-preparation-mcp .

# ECRにプッシュ
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker tag mlops-data-preparation-mcp:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/mlops-data-preparation-mcp:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/mlops-data-preparation-mcp:latest

# CDKでECSサービスをデプロイ
cd ../../cdk
cdk deploy MlopsStackMcpServers
```

### Lambda デプロイ

```bash
# Lambda用にパッケージング
cd mcp_servers/ml_evaluation
pip install -r requirements.txt -t package/
cp -r *.py tools/ package/
cd package && zip -r ../function.zip . && cd ..

# Lambdaにデプロイ
aws lambda update-function-code \
  --function-name mlops-ml-evaluation-mcp \
  --zip-file fileb://function.zip
```

## エージェントからの利用

Lambda AgentからMCPサーバーを呼び出す例:

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def process_data():
    # MCPサーバーの起動パラメータ
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "mcp_servers.data_preparation.server"],
        env={"AWS_REGION": "us-east-1"}
    )

    # MCPクライアントセッション
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 初期化
            await session.initialize()

            # ツールを呼び出し
            result = await session.call_tool(
                "preprocess_supervised",
                arguments={
                    "dataset_s3_uri": "s3://mlops-bucket/datasets/train.csv",
                    "target_column": "label",
                    "task_type": "classification",
                    "preprocessing_config": {
                        "normalize": True,
                        "handle_missing": "mean",
                        "encode_categorical": True
                    }
                }
            )

            print(result)
```

## MCP通信プロトコル

### stdio通信（推奨）

Lambda/ECS AgentがMCPサーバーを子プロセスとして起動し、標準入出力でJSON-RPC通信を行います。

**メリット**:
- シンプル
- オーバーヘッドが少ない
- デバッグしやすい

### SSE通信（代替案）

MCPサーバーをECS Service（常時起動）として運用し、HTTP/SSEで通信します。

**メリット**:
- サーバーの再利用
- 複数クライアントから並行アクセス可能

## パフォーマンス最適化

### キャッシング

頻繁にアクセスされるデータ（モデル、データセット等）はローカルキャッシュを活用:

```python
from functools import lru_cache

@lru_cache(maxsize=10)
def load_cached_model(model_s3_uri: str):
    # S3からモデルをロードしてキャッシュ
    pass
```

### バッチ処理

複数のデータセットを一度に処理する場合、バッチ処理を活用:

```python
result = await session.call_tool(
    "preprocess_supervised_batch",
    arguments={
        "dataset_s3_uris": [
            "s3://mlops-bucket/datasets/train-001.csv",
            "s3://mlops-bucket/datasets/train-002.csv",
            "s3://mlops-bucket/datasets/train-003.csv"
        ],
        # ...
    }
)
```

## トラブルシューティング

### MCPサーバーが起動しない

- Python環境を確認: `python --version`
- 依存関係を確認: `pip list | grep mcp`
- ログを確認: `cat /var/log/mcp_server.log`

### ツール呼び出しが失敗する

- 引数スキーマを確認
- S3アクセス権限を確認
- CloudWatch Logsでエラー詳細を確認

## 参考資料

- [Model Context Protocol 仕様](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP設計書](../mcp_design.md)
- [アーキテクチャ設計書](../architecture_design.md)
