# アーキテクチャ設計書: GitHub Issue駆動型MLOpsシステム

## 0. MLOpsワークフロー要件

本システムは、以下の7段階のMLOpsワークフローを実現します。

### 0.1 ワークフローの7段階

#### 1. 📥 データ収集・前処理

**目的**: データの取得、クリーニング、特徴量エンジニアリング、バージョニング

**実装**:

- さまざまなデータソース（S3、データベース、API等）からデータを取得
- データクリーニング（欠損値処理、異常値除去、重複削除）
- 特徴量エンジニアリング（特徴量生成、選択、変換）
- データバージョニング（DVC、S3バージョニング等）で再現性を確保
- データカタログ（AWS Glue Data Catalog等）でメタデータ管理

**成果物**:

- バージョン管理されたデータセット（train/validation/test）
- データ品質レポート
- 特徴量定義ドキュメント

#### 2. 🧪 モデル開発（実験）

**目的**: モデルの設計、学習、ハイパーパラメータ調整、実験管理

**実装**:

- モデルアーキテクチャの設計と実装
- ハイパーパラメータ調整（Grid Search、Random Search、Bayesian Optimization）
- 実験管理ツール（MLflow、SageMaker Experiments等）で結果を記録
- 複数の実験を並列実行し、最適なモデルを選択
- 実験の再現性を確保（コード、データ、パラメータのバージョン管理）

**成果物**:

- 複数の学習済みモデル候補
- 実験ログ（パラメータ、メトリクス、成果物）
- 最適モデルの選定結果

#### 3. 🧹 モデル検証・テスト

**目的**: モデルの精度評価、バイアスチェック、ドリフト検知準備、自動テスト

**実装**:

- 精度評価（Accuracy、Precision、Recall、F1、AUC-ROC等）
- バイアスチェック（公平性評価、Fairness Indicators等）
- データドリフト検知の準備（ベースライン統計の記録）
- CI/CDパイプラインによる自動テスト
  - ユニットテスト（モデル関数のテスト）
  - 統合テスト（パイプライン全体のテスト）
  - モデル性能テスト（最低精度の保証）
- モデル説明可能性（SHAP、LIME等）

**成果物**:

- 評価レポート（メトリクス、混同行列、ROC曲線等）
- バイアスチェック結果
- テストレポート（全テストの合格/不合格）
- モデル説明レポート

#### 4. 📦 モデルパッケージング

**目的**: モデルをデプロイ可能な形式にパッケージ化、環境差異の排除

**実装**:

- モデルをAPI化（REST API、gRPC等）
- コンテナ化（Docker、SageMaker Inference Container等）
- 依存関係の明確化（requirements.txt、Dockerfile、conda環境等）
- モデルレジストリへの登録（SageMaker Model Registry、MLflow Model Registry等）
- バージョン管理（セマンティックバージョニング v1.0.0、v1.1.0等）
- 環境差異を排除（開発環境と本番環境で同じコンテナイメージを使用）

**成果物**:

- Dockerイメージ（モデル + 推論コード + 依存関係）
- モデルレジストリへの登録エントリ
- デプロイメント仕様書

#### 5. 🚀 デプロイ（リリース）

**目的**: 本番環境へのモデルデプロイ、段階的リリース、自動化

**実装**:

- 本番環境へモデルをデプロイ（SageMaker Endpoint、ECS、Lambda等）
- 段階的リリース戦略:
  - **A/Bテスト**: 新旧モデルを並行稼働し、効果を比較
  - **カナリアリリース**: 一部トラフィックのみ新モデルに流し、問題なければ全体展開
  - **ブルー/グリーンデプロイメント**: 新環境を構築し、切り替え
- CI/CDパイプラインで自動化（GitHub Actions、CodePipeline等）
- インフラストラクチャ as Code（CloudFormation、CDK、Terraform等）
- ロールバック機能の実装

**成果物**:

- 本番環境で稼働するモデルエンドポイント
- デプロイメントログ
- ロールバックプラン

#### 6. 🔍 モニタリング（運用）

**目的**: 推論性能の監視、モデル精度の劣化検知、アラート

**実装**:

- **システムメトリクス監視**:
  - レスポンスタイム（P50、P95、P99）
  - エラー率（4xx、5xx）
  - スループット（RPS）
  - リソース使用率（CPU、メモリ、GPU）
