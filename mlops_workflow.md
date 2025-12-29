# MLOpsワークフロー: GitHub Issue駆動型統合MCPシステム

**バージョン**: 0.1
**作成日**: 2025-12-27

---

## 1. ワークフロー概要

本システムは、GitHub Issueをトリガーとして、機械学習モデルの学習・評価・デプロイを自動化するMLOpsパイプラインです。統合MLOps MCPサーバーを活用し、エージェントベースで処理を実行します。

---

## 2. エンドツーエンドワークフロー図

```mermaid
graph TB
    Start([オペレータ]) -->|1. GitHub Issueを作成<br/>ラベル: mlops:train| Issue[GitHub Issue]

    Issue -->|2. Webhook| Detector[Issue Detector Agent]
    Detector -->|3. Issue解析<br/>パラメータ抽出| Parse{Issue本文<br/>パース}

    Parse -->|4. 有効なパラメータ| SF[Step Functions<br/>ワークフロー起動]
    Parse -->|無効| NotifyError[エラー通知]

    SF -->|5. データ準備| PrepAgent[Data Preparation Agent]
    PrepAgent -->|MCP呼び出し| MCP1[統合MCP Server<br/>Capability 1:<br/>Data Preparation]
    MCP1 -->|6. S3から<br/>データロード| S3_1[(S3: datasets/)]
    MCP1 -->|7. 前処理実行<br/>正規化・エンコーディング| Prep[前処理]
    Prep -->|8. 処理済みデータ保存| S3_2[(S3: processed/)]

    S3_2 -->|9. 学習開始| TrainAgent[Training Agent]
    TrainAgent -->|MCP呼び出し| MCP2[統合MCP Server<br/>Capability 2:<br/>ML Training]
    MCP2 -->|10. SageMaker<br/>Training Job起動| SageMaker[Amazon SageMaker<br/>Training Job]
    SageMaker -->|11. 学習完了<br/>モデル保存| S3_3[(S3: models/)]

    S3_3 -->|12. 評価開始| EvalAgent[Evaluation Agent]
    EvalAgent -->|MCP呼び出し| MCP3[統合MCP Server<br/>Capability 3:<br/>ML Evaluation]
    MCP3 -->|13. モデル評価<br/>メトリクス計算| Eval[評価処理]
    Eval -->|14. 評価結果保存| S3_4[(S3: evaluations/)]

    S3_4 -->|15. 判定| JudgeAgent[Judge Agent]
    JudgeAgent -->|16. 閾値比較| Decision{評価結果<br/>≥ 閾値?}

    Decision -->|Yes: 合格| RegistryAgent[Model Registry操作]
    RegistryAgent -->|MCP呼び出し| MCP5[統合MCP Server<br/>Capability 5:<br/>Model Registry]
    MCP5 -->|17. モデル登録| Registry[(SageMaker<br/>Model Registry)]
    Registry -->|18. バージョン管理| Version[v1.2.3]

    Decision -->|No: 不合格| RetryCheck{再学習<br/>回数<br/>< max_retry?}
    RetryCheck -->|Yes| NotifyRetry[Notification Agent]
    NotifyRetry -->|MCP呼び出し| MCP6[統合MCP Server<br/>Capability 6:<br/>Notification]
    MCP6 -->|19. 再学習通知| Slack1[Slack/Email]
    Slack1 -->|20. オペレータ承認待ち| WaitApproval[承認待機]
    WaitApproval -->|21. 承認| PrepAgent

    RetryCheck -->|No: 超過| RollbackAgent[Rollback Agent]
    RollbackAgent -->|MCP呼び出し| MCP5_2[統合MCP Server<br/>Capability 5:<br/>Model Registry]
    MCP5_2 -->|22. 前バージョンに<br/>ロールバック| Registry

    Version -->|23. 履歴保存| HistoryAgent[History Writer Agent]
    HistoryAgent -->|MCP呼び出し| MCP4[統合MCP Server<br/>Capability 4:<br/>GitHub Integration]
    MCP4 -->|24. 学習結果を<br/>Markdown作成| History[training_history/<br/>train-20251227-001.md]
    MCP4 -->|25. GitHubに<br/>コミット| GitHub[(GitHub Repository)]

    History -->|26. 成功通知| NotifySuccess[Notification Agent]
    NotifySuccess -->|MCP呼び出し| MCP6_2[統合MCP Server<br/>Capability 6:<br/>Notification]
    MCP6_2 -->|27. Issue更新<br/>+ Slack通知| IssueUpdate[Issue #123<br/>ステータス: 完了]
    MCP6_2 -->|28. Slack通知| Slack2[Slack Channel]

    RollbackAgent -->|29. 失敗通知| NotifyFail[Notification Agent]
    NotifyFail -->|MCP呼び出し| MCP6_3[統合MCP Server<br/>Capability 6:<br/>Notification]
    MCP6_3 -->|30. Issue更新<br/>+ Slack通知| IssueFail[Issue #123<br/>ステータス: 失敗]

    IssueUpdate -->|完了| End([終了])
    IssueFail -->|完了| End
    NotifyError -->|完了| End

    style MCP1 fill:#e1f5fe
    style MCP2 fill:#e1f5fe
    style MCP3 fill:#e1f5fe
    style MCP4 fill:#e1f5fe
    style MCP5 fill:#e1f5fe
    style MCP6 fill:#e1f5fe
    style MCP5_2 fill:#e1f5fe
    style MCP6_2 fill:#e1f5fe
    style MCP6_3 fill:#e1f5fe
    style Decision fill:#fff9c4
    style RetryCheck fill:#fff9c4
```

