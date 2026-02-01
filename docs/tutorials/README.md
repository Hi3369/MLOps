# MLOps チュートリアル

## チュートリアル一覧

| # | チュートリアル | 対象者 | 内容 |
|---|-------------|--------|------|
| 1 | [クイックスタート](quickstart.md) | 全員 | 初回セットアップと基本的なパイプライン実行 |
| 2 | [学習パイプライン](training-pipeline.md) | Data Scientist / ML Engineer | データ準備→学習→評価→レジストリの完全フロー |
| 3 | [監視・運用](monitoring-operations.md) | MLOps Engineer | デプロイ→監視→ドリフト検出→再学習 |

## 前提条件

- Python 3.12+
- AWS アカウント（本番環境利用時）
- 本リポジトリのクローン

## 環境セットアップ

```bash
# リポジトリクローン
git clone <repository-url>
cd MLOps

# 仮想環境作成・依存関係インストール
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 開発環境設定（AWSサービス不要）
export MLOPS_ENV=development
```