- **モデルメトリクス監視**:
  - 推論精度の劣化（Accuracy、F1等の低下）
  - データドリフト検知（入力データ分布の変化）
  - コンセプトドリフト検知（入力と出力の関係の変化）
  - 予測分布の変化
- **アラート設定**:
  - CloudWatch Alarms、PagerDuty等
  - Slackへの自動通知
  - GitHub Issueの自動作成
- **ダッシュボード**:
  - CloudWatch Dashboard、Grafana等
  - リアルタイムメトリクス可視化

**成果物**:
- モニタリングダッシュボード
- アラートルール定義
- 運用ログ

#### 7. 🔄 継続的改善（再トレーニング）
**目的**: 新しいデータでの再学習、モデルバージョン管理、パイプライン自動化

**実装**:
- **自動再トレーニングトリガー**:
  - データ変更（新しいデータが追加された時）
  - コード変更（モデルコードが更新された時）
  - スケジュール（週次、月次等の定期実行）
  - メトリクス劣化（精度が閾値を下回った時）
  - ドリフト検知（データドリフトが検出された時）
- モデルのバージョン管理（v1.0.0 → v1.1.0 → v2.0.0）
- パイプラインの自動再実行（Step Functions、Airflow等）
- 新モデルの自動評価と承認フロー
- 継続的デプロイメント（CDによる自動デプロイ）
- フィードバックループ（本番データを次回学習データに活用）

**成果物**:
- 新バージョンのモデル
- 再学習ログ
- パフォーマンス比較レポート（旧モデル vs 新モデル）

### 0.2 ワークフロー全体図

```
┌─────────────────────────────────────────────────────────────────┐
│                    MLOps ライフサイクル                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
         ┌────────────────────────────────────────┐
         │  1. 📥 データ収集・前処理              │
         │  - データソースから取得                 │
         │  - クリーニング、特徴量エンジニアリング   │
         │  - データバージョニング（DVC、S3）      │
         └────────────────┬───────────────────────┘
                          ↓
         ┌────────────────────────────────────────┐
         │  2. 🧪 モデル開発（実験）               │
         │  - モデル設計・学習                    │
         │  - ハイパーパラメータ調整               │
         │  - 実験管理（MLflow、SageMaker）       │
         └────────────────┬───────────────────────┘
                          ↓
         ┌────────────────────────────────────────┐
         │  3. 🧹 モデル検証・テスト               │
         │  - 精度評価、バイアスチェック           │
         │  - データドリフト検知準備               │
         │  - CI自動テスト（ユニット、統合）       │
         └────────────────┬───────────────────────┘
                          ↓
         ┌────────────────────────────────────────┐
         │  4. 📦 モデルパッケージング             │
         │  - API化、コンテナ化                   │
         │  - 依存関係の明確化                    │
         │  - モデルレジストリへ登録               │
         └────────────────┬───────────────────────┘
                          ↓
         ┌────────────────────────────────────────┐
         │  5. 🚀 デプロイ（リリース）             │
         │  - 本番環境へデプロイ                   │
         │  - A/Bテスト、カナリアリリース          │
         │  - CI/CDパイプライン自動化              │
         └────────────────┬───────────────────────┘
                          ↓
         ┌────────────────────────────────────────┐
         │  6. 🔍 モニタリング（運用）             │
         │  - レスポンス、エラー率、スループット    │
         │  - モデル精度劣化、ドリフト検知          │
         │  - アラート設定                        │
         └────────────────┬───────────────────────┘
                          ↓
         ┌────────────────────────────────────────┐
         │  7. 🔄 継続的改善（再トレーニング）      │
         │  - 新データで再学習                     │
         │  - モデルバージョン管理                 │
         │  - パイプライン自動再実行               │
         └────────────────┬───────────────────────┘
                          ↓
                  （1に戻る - ループ）
```

### 0.3 GitHub Issue駆動型との統合

本システムでは、上記の7段階のワークフローを**GitHub Issue**を起点として駆動します。

**GitHub Issueによるトリガー例**:

```yaml
# Issue作成により 1→2→3→4→5 を自動実行
learning_type: supervised
algorithm: xgboost
dataset_id: dataset-20250128-001
hyperparameters:
  num_round: 100
  max_depth: 5
evaluation_threshold: 0.85
deployment_strategy: canary  # カナリアリリース
monitoring_enabled: true     # モニタリング有効化
auto_retrain_on_drift: true  # ドリフト検知時に自動再学習
```

