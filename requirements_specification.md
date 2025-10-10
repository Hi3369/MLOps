# 要件仕様書: GitHub Issue駆動型MLOpsシステム

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

### 2.1 トリガー機能
**FR-001: GitHub Issue検知**
- GitHubリポジトリに特定のラベル（例: `mlops:train`）が付いたIssueが作成されたら自動的にMLパイプラインを起動
- Issue内に学習パラメータ（モデル種類、学習方法、ハイパーパラメータ等）を記載
- Webhookまたはポーリングによる検知

### 2.2 データ管理機能
**FR-002: 学習データ管理**
- 学習データはAmazon S3に保存
- データバージョン管理（S3バージョニング、またはDVC利用）
- SageMaker Training用のデータ形式への変換・配置

**FR-003: 学習済みモデル管理**
- 学習済みモデルをAmazon S3に保存
- 前バージョンのモデルを保持（最低5世代）
- ロールバック機能の実装

**FR-004: モデルバージョン管理**
- モデルレジストリ（SageMaker Model Registry）での管理
- モデルメタデータ（精度、学習日時、パラメータ等）の記録
- バージョンタグ付け（例: v1.0.0）

### 2.3 学習機能
**FR-005: 学習方式選択**
システムは以下の3種類の学習方式をサポート：
1. **教師あり学習（Supervised Learning）**
   - 分類（Classification）
   - 回帰（Regression）
2. **教師なし学習（Unsupervised Learning）**
   - クラスタリング（Clustering）
   - 次元削減（Dimensionality Reduction）
3. **強化学習（Reinforcement Learning）**
   - Q-Learning
   - Policy Gradient

**FR-006: SageMaker学習ジョブ実行**
- SageMaker Training Jobの起動
- 学習進捗のモニタリング
- 学習ログのCloudWatch Logsへの出力

**FR-007: ハイパーパラメータチューニング**
- SageMaker Automatic Model Tuningの利用（オプション）
- Grid Search / Random Search / Bayesian Optimization

### 2.4 評価機能
**FR-008: モデル評価**
- 学習済みモデルと評価用データセットでの評価実施
- 評価指標の算出：
  - 分類: Accuracy, Precision, Recall, F1-Score, AUC-ROC
  - 回帰: RMSE, MAE, R²
  - クラスタリング: Silhouette Score
- 評価結果のS3保存

**FR-009: 閾値判定**
- 事前定義された適合率（精度）の閾値と比較
- 閾値未満の場合、再学習フローへ移行

### 2.5 対話型調整機能
**FR-010: オペレータ対話**
- 適合率が閾値未満の場合、オペレータに通知（Slack/Email/GitHub Comment）
- オペレータが学習設定（ハイパーパラメータ、データ前処理等）を調整
- 調整内容を元に再学習を実行
- 最大再学習回数の設定（例: 3回まで）

### 2.6 ロールバック機能
**FR-011: モデルロールバック**
- 学習失敗時、前バージョンのモデルを自動的に保持
- 手動/自動でのロールバック実行
- ロールバック履歴の記録

### 2.7 履歴管理機能
**FR-012: 学習履歴のGitHub保存**
- 学習結果（精度、パラメータ、実行時間等）をMarkdown/JSON形式で生成
- GitHubリポジトリの特定ディレクトリ（例: `training_history/`）にコミット
- 元のIssueへのコメントとして結果を投稿

### 2.8 オーケストレーション機能
**FR-013: Step Functions統合**
- AWS Step Functionsによるワークフロー制御
- ステート管理（データ準備→学習→評価→判定→通知/再学習）
- エラーハンドリングとリトライロジック

**FR-014: Agentベースアーキテクチャ**
- 各処理を独立したエージェント（Lambda/Container）として実装
- エージェント間の疎結合な連携
- スケーラビリティの確保

---

## 3. 非機能要件

### 3.1 パフォーマンス
**NFR-001: 応答時間**
- Issue検知から学習開始まで: 5分以内
- 学習完了から評価結果通知まで: 10分以内（小規模データセットの場合）

**NFR-002: スケーラビリティ**
- 同時実行可能な学習ジョブ数: 10ジョブ以上
- データサイズ: 最大1TB

### 3.2 可用性
**NFR-003: システム稼働率**
- 目標稼働率: 99.5%以上
- 学習失敗時の自動リトライ: 最大3回

### 3.3 セキュリティ
**NFR-004: アクセス制御**
- IAMロールベースのアクセス制御
- S3バケットの暗号化（SSE-S3またはSSE-KMS）
- GitHub Tokenの安全な管理（AWS Secrets Manager）

**NFR-005: 監査**
- CloudTrailによる操作ログの記録
- 学習履歴の改ざん防止

### 3.4 保守性
**NFR-006: ログ管理**
- CloudWatch Logsへの統合
- ログ保持期間: 90日間

**NFR-007: モニタリング**
- CloudWatch Metricsでの監視
- 異常検知時のアラート通知

