# MCP化設計書: MLOps専門機能のModel Context Protocol対応

## 1. MCP化の目的

### 1.1 現状の課題

現在の設計では、データ前処理・モデル学習・モデル評価などの専門機能がAWS Lambda/ECS Fargateに直接実装されており、以下の課題があります:

- **再利用性の欠如**: 各エージェントに機能が埋め込まれており、他プロジェクトで再利用できない
- **保守性の低下**: 新しいアルゴリズムや評価指標の追加時にLambda/ECSコードを修正する必要がある
- **テストの困難さ**: AWS環境依存のテストになり、ローカル開発が困難
- **ベンダーロックイン**: AWS特化の実装で、他クラウドへの移行が困難

### 1.2 MCP化のメリット

Model Context Protocol (MCP) として専門機能を実装することで:

- ✅ **再利用性向上**: 標準プロトコルに準拠し、他プロジェクトでも利用可能
- ✅ **保守性向上**: MCPサーバーとして独立しており、機能追加・変更が容易
- ✅ **テスト容易性**: ローカル環境で単体テスト可能
- ✅ **拡張性向上**: 新しいツール（アルゴリズム、評価指標）を容易に追加可能
- ✅ **ベンダーニュートラル**: クラウドプロバイダーに依存しない設計
- ✅ **標準化**: MCPという業界標準プロトコルに準拠

---

## 2. MCP化対象コンポーネント

### 2.1 統合MCPサーバーアプローチ

システムの主要機能を**1つの統合MLOps MCPサーバー**として実装します。各機能領域は独立した**capability（機能群）**として提供され、運用の簡素化とリソース効率を実現します。

#### 統合MLOps MCP Server

**責務**: MLOpsパイプラインの全専門機能を統合提供

**アーキテクチャ上のメリット**:

- ✅ **運用の簡素化**: 1つのサーバープロセスのみ管理
- ✅ **デプロイの簡素化**: 1つのコンテナ/Lambdaのみデプロイ
- ✅ **リソース効率**: メモリ・CPUを共有、オーバーヘッド削減
- ✅ **MCP接続の削減**: 1つのMCP接続で全ツールにアクセス可能
- ✅ **一貫性の向上**: バージョン管理・依存関係が統一
- ✅ **開発効率**: 共通ユーティリティ・設定の再利用

### 2.2 提供Capability（11個の機能群）

統合MCPサーバーは、以下の**11個のcapability**を提供します（各MCPエージェントと1対1対応）:

#### Capability 1: GitHub Integration

**対応エージェント**: Issue Detector Agent

**責務**: GitHub Issue検知・パース・ワークフロー起動

**提供ツール**:

- `detect_mlops_issue`: MLOps用Issueの検知
- `parse_issue_config`: Issue本文のYAML/JSON設定パース
- `validate_training_params`: 学習パラメータのバリデーション
- `start_workflow`: Step Functionsワークフローの起動

#### Capability 2: Workflow Optimization

**対応エージェント**: Workflow Optimizer Agent

**責務**: モデル特性分析・最適化提案・履歴ベース最適化

**提供ツール**:

- `analyze_model_characteristics`: モデル特性分析（データサイズ、アルゴリズム等）
- `generate_optimization_proposal`: 最適化提案生成
- `retrieve_similar_model_history`: 類似モデルの履歴取得
- `apply_optimizations`: 最適化の適用
- `track_optimization_history`: 最適化履歴の記録

#### Capability 3: Data Preparation

**対応エージェント**: Data Preparation Agent

**責務**: データ前処理・特徴量エンジニアリング

**提供ツール**:

- `load_dataset`: S3からデータセット読み込み
- `validate_data`: データバリデーション（欠損値、型チェック等）
- `preprocess_supervised`: 教師あり学習用前処理
- `preprocess_unsupervised`: 教師なし学習用前処理
- `preprocess_reinforcement`: 強化学習用前処理
- `feature_engineering`: 特徴量エンジニアリング
- `split_dataset`: データセット分割（train/validation/test）
- `apply_class_imbalance_handling`: クラス不均衡対策

#### Capability 4: Model Training

**対応エージェント**: Training Agent

**責務**: 機械学習モデルの学習・ハイパーパラメータ最適化

**提供ツール**:

- `create_training_job`: SageMaker学習ジョブ作成
- `train_supervised_classifier`: 教師あり学習（分類）
- `train_supervised_regressor`: 教師あり学習（回帰）
- `train_unsupervised_clustering`: 教師なし学習（クラスタリング）
- `train_unsupervised_dimensionality_reduction`: 次元削減
- `train_reinforcement`: 強化学習（PPO/DQN/A3C）
- `hyperparameter_optimization`: ハイパーパラメータ最適化（Grid/Random/Bayesian）
- `monitor_training_progress`: 学習進捗モニタリング
- `get_training_results`: 学習結果取得

#### Capability 5: Model Evaluation

**対応エージェント**: Evaluation Agent

**責務**: モデル評価・メトリクス計算・可視化・バイアス検出

**提供ツール**:

- `evaluate_classifier`: 分類モデル評価（Accuracy, Precision, Recall, F1, AUC-ROC）
- `evaluate_regressor`: 回帰モデル評価（RMSE, MAE, R², MAPE）
- `evaluate_clustering`: クラスタリング評価（Silhouette Score, Davies-Bouldin Index）
- `evaluate_reinforcement`: 強化学習評価（Episode Reward, Success Rate）
- `generate_confusion_matrix`: 混同行列生成
- `generate_roc_curve`: ROC曲線生成
- `calculate_shap_values`: SHAP値計算（モデル解釈性）
- `bias_check`: バイアス検出（SageMaker Clarify）
- `compare_models`: 複数モデル比較
- `create_evaluation_report`: 評価レポート生成

#### Capability 6: Model Packaging

**対応エージェント**: Packaging Agent

**責務**: モデルコンテナ化・ECR登録・最適化

**提供ツール**:

- `build_docker_image`: Dockerイメージビルド
- `push_to_ecr`: ECRへのプッシュ
- `create_model_package`: SageMakerモデルパッケージ作成
- `generate_api_spec`: 推論APIスペック生成
- `optimize_container`: コンテナ最適化（マルチステージビルド、ONNX変換等）

#### Capability 7: Model Deployment

**対応エージェント**: Deployment Agent

**責務**: モデルデプロイ・エンドポイント管理・トラフィック制御

**提供ツール**:

