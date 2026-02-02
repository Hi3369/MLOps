# MLOps開発 次のステップ

## 現在の状態

**ステータス**: Phase 1-5 完了、安定化・本番準備フェーズ

| 項目 | 状況 |
|------|------|
| 14 Capabilities | 全て実装完了（60ツール） |
| テストケース | 599件パス / 1件要修正 |
| テストカバレッジ | 72.5% |
| 専門家レビュー | 完了（876d153） |
| セキュリティ修正 | 完了 |
| ドキュメント | API仕様書・チュートリアル・トラブルシューティング完備 |
| markdownlint | 全ファイル0エラー |

### 完了済みPhase

| Phase | 内容 | コミット |
|-------|------|---------|
| Phase 1 | SHAP/LIME モデル解釈性 | `0f1d08e` |
| Phase 2 | 統合テスト強化（E2E, 依存, AWS） | 統合テスト3ファイル |
| Phase 3 | エクスペリメント追跡 | `d8f66b4` |
| Phase 4 | データバージョニング | `9960785` |
| Phase 5 | ドキュメント拡充 | `6e74d86` |

---

## 次のステップ（優先度順）

### Phase 6: テスト修正・カバレッジ向上（優先度: 高）

**目的**: 既知の不具合修正とカバレッジ80%達成

#### 6.1 失敗テスト修正

- **ファイル**: `tests/integration/test_mcp_server.py::test_server_extensibility`
- **原因**: Capability数が10→12、ツール数が53→60に増加したがテスト期待値が未更新
- **対処**: アサーション値を更新

#### 6.2 カバレッジ向上（72.5% → 80%+）

低カバレッジモジュールを重点的にテスト追加:

| モジュール | 現在カバレッジ | 目標 |
|-----------|--------------|------|
| notification | 49% | 80% |
| workflow_optimization | 56% | 80% |
| retrain_management | 要確認 | 80% |
| common/s3_utils | 要確認 | 80% |

#### 6.3 TODO項目の解消

- `mcp_server/common/s3_utils.py` のTODOコメント
- `docs/specifications/system_specification.md` のTODO

---

### Phase 7: コード品質強化（優先度: 高）

**目的**: 静的解析・型チェックの完全パス

#### 7.1 flake8

```bash
flake8 mcp_server/ tests/ --max-line-length=100
```

#### 7.2 mypy型チェック

```bash
mypy mcp_server/ --ignore-missing-imports
```

#### 7.3 banditセキュリティチェック

```bash
bandit -r mcp_server/ -c pyproject.toml
```

#### 7.4 isort/blackフォーマット確認

```bash
isort --check-only --profile black mcp_server/ tests/
black --check mcp_server/ tests/
```

---

### Phase 8: CI/CD パイプライン構築（優先度: 中）

**目的**: GitHub Actionsによる自動品質保証

#### 8.1 GitHub Actions ワークフロー

- **ファイル**: `.github/workflows/ci.yml`
- **トリガー**: push, pull_request
- **ジョブ**:
  - lint: flake8, mypy, bandit, markdownlint
  - test: pytest with coverage
  - coverage-gate: 80%未満で失敗

#### 8.2 Pre-commit hooks

- **ファイル**: `.pre-commit-config.yaml`
- **フック**: black, isort, flake8, mypy

#### 8.3 PR テンプレート

- **ファイル**: `.github/pull_request_template.md`

---

### Phase 9: 本番デプロイ準備（優先度: 中）

**目的**: 本番AWS環境でのデプロイ準備

#### 9.1 CDK スタック整備

- `cdk/` ディレクトリの既存コードを確認・更新
- S3バケット、SageMaker、Step Functions等のリソース定義

#### 9.2 環境設定

- 本番用 `.env.production` テンプレート
- IAM ロール・ポリシーの最終確認
- VPC・セキュリティグループ設計

#### 9.3 負荷テスト

- 同時学習ジョブの負荷テスト
- エンドポイント推論のレイテンシテスト

---

### Phase 10: 運用機能強化（優先度: 低）

**目的**: 本番運用時の利便性向上

#### 10.1 ダッシュボード

- CloudWatch ダッシュボードテンプレート
- モデルパフォーマンス可視化

#### 10.2 外部ツール連携

- MLflow / Weights & Biases 統合
- DVC (Data Version Control) 統合

#### 10.3 マルチリージョン対応

- クロスリージョンレプリケーション
- DR（災害復旧）計画

---

## 検証コマンド

```bash
# テスト実行（カバレッジ付き）
pytest tests/ -v --cov=mcp_server --cov-report=html

# Lint
flake8 mcp_server/ tests/ --max-line-length=100

# 型チェック
mypy mcp_server/ --ignore-missing-imports

# セキュリティチェック
bandit -r mcp_server/ -c pyproject.toml

# フォーマット確認
black --check mcp_server/ tests/
isort --check-only --profile black mcp_server/ tests/

# Markdownlint
npx markdownlint-cli2 "**/*.md" "#node_modules" "#.venv" "#venv"
```

---

## 関連ドキュメント

- [設計書](../designs/mcp_design.md)
- [実装ガイド](../designs/implementation_guide.md)
- [IAM権限](../designs/iam_permissions.md)
- [API仕様書](../api/README.md)
- [チュートリアル - 学習パイプライン](../tutorials/training-pipeline.md)
- [チュートリアル - 監視・運用](../tutorials/monitoring-operations.md)
- [トラブルシューティング](../troubleshooting.md)
- [専門家レビュー結果](../reviews/876d153/)
