# MLOps Integrated MCP Server

統合MLOps MCPサーバーは、MLOpsパイプラインの全専門機能を単一のMCPサーバーとして提供します。

## 概要

このMCPサーバーは、以下の12個のCapabilityを統合し、Claude Desktop/Claude APIから利用可能にします:

1. **GitHub Integration** - GitHub Issue検知・パース・ワークフロー起動
2. **Workflow Optimization** - モデル特性分析・最適化提案
3. **Data Preparation** - データ前処理・特徴量エンジニアリング（Phase 1実装済み）
4. **ML Training** - モデル学習（教師あり/教師なし/強化学習）
5. **ML Evaluation** - モデル評価・メトリクス計算・可視化
6. **Model Packaging** - モデルコンテナ化・ECR登録
7. **Model Deployment** - モデルデプロイ・エンドポイント管理
8. **Model Monitoring** - パフォーマンス監視・ドリフト検出
9. **Retrain Management** - 再学習トリガー判定・ワークフロー起動
10. **Notification** - 通知管理（Slack/Email/GitHub）
11. **History Management** - 学習履歴記録・GitHub連携
12. **Model Registry** - モデル登録・バージョン管理

### Phase 1 Week 1-2 実装範囲

現在実装されているのは:
- MCPサーバーの基本構造
- Data Preparation Capability（骨格のみ）
  - `load_dataset`: S3からデータセット読み込み
  - `validate_data`: データバリデーション
  - `preprocess_supervised`: 教師あり学習用前処理

## ディレクトリ構造

```
mcp_server/
├── __init__.py              # パッケージ初期化
├── __main__.py              # エントリーポイント
├── server.py                # MLOpsServer本体
├── common/                  # 共通ユーティリティ
│   ├── __init__.py
│   ├── logger.py            # ロギング設定
│   ├── s3_utils.py          # S3操作（Phase 1ではstub）
│   └── config.py            # 設定管理
└── capabilities/            # Capability実装
    └── data_preparation/    # Data Preparation Capability
        ├── __init__.py
        ├── capability.py    # Capability本体
        └── tools/           # ツール実装
            ├── __init__.py
            ├── load_dataset.py
            ├── validate_data.py
            └── preprocess_supervised.py
```

## セットアップ

### 必要要件

- Python 3.10以上
- AWS認証情報（S3アクセス用、Phase 2以降）

### インストール

```bash
# 依存パッケージのインストール
pip install -r requirements.txt

# 開発環境の場合
pip install -r requirements.txt
```

### 環境変数

```bash
# ログレベル
export LOG_LEVEL=INFO

# AWS設定（Phase 2以降で使用）
export MLOPS_S3_BUCKET=your-mlops-bucket
export AWS_REGION=us-west-2
```

## 使用方法

### サーバーの起動

```bash
# モジュールとして実行
python -m mcp_server

# または
python mcp_server/__main__.py
```

### ツールの利用

Phase 1では骨格実装のため、各ツールはダミーデータを返します。

```python
from mcp_server import MLOpsServer

# サーバー初期化
server = MLOpsServer()

# 利用可能なツールのリスト取得
tools = server.list_tools()

# ツールの実行
result = server.call_tool(
    "data_preparation.load_dataset",
    {"bucket": "my-bucket", "key": "data/train.csv"}
)
```

## 開発

### コード品質チェック

```bash
# フォーマット
black mcp_server/
isort mcp_server/

# リント
flake8 mcp_server/

# 型チェック
mypy mcp_server/
```

### テスト

```bash
# テスト実行
pytest

# カバレッジ付き
pytest --cov=mcp_server
```

## Phase 1 実装状況

- [x] MCPサーバー基本構造
- [x] 共通ユーティリティ（logger, config, s3_utils stub）
- [x] Data Preparation Capability骨格
  - [x] load_dataset (stub)
  - [x] validate_data (stub)
  - [x] preprocess_supervised (stub)
- [ ] Phase 2: 実際のS3連携実装
- [ ] Phase 2: データ処理ロジック実装
- [ ] Phase 3+: 他のCapability実装

## アーキテクチャ

### Unified MCP Server方式

単一のMCPサーバーが複数のCapabilityをホストし、ツール名を`{capability}.{tool}`形式で提供します。

**利点:**
- 単一プロセスで全機能を管理
- Capability間のコード共有が容易
- 統一されたログ・監視
- デプロイ・運用がシンプル

### Tool Naming Convention

```
{capability_name}.{tool_name}

例:
- data_preparation.load_dataset
- ml_training.train_supervised
- model_registry.register_model
```

## ライセンス

内部プロジェクト用
