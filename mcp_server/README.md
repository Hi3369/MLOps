# 統合MLOps MCP Server

## 概要

統合MLOps MCP Serverは、MLOpsパイプラインの全専門機能を**1つのMCPサーバー**として提供します。

MCPサーバーは、データ前処理・モデル学習・モデル評価などの機械学習専門機能を標準化されたプロトコルで提供します。これにより、以下のメリットを実現します:

- ✅ **再利用性**: 他プロジェクトでも利用可能
- ✅ **保守性**: 機能追加・変更が1つのサーバー内で完結
- ✅ **テスト容易性**: ローカル環境で全Capabilityを一度にテスト可能
- ✅ **拡張性**: 新しいCapability・ツールを容易に追加
- ✅ **ベンダーニュートラル**: クラウドプロバイダーに非依存
- ✅ **運用の簡素化**: 1つのサーバープロセス/コンテナのみ管理
- ✅ **デプロイの簡素化**: 1つのデプロイパイプラインで完結
- ✅ **リソース効率**: メモリ・CPUを共有、オーバーヘッド削減
- ✅ **MCP接続の最小化**: 1つのMCP接続で全ツールにアクセス

## 提供Capability（6つの機能群）

### 1. Data Preparation

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

### 2. ML Training

**責務**: 機械学習モデルの学習

**提供ツール**:

**教師あり学習**:

- `train_supervised_classifier` - 分類モデルの学習
  - Random Forest
  - XGBoost
  - Neural Network
- `train_supervised_regressor` - 回帰モデルの学習
  - Linear Regression
  - XGBoost Regressor
  - Neural Network Regressor

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

### 3. ML Evaluation

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

### 4. GitHub Integration

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

### 5. Model Registry

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

### 6. Notification

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

## ディレクトリ構造

```
mcp_server/                                # 統合MLOps MCP Server（単数形）
├── __init__.py
├── server.py                             # メインサーバー・ツールルーティング
├── __main__.py                           # エントリーポイント
│
├── capabilities/                          # 11個のCapability実装
│   ├── __init__.py
│   │
│   ├── data_preparation/                 # Capability 1: Data Preparation
│   │   ├── __init__.py
│   │   ├── capability.py                 # Capability定義
│   │   └── tools/
│   │       ├── __init__.py
│   │       ├── load_dataset.py
│   │       ├── validate_data.py
│   │       ├── preprocess_supervised.py
│   │       ├── preprocess_unsupervised.py
│   │       ├── preprocess_reinforcement.py
│   │       ├── feature_engineering.py
│   │       └── split_dataset.py
│   │
│   ├── ml_training/                      # Capability 2: ML Training
│   │   ├── __init__.py
│   │   ├── capability.py
│   │   └── tools/
│   │       ├── __init__.py
│   │       ├── supervised/
│   │       │   ├── random_forest.py
│   │       │   ├── xgboost.py
│   │       │   └── neural_network.py
│   │       ├── unsupervised/
│   │       │   ├── kmeans.py
│   │       │   ├── dbscan.py
│   │       │   ├── pca.py
│   │       │   └── tsne.py
│   │       └── reinforcement/
│   │           ├── ppo.py
│   │           ├── dqn.py
│   │           └── a3c.py
│   │
│   ├── ml_evaluation/                    # Capability 3: ML Evaluation
│   │   ├── __init__.py
│   │   ├── capability.py
│   │   └── tools/
│   │       ├── __init__.py
│   │       ├── evaluate_classifier.py
│   │       ├── evaluate_regressor.py
│   │       ├── evaluate_clustering.py
│   │       ├── evaluate_reinforcement.py
│   │       ├── compare_models.py
│   │       └── visualization.py
│   │
│   ├── github_integration/               # Capability 4: GitHub Integration
│   │   ├── __init__.py
│   │   ├── capability.py
│   │   └── tools/
│   │       ├── __init__.py
│   │       ├── issue_management.py
│   │       ├── label_management.py
│   │       ├── repository_operations.py
│   │       ├── webhook_handler.py
│   │       └── parser.py
│   │
│   ├── model_registry/                   # Capability 5: Model Registry
│   │   ├── __init__.py
│   │   ├── capability.py
│   │   └── tools/
│   │       ├── __init__.py
│   │       ├── model_registration.py
│   │       ├── version_management.py
│   │       ├── status_management.py
│   │       ├── rollback.py
│   │       └── search.py
│   │
│   └── notification/                     # Capability 6: Notification
│       ├── __init__.py
│       ├── capability.py
│       └── tools/
│           ├── __init__.py
│           ├── github_notifier.py
│           ├── slack_notifier.py
│           ├── email_notifier.py
│           ├── teams_notifier.py
│           ├── discord_notifier.py
│           └── template_manager.py
│
├── common/                                # 共通ユーティリティ
│   ├── __init__.py
│   ├── s3_utils.py
│   ├── logger.py
│   └── config.py
│
├── Dockerfile                            # ECS Fargate用Dockerイメージ
└── requirements.txt                      # すべてのcapabilityの依存関係を統合
```

