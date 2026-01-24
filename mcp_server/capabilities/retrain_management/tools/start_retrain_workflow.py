"""
Start Retrain Workflow Tool

再学習ワークフロー起動ツール
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


def start_retrain_workflow(
    workflow_name: str,
    model_config: Dict[str, Any],
    dataset_uri: Optional[str] = None,
    comparison_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    再学習ワークフローを起動

    Args:
        workflow_name: ワークフロー名
        model_config: モデル設定
            - model_name: str
            - model_type: str
            - hyperparameters: dict
            - original_model_arn: str (比較用)
        dataset_uri: データセットURI（S3パス）
        comparison_config: 新旧モデル比較設定（FR-026対応）
            - metrics_to_compare: list
            - improvement_threshold: float
            - auto_deploy_on_improvement: bool

    Returns:
        ワークフロー起動結果辞書
    """
    logger.info(f"Starting retrain workflow: {workflow_name}")

    # パラメータ検証
    if not workflow_name:
        raise ValueError("workflow_name must not be empty")

    if not model_config:
        raise ValueError("model_config must not be empty")

    try:
        timestamp = datetime.now(timezone.utc).isoformat()
        execution_id = str(uuid4())

        # モデル名を取得
        model_name = model_config.get("model_name", "unknown-model")

        # バージョニング情報を生成（FR-027対応）
        current_version = model_config.get("current_version", "v1.0.0")
        next_version = _increment_version(current_version)

        # ワークフロー入力を構築
        workflow_input = {
            "workflow_type": "retraining",
            "execution_id": execution_id,
            "timestamp": timestamp,
            "model_config": model_config,
            "dataset_uri": dataset_uri,
            "versioning": {
                "current_version": current_version,
                "next_version": next_version,
            },
        }

        # 比較設定があれば追加
        if comparison_config:
            workflow_input["comparison_config"] = {
                "metrics_to_compare": comparison_config.get("metrics_to_compare", ["accuracy"]),
                "improvement_threshold": comparison_config.get("improvement_threshold", 0.01),
                "auto_deploy_on_improvement": comparison_config.get(
                    "auto_deploy_on_improvement", False
                ),
            }

        env = os.environ.get("MLOPS_ENV", "development")
        step_functions_arn = os.environ.get("STEP_FUNCTIONS_ARN")

        # 開発/テスト環境ではモック
        if env in ["development", "test"] or not step_functions_arn:
            logger.info("Using mock workflow execution (dev/test environment)")
            return _mock_start_workflow(
                workflow_name=workflow_name,
                model_name=model_name,
                execution_id=execution_id,
                workflow_input=workflow_input,
                timestamp=timestamp,
                next_version=next_version,
            )

        # 本番環境：実際にStep Functionsを起動
        return _real_start_workflow(
            workflow_name=workflow_name,
            model_name=model_name,
            execution_id=execution_id,
            workflow_input=workflow_input,
            timestamp=timestamp,
            next_version=next_version,
            step_functions_arn=step_functions_arn,
        )

    except Exception as e:
        logger.error(f"Failed to start retrain workflow: {e}")
        raise ValueError(f"Failed to start retrain workflow: {e}")


def _increment_version(version: str) -> str:
    """バージョンをインクリメント（マイナーバージョン）"""
    import re

    # v1.2.3 or 1.2.3 形式に対応
    match = re.match(r"^(v?)(\d+)\.(\d+)\.(\d+)(.*)$", version)
    if match:
        prefix = match.group(1)
        major = int(match.group(2))
        minor = int(match.group(3))
        _ = int(match.group(4))  # patch (reset to 0)
        suffix = match.group(5)

        # マイナーバージョンをインクリメント、パッチを0にリセット
        return f"{prefix}{major}.{minor + 1}.0{suffix}"

    # パースできない場合は元のバージョンに-newを付加
    return f"{version}-new"


def _mock_start_workflow(
    workflow_name: str,
    model_name: str,
    execution_id: str,
    workflow_input: Dict[str, Any],
    timestamp: str,
    next_version: str,
) -> Dict[str, Any]:
    """モックワークフロー起動"""
    mock_arn = (
        f"arn:aws:states:ap-northeast-1:123456789012:execution:{workflow_name}:{execution_id}"
    )

    return {
        "status": "success",
        "message": "Retrain workflow started (mock)",
        "workflow_result": {
            "execution_id": execution_id,
            "execution_arn": mock_arn,
            "execution_status": "RUNNING",
            "workflow_name": workflow_name,
            "model_name": model_name,
            "next_version": next_version,
            "input_params": workflow_input,
            "start_time": timestamp,
            "mock": True,
        },
    }


def _real_start_workflow(
    workflow_name: str,
    model_name: str,
    execution_id: str,
    workflow_input: Dict[str, Any],
    timestamp: str,
    next_version: str,
    step_functions_arn: str,
) -> Dict[str, Any]:
    """実際のStep Functionsワークフロー起動"""
    import boto3
    from botocore.exceptions import ClientError

    try:
        sfn_client = boto3.client("stepfunctions")

        # Step Functions実行を開始
        response = sfn_client.start_execution(
            stateMachineArn=step_functions_arn,
            name=f"retrain-{model_name}-{execution_id[:8]}",
            input=json.dumps(workflow_input),
        )

        return {
            "status": "success",
            "message": "Retrain workflow started successfully",
            "workflow_result": {
                "execution_id": execution_id,
                "execution_arn": response["executionArn"],
                "execution_status": "RUNNING",
                "workflow_name": workflow_name,
                "model_name": model_name,
                "next_version": next_version,
                "input_params": workflow_input,
                "start_time": response["startDate"].isoformat(),
                "mock": False,
            },
        }

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        raise ValueError(f"Step Functions error ({error_code}): {e}")
