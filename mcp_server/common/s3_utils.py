"""S3操作ユーティリティ"""
import io
import pandas as pd
import boto3
from botocore.exceptions import ClientError

from .logger import get_logger
from .exceptions import S3Error

logger = get_logger(__name__)


class S3Utils:
    """S3操作ヘルパー"""

    def __init__(self, config):
        self.config = config
        self.s3_client = boto3.client('s3', region_name=config.aws_region)

    async def read_dataframe(self, s3_uri: str) -> pd.DataFrame:
        """S3からDataFrameを読み込む"""
        bucket, key = self._parse_s3_uri(s3_uri)

        try:
            obj = self.s3_client.get_object(Bucket=bucket, Key=key)

            if key.endswith('.csv'):
                df = pd.read_csv(io.BytesIO(obj['Body'].read()))
            elif key.endswith('.parquet'):
                df = pd.read_parquet(io.BytesIO(obj['Body'].read()))
            else:
                raise ValueError(f"Unsupported file format: {key}")

            logger.info(f"Loaded dataframe from {s3_uri}: {df.shape}")
            return df

        except ClientError as e:
            logger.error(f"Failed to read from S3: {s3_uri}", exc_info=True)
            raise S3Error(f"Failed to read from S3: {s3_uri}") from e

    async def write_dataframe(self, df: pd.DataFrame, s3_uri: str):
        """DataFrameをS3に書き込む"""
        bucket, key = self._parse_s3_uri(s3_uri)

        try:
            buffer = io.BytesIO()

            if key.endswith('.csv'):
                df.to_csv(buffer, index=False)
            elif key.endswith('.parquet'):
                df.to_parquet(buffer, index=False)
            else:
                raise ValueError(f"Unsupported file format: {key}")

            buffer.seek(0)
            self.s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=buffer.getvalue(),
                ServerSideEncryption='aws:kms'  # KMS暗号化
            )

            logger.info(f"Wrote dataframe to {s3_uri}: {df.shape}")

        except ClientError as e:
            logger.error(f"Failed to write to S3: {s3_uri}", exc_info=True)
            raise S3Error(f"Failed to write to S3: {s3_uri}") from e

    async def upload_file(self, local_path: str, s3_uri: str):
        """ローカルファイルをS3にアップロード"""
        bucket, key = self._parse_s3_uri(s3_uri)

        try:
            self.s3_client.upload_file(
                local_path,
                bucket,
                key,
                ExtraArgs={'ServerSideEncryption': 'aws:kms'}
            )
            logger.info(f"Uploaded file to {s3_uri}")

        except ClientError as e:
            logger.error(f"Failed to upload to S3: {s3_uri}", exc_info=True)
            raise S3Error(f"Failed to upload to S3: {s3_uri}") from e

    def _parse_s3_uri(self, s3_uri: str) -> tuple[str, str]:
        """S3 URIをbucketとkeyにパース"""
        if not s3_uri.startswith('s3://'):
            raise ValueError(f"Invalid S3 URI: {s3_uri}")

        parts = s3_uri[5:].split('/', 1)
        bucket = parts[0]
        key = parts[1] if len(parts) > 1 else ''

        return bucket, key
