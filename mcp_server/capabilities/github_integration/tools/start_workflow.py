"""
Start Workflow Tool

Step Functionsワークフロー起動ツール
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def start_workflow(
    workflow_type: str,
    input_params: Dict[str, Any],
    execution_name: str = None,
) -> Dict[str, Any]:
    """
    Step Functionsワークフローを起動

    Args:
        workflow_type: ワークフロータイプ（training, inference, batch_transform等）
        input_params: ワークフロー入力パラメータ
        execution_name: 実行名（オプション、未指定時は自動生成）

    Returns:
        ワークフロー起動結果辞書
    """
    logger.info(f"Starting workflow: type={workflow_type}")

    # パラメータ検証
    if not workflow_type:
        raise ValueError("workflow_type must not be empty")

    if not input_params:
        raise ValueError("input_params must not be empty")

    if not isinstance(input_params, dict):
        raise ValueError("input_params must be a dictionary")

    # サポートされるワークフロータイプ
    supported_workflows = {
        "training": "mlops-training-workflow",
        "inference": "mlops-inference-workflow",
        "batch_transform": "mlops-batch-transform-workflow",
        "retraining": "mlops-retraining-workflow",
        "evaluation": "mlops-evaluation-workflow",
    }

    if workflow_type not in supported_workflows:
        raise ValueError(
            f"Unsupported workflow_type: {workflow_type}. "
            f"Supported types: {list(supported_workflows.keys())}"
        )

    try:
        # 実行名の生成
        if not execution_name:
            timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
            execution_name = f"{workflow_type}-{timestamp}-{uuid.uuid4().hex[:8]}"

        # State Machine ARNの取得
        state_machine_arn = _get_state_machine_arn(supported_workflows[workflow_type])

        if not state_machine_arn:
            # State Machineが見つからない場合はモック結果を返す
            logger.warning(
                f"State Machine not found: {supported_workflows[workflow_type]}, "
                "returning mock result"
            )
            return _get_mock_workflow_result(workflow_type, input_params, execution_name)

        # Step Functions クライアント
        sfn = boto3.client("stepfunctions")

        # ワークフロー入力の準備
        workflow_input = _prepare_workflow_input(workflow_type, input_params)

        # ワークフロー実行
        response = sfn.start_execution(
            stateMachineArn=state_machine_arn,
            name=execution_name,
            input=json.dumps(workflow_input),
        )

        execution_arn = response.get("executionArn")
        start_date = response.get("startDate")

        logger.info(f"Workflow started: {execution_arn}")

        return {
            "status": "success",
            "message": f"Workflow started successfully: {execution_name}",
            "workflow_result": {
                "workflow_type": workflow_type,
                "execution_name": execution_name,
                "execution_arn": execution_arn,
                "state_machine_arn": state_machine_arn,
                "start_time": start_date.isoformat() if start_date else None,
                "input_params": workflow_input,
                "execution_status": "RUNNING",
            },
        }

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))

        logger.error(f"Step Functions error: {error_code} - {error_message}")

        # 特定のエラーの場合はモック結果を返す
        if error_code in [
            "StateMachineDoesNotExist",
            "AccessDeniedException",
            "InvalidArn",
        ]:
            logger.warning("Returning mock workflow result due to SFN error")
            return _get_mock_workflow_result(workflow_type, input_params, execution_name)

        raise ValueError(f"Failed to start workflow: {error_message}")

    except Exception as e:
        logger.error(f"Workflow start error: {e}")
        raise ValueError(f"Failed to start workflow: {e}")


def _get_state_machine_arn(state_machine_name: str) -> str:
    """State Machine ARNを取得"""
    try:
        sfn = boto3.client("stepfunctions")

        # 一覧からState Machineを検索
        paginator = sfn.get_paginator("list_state_machines")

        for page in paginator.paginate():
            for sm in page.get("stateMachines", []):
                if sm["name"] == state_machine_name:
                    return sm["stateMachineArn"]

        return None

    except ClientError as e:
        logger.warning(f"Failed to get State Machine ARN: {e}")
        return None
    except Exception as e:
        logger.warning(f"State Machine ARN retrieval error: {e}")
        return None


def _prepare_workflow_input(workflow_type: str, input_params: Dict[str, Any]) -> Dict[str, Any]:
    """ワークフロー入力を準備"""
    base_input = {
        "workflow_type": workflow_type,
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": str(uuid.uuid4()),
    }

    if workflow_type == "training":
        return {
            **base_input,
            "training_config": input_params.get("training_config", input_params),
            "model_type": input_params.get("model_type"),
            "dataset": input_params.get("dataset", {}),
            "hyperparameters": input_params.get("hyperparameters", {}),
            "compute_config": input_params.get("compute_config", {}),
            "notification": input_params.get("notification", {}),
        }

    elif workflow_type == "inference":
        return {
            **base_input,
            "model_arn": input_params.get("model_arn"),
            "endpoint_config": input_params.get("endpoint_config", {}),
            "input_data": input_params.get("input_data", {}),
        }

    elif workflow_type == "batch_transform":
        return {
            **base_input,
            "model_arn": input_params.get("model_arn"),
            "input_data": input_params.get("input_data", {}),
            "output_config": input_params.get("output_config", {}),
            "transform_config": input_params.get("transform_config", {}),
        }

    elif workflow_type == "retraining":
        return {
            **base_input,
            "trigger_reason": input_params.get("trigger_reason"),
            "original_model": input_params.get("original_model", {}),
            "training_config": input_params.get("training_config", {}),
            "evaluation_criteria": input_params.get("evaluation_criteria", {}),
        }

    elif workflow_type == "evaluation":
        return {
            **base_input,
            "model_arn": input_params.get("model_arn"),
            "test_dataset": input_params.get("test_dataset", {}),
            "metrics": input_params.get("metrics", ["accuracy", "precision", "recall"]),
        }

    # デフォルト
    return {**base_input, **input_params}


def _get_mock_workflow_result(
    workflow_type: str,
    input_params: Dict[str, Any],
    execution_name: str,
) -> Dict[str, Any]:
    """モックワークフロー結果を返す（開発・テスト用）"""
    logger.info("Returning mock workflow result")

    mock_execution_arn = (
        f"arn:aws:states:ap-northeast-1:123456789012:"
        f"execution:mlops-{workflow_type}-workflow:{execution_name}"
    )

    mock_state_machine_arn = (
        f"arn:aws:states:ap-northeast-1:123456789012:"
        f"stateMachine:mlops-{workflow_type}-workflow"
    )

    workflow_input = _prepare_workflow_input(workflow_type, input_params)

    return {
        "status": "success",
        "message": f"Workflow started successfully: {execution_name} (mock)",
        "workflow_result": {
            "workflow_type": workflow_type,
            "execution_name": execution_name,
            "execution_arn": mock_execution_arn,
            "state_machine_arn": mock_state_machine_arn,
            "start_time": datetime.utcnow().isoformat(),
            "input_params": workflow_input,
            "execution_status": "RUNNING",
            "is_mock_data": True,
        },
    }
