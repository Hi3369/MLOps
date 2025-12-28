"""構造化ロギング"""
import logging
import json
import sys
from typing import Any


class JSONFormatter(logging.Formatter):
    """JSON形式のログフォーマッター"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # 追加のコンテキスト情報を追加
        if hasattr(record, "extra"):
            log_data.update(record.extra)

        # 例外情報を追加
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def get_logger(name: str) -> logging.Logger:
    """ロガーを取得"""
    logger = logging.getLogger(name)

    if not logger.handlers:
        # ハンドラーを設定
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)

        # ログレベルを設定（環境変数から）
        import os
        log_level = os.environ.get("LOG_LEVEL", "INFO")
        logger.setLevel(getattr(logging, log_level))

    return logger
