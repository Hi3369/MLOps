# テスト設計書: GitHub Issue駆動型MLOpsシステム

## 1. テスト戦略

### 1.1 テストレベル

| テストレベル | 目的 | 実施者 | 自動化 |
|---|---|---|---|
| 単体テスト | 各エージェント/関数の動作確認 | 開発者 | ✓ |
| 統合テスト | エージェント間連携の確認 | 開発者 | ✓ |
| システムテスト | エンドツーエンドの動作確認 | QA | ✓ |
| 性能テスト | パフォーマンス・スケーラビリティ確認 | QA | ✓ |
| セキュリティテスト | 脆弱性・アクセス制御の確認 | セキュリティ | △ |
| 受入テスト | ビジネス要件の充足確認 | ユーザー | - |

### 1.2 テスト方針

- **テスト駆動開発（TDD）**: 可能な限り、実装前にテストを作成
- **継続的テスト**: CI/CDパイプラインでの自動実行
- **テストカバレッジ**: コードカバレッジ80%以上を目標
- **モックとスタブ**: 外部サービス（GitHub, AWS）はモック化

---

## 2. 単体テスト設計

### 2.1 Issue Detector Agent

**テスト対象**: [architecture_design.md:2.1](architecture_design.md#21-issue-detector-agent)

#### TC-UT-001: GitHub Webhook正常受信
- **目的**: Webhookペイロードの正常パース
- **入力**: GitHub Issue作成イベントのWebhookペイロード
- **期待結果**: `training_config`オブジェクトが正しく生成される

**テストケース**:
```python
def test_parse_github_webhook_success():
    # Arrange
    webhook_payload = {
        "action": "opened",
        "issue": {
            "number": 123,
            "labels": [{"name": "mlops:train"}],
            "body": """
learning_type: supervised
algorithm: random_forest
dataset_id: dataset-001
hyperparameters:
  n_estimators: 100
evaluation_threshold: 0.85
"""
        }
    }

    # Act
    result = parse_webhook(webhook_payload)

    # Assert
    assert result["issue_number"] == 123
    assert result["learning_type"] == "supervised"
    assert result["algorithm"] == "random_forest"
    assert result["hyperparameters"]["n_estimators"] == 100
```

#### TC-UT-002: 不正なラベルの処理
- **目的**: `mlops:train`以外のラベルを無視
- **入力**: `mlops:train`ラベルがないIssue
- **期待結果**: `None`を返すか、例外をスロー

#### TC-UT-003: YAML/JSONパースエラー
- **目的**: 不正なフォーマットのエラーハンドリング
- **入力**: 不正なYAML/JSON形式のIssue本文
- **期待結果**: 適切なエラーメッセージを返す

---

### 2.2 Data Preparation Agent

**テスト対象**: [architecture_design.md:2.2](architecture_design.md#22-data-preparation-agent)

#### TC-UT-004: データ取得と前処理
- **目的**: S3からデータを取得し、正しく前処理
- **入力**: `dataset_id`、学習方式
- **期待結果**: 前処理済みデータがS3に保存される

**テストケース**:
```python
def test_data_preparation_supervised():
    # Arrange
    mock_s3 = MockS3Client()
    mock_s3.put_object("s3://bucket/datasets/dataset-001/raw/train.csv", "...")

    agent = DataPreparationAgent(s3_client=mock_s3)
    config = {
        "dataset_id": "dataset-001",
        "learning_type": "supervised"
    }

    # Act
    result = agent.prepare_data(config)

    # Assert
    assert result["training_data_s3"].startswith("s3://bucket/processed/")
    assert result["metadata"]["num_samples"] > 0
    assert mock_s3.object_exists(result["training_data_s3"])
```

#### TC-UT-005: データバリデーション（欠損値検出）
- **目的**: 欠損値が多すぎる場合のエラー検出
- **入力**: 50%以上が欠損値のデータ
- **期待結果**: バリデーションエラーを返す

#### TC-UT-006: 大規模データ処理
- **目的**: 1GB以上のデータの処理
- **入力**: 大規模CSVファイル
- **期待結果**: タイムアウトせずに完了（5分以内）

---

### 2.3 Training Agent

**テスト対象**: [architecture_design.md:2.3](architecture_design.md#23-training-agent)

#### TC-UT-007: SageMaker Training Job起動（教師あり）
- **目的**: 教師あり学習のTraining Job正常起動
- **入力**: 教師あり学習の設定
- **期待結果**: SageMaker APIが正しいパラメータで呼ばれる

**テストケース**:
```python
def test_start_training_job_supervised():
    # Arrange
    mock_sagemaker = MockSageMakerClient()
    agent = TrainingAgent(sagemaker_client=mock_sagemaker)
    config = {
        "learning_type": "supervised",
        "algorithm": "xgboost",
        "training_data_s3": "s3://bucket/processed/train/",
        "hyperparameters": {"num_round": "100"}
    }

    # Act
    result = agent.start_training(config)

    # Assert
    assert mock_sagemaker.create_training_job_called
    assert result["training_job_name"].startswith("train-")
    assert mock_sagemaker.get_training_job_params()["HyperParameters"]["num_round"] == "100"
```

#### TC-UT-008: SageMaker Training Job起動（教師なし）
- **目的**: 教師なし学習（K-Means）のTraining Job正常起動
- **入力**: 教師なし学習の設定
- **期待結果**: K-Meansアルゴリズムで起動

#### TC-UT-009: SageMaker Training Job起動（強化学習）
- **目的**: 強化学習のTraining Job正常起動
- **入力**: 強化学習の設定（Ray RLlib）
- **期待結果**: RLコンテナで起動

#### TC-UT-010: Training Job失敗時のエラーハンドリング
- **目的**: SageMaker APIエラーの適切な処理
- **入力**: 不正なパラメータ
- **期待結果**: エラーメッセージを返し、Step Functionsに伝播

---

### 2.4 Evaluation Agent

**テスト対象**: [architecture_design.md:2.4](architecture_design.md#24-evaluation-agent)

#### TC-UT-011: 分類モデルの評価
- **目的**: 分類モデルの評価指標算出
- **入力**: 学習済み分類モデル、テストデータ
- **期待結果**: Accuracy, Precision, Recall, F1が正しく算出

**テストケース**:
```python
def test_evaluate_classification_model():
    # Arrange
    mock_s3 = MockS3Client()
    mock_s3.put_model("s3://bucket/models/model.pkl", trained_model)
    mock_s3.put_data("s3://bucket/test/data.csv", test_data)

    agent = EvaluationAgent(s3_client=mock_s3)
    config = {
        "model_s3": "s3://bucket/models/model.pkl",
        "test_data_s3": "s3://bucket/test/data.csv",
        "task_type": "classification"
    }

    # Act
    result = agent.evaluate(config)

    # Assert
    assert "accuracy" in result["evaluation_results"]
    assert "precision" in result["evaluation_results"]
    assert 0 <= result["evaluation_results"]["accuracy"] <= 1
```

#### TC-UT-012: 回帰モデルの評価
- **目的**: 回帰モデルの評価指標算出
- **入力**: 学習済み回帰モデル、テストデータ
- **期待結果**: RMSE, MAE, R²が正しく算出

#### TC-UT-013: クラスタリングモデルの評価
- **目的**: クラスタリングモデルの評価指標算出
- **入力**: K-Meansモデル、テストデータ
- **期待結果**: Silhouette Scoreが正しく算出

#### TC-UT-014: 強化学習モデルの評価
- **目的**: 強化学習モデルの評価
- **入力**: RLモデル、評価エピソード数
- **期待結果**: Average Rewardが算出

---

### 2.5 Judge Agent

**テスト対象**: [architecture_design.md:2.5](architecture_design.md#25-judge-agent)

#### TC-UT-015: 閾値以上の評価結果判定
- **目的**: 閾値を超えた場合、`pass`判定
- **入力**: accuracy=0.87, threshold=0.85
- **期待結果**: `decision="pass"`、`next_action="register_model"`

**テストケース**:
```python
def test_judge_pass():
    # Arrange
    agent = JudgeAgent()
    evaluation = {"accuracy": 0.87}
    threshold = 0.85

    # Act
    result = agent.judge(evaluation, threshold, current_retry=0, max_retry=3)

    # Assert
    assert result["decision"] == "pass"
    assert result["next_action"] == "register_model"
```

#### TC-UT-016: 閾値未満の評価結果判定
- **目的**: 閾値未満の場合、`retrain`判定
- **入力**: accuracy=0.80, threshold=0.85
- **期待結果**: `decision="retrain"`、`next_action="notify_operator"`

#### TC-UT-017: 最大リトライ超過判定
- **目的**: リトライ回数が上限に達した場合、`fail`判定
- **入力**: accuracy=0.80, current_retry=3, max_retry=3
- **期待結果**: `decision="fail"`、`next_action="rollback"`

---

### 2.6 Notification Agent

**テスト対象**: [architecture_design.md:2.6](architecture_design.md#26-notification-agent)

#### TC-UT-018: GitHub Issueコメント投稿
- **目的**: GitHub APIでコメント投稿
- **入力**: issue_number, メッセージ
- **期待結果**: コメントが正常に投稿される

**テストケース**:
```python
def test_post_github_comment():
    # Arrange
    mock_github = MockGitHubClient()
    agent = NotificationAgent(github_client=mock_github)
    config = {
        "issue_number": 123,
        "message": "学習が完了しました"
    }

    # Act
    result = agent.notify(config)

    # Assert
    assert mock_github.comment_posted(123)
    assert result["notification_status"] == "success"
```

#### TC-UT-019: Slack通知
- **目的**: Slack Webhookで通知
- **入力**: メッセージ、Webhook URL
- **期待結果**: Slackに通知が届く

#### TC-UT-020: Email通知
- **目的**: SESでメール送信
- **入力**: メッセージ、宛先
- **期待結果**: メールが送信される

---

### 2.7 Rollback Agent

**テスト対象**: [architecture_design.md:2.7](architecture_design.md#27-rollback-agent)

#### TC-UT-021: モデルロールバック
- **目的**: 前バージョンへのロールバック
- **入力**: model_package_group_name, rollback_to_version
- **期待結果**: 前バージョンが`Approved`に変更される

---

### 2.8 History Writer Agent

**テスト対象**: [architecture_design.md:2.8](architecture_design.md#28-history-writer-agent)

#### TC-UT-022: 学習履歴のGitHubコミット
- **目的**: 学習結果をMarkdown形式でコミット
- **入力**: 学習結果データ
- **期待結果**: GitHubにコミットされる

**テストケース**:
```python
def test_write_training_history():
    # Arrange
    mock_github = MockGitHubClient()
    agent = HistoryWriterAgent(github_client=mock_github)
    training_result = {
        "training_job_name": "train-001",
        "evaluation_results": {"accuracy": 0.87},
        "model_version": "v1.0.0"
    }

    # Act
    result = agent.write_history(training_result)

    # Assert
    assert mock_github.commit_created()
    assert result["file_path"].endswith(".md")
    assert result["commit_sha"] is not None
```

---

## 3. 統合テスト設計

### 3.1 エージェント間連携テスト

#### TC-IT-001: Data Preparation → Training連携
- **目的**: データ準備後、学習が正常に開始
- **テストフロー**:
  1. Data Preparation Agentを実行
  2. 出力されたS3パスをTraining Agentに渡す
  3. Training Jobが正常に起動
- **期待結果**: Training Jobが正常に完了

#### TC-IT-002: Training → Evaluation連携
- **目的**: 学習後、評価が正常に実行
- **テストフロー**:
  1. Training Agentで学習完了
  2. モデルS3パスをEvaluation Agentに渡す
  3. 評価実行
- **期待結果**: 評価結果が正しく算出

#### TC-IT-003: Evaluation → Judge → Notification連携
- **目的**: 評価後、判定と通知が正常に実行
- **テストフロー**:
  1. Evaluation Agentで評価完了
  2. Judge Agentで判定
  3. Notification Agentで通知
- **期待結果**: GitHub Issueにコメントが投稿

---

### 3.2 Step Functions統合テスト

#### TC-IT-004: 正常フロー（教師あり学習）
- **目的**: エンドツーエンドの正常動作確認
- **テストフロー**:
  1. GitHub Issueを作成（教師あり学習）
  2. Step Functionsが起動
  3. 全ステートが正常に実行
  4. モデルがModel Registryに登録
  5. 学習履歴がGitHubにコミット
- **期待結果**: ワークフローが`Success`で完了

**テストデータ**:
```yaml
learning_type: supervised
algorithm: xgboost
dataset_id: test-dataset-001
hyperparameters:
  num_round: 10
  max_depth: 3
evaluation_threshold: 0.75
max_retry: 3
```

#### TC-IT-005: 正常フロー（教師なし学習）
- **目的**: K-Meansの正常動作確認
- **テストフロー**: TC-IT-004と同様
- **期待結果**: クラスタリングモデルが正常に学習・評価

#### TC-IT-006: 正常フロー（強化学習）
- **目的**: RLの正常動作確認
- **テストフロー**: TC-IT-004と同様
- **期待結果**: RLモデルが正常に学習・評価

#### TC-IT-007: 再学習フロー
- **目的**: 閾値未満の場合の再学習
- **テストフロー**:
  1. GitHub Issueを作成（低い閾値設定）
  2. 初回学習が閾値未満
  3. オペレータに通知
  4. オペレータがIssueにコメントで設定調整
  5. 再学習実行
  6. 再学習が閾値以上
- **期待結果**: 2回目の学習でモデル登録

#### TC-IT-008: 最大リトライ超過フロー
- **目的**: 最大リトライ後のロールバック
- **テストフロー**:
  1. GitHub Issueを作成（達成不可能な閾値）
  2. 3回再学習を試行
  3. すべて閾値未満
  4. ロールバック実行
- **期待結果**: 前バージョンのモデルが保持される

#### TC-IT-009: エラーハンドリング（データ準備失敗）
- **目的**: データ準備エラー時の処理
- **テストフロー**:
  1. 存在しないdataset_idを指定
  2. Data Preparation Agentが失敗
  3. Step Functionsがエラーハンドリング
- **期待結果**: 適切なエラー通知

---

## 4. システムテスト設計

### 4.1 エンドツーエンドテスト

#### TC-ST-001: 完全なMLOpsサイクル（本番相当データ）
- **目的**: 本番環境に近い条件での動作確認
- **テストデータ**: 10,000件の分類データ
- **テストフロー**:
  1. GitHub Issueを作成
  2. 学習実行（10分以内）
  3. 評価実行
  4. モデル登録
  5. 履歴保存
- **期待結果**: 全プロセスが30分以内に完了

#### TC-ST-002: 複数学習方式の同時実行
- **目的**: 3種類の学習方式を並列実行
- **テストフロー**:
  1. 教師あり、教師なし、強化学習のIssueを同時作成
  2. 3つのワークフローが並列実行
- **期待結果**: すべて正常に完了

---

### 4.2 シナリオテスト

#### TC-ST-003: データサイエンティストの典型的な作業フロー
- **シナリオ**:
  1. 新しいデータセットをS3にアップロード
  2. GitHub Issueで学習リクエスト
  3. 初回学習の精度が低い
  4. ハイパーパラメータを調整して再学習
  5. 精度が改善し、モデル登録
- **期待結果**: スムーズに作業完了

---

## 5. 性能テスト設計

### 5.1 負荷テスト

#### TC-PT-001: 同時実行性能
- **目的**: 10並列実行時の性能確認
- **テスト条件**:
  - 10個のIssueを同時作成
  - 各学習ジョブは5分程度
- **期待結果**:
  - すべてのジョブが正常完了
  - レスポンスタイムの劣化が20%以内

#### TC-PT-002: 大規模データ処理性能
- **目的**: 大規模データでの処理時間確認
- **テスト条件**:
  - データサイズ: 1GB (100万件)
  - インスタンスタイプ: ml.m5.xlarge
- **期待結果**:
  - データ準備: 10分以内
  - 学習: 30分以内
  - 評価: 5分以内

---

### 5.2 スケーラビリティテスト

#### TC-PT-003: スケールアウト性能
- **目的**: 並列数増加時の性能検証
- **テスト条件**: 1, 5, 10, 20並列
- **期待結果**: リニアにスケールアウト

---

### 5.3 ストレステスト

#### TC-PT-004: 長時間実行テスト
- **目的**: 24時間連続実行時の安定性
- **テスト条件**: 1時間ごとに学習ジョブを投入
- **期待結果**: メモリリークやエラーが発生しない

---

## 6. セキュリティテスト設計

### 6.1 認証・認可テスト

#### TC-SEC-001: IAMロール権限確認
- **目的**: 最小権限の原則が守られているか確認
- **テスト方法**:
  - Lambda実行ロールで不要なサービスへのアクセスを試行
  - 期待: アクセス拒否
- **期待結果**: 必要最小限の権限のみ付与

#### TC-SEC-002: GitHub Token漏洩防止
- **目的**: Secrets Managerの適切な使用確認
- **テスト方法**:
  - CloudWatch Logsにトークンが出力されていないか確認
- **期待結果**: ログにトークンが含まれない

---

### 6.2 データ保護テスト

#### TC-SEC-003: S3暗号化確認
- **目的**: S3オブジェクトの暗号化確認
- **テスト方法**: S3オブジェクトのメタデータ確認
- **期待結果**: すべてのオブジェクトが暗号化されている

#### TC-SEC-004: データアクセス制御
- **目的**: 不正なS3アクセスの防止
- **テスト方法**: 権限のないIAMロールでアクセス試行
- **期待結果**: アクセス拒否

---

### 6.3 脆弱性テスト

#### TC-SEC-005: 依存ライブラリの脆弱性スキャン
- **目的**: CVE脆弱性の検出
- **テスト方法**: `pip-audit`や`safety`でスキャン
- **期待結果**: クリティカルな脆弱性がない

#### TC-SEC-006: コードインジェクション対策
- **目的**: YAML/JSONパース時のインジェクション防止
- **テスト方法**: 悪意のあるペイロードを送信
- **期待結果**: 適切にサニタイズされる

---

## 7. 受入テスト設計

### 7.1 ユーザー受入テスト (UAT)

#### TC-UAT-001: ビジネス要件の充足確認
- **確認項目**:
  - [ ] GitHub Issueから学習が起動できる
  - [ ] 3種類の学習方式がすべて動作する
  - [ ] 評価結果が正しく表示される
  - [ ] 再学習が正常に動作する
  - [ ] ロールバックが正常に動作する
  - [ ] 学習履歴がGitHubに保存される

#### TC-UAT-002: ユーザビリティ確認
- **確認項目**:
  - [ ] Issue作成が簡単か
  - [ ] 通知が分かりやすいか
  - [ ] 学習履歴が見やすいか

---

## 8. テスト自動化

### 8.1 CI/CD統合

**GitHub Actionsでの自動テスト実行**:

```yaml
name: MLOps CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  unit-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run unit tests
        run: pytest tests/unit --cov=agents --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  integration-test:
    runs-on: ubuntu-latest
    needs: unit-test
    steps:
      - uses: actions/checkout@v3
      - name: Run integration tests
        run: pytest tests/integration

  security-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run security scan
        run: |
          pip install pip-audit safety
          pip-audit
          safety check
```

### 8.2 テストツール

| ツール | 用途 |
|---|---|
| pytest | 単体・統合テスト実行 |
| pytest-cov | カバレッジ測定 |
| moto | AWS サービスのモック |
| responses | HTTPリクエストのモック |
| locust | 負荷テスト |
| bandit | セキュリティスキャン |
| pip-audit | 依存関係の脆弱性スキャン |

---

## 9. テストデータ管理

### 9.1 テストデータセット

| データセット名 | 用途 | サイズ | 形式 |
|---|---|---|---|
| test-supervised-small | 単体テスト（教師あり） | 100件 | CSV |
| test-supervised-large | 性能テスト（教師あり） | 100万件 | CSV |
| test-unsupervised-small | 単体テスト（教師なし） | 100件 | CSV |
| test-reinforcement-env | 強化学習環境 | - | Gym Env |

**保存場所**: `s3://mlops-test-bucket/test-datasets/`

---

## 10. テスト環境

### 10.1 環境構成

| 環境 | 用途 | AWS アカウント |
|---|---|---|
| Dev | 開発・単体テスト | 開発用アカウント |
| Test | 統合・システムテスト | テスト用アカウント |
| Staging | 受入テスト | 本番相当アカウント |
| Production | 本番運用 | 本番アカウント |

### 10.2 環境固有設定

```python
# config/test_config.py
TEST_CONFIG = {
    "dev": {
        "s3_bucket": "mlops-dev-bucket",
        "sagemaker_instance": "ml.t3.medium",
        "max_parallel_jobs": 2
    },
    "test": {
        "s3_bucket": "mlops-test-bucket",
        "sagemaker_instance": "ml.m5.large",
        "max_parallel_jobs": 5
    },
    "staging": {
        "s3_bucket": "mlops-staging-bucket",
        "sagemaker_instance": "ml.m5.xlarge",
        "max_parallel_jobs": 10
    }
}
```

---

## 11. テスト実施計画

### 11.1 テストスケジュール

| フェーズ | 期間 | 実施内容 |
|---|---|---|
| Phase 1 | Week 1-2 | 単体テスト実装・実施 |
| Phase 2 | Week 3-4 | 統合テスト実施 |
| Phase 3 | Week 5 | システムテスト実施 |
| Phase 4 | Week 6 | 性能・セキュリティテスト実施 |
| Phase 5 | Week 7 | 受入テスト実施 |

### 11.2 テスト完了基準

- [ ] すべての単体テストがパス（カバレッジ80%以上）
- [ ] すべての統合テストがパス
- [ ] すべてのシステムテストがパス
- [ ] 性能要件を満たす（NFR-001, NFR-002）
- [ ] セキュリティテストで重大な問題がない
- [ ] 受入テストでユーザー承認を得る

---

## 12. 不具合管理

### 12.1 不具合分類

| 重要度 | 定義 | 対応期限 |
|---|---|---|
| Critical | システムが動作しない | 即座 |
| High | 主要機能が動作しない | 1日以内 |
| Medium | 一部機能に問題がある | 1週間以内 |
| Low | 軽微な問題 | 次リリース |

### 12.2 不具合トラッキング

- **ツール**: GitHub Issues
- **ラベル**: `bug`, `critical`, `high`, `medium`, `low`

---

## 13. テストメトリクス

### 13.1 測定指標

| メトリクス | 目標値 |
|---|---|
| コードカバレッジ | 80%以上 |
| 単体テストパス率 | 100% |
| 統合テストパス率 | 100% |
| システムテストパス率 | 100% |
| 不具合検出率 | 開発段階で80%以上 |
| 平均修正時間 | Critical: 2時間以内、High: 1日以内 |

---

## 14. 変更履歴

| バージョン | 日付 | 変更内容 | 作成者 |
|---|---|---|---|
| 0.1 | 2025-10-10 | 初版作成 | - |

---

## 15. 付録

### 15.1 テストケーステンプレート

```markdown
## TC-XX-YYY: テストケース名

**目的**: テストの目的

**前提条件**:
- 前提条件1
- 前提条件2

**テスト手順**:
1. ステップ1
2. ステップ2
3. ステップ3

**入力データ**:
- データ1
- データ2

**期待結果**:
- 期待する結果1
- 期待する結果2

**実際の結果**:
[テスト実施後に記入]

**ステータス**: PASS / FAIL

**備考**:
[特記事項があれば記入]
```

### 15.2 モックデータサンプル

```python
# tests/fixtures/mock_data.py

MOCK_GITHUB_WEBHOOK = {
    "action": "opened",
    "issue": {
        "number": 123,
        "labels": [{"name": "mlops:train"}],
        "body": """
learning_type: supervised
algorithm: random_forest
dataset_id: test-dataset-001
hyperparameters:
  n_estimators: 100
  max_depth: 10
evaluation_threshold: 0.85
max_retry: 3
"""
    },
    "repository": {
        "full_name": "org/repo"
    }
}

MOCK_TRAINING_CONFIG = {
    "issue_number": 123,
    "learning_type": "supervised",
    "algorithm": "random_forest",
    "dataset_id": "test-dataset-001",
    "hyperparameters": {
        "n_estimators": 100,
        "max_depth": 10
    },
    "evaluation_threshold": 0.85,
    "max_retry": 3
}

MOCK_EVALUATION_RESULTS = {
    "accuracy": 0.87,
    "precision": 0.85,
    "recall": 0.89,
    "f1_score": 0.87,
    "auc_roc": 0.91
}
```
