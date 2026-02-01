# Model Deployment Capability

SageMaker エンドポイントへのデプロイ・管理を担当する Capability。

## ツール一覧

| ツール名 | 説明 |
|---------|------|
| `deploy_to_sagemaker` | SageMakerエンドポイントにデプロイ |
| `update_endpoint_traffic` | トラフィック配分を更新 |
| `update_endpoint_capacity` | インスタンス数を更新 |
| `configure_autoscaling` | オートスケーリングを設定 |
| `delete_autoscaling` | オートスケーリングを削除 |
| `monitor_endpoint` | エンドポイントを監視 |
| `health_check_endpoint` | ヘルスチェック実行 |
| `delete_endpoint` | エンドポイントを削除 |
| `rollback_deployment` | デプロイをロールバック |

## ツール詳細

### deploy_to_sagemaker

SageMakerエンドポイントにモデルをデプロイする。

```python
deploy_to_sagemaker(
    model_s3_uri: str,
    endpoint_name: str,
    instance_type: str = "ml.t3.medium",
    instance_count: int = 1,
    model_name: str = None,
    wait_for_completion: bool = True,
) -> Dict[str, Any]
```

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|---|:---:|----------|------|
| model_s3_uri | str | o | - | モデルのS3 URI |
| endpoint_name | str | o | - | エンドポイント名 |
| instance_type | str | | "ml.t3.medium" | インスタンスタイプ |
| instance_count | int | | 1 | インスタンス数 |
| model_name | str | | None | モデル名 |
| wait_for_completion | bool | | True | 完了まで待機 |

---

### update_endpoint_traffic

エンドポイントのトラフィック配分を更新する（カナリアデプロイ/A/Bテスト）。

```python
update_endpoint_traffic(
    endpoint_name: str,
    variant_weights: Dict[str, float],
) -> Dict[str, Any]
```

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|---|:---:|----------|------|
| endpoint_name | str | o | - | エンドポイント名 |
| variant_weights | Dict[str, float] | o | - | バリアント別ウェイト（例: {"v1": 0.7, "v2": 0.3}） |

---

### update_endpoint_capacity

エンドポイントのインスタンス数を更新する。

```python
update_endpoint_capacity(
    endpoint_name: str,
    variant_name: str,
    instance_count: int,
) -> Dict[str, Any]
```

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|---|:---:|----------|------|
| endpoint_name | str | o | - | エンドポイント名 |
| variant_name | str | o | - | バリアント名 |
| instance_count | int | o | - | インスタンス数 |

---

### configure_autoscaling

エンドポイントのオートスケーリングを設定する。

```python
configure_autoscaling(
    endpoint_name: str,
    variant_name: str = "AllTraffic",
    min_capacity: int = 1,
    max_capacity: int = 4,
    target_metric: str = "SageMakerVariantInvocationsPerInstance",
    target_value: float = 70.0,
    scale_in_cooldown: int = 300,
    scale_out_cooldown: int = 60,
) -> Dict[str, Any]
```

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|---|:---:|----------|------|
| endpoint_name | str | o | - | エンドポイント名 |
| variant_name | str | | "AllTraffic" | バリアント名 |
| min_capacity | int | | 1 | 最小インスタンス数 |
| max_capacity | int | | 4 | 最大インスタンス数 |
| target_metric | str | | "SageMaker...Instance" | ターゲットメトリクス |
| target_value | float | | 70.0 | ターゲット値 |
| scale_in_cooldown | int | | 300 | スケールインクールダウン（秒） |
| scale_out_cooldown | int | | 60 | スケールアウトクールダウン（秒） |

---

### delete_autoscaling

エンドポイントのオートスケーリング設定を削除する。

```python
delete_autoscaling(
    endpoint_name: str,
    variant_name: str = "AllTraffic",
) -> Dict[str, Any]
```

---

### monitor_endpoint

エンドポイントのステータスとメトリクスを監視する。

```python
monitor_endpoint(
    endpoint_name: str,
    include_metrics: bool = True,
    metric_period_minutes: int = 60,
) -> Dict[str, Any]
```

---

### health_check_endpoint

エンドポイントのヘルスチェックを実行する。

```python
health_check_endpoint(
    endpoint_name: str,
    test_payload: Dict[str, Any] = None,
) -> Dict[str, Any]
```

---

### delete_endpoint

エンドポイントを削除する。

```python
delete_endpoint(
    endpoint_name: str,
    delete_endpoint_config: bool = True,
    delete_model: bool = False,
    force: bool = False,
) -> Dict[str, Any]
```

---

### rollback_deployment

デプロイメントをロールバックする。

```python
rollback_deployment(
    endpoint_name: str,
    previous_config_name: str = None,
) -> Dict[str, Any]
```
