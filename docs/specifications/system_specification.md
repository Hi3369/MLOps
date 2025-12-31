# システム仕様書: GitHub Issue駆動型MLOpsシステム

**バージョン**: 1.0
**作成日**: 2025-12-30

**注**: 本ドキュメントで使用される技術用語・略語の定義は[用語集](../others/glossary.md)を参照してください。

---

## 1. プロジェクト概要

### 1.1 目的

GitHub Issueをトリガーとして、AWS Step FunctionsとAmazon SageMakerを活用したエージェントベースのMLOpsパイプラインを構築する。

### 1.2 システム名

GitHub-Driven MLOps Pipeline with Agent-based Orchestration

### 1.3 対象ユーザー

- データサイエンティスト
- MLエンジニア
- DevOpsエンジニア

---

## 2. 機能要件

### 2.1 MLOpsワークフロー要件

本システムは、以下の7段階のMLOpsライフサイクルを実現します。

#### 2.1.1 📥 フェーズ1: データ収集・前処理

**FR-001: データソース統合**

- S3、RDS、DynamoDB、外部API等の複数データソースからのデータ取得
- データカタログ（AWS Glue Data Catalog）によるメタデータ管理
- データ取得ジョブのスケジュール実行

**FR-002: データクリーニング**

- 欠損値処理（削除、平均値補完、中央値補完、モード補完）
- 異常値検出と除去（IQR法、Z-score法）
- 重複データの検出と削除
- データ品質レポートの生成

**FR-003: 特徴量エンジニアリング**

- 特徴量生成（集約、結合、変換）
- 特徴量選択（相関分析、重要度ベース選択）
- カテゴリカル変数のエンコーディング（One-Hot、Label、Target）
- 数値変数の正規化・標準化
- 特徴量定義ドキュメントの自動生成

**FR-004: データバージョニング**

- S3バージョニングによるデータ履歴管理
- DVC（Data Version Control）統合（オプション）
- データセット分割（train/validation/test）のバージョン管理
- データ系譜（Data Lineage）の記録

#### 2.1.2 🧪 フェーズ2: モデル開発（実験）

**FR-005: 実験管理**

- MLflow Tracking / SageMaker Experiments統合
- 実験パラメータの記録（ハイパーパラメータ、データセットバージョン、コードバージョン）
- 実験メトリクスの記録（精度、損失、学習時間等）
- 実験成果物の管理（モデル、ログ、可視化結果）

**FR-006: ハイパーパラメータ最適化**

- Grid Search（全探索）
- Random Search（ランダム探索）
- Bayesian Optimization（ベイズ最適化）
- SageMaker Automatic Model Tuning統合
- 最適パラメータの自動選択

**FR-007: 学習方式選択**

システムは以下の3種類の学習方式をサポート：

1. **教師あり学習（Supervised Learning）**
   - 分類（Classification）: Random Forest, XGBoost, Neural Network
   - 回帰（Regression）: Linear Regression, XGBoost, Neural Network

2. **教師なし学習（Unsupervised Learning）**
   - クラスタリング（Clustering）: K-Means, DBSCAN
   - 次元削減（Dimensionality Reduction）: PCA, t-SNE

3. **強化学習（Reinforcement Learning）**
   - PPO (Proximal Policy Optimization)
   - DQN (Deep Q-Network)
   - A3C (Asynchronous Advantage Actor-Critic)

**FR-008: SageMaker学習ジョブ実行**

- SageMaker Training Jobの起動と監視
- 分散学習のサポート
- 学習進捗のリアルタイム監視
- 学習ログのCloudWatch Logsへの出力
- GPU/CPU リソースの動的割り当て

#### 2.1.3 🧹 フェーズ3: モデル検証・テスト

**FR-009: モデル精度評価**

- 評価指標の算出：
  - 分類: Accuracy, Precision, Recall, F1-Score, AUC-ROC
  - 回帰: RMSE, MAE, R², MAPE
  - クラスタリング: Silhouette Score, Davies-Bouldin Index
  - 強化学習: Average Reward, Episode Length
- 混同行列、ROC曲線、学習曲線の生成
- 評価レポートの自動生成

**FR-010: バイアスチェック**

- 公平性評価（Fairness Indicators）
- グループ間の精度差分析
- バイアス検出レポートの生成
- SageMaker Clarify統合

**FR-011: データドリフト検知準備**

- ベースライン統計の記録（平均、分散、分布等）
- 特徴量分布の保存
- ドリフト検知用メタデータの生成

**FR-012: CI/CD自動テスト**

- ユニットテスト（モデル関数、前処理関数）
- 統合テスト（パイプライン全体）
- モデル性能テスト（最低精度保証）
- テストカバレッジ: 80%以上
- テストレポートの生成

**FR-013: モデル説明可能性**

- SHAP（SHapley Additive exPlanations）による特徴量重要度分析
- LIME（Local Interpretable Model-agnostic Explanations）
- モデル説明レポートの生成

#### 2.1.4 📦 フェーズ4: モデルパッケージング

**FR-014: モデルAPI化**

- REST API エンドポイントの生成
- gRPC サポート（オプション）
- API仕様書の自動生成（OpenAPI/Swagger）
- 推論レスポンスタイムの最適化

**FR-015: モデルコンテナ化**

- Dockerイメージの自動生成
- SageMaker Inference Container対応
- マルチステージビルドによるイメージサイズ最適化
- 依存関係の明確化（requirements.txt、Dockerfile）

**FR-016: モデルレジストリ管理**

