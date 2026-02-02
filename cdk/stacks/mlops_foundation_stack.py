"""
MLOps Foundation CDK Stack

共有基盤リソース（S3、ECR、IAMロール、CloudWatch）をデプロイします。
他のスタックが依存する基盤レイヤーです。
"""

from aws_cdk import CfnOutput, RemovalPolicy, Stack, Tags
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from constructs import Construct


class MLOpsFoundationStack(Stack):
    """
    MLOps基盤スタック

    デプロイされるリソース:
    - S3バケット（データ・モデル・評価結果用）
    - ECRリポジトリ（モデルコンテナ用）
    - IAMロール（SageMaker実行ロール、MCP Server実行ロール）
    - CloudWatch関連の基盤設定

    パラメータ:
    - env_name: 環境名（dev / staging / prod）
    - project_name: プロジェクト名プレフィックス
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_name: str = "dev",
        project_name: str = "mlops",
        **kwargs,
    ):
        super().__init__(scope, construct_id, **kwargs)

        self.env_name = env_name
        self.project_name = project_name
        prefix = f"{project_name}-{env_name}"

        Tags.of(self).add("Project", project_name)
        Tags.of(self).add("Environment", env_name)

        # ===== S3 バケット =====
        self.data_bucket = s3.Bucket(
            self,
            "DataBucket",
            bucket_name=f"{prefix}-data",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=(RemovalPolicy.RETAIN if env_name == "prod" else RemovalPolicy.DESTROY),
            auto_delete_objects=env_name != "prod",
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="ExpireOldVersions",
                    noncurrent_version_expiration_days=90,
                    enabled=True,
                ),
            ],
        )

        # ===== ECR リポジトリ =====
        self.model_repo = ecr.Repository(
            self,
            "ModelRepository",
            repository_name=f"{prefix}-models",
            removal_policy=(RemovalPolicy.RETAIN if env_name == "prod" else RemovalPolicy.DESTROY),
            empty_on_delete=env_name != "prod",
            lifecycle_rules=[
                ecr.LifecycleRule(
                    description="Keep last 10 images",
                    max_image_count=10,
                    rule_priority=1,
                ),
            ],
        )

        # ===== IAM: SageMaker 実行ロール =====
        self.sagemaker_role = iam.Role(
            self,
            "SageMakerExecutionRole",
            role_name=f"{prefix}-sagemaker-execution-role",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
            description="SageMaker execution role for training and inference",
        )

        # SageMaker → S3 アクセス
        self.data_bucket.grant_read_write(self.sagemaker_role)

        # SageMaker → ECR アクセス
        self.model_repo.grant_pull_push(self.sagemaker_role)

        # SageMaker → CloudWatch Logs
        self.sagemaker_role.add_to_policy(
            iam.PolicyStatement(
                sid="CloudWatchLogs",
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                resources=[f"arn:aws:logs:{self.region}:{self.account}:log-group:/aws/sagemaker/*"],
            )
        )

        # ===== IAM: MCP Server 実行ロール =====
        self.mcp_server_role = iam.Role(
            self,
            "MCPServerRole",
            role_name=f"{prefix}-mcp-server-role",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("lambda.amazonaws.com"),
                iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            ),
            description="MCP Server execution role with all capability permissions",
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
            ],
        )

        # MCP Server → S3 (Data Preparation, ML Evaluation, etc.)
        self.data_bucket.grant_read_write(self.mcp_server_role)

        # MCP Server → ECR (Model Packaging)
        self.model_repo.grant_pull_push(self.mcp_server_role)

        # MCP Server → SageMaker (Training, Deployment, Registry)
        self.mcp_server_role.add_to_policy(
            iam.PolicyStatement(
                sid="SageMakerOperations",
                actions=[
                    "sagemaker:CreateTrainingJob",
                    "sagemaker:DescribeTrainingJob",
                    "sagemaker:CreateModel",
                    "sagemaker:CreateEndpointConfig",
                    "sagemaker:CreateEndpoint",
                    "sagemaker:UpdateEndpoint",
                    "sagemaker:DeleteEndpoint",
                    "sagemaker:DeleteEndpointConfig",
                    "sagemaker:DeleteModel",
                    "sagemaker:DescribeEndpoint",
                    "sagemaker:DescribeEndpointConfig",
                    "sagemaker:UpdateEndpointWeightsAndCapacities",
                    "sagemaker:CreateModelPackage",
                    "sagemaker:CreateModelPackageGroup",
                    "sagemaker:DescribeModelPackage",
                    "sagemaker:DescribeModelPackageGroup",
                    "sagemaker:ListModelPackages",
                    "sagemaker:UpdateModelPackage",
                ],
                resources=[
                    f"arn:aws:sagemaker:{self.region}:{self.account}:*",
                ],
            )
        )

        # MCP Server → IAM PassRole (SageMaker用)
        self.mcp_server_role.add_to_policy(
            iam.PolicyStatement(
                sid="IAMPassRoleForSageMaker",
                actions=["iam:PassRole"],
                resources=[self.sagemaker_role.role_arn],
                conditions={"StringEquals": {"iam:PassedToService": "sagemaker.amazonaws.com"}},
            )
        )

        # MCP Server → CloudWatch (Monitoring)
        self.mcp_server_role.add_to_policy(
            iam.PolicyStatement(
                sid="CloudWatchMonitoring",
                actions=[
                    "cloudwatch:PutMetricData",
                    "cloudwatch:GetMetricStatistics",
                    "cloudwatch:PutMetricAlarm",
                    "cloudwatch:DeleteAlarms",
                    "cloudwatch:DescribeAlarms",
                    "cloudwatch:PutDashboard",
                    "cloudwatch:GetDashboard",
                ],
                resources=["*"],
                conditions={
                    "StringLike": {"cloudwatch:namespace": f"MLOps/{env_name.capitalize()}*"}
                },
            )
        )

        # MCP Server → Application AutoScaling (Deployment)
        self.mcp_server_role.add_to_policy(
            iam.PolicyStatement(
                sid="AutoScaling",
                actions=[
                    "application-autoscaling:RegisterScalableTarget",
                    "application-autoscaling:DeregisterScalableTarget",
                    "application-autoscaling:PutScalingPolicy",
                    "application-autoscaling:DeleteScalingPolicy",
                ],
                resources=["*"],
            )
        )

        # MCP Server → SES (Notification)
        self.mcp_server_role.add_to_policy(
            iam.PolicyStatement(
                sid="SESNotification",
                actions=["ses:SendEmail"],
                resources=[f"arn:aws:ses:{self.region}:{self.account}:identity/*"],
            )
        )

        # MCP Server → Step Functions (Retrain, Workflow)
        self.mcp_server_role.add_to_policy(
            iam.PolicyStatement(
                sid="StepFunctionsExecution",
                actions=[
                    "states:StartExecution",
                    "states:DescribeExecution",
                ],
                resources=[f"arn:aws:states:{self.region}:{self.account}:stateMachine:{prefix}-*"],
            )
        )

        # MCP Server → EventBridge (Retrain scheduling)
        self.mcp_server_role.add_to_policy(
            iam.PolicyStatement(
                sid="EventBridgeScheduling",
                actions=[
                    "events:PutRule",
                    "events:PutTargets",
                    "events:DeleteRule",
                    "events:RemoveTargets",
                ],
                resources=[f"arn:aws:events:{self.region}:{self.account}:rule/{prefix}-*"],
            )
        )

        # ===== Outputs =====
        CfnOutput(
            self,
            "DataBucketName",
            value=self.data_bucket.bucket_name,
            description="S3 bucket for datasets, models, and evaluations",
            export_name=f"{prefix}-data-bucket",
        )

        CfnOutput(
            self,
            "ModelRepoUri",
            value=self.model_repo.repository_uri,
            description="ECR repository URI for model containers",
            export_name=f"{prefix}-model-repo-uri",
        )

        CfnOutput(
            self,
            "SageMakerRoleArn",
            value=self.sagemaker_role.role_arn,
            description="SageMaker execution role ARN",
            export_name=f"{prefix}-sagemaker-role-arn",
        )

        CfnOutput(
            self,
            "MCPServerRoleArn",
            value=self.mcp_server_role.role_arn,
            description="MCP Server execution role ARN",
            export_name=f"{prefix}-mcp-server-role-arn",
        )
