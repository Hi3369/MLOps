# 実装計画書（TDDアプローチ）

**作成日**: 2026-01-29
**担当**: Quality Engineer / MLOps Engineer / Data Engineer

---

## 進捗サマリー

| Phase | タスク | ステータス | 担当専門家 |
|-------|--------|----------|-----------|
| 1 | SHAP/LIME実装 | ✅ 完了 | ML Engineer |
| 2.1 | E2Eパイプラインテスト | ✅ 完了 | Quality Engineer |
| 2.2 | Capability依存テスト | ✅ 完了 | Quality Engineer |
| 2.3 | AWS統合テスト（LocalStack） | ✅ 完了 | MLOps Engineer |
| 3 | エクスペリメント追跡 | ✅ 完了 | ML Engineer |
| 4 | データバージョニング | ✅ 完了 | Data Engineer |
| 5 | ドキュメント拡充 | ✅ 完了 | Quality Engineer / Data Scientist / MLOps Engineer |

---

## Phase 2: 統合テスト強化（現在のフォーカス）

### 2.1 E2Eパイプラインテスト ✅ 完了

**ファイル**: `tests/integration/test_end_to_end_pipeline.py`
**担当**: Quality Engineer
**優先度**: 高
**結果**: 35 passed, 2 skipped

#### TDDステップ

| # | ステップ | 内容 | ステータス |
|---|---------|------|----------|
| 1 | Red | テストケース設計・実装（失敗するテスト） | ✅ 完了 |
| 2 | Green | テストがパスする最小実装 | ✅ 完了 |
| 3 | Refactor | コード整理・最適化 | ✅ 完了 |
| 4 | Review | コードレビュー | ✅ 完了 |
| 5 | Lint | flake8/black/isort | ✅ 完了 |

#### 実装済みテストケース

| # | テストクラス | テスト数 | 内容 |
|---|-------------|---------|------|
| 1 | TestClassificationPipeline | 3 | 分類モデル（RF, LR, NN） |
| 2 | TestRegressionPipeline | 3 | 回帰モデル（RF, LR, Ridge） |
| 3 | TestClusteringPipeline | 2 | クラスタリング（KMeans, DBSCAN） |
| 4 | TestDeploymentPipeline | 6 | デプロイメント・ヘルスチェック・監視 |
| 5 | TestMonitoringPipeline | 7 | メトリクス収集・ドリフト検出・アラーム |
| 6 | TestErrorHandling | 4 | エラーハンドリング |
| 7 | TestABTestingPipeline | 1 | A/Bテスト |
| 8 | TestRetrainPipeline | 1 | 再学習（スキップ） |
| 9 | TestNotificationPipeline | 3 | Slack/Email/GitHub通知 |
| 10 | TestWorkflowOptimization | 3 | ワークフロー最適化 |
| 11 | TestGitHubIntegration | 4 | GitHub統合 |

#### 発見された問題（要対応）

1. `model_packaging.tools/__init__.py`: ツールがエクスポートされていない
2. `retrain_management`: MLOpsServerに未登録

---

### 2.2 Capability依存テスト ✅ 完了

**ファイル**: `tests/integration/test_capability_dependencies.py`
**担当**: Quality Engineer
**優先度**: 高
**結果**: 32 passed

#### TDDステップ（Phase 2.2）

| # | ステップ | 内容 | ステータス |
|---|---------|------|----------|
| 1 | Red | テストケース設計・実装 | ✅ 完了 |
| 2 | Green | テストがパスする最小実装 | ✅ 完了 |
| 3 | Refactor | コード整理・最適化 | ✅ 完了 |
| 4 | Review | コードレビュー | ✅ 完了 |
| 5 | Lint | flake8/black/isort | ✅ 完了 |

#### 実装済みテストケース（Phase 2.2）

