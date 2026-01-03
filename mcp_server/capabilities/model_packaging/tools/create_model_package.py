"""
Create Model Package Tool

モデルパッケージ作成ツール
"""

import json
import logging
import tarfile
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def create_model_package(
    model_s3_uri: str,
    package_name: str,
    framework: str = "sklearn",
    python_version: str = "3.11",
    dependencies: Dict[str, str] = None,
    output_s3_uri: str = None,
) -> Dict[str, Any]:
    """
    モデルパッケージを作成

    Args:
        model_s3_uri: モデルのS3 URI (.pkl)
        package_name: パッケージ名
        framework: フレームワーク (sklearn, tensorflow, pytorch)
        python_version: Pythonバージョン
        dependencies: 依存パッケージ辞書 {package: version}
        output_s3_uri: 出力先S3 URI (省略時は model_s3_uri と同じバケット)

    Returns:
        パッケージ作成結果辞書
    """
    logger.info(f"Creating model package: {package_name}")

    # S3 URIのバリデーション
    if not model_s3_uri.startswith("s3://"):
        raise ValueError("Invalid S3 URI: must start with 's3://'")

    model_parts = model_s3_uri[5:].split("/", 1)
    if len(model_parts) != 2:
        raise ValueError("Invalid S3 URI format: s3://bucket/key required")

    # デフォルト値の設定
    if dependencies is None:
        dependencies = _get_default_dependencies(framework)

    # S3クライアント
    s3_client = boto3.client("s3")

    model_bucket, model_key = model_parts

    # モデルファイルの存在確認
    try:
        s3_client.head_object(Bucket=model_bucket, Key=model_key)
        logger.info(f"Verified model exists at {model_s3_uri}")

    except ClientError as e:
        logger.error(f"S3 access error for model: {e}")
        raise ValueError(f"Model not found at S3 URI: {model_s3_uri}")

    # 一時ディレクトリでパッケージを作成
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        package_dir = tmp_path / package_name

        # パッケージ構造を作成
        _create_package_structure(
            package_dir, model_s3_uri, framework, python_version, dependencies
        )

        # tar.gzに圧縮
        package_file = tmp_path / f"{package_name}.tar.gz"
        _create_tarball(package_dir, package_file)

        # S3にアップロード
        if output_s3_uri is None:
            output_key = f"{model_key.rsplit('/', 1)[0]}/{package_name}.tar.gz"
            output_s3_uri = f"s3://{model_bucket}/{output_key}"
        else:
            if not output_s3_uri.startswith("s3://"):
                raise ValueError("Invalid output S3 URI: must start with 's3://'")

            output_parts = output_s3_uri[5:].split("/", 1)
            if len(output_parts) != 2:
                raise ValueError("Invalid output S3 URI format")

            output_bucket, output_key = output_parts
            model_bucket = output_bucket

        try:
            s3_client.upload_file(str(package_file), model_bucket, output_key)
            logger.info(f"Uploaded package to {output_s3_uri}")

        except ClientError as e:
            logger.error(f"Failed to upload package: {e}")
            raise ValueError(f"Failed to upload package: {e}")

    # パッケージメタデータを作成
    metadata = {
        "package_name": package_name,
        "framework": framework,
        "python_version": python_version,
        "dependencies": dependencies,
        "model_s3_uri": model_s3_uri,
        "package_s3_uri": output_s3_uri,
        "created_at": datetime.utcnow().isoformat(),
    }

    # メタデータもS3に保存
    metadata_key = f"{output_key.rsplit('.', 1)[0]}_metadata.json"
    try:
        metadata_json = json.dumps(metadata, indent=2)
        s3_client.put_object(
            Bucket=model_bucket, Key=metadata_key, Body=metadata_json.encode("utf-8")
        )
        logger.info(f"Saved package metadata to s3://{model_bucket}/{metadata_key}")

    except ClientError as e:
        logger.warning(f"Failed to save metadata: {e}")

    logger.info(f"Package created successfully: {package_name}")

    return {
        "status": "success",
        "message": "Model package created successfully",
        "package_info": {
            "package_name": package_name,
            "package_s3_uri": output_s3_uri,
            "metadata_s3_uri": f"s3://{model_bucket}/{metadata_key}",
            "framework": framework,
            "python_version": python_version,
            "dependencies": dependencies,
        },
    }


def _get_default_dependencies(framework: str) -> Dict[str, str]:
    """フレームワークに応じたデフォルト依存パッケージを取得"""
    defaults = {
        "sklearn": {
            "scikit-learn": "1.3.2",
            "pandas": "2.1.4",
            "numpy": "1.26.2",
        },
        "tensorflow": {
            "tensorflow": "2.15.0",
            "numpy": "1.26.2",
        },
        "pytorch": {
            "torch": "2.1.2",
            "numpy": "1.26.2",
        },
    }

    return defaults.get(framework, {"scikit-learn": "1.3.2"})


def _create_package_structure(
    package_dir: Path,
    model_s3_uri: str,
    framework: str,
    python_version: str,
    dependencies: Dict[str, str],
) -> None:
    """パッケージディレクトリ構造を作成"""
    package_dir.mkdir(parents=True, exist_ok=True)

    # requirements.txt
    requirements = package_dir / "requirements.txt"
    with requirements.open("w") as f:
        for pkg, version in dependencies.items():
            f.write(f"{pkg}=={version}\n")

    # config.json
    config = {
        "model_s3_uri": model_s3_uri,
        "framework": framework,
        "python_version": python_version,
        "entrypoint": "inference.py",
    }

    config_file = package_dir / "config.json"
    with config_file.open("w") as f:
        json.dump(config, f, indent=2)

    # inference.py (シンプルな推論スクリプト)
    inference_script = package_dir / "inference.py"
    inference_code = _generate_inference_script(framework)
    with inference_script.open("w") as f:
        f.write(inference_code)

    logger.info(f"Created package structure at {package_dir}")


def _generate_inference_script(framework: str) -> str:
    """推論スクリプトを生成"""
    template = '''"""
Inference Script

自動生成された推論スクリプト
"""

import json
import os
import joblib
import boto3


def load_model():
    """モデルをロード"""
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path, "r") as f:
        config = json.load(f)

    model_s3_uri = config["model_s3_uri"]
    bucket, key = model_s3_uri[5:].split("/", 1)

    s3_client = boto3.client("s3")
    response = s3_client.get_object(Bucket=bucket, Key=key)
    model_content = response["Body"].read()

    import io
    model = joblib.load(io.BytesIO(model_content))
    return model


def predict(model, input_data):
    """予測を実行"""
    import pandas as pd

    # 入力データをDataFrameに変換
    if isinstance(input_data, dict):
        df = pd.DataFrame([input_data])
    elif isinstance(input_data, list):
        df = pd.DataFrame(input_data)
    else:
        df = input_data

    # 予測
    predictions = model.predict(df)

    return predictions.tolist()


if __name__ == "__main__":
    # テスト実行
    model = load_model()
    print("Model loaded successfully")

    # サンプル予測（実際の入力に合わせて変更）
    sample_input = {"feature1": 1.0, "feature2": 2.0}
    result = predict(model, sample_input)
    print(f"Prediction: {result}")
'''
    return template


def _create_tarball(source_dir: Path, output_file: Path) -> None:
    """ディレクトリをtar.gzに圧縮"""
    with tarfile.open(output_file, "w:gz") as tar:
        tar.add(source_dir, arcname=source_dir.name)

    logger.info(f"Created tarball: {output_file}")
