"""
Save Training History Tool

学習履歴保存ツール
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


def save_training_history(
    training_job_name: str,
    formatted_history: str,
    storage_type: str = "s3",
    s3_bucket: Optional[str] = None,
    s3_prefix: str = "training_history/",
    local_path: Optional[str] = None,
    file_format: str = "md",
) -> Dict[str, Any]:
    """
    フォーマット済み履歴をストレージに保存

    Args:
        training_job_name: 学習ジョブ名
        formatted_history: フォーマット済み履歴コンテンツ
        storage_type: ストレージタイプ（s3, local）
        s3_bucket: S3バケット名
        s3_prefix: S3プレフィックス
        local_path: ローカル保存パス
        file_format: ファイル形式（md, json, txt）

    Returns:
        保存結果辞書
    """
    logger.info(f"Saving training history for job: {training_job_name}")

    # パラメータ検証
    if not training_job_name:
        raise ValueError("training_job_name must not be empty")

    if not formatted_history:
        raise ValueError("formatted_history must not be empty")

    if storage_type not in ["s3", "local"]:
        raise ValueError(f"Invalid storage_type: {storage_type}")

    if file_format not in ["md", "json", "txt"]:
        raise ValueError(f"Invalid file_format: {file_format}")

    try:
        timestamp = datetime.now(timezone.utc)
        timestamp_str = timestamp.strftime("%Y-%m-%d_%H-%M-%S")
        save_id = str(uuid4())[:8]

        # ファイル名生成
        filename = f"{timestamp_str}_{training_job_name}.{file_format}"

        env = os.environ.get("MLOPS_ENV", "development")

        if storage_type == "s3":
            result = _save_to_s3(
                formatted_history=formatted_history,
                bucket=s3_bucket or os.environ.get("MLOPS_HISTORY_BUCKET"),
                prefix=s3_prefix,
                filename=filename,
                env=env,
            )
        else:
            result = _save_to_local(
                formatted_history=formatted_history,
                local_path=local_path or "/tmp/training_history",
                filename=filename,
                env=env,
            )

        logger.info(f"Training history saved successfully: {save_id}")

        return {
            "status": "success",
            "message": f"Training history saved to {storage_type}",
            "save_result": {
                "save_id": save_id,
                "training_job_name": training_job_name,
                "storage_type": storage_type,
                "location": result["location"],
                "filename": filename,
                "timestamp": timestamp.isoformat(),
                "mock": result.get("mock", False),
            },
        }

    except Exception as e:
        logger.error(f"Failed to save training history: {e}")
        raise ValueError(f"Failed to save training history: {e}")


def _save_to_s3(
    formatted_history: str,
    bucket: Optional[str],
    prefix: str,
    filename: str,
    env: str,
) -> Dict[str, Any]:
    """S3に保存"""

    # 開発/テスト環境ではモック
    if env in ["development", "test"] or not bucket:
        logger.info("Using mock S3 save (dev/test environment)")
        mock_bucket = bucket or "mock-history-bucket"
        return {
            "location": f"s3://{mock_bucket}/{prefix}{filename}",
            "mock": True,
        }

    # 本番環境：実際にS3に保存
    import boto3
    from botocore.exceptions import ClientError

    try:
        s3_client = boto3.client("s3")
        key = f"{prefix}{filename}"

        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=formatted_history.encode("utf-8"),
            ContentType="text/plain; charset=utf-8",
        )

        return {
            "location": f"s3://{bucket}/{key}",
            "mock": False,
        }

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        raise ValueError(f"S3 error ({error_code}): {e}")


def _save_to_local(
    formatted_history: str,
    local_path: str,
    filename: str,
    env: str,
) -> Dict[str, Any]:
    """ローカルに保存"""

    # 開発/テスト環境ではモック
    if env in ["development", "test"]:
        logger.info("Using mock local save (dev/test environment)")
        return {
            "location": f"{local_path}/{filename}",
            "mock": True,
        }

    # 本番環境：実際にファイルを保存
    os.makedirs(local_path, exist_ok=True)
    full_path = os.path.join(local_path, filename)

    with open(full_path, "w", encoding="utf-8") as f:
        f.write(formatted_history)

    return {
        "location": full_path,
        "mock": False,
    }
