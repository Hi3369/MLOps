# プロジェクト構造ガイド

このドキュメントでは、MLOpsプロジェクトのディレクトリ構造とファイルの役割を説明します。

## ディレクトリ構造

![Directory Structure](diagrams/directory_structure.mmd)

**ダイアグラム**: [diagrams/directory_structure.mmd](diagrams/directory_structure.mmd)

### テキスト形式のディレクトリツリー

<details>
<summary>詳細なディレクトリ構造を表示（クリックして展開）</summary>

```
MLOps/
├── README.md                              # プロジェクト概要・使い方
├── requirements_specification.md          # 要件仕様書
├── architecture_design.md                 # アーキテクチャ設計書
├── test_design.md                         # テスト設計書
├── PROJECT_STRUCTURE.md                   # このファイル
├── .gitignore                             # Git除外設定
├── requirements.txt                       # Python依存関係
│
├── diagrams/                              # Mermaidダイアグラム
│   ├── README.md                         # ダイアグラム説明
│   ├── system_architecture.mmd           # システムアーキテクチャ図
│   ├── data_flow.mmd                     # データフロー図
│   ├── step_functions_workflow.mmd       # Step Functionsワークフロー図
│   ├── agent_architecture.mmd            # エージェントアーキテクチャ図
│   ├── s3_bucket_structure.mmd           # S3バケット構造図
│   ├── learning_types.mmd                # 学習方式図
│   └── directory_structure.mmd           # ディレクトリ構造図
│
├── agents/                                # エージェント実装
│   ├── __init__.py
│   ├── common/                           # 共通モジュール
│   │   ├── __init__.py
│   │   ├── aws_client.py                # AWS SDK ラッパー
│   │   ├── github_client.py             # GitHub API ラッパー
│   │   ├── logger.py                    # ロギング設定
│   │   └── exceptions.py                # カスタム例外
│   │
│   ├── issue_detector/                   # Issue検知エージェント
│   │   ├── __init__.py
│   │   ├── handler.py                   # Lambda ハンドラー
│   │   ├── parser.py                    # YAML/JSON パーサー
│   │   └── validator.py                 # 入力バリデーション
│   │
│   ├── data_preparation/                 # データ準備エージェント
│   │   ├── __init__.py
│   │   ├── handler.py
│   │   ├── loader.py                    # データ読み込み
│   │   ├── preprocessor.py              # 前処理
│   │   └── validator.py                 # データバリデーション
│   │
│   ├── training/                         # 学習エージェント
│   │   ├── __init__.py
│   │   ├── handler.py
│   │   ├── supervised/                  # 教師あり学習
│   │   │   ├── __init__.py
│   │   │   ├── classifier.py
│   │   │   └── regressor.py
│   │   ├── unsupervised/                # 教師なし学習
│   │   │   ├── __init__.py
│   │   │   ├── clustering.py
│   │   │   └── dimensionality_reduction.py
│   │   └── reinforcement/               # 強化学習
│   │       ├── __init__.py
│   │       └── rl_trainer.py
│   │
│   ├── evaluation/                       # 評価エージェント
│   │   ├── __init__.py
│   │   ├── handler.py
│   │   ├── metrics.py                   # 評価指標計算
│   │   └── visualizer.py                # 可視化
│   │
│   ├── judge/                            # 判定エージェント
│   │   ├── __init__.py
│   │   ├── handler.py
│   │   └── decision.py                  # 判定ロジック
│   │
│   ├── notification/                     # 通知エージェント
│   │   ├── __init__.py
│   │   ├── handler.py
│   │   ├── github_notifier.py           # GitHub通知
│   │   ├── slack_notifier.py            # Slack通知
│   │   └── email_notifier.py            # Email通知
│   │
│   ├── rollback/                         # ロールバックエージェント
│   │   ├── __init__.py
│   │   ├── handler.py
│   │   └── model_version_manager.py     # モデルバージョン管理
│   │
│   └── history_writer/                   # 履歴保存エージェント
│       ├── __init__.py
│       ├── handler.py
│       ├── formatter.py                 # Markdown フォーマッター
│       └── github_writer.py             # GitHub書き込み
│
├── cdk/                                  # AWS CDK (IaC)
│   ├── app.py                           # CDKアプリケーション
│   ├── requirements.txt                 # CDK依存関係
│   ├── cdk.json                         # CDK設定
│   ├── package.json                     # Node.js依存関係
│   │
│   └── stacks/                          # CDKスタック定義
│       ├── __init__.py
│       ├── pipeline_stack.py           # Step Functions/Lambda等
│       ├── storage_stack.py            # S3/DynamoDB等
│       ├── compute_stack.py            # ECS/SageMaker等
│       └── monitoring_stack.py         # CloudWatch等
│
├── tests/                                # テストコード
│   ├── __init__.py
│   ├── conftest.py                      # pytest設定・共通フィクスチャ
│   ├── fixtures/                        # テストデータ
│   │   ├── mock_data.py
│   │   └── sample_datasets/
│   │
│   ├── unit/                            # 単体テスト
│   │   ├── test_issue_detector.py
│   │   ├── test_data_preparation.py
│   │   ├── test_training.py
│   │   ├── test_evaluation.py
│   │   ├── test_judge.py
│   │   ├── test_notification.py
│   │   ├── test_rollback.py
│   │   └── test_history_writer.py
│   │
│   ├── integration/                     # 統合テスト
│   │   ├── test_agent_integration.py
│   │   └── test_step_functions.py
│   │
│   └── system/                          # システムテスト
│       ├── test_e2e_supervised.py
│       ├── test_e2e_unsupervised.py
│       └── test_e2e_reinforcement.py
│
├── config/                               # 設定ファイル
│   ├── dev_config.yaml                 # 開発環境
│   ├── test_config.yaml                # テスト環境
│   └── prod_config.yaml                # 本番環境
│
├── docs/                                 # ドキュメント
│   ├── getting_started.md              # 入門ガイド
│   ├── api_reference.md                # API リファレンス
│   ├── deployment_guide.md             # デプロイガイド
│   └── troubleshooting.md              # トラブルシューティング
│
├── training_history/                     # 学習履歴（自動生成）
│   ├── train-20250110-001.md
│   ├── train-20250110-002.md
│   └── ...
│
└── .github/
    └── workflows/                        # GitHub Actions CI/CD
        ├── ci-cd.yaml                   # CI/CDパイプライン
        ├── security-scan.yaml           # セキュリティスキャン
        └── deploy.yaml                  # デプロイメント
```