## ローカル開発

### 前提条件

- Python 3.9以上
- MCP SDK (`pip install mcp`)

### 統合MCPサーバーの起動

```bash
cd mcp_server && python -m mcp_server
```

または

```bash
python -m mcp_server
```

### 統合MCPサーバーのテスト

```bash
# サーバー・ルーティングのテスト
pytest tests/mcp_server/test_server.py

# 各Capabilityのテスト
pytest tests/mcp_server/test_data_preparation.py
pytest tests/mcp_server/test_ml_training.py
pytest tests/mcp_server/test_ml_evaluation.py
pytest tests/mcp_server/test_github_integration.py
pytest tests/mcp_server/test_model_registry.py
pytest tests/mcp_server/test_notification.py

# 統合テスト
pytest tests/integration/test_agent_mcp_integration.py
```

## デプロイメント

### ECS Fargate デプロイ（推奨）

統合MCPサーバーを1つのECS Fargateタスクとしてデプロイ

**推奨構成**:

- CPU: 2 vCPU
- Memory: 8GB
- Auto Scaling: 最小1タスク、最大5タスク

```bash
# Dockerイメージのビルド
cd mcp_server
docker build -t mlops-unified-mcp-server .

# ECRへのプッシュ
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker tag mlops-unified-mcp-server:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/mlops-unified-mcp-server:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/mlops-unified-mcp-server:latest

# ECS Serviceのデプロイ（CDK経由）
cd cdk
cdk deploy UnifiedMCPServerStack
```

### Lambda デプロイ（軽量処理・開発環境向け）

統合MCPサーバーを1つのLambda関数としてデプロイ

**推奨構成**:

- Memory: 4096MB - 10240MB
- Timeout: 15分
- Ephemeral storage: 10GB

```bash
# Lambda関数のパッケージング
cd mcp_server
zip -r function.zip .

# Lambdaへのデプロイ（CDK経由）
cd cdk
cdk deploy UnifiedMCPServerStack --context deployment-type=lambda
```

## MCPクライアント実装例

```python
# Lambda Agent側（MCP Client）
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def call_mcp_tool():
    # 統合MCPサーバーを起動
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "mcp_server"],  # 統合サーバー
        env={"AWS_REGION": "us-east-1"}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Data Preparationツールを呼び出し
            result = await session.call_tool(
                "preprocess_supervised",
                arguments={
                    "dataset_s3_uri": "s3://mlops-bucket/datasets/train.csv",
                    "target_column": "label",
                    "task_type": "classification"
                }
            )

            # ML Trainingツールを呼び出し（同じセッションで）
            result2 = await session.call_tool(
                "train_supervised_classifier",
                arguments={
                    "algorithm": "random_forest",
                    "train_data_s3_uri": "s3://mlops-bucket/processed/train.csv",
                    "training_job_name": "rf-training-001"
                }
            )

            return result, result2
```

## 統合アプローチのメリット

### 従来の6個独立サーバーと比較

| 項目 | 統合MCPサーバー（1個） | 独立MCPサーバー（6個） |
|------|------|------|
| **運用の簡素さ** | ✅ 1プロセスのみ | ❌ 6プロセス管理 |
| **デプロイの簡素さ** | ✅ 1デプロイのみ | ❌ 6デプロイ管理 |
| **リソース効率** | ✅ 共有により効率的 | ❌ 各サーバーでオーバーヘッド |
| **MCP接続数** | ✅ 1接続のみ | ❌ 6接続必要 |
| **Agent実装** | ✅ 1つのクライアントで全機能 | ❌ 6つのクライアント必要 |
| **インフラコスト** | ✅ 低い（リソース共有） | ❌ 高い（6倍のオーバーヘッド） |

## トラブルシューティング

### サーバーが起動しない

```bash
# 依存関係の確認
pip install -r requirements.txt

# Python versionの確認
python --version  # 3.9以上が必要
```

### ツールが見つからない

```bash
# サーバーのツール一覧を確認
python -m mcp_server --list-tools
```

### メモリ不足エラー

ECS FargateまたはLambdaのメモリ設定を増やしてください:

- ECS: 8GB → 16GB
- Lambda: 4096MB → 10240MB

## 参考資料

- [MCP化設計書](../mcp_design.md)
- [アーキテクチャ設計書](../architecture_design.md)
- [MCP拡張設計書](../mcp_extended_design.md)
- [Model Context Protocol 仕様](https://spec.modelcontextprotocol.io/)