- `deploy_model_to_endpoint`: SageMakerエンドポイントへデプロイ
- `update_endpoint_traffic`: トラフィック配分更新（カナリアデプロイ）
- `configure_auto_scaling`: オートスケーリング設定
- `health_check_endpoint`: エンドポイントヘルスチェック
- `rollback_deployment`: デプロイメントロールバック

#### Capability 8: Model Monitoring

**対応エージェント**: Monitor Agent

**責務**: モデルパフォーマンス監視・ドリフト検出・アラート

**提供ツール**:

- `collect_system_metrics`: システムメトリクス収集（CPU/Memory/Latency）
- `collect_model_metrics`: モデルメトリクス収集（精度、予測分布等）
- `detect_data_drift`: データドリフト検出
- `detect_concept_drift`: コンセプトドリフト検出
- `trigger_cloudwatch_alarms`: CloudWatchアラーム発火
- `update_dashboard`: ダッシュボード更新

#### Capability 9: Retrain Management

**対応エージェント**: Retrain Agent

**責務**: 再学習トリガー判定・再学習ワークフロー起動

**提供ツール**:

- `check_retrain_triggers`: 再学習トリガー確認
- `evaluate_trigger_conditions`: トリガー条件評価（ドリフト閾値、スケジュール等）
- `create_retrain_issue`: 再学習Issue作成
- `start_retrain_workflow`: 再学習ワークフロー起動
- `schedule_periodic_retrain`: 定期再学習スケジュール設定

#### Capability 10: Notification

**対応エージェント**: Notification Agent

**責務**: 外部通知チャネル統合（Slack/Email/GitHub）

**提供ツール**:

- `send_slack_notification`: Slack通知送信
- `send_email_notification`: Email通知送信
- `send_github_notification`: GitHub Issue/PR通知
- `apply_notification_template`: 通知テンプレート適用

#### Capability 11: History Management

**対応エージェント**: History Writer Agent

**責務**: 学習履歴記録・GitHub履歴管理・バージョン追跡

**提供ツール**:

- `format_training_history`: 学習履歴フォーマット
- `commit_to_github`: GitHubリポジトリへコミット
- `post_issue_comment`: Issue進捗コメント投稿
- `track_version_history`: バージョン履歴追跡

### 2.3 Capability構成の設計方針

**11個のCapabilityに分割した理由**:

1. **責務の明確化**: 各Capabilityは単一の明確な責務を持つ（単一責任の原則）
2. **エージェントとの1対1対応**: MCP化された各エージェントに対応
3. **独立性**: 各Capabilityは独立してテスト・デプロイ・スケール可能
4. **保守性**: 機能追加・変更が該当Capabilityのみで完結

**統合MCPサーバーの主要メリット**:

- 🎯 **運用の簡素化**: 1つのサーバープロセス/コンテナのみ管理
- 🎯 **デプロイの簡素化**: 1つのデプロイパイプラインで完結
- 🎯 **リソース効率**: メモリ・CPUを共有、オーバーヘッド削減
- 🎯 **MCP接続の最小化**: 1つのMCP接続で全ツールにアクセス

### 2.4 将来の拡張候補

統合MCPサーバーには、将来的に以下のcapabilityを追加可能です:

**Capability 12: Experiment Tracking** 💡

- MLflow、Weights & Biases等の実験追跡ツール統合
- ハイパーパラメータチューニング履歴管理

**Capability 13: Data Versioning** 💡

- DVC、Delta Lake等のデータバージョニングツール統合
- データ系譜追跡、データ品質モニタリング

詳細は本ドキュメントのセクション15を参照

---

## 3. アーキテクチャ設計

### 3.1 システムアーキテクチャ（統合MLOps MCPサーバー）

```mermaid
graph TB
    subgraph "GitHub"
        GH_ISSUE[GitHub Issue]
    end

    subgraph "External Services"
        SLACK[Slack]
        EMAIL[Email/SES]
        TEAMS[Microsoft Teams]
        DISCORD[Discord]
    end

    subgraph "AWS Cloud"
        subgraph "API Gateway + Lambda"
            ISSUE_DETECTOR[Issue Detector Agent<br/>MCP Client]
        end

        subgraph "Step Functions Workflow"
            SF[Step Functions State Machine]
        end

        subgraph "Lambda Agents (MCP Clients)"
            DATA_PREP[Data Preparation Agent<br/>MCP Client]
            TRAINING[Training Agent<br/>MCP Client]
            EVALUATION[Evaluation Agent<br/>MCP Client]
            JUDGE[Judge Agent]
            NOTIFICATION[Notification Agent<br/>MCP Client]
            ROLLBACK[Rollback Agent<br/>MCP Client]
            HISTORY[History Writer Agent<br/>MCP Client]
        end

        subgraph "Unified MLOps MCP Server"
            MCP_SERVER[統合MLOps MCP Server<br/>ECS Fargate / Lambda]

            subgraph "11 Capabilities"
                CAP1[1. GitHub Integration]
                CAP2[2. Workflow Optimization]
                CAP3[3. Data Preparation]
                CAP4[4. Model Training]
                CAP5[5. Model Evaluation]
                CAP6[6. Model Packaging]
                CAP7[7. Model Deployment]
                CAP8[8. Model Monitoring]
                CAP9[9. Retrain Management]
                CAP10[10. Notification]
                CAP11[11. History Management]
            end
        end

        subgraph "Storage & External APIs"
            S3[S3 Bucket]
            SAGEMAKER_REGISTRY[SageMaker Model Registry]
        end
    end

    GH_ISSUE -->|Webhook| ISSUE_DETECTOR
    ISSUE_DETECTOR -->|MCP| MCP_SERVER
    ISSUE_DETECTOR --> SF

    SF --> DATA_PREP
    SF --> TRAINING
    SF --> EVALUATION
    SF --> JUDGE
    SF --> NOTIFICATION
    SF --> ROLLBACK
    SF --> HISTORY

    DATA_PREP -->|MCP| MCP_SERVER
    TRAINING -->|MCP| MCP_SERVER
    EVALUATION -->|MCP| MCP_SERVER
    NOTIFICATION -->|MCP| MCP_SERVER
    ROLLBACK -->|MCP| MCP_SERVER
    HISTORY -->|MCP| MCP_SERVER

    MCP_SERVER -->|Capability 3,4| S3
    MCP_SERVER -->|Capability 4,5| SAGEMAKER_REGISTRY
    MCP_SERVER -->|Capability 1,11| GH_ISSUE
    MCP_SERVER -->|Capability 10| SLACK
    MCP_SERVER -->|Capability 10| EMAIL
    MCP_SERVER -->|Capability 10| TEAMS
    MCP_SERVER -->|Capability 10| DISCORD
```