| # | テストクラス | テスト数 | 内容 |
|---|-------------|---------|------|
| 1 | TestDataPrepToTrainingFlow | 3 | データ準備→学習 |
| 2 | TestTrainingToEvaluationFlow | 3 | 学習→評価→SHAP |
| 3 | TestEvaluationToPackagingFlow | 2 | 評価→レジストリ・デプロイ判定 |
| 4 | TestDeploymentToMonitoringFlow | 2 | デプロイ→ヘルスチェック・監視 |
| 5 | TestMonitoringToRetrainFlow | 2 | 監視→ドリフト検出→アラート |
| 6 | TestGitHubIntegrationToWorkflow | 2 | GitHub→ワークフロー |
| 7 | TestNotificationChain | 2 | 通知チェーン（Slack/Email/GitHub） |
| 8 | TestModelRegistryIntegration | 2 | レジストリ登録・一覧・ステータス更新 |
| 9 | TestWorkflowOptimizationFlow | 2 | 最適化分析・履歴取得→適用 |
| 10 | TestHistoryRecordingFlow | 4 | 履歴フォーマット・保存・バージョン追跡 |
| 11 | TestTrainingToHistoryFlow | 2 | 学習→評価→履歴記録 |
| 12 | TestDriftToRetrainToNotifyFlow | 2 | ドリフト→通知→履歴 |
| 13 | TestRegistryToHistoryFlow | 2 | レジストリ→バージョン追跡・GitHub通知 |
| 14 | TestGitHubToHistoryFlow | 2 | GitHub→ワークフロー→履歴 |

#### 発見された問題（要対応）（Phase 2.2）

1. `history_management`: MLOpsServerに未登録（直接インポートで対応）
2. `retrain_management`: MLOpsServerに未登録（Phase 2.1でも発見済み）

---

### 2.3 AWS統合テスト（LocalStack） ✅ 完了

**ファイル**: `tests/integration/test_aws_integration.py`
**担当**: MLOps Engineer
**優先度**: 高
**結果**: 34 passed

#### TDDステップ（Phase 2.3）

| # | ステップ | 内容 | ステータス |
|---|---------|------|----------|
| 1 | Red | テストケース設計・実装 | ✅ 完了 |
| 2 | Green | テストがパスする最小実装 | ✅ 完了 |
| 3 | Refactor | コード整理・最適化 | ✅ 完了 |
| 4 | Review | コードレビュー | ✅ 完了 |
| 5 | Lint | flake8/black/isort | ✅ 完了 |

#### 実装済みテストケース（Phase 2.3）

| # | テストクラス | テスト数 | 内容 |
|---|-------------|---------|------|
| 1 | TestS3DataOperations | 5 | S3アップロード・ダウンロード・バリデーション・エラー |
| 2 | TestSageMakerEndpoints | 6 | エンドポイント作成・監視・ロールバック・オートスケーリング |
| 3 | TestCloudWatchMetrics | 4 | アラーム・メトリクス・データドリフト・コンセプトドリフト |
| 4 | TestStepFunctionsWorkflow | 4 | 学習・推論・評価ワークフロー・パラメータ検証 |
| 5 | TestSESNotifications | 4 | Email・Slack・GitHub・マルチチャネル通知 |
| 6 | TestSSMParameterStore | 2 | GitHubトークン取得・Issue設定パース |
| 7 | TestModelRegistryAWS | 4 | 登録・一覧・取得・ステータス更新 |
| 8 | TestEndpointCreation | 2 | 完全ライフサイクル・A/Bテスト |
| 9 | TestWorkflowOptimizationAWS | 3 | 分析・最適化提案・履歴追跡 |

#### 発見された問題・対応（Phase 2.3）

1. `deploy_to_sagemaker`: `describe_endpoint`がエンドポイント存在確認と待機で2回呼ばれるため、list-based `side_effect`で対応
2. `rollback_deployment`: `previous_config_name`未指定時に`list_endpoint_configs`を呼ぶため、テストでは明示的に指定
3. `update_endpoint_traffic`: パラメータ名は`variant_weights`（`traffic_config`ではない）
4. `collect_system_metrics`: パラメータ名は`time_range_minutes`（`metric_names`ではない）
5. `start_workflow`: `deployment`タイプは未サポート（`inference`を使用）

---

## Phase 3: エクスペリメント追跡 ✅ 完了

**Capability**: `mcp_server/capabilities/experiment_tracking/`
**テストファイル**: `tests/unit/test_experiment_tracking.py`
**担当**: ML Engineer
**優先度**: 中
**結果**: 58 passed

### TDDステップ（Phase 3）

| # | ステップ | 内容 | ステータス |
|---|---------|------|----------|
| 1 | Red | テストケース設計・実装 | ✅ 完了 |
| 2 | Green | Capability実装・サーバー登録 | ✅ 完了 |
| 3 | Refactor | コード整理・最適化 | ✅ 完了 |
| 4 | Review | コードレビュー | ✅ 完了 |
| 5 | Lint | flake8/black/isort | ✅ 完了 |

