# トラブルシューティング

MLOps MCP Serverの運用で発生しうる問題と解決策。

---

## 1. サーバー起動

### Capability が登録されない

**症状**: `MLOpsServer()` 初期化時に特定の Capability が `capabilities` に含まれない。

**原因**: ImportError が発生している（依存パッケージ不足、構文エラー等）。

**対処**:

```python
import logging
logging.basicConfig(level=logging.WARNING)

from mcp_server.server import MLOpsServer
server = MLOpsServer()
# => WARNING が出力される場合、該当 Capability の import に失敗している
```

**確認**:

```python
info = server.get_server_info()
print(f"登録済み: {info['capabilities']}")
print(f"ツール数: {info['total_tools']}")
```

---

## 2. AWS接続

### 開発環境で AWS エラーが出る

**症状**: `botocore.exceptions.NoCredentialsError` が発生する。

**原因**: `MLOPS_ENV` が設定されていない（デフォルトは `development` だが、一部のコードパスで未チェック）。

**対処**:

```bash
export MLOPS_ENV=development
```

### 本番環境で権限エラー

**症状**: `botocore.exceptions.ClientError: AccessDenied`

**対処**:

1. IAM ポリシーを確認: `docs/designs/iam_permissions.md`
2. 必要な権限が付与されているか確認
3. STS で一時認証を使用している場合、有効期限を確認

---

## 3. データ準備

### S3 URI のバリデーションエラー

**症状**: `ValueError: s3_uri must start with 's3://'`

**対処**: URI が `s3://` で始まることを確認。

```python
# 正しい
"s3://my-bucket/data/train.csv"

# 誤り
"https://s3.amazonaws.com/my-bucket/data/train.csv"
"/local/path/train.csv"
```

### 前処理でカラムが見つからない

**症状**: `target_column` が存在しないエラー。

**対処**: `validate_data` で事前にカラムを確認する。

```python
result = server.call_tool(
    "data_preparation.validate_data",
    {"s3_uri": "s3://bucket/data.csv", "required_columns": ["target"]}
)
```

---

## 4. モデル学習

### 未サポートのアルゴリズム

**症状**: `ValueError: Unsupported algorithm`

**対処**: 各タスクタイプでサポートされるアルゴリズムを使用する。

| タスク | サポートアルゴリズム |
|--------|-------------------|
| 分類 | `random_forest`, `logistic_regression`, `neural_network` |
| 回帰 | `random_forest`, `linear_regression`, `ridge` |
| クラスタリング | `kmeans`, `dbscan` |

---

## 5. デプロイ

### エンドポイント作成が失敗する

**症状**: `deploy_to_sagemaker` がエラーを返す。

**確認事項**:

1. モデルの S3 URI が正しいか
2. インスタンスタイプが有効か（`ml.t3.medium` 等）
3. SageMaker のサービスクォータに達していないか

### ロールバックが失敗する

**症状**: `rollback_deployment` で `previous_config_name` が見つからない。

**対処**: 明示的に前回の設定名を指定する。

```python
server.call_tool(
    "model_deployment.rollback_deployment",
    {
        "endpoint_name": "my-endpoint",
        "previous_config_name": "my-endpoint-config-20260131",
    }
)
```

---

## 6. 監視

### ドリフト検出の誤検知

**症状**: `detect_data_drift` が常に drift_detected=True を返す。

**対処**:

1. `drift_threshold` を調整（デフォルト: 0.05）
2. ベースラインデータのサンプルサイズを増やす
3. 外れ値を除外してから検定を実行

```python
# 閾値を緩和
result = server.call_tool(
    "model_monitoring.detect_data_drift",
    {
        "baseline_data": baseline,
        "current_data": current,
        "drift_threshold": 0.01,  # より厳密な閾値
    }
)
```

### アラームが発火しない

**確認事項**:

1. `actions_enabled` が `True` か
2. `evaluation_periods` と `period_seconds` の設定が適切か
3. CloudWatch にメトリクスデータが送信されているか

---

## 7. 実験追跡

### 実験名のバリデーションエラー

**症状**: `ValueError: experiment_name must contain only alphanumeric characters, hyphens, underscores, and dots`

**対処**: 実験名には英数字・ハイフン・アンダースコア・ドットのみ使用可能（256文字以内）。

```python
# 正しい
"iris-classification-v1.0"
"my_experiment_2026"

# 誤り
"my experiment"     # スペース不可
"実験1"             # 日本語不可
```

---

## 8. データバージョニング

### フィンガープリントの不一致

**症状**: 同じデータなのにフィンガープリントが異なる。

**原因**: フィンガープリントは `dataset_name + s3_uri + version` から生成される。いずれかが異なると別のフィンガープリントになる。

### バージョン比較で同一バージョン指定エラー

**症状**: `ValueError: version_a and version_b must be different`

**対処**: 比較には必ず異なるバージョンを指定する。

---

## 9. テスト実行

### テスト環境のセットアップ

```bash
# 依存関係インストール
pip install -e ".[dev]"

# 全テスト実行
pytest tests/ -v

# 特定 Capability のテスト
pytest tests/unit/test_data_versioning.py -v

# 統合テスト
pytest tests/integration/ -v
```

### モック環境でテストが失敗する

**確認事項**:

1. `MLOPS_ENV` が `test` または `development` か
2. `unittest.mock` で適切にパッチしているか
3. boto3 クライアントのモックが正しいか

---

## 10. よくある質問

### Q: 開発環境でAWSアカウントは必要？

A: 不要です。`MLOPS_ENV=development`（デフォルト）ではモックデータが返されます。

### Q: 新しいCapabilityを追加するには？

A: 以下の手順に従います:

1. `mcp_server/capabilities/<name>/` にディレクトリ作成
2. `capability.py` で Dict-based パターンを実装
3. `tools/` にツール関数を配置
4. `mcp_server/server.py` の `_register_capabilities()` に登録
5. テストを `tests/unit/test_<name>.py` に作成

詳細は `CLAUDE.md` の「Capability実装パターン」を参照。

### Q: テストのカバレッジ目標は？

A: 各Capabilityに30件以上のテストケース、全体カバレッジ80%以上を目標としています。