### 3.5 移植性
**NFR-008: クラウド非依存設計**
- 可能な限りオープンスタンダードを使用
- 他クラウドへの移行を考慮した設計

---

## 4. システム制約

### 4.1 技術制約
- **CON-001**: AWS環境での実装
- **CON-002**: SageMaker対応のフレームワーク使用（TensorFlow, PyTorch, scikit-learn等）
- **CON-003**: Python 3.8以上

### 4.2 ビジネス制約
- **CON-004**: 初期開発期間: 3ヶ月
- **CON-005**: 月間AWS利用予算: $XXX（要調整）

---

## 5. ユースケース

### 5.1 基本フロー
1. データサイエンティストがGitHub Issueを作成（ラベル: `mlops:train`）
2. Issue内に学習設定を記載（YAML/JSON形式）
3. システムがIssueを検知し、Step Functionsワークフローを起動
4. データ準備エージェントがS3から学習データを取得
5. SageMakerで学習ジョブを実行
6. 学習完了後、評価エージェントが評価を実施
7. 評価結果が閾値を満たす場合、モデルをレジストリに登録
8. 学習結果をGitHubに保存し、Issueにコメント

### 5.2 代替フロー: 再学習
1. 評価結果が閾値未満
2. オペレータにSlack/Email通知
3. オペレータがGitHub Issueにコメントで設定調整を指示
4. システムが調整内容を反映し再学習を実行
5. 最大3回まで繰り返し

### 5.3 代替フロー: ロールバック
1. 学習が失敗
2. 前バージョンのモデルを保持
3. オペレータに失敗通知
4. 必要に応じて手動でロールバック実行

---

## 6. データ仕様

### 6.1 学習データ
- **形式**: CSV, Parquet, TFRecord
- **保存先**: `s3://<bucket>/datasets/<dataset_id>/train/`
- **バージョン管理**: S3バージョニング有効化

### 6.2 評価データ
- **形式**: CSV, Parquet, TFRecord
- **保存先**: `s3://<bucket>/datasets/<dataset_id>/test/`

### 6.3 モデル
- **形式**: TensorFlow SavedModel, PyTorch .pth, scikit-learn .pkl
- **保存先**: `s3://<bucket>/models/<model_id>/<version>/`
- **メタデータ**: model_metadata.json

### 6.4 学習履歴
- **形式**: Markdown
- **保存先**: GitHubリポジトリ `training_history/<training_id>.md`

---

## 7. インターフェース仕様

### 7.1 GitHub Issue形式
```yaml
title: "[MLOps] モデル学習リクエスト: <モデル名>"
labels: mlops:train
body:
  learning_type: supervised  # supervised, unsupervised, reinforcement
  algorithm: random_forest
  dataset_id: dataset-20250110-001
  hyperparameters:
    n_estimators: 100
    max_depth: 10
  evaluation_threshold: 0.85
  max_retry: 3
```

### 7.2 学習結果形式
```markdown
# 学習結果レポート

## 基本情報
- Training ID: train-20250110-123456
- 学習方式: 教師あり学習
- アルゴリズム: Random Forest
- 実行日時: 2025-01-10 12:34:56 UTC

## データセット
- Dataset ID: dataset-20250110-001
- 学習データサイズ: 10,000件
- 評価データサイズ: 2,000件

## ハイパーパラメータ
- n_estimators: 100
- max_depth: 10

## 評価結果
- Accuracy: 0.87
- Precision: 0.85
- Recall: 0.89
- F1-Score: 0.87

## モデル情報
- Model Version: v1.2.3
- S3 Path: s3://mlops-bucket/models/model-001/v1.2.3/
- Model Registry ARN: arn:aws:sagemaker:...

## ステータス
✅ 学習成功（閾値: 0.85をクリア）
```

---

## 8. 承認基準

### 8.1 機能テスト
- [ ] 全機能要件（FR-001〜FR-014）が実装され、動作確認済み
- [ ] 3種類の学習方式（教師あり、教師なし、強化学習）の動作確認済み

### 8.2 非機能テスト
- [ ] 非機能要件（NFR-001〜NFR-008）が満たされている
- [ ] 負荷テスト実施済み

### 8.3 セキュリティテスト
- [ ] 脆弱性スキャン実施済み
- [ ] IAMポリシー最小権限の原則適用済み

---

## 9. 変更履歴

| バージョン | 日付 | 変更内容 | 作成者 |
|---|---|---|---|
| 0.1 | 2025-10-10 | 初版作成 | - |

---

## 10. 付録

### 10.1 用語集
- **MLOps**: Machine Learning Operations（機械学習運用）
- **SageMaker**: Amazon SageMaker（AWSの機械学習プラットフォーム）
- **Step Functions**: AWS Step Functions（サーバーレスワークフローサービス）
- **Model Registry**: モデルバージョン管理システム

### 10.2 参考資料
- [Amazon SageMaker Documentation](https://docs.aws.amazon.com/sagemaker/)
- [AWS Step Functions Documentation](https://docs.aws.amazon.com/step-functions/)
- [MLOps Best Practices](https://ml-ops.org/)