**ワークフローの自動化範囲**:
- **1-5**: GitHub Issue作成により自動実行
- **6**: デプロイ後、継続的に実行
- **7**: モニタリングで検知されたイベント（ドリフト、精度劣化等）により自動実行

---

## 1. アーキテクチャ概要

### 1.1 システムアーキテクチャ図

![System Architecture](diagrams/system_architecture.mmd)

**詳細**: [diagrams/system_architecture.mmd](diagrams/system_architecture.mmd)

### 1.2 エージェントベースアーキテクチャ

本システムは、各処理を独立したエージェント（Agent）として実装します。

![Agent Architecture](diagrams/agent_architecture.mmd)

**詳細**: [diagrams/agent_architecture.mmd](diagrams/agent_architecture.mmd)

**エージェント一覧:**
1. **Issue Detector Agent**: GitHub Issueの検知
2. **Data Preparation Agent**: 学習データの準備と前処理
3. **Training Agent**: SageMakerを使った学習実行
4. **Evaluation Agent**: モデルの評価
5. **Judge Agent**: 評価結果の判定と次アクション決定
6. **Notification Agent**: オペレータへの通知
7. **Rollback Agent**: モデルのロールバック
8. **History Writer Agent**: 学習履歴のGitHub保存

---

## 2. コンポーネント設計

### 2.1 Issue Detector Agent

**責務**: GitHub Issueの検知とパース

**実装方式**:
- AWS Lambda (Python)
- API Gateway + Webhook（GitHub Webhookを受信）
- または EventBridge Scheduler（定期ポーリング）

**処理フロー**:
1. GitHub WebhookまたはGitHub APIでIssue作成イベントを検知
2. ラベルが`mlops:train`であることを確認
3. Issue本文からYAML/JSONパラメータを抽出
4. Step Functionsワークフローを起動
5. パラメータをワークフローに渡す

**入力**:
```json
{
  "issue_number": 123,
  "repository": "org/repo",
  "labels": ["mlops:train"],
  "body": "learning_type: supervised\nalgorithm: random_forest\n..."
}
```

**出力**:
```json
{
  "training_config": {
    "issue_number": 123,
    "learning_type": "supervised",
    "algorithm": "random_forest",
    "dataset_id": "dataset-20250110-001",
    "hyperparameters": {...},
    "evaluation_threshold": 0.85,
    "max_retry": 3
  }
}
```

---

### 2.2 Data Preparation Agent

**責務**: 学習データの取得、前処理、SageMaker用フォーマット変換

**実装方式**:
- AWS Lambda (軽量処理)
- ECS Fargate (大規模データ処理)

**処理フロー**:
1. S3から指定されたdataset_idのデータを取得
2. データのバリデーション（欠損値チェック、型チェック等）
3. 学習方式に応じた前処理（正規化、特徴量エンジニアリング等）
4. SageMaker Training用の形式に変換
5. 処理済みデータをS3の一時領域に保存
6. データのメタデータ（行数、カラム数、統計情報）を返す

**入力**:
```json
{
  "dataset_id": "dataset-20250110-001",
  "learning_type": "supervised",
  "preprocessing_config": {...}
}
```

**出力**:
```json
{
  "training_data_s3": "s3://bucket/processed/train/...",
  "validation_data_s3": "s3://bucket/processed/val/...",
  "test_data_s3": "s3://bucket/processed/test/...",
  "metadata": {
    "num_samples": 10000,
    "num_features": 50
  }
}
```

---

### 2.3 Training Agent

**責務**: SageMaker Training Jobの起動と監視

**実装方式**:
- AWS Lambda (SageMaker APIコール)
- Step Functionsの`.sync`統合（ジョブ完了まで待機）

**処理フロー**:
1. 学習方式とアルゴリズムに応じたSageMaker Training Jobの設定
2. トレーニングジョブの起動
3. ジョブの完了を待機（または非同期で次ステップへ）
4. 学習済みモデルのS3パスを取得
5. CloudWatch Logsからログを取得

**学習方式別の実装**:

![Learning Types](diagrams/learning_types.mmd)

**詳細**: [diagrams/learning_types.mmd](diagrams/learning_types.mmd)

