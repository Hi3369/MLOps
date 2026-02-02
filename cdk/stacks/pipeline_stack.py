"""
MLOps Pipeline CDK Stack

Step Functionsステートマシン（MLOpsパイプライン）と
EventBridgeスケジュール（再学習トリガー）をデプロイします。
"""

from aws_cdk import CfnOutput, Stack, Tags
from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as targets
from aws_cdk import aws_iam as iam
from aws_cdk import aws_logs as logs
from aws_cdk import aws_stepfunctions as sfn
from constructs import Construct


class PipelineStack(Stack):
    """
    MLOpsパイプラインスタック

    デプロイされるリソース:
    - Step Functions ステートマシン（MLOpsパイプライン）
    - EventBridge ルール（定期再学習スケジュール）
    - IAMロール（Step Functions実行ロール）

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

        # ===== Step Functions 実行ロール =====
        sfn_role = iam.Role(
            self,
            "StepFunctionsRole",
            role_name=f"{prefix}-stepfunctions-role",
            assumed_by=iam.ServicePrincipal("states.amazonaws.com"),
            description="Step Functions execution role for MLOps pipeline",
        )

        # SFn → SageMaker（学習ジョブ・エンドポイント管理）
        sfn_role.add_to_policy(
            iam.PolicyStatement(
                sid="SageMakerJobs",
                actions=[
                    "sagemaker:CreateTrainingJob",
                    "sagemaker:DescribeTrainingJob",
                    "sagemaker:CreateModel",
                    "sagemaker:CreateEndpointConfig",
                    "sagemaker:CreateEndpoint",
                    "sagemaker:UpdateEndpoint",
                    "sagemaker:DescribeEndpoint",
                ],
                resources=[
                    f"arn:aws:sagemaker:{self.region}:{self.account}:*",
                ],
            )
        )

        # SFn → S3（データ・モデルの読み書き）
        sfn_role.add_to_policy(
            iam.PolicyStatement(
                sid="S3Access",
                actions=["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
                resources=[
                    f"arn:aws:s3:::{data_bucket_name}",
                    f"arn:aws:s3:::{data_bucket_name}/*",
                ],
            )
        )

        # SFn → IAM PassRole（SageMaker用）
        sfn_role.add_to_policy(
            iam.PolicyStatement(
                sid="IAMPassRole",
                actions=["iam:PassRole"],
                resources=[sagemaker_role_arn] if sagemaker_role_arn else ["*"],
                conditions={"StringEquals": {"iam:PassedToService": "sagemaker.amazonaws.com"}},
            )
        )

        # SFn → CloudWatch Logs
        sfn_role.add_to_policy(
            iam.PolicyStatement(
                sid="CloudWatchLogs",
                actions=[
                    "logs:CreateLogDelivery",
                    "logs:GetLogDelivery",
                    "logs:UpdateLogDelivery",
                    "logs:DeleteLogDelivery",
                    "logs:ListLogDeliveries",
                    "logs:PutResourcePolicy",
                    "logs:DescribeResourcePolicies",
                    "logs:DescribeLogGroups",
                ],
                resources=["*"],
            )
        )

        # ===== Step Functions ログ =====
        sfn_log_group = logs.LogGroup(
            self,
            "PipelineLogGroup",
            log_group_name=f"/aws/stepfunctions/{prefix}-pipeline",
            retention=logs.RetentionDays.ONE_MONTH,
        )

        # ===== Step Functions ステートマシン =====
        # パイプライン定義（ASL: Amazon States Language）
        pipeline_definition = {
            "Comment": f"MLOps Pipeline for {env_name} environment",
            "StartAt": "DataPreparation",
            "States": {
                "DataPreparation": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::sagemaker:createProcessingJob.sync",
                    "Parameters": {
                        "ProcessingJobName.$": "States.Format('data-prep-{}', $$.Execution.Name)",
                        "RoleArn": sagemaker_role_arn,
                        "ProcessingResources": {
                            "ClusterConfig": {
                                "InstanceCount": 1,
                                "InstanceType": "ml.t3.medium",
                                "VolumeSizeInGB": 30,
                            }
                        },
                        "AppSpecification": {
                            "ImageUri.$": "$.container_image",
                        },
                    },
                    "ResultPath": "$.data_prep_result",
                    "Next": "ModelTraining",
                    "Catch": [
                        {
                            "ErrorEquals": ["States.ALL"],
                            "Next": "PipelineFailed",
                            "ResultPath": "$.error",
                        }
                    ],
                },
                "ModelTraining": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::sagemaker:createTrainingJob.sync",
                    "Parameters": {
                        "TrainingJobName.$": "States.Format('train-{}', $$.Execution.Name)",
                        "RoleArn": sagemaker_role_arn,
                        "AlgorithmSpecification": {
                            "TrainingImage.$": "$.container_image",
                            "TrainingInputMode": "File",
                        },
                        "ResourceConfig": {
                            "InstanceCount": 1,
                            "InstanceType": "ml.m5.large",
                            "VolumeSizeInGB": 50,
                        },
                        "StoppingCondition": {"MaxRuntimeInSeconds": 3600},
                        "InputDataConfig": [
                            {
                                "ChannelName": "train",
                                "DataSource": {
                                    "S3DataSource": {
                                        "S3DataType": "S3Prefix",
                                        "S3Uri.$": "$.train_data_s3_uri",
                                    }
                                },
                            }
                        ],
                        "OutputDataConfig": {"S3OutputPath.$": "$.model_output_s3_uri"},
                    },
                    "ResultPath": "$.training_result",
                    "Next": "ModelEvaluation",
                    "Catch": [
                        {
                            "ErrorEquals": ["States.ALL"],
                            "Next": "PipelineFailed",
                            "ResultPath": "$.error",
                        }
                    ],
                },
                "ModelEvaluation": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::sagemaker:createProcessingJob.sync",
                    "Parameters": {
                        "ProcessingJobName.$": "States.Format('eval-{}', $$.Execution.Name)",
                        "RoleArn": sagemaker_role_arn,
                        "ProcessingResources": {
                            "ClusterConfig": {
                                "InstanceCount": 1,
                                "InstanceType": "ml.t3.medium",
                                "VolumeSizeInGB": 30,
                            }
                        },
                        "AppSpecification": {
                            "ImageUri.$": "$.container_image",
                        },
                    },
                    "ResultPath": "$.evaluation_result",
                    "Next": "EvaluationCheck",
                    "Catch": [
                        {
                            "ErrorEquals": ["States.ALL"],
                            "Next": "PipelineFailed",
                            "ResultPath": "$.error",
                        }
                    ],
                },
                "EvaluationCheck": {
                    "Type": "Choice",
                    "Choices": [
                        {
                            "Variable": "$.evaluation_result.approved",
                            "BooleanEquals": True,
                            "Next": "ModelDeployment",
                        }
                    ],
                    "Default": "PipelineFailed",
                },
                "ModelDeployment": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::sagemaker:createEndpoint",
                    "Parameters": {
                        "EndpointName.$": "States.Format('"
                        + prefix
                        + "-endpoint-{}', $$.Execution.Name)",
                        "EndpointConfigName.$": "$.endpoint_config_name",
                    },
                    "ResultPath": "$.deployment_result",
                    "Next": "PipelineSucceeded",
                    "Catch": [
                        {
                            "ErrorEquals": ["States.ALL"],
                            "Next": "PipelineFailed",
                            "ResultPath": "$.error",
                        }
                    ],
                },
                "PipelineSucceeded": {
                    "Type": "Succeed",
                },
                "PipelineFailed": {
                    "Type": "Fail",
                    "Cause": "Pipeline step failed",
                    "Error": "PipelineError",
                },
            },
        }

        self.state_machine = sfn.CfnStateMachine(
            self,
            "MLOpsPipeline",
            state_machine_name=f"{prefix}-pipeline",
            role_arn=sfn_role.role_arn,
            definition=pipeline_definition,
            state_machine_type="STANDARD",
            logging_configuration=sfn.CfnStateMachine.LoggingConfigurationProperty(
                destinations=[
                    sfn.CfnStateMachine.LogDestinationProperty(
                        cloud_watch_logs_log_group=sfn.CfnStateMachine.CloudWatchLogsLogGroupProperty(
                            log_group_arn=sfn_log_group.log_group_arn,
                        )
                    )
                ],
                include_execution_data=True,
                level="ALL",
            ),
        )

        # ===== EventBridge: 定期再学習スケジュール =====
        # 本番環境のみ週次スケジュールを有効化
        retrain_schedule_enabled = env_name == "prod"

        # EventBridge → Step Functions 実行ロール
        eventbridge_role = iam.Role(
            self,
            "EventBridgeRole",
            role_name=f"{prefix}-eventbridge-sfn-role",
            assumed_by=iam.ServicePrincipal("events.amazonaws.com"),
            description="EventBridge role to start Step Functions executions",
        )

        eventbridge_role.add_to_policy(
            iam.PolicyStatement(
                sid="StartStepFunctions",
                actions=["states:StartExecution"],
                resources=[
                    f"arn:aws:states:{self.region}:{self.account}"
                    f":stateMachine:{prefix}-pipeline"
                ],
            )
        )

        self.retrain_rule = events.Rule(
            self,
            "WeeklyRetrainSchedule",
            rule_name=f"{prefix}-weekly-retrain",
            description=f"Weekly retrain trigger for {env_name}",
            schedule=events.Schedule.cron(
                minute="0",
                hour="2",
                week_day="MON",
            ),
            enabled=retrain_schedule_enabled,
        )

        self.retrain_rule.add_target(
            targets.SfnStateMachine(
                sfn.StateMachine.from_state_machine_arn(
                    self,
                    "ImportedPipeline",
                    state_machine_arn=(
                        f"arn:aws:states:{self.region}:{self.account}"
                        f":stateMachine:{prefix}-pipeline"
                    ),
                ),
                role=eventbridge_role,
            )
        )

        # ===== Outputs =====
        CfnOutput(
            self,
            "StateMachineArn",
            value=(
                f"arn:aws:states:{self.region}:{self.account}" f":stateMachine:{prefix}-pipeline"
            ),
            description="Step Functions state machine ARN",
            export_name=f"{prefix}-pipeline-arn",
        )

        CfnOutput(
            self,
            "RetrainRuleName",
            value=self.retrain_rule.rule_name,
            description="EventBridge retrain schedule rule",
            export_name=f"{prefix}-retrain-rule",
        )