### 3.2 エージェント・統合MCPサーバー連携フロー

```mermaid
sequenceDiagram
    participant SF as Step Functions
    participant Agent as Lambda Agent<br/>(MCP Client)
    participant MCP as 統合MLOps MCP Server<br/>(ECS/Lambda)
    participant S3 as S3 Storage

    SF->>Agent: タスク実行指示
    Agent->>MCP: MCP Request<br/>(JSON-RPC over stdio/SSE)
    Note over MCP: 適切なCapabilityに<br/>リクエストをルーティング
    MCP->>S3: データ取得
    S3-->>MCP: データ返却
    MCP->>MCP: 処理実行<br/>(前処理/学習/評価)
    MCP->>S3: 結果保存
    MCP-->>Agent: MCP Response<br/>(結果データ)
    Agent-->>SF: タスク完了
```

---

## 4. 統合MCPサーバー詳細設計

### 4.1 Capability 1: Data Preparation

#### ツール定義例

**ツール名**: `preprocess_supervised`

**入力スキーマ**:

```json
{
  "name": "preprocess_supervised",
  "description": "教師あり学習用のデータ前処理を実行",
  "inputSchema": {
    "type": "object",
    "properties": {
      "dataset_s3_uri": {
        "type": "string",
        "description": "S3上の生データのURI"
      },
      "target_column": {
        "type": "string",
        "description": "目的変数のカラム名"
      },
      "task_type": {
        "type": "string",
        "enum": ["classification", "regression"],
        "description": "タスクタイプ"
      },
      "preprocessing_config": {
        "type": "object",
        "properties": {
          "normalize": {"type": "boolean"},
          "handle_missing": {"type": "string", "enum": ["drop", "mean", "median", "mode"]},
          "encode_categorical": {"type": "boolean"}
        }
      }
    },
    "required": ["dataset_s3_uri", "target_column", "task_type"]
  }
}
```

**出力例**:

```json
{
  "content": [
    {
      "type": "text",
      "text": "データ前処理が完了しました"
    },
    {
      "type": "resource",
      "resource": {
        "uri": "s3://mlops-bucket/processed/train-001/train.csv",
        "name": "処理済み学習データ",
        "mimeType": "text/csv"
      }
    }
  ],
  "metadata": {
    "num_samples": 10000,
    "num_features": 50,
    "target_distribution": {"class_0": 5000, "class_1": 5000}
  }
}
```

### 4.2 Capability 2: ML Training

#### ツール定義例 (ML Training)

**ツール名**: `train_supervised_classifier`

**入力スキーマ**:

```json
{
  "name": "train_supervised_classifier",
  "description": "教師あり学習（分類）モデルを学習",
  "inputSchema": {
    "type": "object",
    "properties": {
      "algorithm": {
        "type": "string",
        "enum": ["random_forest", "xgboost", "neural_network"],
        "description": "使用するアルゴリズム"
      },
      "train_data_s3_uri": {
        "type": "string",
        "description": "学習データのS3 URI"
      },
      "validation_data_s3_uri": {
        "type": "string",
        "description": "検証データのS3 URI"
      },
      "hyperparameters": {
        "type": "object",
        "description": "ハイパーパラメータ"
      },
      "training_job_name": {
        "type": "string",
        "description": "学習ジョブ名"
      }
    },
    "required": ["algorithm", "train_data_s3_uri", "training_job_name"]
  }
}
```

**出力例**:

```json
{
  "content": [
    {
      "type": "text",
      "text": "Random Forest分類モデルの学習が完了しました"
    },
    {
      "type": "resource",
      "resource": {
        "uri": "s3://mlops-bucket/models/train-001/model.pkl",
        "name": "学習済みモデル",
        "mimeType": "application/octet-stream"
      }
    }
  ],
  "metrics": {
    "train_accuracy": 0.92,
    "validation_accuracy": 0.87,
    "train_loss": 0.23,
    "validation_loss": 0.35,
    "training_time_seconds": 120.5
  }
}
```

### 4.3 Capability 3: ML Evaluation

#### ツール定義例 (ML Evaluation)

**ツール名**: `evaluate_classifier`

**入力スキーマ**:

```json
{
  "name": "evaluate_classifier",
  "description": "分類モデルを評価",
  "inputSchema": {
    "type": "object",
    "properties": {
      "model_s3_uri": {
        "type": "string",
        "description": "モデルのS3 URI"
      },
      "test_data_s3_uri": {
        "type": "string",
        "description": "テストデータのS3 URI"
      },
      "generate_plots": {
        "type": "boolean",
        "description": "プロットを生成するか",
        "default": true
      }
    },
    "required": ["model_s3_uri", "test_data_s3_uri"]
  }
}
```

**出力例**:

```json
{
  "content": [
    {
      "type": "text",
      "text": "モデル評価が完了しました"
    },
    {
      "type": "resource",
      "resource": {
        "uri": "s3://mlops-bucket/evaluations/train-001/confusion_matrix.png",
        "name": "混同行列",
        "mimeType": "image/png"
      }
    },
    {
      "type": "resource",
      "resource": {
        "uri": "s3://mlops-bucket/evaluations/train-001/roc_curve.png",
        "name": "ROC曲線",
        "mimeType": "image/png"
      }
    }
  ],
  "metrics": {
    "accuracy": 0.87,
    "precision": 0.85,
    "recall": 0.89,
    "f1_score": 0.87,
    "auc_roc": 0.91
  }
}
```

### 4.4 統合サーバーのツールルーティング

統合MCPサーバーは、受信したツール呼び出しを適切なcapabilityにルーティングします:

```python
# 統合MCPサーバーのツールルーティング例
class UnifiedMLOpsMCPServer:
    def __init__(self):
        self.capabilities = {
            'data_preparation': DataPreparationCapability(),
            'ml_training': MLTrainingCapability(),
            'ml_evaluation': MLEvaluationCapability(),
            'github_integration': GitHubIntegrationCapability(),
            'model_registry': ModelRegistryCapability(),
            'notification': NotificationCapability()
        }

    async def handle_tool_call(self, tool_name: str, arguments: dict):
        # ツール名からcapabilityを特定
        capability_name = self._get_capability_for_tool(tool_name)
        capability = self.capabilities[capability_name]

        # 該当capabilityでツールを実行
        return await capability.execute_tool(tool_name, arguments)
```

---

