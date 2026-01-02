"""
Configuration Management for MLOps MCP Server
"""

import os
from typing import Any, Dict


class Config:
    """
    MCPサーバーの設定管理

    環境変数から設定を読み込み、デフォルト値を提供します。
    """

    def __init__(self):
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.s3_bucket = os.getenv("MLOPS_S3_BUCKET", "mlops-bucket")
        self.aws_region = os.getenv("AWS_REGION", "us-west-2")

    def to_dict(self) -> Dict[str, Any]:
        """設定を辞書形式で返す"""
        return {
            "log_level": self.log_level,
            "s3_bucket": self.s3_bucket,
            "aws_region": self.aws_region,
        }