</details>

## 主要ファイルの説明

### ルートディレクトリ

| ファイル | 説明 |
|---------|------|
| [README.md](README.md) | プロジェクトの概要、セットアップ手順、使い方 |
| [requirements_specification.md](requirements_specification.md) | 機能要件・非機能要件の詳細 |
| [architecture_design.md](architecture_design.md) | システムアーキテクチャ、各コンポーネント設計 |
| [test_design.md](test_design.md) | テスト戦略、テストケース、テスト計画 |
| requirements.txt | Python依存ライブラリ一覧 |
| .gitignore | Git管理対象外ファイル設定 |

### agents/ - エージェント実装

各エージェントは独立したディレクトリで管理され、以下の構造を持ちます:

- **handler.py**: Lambda関数のエントリーポイント
- **ビジネスロジック**: エージェント固有の処理
- **__init__.py**: モジュール初期化

#### 共通モジュール (agents/common/)

全エージェントで共有するユーティリティ:

- **aws_client.py**: S3, SageMaker, SNS等のAWS APIクライアント
- **github_client.py**: PyGitHubを使ったGitHub API操作
- **logger.py**: CloudWatch Logsへのログ出力設定
- **exceptions.py**: カスタム例外クラス

### cdk/ - Infrastructure as Code

AWS CDKを使ったインフラ定義:

- **app.py**: CDKアプリケーションのエントリーポイント
- **stacks/**: 各AWSリソースのスタック定義
  - **pipeline_stack.py**: Step Functions、Lambda関数
  - **storage_stack.py**: S3バケット、DynamoDBテーブル
  - **compute_stack.py**: ECSタスク、SageMakerリソース
  - **monitoring_stack.py**: CloudWatch、アラーム

### tests/ - テストコード

3層のテスト構造:

1. **unit/**: 各エージェントの単体テスト（モック使用）
2. **integration/**: エージェント間連携テスト
3. **system/**: エンドツーエンドのシステムテスト

#### フィクスチャ (tests/fixtures/)

- **mock_data.py**: テスト用のモックデータ
- **sample_datasets/**: サンプルデータセット（CSV等）

### config/ - 設定ファイル

環境別の設定をYAML形式で管理:

- **dev_config.yaml**: 開発環境（小さいインスタンス、低コスト）
- **test_config.yaml**: テスト環境（中規模インスタンス）
- **prod_config.yaml**: 本番環境（大規模インスタンス、高可用性）

### training_history/ - 学習履歴

システムが自動生成する学習結果のMarkdownファイル:

- 学習パラメータ
- 評価結果
- モデル情報
- 実行ログ

## 開発フロー

### 1. 新しいエージェントの追加

```bash
# 1. ディレクトリ作成
mkdir -p agents/new_agent

# 2. ファイル作成
touch agents/new_agent/__init__.py
touch agents/new_agent/handler.py

# 3. テスト作成
touch tests/unit/test_new_agent.py
```

### 2. テスト実行

```bash
# 単体テスト
pytest tests/unit/test_new_agent.py

# すべてのテスト
pytest

# カバレッジ付き
pytest --cov=agents --cov-report=html
```

### 3. CDKデプロイ

```bash
cd cdk

# スタックの差分確認
cdk diff

# デプロイ
cdk deploy --all
```

## ベストプラクティス

### コーディング規約

- **PEP 8準拠**: black、flake8でフォーマット
- **型ヒント**: mypy で型チェック
- **ドキュメント**: docstringを必ず記載

### テスト

- **カバレッジ80%以上**: pytest-covで測定
- **モック使用**: 外部サービスはmoto、responsesでモック
- **テスト駆動開発**: 実装前にテストを書く

### セキュリティ

- **シークレット管理**: AWS Secrets Manager使用
- **最小権限**: IAMロールは最小権限の原則
- **脆弱性スキャン**: pip-audit、banditで定期スキャン

## 次のステップ

1. [README.md](README.md)でセットアップ手順を確認
2. [requirements_specification.md](requirements_specification.md)で要件を理解
3. [architecture_design.md](architecture_design.md)でアーキテクチャを学習
4. 各エージェントの実装を開始

## 問い合わせ

質問や問題がある場合は、GitHub Issuesで報告してください。