### 実装済みツール（Phase 3）

| # | ツール名 | 説明 |
|---|---------|------|
| 1 | start_experiment | 実験開始・管理 |
| 2 | log_parameters | パラメータ記録 |
| 3 | log_metrics | メトリクス記録 |
| 4 | compare_experiments | 実験比較 |

### 実装済みテストケース（Phase 3）

| # | テストクラス | テスト数 | 内容 |
|---|-------------|---------|------|
| 1 | TestExperimentTrackingCapability | 4 | 初期化・ツール取得・スキーマ・サーバー登録 |
| 2 | TestStartExperiment | 13 | 正常系・バリデーション・フォーマット |
| 3 | TestLogParameters | 11 | 正常系・型検証・バリデーション |
| 4 | TestLogMetrics | 12 | 正常系・サマリー・バリデーション |
| 5 | TestCompareExperiments | 15 | 比較・ソート・サマリー・バリデーション |
| 6 | TestExperimentTrackingIntegration | 3 | 完全ワークフロー・HP探索・比較 |

### 作成ファイル（Phase 3）

| ファイル | 説明 |
|---------|------|
| `mcp_server/capabilities/experiment_tracking/__init__.py` | Capability エクスポート |
| `mcp_server/capabilities/experiment_tracking/capability.py` | Capability クラス |
| `mcp_server/capabilities/experiment_tracking/tools/__init__.py` | ツール エクスポート |
| `mcp_server/capabilities/experiment_tracking/tools/start_experiment.py` | 実験開始 |
| `mcp_server/capabilities/experiment_tracking/tools/log_parameters.py` | パラメータ記録 |
| `mcp_server/capabilities/experiment_tracking/tools/log_metrics.py` | メトリクス記録 |
| `mcp_server/capabilities/experiment_tracking/tools/compare_experiments.py` | 実験比較 |
| `tests/unit/test_experiment_tracking.py` | ユニットテスト |
| `mcp_server/server.py` | サーバー登録追加 |

---

## Phase 4: データバージョニング ✅ 完了

**Capability**: `mcp_server/capabilities/data_versioning/`
**テストファイル**: `tests/unit/test_data_versioning.py`
**担当**: Data Engineer
**優先度**: 中
**結果**: 54 passed

### TDDステップ（Phase 4）

| # | ステップ | 内容 | ステータス |
|---|---------|------|----------|
| 1 | Red | テストケース設計・実装 | ✅ 完了 |
| 2 | Green | Capability実装・サーバー登録 | ✅ 完了 |
| 3 | Refactor | コード整理・最適化 | ✅ 完了 |
| 4 | Review | コードレビュー | ✅ 完了 |
| 5 | Lint | flake8/black/isort | ✅ 完了 |

### 実装済みツール（Phase 4）

| # | ツール名 | 説明 |
|---|---------|------|
| 1 | version_dataset | データセットバージョン登録・フィンガープリント生成 |
| 2 | get_dataset_lineage | データセットリネージ追跡・親子関係 |
| 3 | compare_datasets | データセット比較（スキーマ・統計・サンプル） |

### 実装済みテストケース（Phase 4）

| # | テストクラス | テスト数 | 内容 |
|---|-------------|---------|------|
| 1 | TestDataVersioningCapability | 4 | 初期化・ツール取得・スキーマ・サーバー登録 |
| 2 | TestVersionDataset | 19 | 正常系・フォーマット・フィンガープリント・バリデーション |
| 3 | TestGetDatasetLineage | 12 | リネージ追跡・チェーン構造・変換履歴・バリデーション |
| 4 | TestCompareDatasets | 16 | スキーマ差分・統計差分・サンプル・バリデーション |
| 5 | TestDataVersioningIntegration | 3 | 完全ワークフロー・マルチバージョン・品質比較 |

### 作成ファイル（Phase 4）