---

## 3. 詳細シーケンス図

### 3.1 正常系フロー（教師あり学習）

```mermaid
sequenceDiagram
    participant Op as オペレータ
    participant GH as GitHub
    participant Det as Issue Detector<br/>Agent
    participant SF as Step Functions
    participant Prep as Data Prep<br/>Agent
    participant MCP as 統合MCP Server
    participant S3 as Amazon S3
    participant Train as Training<br/>Agent
    participant SM as SageMaker
    participant Eval as Evaluation<br/>Agent
    participant Judge as Judge Agent
    participant Reg as Model Registry<br/>操作Agent
    participant Hist as History Writer<br/>Agent
    participant Notif as Notification<br/>Agent

    Op->>GH: 1. Issue作成<br/>(ラベル: mlops:train)
    Note over GH: learning_type: supervised<br/>algorithm: random_forest<br/>dataset_id: iris<br/>threshold: 0.85

    GH->>Det: 2. Webhook通知
    Det->>Det: 3. Issue解析<br/>YAML/JSONパース
    Det->>SF: 4. ワークフロー起動<br/>(パラメータ渡す)

    SF->>Prep: 5. データ準備タスク実行
    Prep->>MCP: 6. preprocess_supervised<br/>(Capability 1呼び出し)
    MCP->>S3: 7. データロード<br/>s3://bucket/datasets/iris.csv
    MCP->>MCP: 8. 前処理実行<br/>(正規化・エンコーディング)
    MCP->>S3: 9. 処理済みデータ保存<br/>s3://bucket/processed/iris_train.csv
    MCP-->>Prep: 10. 前処理完了
    Prep-->>SF: 11. タスク完了

    SF->>Train: 12. 学習タスク実行
    Train->>MCP: 13. train_supervised_classifier<br/>(Capability 2呼び出し)
    MCP->>SM: 14. Training Job起動<br/>(algorithm: random_forest)
    SM->>SM: 15. モデル学習
    SM->>S3: 16. モデル保存<br/>s3://bucket/models/iris-rf-001.pkl
    SM-->>MCP: 17. 学習完了
    MCP-->>Train: 18. 学習結果返却
    Train-->>SF: 19. タスク完了

    SF->>Eval: 20. 評価タスク実行
    Eval->>MCP: 21. evaluate_classifier<br/>(Capability 3呼び出し)
    MCP->>S3: 22. モデル・テストデータロード
    MCP->>MCP: 23. 評価実行<br/>(Accuracy, F1等算出)
    MCP->>S3: 24. 評価結果保存<br/>s3://bucket/evaluations/results.json
    MCP-->>Eval: 25. 評価完了<br/>(accuracy: 0.92)
    Eval-->>SF: 26. タスク完了

    SF->>Judge: 27. 判定タスク実行
    Judge->>Judge: 28. 閾値比較<br/>(0.92 >= 0.85: OK)
    Judge-->>SF: 29. 判定結果: 合格

    SF->>Reg: 30. モデル登録タスク実行
    Reg->>MCP: 31. register_model<br/>(Capability 5呼び出し)
    MCP->>MCP: 32. SageMaker Model Registry登録<br/>(version: v1.2.0)
    MCP-->>Reg: 33. 登録完了
    Reg-->>SF: 34. タスク完了

    SF->>Hist: 35. 履歴保存タスク実行
    Hist->>MCP: 36. commit_training_history<br/>(Capability 4呼び出し)
    MCP->>MCP: 37. Markdown作成<br/>(学習結果まとめ)
    MCP->>GH: 38. ファイルコミット<br/>training_history/train-20251227-001.md
    MCP-->>Hist: 39. コミット完了
    Hist-->>SF: 40. タスク完了

    SF->>Notif: 41. 通知タスク実行
    Notif->>MCP: 42. notify_success<br/>(Capability 4, 6呼び出し)
    MCP->>GH: 43. Issueコメント追加<br/>(学習成功・モデルv1.2.0登録)
    MCP->>MCP: 44. Slackメッセージ送信<br/>(Capability 6)
    MCP-->>Notif: 45. 通知完了
    Notif-->>SF: 46. タスク完了

    SF-->>Op: 47. ワークフロー完了<br/>(GitHub Issue & Slackで確認)
```

