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

## 2. MLOpsワークフロー要件

本システムは、以下の7段階のMLOpsライフサイクルを実現します。

### 2.1 📥 フェーズ1: データ収集・前処理

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

### 2.2 🧪 フェーズ2: モデル開発（実験）

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

### 2.3 🧹 フェーズ3: モデル検証・テスト

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

### 2.4 📦 フェーズ4: モデルパッケージング

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

### 2.5 🚀 フェーズ5: デプロイ（リリース）

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

### 2.6 🔍 フェーズ6: モニタリング（運用）

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

### 2.7 🔄 フェーズ7: 継続的改善（再トレーニング）

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

### 2.8 トリガー機能

**FR-029: GitHub Issue検知**
- GitHubリポジトリに特定のラベル（例: `mlops:train`）が付いたIssueが作成されたら自動的にMLパイプラインを起動
- Issue内に学習パラメータ（モデル種類、学習方法、ハイパーパラメータ、デプロイ戦略等）を記載
- Webhookまたはポーリングによる検知

### 2.9 ワークフロー最適化機能

**FR-034: モデル特性自動検出**
- Issue内の学習方式（supervised/unsupervised/reinforcement）とタスク種別（classification/regression/clustering等）を解析
- モデルアルゴリズム（Random Forest, XGBoost, Neural Network, PPO等）の特性を識別
- データセットサイズ、特徴量数、クラス分布等のメタデータを分析
- 過去の学習履歴から類似モデルのパターンを抽出

**FR-035: ワークフローフェーズ最適化**
システムは検出されたモデル特性に基づき、7段階ワークフローの各フェーズで実行する機能を最適化：

1. **フェーズ1（データ収集・前処理）の最適化**
   - **強化学習モデル**: 環境シミュレーションデータの生成、報酬関数の正規化を優先
   - **画像分類モデル**: データ拡張（回転、反転、クロップ）を自動適用
   - **時系列モデル**: 時間窓のスライディング、ラグ特徴量生成を優先
   - **テーブルデータモデル**: 欠損値処理、カテゴリカルエンコーディングを重視
   - **不均衡データ検出時**: SMOTE、アンダーサンプリング等のリバランス処理を提案

2. **フェーズ2（モデル開発）の最適化**
   - **小規模データセット（<10,000件）**: Grid Search優先、学習時間短縮
   - **大規模データセット（>100,000件）**: Bayesian Optimization優先、分散学習推奨
   - **強化学習**: PPO/DQNのハイパーパラメータレンジを専用設定
   - **ディープラーニング**: GPU自動割り当て、Early Stopping設定
   - **軽量モデル（RF, XGBoost）**: CPU最適化、並列実行数増加

3. **フェーズ3（モデル検証）の最適化**
   - **分類モデル**: Precision/Recall/F1/AUC-ROCを優先評価
   - **回帰モデル**: RMSE/MAE/R²を優先評価
   - **強化学習**: Episode Reward、Convergence Speedを評価
   - **不均衡データ**: クラスごとのPrecision/Recallを詳細分析
   - **公平性重視タスク**: バイアスチェック（SageMaker Clarify）を必須化

4. **フェーズ4（パッケージング）の最適化**
   - **リアルタイム推論要求**: REST API + 軽量コンテナ最適化
   - **バッチ推論**: S3バッチ処理パイプラインを推奨
   - **エッジデプロイ**: TensorFlow Lite / ONNX変換を提案
   - **高スループット要求**: gRPC + マルチインスタンス構成

5. **フェーズ5（デプロイ）の最適化**
   - **本番初回デプロイ**: カナリアリリース（10%→50%→100%）を推奨
   - **マイナーバージョンアップ**: A/Bテストで精度比較
   - **緊急修正**: ブルー/グリーンで即座切替
   - **低トラフィック環境**: シンプルデプロイで迅速化

6. **フェーズ6（モニタリング）の最適化**
   - **リアルタイム推論**: レイテンシ（P50/P95/P99）を重点監視
   - **分類モデル**: クラスごとの予測分布変化を監視
   - **回帰モデル**: 予測値の平均・分散の推移を監視
   - **強化学習**: 報酬の移動平均、方策エントロピーを監視
   - **時系列モデル**: 時間窓ごとのドリフトスコアを計算

