"""AWS Secrets Manager統合"""
import json
from functools import lru_cache

import boto3
from botocore.exceptions import ClientError

from .logger import get_logger

logger = get_logger(__name__)


class SecretsManager:
    """Secrets Manager操作"""

    def __init__(self, config):
        self.config = config
        self.client = boto3.client("secretsmanager", region_name=config.aws_region)

    @lru_cache(maxsize=10)
    def get_secret(self, secret_name: str) -> dict:
        """
        AWS Secrets Managerからシークレットを取得（キャッシュあり）

        Args:
            secret_name: シークレット名（プレフィックスなし）

        Returns:
            シークレット値の辞書
        """
        full_secret_name = f"{self.config.secrets_prefix}{secret_name}"

        try:
            response = self.client.get_secret_value(SecretId=full_secret_name)
            secret_value = json.loads(response["SecretString"])
            logger.info(f"Retrieved secret: {full_secret_name}")
            return secret_value

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ResourceNotFoundException":
                logger.error(f"Secret not found: {full_secret_name}")
            elif error_code == "InvalidRequestException":
                logger.error(f"Invalid request for secret: {full_secret_name}")
            elif error_code == "InvalidParameterException":
                logger.error(f"Invalid parameter for secret: {full_secret_name}")
            else:
                logger.error(f"Failed to get secret: {full_secret_name}", exc_info=True)
            raise

    def get_github_token(self) -> str:
        """GitHub Personal Access Tokenを取得"""
        secret = self.get_secret("github")
        return secret.get("token", "")

    def get_slack_webhook_url(self) -> str:
        """Slack Webhook URLを取得"""
        secret = self.get_secret("slack")
        return secret.get("webhook_url", "")

    def get_email_credentials(self) -> dict:
        """Email送信用の認証情報を取得"""
        return self.get_secret("email")