- SageMaker Model Registry / MLflow Model Registry統合
- モデルメタデータの記録（精度、パラメータ、学習日時等）
- セマンティックバージョニング（v1.0.0、v1.1.0等）
- モデル系譜（Model Lineage）の記録
- 最低5世代のモデル保持

#### 2.1.5 🚀 フェーズ5: デプロイ（リリース）

**FR-017: デプロイ戦略**

- **A/Bテスト**: 新旧モデルを並行稼働し効果を比較
- **カナリアリリース**: 一部トラフィック（10%→50%→100%）で段階的展開
- **ブルー/グリーンデプロイメント**: 新環境構築後に切り替え
- デプロイ戦略の選択はGitHub Issueで指定可能

**FR-018: 本番環境デプロイ**

- SageMaker Endpoint へのデプロイ
- ECS Fargate / Lambda へのデプロイ（オプション）
- Auto Scaling設定（負荷に応じた自動スケール）
- ヘルスチェックの実装

**FR-019: CI/CD パイプライン**

- GitHub Actions / AWS CodePipeline統合
- Infrastructure as Code（CloudFormation、CDK、Terraform）
- 自動デプロイメント（承認後）
- デプロイメントログの記録

**FR-020: ロールバック機能**

- ワンクリックロールバック
- 自動ロールバック（エラー率が閾値を超えた場合）
- ロールバック履歴の記録

#### 2.1.6 🔍 フェーズ6: モニタリング（運用）

**FR-021: システムメトリクス監視**

- レスポンスタイム（P50、P95、P99）の監視
- エラー率（4xx、5xx）の監視
- スループット（RPS: Requests Per Second）の監視
- リソース使用率（CPU、メモリ、GPU）の監視
- CloudWatch Dashboard による可視化

**FR-022: モデルメトリクス監視**

- 推論精度の劣化検知
- データドリフト検知（入力データ分布の変化）
- コンセプトドリフト検知（入力と出力の関係の変化）
- 予測分布の変化検知
- SageMaker Model Monitor統合

**FR-023: アラート設定**

- CloudWatch Alarms設定
- Slack / Email / PagerDuty への通知
- GitHub Issueの自動作成（重大な問題発生時）
- アラート閾値のカスタマイズ

**FR-024: ダッシュボード**

- リアルタイムメトリクス可視化
- 過去データとの比較グラフ
- Grafana統合（オプション）

#### 2.1.7 🔄 フェーズ7: 継続的改善（再トレーニング）

**FR-025: 自動再トレーニングトリガー**

- **データ変更トリガー**: 新しいデータがS3に追加された時
- **コード変更トリガー**: モデルコードがGitにプッシュされた時
- **スケジュールトリガー**: 週次、月次等の定期実行
- **メトリクス劣化トリガー**: 精度が閾値を下回った時
- **ドリフト検知トリガー**: データドリフトが検出された時

**FR-026: 自動再学習パイプライン**

- Step Functions / Apache Airflow によるパイプライン自動実行
- 新データでの自動学習
- 新旧モデルの自動比較
- 改善が認められた場合のみ自動デプロイ

**FR-027: モデルバージョン管理**

- セマンティックバージョニング（v1.0.0 → v1.1.0 → v2.0.0）
- バージョン間の差分レポート
- パフォーマンス比較レポート（旧モデル vs 新モデル）

**FR-028: フィードバックループ**

- 本番推論データの収集
- ラベル付けされたデータの学習データへの追加
- 継続的なモデル改善

#### 2.1.8 トリガー機能

**FR-029: GitHub Issue検知**

- GitHubリポジトリに特定のラベル（例: `mlops:train`）が付いたIssueが作成されたら自動的にMLパイプラインを起動
- Issue内に学習パラメータ（モデル種類、学習方法、ハイパーパラメータ、デプロイ戦略等）を記載
- Webhookまたはポーリングによる検知

#### 2.1.9 オーケストレーション機能

**FR-030: Step Functions統合**

- AWS Step Functionsによる7段階ワークフローの制御
- ステート管理（データ収集→実験→検証→パッケージング→デプロイ→モニタリング→再学習）
- エラーハンドリングとリトライロジック
- 各フェーズ間のデータ受け渡し

**FR-031: Agentベースアーキテクチャ**

- 各処理を独立したエージェント（Lambda/Container）として実装
- エージェント間の疎結合な連携
- スケーラビリティの確保
- MCP（Model Context Protocol）による標準化された通信

**FR-032: 対話型調整機能**

- 適合率が閾値未満の場合、オペレータに通知（Slack/Email/GitHub Comment）
- オペレータがGitHub Issueコメントで学習設定を調整
- 調整内容を元に自動再学習を実行
- 最大再学習回数の設定（デフォルト: 3回）

**FR-033: 学習履歴のGitHub保存**

- 学習結果（精度、パラメータ、実行時間等）をMarkdown形式で生成
- GitHubリポジトリの`training_history/`ディレクトリにコミット
- 元のIssueへのコメントとして結果を投稿
- バージョン管理による履歴追跡

---

## 3. 非機能要件

### 3.1 パフォーマンス

**NFR-001: 応答時間**

- Issue検知からデータ準備開始まで: 5分以内
- 学習完了から評価結果通知まで: 10分以内（小規模データセットの場合）
- 推論レスポンスタイム: P95で100ms以内
- モデルデプロイ時間: 15分以内

**NFR-002: スケーラビリティ**

- 同時実行可能な学習ジョブ数: 10ジョブ以上
- データサイズ: 最大1TB
- 推論エンドポイント: Auto Scalingで最大100インスタンス
- 並列実験実行数: 最大20実験

**NFR-003: スループット**

- 推論エンドポイント: 最小1000 RPS
- データ前処理: 100GB/時間以上
- モデル評価: 1万件/分以上