7. **フェーズ7（継続的改善）の最適化**
   - **データドリフト検知モデル**: 自動再学習頻度を高める（週次→日次）
   - **安定モデル**: 再学習頻度を低減（週次→月次）
   - **強化学習**: 環境変化検知時に即座再学習
   - **季節性データ**: 季節ごとのスケジュール再学習

**FR-036: リソース最適化**
- **GPU要求モデル（Neural Network, DQN）**: 自動的にGPUインスタンス（ml.p3.2xlarge等）を割り当て
- **CPU最適モデル（Random Forest, XGBoost）**: CPUインスタンス（ml.m5.xlarge等）でコスト削減
- **大規模データ処理**: 分散学習（SageMaker Distributed Training）を自動提案
- **小規模データ**: Spot Instanceで学習コスト削減（最大70%削減）
- **推論負荷予測**: Auto Scalingの最小/最大インスタンス数を動的調整

**FR-037: パフォーマンスプロファイル選択**
システムは以下の最適化プロファイルから自動選択（またはユーザー指定）：

- **速度優先モード**:
  - ハイパーパラメータ最適化を簡略化（max_trials: 10）
  - 軽量な前処理、デプロイを迅速化
  - 用途: PoC、プロトタイピング

- **精度優先モード**:
  - ハイパーパラメータ最適化を徹底（max_trials: 50+）
  - データ拡張、アンサンブル学習を適用
  - 用途: 本番モデル、コンペティション

- **コスト優先モード**:
  - Spot Instance優先、CPUインスタンス使用
  - ハイパーパラメータ最適化を制限
  - 用途: 定期バッチ処理、予算制約下

- **バランスモード**:
  - 速度・精度・コストのバランス
  - 用途: 通常の本番運用（デフォルト）

**FR-038: 最適化提案機能**
- ワークフロー実行前に、検出されたモデル特性に基づく最適化提案をGitHub Issueコメントで通知
- 提案内容: 推奨フェーズ構成、リソース設定、評価指標、デプロイ戦略
- ユーザーは提案を承認、または手動で設定を上書き可能
- 過去の類似モデルの成功パターンを参照し、ベストプラクティスを推薦

### 2.10 オーケストレーション機能

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

## 5. ユースケース

### 5.1 基本フロー: 完全MLOpsサイクル

1. **データサイエンティストがGitHub Issueを作成**
   - ラベル: `mlops:train`
   - Issue本文にワークフロー設定を記載（YAML形式）

2. **フェーズ1: データ収集・前処理**
   - システムがIssueを検知し、Step Functionsワークフローを起動
   - Data Preparation AgentがS3から生データを取得
   - データクリーニング、特徴量エンジニアリングを実行
   - 前処理済みデータをS3に保存（バージョン管理）

3. **フェーズ2: モデル開発（実験）**
   - Training AgentがSageMaker Experimentsを初期化
   - ハイパーパラメータ最適化を実行（指定がある場合）
   - SageMakerで学習ジョブを実行
   - 学習済みモデルをS3に保存

4. **フェーズ3: モデル検証・テスト**
   - Evaluation Agentがモデルを評価
   - 精度メトリクスを算出
   - バイアスチェックを実行
   - CI/CDパイプラインで自動テストを実行

5. **フェーズ4: モデルパッケージング**
   - Packaging AgentがモデルをDockerコンテナ化
   - SageMaker Model Registryに登録
   - バージョンタグ付け（v1.0.0）

6. **フェーズ5: デプロイ（リリース）**
   - 評価結果が閾値を満たす場合、デプロイを実行
   - デプロイ戦略に応じた展開（A/B、カナリア、ブルー/グリーン）
   - SageMaker Endpointを作成

7. **フェーズ6: モニタリング（運用）**
   - CloudWatch Dashboardでメトリクス監視開始
   - データドリフト検知を開始
   - アラート設定を有効化

8. **フェーズ7: 継続的改善**
   - 学習結果をGitHubに保存（`training_history/`）
   - 元のIssueにコメントで結果を投稿
   - 自動再学習トリガーを設定

### 5.2 代替フロー: 閾値未達による再学習

1. **評価結果が閾値未満**
   - Judge Agentが閾値比較を実行
   - 閾値未達を検知