### 3.2 異常系フロー（再学習）

```mermaid
sequenceDiagram
    participant SF as Step Functions
    participant Judge as Judge Agent
    participant Notif as Notification<br/>Agent
    participant MCP as 統合MCP Server
    participant GH as GitHub
    participant Slack as Slack
    participant Op as オペレータ
    participant Prep as Data Prep<br/>Agent

    Note over SF: 評価完了<br/>(accuracy: 0.70)

    SF->>Judge: 1. 判定タスク実行
    Judge->>Judge: 2. 閾値比較<br/>(0.70 < 0.85: NG)
    Judge->>Judge: 3. リトライ回数確認<br/>(current: 0, max: 3)
    Judge-->>SF: 4. 判定結果: 再学習必要

    SF->>Notif: 5. 再学習通知タスク実行
    Notif->>MCP: 6. notify_retrain_required<br/>(Capability 4, 6呼び出し)
    MCP->>GH: 7. Issueコメント追加<br/>("評価不合格。再学習しますか？")
    MCP->>Slack: 8. Slack通知<br/>(@operator 承認依頼)
    MCP-->>Notif: 9. 通知完了
    Notif-->>SF: 10. タスク完了

    SF->>SF: 11. Task Token発行<br/>(承認待機状態)
    Note over SF: WaitForApproval<br/>ステート

    Op->>GH: 12. Issueコメント<br/>("承認: 再学習実行")
    GH->>Notif: 13. Webhook通知<br/>(コメント追加イベント)
    Notif->>Notif: 14. コメント解析<br/>("承認"を検出)
    Notif->>SF: 15. Task Token返却<br/>(SendTaskSuccess)

    SF->>SF: 16. リトライカウンタ+1<br/>(current: 1)
    SF->>Prep: 17. データ準備タスク再実行<br/>(2回目の学習開始)

    Note over Prep: 以降、通常フローと同じ
```

### 3.3 異常系フロー（ロールバック）

```mermaid
sequenceDiagram
    participant SF as Step Functions
    participant Judge as Judge Agent
    participant Rollback as Rollback<br/>Agent
    participant MCP as 統合MCP Server
    participant Registry as SageMaker<br/>Model Registry
    participant Notif as Notification<br/>Agent
    participant GH as GitHub
    participant Slack as Slack

    Note over SF: 評価完了（3回目）<br/>(accuracy: 0.68)

    SF->>Judge: 1. 判定タスク実行
    Judge->>Judge: 2. 閾値比較<br/>(0.68 < 0.85: NG)
    Judge->>Judge: 3. リトライ回数確認<br/>(current: 3, max: 3)
    Judge-->>SF: 4. 判定結果: 失敗<br/>(最大リトライ超過)

    SF->>Rollback: 5. ロールバックタスク実行
    Rollback->>MCP: 6. rollback_model<br/>(Capability 5呼び出し)
    MCP->>Registry: 7. 前バージョン取得<br/>(v1.1.0)
    MCP->>Registry: 8. v1.2.0 → Archived
    MCP->>Registry: 9. v1.1.0 → Approved
    MCP-->>Rollback: 10. ロールバック完了
    Rollback-->>SF: 11. タスク完了

    SF->>Notif: 12. 失敗通知タスク実行
    Notif->>MCP: 13. notify_training_failed<br/>(Capability 4, 6呼び出し)
    MCP->>GH: 14. Issueコメント追加<br/>("学習失敗。v1.1.0にロールバック")
    MCP->>GH: 15. Issueラベル更新<br/>(mlops:failed)
    MCP->>Slack: 16. Slack通知<br/>(@operator 失敗アラート)
    MCP-->>Notif: 17. 通知完了
    Notif-->>SF: 18. タスク完了

    SF-->>SF: 19. ワークフロー終了<br/>(失敗ステート)
```

