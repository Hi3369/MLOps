"""
Log Parameters Tool

実験パラメータ記録ツール
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def log_parameters(
    experiment_id: str,
    parameters: Dict[str, Any],
    run_name: Optional[str] = None,
    step: Optional[int] = None,
) -> Dict[str, Any]:
    """
    実験にパラメータを記録する

    Args:
        experiment_id: 実験ID
        parameters: 記録するパラメータ辞書
        run_name: 実行名（省略時は自動生成）
        step: ステップ番号

    Returns:
        パラメータ記録結果辞書
    """
    logger.info(f"Logging parameters for experiment: {experiment_id}")

    # パラメータ検証
    if not experiment_id:
        raise ValueError("experiment_id must not be empty")

    if not parameters:
        raise ValueError("parameters must not be empty")

    if not isinstance(parameters, dict):
        raise ValueError("parameters must be a dictionary")

    # パラメータ値の型検証
    for key, value in parameters.items():
        if not isinstance(key, str):
            raise ValueError(f"Parameter key must be a string, got {type(key)}")
        if not isinstance(value, (str, int, float, bool, list)):
            raise ValueError(
                f"Parameter value for '{key}' must be str, int, float, "
                f"bool, or list, got {type(value)}"
            )

    if step is not None and step < 0:
        raise ValueError("step must be a non-negative integer")

    try:
        env = os.environ.get("MLOPS_ENV", "development")
        timestamp = datetime.now(timezone.utc).isoformat()
        log_id = str(uuid4())[:8]

        if run_name is None:
            run_name = f"run-{log_id}"

        # 開発/テスト環境ではモック
        if env in ["development", "test"]:
            return _mock_log_parameters(
                experiment_id=experiment_id,
                parameters=parameters,
                run_name=run_name,
                step=step,
                log_id=log_id,
                timestamp=timestamp,
            )

        # 本番環境: S3 + SageMaker
        return _real_log_parameters(
            experiment_id=experiment_id,
            parameters=parameters,
            run_name=run_name,
            step=step,
            log_id=log_id,
            timestamp=timestamp,
        )

    except ClientError as e:
        logger.error(f"AWS error logging parameters: {e}")
        raise ValueError(f"Failed to log parameters: {e}")
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Failed to log parameters: {e}")
        raise ValueError(f"Failed to log parameters: {e}")


def _mock_log_parameters(
    experiment_id: str,
    parameters: Dict[str, Any],
    run_name: str,
    step: Optional[int],
    log_id: str,
    timestamp: str,
) -> Dict[str, Any]:
    """モックパラメータ記録（開発・テスト用）"""
    logger.info("Using mock parameter logging")

    return {
        "status": "success",
        "message": f"Parameters logged for experiment: {experiment_id}",
        "parameter_info": {
            "log_id": f"param-{log_id}",
            "experiment_id": experiment_id,
            "run_name": run_name,
            "parameters": parameters,
            "parameter_count": len(parameters),
            "step": step,
            "logged_at": timestamp,
            "mock": True,
        },
    }


def _real_log_parameters(
    experiment_id: str,
    parameters: Dict[str, Any],
    run_name: str,
    step: Optional[int],
    log_id: str,
    timestamp: str,
) -> Dict[str, Any]:
    """本番パラメータ記録（SageMaker Experiments + S3）"""
    import json

    s3_client = boto3.client("s3")
    bucket = os.environ.get("MLOPS_EXPERIMENT_BUCKET", "mlops-experiments")

    # パラメータデータ
    param_data = {
        "log_id": f"param-{log_id}",
        "experiment_id": experiment_id,
        "run_name": run_name,
        "parameters": parameters,
        "parameter_count": len(parameters),
        "step": step,
        "logged_at": timestamp,
    }

    # S3に保存
    s3_key = f"experiments/{experiment_id}/parameters/{run_name}/{log_id}.json"
    s3_client.put_object(
        Bucket=bucket,
        Key=s3_key,
        Body=json.dumps(param_data),
        ContentType="application/json",
    )

    return {
        "status": "success",
        "message": f"Parameters logged for experiment: {experiment_id}",
        "parameter_info": {
            "log_id": f"param-{log_id}",
            "experiment_id": experiment_id,
            "run_name": run_name,
            "parameters": parameters,
            "parameter_count": len(parameters),
            "step": step,
            "s3_uri": f"s3://{bucket}/{s3_key}",
            "logged_at": timestamp,
        },
    }
