"""
Apply Notification Template Tool

通知テンプレート適用ツール
"""

import logging
import re
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# 組み込みテンプレート
BUILTIN_TEMPLATES = {
    "training_started": {
        "subject": "[MLOps] Training Started: {model_name}",
        "body": """Training job has started.

**Model:** {model_name}
**Job ID:** {job_id}
**Started at:** {start_time}

**Configuration:**
- Model Type: {model_type}
- Dataset: {dataset_path}
- Instance Type: {instance_type}

Training is now in progress. You will be notified when it completes.""",
        "slack_blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": ":rocket: Training Started"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": "*Model:*\n{model_name}"},
                    {"type": "mrkdwn", "text": "*Job ID:*\n{job_id}"},
                ],
            },
        ],
    },
    "training_completed": {
        "subject": "[MLOps] Training Completed: {model_name}",
        "body": """Training job has completed successfully.

**Model:** {model_name}
**Job ID:** {job_id}
**Duration:** {duration}

**Results:**
- Accuracy: {accuracy}
- Loss: {loss}
- Model ARN: {model_arn}

The model is now ready for evaluation and deployment.""",
        "slack_blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": ":white_check_mark: Training Completed"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": "*Model:*\n{model_name}"},
                    {"type": "mrkdwn", "text": "*Duration:*\n{duration}"},
                    {"type": "mrkdwn", "text": "*Accuracy:*\n{accuracy}"},
                ],
            },
        ],
    },
    "training_failed": {
        "subject": "[MLOps] Training Failed: {model_name}",
        "body": """Training job has failed.

**Model:** {model_name}
**Job ID:** {job_id}
**Failed at:** {failed_time}

**Error:**
```
{error_message}
```

Please review the logs and retry if necessary.""",
        "slack_blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": ":x: Training Failed"},
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Model:* {model_name}\n*Error:* {error_message}",
                },
            },
        ],
    },
    "deployment_started": {
        "subject": "[MLOps] Deployment Started: {model_name}",
        "body": """Model deployment has started.

**Model:** {model_name}
**Endpoint:** {endpoint_name}
**Environment:** {environment}

Deployment is in progress...""",
    },
    "deployment_completed": {
        "subject": "[MLOps] Deployment Completed: {model_name}",
        "body": """Model deployment has completed successfully.

**Model:** {model_name}
**Endpoint:** {endpoint_name}
**Environment:** {environment}
**Endpoint URL:** {endpoint_url}

The model is now live and ready to serve predictions.""",
    },
    "drift_detected": {
        "subject": "[MLOps] Data Drift Detected: {model_name}",
        "body": """Data drift has been detected for the model.

**Model:** {model_name}
**Endpoint:** {endpoint_name}
**Detected at:** {detected_time}

**Drift Details:**
- Drift Score: {drift_score}
- Affected Features: {affected_features}
- Threshold: {threshold}

Please consider retraining the model with recent data.""",
        "slack_blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": ":warning: Data Drift Detected"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": "*Model:*\n{model_name}"},
                    {"type": "mrkdwn", "text": "*Drift Score:*\n{drift_score}"},
                ],
            },
        ],
    },
    "alert_triggered": {
        "subject": "[MLOps Alert] {alert_name}: {severity}",
        "body": """An alert has been triggered.

**Alert:** {alert_name}
**Severity:** {severity}
**Triggered at:** {triggered_time}

**Details:**
{alert_details}

**Recommended Action:**
{recommended_action}""",
    },
}