### 3.2 可用性

**NFR-004: システム稼働率**

- 目標稼働率: 99.5%以上（学習パイプライン）
- 推論エンドポイント稼働率: 99.9%以上
- 学習失敗時の自動リトライ: 最大3回
- デプロイ失敗時の自動ロールバック

**NFR-005: 災害対策**

- マルチAZ構成
- S3クロスリージョンレプリケーション（重要データ）
- RPO（Recovery Point Objective）: 1時間
- RTO（Recovery Time Objective）: 4時間

### 3.3 セキュリティ

**NFR-006: アクセス制御**

- IAMロールベースのアクセス制御（最小権限の原則）
- S3バケットの暗号化（SSE-KMS）
- データ転送時のTLS 1.2以上使用
- VPC内での閉域ネットワーク構成

**NFR-007: 認証・認可**

- GitHub Tokenの安全な管理（AWS Secrets Manager）
- API Key/トークンのローテーション（90日ごと）
- MFA（多要素認証）の強制
- サービス間通信の相互認証

**NFR-008: 監査**

- CloudTrailによる全操作ログの記録
- 学習履歴の改ざん防止（署名付きコミット）
- アクセスログの保持（最低1年間）
- 定期的なセキュリティ監査

**NFR-009: コンプライアンス**

- GDPR対応（個人データ削除機能）
- データ匿名化機能
- バイアス検出とレポーティング

### 3.4 保守性

**NFR-010: ログ管理**

- CloudWatch Logsへの統合
- 構造化ログ（JSON形式）
- ログ保持期間: 90日間（アーカイブは1年間）
- ログレベル: DEBUG, INFO, WARN, ERROR

**NFR-011: モニタリング**

- CloudWatch Metricsでの監視
- カスタムメトリクスの記録
- 異常検知時のアラート通知
- ダッシュボードによる可視化

**NFR-012: デバッグ性**

- 分散トレーシング（AWS X-Ray）
- エラー時のコンテキスト情報記録
- 再現可能なテスト環境

**NFR-013: ドキュメント**

- API仕様書の自動生成
- アーキテクチャダイアグラムの保守
- ランブック（障害対応手順書）の整備

### 3.5 テスト容易性

**NFR-014: テスト自動化**

- ユニットテストカバレッジ: 80%以上
- 統合テストの自動実行
- CI/CDパイプラインでの自動テスト
- モックデータによるテスト環境

**NFR-015: テスト環境**

- 本番相当のステージング環境
- データのサニタイズ機能
- テストデータの自動生成

### 3.6 移植性

**NFR-016: クラウド非依存設計**

- MCP（Model Context Protocol）による標準化
- コンテナ化によるポータビリティ
- IaC（Infrastructure as Code）による環境再現性
- オープンソースツールの優先使用

**NFR-017: ベンダーロックイン回避**

- マルチクラウド対応を考慮した設計
- データエクスポート機能
- 標準フォーマットでのデータ保存

### 3.7 運用性

**NFR-018: デプロイメント**

- ゼロダウンタイムデプロイメント
- カナリアリリースによる段階的展開
- 自動ロールバック機能
- デプロイメント履歴の記録

**NFR-019: バックアップ**

- 日次自動バックアップ
- バックアップの定期的なリストアテスト
- バックアップ保持期間: 30日間

**NFR-020: コスト最適化**

- 未使用リソースの自動削除
- Spot Instanceの活用（学習ジョブ）
- S3ライフサイクルポリシー
- コスト異常検知アラート

---

## 4. システム制約

### 4.1 技術制約

- **CON-001**: AWS環境での実装
- **CON-002**: SageMaker対応のフレームワーク使用（TensorFlow, PyTorch, scikit-learn等）
- **CON-003**: Python 3.11以上
- **CON-004**: MCP（Model Context Protocol）v1.0以上
- **CON-005**: Docker対応環境

### 4.2 ビジネス制約

- **CON-006**: Phase 1開発期間: 6週間（コアMLOps機能）
- **CON-007**: Phase 2開発期間: 6週間（統合機能）
- **CON-008**: Phase 3開発期間: 2週間（E2Eテスト・最適化）
- **CON-009**: 月間AWS利用予算: $XXX（要調整）

### 4.3 運用制約

- **CON-010**: 本番環境は24時間365日稼働
- **CON-011**: メンテナンスウィンドウ: 週次2時間（日曜深夜）
- **CON-012**: 変更管理プロセスの遵守

---

## 5. アーキテクチャ設計

### 5.1 システムアーキテクチャ図

