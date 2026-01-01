#!/usr/bin/env python3
"""
CDK Application Entry Point for MLOps Infrastructure
"""

import os

import aws_cdk as cdk
from stacks.judge_agent_stack import JudgeAgentStack

app = cdk.App()

# Judge Agent Stack
JudgeAgentStack(
    app,
    "JudgeAgentStack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION", "us-west-2"),
    ),
    description="Judge Agent for model evaluation judgment and next action determination",
)

app.synth()