def apply_notification_template(
    template_name: str,
    variables: Dict[str, Any],
    custom_template: Optional[Dict[str, str]] = None,
    output_format: str = "all",
) -> Dict[str, Any]:
    """
    通知テンプレートを適用

    Args:
        template_name: テンプレート名（組み込みテンプレートを使用）
        variables: テンプレート変数
        custom_template: カスタムテンプレート（subject, body, slack_blocksを含む辞書）
        output_format: 出力フォーマット（all, email, slack, github）

    Returns:
        適用されたテンプレート辞書
    """
    logger.info(f"Applying notification template: {template_name}")

    # パラメータ検証
    if not template_name:
        raise ValueError("template_name must not be empty")

    if not variables:
        raise ValueError("variables must not be empty")

    if not isinstance(variables, dict):
        raise ValueError("variables must be a dictionary")

    valid_formats = ["all", "email", "slack", "github"]
    if output_format not in valid_formats:
        raise ValueError(f"output_format must be one of {valid_formats}")

    try:
        # テンプレート取得
        if custom_template:
            template = custom_template
        elif template_name in BUILTIN_TEMPLATES:
            template = BUILTIN_TEMPLATES[template_name]
        else:
            available = list(BUILTIN_TEMPLATES.keys())
            raise ValueError(f"Unknown template: {template_name}. Available templates: {available}")

        # テンプレート適用
        applied = _apply_variables(template, variables)

        # 出力フォーマットに応じてフィルタリング
        result = {
            "status": "success",
            "message": f"Template '{template_name}' applied successfully",
            "template_result": {
                "template_name": template_name,
                "applied_variables": list(variables.keys()),
                "output_format": output_format,
            },
        }

        if output_format in ["all", "email"]:
            result["template_result"]["email"] = {
                "subject": applied.get("subject", ""),
                "body": applied.get("body", ""),
            }

        if output_format in ["all", "slack"]:
            result["template_result"]["slack"] = {
                "text": applied.get("body", ""),
                "blocks": applied.get("slack_blocks"),
            }

        if output_format in ["all", "github"]:
            result["template_result"]["github"] = {
                "title": applied.get("subject", ""),
                "body": applied.get("body", ""),
            }

        logger.info(f"Template applied with {len(variables)} variables")
        return result

    except Exception as e:
        logger.error(f"Template application error: {e}")
        raise ValueError(f"Failed to apply notification template: {e}")


def _apply_variables(template: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
    """テンプレートに変数を適用"""
    applied = {}

    for key, value in template.items():
        if isinstance(value, str):
            # 文字列の場合は変数を置換
            applied[key] = _substitute_variables(value, variables)
        elif isinstance(value, list):
            # リスト（slack_blocks等）の場合は再帰的に処理
            applied[key] = _apply_variables_to_list(value, variables)
        elif isinstance(value, dict):
            # 辞書の場合は再帰的に処理
            applied[key] = _apply_variables(value, variables)
        else:
            applied[key] = value

    return applied


def _apply_variables_to_list(items: list, variables: Dict[str, Any]) -> list:
    """リスト内の要素に変数を適用"""
    result = []
    for item in items:
        if isinstance(item, str):
            result.append(_substitute_variables(item, variables))
        elif isinstance(item, dict):
            result.append(_apply_variables(item, variables))
        elif isinstance(item, list):
            result.append(_apply_variables_to_list(item, variables))
        else:
            result.append(item)
    return result


def _substitute_variables(text: str, variables: Dict[str, Any]) -> str:
    """テキスト内の変数を置換"""

    # {variable_name} 形式の変数を置換
    def replace_var(match):
        var_name = match.group(1)
        if var_name in variables:
            return str(variables[var_name])
        return match.group(0)  # 変数が見つからない場合はそのまま

    pattern = r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}"
    return re.sub(pattern, replace_var, text)


def list_available_templates() -> Dict[str, Any]:
    """利用可能なテンプレート一覧を取得"""
    templates = []
    for name, template in BUILTIN_TEMPLATES.items():
        # テンプレートで使用されている変数を抽出
        all_text = str(template)
        variables = set(re.findall(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}", all_text))

        templates.append(
            {
                "name": name,
                "has_subject": "subject" in template,
                "has_body": "body" in template,
                "has_slack_blocks": "slack_blocks" in template,
                "variables": sorted(list(variables)),
            }
        )

    return {
        "status": "success",
        "templates": templates,
        "total": len(templates),
    }