```mermaid
graph TB
    subgraph "GitHub"
        Issue[GitHub Issue<br/>mlops:train]
    end

    subgraph "AWS Cloud"
        subgraph "トリガー層"
            Webhook[API Gateway<br/>Webhook]
            IssueDetector[Issue Detector<br/>Lambda]
        end

        subgraph "オーケストレーション層"
            StepFunctions[Step Functions<br/>MLOps Workflow]
        end

        subgraph "エージェント層（MCP Client）"
            DataPrepAgent[Data Preparation<br/>Agent Lambda]
            TrainingAgent[Training<br/>Agent Lambda]
            EvalAgent[Evaluation<br/>Agent Lambda]
            JudgeAgent[Judge<br/>Agent Lambda]
            PackageAgent[Packaging<br/>Agent Lambda]
            DeployAgent[Deployment<br/>Agent Lambda]
            MonitorAgent[Monitor<br/>Agent Lambda]
            RetrainAgent[Retrain<br/>Agent Lambda]
            NotifyAgent[Notification<br/>Agent Lambda]
            HistoryAgent[History Writer<br/>Agent Lambda]
        end

        subgraph "統合MCP層"
            MCPServer[統合MLOps MCP Server<br/>ECS Fargate/Lambda]
        end

        subgraph "AWSサービス層"
            S3[(S3<br/>Data/Models)]
            SageMaker[SageMaker<br/>Training/Endpoint]
            ModelRegistry[SageMaker<br/>Model Registry]
            CloudWatch[CloudWatch<br/>Logs/Metrics]
            Secrets[Secrets Manager]
            SNS[SNS<br/>Notifications]
        end
    end

    subgraph "外部サービス"
        Slack[Slack]
        Email[Email]
    end

    Issue -->|Webhook| Webhook
    Webhook --> IssueDetector
    IssueDetector --> StepFunctions

    StepFunctions --> DataPrepAgent
    StepFunctions --> TrainingAgent
    StepFunctions --> EvalAgent
    StepFunctions --> JudgeAgent
    StepFunctions --> PackageAgent
    StepFunctions --> DeployAgent
    StepFunctions --> MonitorAgent
    StepFunctions --> RetrainAgent
    StepFunctions --> NotifyAgent
    StepFunctions --> HistoryAgent

    DataPrepAgent -->|MCP Protocol| MCPServer
    TrainingAgent -->|MCP Protocol| MCPServer
    EvalAgent -->|MCP Protocol| MCPServer
    PackageAgent -->|MCP Protocol| MCPServer
    DeployAgent -->|MCP Protocol| MCPServer
    MonitorAgent -->|MCP Protocol| MCPServer
    RetrainAgent -->|MCP Protocol| MCPServer
    NotifyAgent -->|MCP Protocol| MCPServer
    HistoryAgent -->|MCP Protocol| MCPServer

    MCPServer --> S3
    MCPServer --> SageMaker
    MCPServer --> ModelRegistry
    MCPServer --> CloudWatch
    MCPServer --> Secrets
    MCPServer --> SNS

    NotifyAgent --> Slack
    NotifyAgent --> Email
    HistoryAgent --> Issue
```

### 5.2 エージェントベースアーキテクチャ

本システムは、各処理を独立したエージェント（Agent）として実装し、統合MLOps MCPサーバーを介してAWSサービスや外部サービスと連携します。

**エージェント一覧（11個）**:

| エージェント名             | 責務                               | MCP化    |
| -------------------------- | ---------------------------------- | -------- |
| 1. Issue Detector Agent    | GitHub Issueの検知とパース         | ✅ MCP   |
| 2. Data Preparation Agent  | 学習データの準備と前処理           | ✅ MCP   |
| 3. Training Agent          | SageMakerを使った学習実行          | ✅ MCP   |
| 4. Evaluation Agent        | モデルの評価                       | ✅ MCP   |
| 5. Judge Agent             | 評価結果の判定と次アクション決定   | ❌ Lambda |
| 6. Packaging Agent         | モデルのコンテナ化とレジストリ登録 | ✅ MCP   |
| 7. Deployment Agent        | モデルのデプロイとロールバック     | ✅ MCP   |
| 8. Monitor Agent           | モデルとシステムのモニタリング     | ✅ MCP   |
| 9. Retrain Agent           | 自動再学習トリガー管理             | ✅ MCP   |
| 10. Notification Agent     | オペレータへの通知                 | ✅ MCP   |
| 11. History Writer Agent   | 学習履歴のGitHub保存               | ✅ MCP   |

**MCP化率**: 10/11エージェント（約91%）

### 5.3 統合MLOps MCPサーバー設計

**1つの統合MLOps MCPサーバー**として実装し、**11個のCapability（機能群）**を提供します。

#### Capability一覧

1. **GitHub Integration** - Issue検知・パース・ワークフロー起動
2. **Workflow Optimization** - モデル特性分析・最適化提案（将来実装）
3. **Data Preparation** - データ前処理・特徴量エンジニアリング
4. **Model Training** - 機械学習モデルの学習
5. **Model Evaluation** - モデル評価・可視化・バイアス検出
6. **Model Packaging** - モデルコンテナ化・ECR登録
7. **Model Deployment** - モデルデプロイ・エンドポイント管理
8. **Model Monitoring** - パフォーマンス監視・ドリフト検出
9. **Retrain Management** - 再学習トリガー判定・ワークフロー起動
10. **Notification** - 外部通知チャネル統合
11. **History Management** - 学習履歴記録・GitHub履歴管理

#### 統合アプローチのメリット

- 🎯 **運用の簡素化**: 1つのサーバープロセス/コンテナのみ管理
- 🎯 **デプロイの簡素化**: 1つのデプロイパイプラインで完結
- 🎯 **リソース効率**: メモリ・CPUを共有、オーバーヘッド削減
- 🎯 **MCP接続の最小化**: 1つのMCP接続で全ツールにアクセス

### 5.4 データフロー設計

#### S3バケット構造

```text
s3://mlops-bucket/
├── datasets/
│   ├── {dataset_id}/
│   │   ├── raw/
│   │   │   ├── data.csv
│   │   │   └── metadata.json
│   │   ├── processed/
│   │   │   ├── train/
│   │   │   ├── validation/
│   │   │   └── test/
│   │   └── versions/
│   │       ├── v1.0.0/
│   │       └── v1.1.0/
│   └── ...
├── models/
│   ├── {model_id}/
│   │   ├── {version}/
│   │   │   ├── model.tar.gz
│   │   │   ├── model_metadata.json
│   │   │   └── inference_code/
│   │   └── ...
│   └── ...
├── evaluations/
│   ├── {training_id}/
│   │   ├── results.json
│   │   ├── confusion_matrix.png
│   │   ├── roc_curve.png
│   │   └── shap_values.pkl
│   └── ...
└── logs/
    ├── {training_id}/
    │   ├── preprocessing.log
    │   ├── training.log
    │   └── evaluation.log
    └── ...
```

