"""
Format Training History Tool

学習履歴フォーマットツール
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


def format_training_history(
    training_job_name: str,
    metrics: Dict[str, Any],
    hyperparameters: Optional[Dict[str, Any]] = None,
    model_name: Optional[str] = None,
    model_version: Optional[str] = None,
    dataset_info: Optional[Dict[str, Any]] = None,
    training_time_seconds: Optional[float] = None,
    instance_type: Optional[str] = None,
    output_format: str = "markdown",
) -> Dict[str, Any]:
    """
    学習結果をフォーマット

    Args:
        training_job_name: 学習ジョブ名
        metrics: メトリクス辞書（accuracy, loss, precision, recall等）
        hyperparameters: ハイパーパラメータ辞書
        model_name: モデル名
        model_version: モデルバージョン
        dataset_info: データセット情報
        training_time_seconds: 学習時間（秒）
        instance_type: インスタンスタイプ
        output_format: 出力形式（markdown, json, text）

    Returns:
        フォーマット結果辞書
    """
    logger.info(f"Formatting training history for job: {training_job_name}")

    # パラメータ検証
    if not training_job_name:
        raise ValueError("training_job_name must not be empty")

    if not metrics:
        raise ValueError("metrics must not be empty")

    if output_format not in ["markdown", "json", "text"]:
        raise ValueError(f"Invalid output_format: {output_format}")

    try:
        timestamp = datetime.now(timezone.utc).isoformat()
        history_id = str(uuid4())[:8]

        # 履歴データ構造
        history_data = {
            "history_id": history_id,
            "training_job_name": training_job_name,
            "timestamp": timestamp,
            "metrics": metrics,
            "hyperparameters": hyperparameters or {},
            "model_name": model_name,
            "model_version": model_version,
            "dataset_info": dataset_info,
            "training_time_seconds": training_time_seconds,
            "instance_type": instance_type,
        }

        # フォーマット生成
        if output_format == "markdown":
            formatted = _format_as_markdown(history_data)
        elif output_format == "json":
            formatted = _format_as_json(history_data)
        else:
            formatted = _format_as_text(history_data)

        logger.info(f"Training history formatted successfully: {history_id}")

        return {
            "status": "success",
            "message": f"Training history formatted as {output_format}",
            "history_result": {
                "history_id": history_id,
                "training_job_name": training_job_name,
                "output_format": output_format,
                "formatted_content": formatted,
                "timestamp": timestamp,
            },
        }

    except Exception as e:
        logger.error(f"Failed to format training history: {e}")
        raise ValueError(f"Failed to format training history: {e}")


def _format_as_markdown(data: Dict[str, Any]) -> str:
    """Markdown形式でフォーマット"""
    lines = [
        f"# Training History: {data['training_job_name']}",
        "",
        f"**History ID:** {data['history_id']}",
        f"**Timestamp:** {data['timestamp']}",
        "",
    ]

    if data.get("model_name"):
        lines.append(f"**Model:** {data['model_name']}")
        if data.get("model_version"):
            lines.append(f"**Version:** {data['model_version']}")
        lines.append("")

    if data.get("instance_type"):
        lines.append(f"**Instance Type:** {data['instance_type']}")

    if data.get("training_time_seconds"):
        minutes = data["training_time_seconds"] / 60
        lines.append(f"**Training Time:** {minutes:.2f} minutes")
        lines.append("")

    # Metrics section
    lines.extend(["## Metrics", ""])
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    for key, value in data["metrics"].items():
        if isinstance(value, float):
            lines.append(f"| {key} | {value:.4f} |")
        else:
            lines.append(f"| {key} | {value} |")
    lines.append("")

    # Hyperparameters section
    if data.get("hyperparameters"):
        lines.extend(["## Hyperparameters", ""])
        lines.append("| Parameter | Value |")
        lines.append("|-----------|-------|")
        for key, value in data["hyperparameters"].items():
            lines.append(f"| {key} | {value} |")
        lines.append("")

    # Dataset info section
    if data.get("dataset_info"):
        lines.extend(["## Dataset Information", ""])
        for key, value in data["dataset_info"].items():
            lines.append(f"- **{key}:** {value}")
        lines.append("")

    return "\n".join(lines)


def _format_as_json(data: Dict[str, Any]) -> str:
    """JSON形式でフォーマット"""
    return json.dumps(data, indent=2, ensure_ascii=False)


def _format_as_text(data: Dict[str, Any]) -> str:
    """テキスト形式でフォーマット"""
    lines = [
        f"Training History: {data['training_job_name']}",
        f"History ID: {data['history_id']}",
        f"Timestamp: {data['timestamp']}",
        "",
    ]

    if data.get("model_name"):
        lines.append(f"Model: {data['model_name']}")
        if data.get("model_version"):
            lines.append(f"Version: {data['model_version']}")

    if data.get("instance_type"):
        lines.append(f"Instance Type: {data['instance_type']}")

    if data.get("training_time_seconds"):
        minutes = data["training_time_seconds"] / 60
        lines.append(f"Training Time: {minutes:.2f} minutes")

    lines.append("")
    lines.append("Metrics:")
    for key, value in data["metrics"].items():
        if isinstance(value, float):
            lines.append(f"  {key}: {value:.4f}")
        else:
            lines.append(f"  {key}: {value}")

    if data.get("hyperparameters"):
        lines.append("")
        lines.append("Hyperparameters:")
        for key, value in data["hyperparameters"].items():
            lines.append(f"  {key}: {value}")

    return "\n".join(lines)