2. **オペレータへの通知**
   - Notification AgentがSlack/Email/GitHub Issueに通知
   - 現在の精度と閾値の差分を報告

3. **設定調整**
   - オペレータがGitHub Issueにコメントで設定を調整
   - ハイパーパラメータ、データ前処理設定等を変更

4. **再学習実行**
   - システムが調整内容をパース
   - フェーズ2から自動再実行

5. **最大リトライ判定**
   - 最大3回まで繰り返し
   - 3回で閾値に達しない場合は失敗として記録

### 5.3 代替フロー: デプロイ失敗時のロールバック

1. **デプロイ失敗検知**
   - Deployment Agentがエラーを検知
   - または、モニタリングでエラー率が閾値超過

2. **自動ロールバック実行**
   - Rollback Agentが前バージョンのモデルに切り替え
   - エンドポイント更新

3. **通知と記録**
   - オペレータに失敗とロールバック完了を通知
   - ロールバック履歴をGitHubに記録

4. **原因調査**
   - ログとメトリクスを収集
   - 問題分析レポートを生成

### 5.4 代替フロー: データドリフト検知による自動再学習

1. **ドリフト検知**
   - Model Monitor Agentがデータドリフトを検知
   - アラートを発火

2. **自動再学習トリガー**
   - 設定に応じて自動的に新しいIssueを作成
   - または既存Issueにコメント

3. **新データでの学習**
   - フェーズ1から自動実行
   - 新旧モデルの比較を実施

4. **改善確認**
   - 新モデルが旧モデルより優れている場合のみデプロイ
   - 劣化している場合は通知のみ

### 5.5 代替フロー: ワークフロー最適化による自動調整

1. **Issue作成とモデル特性検出**
   - データサイエンティストがGitHub Issueを作成
   - Workflow Optimizer Agentが以下を自動検出:
     - 学習方式: `supervised`, タスク種別: `classification`
     - アルゴリズム: `random_forest`
     - データセット: 50,000件（中規模）
     - クラス不均衡: 陽性10%, 陰性90%

2. **最適化提案の生成**
   - システムが最適化提案をGitHub Issueコメントで投稿:
     ```markdown
     ## ワークフロー最適化提案

     **検出されたモデル特性:**
     - 学習方式: 教師あり学習（分類）
     - アルゴリズム: Random Forest
     - データサイズ: 50,000件（中規模）
     - クラス不均衡: 検出（陽性10%）

     **推奨される最適化:**
     1. フェーズ1: SMOTE適用でクラスバランス調整
     2. フェーズ2: Grid Search（max_trials: 20）
     3. フェーズ3: Precision/Recall重視評価（不均衡対応）
     4. リソース: CPUインスタンス（ml.m5.xlarge）でコスト削減
     5. デプロイ: カナリアリリース推奨

     **最適化プロファイル:** バランスモード（速度・精度・コスト）

     承認してワークフローを開始するには👍リアクション、
     手動設定するには設定YAMLを編集してください。
     ```

3. **ユーザー承認**
   - データサイエンティストが提案を確認
   - 👍リアクションで承認、または設定を手動調整

4. **最適化されたワークフロー実行**
   - フェーズ1: SMOTEでクラスバランス調整を自動適用
   - フェーズ2: Grid Searchで20パターンを効率的に探索
   - フェーズ3: Precision/Recallを重点評価、クラスごとのメトリクスを詳細出力
   - リソース: ml.m5.xlargeインスタンスを自動選択
   - デプロイ: カナリアリリース（10%→50%→100%）

5. **結果報告と学習**
   - 最適化適用結果をGitHubに記録
   - 過去の類似モデル履歴に追加し、将来の提案精度を向上

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
title: "[MLOps] モデル学習リクエスト: Random Forest 分類モデル v1.2"
labels: mlops:train

# === フェーズ1: データ収集・前処理 ===
dataset_id: dataset-20250128-001
data_preprocessing:
  handle_missing: mean  # drop, mean, median, mode
  normalize: true
  encode_categorical: onehot  # onehot, label, target
  feature_engineering:
    - aggregate_by_user
    - time_features

# === フェーズ2: モデル開発（実験） ===
learning_type: supervised  # supervised, unsupervised, reinforcement
task_type: classification  # classification, regression, clustering, etc.
algorithm: random_forest

