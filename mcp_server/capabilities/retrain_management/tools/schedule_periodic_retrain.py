"""
Schedule Periodic Retrain Tool

定期再学習スケジュール設定ツール
"""

import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


def schedule_periodic_retrain(
    model_name: str,
    schedule_expression: str,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    定期再学習スケジュールを設定

    Args:
        model_name: モデル名
        schedule_expression: cron式またはrate式
            - cron式: "cron(0 0 * * ? *)" = 毎日0時
            - rate式: "rate(7 days)" = 7日ごと
        config: 再学習設定（オプション）
            - workflow_name: str
            - model_config: dict
            - dataset_uri: str
            - notification_enabled: bool

    Returns:
        スケジュール設定結果辞書
    """
    logger.info(f"Scheduling periodic retrain for model: {model_name}")

    # パラメータ検証
    if not model_name:
        raise ValueError("model_name must not be empty")

    if not schedule_expression:
        raise ValueError("schedule_expression must not be empty")

    # スケジュール式の検証
    if not _validate_schedule_expression(schedule_expression):
        raise ValueError(
            f"Invalid schedule expression: {schedule_expression}. "
            "Must be cron(...) or rate(...) format."
        )

    try:
        timestamp = datetime.now(timezone.utc).isoformat()
        schedule_id = str(uuid4())[:8]

        # ルール名を生成
        rule_name = f"mlops-retrain-{model_name}-{schedule_id}"

        # スケジュール設定
        schedule_config = {
            "model_name": model_name,
            "schedule_expression": schedule_expression,
            "workflow_name": (config or {}).get("workflow_name", "mlops-retraining-workflow"),
            "model_config": (config or {}).get("model_config", {}),
            "dataset_uri": (config or {}).get("dataset_uri"),
            "notification_enabled": (config or {}).get("notification_enabled", True),
        }

        env = os.environ.get("MLOPS_ENV", "development")
        lambda_arn = os.environ.get("EVENTBRIDGE_LAMBDA_ARN")

        # 開発/テスト環境ではモック
        if env in ["development", "test"] or not lambda_arn:
            logger.info("Using mock schedule creation (dev/test environment)")
            return _mock_schedule_retrain(
                model_name=model_name,
                rule_name=rule_name,
                schedule_expression=schedule_expression,
                schedule_config=schedule_config,
                schedule_id=schedule_id,
                timestamp=timestamp,
            )

        # 本番環境：実際にEventBridgeルールを作成
        return _real_schedule_retrain(
            model_name=model_name,
            rule_name=rule_name,
            schedule_expression=schedule_expression,
            schedule_config=schedule_config,
            schedule_id=schedule_id,
            timestamp=timestamp,
            lambda_arn=lambda_arn,
        )

    except Exception as e:
        logger.error(f"Failed to schedule periodic retrain: {e}")
        raise ValueError(f"Failed to schedule periodic retrain: {e}")


def _validate_schedule_expression(expression: str) -> bool:
    """スケジュール式を検証"""
    # cron式: cron(0 0 * * ? *)
    cron_pattern = r"^cron\(.+\)$"

    # rate式: rate(1 day), rate(7 days), rate(1 hour)
    rate_pattern = r"^rate\(\d+\s+(minute|minutes|hour|hours|day|days)\)$"

    if re.match(cron_pattern, expression):
        return True
    if re.match(rate_pattern, expression):
        return True

    return False


def _mock_schedule_retrain(
    model_name: str,
    rule_name: str,
    schedule_expression: str,
    schedule_config: Dict[str, Any],
    schedule_id: str,
    timestamp: str,
) -> Dict[str, Any]:
    """モックスケジュール作成"""
    mock_rule_arn = f"arn:aws:events:ap-northeast-1:123456789012:rule/{rule_name}"

    # 次回実行時間を推定
    next_run = _estimate_next_run(schedule_expression, timestamp)

    return {
        "status": "success",
        "message": "Periodic retrain scheduled (mock)",
        "schedule_result": {
            "schedule_id": schedule_id,
            "rule_name": rule_name,
            "rule_arn": mock_rule_arn,
            "model_name": model_name,
            "schedule_expression": schedule_expression,
            "schedule_config": schedule_config,
            "schedule_status": "ENABLED",
            "next_scheduled_run": next_run,
            "created_at": timestamp,
            "mock": True,
        },
    }


def _real_schedule_retrain(
    model_name: str,
    rule_name: str,
    schedule_expression: str,
    schedule_config: Dict[str, Any],
    schedule_id: str,
    timestamp: str,
    lambda_arn: str,
) -> Dict[str, Any]:
    """実際のEventBridgeスケジュール作成"""
    import boto3
    from botocore.exceptions import ClientError

    try:
        events_client = boto3.client("events")

        # EventBridgeルールを作成
        rule_response = events_client.put_rule(
            Name=rule_name,
            ScheduleExpression=schedule_expression,
            State="ENABLED",
            Description=f"Periodic retraining schedule for {model_name}",
        )

        rule_arn = rule_response["RuleArn"]

        # ターゲット（Lambda）を設定
        events_client.put_targets(
            Rule=rule_name,
            Targets=[
                {
                    "Id": f"retrain-target-{schedule_id}",
                    "Arn": lambda_arn,
                    "Input": json.dumps(schedule_config),
                }
            ],
        )

        # 次回実行時間を推定
        next_run = _estimate_next_run(schedule_expression, timestamp)

        return {
            "status": "success",
            "message": "Periodic retrain scheduled successfully",
            "schedule_result": {
                "schedule_id": schedule_id,
                "rule_name": rule_name,
                "rule_arn": rule_arn,
                "model_name": model_name,
                "schedule_expression": schedule_expression,
                "schedule_config": schedule_config,
                "schedule_status": "ENABLED",
                "next_scheduled_run": next_run,
                "created_at": timestamp,
                "mock": False,
            },
        }

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        raise ValueError(f"EventBridge error ({error_code}): {e}")


def _estimate_next_run(schedule_expression: str, current_time: str) -> str:
    """次回実行時間を推定"""
    try:
        now = datetime.fromisoformat(current_time.replace("Z", "+00:00"))

        # rate式の場合
        rate_match = re.match(
            r"^rate\((\d+)\s+(minute|minutes|hour|hours|day|days)\)$",
            schedule_expression,
        )
        if rate_match:
            value = int(rate_match.group(1))
            unit = rate_match.group(2)

            from datetime import timedelta

            if "minute" in unit:
                delta = timedelta(minutes=value)
            elif "hour" in unit:
                delta = timedelta(hours=value)
            else:
                delta = timedelta(days=value)

            next_time = now + delta
            return next_time.isoformat()

        # cron式の場合は概算（正確にはcroniterライブラリが必要）
        # デフォルトで翌日0時を返す
        from datetime import timedelta

        next_time = now + timedelta(days=1)
        next_time = next_time.replace(hour=0, minute=0, second=0, microsecond=0)
        return next_time.isoformat()

    except Exception:
        return "unknown"
