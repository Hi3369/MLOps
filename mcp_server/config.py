"""設定管理"""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """統合MCPサーバーの設定"""

    # AWS設定
    aws_region: str
    s3_bucket: str

    # Secrets Manager プレフィックス
    secrets_prefix: str = "mlops/"

    # ログレベル
    log_level: str = "INFO"

    # CloudWatch Logs設定
    cloudwatch_log_group: Optional[str] = None
    cloudwatch_log_stream: Optional[str] = None

    # SageMaker設定
    sagemaker_role_arn: Optional[str] = None

    @classmethod
    def from_env(cls) -> "Config":
        """環境変数から設定を読み込む"""
        return cls(
            aws_region=os.environ.get("AWS_REGION", "us-east-1"),
            s3_bucket=os.environ["MLOPS_S3_BUCKET"],
            secrets_prefix=os.environ.get("MLOPS_SECRETS_PREFIX", "mlops/"),
            log_level=os.environ.get("LOG_LEVEL", "INFO"),
            cloudwatch_log_group=os.environ.get("CLOUDWATCH_LOG_GROUP"),
            cloudwatch_log_stream=os.environ.get("CLOUDWATCH_LOG_STREAM"),
            sagemaker_role_arn=os.environ.get("SAGEMAKER_ROLE_ARN"),
        )
