# GitHub Issue駆動型MLOpsシステム

AWS Step FunctionsとAmazon SageMakerを使用したエージェントベースのMLOpsパイプライン

## 概要

このシステムは、GitHub Issueをトリガーとして機械学習モデルの学習・評価・デプロイを自動化します。3種類の学習方式（教師あり学習、教師なし学習、強化学習）をサポートし、評価結果に基づく自動再学習とロールバック機能を備えています。

## 主な機能

- **GitHub Issue駆動**: Issueにラベル`mlops:train`を付けるだけで学習パイプラインが起動
- **3種類の学習方式サポート**:
  - 教師あり学習（分類・回帰）
  - 教師なし学習（クラスタリング・次元削減）
  - 強化学習（Q-Learning・Policy Gradient）
- **自動評価・判定**: 学習後の自動評価と閾値判定
- **対話型再学習**: 精度が閾値未満の場合、オペレータと対話して設定調整
- **ロールバック機能**: 学習失敗時の前バージョン保持
- **履歴管理**: 学習結果をGitHubリポジトリに自動保存

## アーキテクチャ

![System Architecture](diagrams/system_architecture.mmd)

![Data Flow](diagrams/data_flow.mmd)

詳細は[docs/specifications/system_specification.md](docs/specifications/system_specification.md)を参照してください。

## ディレクトリ構造

![Directory Structure](diagrams/directory_structure.mmd)

