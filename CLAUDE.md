# Claude Code プロジェクトガイドライン

## プロジェクト概要

### MLOpsとは

**MLOps（Machine Learning Operations）** は、機械学習モデルの開発から本番運用までのライフサイクル全体を効率化・自動化するための手法とツールの総称。

### 本プロジェクトの目的

GitHub Issueをトリガーとして、機械学習モデルの学習・評価・デプロイを自動化する**MLOpsパイプライン**を構築する。

### アーキテクチャ

```text
[GitHub Issue] → [Issue Detector Agent] → [Step Functions Workflow]
                                                    ↓
┌─────────────────────────────────────────────────────────────────┐
│                    MLOps MCP Server                             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ Data Prep    │ │ ML Training  │ │ ML Evaluation│            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ Packaging    │ │ Deployment   │ │ Monitoring   │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                                                    ↓
                              [SageMaker Endpoint] → [CloudWatch監視]
```

### 主要機能

| フェーズ | 機能 | 説明 |
|---------|------|------|
| **データ準備** | 前処理・特徴量エンジニアリング | S3からデータ読み込み、バリデーション、分割 |
| **学習** | モデル訓練・ハイパーパラメータ最適化 | SageMaker学習ジョブ実行 |
| **評価** | メトリクス計算・バイアス検出 | Accuracy, F1, SHAP値等 |
| **パッケージング** | コンテナ化・ECR登録 | Dockerイメージビルド |
| **デプロイ** | エンドポイント作成・A/Bテスト | SageMaker Endpoints |
| **監視** | ドリフト検出・アラート | CloudWatch, Model Monitor |
| **再学習** | 自動トリガー・スケジュール実行 | EventBridge, Step Functions |

### 技術スタック

- **言語**: Python 3.12+
- **プロトコル**: Model Context Protocol (MCP)
- **クラウド**: AWS (SageMaker, S3, ECR, Step Functions, EventBridge, CloudWatch)
- **CI/CD**: GitHub Actions
- **テスト**: pytest

---

## コーディング基準

経験豊富なプログラマーとしてコードを実装・修正すること:

- クリーンで読みやすいコードを書く
- 適切なエラーハンドリングを実装
- 型ヒントを適切に使用
- docstringでドキュメント化
- Python 3.12+の最新機能を活用（`datetime.now(timezone.utc)` 等）
- インポートはファイル先頭に配置
- 未使用のインポート・変数は削除

## コードレビュー基準

経験豊富なコードレビューアーとしてレビューを実施すること:

### チェックポイント

1. **コード品質**
   - 命名規則の一貫性
   - 関数の単一責任原則
   - 重複コードの排除

2. **セキュリティ**
   - 入力値の検証
   - 機密情報のハードコーディング防止
   - 適切な権限管理

3. **パフォーマンス**
   - 不要なループ・計算の回避
   - 適切なデータ構造の選択
   - リソースの適切な解放

4. **保守性**
   - 適切なコメント・ドキュメント
   - テストカバレッジ
   - 明確なエラーメッセージ

## AWS情報の取得

AWS関連の情報はAWS MCP Serversから取得すること:

- ドキュメント: `awslabs.aws-documentation-mcp-server`
- API操作: `awslabs.aws-api-mcp-server`
- ナレッジ: `awslabs.aws-knowledge-mcp-server`

詳細: <https://awslabs.github.io/mcp/>

## Git ワークフロー

### 実装フェーズ

1. developからfeatureブランチを作成
2. 熟練の実装技術者として実装
   - Dict-basedパターンに従う（Capabilityの場合）
   - 環境別の動作（mock/real）を考慮
3. 熟練のテスト技術者としてテスト作成
   - 正常系・異常系・統合テストを網羅
   - 40件以上のテストケースを目標
4. 熟練の実装技術者としてエラーが無くなるまでテストと修正を繰り返す

### レビューフェーズ

1. 熟練のコードレビュアーとしてコードレビュー
   - 本ドキュメントのレビュー基準に従う
2. 熟練の実装技術者としてレビュー指摘箇所を修正

### 品質確認フェーズ

1. 熟練のコード品質管理者としてLint/フォーマッター実行

   ```bash
   flake8 <path> --max-line-length=100
   black <path>
   ```

2. テストを再実行して全パスを確認

### マージフェーズ

1. developにマージ（--no-ff）
2. featureブランチを削除

## Capability実装パターン

### Dict-basedパターン

```python
class XxxCapability:
    def __init__(self):
        self._tools: Dict[str, Callable] = {...}
        self._tool_schemas: Dict[str, Dict[str, Any]] = {...}

    def get_tools(self) -> Dict[str, Callable]: ...
    def get_tool_schemas(self) -> Dict[str, Dict[str, Any]]: ...
```

### 環境別動作

- 開発/テスト環境（MLOPS_ENV=development/test）: モック動作
- 本番環境: 実際のAWSサービス呼び出し

### ツール関数パターン