---

## 4. 学習方式別ワークフロー

### 4.1 教師あり学習（分類）

```mermaid
graph LR
    A[データ準備] -->|正規化・<br/>エンコーディング| B[学習]
    B -->|Random Forest<br/>XGBoost<br/>Neural Network| C[評価]
    C -->|Accuracy<br/>Precision<br/>Recall<br/>F1-Score<br/>AUC-ROC| D[判定]
    D -->|≥閾値| E[モデル登録]
    D -->|<閾値| F[再学習]
    F --> A
```

### 4.2 教師あり学習（回帰）

```mermaid
graph LR
    A[データ準備] -->|正規化| B[学習]
    B -->|Linear Regression<br/>XGBoost<br/>Neural Network| C[評価]
    C -->|RMSE<br/>MAE<br/>R²<br/>MAPE| D[判定]
    D -->|≥閾値| E[モデル登録]
    D -->|<閾値| F[再学習]
    F --> A
```

### 4.3 教師なし学習（クラスタリング）

```mermaid
graph LR
    A[データ準備] -->|正規化| B[学習]
    B -->|K-Means<br/>DBSCAN<br/>Autoencoder| C[評価]
    C -->|Silhouette Score<br/>Davies-Bouldin Index<br/>Inertia| D[判定]
    D -->|≥閾値| E[モデル登録]
    D -->|<閾値| F[再学習]
    F --> A
```

### 4.4 強化学習

```mermaid
graph LR
    A[環境準備] -->|状態空間<br/>行動空間定義| B[学習]
    B -->|PPO<br/>DQN<br/>A3C| C[評価]
    C -->|Episode Reward<br/>Success Rate<br/>Average Steps| D[判定]
    D -->|≥閾値| E[モデル登録]
    D -->|<閾値| F[再学習]
    F --> A
```

---

## 5. MCPサーバー連携詳細

### 5.1 Agent → MCP Server通信フロー

```mermaid
sequenceDiagram
    participant Agent as Lambda Agent<br/>(MCP Client)
    participant MCP as 統合MCP Server<br/>(stdio/SSE)
    participant Cap as Capability<br/>(Data Prep etc.)
    participant Tool as Tool<br/>(preprocess_supervised)
    participant AWS as AWS Services<br/>(S3/SageMaker)

    Agent->>MCP: 1. MCP接続確立<br/>(stdio起動 or SSE接続)
    MCP-->>Agent: 2. 接続確立

    Agent->>MCP: 3. list_tools()<br/>(利用可能ツール一覧取得)
    MCP->>MCP: 4. 全Capabilityから<br/>ツール収集
    MCP-->>Agent: 5. ツール一覧返却<br/>(60+ tools)

    Agent->>MCP: 6. call_tool()<br/>name: preprocess_supervised<br/>arguments: {...}
    MCP->>MCP: 7. ツールルーティング<br/>(ToolRouter)
    MCP->>Cap: 8. Capability特定<br/>(data_preparation)
    Cap->>Tool: 9. ツール実行<br/>(preprocess_supervised.execute)
    Tool->>AWS: 10. S3からデータロード
    AWS-->>Tool: 11. データ返却
    Tool->>Tool: 12. 前処理実行
    Tool->>AWS: 13. S3に結果保存
    Tool-->>Cap: 14. 処理結果返却
    Cap-->>MCP: 15. MCP Response作成<br/>(TextContent + EmbeddedResource)
    MCP-->>Agent: 16. call_tool() 結果返却

    Agent->>Agent: 17. 結果処理<br/>(次のステップへ)
```

### 5.2 統合MCPサーバー内部ルーティング