#### 教師あり学習 (Supervised)
- **分類 (Classification)**:
  - Random Forest (scikit-learn)
  - XGBoost (SageMaker built-in)
  - Neural Network (TensorFlow/PyTorch)
- **回帰 (Regression)**:
  - Linear Regression (scikit-learn)
  - XGBoost (SageMaker built-in)
  - Neural Network (TensorFlow/PyTorch)

#### 教師なし学習 (Unsupervised)
- **クラスタリング (Clustering)**:
  - K-Means (SageMaker built-in)
  - DBSCAN (scikit-learn)
  - Autoencoder (TensorFlow/PyTorch)
- **次元削減 (Dimensionality Reduction)**:
  - PCA (SageMaker built-in)
  - t-SNE (scikit-learn)

#### 強化学習 (Reinforcement)
- **アルゴリズム**:
  - PPO (Ray RLlib)
  - DQN (Ray RLlib)
  - A3C (Ray RLlib)

**入力**:
```json
{
  "training_data_s3": "s3://...",
  "learning_type": "supervised",
  "algorithm": "random_forest",
  "hyperparameters": {...},
  "training_job_name": "train-20250110-123456"
}
```

**出力**:
```json
{
  "training_job_name": "train-20250110-123456",
  "model_s3": "s3://bucket/models/train-20250110-123456/output/model.tar.gz",
  "training_metrics": {
    "train_loss": 0.123,
    "train_accuracy": 0.89
  }
}
```

---

### 2.4 Evaluation Agent

**責務**: 学習済みモデルの評価

**実装方式**:
- AWS Lambda (軽量モデル)
- SageMaker Processing Job (大規模評価)

**処理フロー**:
1. S3から学習済みモデルをロード
2. 評価用データセットをロード
3. 学習方式に応じた評価指標を計算
4. 評価結果をJSON形式で保存
5. 評価結果をS3に保存

**評価指標**:
- **教師あり学習（分類）**: Accuracy, Precision, Recall, F1-Score, AUC-ROC, Confusion Matrix
- **教師あり学習（回帰）**: RMSE, MAE, R², MAPE
- **教師なし学習**: Silhouette Score, Davies-Bouldin Index, Inertia
- **強化学習**: Episode Reward, Success Rate, Average Steps

**入力**:
```json
{
  "model_s3": "s3://bucket/models/.../model.tar.gz",
  "test_data_s3": "s3://bucket/processed/test/...",
  "learning_type": "supervised",
  "task_type": "classification"
}
```

**出力**:
```json
{
  "evaluation_results": {
    "accuracy": 0.87,
    "precision": 0.85,
    "recall": 0.89,
    "f1_score": 0.87,
    "auc_roc": 0.91
  },
  "evaluation_s3": "s3://bucket/evaluations/train-20250110-123456/results.json"
}
```

---

### 2.5 Judge Agent

**責務**: 評価結果の判定と次アクション決定

**実装方式**:
- AWS Lambda (ビジネスロジック)

**処理フロー**:
1. 評価結果を取得
2. 設定された閾値と比較
3. 判定結果に基づいて次アクションを決定:
   - **閾値以上**: モデルをSageMaker Model Registryに登録
   - **閾値未満**: オペレータに通知、再学習フローへ
   - **最大リトライ超過**: 前バージョンのモデルを保持し、失敗通知
4. 判定結果を返す

**入力**:
```json
{
  "evaluation_results": {...},
  "evaluation_threshold": 0.85,
  "current_retry": 0,
  "max_retry": 3
}
```

**出力**:
```json
{
  "decision": "pass" | "retrain" | "fail",
  "next_action": "register_model" | "notify_operator" | "rollback",
  "message": "評価結果が閾値0.85を上回りました（0.87）"
}
```

---

### 2.6 Notification Agent

**責務**: オペレータへの通知

**実装方式**:
- AWS Lambda
- Amazon SNS (トピック発行)
- Slack Webhook / Amazon SES

**処理フロー**:
1. 通知内容を受け取る
2. 通知先（Slack/Email）に応じたメッセージフォーマット
3. GitHub IssueにコメントとしてPOST
4. Slack/Emailに通知

**入力**:
```json
{
  "notification_type": "retrain_required" | "training_success" | "training_failed",
  "issue_number": 123,
  "message": "...",
  "evaluation_results": {...}
}
```

