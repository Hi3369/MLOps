# プロジェクト構造ガイド

このドキュメントでは、MLOpsプロジェクトのディレクトリ構造とファイルの役割を説明します。

## ディレクトリ構造

![Directory Structure](diagrams/directory_structure.mmd)

**ダイアグラム**: [diagrams/directory_structure.mmd](diagrams/directory_structure.mmd)

### テキスト形式のディレクトリツリー

<details>
<summary>詳細なディレクトリ構造を表示（クリックして展開）</summary>

```text
MLOps/
├── README.md                              # プロジェクト概要・使い方
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
├── docs/                                  # ドキュメント
│   ├── specifications/                   # 仕様書
│   │   └── system_specification.md      # システム仕様書（機能要件、非機能要件、アーキテクチャ）
│   │
│   ├── designs/                          # 設計書
│   │   ├── mcp_design.md                # MCP設計書（統合MCPサーバー設計、セキュリティ）
│   │   └── implementation_guide.md      # 実装ガイド（実装設計、ワークフロー、開発・運用）
│   │
│   ├── reviews/                          # レビュー記録
│   │   ├── aeccac7f80a7f090dd9c49b91aded0ace072c42a/
│   │   │   └── REVIEW.md               # ドキュメント統合レビュー
│   │   ├── 67f469b273e25bba3454858a6f2de40d0202979e/
│   │   │   └── REVIEW.md               # 用語集レビュー
│   │   ├── 16273bde26a95b2a7e3cf515655599f252000354/
│   │   │   └── REVIEW.md               # 自動運転ユースケース追加レビュー
│   │   └── eaa0ad0a53d5d24678b8dba91642038400ccd4f0/
│   │       └── REVIEW.md               # 統合MCPサーバー設計レビュー
│   │
│   └── others/                           # その他ドキュメント
│       ├── glossary.md                  # 用語集（MLOps技術用語・略語・概念）
│       └── risk_management.md           # リスク管理マトリクス
│
├── mcp_server/                            # 統合MCPサーバー実装
│   ├── README.md                         # MCPサーバー説明・使い方
│   ├── server.py                         # MCPサーバーメイン
│   │
│   ├── common/                           # 共通モジュール
│   │   ├── __init__.py
│   │   ├── aws_client.py                # AWS SDK ラッパー
│   │   ├── logger.py                    # ロギング設定
│   │   └── exceptions.py                # カスタム例外
│   │
│   └── capabilities/                     # 11 Capabilities
│       ├── data_preparation/            # Capability 1: データ準備
│       │   ├── __init__.py
│       │   └── tools/                   # MCPツール実装
│       │       ├── load_dataset.py
│       │       ├── preprocess_data.py
│       │       └── validate_data.py
│       │
│       ├── ml_training/                 # Capability 2: ML学習
│       │   ├── __init__.py
│       │   └── tools/
│       │       ├── supervised/          # 教師あり学習
│       │       │   ├── train_classifier.py
│       │       │   └── train_regressor.py
│       │       ├── unsupervised/        # 教師なし学習
│       │       │   ├── train_clustering.py
│       │       │   └── train_dimensionality_reduction.py
│       │       └── reinforcement/       # 強化学習
│       │           └── train_rl.py
│       │
│       ├── ml_evaluation/               # Capability 3: ML評価
│       │   ├── __init__.py
│       │   └── tools/
│       │       ├── evaluate_model.py
│       │       └── calculate_metrics.py
│       │
│       ├── model_packaging/             # Capability 4: モデルパッケージング
│       │   ├── __init__.py
│       │   └── tools/
│       │       ├── export_to_onnx.py
│       │       └── export_to_pkl.py
│       │
│       ├── model_deployment/            # Capability 5: モデルデプロイメント
│       │   ├── __init__.py
│       │   └── tools/
│       │       ├── deploy_endpoint.py
│       │       └── update_endpoint.py
│       │
│       ├── monitoring/                  # Capability 6: モニタリング
│       │   ├── __init__.py
│       │   └── tools/
│       │       ├── get_endpoint_metrics.py
│       │       └── detect_drift.py
│       │
│       ├── workflow_optimization/       # Capability 7: ワークフロー最適化
│       │   ├── __init__.py
│       │   └── tools/
│       │       ├── analyze_execution_time.py
│       │       └── suggest_parallelization.py
│       │
│       ├── github_integration/          # Capability 8: GitHub統合
│       │   ├── __init__.py
│       │   └── tools/
│       │       ├── create_comment.py
│       │       └── update_issue.py
│       │
│       ├── retrain_orchestration/      # Capability 9: 再学習オーケストレーション
│       │   ├── __init__.py
│       │   └── tools/
│       │       ├── check_retrain_triggers.py
│       │       └── start_retrain_workflow.py
│       │
│       ├── notification/                # Capability 10: 通知
│       │   ├── __init__.py
│       │   └── tools/
│       │       ├── send_slack.py
│       │       └── send_email.py
│       │
│       └── history_management/          # Capability 11: 履歴管理
│           ├── __init__.py
│           └── tools/
│               ├── format_training_history.py
│               └── commit_to_github.py
│
├── mcp_servers_legacy/                    # 旧MCPサーバー（非推奨・参考用）
│   ├── README.md                         # レガシーMCPサーバー説明
│   ├── data_preparation/
│   ├── ml_training/
│   ├── ml_evaluation/
│   ├── github_integration/
│   ├── model_registry/
│   └── notification/
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
│   │   ├── test_data_preparation.py
│   │   ├── test_ml_training.py
│   │   ├── test_ml_evaluation.py
│   │   └── test_mcp_server.py
│   │
│   ├── integration/                     # 統合テスト
│   │   ├── test_capability_integration.py
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

| ファイル                                     | 説明                                           |
| -------------------------------------------- | ---------------------------------------------- |
| [README.md](README.md)                       | プロジェクトの概要、セットアップ手順、使い方 |
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | プロジェクト構造の説明（このファイル）         |
| requirements.txt                             | Python依存ライブラリ一覧                       |
| .gitignore                                   | Git管理対象外ファイル設定                      |

### docs/ - ドキュメント

#### 仕様書 (docs/specifications/)

| ファイル                                                                   | 説明                                                                                         |
| -------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| [system_specification.md](docs/specifications/system_specification.md)    | システム仕様書（機能要件、非機能要件、システムアーキテクチャ、自動運転ユースケース）         |

#### 設計書 (docs/designs/)

| ファイル                                                            | 説明                                                                                 |
| ------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| [mcp_design.md](docs/designs/mcp_design.md)                        | MCP設計書（統合MLOps MCPサーバー設計、11 Capabilities、セキュリティ設計）          |
| [implementation_guide.md](docs/designs/implementation_guide.md)    | 実装ガイド（実装設計、MLOpsワークフロー、開発・運用ガイド、自動運転実装例）       |

#### レビュー記録 (docs/reviews/)

各コミットに対する設計レビュー記録:

| ディレクトリ           | 内容                                           |
| ---------------------- | ---------------------------------------------- |
| aeccac7f/REVIEW.md     | ドキュメント統合レビュー（8→4ファイルに統合） |
| 67f469b2/REVIEW.md     | 用語集追加レビュー                             |
| 16273bde/REVIEW.md     | 自動運転ユースケース追加レビュー               |
| eaa0ad0a/REVIEW.md     | 統合MCPサーバー設計レビュー                    |

#### その他 (docs/others/)

| ファイル                                                | 説明                                                                   |
| ------------------------------------------------------- | ---------------------------------------------------------------------- |
| [glossary.md](docs/others/glossary.md)                 | MLOps技術用語・略語・概念の定義（100+用語、自動運転用語26語含む）      |
| [risk_management.md](docs/others/risk_management.md)   | リスク管理マトリクス（技術・セキュリティ・運用・ビジネスリスク）       |

### mcp_server/ - 統合MCPサーバー

統合MLOps MCPサーバーの実装:

- **server.py**: MCPサーバーのメインエントリーポイント
- **common/**: AWS SDK、ロギング、例外処理などの共通モジュール
- **capabilities/**: 11個のCapabilityグループ
  - Capability 1: Data Preparation
  - Capability 2: ML Training（教師あり・教師なし・強化学習）
  - Capability 3: ML Evaluation
  - Capability 4: GitHub Integration
  - Capability 5: Model Registry
  - Capability 6: Notification

詳細は[mcp_server/README.md](mcp_server/README.md)を参照。

### mcp_servers_legacy/ - 旧MCPサーバー（非推奨）

旧アーキテクチャのMCPサーバー実装。参考用として残されていますが、新規開発では**統合MCPサーバー（mcp_server/）**を使用してください。

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

1. **unit/**: 各Capabilityの単体テスト（モック使用）
2. **integration/**: Capability間連携テスト、Step Functionsテスト
3. **system/**: エンドツーエンドのシステムテスト（教師あり・教師なし・強化学習）

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

### 1. 新しいMCP Capabilityの追加

```bash
# 1. ディレクトリ作成
mkdir -p mcp_server/capabilities/new_capability/tools