| ファイル | 説明 |
|---------|------|
| `mcp_server/capabilities/data_versioning/__init__.py` | Capability エクスポート |
| `mcp_server/capabilities/data_versioning/capability.py` | Capability クラス |
| `mcp_server/capabilities/data_versioning/tools/__init__.py` | ツール エクスポート |
| `mcp_server/capabilities/data_versioning/tools/version_dataset.py` | バージョン登録 |
| `mcp_server/capabilities/data_versioning/tools/get_dataset_lineage.py` | リネージ追跡 |
| `mcp_server/capabilities/data_versioning/tools/compare_datasets.py` | データセット比較 |
| `tests/unit/test_data_versioning.py` | ユニットテスト |
| `mcp_server/server.py` | サーバー登録追加 |

---

## Phase 5: ドキュメント拡充 ✅ 完了

**担当**: Quality Engineer / Data Scientist / MLOps Engineer
**優先度**: 中

### 作成物

#### API仕様書（docs/api/）- Quality Engineer担当

| # | ファイル | 内容 |
|---|---------|------|
| 1 | `README.md` | API概要・共通レスポンス形式・AWS依存一覧 |
| 2 | `github_integration.md` | 4ツール: detect_issues, parse_issue, create_workflow, start_workflow |
| 3 | `data_preparation.md` | 3ツール: load_dataset, validate_data, preprocess_supervised |
| 4 | `ml_training.md` | 3ツール: train_classification, train_regression, train_clustering |
| 5 | `ml_evaluation.md` | 5ツール: evaluate_*, calculate_shap/lime |
| 6 | `model_packaging.md` | 5ツール: extract_metadata, create_dockerfile/package, generate_config, validate |
| 7 | `model_deployment.md` | 9ツール: deploy, traffic, capacity, autoscaling等 |
| 8 | `model_monitoring.md` | 10ツール: metrics, drift, alarms, dashboards |
| 9 | `model_registry.md` | 5ツール: register, list, get, update_status, delete |
| 10 | `workflow_optimization.md` | 5ツール: analyze, generate, retrieve_history, apply, track |
| 11 | `notification.md` | 5ツール: slack, email, github, template, list_templates |
| 12 | `retrain_management.md` | 5ツール: check_triggers, evaluate_conditions等 |
| 13 | `history_management.md` | 4ツール: format, save, post_comment, track_version |
| 14 | `experiment_tracking.md` | 4ツール: start_experiment, log_parameters/metrics, compare |
| 15 | `data_versioning.md` | 3ツール: version_dataset, get_lineage, compare_datasets |

#### チュートリアル（docs/tutorials/）- Data Scientist担当

| # | ファイル | 内容 |
|---|---------|------|
| 1 | `README.md` | チュートリアル一覧・前提条件・セットアップ |
| 2 | `quickstart.md` | サーバー起動・ツール呼び出し・環境説明 |
| 3 | `training-pipeline.md` | 7ステップ: load→validate→preprocess→train→evaluate→track→register |
| 4 | `monitoring-operations.md` | 7ステップ: deploy→health→monitor→drift→notify→retrain→rollback |

#### トラブルシューティング - MLOps Engineer担当

| # | ファイル | 内容 |
|---|---------|------|
| 1 | `troubleshooting.md` | 10セクション: 起動・AWS・データ・学習・デプロイ・監視・実験追跡・バージョニング・テスト・FAQ |

---

## 実装ルール

### TDDプロセス

```text
1. RED: 失敗するテストを書く
2. GREEN: テストがパスする最小限のコードを書く
3. REFACTOR: コードを整理する
```

### 品質基準

- 各テストファイル: 30件以上のテストケース
- カバレッジ: 80%以上
- Lint: flake8エラー0件
- フォーマット: black/isort適用済み

### コミット規約

```text
test: [Phase X.Y] テスト説明

- テストケース詳細
- 対象Capability

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

---

## 変更履歴

| 日時 | 変更内容 |
|------|---------|
| 2026-01-29 | 初版作成 |
| 2026-01-29 | Phase 2.1 E2Eパイプラインテスト完了（35 passed, 2 skipped） |
| 2026-01-30 | Phase 2.2 Capability依存テスト完了（32 passed） |
| 2026-01-31 | Phase 2.3 AWS統合テスト完了（34 passed） |
| 2026-01-31 | Phase 3 エクスペリメント追跡Capability実装完了（58 passed） |
| 2026-01-31 | Phase 4 データバージョニングCapability実装完了（54 passed） |
| 2026-02-01 | Phase 5 ドキュメント拡充完了（API仕様書15件、チュートリアル4件、トラブルシューティング1件） |