### 5.5 セキュリティ設計

#### IAMロール設計

**Lambda Execution Role（エージェント用）**

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
        "sagemaker:CreateModelPackage",
        "sagemaker:CreateEndpoint",
        "sagemaker:UpdateEndpoint",
        "sagemaker:DescribeEndpoint"
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
      "Resource": "arn:aws:secretsmanager:*:*:secret:mlops/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "states:StartExecution"
      ],
      "Resource": "arn:aws:states:*:*:stateMachine:mlops-workflow"
    }
  ]
}
```

#### シークレット管理

AWS Secrets Managerで以下のシークレットを管理:

- **GitHub Token**: `mlops/github-token`
- **Slack Webhook URL**: `mlops/slack-webhook`
- **Email SMTP Credentials**: `mlops/email-smtp`
- **API Keys**: `mlops/api-keys`

#### ネットワークセキュリティ

- **Lambda/ECS**: VPC内で実行（プライベートサブネット）
- **SageMaker**: VPC Modeで実行
- **S3**: VPCエンドポイント経由でアクセス
- **Secrets Manager**: VPCエンドポイント経由でアクセス
- **Security Group**: 最小限のインバウンド/アウトバウンドルール

#### データ暗号化

- **S3バケット**: SSE-KMS暗号化
- **通信**: TLS 1.2以上
- **SageMaker**: モデルとデータの暗号化

#### 監査ログ

- **CloudTrail**: 全API操作の記録
- **CloudWatch Logs**: エージェント実行ログ
- **アクセスログ保持**: 最低1年間

### 5.6 技術スタック

#### AWSサービス

| サービス                 | 用途                             |
| ------------------------ | -------------------------------- |
| AWS Lambda               | エージェント実装（軽量処理）     |
| Amazon ECS Fargate       | 統合MCPサーバー、大規模処理      |
| AWS Step Functions       | ワークフローオーケストレーション |
| Amazon SageMaker         | 機械学習モデルの学習・評価・デプロイ |
| Amazon S3                | データ・モデル保存               |
| SageMaker Model Registry | モデルバージョン管理             |
| Amazon SNS               | 通知                             |
| AWS Secrets Manager      | シークレット管理                 |
| Amazon CloudWatch        | モニタリング・ロギング           |
| AWS CloudTrail           | 監査ログ                         |
| Amazon API Gateway       | Webhook受信                      |
| Amazon EventBridge       | イベント駆動処理                 |
| Amazon ECR               | Dockerイメージレジストリ         |

#### プログラミング言語・フレームワーク

- **Python 3.11+**: Lambda/エージェント実装、統合MCPサーバー
- **Boto3**: AWS SDK
- **MCP Python SDK**: MCP Protocol実装
- **PyGithub**: GitHub API連携
- **scikit-learn**: 機械学習（教師あり・教師なし）
- **XGBoost**: 勾配ブースティング
- **TensorFlow/PyTorch**: ディープラーニング
- **Ray RLlib**: 強化学習
- **AWS CDK**: IaC
- **pytest**: テストフレームワーク

---

## 6. ユースケース: 自動運転向けコンピュータビジョン

本システムは、自動運転領域のコンピュータビジョンタスクに対応します。以下、YOLOX、KITTI、VAD（Vision-based Autonomous Driving）
を用いた具体的なユースケースを示します。

### 6.1 対象タスクと使用モデル

#### 6.1.1 物体検出: YOLOX

**タスク**: 道路上の車両、歩行者、自転車、信号機等のリアルタイム検出

**モデル**: YOLOX (YOLO eXceeding YOLO series in 2021)

**特徴**:

- Anchor-freeアプローチで高速推論
- YOLOX-Nano/Tiny/S/M/L/Xの6サイズ展開（エッジデバイス～サーバー対応）
- COCO datasetでYOLOv5を上回る精度
- 自動運転に必要な30FPS以上の推論速度を実現

**本システムでの実装**:

- **学習タスク**: `supervised_learning` (分類: 物体クラス、回帰: Bounding Box座標)
- **データセット**: KITTI、BDD100K、Waymo Open Dataset等
- **前処理**: Mosaic Augmentation、MixUp、HSV Color Jitter
- **評価指標**: mAP@0.5、mAP@0.5:0.95、Recall、Precision、Inference Latency

**GitHub Issue設定例**:

```yaml
model_type: supervised_learning
algorithm: yolox
variant: yolox-m  # Nano/Tiny/S/M/L/X
dataset:
  name: kitti_object_detection
  s3_uri: s3://mlops-datasets/kitti/object/
  train_split: 7481
  val_split: 7518
hyperparameters:
  input_size: [640, 640]
  batch_size: 32
  epochs: 300
  lr: 0.01
  warmup_epochs: 5
  mosaic_prob: 1.0
  mixup_prob: 1.0
augmentation:
  - mosaic
  - mixup
  - hsv_jitter
  - random_flip
evaluation_metrics:
  - mAP@0.5
  - mAP@0.5:0.95
  - inference_latency_ms
deployment:
  target: sagemaker_endpoint
  instance_type: ml.g4dn.xlarge  # GPU推論
  auto_scaling:
    min_instances: 1
    max_instances: 10
    target_latency_ms: 50
