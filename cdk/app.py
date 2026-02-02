#!/usr/bin/env python3
"""
CDK Application Entry Point for MLOps Infrastructure

環境変数:
  CDK_DEFAULT_ACCOUNT: AWSアカウントID
  CDK_DEFAULT_REGION: AWSリージョン（デフォルト: ap-northeast-1）
  MLOPS_ENV: 環境名（dev / staging / prod、デフォルト: dev）
"""

import os

import aws_cdk as cdk
from stacks.judge_agent_stack import JudgeAgentStack
from stacks.mlops_foundation_stack import MLOpsFoundationStack
from stacks.pipeline_stack import PipelineStack
from stacks.sagemaker_stack import SageMakerStack

app = cdk.App()

# 環境設定
env_name = os.getenv("MLOPS_ENV", "dev")
aws_env = cdk.Environment(
    account=os.getenv("CDK_DEFAULT_ACCOUNT"),
    region=os.getenv("CDK_DEFAULT_REGION", "ap-northeast-1"),
)
project_name = "mlops"

# 1. Foundation Stack（S3, ECR, IAMロール）
foundation = MLOpsFoundationStack(
    app,
    f"MLOpsFoundation-{env_name.capitalize()}",
    env=aws_env,
    env_name=env_name,
    project_name=project_name,
    description=f"MLOps foundation resources ({env_name}): S3, ECR, IAM roles",
)

# 2. SageMaker Stack（モデルレジストリ、モニタリング）
sagemaker = SageMakerStack(
    app,
    f"MLOpsSageMaker-{env_name.capitalize()}",
    env=aws_env,
    env_name=env_name,
    project_name=project_name,
    sagemaker_role_arn=foundation.sagemaker_role.role_arn,
    data_bucket_name=foundation.data_bucket.bucket_name,
    description=f"MLOps SageMaker resources ({env_name}): model registry, monitoring",
)
sagemaker.add_dependency(foundation)

# 3. Pipeline Stack（Step Functions, EventBridge）
pipeline = PipelineStack(
    app,
    f"MLOpsPipeline-{env_name.capitalize()}",
    env=aws_env,
    env_name=env_name,
    project_name=project_name,
    sagemaker_role_arn=foundation.sagemaker_role.role_arn,
    data_bucket_name=foundation.data_bucket.bucket_name,
    description=f"MLOps pipeline ({env_name}): Step Functions, EventBridge",
)
pipeline.add_dependency(foundation)

# 4. Judge Agent Stack（Lambda）
judge_agent = JudgeAgentStack(
    app,
    f"MLOpsJudgeAgent-{env_name.capitalize()}",
    env=aws_env,
    description=f"Judge Agent for model evaluation judgment ({env_name})",
)

app.synth()
