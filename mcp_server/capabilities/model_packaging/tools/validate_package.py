"""
Validate Package Tool

パッケージ検証ツール
"""

import io
import json
import logging
import tarfile
import tempfile
from pathlib import Path
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def validate_package(
    package_s3_uri: str,
) -> Dict[str, Any]:
    """
    モデルパッケージを検証

    Args:
        package_s3_uri: パッケージのS3 URI (.tar.gz)

    Returns:
        検証結果辞書
    """
    logger.info(f"Validating package: {package_s3_uri}")

    # S3 URIのバリデーション
    if not package_s3_uri.startswith("s3://"):
        raise ValueError("Invalid S3 URI: must start with 's3://'")

    package_parts = package_s3_uri[5:].split("/", 1)
    if len(package_parts) != 2:
        raise ValueError("Invalid S3 URI format: s3://bucket/key required")

    # S3クライアント
    s3_client = boto3.client("s3")

    package_bucket, package_key = package_parts

    # パッケージファイルをダウンロード
    try:
        response = s3_client.get_object(Bucket=package_bucket, Key=package_key)
        package_content = response["Body"].read()
        logger.info(f"Downloaded package from {package_s3_uri}")

    except ClientError as e:
        logger.error(f"S3 access error: {e}")
        raise ValueError(f"Package not found at S3 URI: {package_s3_uri}")

    # 一時ディレクトリで展開・検証
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # tar.gzを展開
        try:
            with tarfile.open(fileobj=io.BytesIO(package_content), mode="r:gz") as tar:
                tar.extractall(tmp_path)

            logger.info("Package extracted successfully")

        except (tarfile.TarError, Exception) as e:
            logger.error(f"Failed to extract package: {e}")
            return {
                "status": "error",
                "message": f"Failed to extract package: {e}",
                "validation_results": {
                    "is_valid": False,
                    "errors": [f"Package extraction failed: {e}"],
                },
            }

        # パッケージ内容を検証
        validation_results = _validate_package_contents(tmp_path)

    logger.info("Package validation completed")

    return {
        "status": "success",
        "message": "Package validation completed",
        "validation_results": validation_results,
    }


def _validate_package_contents(package_dir: Path) -> Dict[str, Any]:
    """パッケージ内容を検証"""
    errors = []
    warnings = []
    files_found = []

    # パッケージ内のディレクトリを探す
    subdirs = [d for d in package_dir.iterdir() if d.is_dir()]

    if not subdirs:
        errors.append("No package directory found in archive")
        return {
            "is_valid": False,
            "errors": errors,
            "warnings": warnings,
            "files_found": files_found,
        }

    # 最初のディレクトリをパッケージルートとする
    pkg_root = subdirs[0]

    # 必須ファイルの確認
    required_files = {
        "requirements.txt": False,
        "config.json": False,
        "inference.py": False,
    }

    for file_name in required_files.keys():
        file_path = pkg_root / file_name
        if file_path.exists():
            required_files[file_name] = True
            files_found.append(file_name)
        else:
            errors.append(f"Required file not found: {file_name}")

    # config.jsonの検証
    config_path = pkg_root / "config.json"
    if config_path.exists():
        try:
            with config_path.open("r") as f:
                config = json.load(f)

            # 必須フィールドの確認
            required_fields = ["model_s3_uri", "framework", "entrypoint"]
            for field in required_fields:
                if field not in config:
                    errors.append(f"Required config field missing: {field}")

            # model_s3_uriの検証
            if "model_s3_uri" in config:
                if not config["model_s3_uri"].startswith("s3://"):
                    errors.append("Invalid model_s3_uri in config.json")

        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON in config.json: {e}")

    # requirements.txtの検証
    requirements_path = pkg_root / "requirements.txt"
    if requirements_path.exists():
        try:
            with requirements_path.open("r") as f:
                requirements = f.readlines()

            if len(requirements) == 0:
                warnings.append("requirements.txt is empty")

            # 基本的な構文チェック
            for i, line in enumerate(requirements, 1):
                line = line.strip()
                if line and not line.startswith("#"):
                    if "==" not in line and not line.startswith("-"):
                        warnings.append(f"Line {i} in requirements.txt may be invalid: {line}")

        except Exception as e:
            errors.append(f"Failed to read requirements.txt: {e}")

    # inference.pyの検証
    inference_path = pkg_root / "inference.py"
    if inference_path.exists():
        try:
            with inference_path.open("r") as f:
                inference_code = f.read()

            # 基本的な関数の存在確認
            if "def load_model" not in inference_code:
                warnings.append("load_model function not found in inference.py")

            if "def predict" not in inference_code:
                warnings.append("predict function not found in inference.py")

        except Exception as e:
            errors.append(f"Failed to read inference.py: {e}")

    # 検証結果の集計
    is_valid = len(errors) == 0

    return {
        "is_valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "files_found": files_found,
        "required_files": required_files,
    }