```

#### 6.1.2 3D物体検出: KITTI 3D Object Detection

**タスク**: カメラ画像とLiDAR点群から3D Bounding Boxを推定

**データセット**: KITTI Vision Benchmark Suite

**モデルアーキテクチャ例**:

- PointPillars (LiDAR点群ベース)
- MonoDETR (単眼カメラ画像ベース)
- BEVFormer (Bird's Eye View変換ベース)

**KITTI データセット構造**:

```text
s3://mlops-datasets/kitti/
├── object/                    # 3D物体検出
│   ├── training/
│   │   ├── image_2/          # 左カメラ画像（7481枚）
│   │   ├── image_3/          # 右カメラ画像（ステレオ）
│   │   ├── velodyne/         # LiDAR点群（.bin）
│   │   ├── calib/            # カメラ・LiDARキャリブレーション
│   │   └── label_2/          # 3D Bounding Box アノテーション
│   └── testing/
│       ├── image_2/          # テスト画像（7518枚）
│       ├── velodyne/
│       └── calib/
├── tracking/                  # 物体追跡
│   ├── training/
│   └── testing/
└── depth/                     # 深度推定
    ├── train/
    └── val/
```

**本システムでの実装**:

- **学習タスク**: `supervised_learning` (3D Bounding Box回帰 + クラス分類)
- **前処理**:
  - LiDAR点群のVoxelization
  - カメラ画像の正規化・リサイズ
  - Data Augmentation: Random Flip、Random Rotation、Global Scaling
- **評価指標**:
  - 3D AP (Average Precision): Easy/Moderate/Hard
  - BEV AP (Bird's Eye View)
  - AOS (Average Orientation Similarity)

**FR-034: KITTI データ前処理サポート**

システムは以下のKITTI固有の前処理をサポートする:

- LiDAR点群のロード（.bin形式）
- カメラ・LiDARキャリブレーション行列の適用
- 3D Bounding BoxのCamera座標系⇔LiDAR座標系変換
- Point Cloud範囲フィルタリング（X: 0～70m, Y: -40～40m, Z: -3～1m）

#### 6.1.3 Vision-based Autonomous Driving (VAD)

**タスク**: End-to-Endの自動運転（画像入力 → 車両制御出力）

**アプローチ**:

1. **Imitation Learning**: 人間のドライバーの運転データから学習
2. **Reinforcement Learning**: シミュレータ環境（CARLA、AirSim等）で報酬最大化

**VAD タスクの分類**:

| サブタスク            | 入力              | 出力                   | 学習タイプ        |
| --------------------- | ----------------- | ---------------------- | ----------------- |
| Lane Detection        | カメラ画像        | 車線ポリライン         | 教師あり          |
| Semantic Segmentation | カメラ画像        | ピクセル単位クラス     | 教師あり          |
| Depth Estimation      | 単眼/ステレオ画像 | 深度マップ             | 教師あり          |
| Path Planning         | BEV Feature Map   | 将来の軌跡座標         | 教師あり          |
| End-to-End Control    | カメラ画像        | ステアリング・加減速   | 模倣学習/強化学習 |

**本システムでの実装例: End-to-End制御**

- **学習タスク**: `reinforcement_learning` または `supervised_learning` (模倣学習)
- **環境**: CARLA Simulator、AirSim
- **入力**: フロントカメラ画像（RGB）、車速、GPS
- **出力**: ステアリング角度、スロットル、ブレーキ
- **ネットワーク**: CNN（特徴抽出）+ LSTM（時系列処理）+ MLP（制御出力）

**FR-035: シミュレータ統合**

システムは以下のシミュレータとの統合をサポートする:

- CARLA Simulator (Python API)
- AirSim (Unreal Engine ベース)
- AWS RoboMaker (Gazebo ベース)

シミュレータからのセンサーデータ（カメラ、LiDAR、IMU等）をS3に自動保存し、学習データとして利用可能。

### 6.2 自動運転向け機能要件

#### FR-036: マルチモーダルデータ処理

システムは以下のセンサーデータを統合処理する:

- **カメラ画像**: RGB、Depth、Thermal
- **LiDAR点群**: .bin、.pcd、.ply形式
- **Radar**: Range-Doppler Map
- **IMU/GPS**: 車両姿勢・位置情報

各センサーデータのタイムスタンプ同期と座標系変換を自動実行。

#### FR-037: BEV (Bird's Eye View) 特徴量生成

カメラ画像・LiDAR点群から統一されたBEV特徴マップを生成:

- LSS (Lift-Splat-Shoot) 手法
- BEVFormer Transformer ベース手法
- 出力: BEV特徴マップ（例: 200x200ピクセル、各ピクセル=0.5m）

#### FR-038: 時系列データ処理

自動運転では過去フレームの情報が重要:

- Temporal Fusion: 過去N フレーム（N=3～10）の特徴量を統合
- Optical Flow: フレーム間の動き推定
- Object Tracking: 物体IDの時間的追跡（DeepSORT、ByteTrack等）

#### FR-039: オンライン学習対応

実車両からのフィードバックデータで継続的に学習:

- Edge Case収集: モデルが誤検出したケースを自動収集
- Active Learning: 不確実性の高いデータを優先的にラベリング
- Incremental Learning: 新規データで既存モデルをFine-tuning

### 6.3 自動運転向け非機能要件

#### NFR-021: リアルタイム推論性能

- **レイテンシ**: エンドツーエンド推論 < 100ms (10Hz以上)
  - 物体検出: < 30ms (30FPS)
  - Lane Detection: < 20ms
  - Path Planning: < 50ms
- **GPU使用率**: < 80%（余裕を持った運用）

#### NFR-022: 安全性とフェイルセーフ

- **モデル不確実性推定**: Bayesian Neural Network、MC Dropout等で予測の信頼度を算出
- **Fallback機構**: モデル推論失敗時、ルールベース制御に切り替え
- **冗長性**: 複数モデルのアンサンブルによる誤検知低減

#### NFR-023: データプライバシー

- **個人情報保護**: カメラ画像から顔・ナンバープレートを自動マスキング
- **データ匿名化**: GPS座標の粗視化（例: 100m単位）
- **GDPR/CCPA準拠**: EU・カリフォルニア州のプライバシー法規制対応

### 6.4 YOLOX + KITTI ワークフロー例

以下、GitHub IssueからYOLOX学習→KITTI評価までの具体的なワークフローを示します。

#### Step 1: GitHub Issue作成

```yaml
title: "[MLOps] YOLOX-M on KITTI Object Detection"
labels: mlops, supervised_learning, yolox, kitti
body: |
  model_type: supervised_learning
  algorithm: yolox
  variant: yolox-m

  dataset:
    name: kitti_object_detection
    s3_uri: s3://mlops-datasets/kitti/object/
    classes: [Car, Pedestrian, Cyclist]
    train_size: 7481
    val_size: 7518

  preprocessing:
    input_size: [640, 640]
    augmentation:
      - mosaic
      - mixup
      - hsv_jitter
      - random_horizontal_flip

  hyperparameters:
    batch_size: 32
    epochs: 300
    lr: 0.01
    weight_decay: 0.0005
    warmup_epochs: 5
    mosaic_prob: 1.0
    mixup_prob: 1.0

  evaluation:
    metrics:
      - mAP@0.5
      - mAP@0.5:0.95
      - recall
      - precision
      - inference_latency_ms
    test_dataset: kitti_val

  deployment:
    target: sagemaker_endpoint
    instance_type: ml.g4dn.xlarge
    auto_scaling:
      min_instances: 1
      max_instances: 5
      target_invocations_per_instance: 100