# 2. ファイル作成
touch mcp_server/capabilities/new_capability/__init__.py
touch mcp_server/capabilities/new_capability/tools/new_tool.py

# 3. テスト作成
touch tests/unit/test_new_capability.py
```

### 2. テスト実行

```bash
# 単体テスト
pytest tests/unit/test_new_capability.py

# すべてのテスト
pytest

# カバレッジ付き
pytest --cov=mcp_server --cov-report=html
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
- **MCP仕様準拠**: [Model Context Protocol仕様](https://spec.modelcontextprotocol.io/)に従う

### テスト

- **カバレッジ80%以上**: pytest-covで測定
- **モック使用**: 外部サービスはmoto、responsesでモック
- **テスト駆動開発**: 実装前にテストを書く

### セキュリティ

- **シークレット管理**: AWS Secrets Manager使用
- **最小権限**: IAMロールは最小権限の原則
- **脆弱性スキャン**: pip-audit、banditで定期スキャン
- **リスク管理**: [リスク管理マトリクス](docs/others/risk_management.md)を参照

## ドキュメント体系

```text
docs/
├── specifications/          # 仕様書（What）
│   └── system_specification.md
│
├── designs/                 # 設計書（How）
│   ├── mcp_design.md       # MCP統合設計
│   └── implementation_guide.md  # 実装ガイド
│
├── reviews/                 # レビュー記録（Quality Assurance）
│   └── [commit_hash]/REVIEW.md
│
└── others/                  # その他
    ├── glossary.md          # 用語集
    └── risk_management.md   # リスク管理
```

## 次のステップ

1. [README.md](README.md)でセットアップ手順を確認
2. [用語集](docs/others/glossary.md)でMLOps用語を理解
3. [システム仕様書](docs/specifications/system_specification.md)で要件を理解
4. [MCP設計書](docs/designs/mcp_design.md)でアーキテクチャを学習
5. [実装ガイド](docs/designs/implementation_guide.md)で実装を開始

## 問い合わせ

質問や問題がある場合は、GitHub Issuesで報告してください。