## 5. デプロイメント戦略

### 5.1 統合MCPサーバーのホスティング

#### オプション1: ECS Fargate（推奨）

統合MCPサーバーを1つのECS Fargateタスクとしてデプロイ

**メリット**:

- ✅ **運用の簡素化**: 1つのコンテナのみ管理
- ✅ **長時間実行可能**: Lambda 15分制限なし
- ✅ **依存関係の統一**: すべてのcapabilityが同じコンテナイメージを使用
- ✅ **リソース共有**: メモリ・CPUを効率的に共有

**デメリット**:

- ❌ 常時起動の場合、コスト高
- ❌ Lambdaより起動が遅い

**推奨構成**:

- CPU: 2 vCPU
- Memory: 8GB
- Auto Scaling: 最小1タスク、最大5タスク

#### オプション2: Lambda（軽量処理・開発環境向け）

統合MCPサーバーを1つのLambda関数としてデプロイ

**メリット**:

- ✅ **従量課金**: 使用時のみ課金
- ✅ **運用が簡単**: サーバーレス
- ✅ **コールドスタート最小化**: 1つの関数のみウォームアップ

**デメリット**:

- ❌ 15分のタイムアウト制限
- ❌ メモリ制限（最大10GB）
- ❌ 大規模データ処理には不向き

**推奨構成**:

- Memory: 4096MB - 10240MB
- Timeout: 15分
- Ephemeral storage: 10GB

#### オプション3: ハイブリッド（将来の最適化）

統合MCPサーバーで軽量処理を実行し、重い処理は別サービスへ委譲

- 統合MCP Server (Lambda): ツールルーティング、軽量処理
- SageMaker Training Job: 大規模学習（MCPサーバーがジョブを起動）
- SageMaker Processing Job: 大規模データ処理

### 5.2 MCP通信プロトコル

#### stdio通信（推奨）

Lambda/ECS AgentがMCPサーバーを子プロセスとして起動:

```python
# Lambda Agent側（MCP Client）
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def call_mcp_tool():
    # 統合MCPサーバーを起動
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "mcp_server"],  # 統合サーバー
        env={"AWS_REGION": "us-east-1"}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Data Preparationツールを呼び出し
            result = await session.call_tool(
                "preprocess_supervised",
                arguments={
                    "dataset_s3_uri": "s3://...",
                    "target_column": "label",
                    "task_type": "classification"
                }
            )

            return result
```

**メリット**:

- ✅ 1つのサーバープロセスのみ起動
- ✅ すべてのcapabilityに同じセッションでアクセス可能
- ✅ 接続オーバーヘッド最小

#### SSE通信（代替案）

統合MCPサーバーをECS Service（常時起動）として運用し、HTTP/SSEで通信:

- Lambda AgentがHTTPリクエストでMCPサーバーにアクセス
- サーバー側はFastAPI等でHTTPエンドポイントを提供
- 複数のAgentから同時にアクセス可能

---

## 6. 実装ディレクトリ構造（統合MCPサーバー対応）

```text
MLOps/
├── agents/                                # Lambda Agents（MCP Clients）
│   ├── issue_detector/                    # MCP Client実装
│   │   ├── handler.py                    # Lambda handler
│   │   └── mcp_client.py                 # 統合MCP Client
│   ├── data_preparation/                  # MCP Client実装
│   │   ├── handler.py
│   │   └── mcp_client.py                 # 統合MCP Client
│   ├── training/                          # MCP Client実装
│   │   ├── handler.py
│   │   └── mcp_client.py                 # 統合MCP Client
│   ├── evaluation/                        # MCP Client実装
│   │   ├── handler.py
│   │   └── mcp_client.py                 # 統合MCP Client
│   ├── judge/
│   ├── notification/                      # MCP Client実装
│   │   ├── handler.py
│   │   └── mcp_client.py                 # 統合MCP Client
│   ├── rollback/                          # MCP Client実装
│   │   ├── handler.py
│   │   └── mcp_client.py                 # 統合MCP Client
│   └── history_writer/                    # MCP Client実装
│       ├── handler.py
│       └── mcp_client.py                 # 統合MCP Client
│
├── mcp_server/                            # 統合MLOps MCP Server（単数形）
│   ├── __init__.py
│   ├── server.py                         # メインサーバー・ツールルーティング
│   ├── __main__.py                       # エントリーポイント
│   │
│   ├── capabilities/                      # 11個のCapability実装
│   │   ├── __init__.py
│   │   │
│   │   ├── data_preparation/             # Capability 1: Data Preparation
│   │   │   ├── __init__.py
│   │   │   ├── capability.py             # Capability定義
│   │   │   └── tools/
│   │   │       ├── __init__.py
│   │   │       ├── load_dataset.py
│   │   │       ├── validate_data.py
│   │   │       ├── preprocess_supervised.py
│   │   │       ├── preprocess_unsupervised.py
│   │   │       ├── preprocess_reinforcement.py
│   │   │       ├── feature_engineering.py
│   │   │       └── split_dataset.py
│   │   │
│   │   ├── ml_training/                  # Capability 2: ML Training
│   │   │   ├── __init__.py
│   │   │   ├── capability.py
│   │   │   └── tools/
│   │   │       ├── __init__.py
│   │   │       ├── supervised/
│   │   │       │   ├── random_forest.py
│   │   │       │   ├── xgboost.py
│   │   │       │   └── neural_network.py
│   │   │       ├── unsupervised/
│   │   │       │   ├── kmeans.py
│   │   │       │   ├── dbscan.py
│   │   │       │   ├── pca.py
│   │   │       │   └── tsne.py
│   │   │       └── reinforcement/
│   │   │           ├── ppo.py
│   │   │           ├── dqn.py
│   │   │           └── a3c.py
│   │   │
│   │   ├── ml_evaluation/                # Capability 3: ML Evaluation
│   │   │   ├── __init__.py
│   │   │   ├── capability.py
│   │   │   └── tools/
│   │   │       ├── __init__.py
│   │   │       ├── evaluate_classifier.py
│   │   │       ├── evaluate_regressor.py
│   │   │       ├── evaluate_clustering.py
│   │   │       ├── evaluate_reinforcement.py
│   │   │       ├── compare_models.py
│   │   │       └── visualization.py
│   │   │
│   │   ├── github_integration/           # Capability 4: GitHub Integration
│   │   │   ├── __init__.py
│   │   │   ├── capability.py
│   │   │   └── tools/
│   │   │       ├── __init__.py
│   │   │       ├── issue_management.py
│   │   │       ├── label_management.py
│   │   │       ├── repository_operations.py
│   │   │       ├── webhook_handler.py
│   │   │       └── parser.py
│   │   │
│   │   ├── model_registry/               # Capability 5: Model Registry
│   │   │   ├── __init__.py
│   │   │   ├── capability.py
│   │   │   └── tools/
│   │   │       ├── __init__.py
│   │   │       ├── model_registration.py
│   │   │       ├── version_management.py
│   │   │       ├── status_management.py
│   │   │       ├── rollback.py
│   │   │       └── search.py
│   │   │
│   │   └── notification/                 # Capability 6: Notification
│   │       ├── __init__.py
│   │       ├── capability.py
│   │       └── tools/
│   │           ├── __init__.py
│   │           ├── github_notifier.py
│   │           ├── slack_notifier.py
│   │           ├── email_notifier.py
│   │           ├── teams_notifier.py
│   │           ├── discord_notifier.py
│   │           └── template_manager.py
│   │
│   ├── common/                            # 共通ユーティリティ
│   │   ├── __init__.py
│   │   ├── s3_utils.py
│   │   ├── logger.py
│   │   └── config.py
│   │
│   ├── Dockerfile                        # ECS Fargate用Dockerイメージ
│   └── requirements.txt                  # すべてのcapabilityの依存関係を統合
│
├── tests/
│   ├── mcp_server/                       # 統合MCPサーバーのテスト
│   │   ├── test_server.py               # サーバー・ルーティングのテスト
│   │   ├── test_data_preparation.py
│   │   ├── test_ml_training.py
│   │   ├── test_ml_evaluation.py
│   │   ├── test_github_integration.py
│   │   ├── test_model_registry.py
│   │   └── test_notification.py
│   └── integration/
│       └── test_agent_mcp_integration.py
│
└── cdk/
    └── stacks/
        ├── unified_mcp_server_stack.py   # 統合MCPサーバー用ECS/Lambda
        └── ...
```

