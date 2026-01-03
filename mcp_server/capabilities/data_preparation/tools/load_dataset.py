"""
Load Dataset Tool

S3からデータセットを読み込むツール
"""

import io
import logging
from typing import Any, Dict

import boto3
import pandas as pd
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def load_dataset(s3_uri: str, file_format: str = "csv") -> Dict[str, Any]:
    """
    S3からデータセットを読み込む

    Args:
        s3_uri: S3 URI (例: s3://bucket-name/path/to/file.csv)
        file_format: ファイルフォーマット (csv, parquet, json)

    Returns:
        読み込んだデータセット情報

    Raises:
        ValueError: 無効なS3 URIまたはファイルフォーマット
        ClientError: S3アクセスエラー
    """
    logger.info(f"Loading dataset from {s3_uri} (format: {file_format})")

    # S3 URIをパース
    if not s3_uri.startswith("s3://"):
        raise ValueError(f"Invalid S3 URI: {s3_uri}. Must start with 's3://'")

    # s3://bucket/key の形式をパース
    parts = s3_uri[5:].split("/", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid S3 URI format: {s3_uri}")

    bucket, key = parts

    try:
        # S3からデータを読み込み
        s3_client = boto3.client("s3")
        response = s3_client.get_object(Bucket=bucket, Key=key)
        file_content = response["Body"].read()

        # ファイルフォーマットに応じて読み込み
        if file_format.lower() == "csv":
            df = pd.read_csv(io.BytesIO(file_content))
        elif file_format.lower() == "parquet":
            df = pd.read_parquet(io.BytesIO(file_content))
        elif file_format.lower() == "json":
            df = pd.read_json(io.BytesIO(file_content))
        else:
            raise ValueError(
                f"Unsupported file format: {file_format}. "
                f"Supported formats: csv, parquet, json"
            )

        # データセット情報を収集
        dataset_info = {
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": df.columns.tolist(),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "memory_usage_mb": df.memory_usage(deep=True).sum() / 1024 / 1024,
            "missing_values": df.isnull().sum().to_dict(),
        }

        logger.info(
            f"Successfully loaded dataset: {dataset_info['rows']} rows, "
            f"{dataset_info['columns']} columns"
        )

        return {
            "status": "success",
            "message": f"Dataset loaded from {s3_uri}",
            "s3_uri": s3_uri,
            "bucket": bucket,
            "key": key,
            "file_format": file_format,
            "dataset_info": dataset_info,
            # データ本体は返さない（大きすぎる可能性があるため）
            # 必要に応じて別のツールでアクセス
        }

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]
        logger.error(f"S3 access error: {error_code} - {error_message}")
        raise

    except Exception as e:
        logger.error(f"Failed to load dataset: {str(e)}", exc_info=True)
        raise
