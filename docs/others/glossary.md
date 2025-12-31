# MLOps用語集

このドキュメントは、MLOpsシステムで使用される技術用語、略語、概念の定義を提供します。

## 目次

- [A](#a)
- [B](#b)
- [C](#c)
- [D](#d)
- [E](#e)
- [F](#f)
- [G](#g)
- [H](#h)
- [I](#i)
- [J](#j)
- [K](#k)
- [L](#l)
- [M](#m)
- [N](#n)
- [O](#o)
- [P](#p)
- [Q](#q)
- [R](#r)
- [S](#s)
- [T](#t)
- [U](#u)
- [V](#v)
- [W](#w)
- [X-Z](#x-z)

---

## A

### A3C (Asynchronous Advantage Actor-Critic)

非同期アドバンテージ Actor-Critic。強化学習アルゴリズムの一種で、複数のエージェントを並列実行して学習を高速化する手法。

### Agent (エージェント)

MLOpsパイプラインにおいて、特定のタスクを自律的に実行するソフトウェアコンポーネント。本システムでは、Issue Detector、Data Preparation、
Training、Evaluationなど11個のエージェントが存在する。

### API Gateway

AWSのサービス。RESTful APIやWebSocket APIを作成・公開・保守・監視・保護するためのフルマネージドサービス。

### AUC-ROC (Area Under the Receiver Operating Characteristic Curve)

ROC曲線の下の面積。分類モデルの性能を評価する指標で、0.5（ランダム）から1.0（完全な分類）の値を取る。

### Auto Scaling

負荷に応じて自動的にコンピューティングリソース（インスタンス数、メモリ等）を増減させる機能。

### AWS (Amazon Web Services)

Amazonが提供するクラウドコンピューティングサービス。本システムではSageMaker、Step Functions、Lambda、ECS等を使用。

---

## B

### Bayesian Optimization

ベイズ最適化。ハイパーパラメータチューニングの手法の一つで、過去の評価結果を基に次に評価すべきパラメータを確率的に選択する。

### Bias Check (バイアス検出)

機械学習モデルが特定の属性（性別、人種等）に対して不公平な予測をしていないか検証するプロセス。SageMaker Clarifyで実施。

### Blue/Green Deployment

新バージョン（Green）を本番環境と並行して準備し、テスト後に一気に切り替えるデプロイメント手法。ロールバックが容易。

---

## C

### Canary Deployment (カナリアデプロイメント)

新バージョンを少数のユーザーにのみ公開し、問題がなければ段階的に全体に展開するデプロイメント手法。

### Capability (ケイパビリティ)

統合MCP Serverが提供する機能群の単位。本システムでは11個のCapabilityが存在（Data Preparation、ML Training、ML Evaluation等）。

### CI/CD (Continuous Integration/Continuous Delivery)

継続的インテグレーション/継続的デリバリー。コードの変更を自動的にビルド・テスト・デプロイするプロセス。

### Classification (分類)

教師あり学習の一種。入力データを事前に定義されたカテゴリ（クラス）に分類するタスク。例: スパム検出、画像分類。

### CloudWatch

AWSの監視・ログサービス。メトリクス収集、ログ管理、アラーム設定等を提供。

### CloudTrail

AWSのAPI呼び出しを記録する監査ログサービス。セキュリティ分析、リソース変更追跡に使用。

### Clustering (クラスタリング)

教師なし学習の一種。データを類似性に基づいてグループ（クラスタ）に分類する手法。例: 顧客セグメンテーション。

### Concept Drift (コンセプトドリフト)

時間経過により、予測対象の概念そのものが変化する現象。例: ユーザーの嗜好の変化。再学習のトリガーとなる。

### Confusion Matrix (混同行列)

分類モデルの予測結果を真陽性、偽陽性、真陰性、偽陰性の4つに分類した行列。モデル評価に使用。

### Container (コンテナ)

アプリケーションとその依存関係を1つのパッケージにまとめた実行環境。Dockerが代表的。

---

## D

### Data Drift (データドリフト)

時間経過により、入力データの分布が学習時と異なるようになる現象。モデルの性能低下の原因となる。

### Data Lineage (データ系譜)

データの起源、移動、変換の履歴を追跡する情報。データガバナンスに重要。

### Data Versioning (データバージョニング)

データセットの変更履歴を管理し、特定バージョンを再現可能にする手法。DVC、Delta Lake等のツールを使用。

### Davies-Bouldin Index

クラスタリングの評価指標。値が小さいほど、クラスタ内の密度が高く、クラスタ間の分離が良い。

### DBSCAN (Density-Based Spatial Clustering of Applications with Noise)

密度ベースのクラスタリングアルゴリズム。K-meansと異なり、クラスタ数を事前に指定不要で、ノイズ（外れ値）を検出可能。

### Deployment (デプロイメント)

学習済みモデルを本番環境に配置し、推論可能な状態にするプロセス。

### Dimensionality Reduction (次元削減)

高次元データを低次元に変換する手法。可視化やノイズ除去に使用。PCA、t-SNEが代表的。

### Docker

コンテナ技術の代表的なプラットフォーム。アプリケーションとその依存関係を1つのイメージにパッケージ化。

### DQN (Deep Q-Network)

深層Q学習。強化学習アルゴリズムの一種で、Q関数をニューラルネットワークで近似する。

### DVC (Data Version Control)

データバージョニングツール。Gitのようにデータセットのバージョン管理を実現。

---

## E

### ECR (Elastic Container Registry)

AWSのDockerコンテナレジストリサービス。コンテナイメージの保存・管理を提供。

### ECS (Elastic Container Service)

AWSのコンテナオーケストレーションサービス。Dockerコンテナの実行・管理を提供。

### ECS Fargate

ECSのサーバーレス実行モード。インフラ管理不要でコンテナを実行可能。

### Endpoint (エンドポイント)

デプロイされたモデルにHTTP/HTTPS経由でアクセスするためのURL。SageMakerエンドポイントが代表的。

### Experiment Tracking (実験追跡)

機械学習実験のパラメータ、メトリクス、アーティファクトを記録・管理するプロセス。MLflow、Weights & Biasesが代表的。

---

## F

### F1 Score

分類モデルの評価指標。Precision（適合率）とRecall（再現率）の調和平均。不均衡データセットで有用。

### Feature Engineering (特徴量エンジニアリング)

生データから機械学習モデルに適した特徴量を作成・選択するプロセス。モデル性能に大きく影響。

### Fine-tuning (ファインチューニング)

事前学習済みモデルを新しいタスクに適応させるため、少量のデータで追加学習するプロセス。

---

## G

### GitHub Actions

GitHub提供のCI/CDサービス。リポジトリ内でワークフローを自動実行。

### GitHub Issue

GitHubのタスク管理機能。本システムではIssueをトリガーとしてMLOpsパイプラインを起動。

### Grid Search

ハイパーパラメータチューニング手法。事前に定義したパラメータの全組み合わせを試行。

---

## H

### Health Check (ヘルスチェック)

システムやサービスが正常に動作しているか定期的に確認するプロセス。

### Hyperparameter (ハイパーパラメータ)

機械学習アルゴリズムの挙動を制御するパラメータ。学習前に設定が必要（例: 学習率、木の深さ）。

### Hyperparameter Optimization (ハイパーパラメータ最適化)

最適なハイパーパラメータを探索するプロセス。Grid Search、Random Search、Bayesian Optimizationが代表的。

---

## I

### IAM (Identity and Access Management)

AWSのアクセス管理サービス。ユーザー、ロール、ポリシーを通じて権限を制御。

### IAM Role

AWSリソースが他のAWSサービスにアクセスする際に使用する権限セット。最小権限の原則に従って設計。

### Inference (推論)

学習済みモデルを使用して新しいデータに対する予測を行うプロセス。

### Issue Detector Agent

GitHubのIssueを検知し、MLOps用のIssueかどうかを判定し、パイプラインを起動するエージェント。

---

## J

### JSON-RPC

JSONフォーマットを使用したリモートプロシージャコール（RPC）プロトコル。MCPの通信プロトコルとして使用。

---

## K

### K-means

代表的なクラスタリングアルゴリズム。データをK個のクラスタに分割（Kは事前に指定）。

### KMS (Key Management Service)

AWSの暗号化キー管理サービス。データの暗号化・復号化に使用する鍵を一元管理。

### KPI (Key Performance Indicator)

重要業績評価指標。システムやプロジェクトの成功を測定する指標。

---

## L

### Lambda (AWS Lambda)

AWSのサーバーレスコンピューティングサービス。コードを実行する際にサーバー管理が不要。本システムでは各エージェントがLambda関数として実装。

### Latency (レイテンシ)

リクエストを送信してからレスポンスを受信するまでの遅延時間。

### Least Privilege (最小権限の原則)

セキュリティのベストプラクティス。ユーザーやサービスに必要最小限の権限のみを付与する。

---

## M

### MAE (Mean Absolute Error)

平均絶対誤差。回帰モデルの評価指標で、予測値と実測値の絶対誤差の平均。

### MAPE (Mean Absolute Percentage Error)

平均絶対パーセント誤差。回帰モデルの評価指標で、誤差を実測値のパーセンテージで表現。

### MCP (Model Context Protocol)

Anthropic社が提唱する標準プロトコル。LLMアプリケーションと外部ツール・データソース間の連携を標準化。

### MCP Client

MCPプロトコルを使用してMCP Serverにリクエストを送信するクライアント。本システムでは各エージェントがMCP Client。

### MCP Server

MCPプロトコルに準拠したサーバー。ツール（機能）を提供し、MCP Clientからのリクエストに応答。

### Metrics (メトリクス)

システムやモデルのパフォーマンスを測定する数値指標。例: Accuracy、Precision、Recall、Latency等。

### MLflow

オープンソースの機械学習ライフサイクル管理プラットフォーム。実験追跡、モデル管理、デプロイメントをサポート。

### MLOps (Machine Learning Operations)

機械学習モデルの開発から本番運用までのライフサイクルを効率化・自動化するプラクティス。DevOpsのML版。

### Model (モデル)

機械学習アルゴリズムが学習したパターンを表現する数学的表現。新しいデータへの予測に使用。

### Model Drift

モデルの予測精度が時間経過とともに低下する現象。Data DriftやConcept Driftが原因。

### Model Registry (モデルレジストリ)

学習済みモデルを一元管理するリポジトリ。バージョン管理、メタデータ管理、ステータス管理（承認、本番等）を提供。

### Monitoring (モニタリング)

システムやモデルの状態を継続的に監視するプロセス。異常検知や性能追跡に使用。

---

## N

### NAT Gateway

AWSのネットワークアドレス変換サービス。プライベートサブネット内のリソースがインターネットにアクセス可能にする。

### Neural Network (ニューラルネットワーク)

人間の脳の神経回路を模した機械学習モデル。ディープラーニングの基礎。

### NFR (Non-Functional Requirement)

非機能要件。性能、セキュリティ、可用性等、システムの品質属性に関する要件。

### Notification (通知)

システムのイベントや状態をユーザーに伝えるメッセージ。Slack、Email、Teams、Discord等のチャネルを使用。

---

## O

### ONNX (Open Neural Network Exchange)

機械学習モデルの相互運用可能なフォーマット。異なるフレームワーク間でモデルを変換・移植可能。

### Orchestration (オーケストレーション)

複数のタスクやサービスを連携させて1つのワークフローとして実行するプロセス。AWS Step Functionsが代表的。

---

## P

### PCA (Principal Component Analysis)

主成分分析。次元削減手法の一つで、データの分散を最大化する方向に新しい軸を設定。

### Pipeline (パイプライン)

データ処理や機械学習の一連の処理を自動化したワークフロー。データ収集→前処理→学習→評価→デプロイの流れ。

### Precision (適合率)

分類モデルの評価指標。陽性と予測したもののうち、実際に陽性だった割合。TP / (TP + FP)。

### PPO (Proximal Policy Optimization)

近接方策最適化。強化学習アルゴリズムの一種で、安定した学習が可能。

### Pre-processing (前処理)

機械学習モデルに入力する前にデータを加工するプロセス。正規化、欠損値補完、カテゴリカル変数のエンコーディング等。

---

## Q

### Q-Learning

強化学習アルゴリズムの一種。状態と行動のペアに対する価値（Q値）を学習。

---

## R

### R² (R-squared, 決定係数)

回帰モデルの評価指標。モデルがデータの変動をどれだけ説明できるかを示す（0～1の値）。

### Random Forest

複数の決定木を組み合わせたアンサンブル学習アルゴリズム。高精度で過学習しにくい。

### Random Search

ハイパーパラメータチューニング手法。パラメータをランダムにサンプリングして試行。Grid Searchより効率的。

### Recall (再現率)

分類モデルの評価指標。実際の陽性のうち、正しく陽性と予測できた割合。TP / (TP + FN)。

### Regression (回帰)

教師あり学習の一種。連続値を予測するタスク。例: 価格予測、需要予測。

### Reinforcement Learning (強化学習)

エージェントが環境と相互作用しながら、報酬を最大化する行動を学習する機械学習手法。

### Retrain (再学習)

既存のモデルを新しいデータで再度学習させるプロセス。Data DriftやConcept Driftに対応。

### RMSE (Root Mean Squared Error)

二乗平均平方根誤差。回帰モデルの評価指標で、予測値と実測値の誤差の二乗平均の平方根。

### ROC Curve (Receiver Operating Characteristic Curve)

分類モデルの性能を可視化するグラフ。True Positive RateとFalse Positive Rateをプロット。

### Rollback (ロールバック)

デプロイ後に問題が発生した際、以前のバージョンに戻すプロセス。

---

## S

### S3 (Simple Storage Service)

AWSのオブジェクトストレージサービス。データセット、モデル、ログ等を保存。

### SageMaker

AWSのフルマネージド機械学習サービス。データ準備、モデル学習、デプロイ、監視を統合提供。

### SageMaker Clarify

SageMakerの機能。モデルのバイアス検出と説明可能性（SHAP値）を提供。

### SageMaker Model Registry

SageMakerのモデル管理機能。バージョン管理、承認ワークフロー、メタデータ管理を提供。

### Secrets Manager

AWSのシークレット管理サービス。APIキー、パスワード、データベース認証情報等を安全に保存。

### Security Group

AWSのファイアウォール機能。インバウンド・アウトバウンドトラフィックを制御。

### SES (Simple Email Service)

AWSのメール送信サービス。通知メールの送信に使用。

### SHAP (SHapley Additive exPlanations)

モデルの予測結果を説明するための手法。各特徴量の予測への寄与度を計算。

### Silhouette Score

クラスタリングの評価指標。各データポイントが自分のクラスタにどれだけ適合しているかを測定（-1～1の値）。

### Slack

チームコラボレーションツール。本システムでは通知チャネルとして使用。

### SSE (Server-Sent Events)

サーバーからクライアントへの一方向リアルタイム通信プロトコル。MCPの通信方式の一つ。

### SSE-KMS

S3のサーバーサイド暗号化方式。AWS KMSで管理されたキーを使用。

### State Machine (ステートマシン)

AWS Step Functionsで定義されるワークフロー。状態の遷移を定義し、複雑な処理フローを管理。

### Step Functions

AWSのワークフローオーケストレーションサービス。複数のLambda関数やサービスを連携させて実行。

### stdio (Standard Input/Output)

標準入出力。MCPの通信方式の一つで、プロセス間通信に使用。

### Supervised Learning (教師あり学習)

ラベル付きデータ（入力と正解のペア）を使用して学習する機械学習手法。分類と回帰が代表的。

---

## T

### t-SNE (t-distributed Stochastic Neighbor Embedding)

次元削減手法の一つで、高次元データを2次元・3次元に可視化する際に使用。

### TLS (Transport Layer Security)

通信を暗号化するプロトコル。HTTPSで使用（TLS 1.2以上を推奨）。

### Tool (ツール)

MCPサーバーが提供する機能の単位。例: `preprocess_supervised`、`train_classifier`等。

### Training (学習)

機械学習モデルがデータからパターンを学習するプロセス。

### Training Job

SageMakerで実行される学習タスク。学習データ、アルゴリズム、ハイパーパラメータを指定して実行。

---

## U

### Unsupervised Learning (教師なし学習)

ラベルなしデータから構造やパターンを発見する機械学習手法。クラスタリングや次元削減が代表的。

---

## V

### Validation Data (検証データ)

モデルのハイパーパラメータチューニングやモデル選択に使用するデータセット。学習には使用しない。

### VPC (Virtual Private Cloud)

AWSの仮想プライベートネットワーク。リソースを論理的に分離し、セキュリティを強化。

### VPC Endpoint

VPC内からAWSサービスにプライベート接続するためのエンドポイント。インターネットを経由せずアクセス可能。

---

## W

### Weights & Biases (W&B)

機械学習実験追跡プラットフォーム。実験管理、可視化、チームコラボレーション機能を提供。

### Webhook

特定のイベント発生時にHTTPリクエストを送信する仕組み。GitHubのIssue作成時にWebhookでLambdaを起動。

### Workflow (ワークフロー)

一連のタスクを自動化した処理フロー。本システムではStep Functionsで定義。

---

## X-Z

### XGBoost (eXtreme Gradient Boosting)

勾配ブースティング決定木の実装。高性能で広く使用される機械学習アルゴリズム。

### YAML (YAML Ain't Markup Language)

人間が読みやすいデータシリアライゼーション形式。設定ファイルやGitHub Issueのパラメータ記述に使用。

### YOLOX (YOLO eXceeding YOLO series)

Anchor-freeアプローチを採用した物体検出モデル。YOLO系列の最新版で、6サイズ展開（Nano/Tiny/S/M/L/X）により
エッジデバイスからサーバーまで幅広い環境に対応。自動運転に必要な30FPS以上の推論速度を実現。

---

## 自動運転・コンピュータビジョン関連用語

### 3D AP (3D Average Precision)

3D物体検出の評価指標。KITTI データセットでEasy/Moderate/Hardの3段階難易度で計測される。

### Active Learning

機械学習モデルの不確実性が高いデータを優先的にラベリングする手法。ラベリングコストを削減しながら
モデル性能を効率的に向上させる。自動運転のEdge Case収集に有用。

### AirSim

Microsoft製のオープンソース自動運転・ドローンシミュレータ。Unreal Engineベースで高品質な視覚表現を提供。
カメラ、LiDAR、IMU等のセンサーシミュレーションが可能。

### BEV (Bird's Eye View)

鳥瞰図。カメラ画像やLiDAR点群を上空から見下ろした2D表現に変換したもの。自動運転では異なるセンサーデータを
統一的に扱うための中間表現として使用される（例: 200x200ピクセル、各ピクセル=0.5m）。

### BEVFormer

Transformerベースの手法でカメラ画像からBEV特徴マップを生成するアーキテクチャ。時系列情報も統合可能。

### CARLA (CAR Learning to Act)

オープンソースの自動運転シミュレータ。Unreal Engineベースで、町並み・交通・天候等をシミュレート可能。
Python APIを通じてセンサーデータ取得や車両制御が可能。強化学習の環境として広く使用される。

### Domain Adaptation

シミュレータ（ソースドメイン）で学習したモデルを実環境（ターゲットドメイン）に適応させる技術。
Adversarial Trainingにより、ドメイン不変な特徴量を学習する。

### Domain Randomization

シミュレータの環境パラメータ（照明、天候、車両モデル、テクスチャ等）をランダム化することで、
Sim-to-Real Gapを緩和する手法。実環境の多様性にロバストなモデルを学習可能。

### HSV Jitter

HSV色空間（Hue, Saturation, Value）の値をランダムに変化させるData Augmentation手法。
照明条件の変化に対するロバスト性を向上させる。

### Imitation Learning

模倣学習。人間の運転データ（状態-行動ペア）から学習する教師あり学習アプローチ。
強化学習に比べて学習が安定しやすいが、人間のミスも学習してしまう可能性がある。

### Incremental Learning

新規データで既存モデルをFine-tuningする継続学習手法。Catastrophic Forgetting（破壊的忘却）を避けながら
新しい知識を追加する。オンライン学習の一種。

### KITTI Vision Benchmark Suite

カールスルーエ工科大学とトヨタ・シカゴ技術研究所が公開する自動運転向けベンチマークデータセット。
3D物体検出、トラッキング、深度推定、Optical Flow等のタスクを提供。学習用7481枚、検証用7518枚の
カメラ画像とLiDAR点群を含む。

### LiDAR (Light Detection and Ranging)

レーザー測距センサー。レーザー光を照射し、反射光から距離を計測して3D点群データを生成する。
自動運転では360度の周囲環境を高精度に認識するために使用。データ形式は.bin、.pcd、.ply等。

### LSS (Lift-Splat-Shoot)

カメラ画像からBEV特徴マップを生成する手法。画像特徴を3D空間にLift（持ち上げ）し、BEV平面にSplat（投影）する。

### mAP (mean Average Precision)

物体検出の評価指標。各クラスのAverage Precision（AP）の平均値。mAP@0.5はIoU閾値0.5、
mAP@0.5:0.95はIoU閾値0.5～0.95（0.05刻み）の平均を表す。

### MixUp

2枚の画像とそのラベルを線形補間してブレンドするData Augmentation手法。
`mixed_image = λ * image1 + (1-λ) * image2` のように合成し、過学習を抑制する。

### Mosaic Augmentation

4枚の画像をモザイク状に結合するData Augmentation手法。YOLOXで使用され、小物体の検出性能向上に寄与する。
バッチサイズを疑似的に4倍にする効果もある。

### Optical Flow

連続フレーム間のピクセルの動きベクトル。動物体の検出や追跡、カメラの自己運動推定に使用される。

### Point Cloud

LiDARセンサーが生成する3D点群データ。各点は(x, y, z)座標と反射強度を持つ。
自動運転では点群から物体や地面を識別する。

### PointPillars

LiDAR点群ベースの3D物体検出アルゴリズム。点群をPillar（柱）単位にエンコードし、
2D畳み込みで高速処理を実現。

### Sim-to-Real Gap

シミュレータと実環境の差異。シミュレータで学習したモデルが実環境で性能低下する現象。
Domain Randomization、Domain Adaptation、Transfer Learningで緩和される。

### Temporal Fusion

過去N フレーム（N=3～10）の特徴量を時系列方向に統合する手法。LSTM、GRU、Transformerなどで実装される。
動物体の追跡や将来予測に有用。

### TensorRT

NVIDIA製の推論最適化エンジン。FP16/INT8量子化、カーネル融合、グラフ最適化により推論速度を2-10倍高速化。
ONNXモデルをTensorRTエンジンに変換して使用する。

### VAD (Vision-based Autonomous Driving)

カメラ画像を主センサーとする自動運転アプローチ。End-to-End学習により、画像から直接ステアリング・加減速を
出力する。模倣学習または強化学習で実現される。

### Voxelization

3D点群を3Dグリッド（Voxel：ボクセル）に変換する処理。点群の不規則な配置を規則的な3D配列に変換し、
3D畳み込みニューラルネットワークで処理可能にする。

---

## 参考資料

- [システム仕様書](../specifications/system_specification.md)
- [MCP設計書](../designs/mcp_design.md)
- [実装ガイド](../designs/implementation_guide.md)
- [Model Context Protocol 仕様](https://spec.modelcontextprotocol.io/)
- [AWS Documentation](https://docs.aws.amazon.com/)
- [Amazon SageMaker Documentation](https://docs.aws.amazon.com/sagemaker/)

---

## 変更履歴

| バージョン | 日付       | 変更内容                                           | 作成者 |
| ---------- | ---------- | -------------------------------------------------- | ------ |
| 1.0        | 2025-12-31 | 初版発行（用語集）                                 | -      |
| 1.1        | 2025-12-31 | 自動運転・コンピュータビジョン関連用語追加（26語） | -      |
