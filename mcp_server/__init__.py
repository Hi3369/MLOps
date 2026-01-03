"""
MLOps Integrated MCP Server

統合MLOpsサーバーは、MLOpsパイプラインの全専門機能を
単一のMCPサーバーとして提供します。

提供Capabilities (12個):
1. GitHub Integration - GitHub Issue検知・パース・ワークフロー起動
2. Workflow Optimization - モデル特性分析・最適化提案
3. Data Preparation - データ前処理・特徴量エンジニアリング
4. ML Training - モデル学習（教師あり/教師なし/強化学習）
5. ML Evaluation - モデル評価・メトリクス計算・可視化
6. Model Packaging - モデルコンテナ化・ECR登録
7. Model Deployment - モデルデプロイ・エンドポイント管理
8. Model Monitoring - パフォーマンス監視・ドリフト検出
9. Retrain Management - 再学習トリガー判定・ワークフロー起動
10. Notification - 通知管理（Slack/Email/GitHub）
11. History Management - 学習履歴記録・GitHub連携
12. Model Registry - モデル登録・バージョン管理
"""

__version__ = "0.1.0"
__all__ = ["MLOpsServer"]

from .server import MLOpsServer