```python
def tool_function(
    required_param: str,
    optional_param: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    ツールの説明（日本語）

    Args:
        required_param: 必須パラメータの説明
        optional_param: オプションパラメータの説明

    Returns:
        結果辞書
    """
    # パラメータ検証
    if not required_param:
        raise ValueError("required_param must not be empty")

    try:
        timestamp = datetime.now(timezone.utc).isoformat()
        result_id = str(uuid4())[:8]

        env = os.environ.get("MLOPS_ENV", "development")

        # 開発/テスト環境ではモック
        if env in ["development", "test"]:
            return _mock_function(...)

        # 本番環境
        return _real_function(...)

    except Exception as e:
        logger.error(f"Failed to ...: {e}")
        raise ValueError(f"Failed to ...: {e}")
```

## プロジェクト構造

### 設計書

- 設計書: [docs/designs/mcp_design.md](docs/designs/mcp_design.md)
- 実装ガイド: [docs/designs/implementation_guide.md](docs/designs/implementation_guide.md)
- エージェント設計: [docs/designs/agent_design.md](docs/designs/agent_design.md)

### 12 Capabilities

| # | Capability | 責務 | 主要AWSサービス |
|---|-----------|------|----------------|
| 1 | github_integration | Issue検知・ワークフロー起動 | Step Functions |
| 2 | workflow_optimization | モデル特性分析・最適化提案 | - |
| 3 | data_preparation | データ前処理・特徴量エンジニアリング | S3 |
| 4 | ml_training | モデル学習・ハイパーパラメータ最適化 | SageMaker |
| 5 | ml_evaluation | モデル評価・メトリクス計算 | SageMaker Clarify |
| 6 | model_packaging | コンテナ化・ECR登録 | ECR |
| 7 | model_deployment | エンドポイントデプロイ | SageMaker Endpoints |
| 8 | model_monitoring | パフォーマンス監視・ドリフト検出 | CloudWatch, SageMaker Model Monitor |
| 9 | retrain_management | 再学習トリガー管理 | Step Functions, EventBridge |
| 10 | notification | 通知送信 | SNS, GitHub API |
| 11 | history_management | 学習履歴記録・GitHub連携 | S3, GitHub API |
| 12 | model_registry | モデルバージョン管理 | SageMaker Model Registry |

### テストファイル配置

```text
tests/unit/test_<capability_name>.py
```

## 参照パターン

### 実装時の参照ファイル

| 目的 | 参照ファイル |
|------|------------|
| Dict-basedパターン | `mcp_server/capabilities/notification/capability.py` |
| GitHub API連携 | `mcp_server/capabilities/notification/tools/send_github_notification.py` |
| Step Functions連携 | `mcp_server/capabilities/github_integration/tools/start_workflow.py` |
| ドリフト検知 | `mcp_server/capabilities/model_monitoring/tools/detect_data_drift.py` |
| テストパターン | `tests/unit/test_notification.py` |

### 機能要件ID（FR-xxx）

設計書の機能要件IDを実装時に参照すること:

- FR-025: 自動再学習トリガー
- FR-026: 再学習パイプライン（新旧モデル比較）
- FR-027: セマンティックバージョニング
- FR-028: フィードバックループ

## 品質基準

### テスト基準

- 各Capabilityに40件以上のテストケース
- カバー範囲: 正常系、異常系（バリデーションエラー）、統合テスト
- モック動作のテスト（開発/テスト環境）

### Lint設定

```bash
# isort（インポート整理）
isort --profile black <path>

# black（フォーマット）
black <path>

# flake8（静的解析）
flake8 <path> --max-line-length=100
```

### コミットメッセージ規約

```text
<type>: <subject>

<body>

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

type: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

## MLOps専門家スキル

MLOps運用に必要な6つの専門家スキルを `.claude/skills/` に定義。
Claudeが作業内容に応じて自動的に適切なスキルを選択、または `/data-engineer` 等で明示的に呼び出し可能。

### スキル一覧

| スキル | コマンド | 専門領域 | 担当Capability |
|--------|---------|----------|----------------|
| Data Engineer | `/data-engineer` | データパイプライン、ETL、データ品質 | data_preparation |
| ML Engineer | `/ml-engineer` | モデル開発、学習、評価 | ml_training, ml_evaluation |
| MLOps Engineer | `/mlops-engineer` | インフラ、デプロイ、監視 | model_packaging, model_deployment, model_monitoring, retrain_management |
| Quality Engineer | `/quality-engineer` | テスト、静的解析、コードレビュー | 全Capability |
| Data Scientist | `/data-scientist` | 分析、特徴量エンジニアリング | data_preparation, workflow_optimization |
| DevOps Engineer | `/devops-engineer` | GitHub連携、ワークフロー、通知 | github_integration, notification, history_management |

### スキル構造

```text
.claude/skills/
├── data-engineer/SKILL.md
├── ml-engineer/SKILL.md
├── mlops-engineer/SKILL.md
├── quality-engineer/SKILL.md
├── data-scientist/SKILL.md
└── devops-engineer/SKILL.md
```

### 使用例

```bash
# 明示的に呼び出し（引数付き）
/data-engineer data_preparation Capabilityのデータ検証機能を実装して

# 明示的に呼び出し（引数なし）
/mlops-engineer

# 自動呼び出し: Claudeが作業内容からスキルを判断
# 例: 「テストを作成して」→ quality-engineer スキルが自動選択
```