---

## 7. 実装戦略（統合MCPサーバー）

### 7.1 段階的実装アプローチ

統合MCPサーバーは**単一のサーバー**として実装しますが、capabilityごとに段階的に機能を追加します。

#### Phase 1: コアMLOps Capability実装（Week 1-6）

**Week 1-2: 統合サーバーの基盤 + Data Preparation Capability**

- [ ] 統合MCPサーバーの基本構造実装（`mcp_server/server.py`）
- [ ] ツールルーティング機構の実装
- [ ] Data Preparation Capabilityの実装
- [ ] Data Preparation AgentをMCPクライアント化
- [ ] 単体テスト・統合テスト
- [ ] デプロイ・動作確認

**Week 3-4: ML Training Capability追加**

- [ ] ML Training Capabilityの実装
- [ ] 統合サーバーへのツール登録
- [ ] Training AgentをMCPクライアント化
- [ ] 単体テスト・統合テスト
- [ ] デプロイ・動作確認

**Week 5-6: ML Evaluation Capability追加**

- [ ] ML Evaluation Capabilityの実装
- [ ] 統合サーバーへのツール登録
- [ ] Evaluation AgentをMCPクライアント化
- [ ] 単体テスト・統合テスト
- [ ] デプロイ・動作確認

#### Phase 2: 統合Capability実装（Week 7-12）

**Week 7-8: GitHub Integration Capability追加**

- [ ] GitHub Integration Capabilityの実装
- [ ] 統合サーバーへのツール登録
- [ ] Issue Detector AgentをMCPクライアント化
- [ ] History Writer AgentをMCPクライアント化
- [ ] 単体テスト・統合テスト
- [ ] デプロイ・動作確認

**Week 9-10: Model Registry Capability追加**

- [ ] Model Registry Capabilityの実装
- [ ] 統合サーバーへのツール登録
- [ ] Training AgentのMCPクライアントにモデル登録機能追加
- [ ] Rollback AgentをMCPクライアント化
- [ ] 単体テスト・統合テスト
- [ ] デプロイ・動作確認

**Week 11-12: Notification Capability追加**

- [ ] Notification Capabilityの実装
- [ ] 統合サーバーへのツール登録
- [ ] Notification AgentをMCPクライアント化
- [ ] Slack/Email/Teams/Discord通知機能の実装
- [ ] 通知テンプレート管理機能の実装
- [ ] 単体テスト・統合テスト
- [ ] デプロイ・動作確認

#### Phase 3: E2Eテスト・最適化（Week 13-14）

- [ ] E2Eテストの実施（全学習方式）
- [ ] 統合MCPサーバーの全Capabilityテスト
- [ ] パフォーマンステスト・最適化
- [ ] ドキュメント更新（README、アーキテクチャ設計書等）
- [ ] 運用手順書作成
- [ ] 実装完了報告書作成

### 7.2 後方互換性

実装期間中は以下の戦略を採用:

- 既存のLambda/ECS実装を残す
- 統合MCPサーバー版と既存実装を並行運用
- 環境変数で切り替え可能にする
- Capabilityごとに段階的に移行

---

## 8. メリット・デメリット評価

### 8.1 統合MCPサーバーのメリット

| 項目                     | 詳細                                                       |
| ------------------------ | ---------------------------------------------------------- |
| **再利用性**             | 統合MCPサーバーを他プロジェクトでも利用可能                |
| **保守性**               | 機能追加・変更が1つのサーバー内で完結                      |
| **テスト容易性**         | ローカル環境で全Capabilityを一度にテスト可能               |
| **拡張性**               | 新しいCapability・ツールを容易に追加                       |
| **標準化**               | MCPという業界標準プロトコルに準拠                          |
| **ベンダーニュートラル** | AWS以外のクラウドでも利用可能                              |
| **疎結合**               | Agent層とML処理層が完全に分離                              |
| **運用の簡素化** ⭐      | 1つのサーバープロセス/コンテナのみ管理                     |
| **デプロイの簡素化** ⭐  | 1つのデプロイパイプラインで完結                            |
| **リソース効率** ⭐      | メモリ・CPUを共有、オーバーヘッド削減                      |
| **MCP接続の最小化** ⭐   | 1つのMCP接続で全ツールにアクセス                           |
| **依存関係の統一** ⭐    | すべてのCapabilityで同じバージョンの依存ライブラリを使用   |

### 8.2 デメリット・課題