**出力**:
```json
{
  "notification_status": "success",
  "github_comment_url": "https://github.com/org/repo/issues/123#comment-...",
  "slack_message_ts": "1234567890.123456"
}
```

---

### 2.7 Rollback Agent

**責務**: モデルのロールバック

**実装方式**:
- AWS Lambda

**処理フロー**:
1. SageMaker Model Registryから前バージョンのモデルを取得
2. 現在のモデルのステータスを`Archived`に変更
3. 前バージョンのモデルを`Approved`に変更
4. ロールバック履歴を記録

**入力**:
```json
{
  "model_package_group_name": "model-001",
  "rollback_to_version": "v1.1.0"
}
```

**出力**:
```json
{
  "rollback_status": "success",
  "current_model_version": "v1.1.0",
  "previous_model_version": "v1.2.0"
}
```

---

### 2.8 History Writer Agent

**責務**: 学習履歴のGitHub保存

**実装方式**:
- AWS Lambda
- GitHub API (PyGithub)

**処理フロー**:
1. 学習結果をMarkdown形式に整形
2. GitHub APIでリポジトリの`training_history/`ディレクトリにコミット
3. 元のIssueにコメントとして結果を投稿
4. コミットハッシュを返す

**入力**:
```json
{
  "training_job_name": "train-20250110-123456",
  "training_config": {...},
  "evaluation_results": {...},
  "model_s3": "...",
  "model_version": "v1.2.3"
}
```

**出力**:
```json
{
  "commit_sha": "abc123...",
  "file_path": "training_history/train-20250110-123456.md",
  "commit_url": "https://github.com/org/repo/commit/abc123..."
}
```

---

## 3. データフロー設計

### 3.1 エンドツーエンドデータフロー

![Data Flow](diagrams/data_flow.mmd)

**詳細**: [diagrams/data_flow.mmd](diagrams/data_flow.mmd)

### 3.2 S3バケット構造

![S3 Bucket Structure](diagrams/s3_bucket_structure.mmd)

**詳細**: [diagrams/s3_bucket_structure.mmd](diagrams/s3_bucket_structure.mmd)

---

## 4. ワークフロー設計 (Step Functions)

### 4.1 Step Functions State Machine定義

![Step Functions Workflow](diagrams/step_functions_workflow.mmd)

**詳細**: [diagrams/step_functions_workflow.mmd](diagrams/step_functions_workflow.mmd)

**ワークフローの主要ステート**:
- **PrepareData**: データ準備エージェントを実行
- **TrainModel**: SageMaker Training Jobを実行（.sync統合）
- **EvaluateModel**: 評価エージェントを実行
- **JudgeResults**: 判定エージェントを実行
- **DecisionSwitch**: 評価結果に基づく分岐
  - Pass → RegisterModel → WriteHistory → NotifySuccess
  - Retrain → CheckRetryLimit → NotifyOperator → WaitForOperatorInput → IncrementRetry → TrainModel
  - Fail → RollbackModel → NotifyFailure
- **エラーハンドリング**: 各ステートでのCatch設定とエラーステート

**Task Token パターン**:
`WaitForOperatorInput`ステートでは、Task Tokenパターンを使用してオペレータの入力を待機します。オペレータがGitHub Issueにコメントすると、Lambda関数がTask Tokenを使ってワークフローを再開します。

---

## 5. セキュリティ設計

### 5.1 IAMロール設計