```mermaid
graph TB
    Agent[Lambda Agent] -->|MCP Request<br/>tool: train_supervised_classifier| Server[MCP Server]

    Server --> Router[ToolRouter]
    Router -->|ツール名で検索| Mapping{Tool Mapping<br/>Dictionary}

    Mapping -->|"train_supervised_classifier"<br/>→ "ml_training"| Cap2[Capability 2:<br/>ML Training]
    Mapping -->|"preprocess_supervised"<br/>→ "data_preparation"| Cap1[Capability 1:<br/>Data Preparation]
    Mapping -->|"evaluate_classifier"<br/>→ "ml_evaluation"| Cap3[Capability 3:<br/>ML Evaluation]
    Mapping -->|"register_model"<br/>→ "model_registry"| Cap5[Capability 5:<br/>Model Registry]

    Cap2 --> Tool[train_supervised_classifier<br/>ツール実行]
    Tool --> SM[SageMaker<br/>Training Job起動]
    SM --> Result[MCP Response]
    Result --> Agent

    style Mapping fill:#fff9c4
    style Router fill:#e1f5fe
```

---

## 6. データフロー

### 6.1 S3バケット間のデータ移動

```mermaid
graph LR
    Raw[(S3: datasets/<br/>raw data)] -->|1. Data Prep Agent<br/>MCP: load_dataset| Prep
    Prep[データ前処理] -->|2. MCP: preprocess_*| Processed[(S3: processed/<br/>train/val/test)]

    Processed -->|3. Training Agent<br/>MCP: train_*| Train[SageMaker<br/>Training Job]
    Train -->|4. 学習済みモデル| Models[(S3: models/<br/>model.pkl)]

    Models -->|5. Evaluation Agent<br/>MCP: evaluate_*| Eval[評価処理]
    Eval -->|6. 評価結果・可視化| EvalResults[(S3: evaluations/<br/>results.json<br/>plots.png)]

    Models -->|7. Model Registry Agent<br/>MCP: register_model| Registry[(SageMaker<br/>Model Registry<br/>v1.2.0)]

    EvalResults -->|8. History Writer Agent<br/>MCP: commit_history| GitHub[(GitHub:<br/>training_history/<br/>*.md)]

    style Raw fill:#fff3e0
    style Processed fill:#e8f5e9
    style Models fill:#e3f2fd
    style EvalResults fill:#f3e5f5
    style Registry fill:#fce4ec
    style GitHub fill:#e0f2f1
```

### 6.2 メタデータフロー

```mermaid
graph TB
    Issue[GitHub Issue<br/>パラメータ] -->|Issue Detector| Metadata{メタデータ}

    Metadata -->|training_config| SF[Step Functions<br/>実行コンテキスト]
    SF -->|各Agentに渡す| Agent1[Data Prep Agent]
    SF -->|各Agentに渡す| Agent2[Training Agent]
    SF -->|各Agentに渡す| Agent3[Evaluation Agent]

    Agent1 -->|前処理メタデータ| Meta1[num_samples<br/>num_features<br/>target_distribution]
    Agent2 -->|学習メタデータ| Meta2[algorithm<br/>hyperparameters<br/>train_accuracy<br/>train_loss]
    Agent3 -->|評価メタデータ| Meta3[test_accuracy<br/>precision<br/>recall<br/>f1_score]

    Meta1 --> Combine[メタデータ統合]
    Meta2 --> Combine
    Meta3 --> Combine

    Combine -->|History Writer Agent| History[学習履歴<br/>Markdown]
    History -->|GitHub保存| Final[training_history/<br/>train-20251227-001.md]

    style Metadata fill:#fff9c4
    style Combine fill:#e1f5fe
```

---

## 7. Step Functions ステートマシン詳細

### 7.1 メインワークフロー（状態遷移図）

```mermaid
stateDiagram-v2
    [*] --> PrepareData: ワークフロー開始

    PrepareData --> TrainModel: データ準備完了
    TrainModel --> EvaluateModel: 学習完了
    EvaluateModel --> JudgeResults: 評価完了

    JudgeResults --> RegisterModel: 判定: 合格
    JudgeResults --> CheckRetryLimit: 判定: 不合格
    JudgeResults --> RollbackModel: 判定: 失敗

    CheckRetryLimit --> NotifyOperator: リトライ回数 < max
    CheckRetryLimit --> RollbackModel: リトライ回数 >= max

    NotifyOperator --> WaitForOperatorInput: 通知送信完了
    WaitForOperatorInput --> IncrementRetry: オペレータ承認
    IncrementRetry --> PrepareData: リトライカウンタ+1

    RegisterModel --> WriteHistory: モデル登録完了
    WriteHistory --> NotifySuccess: 履歴保存完了
    NotifySuccess --> [*]: ワークフロー成功

    RollbackModel --> NotifyFailure: ロールバック完了
    NotifyFailure --> [*]: ワークフロー失敗

    PrepareData --> ErrorHandler: エラー発生
    TrainModel --> ErrorHandler: エラー発生
    EvaluateModel --> ErrorHandler: エラー発生
    ErrorHandler --> NotifyFailure: エラー通知
```

