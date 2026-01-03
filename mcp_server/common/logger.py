"""
Logging Utility for MLOps MCP Server
"""

import logging
import sys


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    ロガーのセットアップ

    Args:
        name: ロガー名
        level: ログレベル

    Returns:
        設定済みLogger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # ハンドラーが既に設定されている場合はスキップ
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
