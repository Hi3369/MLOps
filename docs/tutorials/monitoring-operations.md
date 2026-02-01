# 監視・運用チュートリアル

モデルデプロイから監視・ドリフト検出・再学習トリガーまでの運用フローを構築する。

## 運用フロー概要

```text
デプロイ → ヘルスチェック → 監視設定 → ドリフト検出 → アラート → 再学習判定
```

## Step 1: サーバー初期化

```python
import os
os.environ["MLOPS_ENV"] = "development"

from mcp_server.server import MLOpsServer
server = MLOpsServer()
```

## Step 2: モデルデプロイ

### 2.1 SageMakerエンドポイント作成

```python
deploy_result = server.call_tool(
    "model_deployment.deploy_to_sagemaker",
    {
        "model_s3_uri": "s3://mlops-models/iris-classifier/model.tar.gz",
        "endpoint_name": "iris-classifier-prod",
        "instance_type": "ml.t3.medium",
        "instance_count": 1,
    }
)
endpoint = deploy_result["result"]["deployment_info"]
print(f"エンドポイント: {endpoint['endpoint_name']}")
print(f"ステータス: {endpoint['status']}")
```

### 2.2 ヘルスチェック

```python
health_result = server.call_tool(
    "model_deployment.health_check_endpoint",
    {"endpoint_name": "iris-classifier-prod"}
)
print(f"ヘルス: {health_result['result']['health_info']['status']}")
```

### 2.3 オートスケーリング設定

```python
server.call_tool(
    "model_deployment.configure_autoscaling",
    {
        "endpoint_name": "iris-classifier-prod",
        "min_capacity": 1,
        "max_capacity": 4,
        "target_value": 70.0,
    }
)
```

## Step 3: 監視設定

### 3.1 CloudWatchダッシュボード作成

```python
server.call_tool(
    "model_monitoring.create_monitoring_dashboard",
    {
        "dashboard_name": "iris-classifier-dashboard",
        "endpoint_name": "iris-classifier-prod",
    }
)
```

### 3.2 アラーム作成

```python
# レイテンシアラーム
server.call_tool(
    "model_monitoring.create_cloudwatch_alarm",
    {
        "alarm_name": "iris-high-latency",
        "endpoint_name": "iris-classifier-prod",
        "metric_name": "ModelLatency",
        "threshold": 1000.0,
        "comparison_operator": "GreaterThanThreshold",
        "evaluation_periods": 3,
    }
)

# エラー率アラーム
server.call_tool(
    "model_monitoring.create_cloudwatch_alarm",
    {
        "alarm_name": "iris-high-error-rate",
        "endpoint_name": "iris-classifier-prod",
        "metric_name": "Invocation5XXErrors",
        "threshold": 5.0,
        "comparison_operator": "GreaterThanThreshold",
    }
)
```

### 3.3 メトリクス収集

```python
# システムメトリクス（CPU, メモリ等）
sys_result = server.call_tool(
    "model_monitoring.collect_system_metrics",
    {"endpoint_name": "iris-classifier-prod", "time_range_minutes": 60}
)

# モデルメトリクス（レイテンシ, 呼び出し数等）
model_result = server.call_tool(
    "model_monitoring.collect_model_metrics",
    {"endpoint_name": "iris-classifier-prod", "time_range_minutes": 60}
)
```

## Step 4: ドリフト検出

### 4.1 データドリフト検出

```python
drift_result = server.call_tool(
    "model_monitoring.detect_data_drift",
    {
        "baseline_data": {
            "sepal_length": [5.1, 4.9, 4.7, 5.0, 5.4],
            "sepal_width": [3.5, 3.0, 3.2, 3.6, 3.9],
        },
        "current_data": {
            "sepal_length": [6.1, 5.9, 6.7, 6.0, 6.4],
            "sepal_width": [2.5, 2.0, 2.2, 2.6, 2.9],
        },
        "drift_threshold": 0.05,
        "method": "ks_test",
    }
)
drift_info = drift_result["result"]["drift_info"]
print(f"ドリフト検出: {drift_info['drift_detected']}")
for feat, detail in drift_info["feature_drift"].items():
    print(f"  {feat}: p-value={detail['p_value']:.4f}")
```

### 4.2 コンセプトドリフト検出

```python
concept_result = server.call_tool(
    "model_monitoring.detect_concept_drift",
    {
        "predictions": [0, 1, 1, 0, 1, 0, 0, 1, 1, 0],
        "actual_labels": [0, 1, 0, 0, 1, 1, 0, 0, 1, 0],
        "window_size": 5,
        "drift_threshold": 0.1,
    }
)
print(f"コンセプトドリフト: {concept_result['result']['drift_info']['drift_detected']}")
```

## Step 5: 通知

### 5.1 ドリフト検出時の通知

```python
if drift_info["drift_detected"]:
    # Slack通知
    server.call_tool(
        "notification.send_slack_notification",
        {
            "message": "Data drift detected on iris-classifier-prod",
            "channel": "#mlops-alerts",
        }
    )

    # GitHub Issue通知
    server.call_tool(
        "notification.send_github_notification",
        {
            "repo_owner": "my-org",
            "repo_name": "mlops-models",
            "notification_type": "issue_comment",
            "target_number": 42,
            "message": "Data drift detected. Retraining may be required.",
        }
    )
```

## Step 6: 再学習判定

### 6.1 トリガー条件評価

```python
trigger_result = server.call_tool(
    "retrain_management.check_retrain_triggers",
    {
        "model_name": "iris-classifier",
        "trigger_config": {
            "drift_threshold": 0.05,
            "performance_threshold": 0.85,
            "max_age_days": 30,
        },
    }
)
print(f"再学習必要: {trigger_result['result']['trigger_info']['should_retrain']}")
```

### 6.2 再学習ワークフロー起動

```python
if trigger_result["result"]["trigger_info"]["should_retrain"]:
    server.call_tool(
        "retrain_management.start_retrain_workflow",
        {
            "workflow_name": "iris-retrain",
            "model_config": {
                "algorithm": "random_forest",
                "hyperparameters": {"n_estimators": 100},
            },
            "dataset_uri": "s3://mlops-data/iris/latest.csv",
        }
    )
```

## Step 7: ロールバック（障害時）

```python
# エンドポイントのロールバック
server.call_tool(
    "model_deployment.rollback_deployment",
    {
        "endpoint_name": "iris-classifier-prod",
        "previous_config_name": "iris-classifier-config-v1",
    }
)
```

## 運用で使用する Capability

| # | Capability | 用途 |
|---|-----------|------|
| 1 | model_deployment | デプロイ・スケーリング・ロールバック |
| 2 | model_monitoring | メトリクス収集・ドリフト検出・アラーム |
| 3 | notification | Slack/Email/GitHub通知 |
| 4 | retrain_management | 再学習トリガー・ワークフロー起動 |
| 5 | history_management | 履歴記録・GitHub連携 |

## 次のステップ

- [API仕様書](../api/model_deployment.md) - デプロイツール詳細
- [API仕様書](../api/model_monitoring.md) - 監視ツール詳細
- [トラブルシューティング](../troubleshooting.md) - よくある問題と解決策
