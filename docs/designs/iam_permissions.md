# IAM Permissions Reference

MLOps MCP Serverが必要とするIAM権限の一覧です。

## 概要

MLOps MCP Serverは12のCapabilityで構成され、各Capabilityは特定のAWSサービスへのアクセスを必要とします。

## Capability別必要権限

### Capability 1: GitHub Integration

外部サービス（GitHub API）を使用。AWSリソースへの直接アクセスなし。

### Capability 2: Workflow Optimization

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/mlops-*"
    }
  ]
}
```

### Capability 3: Data Preparation

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::mlops-*",
        "arn:aws:s3:::mlops-*/*"
      ]
    }
  ]
}
```

### Capability 4: ML Training

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::mlops-*/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sagemaker:CreateTrainingJob",
        "sagemaker:DescribeTrainingJob"
      ],
      "Resource": "*"
    }
  ]
}
```

### Capability 5: ML Evaluation

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::mlops-*/*"
    }
  ]
}
```

### Capability 6: Model Packaging

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::mlops-*/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:PutImage"
      ],
      "Resource": "*"
    }
  ]
}
```

### Capability 7: Model Deployment

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sagemaker:CreateModel",
        "sagemaker:CreateEndpointConfig",
        "sagemaker:CreateEndpoint",
        "sagemaker:UpdateEndpoint",
        "sagemaker:DeleteEndpoint",
        "sagemaker:DeleteEndpointConfig",
        "sagemaker:DeleteModel",
        "sagemaker:DescribeEndpoint",
        "sagemaker:DescribeEndpointConfig",
        "sagemaker:UpdateEndpointWeightsAndCapacities"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "application-autoscaling:RegisterScalableTarget",
        "application-autoscaling:DeregisterScalableTarget",
        "application-autoscaling:PutScalingPolicy",
        "application-autoscaling:DeleteScalingPolicy"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "iam:PassRole"
      ],
      "Resource": "arn:aws:iam::*:role/sagemaker-*"
    }
  ]
}
```

### Capability 8: Model Monitoring

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData",
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:PutMetricAlarm",
        "cloudwatch:DeleteAlarms",
        "cloudwatch:DescribeAlarms"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutDashboard",
        "cloudwatch:GetDashboard"
      ],
      "Resource": "arn:aws:cloudwatch::*:dashboard/mlops-*"
    }
  ]
}
```

### Capability 9: Retrain Management

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "states:StartExecution",
        "states:DescribeExecution"
      ],
      "Resource": "arn:aws:states:*:*:stateMachine:mlops-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "events:PutRule",
        "events:PutTargets",
        "events:DeleteRule",
        "events:RemoveTargets"
      ],
      "Resource": "arn:aws:events:*:*:rule/mlops-*"
    }
  ]
}
```

### Capability 10: Notification

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sns:Publish"
      ],
      "Resource": "arn:aws:sns:*:*:mlops-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ses:SendEmail"
      ],
      "Resource": "*"
    }
  ]
}
```

### Capability 11: History Management

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/mlops-*"
    }
  ]
}
```

### Capability 12: Model Registry

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sagemaker:CreateModelPackage",
        "sagemaker:CreateModelPackageGroup",
        "sagemaker:DescribeModelPackage",
        "sagemaker:DescribeModelPackageGroup",
        "sagemaker:ListModelPackages",
        "sagemaker:UpdateModelPackage"
      ],
      "Resource": "*"
    }
  ]
}
```

## 統合ポリシー

全Capabilityを使用する場合の統合ポリシーは、上記全ての権限を含みます。
本番環境では、最小権限の原則に従い、使用するCapabilityのみの権限を付与してください。

## 環境変数

| 変数名 | 説明 | 必須 |
|--------|------|------|
| `SAGEMAKER_EXECUTION_ROLE_ARN` | SageMaker実行ロールARN | Capability 7 |
| `SAGEMAKER_CONTAINER_IMAGE` | SageMakerコンテナイメージ | Capability 7 (オプション) |
| `MLOPS_ENV` | 環境識別子 (test/dev/prod) | 全体 (オプション) |
| `GITHUB_TOKEN` | GitHub APIトークン | Capability 1, 9, 10 |

## セキュリティ推奨事項

1. **最小権限の原則**: 使用するCapabilityのみの権限を付与
2. **リソース制限**: `Resource`にワイルドカード(`*`)の代わりに具体的なARNを指定
3. **条件キー**: `aws:RequestedRegion`等の条件キーで操作可能なリージョンを制限
4. **監査ログ**: CloudTrailで全API呼び出しを記録