hyperparameters:
  n_estimators: 100
  max_depth: 10
  min_samples_split: 2

# ハイパーパラメータ最適化（オプション）
hpo_enabled: false
hpo_config:
  method: bayesian  # grid, random, bayesian
  max_trials: 20

# 実験管理
experiment_name: "customer-churn-v1"
track_with: sagemaker_experiments  # mlflow, sagemaker_experiments

# === フェーズ3: モデル検証・テスト ===
evaluation_threshold: 0.85
evaluation_metrics:
  - accuracy
  - precision
  - recall
  - f1_score
  - auc_roc

bias_check_enabled: true
ci_tests_enabled: true

# === フェーズ4: モデルパッケージング ===
model_version: v1.2.0  # セマンティックバージョニング
api_type: rest  # rest, grpc
container_optimization: true

# === フェーズ5: デプロイ（リリース） ===
deployment_strategy: canary  # ab_test, canary, blue_green
deployment_config:
  canary_traffic_percentage: 10  # カナリアリリースの初期トラフィック割合
  canary_duration_minutes: 30     # カナリア期間
  auto_rollback_on_error: true

deploy_to: staging  # dev, staging, production

# === フェーズ6: モニタリング（運用） ===
monitoring_enabled: true
alert_thresholds:
  error_rate: 0.01       # 1%
  latency_p95_ms: 100    # 100ms
  drift_score: 0.3       # ドリフトスコア閾値

# === フェーズ7: 継続的改善（再トレーニング） ===
auto_retrain_enabled: true
retrain_triggers:
  - data_change        # 新データ追加時
  - schedule_weekly    # 週次スケジュール
  - drift_detected     # ドリフト検知時
  - metric_degradation # 精度劣化時

# === ワークフロー最適化設定 ===
workflow_optimization:
  enabled: true  # true: 自動最適化有効, false: 手動設定のみ
  auto_approve: false  # true: 最適化提案を自動承認, false: ユーザー承認待ち

  # パフォーマンスプロファイル
  performance_profile: balanced  # speed, accuracy, cost, balanced

  # カスタム最適化設定（オプション: 自動検出を上書き）
  custom_optimizations:
    # フェーズ1: データ前処理
    phase1_preprocessing:
      class_imbalance_handling: auto  # auto, smote, undersample, oversample, none
      data_augmentation: auto  # auto, enabled, disabled

    # フェーズ2: モデル開発
    phase2_training:
      resource_type: auto  # auto, gpu, cpu
      instance_type: auto  # auto, ml.m5.xlarge, ml.p3.2xlarge, etc.
      distributed_training: auto  # auto, enabled, disabled
      use_spot_instances: auto  # auto, enabled, disabled

    # フェーズ3: モデル検証
    phase3_evaluation:
      priority_metrics: auto  # auto, [accuracy, precision, recall], etc.
      bias_check_level: auto  # auto, strict, standard, minimal, none

    # フェーズ5: デプロイ
    phase5_deployment:
      strategy_override: auto  # auto, canary, ab_test, blue_green, simple

    # フェーズ6: モニタリング
    phase6_monitoring:
      monitoring_intensity: auto  # auto, high, medium, low
      drift_detection_frequency: auto  # auto, hourly, daily, weekly

    # フェーズ7: 継続的改善
    phase7_improvement:
      retrain_frequency: auto  # auto, daily, weekly, monthly

# === 共通設定 ===
max_retry: 3
notification_channels:
  - slack
  - email
  - github_issue

tags:
  project: customer-churn
  team: data-science
  priority: high
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

## ワークフロー最適化
### 適用された最適化
- **パフォーマンスプロファイル**: バランスモード
- **検出されたモデル特性**: 分類モデル（Random Forest）、中規模データセット（50,000件）、クラス不均衡検出
- **最適化適用結果**:
  - ✅ フェーズ1: SMOTE適用でクラスバランス調整（陽性10%→50%）
  - ✅ フェーズ2: Grid Search（max_trials: 20）で最適パラメータ探索
  - ✅ フェーズ3: Precision/Recall重視評価、クラスごとのメトリクス算出
  - ✅ リソース: CPUインスタンス（ml.m5.xlarge）でコスト削減（予測費用: $12.50）
  - ✅ デプロイ: カナリアリリース（10%→50%→100%）