### 7.2 各ステートの詳細

| ステート名 | タイプ | 実行内容 | タイムアウト | リトライ |
|-----------|--------|---------|------------|---------|
| **PrepareData** | Task | Data Preparation Agent実行 | 15分 | 3回 |
| **TrainModel** | Task | Training Agent実行（.sync統合） | 60分 | 1回 |
| **EvaluateModel** | Task | Evaluation Agent実行 | 15分 | 3回 |
| **JudgeResults** | Task | Judge Agent実行 | 5分 | なし |
| **CheckRetryLimit** | Choice | リトライ回数判定 | - | - |
| **NotifyOperator** | Task | Notification Agent実行 | 5分 | 3回 |
| **WaitForOperatorInput** | Task (Token) | オペレータ承認待機 | 24時間 | なし |
| **IncrementRetry** | Pass | リトライカウンタ+1 | - | - |
| **RegisterModel** | Task | Model Registry操作Agent実行 | 10分 | 3回 |
| **WriteHistory** | Task | History Writer Agent実行 | 5分 | 3回 |
| **NotifySuccess** | Task | Notification Agent実行 | 5分 | 3回 |
| **RollbackModel** | Task | Rollback Agent実行 | 10分 | 3回 |
| **NotifyFailure** | Task | Notification Agent実行 | 5分 | 3回 |
| **ErrorHandler** | Catch | エラーハンドリング | - | - |

---

## 8. 通知フロー

### 8.1 通知チャネルマトリクス

| イベント | GitHub Issue | Slack | Email | 内容 |
|---------|-------------|-------|-------|------|
| **学習開始** | コメント | メッセージ | - | "学習を開始しました（Job: train-001）" |
| **学習完了** | - | メッセージ | - | "学習が完了しました（Accuracy: 0.92）" |
| **評価完了** | コメント | - | - | "評価結果: Accuracy=0.92, F1=0.90" |
| **合格判定** | コメント + ラベル更新 | メンション付き | - | "閾値を超えました。モデルv1.2.0を登録" |
| **再学習要求** | コメント | メンション付き | メール | "評価不合格。再学習承認をお願いします" |
| **学習成功** | コメント + Issueクローズ | メンション付き | メール | "学習成功。モデルv1.2.0をデプロイ可能" |
| **学習失敗** | コメント + ラベル更新 | アラート | メール | "最大リトライ超過。v1.1.0にロールバック" |

### 8.2 通知テンプレート例

**GitHub Issueコメント（学習成功）**:
```markdown
## ✅ 学習成功

**学習ジョブ**: train-20251227-001
**アルゴリズム**: Random Forest
**モデルバージョン**: v1.2.0

### 📊 評価結果
- **Accuracy**: 0.92 (閾値: 0.85)
- **Precision**: 0.90
- **Recall**: 0.94
- **F1-Score**: 0.92

### 📁 成果物
- モデル: [s3://mlops-bucket/models/train-20251227-001/model.pkl](...)
- 評価レポート: [training_history/train-20251227-001.md](...)

**ステータス**: モデルはSageMaker Model Registryに登録済みです。デプロイ可能です。
```

**Slack通知（再学習要求）**:
```
⚠️ *再学習承認が必要です* @operator

*Issue*: #123 Iris分類モデルの学習
*評価結果*: Accuracy=0.70 (閾値: 0.85未満)
*現在のリトライ*: 0/3

以下のいずれかを選択してください:
• Issueに "承認" とコメント → 再学習実行
• Issueに "却下" とコメント → ロールバック
```

---

## 9. エラーハンドリング戦略

### 9.1 エラー分類と対応