#### Lambda Execution Role
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::mlops-bucket/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "sagemaker:CreateTrainingJob",
        "sagemaker:DescribeTrainingJob",
        "sagemaker:CreateModel",
        "sagemaker:CreateModelPackage"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:github-token-*"
    }
  ]
}
```

#### SageMaker Execution Role
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::mlops-bucket/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

### 5.2 シークレット管理

- **GitHub Token**: AWS Secrets Managerに保存
- **Slack Webhook URL**: AWS Secrets Managerに保存
- **API Keys**: AWS Secrets Managerに保存

### 5.3 ネットワークセキュリティ

- Lambda/ECS: VPC内で実行（プライベートサブネット）
- SageMaker: VPC Modeで実行
- S3: VPCエンドポイント経由でアクセス
- Secrets Manager: VPCエンドポイント経由でアクセス

---

## 6. スケーラビリティ設計

### 6.1 並列実行制御

- Step Functions: 同時実行制限（10並列）
- SageMaker Training: アカウントクォータ内で並列実行
- Lambda: 同時実行数制限（Reserved Concurrency）

### 6.2 コスト最適化

- **Spot Instances**: SageMaker Training JobでSpot Instancesを使用
- **S3 Lifecycle Policy**: 古いデータを自動的にGlacierに移行
- **Lambda**: メモリサイズとタイムアウトの最適化

---

## 7. モニタリング・ロギング設計

### 7.1 CloudWatch Metrics

- **Step Functions**: 実行回数、成功率、実行時間
- **SageMaker**: 学習ジョブの成功率、実行時間
- **Lambda**: エラー率、実行時間、スロットリング

### 7.2 CloudWatch Logs

- すべてのLambda関数のログ
- SageMaker Training Jobのログ
- Step Functions実行履歴

### 7.3 アラート設定

- 学習ジョブ失敗時
- Lambda関数エラー率が閾値超過時
- Step Functions実行失敗時

---

## 8. デプロイメント戦略

### 8.1 Infrastructure as Code (IaC)

**AWS CDK (Python)** を使用してインフラをコード化

```
project/
├── cdk/
│   ├── app.py
│   ├── stacks/
│   │   ├── pipeline_stack.py
│   │   ├── storage_stack.py
│   │   ├── compute_stack.py
│   │   └── monitoring_stack.py
│   └── requirements.txt
```

### 8.2 CI/CD Pipeline

- **GitHub Actions**: コードプッシュ時の自動テスト・デプロイ
- **AWS CodePipeline**: CDKスタックのデプロイ

---

## 9. 拡張性の考慮事項

### 9.1 将来的な拡張

- **マルチリージョン対応**: 複数のAWSリージョンでの実行
- **ハイブリッドクラウド**: オンプレミスとクラウドの連携
- **AutoML統合**: SageMaker Autopilotとの統合
- **リアルタイム推論**: SageMaker Endpointへの自動デプロイ

### 9.2 プラグイン機構

- カスタムエージェントの追加
- カスタム評価指標の追加
- カスタム通知先の追加

---

## 10. 技術スタック

### 10.1 AWSサービス

| サービス | 用途 |
|---|---|
| AWS Lambda | エージェント実装（軽量処理） |
| Amazon ECS Fargate | エージェント実装（大規模処理） |
| AWS Step Functions | ワークフローオーケストレーション |
| Amazon SageMaker | 機械学習モデルの学習・評価 |
| Amazon S3 | データ・モデル保存 |
| SageMaker Model Registry | モデルバージョン管理 |
| Amazon SNS | 通知 |
| AWS Secrets Manager | シークレット管理 |
| Amazon CloudWatch | モニタリング・ロギング |
| AWS CloudTrail | 監査ログ |
| Amazon API Gateway | Webhook受信 |
| Amazon EventBridge | イベント駆動処理 |

### 10.2 プログラミング言語・フレームワーク

- **Python 3.9+**: Lambda/エージェント実装
- **Boto3**: AWS SDK
- **PyGithub**: GitHub API連携
- **scikit-learn**: 機械学習（教師あり・教師なし）
- **TensorFlow/PyTorch**: ディープラーニング
- **Ray RLlib**: 強化学習
- **AWS CDK**: IaC

---

---

## 11. MCP (Model Context Protocol) 対応設計

### 11.1 MCP化の背景

現在の設計では、データ前処理・モデル学習・モデル評価などの専門機能がAWS Lambda/ECS Fargateに直接実装されていますが、以下の課題があります:

- 再利用性の欠如
- 保守性の低下
- テストの困難さ
- ベンダーロックイン

これらを解決するため、専門機能を**Model Context Protocol (MCP)** サーバーとして実装します。

### 11.2 統合MLOps MCPサーバー設計

**1つの統合MLOps MCPサーバー**として実装し、**6つのCapability（機能群）**を提供します。

#### 統合アプローチの主要メリット

- 🎯 **運用の簡素化**: 1つのサーバープロセス/コンテナのみ管理
- 🎯 **デプロイの簡素化**: 1つのデプロイパイプラインで完結
- 🎯 **リソース効率**: メモリ・CPUを共有、オーバーヘッド削減
- 🎯 **MCP接続の最小化**: 1つのMCP接続で全ツールにアクセス

#### 6つのCapability

**Capability 1: Data Preparation**

- データ前処理・特徴量エンジニアリング
- 提供ツール: `load_dataset`, `validate_data`, `preprocess_supervised/unsupervised/reinforcement`, `feature_engineering`, `split_dataset`

**Capability 2: ML Training**

- 機械学習モデルの学習
- 提供ツール: 教師あり学習、教師なし学習、強化学習の各アルゴリズム実装

**Capability 3: ML Evaluation**

- モデルの評価・可視化
- 提供ツール: `evaluate_classifier/regressor/clustering/reinforcement`, `compare_models`, `generate_evaluation_report`

**Capability 4: GitHub Integration**

- GitHub連携機能の統合（Issue管理、ラベル管理、リポジトリ操作、Webhook処理）
- 影響: Issue Detector Agent、History Writer Agent

**Capability 5: Model Registry**

- モデルバージョン管理・レジストリ操作
- 影響: Training Agent、Rollback Agent

**Capability 6: Notification**

- 通知チャネルの統合管理（Slack、Email、Teams、Discord）
- 通知テンプレート管理
- 影響: Notification Agent

### 11.3 統合MCP対応アーキテクチャ

```text
Lambda Agents (MCP Clients)
    ↓ MCP Protocol (JSON-RPC over stdio/SSE)
    ↓ 1つのMCP接続のみ