```

#### Step 2: Data Preparation Agent実行

**タスク**: KITTI データの前処理

**処理内容**:

1. S3からKITTI画像とアノテーションをダウンロード
2. KITTI形式のラベルをYOLOX形式（COCO JSON）に変換
   - KITTI: `<class> <truncated> <occluded> <alpha> <bbox> <dimensions> <location> <rotation_y>`
   - YOLOX: `{"image_id": 1, "category_id": 1, "bbox": [x, y, w, h], ...}`
3. データ拡張の適用
   - Mosaic: 4枚の画像をモザイク状に結合
   - MixUp: 2枚の画像をブレンド
   - HSV Jitter: 色空間の変換
4. Train/Val分割（デフォルト: 80/20）
5. 前処理済みデータをS3に保存

**出力**:

```text
s3://mlops-bucket/processed/yolox-kitti-001/
├── train/
│   ├── images/           # 前処理済み画像
│   └── annotations.json  # COCO形式アノテーション
├── val/
│   ├── images/
│   └── annotations.json
└── metadata.json         # データセット統計情報
```

#### Step 3: Training Agent実行

**タスク**: YOLOXモデルの学習

**処理内容**:

1. SageMaker Training Jobの起動
   - インスタンス: ml.p3.2xlarge (Tesla V100 GPU)
   - コンテナイメージ: YOLOX公式Dockerイメージ + 本システム拡張
2. YOLOX-Mモデルの学習
   - COCO事前学習済み重みからFine-tuning
   - 300エポック学習（Early Stopping有効）
3. 学習ログのCloudWatch Logsへの送信
4. 学習済みモデル（.pth）とONNXモデルをS3に保存

**出力**:

```text
s3://mlops-bucket/models/yolox-kitti-001/
├── yolox_m_kitti.pth       # PyTorch重み
├── yolox_m_kitti.onnx      # ONNX形式（推論最適化）
├── training_log.json       # 学習ログ
└── hyperparameters.json    # ハイパーパラメータ記録
```

#### Step 4: Evaluation Agent実行

**タスク**: KITTI Validation Setでの評価

**処理内容**:

1. 学習済みモデルのロード
2. KITTI Validation Set（7518枚）で推論実行
3. 評価指標の計算
   - mAP@0.5: 0.87
   - mAP@0.5:0.95: 0.65
   - Recall: 0.89
   - Precision: 0.85
   - Inference Latency: 25ms (40FPS)
4. 検出結果の可視化（Bounding Box描画）
5. 混同行列・PR曲線の生成

**出力**:

```text
s3://mlops-bucket/evaluations/yolox-kitti-001/
├── metrics.json
├── confusion_matrix.png
├── pr_curve.png
├── predictions/              # 検出結果画像
│   ├── 000000.png
│   ├── 000001.png
│   └── ...
└── evaluation_report.pdf
```

#### Step 5: Deployment Agent実行

**タスク**: SageMaker Endpointへのデプロイ

**処理内容**:

1. ONNX形式モデルのコンテナ化
2. SageMaker Endpointの作成
   - インスタンス: ml.g4dn.xlarge (NVIDIA T4 GPU)
   - TensorRT最適化適用（推論速度2倍向上）
3. Auto Scalingの設定
4. エンドポイントのヘルスチェック

**出力**: エンドポイントURL

```text
https://runtime.sagemaker.us-east-1.amazonaws.com/endpoints/yolox-kitti-001/invocations
```

#### Step 6: Monitor Agent実行

**タスク**: 本番環境での継続的監視

**監視項目**:

- **システムメトリクス**: Latency、Throughput、GPU使用率
- **モデルメトリクス**: 予測信頼度分布、検出物体数分布
- **データドリフト**: 入力画像の輝度・コントラスト分布の変化
- **エッジケース検出**: 信頼度が低い検出結果を自動収集

**アラート条件**:

- Latency > 50ms が5分継続 → Slack通知
- データドリフト検出 → 再学習トリガー

### 6.5 VAD強化学習ワークフロー例

#### Step 1: VAD用GitHub Issue作成

```yaml
title: "[MLOps] VAD End-to-End Control with PPO"
labels: mlops, reinforcement_learning, vad, carla
body: |
  model_type: reinforcement_learning
  algorithm: ppo  # Proximal Policy Optimization

  environment:
    simulator: carla
    version: 0.9.15
    town: Town03  # 都市環境
    weather: ClearNoon
    num_vehicles: 50
    num_pedestrians: 100

  agent:
    observation:
      - front_camera_rgb: [224, 224, 3]
      - vehicle_speed: [1]
      - gps_location: [2]
    action:
      - steering: [-1.0, 1.0]  # 連続値
      - throttle: [0.0, 1.0]
      - brake: [0.0, 1.0]

  reward_function:
    - forward_progress: +1.0 per meter
    - collision: -100.0
    - lane_invasion: -10.0
    - traffic_light_violation: -50.0
    - speed_limit_violation: -5.0

  hyperparameters:
    gamma: 0.99
    lambda_gae: 0.95
    learning_rate: 3e-4
    batch_size: 256
    num_epochs: 10
    clip_range: 0.2
    total_timesteps: 10000000  # 1000万ステップ

  evaluation:
    episodes: 100
    success_criteria:
      - collision_rate < 0.05
      - avg_speed > 20 km/h
      - route_completion_rate > 0.90