| エラー種別 | 例 | 対応 | 通知 |
|----------|---|------|------|
| **一時的エラー** | S3接続タイムアウト | 自動リトライ（3回） | なし |
| **データエラー** | 欠損値過多、型不整合 | ワークフロー停止 | GitHub + Slack |
| **学習エラー** | SageMaker Job失敗 | リトライ（1回）→失敗なら通知 | GitHub + Slack |
| **評価不合格** | Accuracy < 閾値 | 再学習フロー | GitHub + Slack |
| **最大リトライ超過** | 3回再学習しても不合格 | ロールバック | GitHub + Slack + Email |
| **システムエラー** | Lambda OOM、ECS Task停止 | エラーログ記録、アラート | Slack + Email |

### 9.2 エラーリカバリーフロー

```mermaid
graph TB
    Error[エラー発生] --> Classify{エラー分類}

    Classify -->|一時的エラー| Retry[自動リトライ<br/>最大3回]
    Retry -->|成功| Continue[処理継続]
    Retry -->|失敗| Permanent

    Classify -->|永続的エラー| Permanent[永続的エラー]
    Permanent --> Log[CloudWatch Logs<br/>エラーログ記録]
    Log --> Notify[通知送信<br/>GitHub + Slack]
    Notify --> Rollback{ロールバック<br/>必要?}

    Rollback -->|Yes| DoRollback[前バージョンに<br/>ロールバック]
    Rollback -->|No| Stop[ワークフロー停止]

    DoRollback --> NotifyOp[オペレータ通知]
    Stop --> NotifyOp
    NotifyOp --> Manual[手動対応待ち]

    style Error fill:#ffebee
    style Permanent fill:#ffcdd2
    style Manual fill:#fff9c4
```

---

## 10. モニタリング・ロギング

### 10.1 モニタリング項目

| カテゴリ | メトリクス | 閾値 | アクション |
|---------|----------|------|-----------|
| **ワークフロー** | 実行成功率 | < 95% | アラート |
| | 平均実行時間 | > 90分 | パフォーマンス調査 |
| **学習** | SageMaker Job成功率 | < 90% | アラート |
| | 学習時間 | > 60分 | リソース見直し |
| **評価** | 評価指標の推移 | 低下傾向 | データ品質調査 |
| **MCP Server** | ツール呼び出しレイテンシ | P95 > 1秒 | パフォーマンス最適化 |
| | エラー率 | > 1% | エラー原因調査 |
| **インフラ** | Lambda同時実行数 | > 80% | 制限緩和申請 |
| | ECS CPU使用率 | > 80% | スケールアウト |

### 10.2 ロギング構造

**CloudWatch Logs ロググループ構成**:
```
/aws/lambda/issue-detector-agent
/aws/lambda/data-preparation-agent
/aws/lambda/training-agent
/aws/lambda/evaluation-agent
/aws/lambda/judge-agent
/aws/lambda/notification-agent
/aws/lambda/rollback-agent
/aws/lambda/history-writer-agent
/aws/ecs/unified-mcp-server
/aws/sagemaker/TrainingJobs
/aws/states/mlops-workflow
```

**統合ログフォーマット（JSON）**:
```json
{
  "timestamp": "2025-12-27T10:30:00.123Z",
  "level": "INFO",
  "service": "training-agent",
  "execution_id": "exec-abc123",
  "issue_number": 123,
  "training_job_name": "train-20251227-001",
  "message": "Training job started successfully",
  "duration_ms": 1234,
  "status": "success"
}
```

---

## 11. まとめ

本MLOpsワークフローは以下の特徴を持ちます:

✅ **GitHub Issue駆動**: オペレータが簡単にIssueを作成するだけで学習を開始
✅ **完全自動化**: データ準備→学習→評価→判定→デプロイまで自動化
✅ **統合MCP対応**: 11個のCapabilityを1つのMCPサーバーで提供し、運用を簡素化
✅ **エージェントベース**: 各処理を独立したAgentとして実装し、疎結合を実現
✅ **柔軟な学習方式**: 教師あり・教師なし・強化学習をサポート
✅ **堅牢なエラーハンドリング**: 自動リトライ、再学習フロー、ロールバック機能
✅ **透明性**: GitHub履歴保存、Slack/Email通知、CloudWatch Logsで可視化

---

## 12. 変更履歴

| バージョン | 日付 | 変更内容 | 作成者 |
| --- | --- | --- | --- |
| 0.1 | 2025-12-27 | 初版発行 | - |