**詳細**: [diagrams/directory_structure.mmd](diagrams/directory_structure.mmd) | [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

## セットアップ

### 前提条件

- Python 3.9以上
- AWS CLI設定済み
- Node.js 18以上（AWS CDK用）
- GitHub Personal Access Token

### 1. リポジトリのクローン

```bash
git clone https://github.com/your-org/mlops-pipeline.git
cd mlops-pipeline
```

### 2. 依存関係のインストール

```bash
# Python依存関係
pip install -r requirements.txt

# CDK依存関係
cd cdk
npm install
```

### 3. AWS環境のセットアップ

```bash
# CDKのブートストラップ（初回のみ）
cdk bootstrap

# スタックのデプロイ
cdk deploy --all
```

### 4. GitHub Webhook設定

1. GitHubリポジトリの設定で「Webhooks」を開く
2. Webhook URLにAPI Gateway URLを設定（CDKデプロイ後に出力される）
3. Content typeを`application/json`に設定
4. Eventsで「Issues」を選択

### 5. シークレットの設定

```bash
# GitHub Tokenの保存
aws secretsmanager create-secret \
  --name github-token \
  --secret-string '{"token":"YOUR_GITHUB_TOKEN"}'

# Slack Webhook URLの保存（オプション）
aws secretsmanager create-secret \
  --name slack-webhook-url \
  --secret-string '{"url":"YOUR_SLACK_WEBHOOK_URL"}'
```

## 使い方

### 1. 学習データの準備

学習データをS3にアップロード:

```bash
aws s3 cp train.csv s3://mlops-bucket/datasets/my-dataset-001/raw/train.csv
aws s3 cp test.csv s3://mlops-bucket/datasets/my-dataset-001/raw/test.csv
```

### 2. GitHub Issueの作成

GitHubリポジトリで新しいIssueを作成し、以下の内容を記載:

**タイトル**: `[MLOps] Random Forest分類モデルの学習`

**ラベル**: `mlops:train`

**本文**:
```yaml
learning_type: supervised
algorithm: random_forest
dataset_id: my-dataset-001
hyperparameters:
  n_estimators: 100
  max_depth: 10
  min_samples_split: 2
evaluation_threshold: 0.85
max_retry: 3
```

### 3. 学習の開始

Issueを作成すると、自動的に学習パイプラインが起動します。進捗はIssueのコメントで通知されます。

### 4. 結果の確認

学習完了後、以下が自動的に実行されます:

- 評価結果がIssueにコメントとして投稿
- 学習履歴が`training_history/`にコミット
- モデルがSageMaker Model Registryに登録（閾値以上の場合）

## 学習方式の詳細

### 教師あり学習（Supervised Learning）

**分類（Classification）**:
```yaml
learning_type: supervised
algorithm: random_forest  # または xgboost, neural_network
task_type: classification
dataset_id: classification-dataset-001
hyperparameters:
  n_estimators: 100
  max_depth: 10
evaluation_threshold: 0.85  # Accuracy閾値
```

**回帰（Regression）**:
```yaml
learning_type: supervised
algorithm: linear_regression  # または xgboost, neural_network
task_type: regression
dataset_id: regression-dataset-001
hyperparameters:
  alpha: 0.1
evaluation_threshold: 0.9  # R²閾値
```

### 教師なし学習（Unsupervised Learning）

**クラスタリング（K-Means）**:
```yaml
learning_type: unsupervised
algorithm: kmeans
dataset_id: clustering-dataset-001
hyperparameters:
  k: 10
  feature_dim: 50
evaluation_threshold: 0.5  # Silhouette Score閾値
```

**次元削減（PCA）**:
```yaml
learning_type: unsupervised
algorithm: pca
dataset_id: dimension-reduction-dataset-001
hyperparameters:
  num_components: 10
```

### 強化学習（Reinforcement Learning）

```yaml
learning_type: reinforcement
algorithm: ppo  # または dqn, a3c
environment: CartPole-v1
hyperparameters:
  gamma: 0.99
  learning_rate: 0.001
  num_episodes: 1000
evaluation_threshold: 195.0  # Average Reward閾値
```

## 再学習フロー

精度が閾値未満の場合:

1. システムがオペレータに通知（GitHub Issue + Slack/Email）
2. オペレータがIssueにコメントで設定調整を指示:
   ```yaml
   adjusted_hyperparameters:
     n_estimators: 200
     max_depth: 15
   ```
3. システムが調整された設定で再学習を実行
4. 最大3回まで繰り返し

## モニタリング

### CloudWatch Dashboard

AWS コンソール → CloudWatch → Dashboards → `MLOps-Pipeline-Dashboard`

- 学習ジョブの実行回数
- 成功率・失敗率
- 平均実行時間
- エラー統計

### ログの確認

```bash
# Step Functions実行ログ
aws logs tail /aws/states/MLOpsPipeline --follow

# Lambda関数ログ
aws logs tail /aws/lambda/IssueDetectorAgent --follow
```

## トラブルシューティング

### 学習が開始しない

- GitHub Webhookが正しく設定されているか確認
- Issueに`mlops:train`ラベルが付いているか確認
- CloudWatch Logsでエラーを確認

### 学習が失敗する

- データがS3に正しくアップロードされているか確認
- SageMakerのクォータ制限を確認
- ハイパーパラメータが正しいか確認

### モデルが登録されない

- 評価結果が閾値以上か確認
- SageMaker Model Registryの権限を確認

## 開発

### テストの実行

```bash
# 単体テスト
pytest tests/unit

# 統合テスト
pytest tests/integration

# カバレッジ付きテスト
pytest --cov=agents --cov-report=html
```

### コードフォーマット

```bash
# フォーマット
black agents/ tests/

# リンター
flake8 agents/ tests/

# 型チェック
mypy agents/
```

### セキュリティスキャン

```bash
# 依存関係の脆弱性スキャン
pip-audit

# コードの脆弱性スキャン
bandit -r agents/
```

## ライセンス

MIT License

## 貢献

プルリクエストを歓迎します！詳細は[CONTRIBUTING.md](CONTRIBUTING.md)を参照してください。

## サポート

質問や問題がある場合は、GitHub Issuesで報告してください。

## ドキュメント

### 仕様書

- [システム仕様書](docs/specifications/system_specification.md) - 機能要件、非機能要件、システムアーキテクチャ

### 設計書

- [MCP設計書](docs/designs/mcp_design.md) - 統合MLOps MCPサーバー設計、セキュリティ設計
- [実装ガイド](docs/designs/implementation_guide.md) - 実装設計、MLOpsワークフロー、開発・運用ガイド
- [設計レビュー](docs/designs/REVIEW.md) - 設計判断の経緯と意思決定記録

### その他

- [テスト設計書](test_design.md)
- [プロジェクト構造](PROJECT_STRUCTURE.md)

### 外部リンク

- [Amazon SageMaker Documentation](https://docs.aws.amazon.com/sagemaker/)
- [AWS Step Functions Documentation](https://docs.aws.amazon.com/step-functions/)
- [Model Context Protocol 仕様](https://spec.modelcontextprotocol.io/)
