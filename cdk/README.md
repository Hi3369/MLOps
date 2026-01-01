# MLOps Infrastructure CDK

AWS CDK を使用した MLOps インフラストラクチャの定義

## 前提条件

- Python 3.12+
- AWS CLI configured
- AWS CDK CLI installed (`npm install -g aws-cdk`)

## セットアップ

```bash
# CDK ディレクトリに移動
cd cdk

# 仮想環境の作成
python3 -m venv .venv

# 仮想環境のアクティベート
source .venv/bin/activate  # Linux/Mac
# または
.venv\Scripts\activate.bat  # Windows

# 依存関係のインストール
pip install -r requirements.txt
```

## デプロイ

### Judge Agent Stack のデプロイ

```bash
# CDK Bootstrap（初回のみ）
cdk bootstrap

# スタックの確認
cdk list

# 変更内容の確認
cdk diff JudgeAgentStack

# デプロイ実行
cdk deploy JudgeAgentStack

# 全スタック一括デプロイ
cdk deploy --all
```

## スタック構成

### JudgeAgentStack

モデル評価結果の判定と次アクション決定を行う Judge Agent

**リソース:**
- Lambda 関数: `mlops-judge-agent`
  - Runtime: Python 3.12
  - Memory: 256 MB
  - Timeout: 60 seconds
  - Log Retention: 1 month

**権限:**
- S3 読み取り: `s3://mlops-bucket/evaluations/*`
- CloudWatch Metrics 書き込み: `MLOps/JudgeAgent` namespace
- CloudWatch Logs 書き込み

## 開発

### スタックの追加

新しいスタックを追加する場合:

1. `stacks/` ディレクトリに新しいスタッククラスを作成
2. `stacks/__init__.py` に追加
3. `app.py` でインスタンス化

### スタックのテスト

```bash
# CDK の合成（CloudFormation テンプレート生成）
cdk synth JudgeAgentStack

# 生成されたテンプレートの確認
cat cdk.out/JudgeAgentStack.template.json
```

### クリーンアップ

```bash
# スタックの削除
cdk destroy JudgeAgentStack

# 全スタック削除
cdk destroy --all
```

## トラブルシューティング

### Bootstrap が必要なエラー

```
This stack uses assets, so the toolkit stack must be deployed to the environment
```

**解決策:**
```bash
cdk bootstrap aws://ACCOUNT-ID/REGION
```

### Lambda パッケージが大きすぎるエラー

Judge Agent の依存関係が大きい場合は、Lambda Layer の使用を検討してください。

### IAM 権限エラー

デプロイには適切な AWS 権限が必要です:
- CloudFormation スタック作成/更新/削除
- Lambda 関数作成/更新
- IAM ロール作成
- CloudWatch Logs 作成

## 参考資料

- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [AWS CDK Python API Reference](https://docs.aws.amazon.com/cdk/api/v2/python/)
