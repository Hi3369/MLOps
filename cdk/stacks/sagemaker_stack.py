"""
SageMaker CDK Stack

SageMakerリソース（モデルレジストリ、エンドポイント設定）をデプロイします。
MLOpsFoundationStackのS3バケット・IAMロールに依存します。
"""

from aws_cdk import CfnOutput, Stack, Tags
from aws_cdk import aws_iam as iam
from aws_cdk import aws_sagemaker as sagemaker
from constructs import Construct


class SageMakerStack(Stack):
    """
    SageMakerスタック

    デプロイされるリソース:
    - SageMaker Model Package Group（モデルレジストリ）
    - SageMaker Monitoring Schedule用 IAMロール

    パラメータ:
    - env_name: 環境名（dev / staging / prod）
    - project_name: プロジェクト名プレフィックス
    - sagemaker_role_arn: SageMaker実行ロールARN（FoundationStackから）
    - data_bucket_name: データバケット名（FoundationStackから）
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_name: str = "dev",
        project_name: str = "mlops",
        sagemaker_role_arn: str = "",
        data_bucket_name: str = "",
        **kwargs,
    ):
        super().__init__(scope, construct_id, **kwargs)

        self.env_name = env_name
        self.project_name = project_name
        prefix = f"{project_name}-{env_name}"

        Tags.of(self).add("Project", project_name)
        Tags.of(self).add("Environment", env_name)

        # ===== Model Package Group（モデルレジストリ） =====
        self.model_package_group = sagemaker.CfnModelPackageGroup(
            self,
            "ModelPackageGroup",
            model_package_group_name=f"{prefix}-models",
            model_package_group_description=(f"MLOps model registry for {env_name} environment"),
        )

        # ===== Model Monitor 実行ロール =====
        self.monitor_role = iam.Role(
            self,
            "ModelMonitorRole",
            role_name=f"{prefix}-model-monitor-role",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
            description="Role for SageMaker Model Monitor jobs",
        )

        # Monitor → S3 (ベースライン・結果の読み書き)
        self.monitor_role.add_to_policy(
            iam.PolicyStatement(
                sid="S3Access",
                actions=["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
                resources=[
                    f"arn:aws:s3:::{data_bucket_name}",
                    f"arn:aws:s3:::{data_bucket_name}/*",
                ],
            )
        )

        # Monitor → CloudWatch (メトリクス・アラーム)
        self.monitor_role.add_to_policy(
            iam.PolicyStatement(
                sid="CloudWatchMetrics",
                actions=[
                    "cloudwatch:PutMetricData",
                    "cloudwatch:GetMetricStatistics",
                ],
                resources=["*"],
            )
        )

        # Monitor → CloudWatch Logs
        self.monitor_role.add_to_policy(
            iam.PolicyStatement(
                sid="CloudWatchLogs",
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                resources=[
                    f"arn:aws:logs:{self.region}:{self.account}:log-group:"
                    f"/aws/sagemaker/MonitoringSchedules/*"
                ],
            )
        )

        # ===== Outputs =====
        CfnOutput(
            self,
            "ModelPackageGroupName",
            value=self.model_package_group.model_package_group_name or "",
            description="SageMaker Model Package Group name",
            export_name=f"{prefix}-model-package-group",
        )

        CfnOutput(
            self,
            "MonitorRoleArn",
            value=self.monitor_role.role_arn,
            description="SageMaker Model Monitor role ARN",
            export_name=f"{prefix}-monitor-role-arn",
        )