| 項目                    | 詳細                               | 対策                                   |
| ----------------------- | ---------------------------------- | -------------------------------------- |
| **レイテンシ増加**      | MCP通信のオーバーヘッド            | stdio通信で最小化、キャッシング活用    |
| **複雑性増加**          | MCPサーバーという新しい層が追加    | ドキュメント整備、開発者教育           |
| **初期開発コスト**      | 統合MCPサーバー実装に時間が必要    | 段階的移行、優先度付け                 |
| **運用コスト**          | ECS Fargateの運用コスト増          | Lambda代替、Auto Scaling活用           |
| **単一障害点** ⭐       | サーバーダウン時、全機能が停止     | ECS Auto Scaling、ヘルスチェック強化   |
| **依存関係の肥大化** ⭐ | すべてのCapabilityの依存関係を含む | マルチステージDockerビルドで最適化     |

### 8.3 11個の独立サーバーとの比較

| 項目                 | 統合MCPサーバー（1個）        | 独立MCPサーバー（11個）                |
| -------------------- | ----------------------------- | -------------------------------------- |
| **運用の簡素さ**     | ✅ 1プロセスのみ              | ❌ 11プロセス管理                      |
| **デプロイの簡素さ** | ✅ 1デプロイのみ              | ❌ 11デプロイ管理                      |
| **リソース効率**     | ✅ 共有により効率的           | ❌ 各サーバーでオーバーヘッド          |
| **MCP接続数**        | ✅ 1接続のみ                  | ❌ 11接続必要                          |
| **障害の隔離**       | ❌ 単一障害点                 | ✅ 1サーバーダウンでも他は動作         |
| **個別スケーリング** | ❌ 全Capability一緒にスケール | ✅ Capabilityごとに独立スケール        |
| **開発の独立性**     | △ 同じリポジトリで開発        | ✅ 完全に独立して開発可能              |

### 8.4 総合評価

**推奨**: 統合MCPサーバーアプローチを採用すべき

**理由**:

- ✅ 運用・デプロイの簡素化により、長期的な保守コストが大幅に削減
- ✅ リソース効率の向上により、インフラコストも削減
- ✅ 機械学習アルゴリズムは頻繁に追加・変更されるため、柔軟性が重要
- ✅ 標準プロトコル準拠により、将来的な技術選択肢が広がる
- ✅ 1つのMCP接続で全機能にアクセスでき、Agent側の実装が簡素化
- ⚠️ 単一障害点のリスクはあるが、ECS Auto Scalingとヘルスチェックで緩和可能
- ⚠️ 初期コストは高いが、中長期的にはROIが非常に高い

---

## 9. セキュリティ設計

### 9.1 認証・認可

#### MCP通信の認証

統合MCPサーバーへのアクセスは、以下の認証メカニズムで保護します:

**stdio通信モード（Lambda/ECS Agent → MCP Server）**:

- Lambda/ECS AgentがMCPサーバーを子プロセスとして起動するため、プロセス間通信は信頼される
- IAMロールベースの認証: Lambda/ECS AgentのIAMロールで権限を制御
- 環境変数による設定: AWS_REGION、AWS_PROFILE等

**SSE通信モード（HTTP経由）**:

- API Keyベースの認証: カスタムヘッダー `X-API-Key` で認証
- IAM認証: AWS SigV4署名による認証（API Gateway統合時）
- VPC内通信: プライベートサブネット内のみでアクセス可能

#### IAMロール設計