### 最適化による改善
- **学習時間**: 45分（最適化なし: 60分想定）→ 25%短縮
- **コスト**: $12.50（GPU使用想定: $45.00）→ 72%削減
- **精度向上**: Baseline 0.82 → 最適化後 0.87（+6%）

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
- [ ] 全機能要件（FR-001〜FR-038）が実装され、動作確認済み
- [ ] 3種類の学習方式（教師あり、教師なし、強化学習）の動作確認済み
- [ ] ワークフロー最適化機能（FR-034〜FR-038）の動作確認済み
  - [ ] モデル特性自動検出が正常に動作
  - [ ] 7段階ワークフローの各フェーズ最適化が適用される
  - [ ] 4種類のパフォーマンスプロファイル（速度/精度/コスト/バランス）が選択可能
  - [ ] リソース最適化（GPU/CPU、インスタンスタイプ、Spot Instance）が適用される
  - [ ] 最適化提案機能がGitHub Issueコメントで正常に動作

### 8.2 非機能テスト
- [ ] 非機能要件（NFR-001〜NFR-020）が満たされている
- [ ] 負荷テスト実施済み
- [ ] ワークフロー最適化によるパフォーマンス改善の確認
  - [ ] 速度優先モードで学習時間が短縮されることを確認
  - [ ] コスト優先モードでAWS利用料が削減されることを確認
  - [ ] 精度優先モードで評価指標が向上することを確認

### 8.3 セキュリティテスト
- [ ] 脆弱性スキャン実施済み
- [ ] IAMポリシー最小権限の原則適用済み

### 8.4 ワークフロー最適化テスト
- [ ] 各モデルタイプでの最適化動作確認
  - [ ] 分類モデル（Random Forest, XGBoost）での最適化
  - [ ] 回帰モデルでの最適化
  - [ ] 強化学習モデル（PPO, DQN）での最適化
  - [ ] 画像分類モデルでの最適化（データ拡張確認）
  - [ ] 時系列モデルでの最適化（ラグ特徴量生成確認）
- [ ] データセットサイズ別の最適化
  - [ ] 小規模データセット（<10,000件）: Grid Search優先確認
  - [ ] 大規模データセット（>100,000件）: Bayesian Optimization、分散学習確認
- [ ] クラス不均衡検出と対応
  - [ ] SMOTE、アンダーサンプリング等のリバランス処理が適用されることを確認
- [ ] 過去の学習履歴からのパターン抽出とベストプラクティス推薦が機能することを確認

---

## 9. 変更履歴

| バージョン | 日付 | 変更内容 | 作成者 |
|---|---|---|---|
| 0.1 | 2025-01-29 | 初版作成（7段階MLOpsライフサイクル、ワークフロー最適化機能含む） | - |

---

## 10. 付録

### 10.1 用語集
- **MLOps**: Machine Learning Operations（機械学習運用）
- **SageMaker**: Amazon SageMaker（AWSの機械学習プラットフォーム）
- **Step Functions**: AWS Step Functions（サーバーレスワークフローサービス）
- **Model Registry**: モデルバージョン管理システム
- **ワークフロー最適化**: モデル特性に基づいてMLOpsパイプラインの各フェーズを自動調整する機能
- **パフォーマンスプロファイル**: 速度・精度・コストのバランスを制御する最適化設定（速度優先/精度優先/コスト優先/バランス）
- **SMOTE**: Synthetic Minority Over-sampling Technique（クラス不均衡データのリバランス手法）
- **データドリフト**: 本番環境での入力データ分布が学習時と異なる現象
- **コンセプトドリフト**: 入力と出力の関係性が時間とともに変化する現象
- **Spot Instance**: AWSの余剰リソースを利用した低コストインスタンス（最大90%割引）
- **カナリアリリース**: 一部トラフィックで新バージョンを段階的に展開するデプロイ戦略

### 10.2 参考資料
- [Amazon SageMaker Documentation](https://docs.aws.amazon.com/sagemaker/)
- [AWS Step Functions Documentation](https://docs.aws.amazon.com/step-functions/)
- [MLOps Best Practices](https://ml-ops.org/)