```

#### Step 2: VAD Training Agent実行（強化学習）

**タスク**: CARLA SimulatorでPPO学習

**処理内容**:

1. SageMaker Training Job + CARLA Dockerコンテナの起動
2. PPOアルゴリズムによる学習
   - Actor Network: カメラ画像 → 行動（ステアリング、スロットル、ブレーキ）
   - Critic Network: 状態価値の推定
3. エピソードごとの報酬・成功率の記録
4. 学習済みポリシーネットワークをS3に保存

**出力**:

```text
s3://mlops-bucket/models/vad-ppo-carla-001/
├── policy_network.pth
├── value_network.pth
├── training_curves.png     # 報酬・成功率のグラフ
└── hyperparameters.json
```

#### Step 3: VAD Evaluation Agent実行

**タスク**: CARLA評価環境での性能測定

**処理内容**:

1. 学習済みポリシーで100エピソード実行
2. 評価指標の計算
   - Collision Rate: 3.2%
   - Route Completion Rate: 92.5%
   - Average Speed: 24.3 km/h
   - Traffic Light Violation Rate: 1.5%
3. 評価動画の生成（成功例・失敗例）

**出力**:

```text
s3://mlops-bucket/evaluations/vad-ppo-carla-001/
├── metrics.json
├── success_episodes/        # 成功エピソードの動画
│   ├── episode_001.mp4
│   └── ...
└── failure_episodes/        # 失敗エピソードの動画
    ├── episode_042.mp4
    └── ...
```

### 6.6 自動運転MLOpsの課題と対策

#### 課題1: 大容量データの管理

**問題**: KITTI、Waymo等のデータセットは数百GB～数TB

**対策**:

- S3 Intelligent-Tieringによるコスト最適化
- データサンプリング: 初期実験では全データの10%で検証
- データバージョニング: DVC、Delta Lakeによる効率的な管理

#### 課題2: GPU リソースコスト

**問題**: 学習・推論に高価なGPUインスタンスが必要

**対策**:

- **学習**: SageMaker Training JobでSpot Instanceを活用（最大70%コスト削減）
- **推論**: TensorRT最適化、量子化（FP16、INT8）で低スペックGPUでも高速化
- **Auto Scaling**: トラフィックに応じてインスタンス数を動的調整

#### 課題3: シミュレータと実環境のギャップ

**問題**: シミュレータで学習したモデルが実車両で性能低下（Sim-to-Real Gap）

**対策**:

- **Domain Randomization**: シミュレータの環境（天候、照明、車両モデル）をランダム化
- **Domain Adaptation**: Simulatorデータと実データでAdversarial Training
- **Transfer Learning**: Simulatorで事前学習 → 実データでFine-tuning

---

## 7. 変更履歴

| バージョン | 日付       | 変更内容                                       | 作成者 |
| ---------- | ---------- | ---------------------------------------------- | ------ |
| 1.0        | 2025-12-30 | 要件仕様書とアーキテクチャ設計書を統合         | -      |
| 1.1        | 2025-12-31 | 自動運転向けユースケースを追加（YOLOX、KITTI、VAD） | -      |

---

## 7. 用語集

- **MLOps**: Machine Learning Operations（機械学習運用）
- **SageMaker**: Amazon SageMaker（AWSの機械学習プラットフォーム）
- **Step Functions**: AWS Step Functions（サーバーレスワークフローサービス）
- **Model Registry**: モデルバージョン管理システム
- **MCP**: Model Context Protocol（モデルコンテキストプロトコル）
- **SMOTE**: Synthetic Minority Over-sampling Technique（クラス不均衡データのリバランス手法）
- **データドリフト**: 本番環境での入力データ分布が学習時と異なる現象
- **コンセプトドリフト**: 入力と出力の関係性が時間とともに変化する現象
- **Spot Instance**: AWSの余剰リソースを利用した低コストインスタンス（最大90%割引）
- **カナリアリリース**: 一部トラフィックで新バージョンを段階的に展開するデプロイ戦略
