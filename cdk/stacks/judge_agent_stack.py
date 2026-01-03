"""
Judge Agent CDK Stack

このスタックは、モデル評価結果の判定と次アクション決定を行う
Judge Agent用のAWSリソースをデプロイします。
"""

from aws_cdk import Duration, Stack
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_logs as logs
from constructs import Construct


class JudgeAgentStack(Stack):
    """
    Judge Agent用のCDKスタック

    デプロイされるリソース:
    - Lambda関数 (Judge Agent)
    - IAMロール (Lambda実行ロール)
    - CloudWatch Logs (ログ保持期間: 1ヶ月)

    権限:
    - S3読み取り (評価結果の取得)
    - CloudWatch Metrics書き込み (メトリクス記録)
    - CloudWatch Logs書き込み (ログ記録)
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # IAMロール
        judge_agent_role = iam.Role(
            self,
            "JudgeAgentRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description="Execution role for Judge Agent Lambda function",
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ],
        )

        # S3読み取り権限（評価結果の取得用）
        judge_agent_role.add_to_policy(
            iam.PolicyStatement(
                sid="S3ReadEvaluationResults",
                actions=["s3:GetObject"],
                resources=["arn:aws:s3:::mlops-bucket/evaluations/*"],
            )
        )

        # CloudWatch Metrics書き込み権限（メトリクス記録用）
        judge_agent_role.add_to_policy(
            iam.PolicyStatement(
                sid="CloudWatchPutMetrics",
                actions=["cloudwatch:PutMetricData"],
                resources=["*"],
                conditions={"StringEquals": {"cloudwatch:namespace": "MLOps/JudgeAgent"}},
            )
        )

        # Lambda関数
        self.judge_agent_function = lambda_.Function(
            self,
            "JudgeAgentFunction",
            function_name="mlops-judge-agent",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="lambda_function.lambda_handler",
            code=lambda_.Code.from_asset("../agents/judge_agent"),
            role=judge_agent_role,
            timeout=Duration.seconds(60),
            memory_size=256,
            description="Judge Agent for model evaluation judgment",
            environment={
                "LOG_LEVEL": "INFO",
                "POWERTOOLS_SERVICE_NAME": "judge-agent",
            },
            log_retention=logs.RetentionDays.ONE_MONTH,
        )

        # Step Functions用にLambda関数のARNを出力
        self.function_arn = self.judge_agent_function.function_arn
