# Model Packaging Capability

モデルのコンテナ化・ECR登録を担当する Capability。

## ツール一覧

| ツール名 | 説明 |
|---------|------|
| `extract_model_metadata` | モデルからメタデータを抽出 |
| `create_dockerfile` | モデル用Dockerfileを生成 |
| `create_model_package` | モデルパッケージを作成 |
| `generate_deployment_config` | デプロイ設定を生成 |
| `validate_package` | モデルパッケージを検証 |

## ツール詳細

### extract_model_metadata

モデルからメタデータを抽出する。

```python
extract_model_metadata(
    model_s3_uri: str,
) -> Dict[str, Any]
```

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|---|:---:|----------|------|
| model_s3_uri | str | o | - | モデルのS3 URI |

---

### create_dockerfile

モデル用のDockerfileを生成する。

```python
create_dockerfile(
    model_s3_uri: str,
    framework: str = "sklearn",
    python_version: str = "3.11",
    base_image: str = None,
    optimize: bool = True,
) -> Dict[str, Any]
```

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|---|:---:|----------|------|
| model_s3_uri | str | o | - | モデルのS3 URI |
| framework | str | | "sklearn" | フレームワーク（sklearn/pytorch/tensorflow） |
| python_version | str | | "3.11" | Pythonバージョン |
| base_image | str | | None | ベースDockerイメージ |
| optimize | bool | | True | イメージ最適化 |

---

### create_model_package

モデルパッケージを作成する。

```python
create_model_package(
    model_s3_uri: str,
    package_name: str,
    framework: str = "sklearn",
    python_version: str = "3.11",
    dependencies: Dict[str, str] = None,
    output_s3_uri: str = None,
) -> Dict[str, Any]
```

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|---|:---:|----------|------|
| model_s3_uri | str | o | - | モデルのS3 URI |
| package_name | str | o | - | パッケージ名 |
| framework | str | | "sklearn" | フレームワーク |
| python_version | str | | "3.11" | Pythonバージョン |
| dependencies | Dict | | None | 追加依存関係 |
| output_s3_uri | str | | None | 出力先S3 URI |

---

### generate_deployment_config

デプロイ設定を生成する。

```python
generate_deployment_config(
    model_s3_uri: str,
    deployment_type: str = "sagemaker",
    instance_type: str = "ml.t3.medium",
    instance_count: int = 1,
    auto_scaling: bool = False,
) -> Dict[str, Any]
```

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|---|:---:|----------|------|
| model_s3_uri | str | o | - | モデルのS3 URI |
| deployment_type | str | | "sagemaker" | デプロイ先 |
| instance_type | str | | "ml.t3.medium" | インスタンスタイプ |
| instance_count | int | | 1 | インスタンス数 |
| auto_scaling | bool | | False | オートスケーリング有効化 |

---

### validate_package

モデルパッケージを検証する。

```python
validate_package(
    package_s3_uri: str,
) -> Dict[str, Any]
```

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|---|:---:|----------|------|
| package_s3_uri | str | o | - | パッケージのS3 URI |
