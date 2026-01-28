# MLOps開発 次のステップ

## 現在の状態

**ステータス**: 基盤実装完了

| 項目 | 状況 |
|------|------|
| 12 Capabilities | 全て実装完了 |
| テストケース | 約448件 |
| 専門家レビュー | 完了（876d153） |
| セキュリティ修正 | 完了 |
| 依存関係管理 | pyproject.toml完備 |

---

## 次のステップ（優先度順）

### Phase 1: モデル解釈性機能（優先度: 高）

**目的**: レビューで指摘されたSHAP/LIME機能の実装

#### 1.1 SHAP値計算ツール
- **ファイル**: `mcp_server/capabilities/ml_evaluation/tools/calculate_shap_values.py`
- **機能**:
  - TreeExplainer（決定木・アンサンブル用）
  - KernelExplainer（汎用）
  - DeepExplainer（ニューラルネット用）
- **テスト**: 30件以上

#### 1.2 LIME説明ツール
- **ファイル**: `mcp_server/capabilities/ml_evaluation/tools/calculate_lime_explanation.py`
- **機能**:
  - タビュラーデータ対応
  - 局所的解釈可能性分析
- **テスト**: 20件以上

#### 1.3 設計書更新
- `docs/designs/mcp_design.md` のCapability 5セクションを詳細化

---

### Phase 2: 統合テスト強化（優先度: 高）

**目的**: エンドツーエンドの品質保証

#### 2.1 追加すべきテストファイル
```
tests/integration/
├── test_end_to_end_pipeline.py    # フルパイプラインテスト
├── test_capability_dependencies.py # Capability間依存テスト
└── test_aws_integration.py         # AWS統合テスト（LocalStack）
```

#### 2.2 カバレッジ目標
- 現在: 約70%（推定）
- 目標: 80%以上
- コマンド: `pytest --cov --cov-report=html`

---

### Phase 3: エクスペリメント追跡（優先度: 中）

**目的**: 実験管理の自動化

#### 3.1 新規Capability: experiment_tracking
- **ツール**:
  - `start_experiment`: 実験開始
  - `log_parameters`: パラメータ記録
  - `log_metrics`: メトリクス記録
  - `compare_experiments`: 実験比較

#### 3.2 統合候補
- MLflow
- Weights & Biases
- SageMaker Experiments

---

### Phase 4: データバージョニング（優先度: 中）

**目的**: データ系譜の追跡

#### 4.1 新規Capability: data_versioning
- **ツール**:
  - `version_dataset`: データセットバージョン登録
  - `get_dataset_lineage`: データ系譜取得
  - `compare_datasets`: データセット比較

#### 4.2 統合候補
- DVC (Data Version Control)
- Delta Lake

---

### Phase 5: ドキュメント拡充（優先度: 低）

#### 5.1 追加すべきドキュメント
- `docs/api/` - API仕様書（OpenAPI形式）
- `docs/tutorials/` - チュートリアル
- `docs/troubleshooting.md` - トラブルシューティング

---

## 実装ファイル一覧

### Phase 1で作成するファイル

| ファイル | 説明 |
|---------|------|
| `mcp_server/capabilities/ml_evaluation/tools/calculate_shap_values.py` | SHAP値計算 |
| `mcp_server/capabilities/ml_evaluation/tools/calculate_lime_explanation.py` | LIME説明 |
| `tests/unit/test_shap_lime.py` | SHAP/LIMEテスト |

### Phase 2で作成するファイル

| ファイル | 説明 |
|---------|------|
| `tests/integration/test_end_to_end_pipeline.py` | E2Eテスト |
| `tests/integration/test_capability_dependencies.py` | 依存テスト |
| `tests/integration/test_aws_integration.py` | AWS統合テスト |

---

## 検証コマンド

```bash
# テスト実行
pytest tests/ -v --cov

# Lint
flake8 mcp_server/ tests/ --max-line-length=100

# セキュリティチェック
bandit -r mcp_server/ -c pyproject.toml

# 型チェック
mypy mcp_server/ --ignore-missing-imports
```

---

## 推奨スケジュール

| Phase | 内容 | 期間目安 |
|-------|------|---------|
| Phase 1 | SHAP/LIME実装 | 1-2週間 |
| Phase 2 | 統合テスト強化 | 1週間 |
| Phase 3 | エクスペリメント追跡 | 2週間 |
| Phase 4 | データバージョニング | 1週間 |
| Phase 5 | ドキュメント拡充 | 継続的 |

---

## 関連ドキュメント

- [設計書](../designs/mcp_design.md)
- [実装ガイド](../designs/implementation_guide.md)
- [IAM権限](../designs/iam_permissions.md)
- [専門家レビュー結果](../reviews/876d153/)