**Lambda Agent用IAMロール**:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::mlops-bucket/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sagemaker:CreateTrainingJob",
        "sagemaker:DescribeTrainingJob"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:mlops/*"
    }
  ]
}
```

**MCP Server用IAMロール（ECS Task Role）**:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::mlops-bucket",
        "arn:aws:s3:::mlops-bucket/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "sagemaker:*"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "us-east-1"
        }
      }
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:mlops/*"
    }
  ]
}
```

### 9.2 データ暗号化

#### 保存時の暗号化（Encryption at Rest）

**S3バケット暗号化**:

- **デフォルト暗号化**: SSE-S3（AES-256）を有効化
- **推奨**: SSE-KMS（AWS KMS管理キー）を使用し、キーローテーションを有効化
- **バケットポリシー**: 暗号化されていないオブジェクトのアップロードを拒否

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::mlops-bucket/*",
      "Condition": {
        "StringNotEquals": {
          "s3:x-amz-server-side-encryption": "aws:kms"
        }
      }
    }
  ]
}
```

**SageMaker Model Registry暗号化**:

- モデルアーティファクトはKMS暗号化されたS3に保存
- モデルメタデータは自動的にAWS管理キーで暗号化

#### 通信時の暗号化（Encryption in Transit）

**stdio通信**:

- ローカルプロセス間通信のため、TLSは不要
- ただし、Lambda/ECS Agent ↔ AWS SDK通信はHTTPS

**SSE/HTTP通信**:

- **必須**: TLS 1.2以上を使用
- Application Load Balancer（ALB）でTLS終端
- ALB → ECS TaskはVPC内HTTPSまたはHTTP（VPC内のため許容）

**AWS SDK通信**:

- すべてのAWS API呼び出しはHTTPS（TLS 1.2+）

### 9.3 シークレット管理

#### AWS Secrets Managerの使用

すべての機密情報はAWS Secrets Managerに保存:

**保存するシークレット**:

- `mlops/github-token`: GitHub Personal Access Token（Capaiblity 4用）
- `mlops/slack-webhook-url`: Slack Webhook URL（Capability 6用）
- `mlops/email-smtp-password`: Email SMTP認証情報（Capability 6用）
- `mlops/teams-webhook-url`: Microsoft Teams Webhook URL（Capability 6用）
- `mlops/discord-webhook-url`: Discord Webhook URL（Capability 6用）

**シークレット取得のベストプラクティス**:

```python
import boto3
import json
from functools import lru_cache

@lru_cache(maxsize=10)
def get_secret(secret_name: str) -> dict:
    """AWS Secrets Managerからシークレットを取得（キャッシュあり）"""
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# 使用例
github_token = get_secret('mlops/github-token')['token']
```

**シークレットローテーション**:

- 推奨: 90日ごとにシークレットをローテーション
- Lambda関数を使用した自動ローテーション設定

### 9.4 ネットワークセキュリティ

#### VPC設計

**統合MCPサーバー（ECS Fargate）**:

- **配置**: プライベートサブネット
- **アウトバウンド**: NAT Gatewayまたはインターフェースエンドポイント経由
- **インバウンド**: Lambda/ECS Agentからのみアクセス可能（Security Group制限）

**Lambda Agent**:

- **配置**: VPC内プライベートサブネット（VPC Lambda）
- **アウトバウンド**: NAT Gatewayまたはインターフェースエンドポイント経由

**Security Group設定**:

```yaml
# MCP Server Security Group
MCPServerSG:
  Inbound:
    - Port: 8080 (SSEモードの場合のみ)
      Source: LambdaAgentSG
      Protocol: TCP
  Outbound:
    - Port: 443
      Destination: 0.0.0.0/0  # AWS APIs, GitHub API, Slack API等
      Protocol: TCP

# Lambda Agent Security Group
LambdaAgentSG:
  Outbound:
    - Port: 8080 (SSEモードの場合のみ)
      Destination: MCPServerSG
      Protocol: TCP
    - Port: 443
      Destination: 0.0.0.0/0  # AWS APIs
      Protocol: TCP
```

#### VPCエンドポイント

コスト削減とセキュリティ向上のため、以下のVPCエンドポイントを作成:

- **com.amazonaws.region.s3**: S3アクセス（Gateway Endpoint、無料）
- **com.amazonaws.region.secretsmanager**: Secrets Managerアクセス
- **com.amazonaws.region.sagemaker.api**: SageMaker APIアクセス
- **com.amazonaws.region.logs**: CloudWatch Logsアクセス

### 9.5 監査ログ

#### CloudTrailによる操作ログ記録

すべてのAWS API呼び出しをCloudTrailで記録:

- **対象**: S3、SageMaker、Secrets Manager、ECS等のAPI呼び出し
- **保存先**: S3バケット（KMS暗号化、90日保持）
- **ログ検証**: ログファイルの整合性検証を有効化

#### MCPツール呼び出しログ

すべてのMCPツール呼び出しをCloudWatch Logsに記録:

**ログフォーマット（JSON）**:

```json
{
  "timestamp": "2025-12-27T10:30:00.123Z",
  "level": "INFO",
  "capability": "ml_training",
  "tool_name": "train_supervised_classifier",
  "agent_id": "training-agent-001",
  "request_id": "req-abc123",
  "arguments": {
    "algorithm": "random_forest",
    "training_job_name": "train-20251227-001"
  },
  "duration_ms": 1234,
  "status": "success",
  "result_summary": "Training job started successfully"
}
```

**ログ保持期間**: 90日（NFR-006）

**機密情報のマスキング**:

- GitHub Token、Slack Webhook URL等の機密情報はログ出力時にマスキング
- 例: `"github_token": "ghp_***masked***"`

### 9.6 脆弱性管理

#### 依存ライブラリのスキャン

**CI/CDパイプラインでの自動スキャン**:

- **ツール**: Snyk、Dependabot、AWS Inspector
- **頻度**: プルリクエストごと、および毎日定期スキャン
- **対応**: Critical/High脆弱性は24時間以内に修正

**Dockerイメージスキャン**:

- **ツール**: Amazon ECR Image Scanning、Trivy
- **対象**: 統合MCPサーバーのDockerイメージ
- **頻度**: イメージプッシュ時、および毎日定期スキャン

#### セキュリティパッチ適用

**定期更新スケジュール**:

- **依存ライブラリ**: 月次で最新バージョンに更新
- **ベースイメージ**: 月次でセキュリティパッチ適用
- **緊急パッチ**: Critical脆弱性発見時は即座に対応

### 9.7 セキュリティチェックリスト

実装前・デプロイ前のチェックリスト:

**実装前**:

- [ ] IAMロールの最小権限原則（Least Privilege）を適用
- [ ] すべてのシークレットをAWS Secrets Managerに保存
- [ ] VPC内にリソースを配置（プライベートサブネット）
- [ ] Security Groupで必要最小限のポートのみ開放

**デプロイ前**:

- [ ] S3バケット暗号化（SSE-KMS）が有効
- [ ] CloudTrailが有効化されている
- [ ] VPCエンドポイントが設定されている
- [ ] 依存ライブラリの脆弱性スキャンに合格
- [ ] Dockerイメージの脆弱性スキャンに合格

**運用中**:

- [ ] CloudWatch Logsでツール呼び出しログを記録
- [ ] 定期的な脆弱性スキャン（日次）
- [ ] シークレットローテーション（90日ごと）
- [ ] セキュリティパッチ適用（月次）

---

## 10. 代替案との比較

### 10.1 Option A: 現状維持（Lambda/ECS直接実装）

**メリット**: 開発コスト低、シンプル
**デメリット**: 拡張性・保守性が低い
**推奨度**: ❌

### 10.2 Option B: 11個の独立MCPサーバー

**メリット**: 障害の隔離、個別スケーリング、開発の独立性
**デメリット**: 運用・デプロイの複雑化、リソースオーバーヘッド、11個のMCP接続が必要
**推奨度**: △（大規模チーム・高可用性要件がある場合）

### 10.3 Option C: 統合MCPサーバー（本提案）⭐

**メリット**: 運用の簡素化、デプロイの簡素化、リソース効率、1つのMCP接続のみ
**デメリット**: 単一障害点、初期開発コスト高
**推奨度**: ✅（推奨）

### 10.4 Option D: SageMaker Pipelines利用

**メリット**: AWSネイティブ、GUI管理可能
**デメリット**: ベンダーロックイン、柔軟性が低い
**推奨度**: △（AWS縛りOKなら選択肢）

### 10.5 Option E: Kubeflow Pipelines

**メリット**: ML特化、豊富な機能
**デメリット**: インフラ複雑、運用コスト高
**推奨度**: △（大規模組織向け）

---

## 11. 成功指標（KPI）

### 11.1 技術指標

| 指標                       | 目標値             | 測定方法           |
| -------------------------- | ------------------ | ------------------ |
| **コードカバレッジ**       | 80%以上            | pytest-cov         |
| **レイテンシ増加**         | 従来比+10%以内     | CloudWatch Metrics |
| **新アルゴリズム追加時間** | 4時間以内          | 実測               |
| **ローカルテスト成功率**   | 95%以上            | CI/CD統計          |

### 11.2 ビジネス指標

| 指標               | 目標値                  | 測定方法       |
| ------------------ | ----------------------- | -------------- |
| **開発速度向上**   | 新機能追加時間50%削減   | 開発チーム計測 |
| **再利用率**       | 3プロジェクト以上で利用 | 利用状況追跡   |
| **保守コスト削減** | 月次保守時間30%削減     | 保守ログ       |

---

## 12. リスク管理

### 12.1 リスク一覧

| リスク                          | 影響度 | 発生確率 | 対策                             |
| ------------------------------- | ------ | -------- | -------------------------------- |
| MCPサーバーのパフォーマンス問題 | 高     | 中       | 事前性能テスト、キャッシング実装 |
| 開発期間の遅延                  | 中     | 高       | 段階的移行、スコープ調整         |
| チーム学習コスト                | 中     | 中       | ドキュメント整備、ハンズオン実施 |
| ECS運用コスト増加               | 中     | 中       | Auto Scaling、Spot Instance活用  |

---

## 13. 次のステップ

### 13.1 即座に実施すべきこと

1. **POC実施**: Data Preparation MCPサーバーの小規模実装
2. **パフォーマンステスト**: レイテンシ・スループット測定
3. **コスト見積もり**: ECS Fargateのコスト試算

### 13.2 承認後のアクション

1. 詳細実装計画の策定
2. チーム体制の確立
3. Phase 1の実装開始

---

## 14. まとめ

### 14.1 統合MCPサーバーの設計概要

**1つの統合MLOps MCPサーバー** として実装し、**11個のCapability**を提供します（各MCPエージェントと1対1対応）:

1. **GitHub Integration** - Issue検知・パース・ワークフロー起動
2. **Workflow Optimization** - モデル特性分析・最適化提案
3. **Data Preparation** - データ前処理・特徴量エンジニアリング
4. **Model Training** - 機械学習モデルの学習
5. **Model Evaluation** - モデル評価・可視化・バイアス検出
6. **Model Packaging** - モデルコンテナ化・ECR登録
7. **Model Deployment** - モデルデプロイ・エンドポイント管理
8. **Model Monitoring** - パフォーマンス監視・ドリフト検出
9. **Retrain Management** - 再学習トリガー判定・ワークフロー起動
10. **Notification** - 外部通知チャネル統合
11. **History Management** - 学習履歴記録・GitHub履歴管理

**統合アプローチの主要メリット**:

- 🎯 **運用の簡素化**: 1つのサーバープロセス/コンテナのみ管理
- 🎯 **デプロイの簡素化**: 1つのデプロイパイプラインで完結
- 🎯 **リソース効率**: メモリ・CPUを共有、オーバーヘッド削減
- 🎯 **MCP接続の最小化**: 1つのMCP接続で全ツールにアクセス

この統合MCPサーバーで、**システムの約90%の機能をMCP化**します。

### 14.2 期待される効果

**従来の11個独立サーバーと比較した追加メリット**:

- ✅ **運用コスト削減**: 11プロセス→1プロセスにより、運用負荷が大幅に削減
- ✅ **デプロイ時間短縮**: 11デプロイ→1デプロイにより、リリースサイクル高速化
- ✅ **インフラコスト削減**: リソース共有により、メモリ・CPU使用量を最適化
- ✅ **Agent実装の簡素化**: 1つのMCP接続のみで全機能にアクセス可能

**共通メリット**:

- ✅ **再利用性**: 他のMLOpsプロジェクトでも利用可能
- ✅ **保守性**: 機能追加・変更が1つのサーバー内で完結
- ✅ **テスト容易性**: ローカル環境で全Capabilityを一度にテスト可能
- ✅ **拡張性**: 新しいCapability・ツールを容易に追加
- ✅ **標準化**: MCPという業界標準プロトコルに準拠
- ✅ **ベンダーニュートラル**: クラウドプロバイダーに非依存

### 14.3 追加で検討可能なCapability (Phase 3以降)

将来的に統合MCPサーバーに追加可能:

- **Experiment Tracking Capability** - 実験追跡ツール統合（MLflow、W&B等）
- **Data Versioning Capability** - データバージョニングツール統合（DVC、Delta Lake等）

詳細は本ドキュメントのセクション15を参照。

---

## 15. 拡張機能提案

### 15.1 将来的に追加可能なCapability

統合MCPサーバーには、将来的に以下のcapabilityを追加可能です:

#### Capability 12: Experiment Tracking 💡 オプション

**責務**: MLflow、Weights & Biases等の実験追跡ツール統合

**提供ツール**:

- `create_experiment` - 実験の作成
- `log_params` - パラメータのログ
- `log_metrics` - メトリクスのログ
- `log_artifacts` - アーティファクトのログ
- `search_experiments` - 実験検索
- `compare_experiments` - 実験比較
- `get_best_experiment` - 最良実験の取得

**メリット**:

- MLflow、Weights & Biases等の実験追跡ツールを標準インターフェースで利用
- 実験管理をMLOpsパイプラインから分離
- 複数の実験追跡ツールを並行利用可能

#### Capability 13: Data Versioning 💡 オプション

**責務**: DVC、Delta Lake等のデータバージョニングツール統合

**提供ツール**:

- `register_dataset` - データセット登録
- `version_dataset` - データセットのバージョン作成
- `get_dataset_version` - 特定バージョンの取得
- `list_dataset_versions` - バージョン一覧取得
- `track_data_lineage` - データ系譜の記録
- `get_data_lineage` - データ系譜の取得
- `validate_data_quality` - データ品質検証
- `calculate_data_statistics` - データ統計計算
- `detect_data_drift` - データドリフト検出

**メリット**:

- DVC、Delta Lake等のデータバージョニングツールを統一インターフェースで利用
- データセットの変更履歴を追跡
- データ品質メトリクスの自動計算

### 15.2 優先度付け

#### Phase 4: オプション機能（将来的に検討）

**Experiment Tracking Capability**:

- 理由: 高度な実験管理が必要な場合
- 工数: 2週間

**Data Versioning Capability**:

- 理由: データガバナンスが重要な場合
- 工数: 2週間

### 15.3 コスト・ベネフィット分析

| Capability           | 開発工数 | 運用コスト増 | 再利用性 | 保守性向上 | 総合評価    |
| -------------------- | -------- | ------------ | -------- | ---------- | ----------- |
| Experiment Tracking  | 2週間    | 中           | ⭐⭐     | ⭐⭐       | 🔵 オプション |
| Data Versioning      | 2週間    | 中           | ⭐⭐     | ⭐⭐       | 🔵 オプション |

---

## 16. 変更履歴

| バージョン | 日付       | 変更内容                                                | 作成者 |
| ---------- | ---------- | ------------------------------------------------------- | ------ |
| 0.1        | 2025-12-27 | 初版発行（統合MLOps MCPサーバー設計）                   | -      |
| 1.0        | 2025-12-30 | 拡張機能提案を追加（mcp_extended_design.mdの内容を統合）| -      |