統合MLOps MCPサーバー (ECS Fargate or Lambda)
    ├─ Capability 1: Data Preparation
    ├─ Capability 2: ML Training
    ├─ Capability 3: ML Evaluation
    ├─ Capability 4: GitHub Integration
    ├─ Capability 5: Model Registry
    └─ Capability 6: Notification
    ↓ AWS SDK / GitHub API / Slack API / Email API
S3 / SageMaker / GitHub / Slack / Email / その他サービス
```

**詳細**: [mcp_design.md](mcp_design.md) および [mcp_extended_design.md](mcp_extended_design.md) を参照

### 11.4 期待される効果

**統合アプローチによる追加メリット**:

- ✅ **運用コスト削減**: 6プロセス→1プロセスにより、運用負荷が大幅に削減
- ✅ **デプロイ時間短縮**: 6デプロイ→1デプロイにより、リリースサイクル高速化
- ✅ **インフラコスト削減**: リソース共有により、メモリ・CPU使用量を最適化
- ✅ **Agent実装の簡素化**: 1つのMCP接続のみで全機能にアクセス可能

**共通メリット**:

- ✅ **再利用性**: 標準プロトコルに準拠し、他プロジェクトでも利用可能
- ✅ **保守性**: 機能追加・変更が1つのサーバー内で完結
- ✅ **テスト容易性**: ローカル環境で全Capabilityを一度にテスト可能
- ✅ **拡張性**: 新しいCapability・ツールを容易に追加可能
- ✅ **ベンダーニュートラル**: クラウドプロバイダーに依存しない設計
- ✅ **GitHub連携の一元化**: GitHub APIコードが1箇所に集約
- ✅ **モデルガバナンス強化**: モデルバージョン管理が標準化
- ✅ **通知チャネル統合**: Slack/Email/Teams/Discord等を一元管理

**MCP化範囲**: 統合MCPサーバーでシステムの約90%の機能をMCP化、残り10%（Judge Agentなど）は既存実装を継続

### 11.5 セキュリティ設計

統合MCPサーバーのセキュリティ設計については、[mcp_design.md セクション9](mcp_design.md#9-セキュリティ設計)を参照してください。

**主要なセキュリティ対策**:

- ✅ **認証・認可**: IAMロールベース認証、最小権限原則
- ✅ **データ暗号化**: S3バケット暗号化（SSE-KMS）、通信時TLS 1.2+
- ✅ **シークレット管理**: AWS Secrets Managerで一元管理
- ✅ **ネットワーク分離**: VPC内プライベートサブネット配置、Security Group制限
- ✅ **監査ログ**: CloudTrailとCloudWatch Logsで全操作を記録
- ✅ **脆弱性管理**: 依存ライブラリとDockerイメージの定期スキャン

---

## 12. 変更履歴

| バージョン | 日付 | 変更内容 | 作成者 |
| --- | --- | --- | --- |
| 0.1 | 2025-12-27 | 初版発行（統合MCP対応アーキテクチャ設計） | - |
