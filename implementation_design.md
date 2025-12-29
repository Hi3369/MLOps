# 統合MLOps MCPサーバー 実装設計書

**バージョン**: 0.1
**作成日**: 2025-12-27
**対象**: 統合MLOps MCPサーバー（11個のCapability）

---

## 1. 概要

本書は、統合MLOps MCPサーバーの詳細な実装設計を定義します。[mcp_design.md](mcp_design.md)および[architecture_design.md](architecture_design.md)で定義されたアーキテクチャを実装レベルに落とし込みます。

### 1.1 実装範囲

**Phase 1（Week 1-6）**: コアMLOps Capability実装

- 統合サーバーの基盤構築
- Capability 1: Data Preparation
- Capability 2: ML Training
- Capability 3: ML Evaluation

**Phase 2（Week 7-12）**: 統合Capability実装

- Capability 4: GitHub Integration
- Capability 5: Model Registry
- Capability 6: Notification

**Phase 3（Week 13-14）**: E2Eテスト・最適化

### 1.2 技術スタック

| カテゴリ               | 技術            | バージョン |
| ---------------------- | --------------- | ---------- |
| **言語**               | Python          | 3.11+      |
| **MCPフレームワーク**  | mcp             | 1.0.0+     |
| **AWS SDK**            | boto3           | 1.34.0+    |
| **機械学習**           | scikit-learn    | 1.4.0+     |
|                        | xgboost         | 2.0.0+     |
|                        | tensorflow      | 2.15.0+    |
|                        | pytorch         | 2.1.0+     |
| **強化学習**           | ray[rllib]      | 2.9.0+     |
| **GitHub API**         | PyGithub        | 2.1.1+     |
| **通知**               | slack-sdk       | 3.26.0+    |
| **テスト**             | pytest          | 8.0.0+     |
|                        | pytest-asyncio  | 0.23.0+    |
|                        | pytest-cov      | 4.1.0+     |
| **リンター**           | ruff            | 0.1.0+     |
|                        | mypy            | 1.8.0+     |
| **コンテナ**           | Docker          | 24.0+      |

---

## 2. ディレクトリ構造詳細

```text
mcp_server/
├── __init__.py                         # パッケージ初期化
├── __main__.py                         # エントリーポイント
├── server.py                           # メインサーバー実装
├── config.py                           # 設定管理
├── router.py                           # ツールルーティング
│
├── capabilities/                       # 11個のCapability実装
│   ├── __init__.py
│   ├── base.py                        # 基底Capabilityクラス
│   │
│   ├── data_preparation/              # Capability 1
│   │   ├── __init__.py
│   │   ├── capability.py              # DataPreparationCapability
│   │   ├── schemas.py                 # Pydanticスキーマ定義
│   │   └── tools/
│   │       ├── __init__.py
│   │       ├── load_dataset.py
│   │       ├── validate_data.py
│   │       ├── preprocess_supervised.py
│   │       ├── preprocess_unsupervised.py
│   │       ├── preprocess_reinforcement.py
│   │       ├── feature_engineering.py
│   │       ├── split_dataset.py
│   │       └── save_processed_data.py
│   │
│   ├── ml_training/                   # Capability 2
│   │   ├── __init__.py
│   │   ├── capability.py              # MLTrainingCapability
│   │   ├── schemas.py
│   │   └── tools/
│   │       ├── __init__.py
│   │       ├── supervised/
│   │       │   ├── __init__.py
│   │       │   ├── random_forest.py
│   │       │   ├── xgboost.py
│   │       │   └── neural_network.py
│   │       ├── unsupervised/
│   │       │   ├── __init__.py
│   │       │   ├── kmeans.py
│   │       │   ├── dbscan.py
│   │       │   ├── pca.py
│   │       │   └── tsne.py
│   │       ├── reinforcement/
│   │       │   ├── __init__.py
│   │       │   ├── ppo.py
│   │       │   ├── dqn.py
│   │       │   └── a3c.py
│   │       ├── get_training_metrics.py
│   │       └── save_model.py
│   │
│   ├── ml_evaluation/                 # Capability 3
│   │   ├── __init__.py
│   │   ├── capability.py              # MLEvaluationCapability
│   │   ├── schemas.py
│   │   └── tools/
│   │       ├── __init__.py
│   │       ├── load_model.py
│   │       ├── evaluate_classifier.py
│   │       ├── evaluate_regressor.py
│   │       ├── evaluate_clustering.py
│   │       ├── evaluate_reinforcement.py
│   │       ├── compare_models.py
│   │       ├── generate_report.py
│   │       └── visualization.py
│   │
│   ├── github_integration/            # Capability 4
│   │   ├── __init__.py
│   │   ├── capability.py              # GitHubIntegrationCapability
│   │   ├── schemas.py
│   │   └── tools/
│   │       ├── __init__.py
│   │       ├── issue_management.py
│   │       ├── label_management.py
│   │       ├── repository_operations.py
│   │       ├── webhook_handler.py
│   │       └── parser.py
│   │
│   ├── model_registry/                # Capability 5
│   │   ├── __init__.py
│   │   ├── capability.py              # ModelRegistryCapability
│   │   ├── schemas.py
│   │   └── tools/
│   │       ├── __init__.py
│   │       ├── model_registration.py
│   │       ├── version_management.py
│   │       ├── status_management.py
│   │       ├── rollback.py
│   │       └── search.py
│   │
│   └── notification/                  # Capability 6
│       ├── __init__.py
│       ├── capability.py              # NotificationCapability
│       ├── schemas.py
│       └── tools/
│           ├── __init__.py
│           ├── slack_notifier.py
│           ├── email_notifier.py
│           ├── teams_notifier.py
│           ├── discord_notifier.py
│           └── template_manager.py
│
├── common/                            # 共通ユーティリティ
│   ├── __init__.py
│   ├── s3_utils.py                   # S3操作ヘルパー
│   ├── secrets.py                    # Secrets Manager統合
│   ├── logger.py                     # 構造化ロギング
│   ├── exceptions.py                 # カスタム例外
│   └── metrics.py                    # CloudWatch Metrics統合
│
├── Dockerfile                        # ECS Fargate用
├── Dockerfile.lambda                 # Lambda用（オプション）
├── requirements.txt                  # 依存関係
├── requirements-dev.txt              # 開発用依存関係
└── pyproject.toml                    # プロジェクト設定（ruff, mypy等）
```

---

## 3. コアコンポーネント実装

### 3.1 メインサーバー（server.py）

```python
"""統合MLOps MCPサーバーのメイン実装"""
import asyncio
from typing import Any

from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

from .config import Config
from .router import ToolRouter
from .capabilities import (
    DataPreparationCapability,
    MLTrainingCapability,
    MLEvaluationCapability,
    GitHubIntegrationCapability,
    ModelRegistryCapability,
    NotificationCapability,
)
from .common.logger import get_logger
from .common.exceptions import MCPServerError

logger = get_logger(__name__)


class UnifiedMLOpsMCPServer:
    """統合MLOps MCPサーバー"""

    def __init__(self, config: Config):
        self.config = config
        self.server = Server("unified-mlops-mcp-server")

        # Capabilityの初期化
        self.capabilities = {
            "data_preparation": DataPreparationCapability(config),
            "ml_training": MLTrainingCapability(config),
            "ml_evaluation": MLEvaluationCapability(config),
            "github_integration": GitHubIntegrationCapability(config),
            "model_registry": ModelRegistryCapability(config),
            "notification": NotificationCapability(config),
        }

        # ツールルーター初期化
        self.router = ToolRouter(self.capabilities)

        # MCPハンドラー登録
        self._register_handlers()

        logger.info("Unified MLOps MCP Server initialized")

    def _register_handlers(self):
        """MCPハンドラーを登録"""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """全Capabilityのツール一覧を返す"""
            tools = []
            for capability in self.capabilities.values():
                tools.extend(capability.list_tools())
            logger.info(f"Listed {len(tools)} tools")
            return tools

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent | ImageContent | EmbeddedResource]:
            """ツールを実行（適切なCapabilityにルーティング）"""
            try:
                logger.info(f"Tool call: {name}", extra={
                    "tool_name": name,
                    "arguments": self._mask_secrets(arguments),
                })

                # ツールルーターで適切なCapabilityに振り分け
                result = await self.router.route_tool_call(name, arguments)

                logger.info(f"Tool call succeeded: {name}", extra={
                    "tool_name": name,
                    "status": "success",
                })

                return result

            except Exception as e:
                logger.error(f"Tool call failed: {name}", extra={
                    "tool_name": name,
                    "error": str(e),
                    "status": "error",
                }, exc_info=True)
                raise MCPServerError(f"Tool execution failed: {str(e)}") from e

    def _mask_secrets(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """機密情報をマスク"""
        masked = arguments.copy()
        secret_keys = {"token", "password", "api_key", "webhook_url"}

        for key in masked:
            if any(secret in key.lower() for secret in secret_keys):
                masked[key] = "***masked***"

        return masked

    async def run(self):
        """サーバーを起動"""
        from mcp.server.stdio import stdio_server

        logger.info("Starting Unified MLOps MCP Server")
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )
```

### 3.2 ツールルーター（router.py）

```python
"""ツールルーティング機構"""
from typing import Any

from mcp.types import TextContent, ImageContent, EmbeddedResource

from .common.logger import get_logger
from .common.exceptions import ToolNotFoundError

logger = get_logger(__name__)


class ToolRouter:
    """ツールを適切なCapabilityにルーティング"""

    def __init__(self, capabilities: dict):
        self.capabilities = capabilities
        self._tool_mapping = self._build_tool_mapping()

    def _build_tool_mapping(self) -> dict[str, str]:
        """ツール名 → Capability名のマッピングを構築"""
        mapping = {}

        for capability_name, capability in self.capabilities.items():
            for tool in capability.list_tools():
                if tool.name in mapping:
                    raise ValueError(
                        f"Tool name collision: {tool.name} is defined in multiple capabilities"
                    )
                mapping[tool.name] = capability_name

        logger.info(f"Built tool mapping: {len(mapping)} tools")
        return mapping

    async def route_tool_call(
        self,
        tool_name: str,
        arguments: dict[str, Any]
    ) -> list[TextContent | ImageContent | EmbeddedResource]:
        """ツール呼び出しを適切なCapabilityにルーティング"""

        # ツール名からCapabilityを特定
        capability_name = self._tool_mapping.get(tool_name)

        if not capability_name:
            raise ToolNotFoundError(f"Tool not found: {tool_name}")

        # Capabilityを取得
        capability = self.capabilities[capability_name]

        # ツールを実行
        logger.debug(f"Routing {tool_name} to {capability_name}")
        return await capability.execute_tool(tool_name, arguments)
```

### 3.3 設定管理（config.py）

```python
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
```

### 3.4 基底Capabilityクラス（capabilities/base.py）

```python
"""基底Capabilityクラス"""
from abc import ABC, abstractmethod
from typing import Any

from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

from ..config import Config
from ..common.logger import get_logger

logger = get_logger(__name__)


class BaseCapability(ABC):
    """すべてのCapabilityの基底クラス"""

    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    def list_tools(self) -> list[Tool]:
        """このCapabilityが提供するツール一覧を返す"""
        pass

    @abstractmethod
    async def execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any]
    ) -> list[TextContent | ImageContent | EmbeddedResource]:
        """ツールを実行"""
        pass
```

---

## 4. Capability別実装詳細

### 4.1 Capability 1: Data Preparation

**ファイル**: `capabilities/data_preparation/capability.py`

```python
"""Data Preparation Capability実装"""
from typing import Any

from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

from ..base import BaseCapability
from .tools import (
    load_dataset,
    validate_data,
    preprocess_supervised,
    preprocess_unsupervised,
    preprocess_reinforcement,
    feature_engineering,
    split_dataset,
    save_processed_data,
)


class DataPreparationCapability(BaseCapability):
    """データ前処理・特徴量エンジニアリング"""

    def list_tools(self) -> list[Tool]:
        """提供ツール一覧"""
        return [
            Tool(
                name="load_dataset",
                description="S3からデータセットを読み込む",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "s3_uri": {"type": "string", "description": "S3 URI (s3://bucket/key)"},
                        "file_format": {"type": "string", "enum": ["csv", "parquet", "json"], "default": "csv"},
                    },
                    "required": ["s3_uri"],
                },
            ),
            Tool(
                name="validate_data",
                description="データのバリデーション（欠損値、型チェック等）",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "data_s3_uri": {"type": "string"},
                        "schema": {"type": "object", "description": "期待されるスキーマ"},
                    },
                    "required": ["data_s3_uri"],
                },
            ),
            Tool(
                name="preprocess_supervised",
                description="教師あり学習用の前処理",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "dataset_s3_uri": {"type": "string"},
                        "target_column": {"type": "string"},
                        "task_type": {"type": "string", "enum": ["classification", "regression"]},
                        "preprocessing_config": {
                            "type": "object",
                            "properties": {
                                "normalize": {"type": "boolean", "default": True},
                                "handle_missing": {"type": "string", "enum": ["drop", "mean", "median", "mode"], "default": "mean"},
                                "encode_categorical": {"type": "boolean", "default": True},
                            },
                        },
                    },
                    "required": ["dataset_s3_uri", "target_column", "task_type"],
                },
            ),
            # ... 他のツール定義
        ]

    async def execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any]
    ) -> list[TextContent | ImageContent | EmbeddedResource]:
        """ツール実行"""

        tool_map = {
            "load_dataset": load_dataset.execute,
            "validate_data": validate_data.execute,
            "preprocess_supervised": preprocess_supervised.execute,
            "preprocess_unsupervised": preprocess_unsupervised.execute,
            "preprocess_reinforcement": preprocess_reinforcement.execute,
            "feature_engineering": feature_engineering.execute,
            "split_dataset": split_dataset.execute,
            "save_processed_data": save_processed_data.execute,
        }

        tool_func = tool_map.get(tool_name)
        if not tool_func:
            raise ValueError(f"Unknown tool: {tool_name}")

        return await tool_func(self.config, arguments)
```

**ツール実装例**: `capabilities/data_preparation/tools/preprocess_supervised.py`

```python
"""教師あり学習用の前処理ツール"""
import pandas as pd
from sklearn.preprocessing import StandardScaler, LabelEncoder
from mcp.types import TextContent, EmbeddedResource

from ...common.s3_utils import S3Utils
from ...common.logger import get_logger

logger = get_logger(__name__)


async def execute(config, arguments: dict) -> list:
    """教師あり学習用の前処理を実行"""

    dataset_s3_uri = arguments["dataset_s3_uri"]
    target_column = arguments["target_column"]
    task_type = arguments["task_type"]
    preprocessing_config = arguments.get("preprocessing_config", {})

    logger.info(f"Starting supervised preprocessing: {dataset_s3_uri}")

    # S3からデータロード
    s3_utils = S3Utils(config)
    df = await s3_utils.read_dataframe(dataset_s3_uri)

    # ターゲットと特徴量を分離
    X = df.drop(columns=[target_column])
    y = df[target_column]

    # 欠損値処理
    if preprocessing_config.get("handle_missing", "mean") != "drop":
        strategy = preprocessing_config["handle_missing"]
        X = X.fillna(X.mean() if strategy == "mean" else X.median())
    else:
        X = X.dropna()

    # カテゴリカル変数のエンコーディング
    if preprocessing_config.get("encode_categorical", True):
        for col in X.select_dtypes(include=["object"]).columns:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col])

    # 正規化
    if preprocessing_config.get("normalize", True):
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        X = pd.DataFrame(X_scaled, columns=X.columns)

    # 処理済みデータを結合
    processed_df = pd.concat([X, y], axis=1)

    # S3に保存
    output_s3_uri = dataset_s3_uri.replace(".csv", "_processed.csv")
    await s3_utils.write_dataframe(processed_df, output_s3_uri)

    logger.info(f"Preprocessing completed: {output_s3_uri}")

    return [
        TextContent(
            type="text",
            text=f"データ前処理が完了しました。処理済みデータ: {output_s3_uri}"
        ),
        EmbeddedResource(
            type="resource",
            resource={
                "uri": output_s3_uri,
                "name": "処理済み学習データ",
                "mimeType": "text/csv"
            }
        )
    ]
```

### 4.2 Capability 2: ML Training

**主要ツール実装**: `capabilities/ml_training/tools/supervised/random_forest.py`

```python
"""Random Forest分類器の学習ツール"""
import joblib
from sklearn.ensemble import RandomForestClassifier
from mcp.types import TextContent, EmbeddedResource

from ....common.s3_utils import S3Utils
from ....common.logger import get_logger

logger = get_logger(__name__)


async def execute(config, arguments: dict) -> list:
    """Random Forest分類モデルを学習"""

    train_data_s3_uri = arguments["train_data_s3_uri"]
    target_column = arguments.get("target_column", "target")
    hyperparameters = arguments.get("hyperparameters", {})
    model_output_s3_uri = arguments["model_output_s3_uri"]

    logger.info(f"Training Random Forest classifier: {train_data_s3_uri}")

    # データロード
    s3_utils = S3Utils(config)
    df = await s3_utils.read_dataframe(train_data_s3_uri)

    X = df.drop(columns=[target_column])
    y = df[target_column]

    # モデル学習
    model = RandomForestClassifier(
        n_estimators=hyperparameters.get("n_estimators", 100),
        max_depth=hyperparameters.get("max_depth", None),
        random_state=42
    )
    model.fit(X, y)

    # モデル保存
    model_path = "/tmp/model.pkl"
    joblib.dump(model, model_path)
    await s3_utils.upload_file(model_path, model_output_s3_uri)

    # 学習メトリクス
    train_accuracy = model.score(X, y)

    logger.info(f"Training completed. Accuracy: {train_accuracy:.4f}")

    return [
        TextContent(
            type="text",
            text=f"Random Forest分類モデルの学習が完了しました。Train Accuracy: {train_accuracy:.4f}"
        ),
        EmbeddedResource(
            type="resource",
            resource={
                "uri": model_output_s3_uri,
                "name": "学習済みモデル",
                "mimeType": "application/octet-stream"
            }
        )
    ]
```

### 4.3 共通ユーティリティ

**S3操作**: `common/s3_utils.py`

```python
"""S3操作ユーティリティ"""
import io
import pandas as pd
import boto3
from botocore.exceptions import ClientError

from .logger import get_logger

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
            raise

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
            raise

    def _parse_s3_uri(self, s3_uri: str) -> tuple[str, str]:
        """S3 URIをbucketとkeyにパース"""
        if not s3_uri.startswith('s3://'):
            raise ValueError(f"Invalid S3 URI: {s3_uri}")

        parts = s3_uri[5:].split('/', 1)
        bucket = parts[0]
        key = parts[1] if len(parts) > 1 else ''

        return bucket, key
```

**Secrets Manager統合**: `common/secrets.py`

```python
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
        self.client = boto3.client('secretsmanager', region_name=config.aws_region)

    @lru_cache(maxsize=10)
    def get_secret(self, secret_name: str) -> dict:
        """シークレットを取得（キャッシュあり）"""
        full_secret_name = f"{self.config.secrets_prefix}{secret_name}"

        try:
            response = self.client.get_secret_value(SecretId=full_secret_name)
            secret = json.loads(response['SecretString'])
            logger.info(f"Retrieved secret: {full_secret_name}")
            return secret

        except ClientError as e:
            logger.error(f"Failed to retrieve secret: {full_secret_name}", exc_info=True)
            raise
```

**構造化ロギング**: `common/logger.py`

```python
"""構造化ロギング"""
import logging
import json
import sys
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """JSON形式のログフォーマッター"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # 追加フィールド
        if hasattr(record, 'tool_name'):
            log_data['tool_name'] = record.tool_name
        if hasattr(record, 'capability'):
            log_data['capability'] = record.capability
        if hasattr(record, 'duration_ms'):
            log_data['duration_ms'] = record.duration_ms
        if hasattr(record, 'status'):
            log_data['status'] = record.status

        # エラー情報
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def get_logger(name: str) -> logging.Logger:
    """構造化ロガーを取得"""
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger
```

---

## 5. エラーハンドリング

**カスタム例外**: `common/exceptions.py`

```python
"""カスタム例外定義"""


class MCPServerError(Exception):
    """MCPサーバーの基底例外"""
    pass


class ToolNotFoundError(MCPServerError):
    """ツールが見つからない"""
    pass


class ToolExecutionError(MCPServerError):
    """ツール実行エラー"""
    pass


class S3Error(MCPServerError):
    """S3操作エラー"""
    pass


class SecretsManagerError(MCPServerError):
    """Secrets Manager操作エラー"""
    pass


class ValidationError(MCPServerError):
    """入力検証エラー"""
    pass
```

---

## 6. デプロイメント

### 6.1 Dockerfile（ECS Fargate用）

```dockerfile
FROM python:3.11-slim

# 作業ディレクトリ
WORKDIR /app

# システム依存関係
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Python依存関係
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコード
COPY mcp_server/ ./mcp_server/

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# エントリーポイント
ENTRYPOINT ["python", "-m", "mcp_server"]
```

### 6.2 requirements.txt

```txt
# MCPフレームワーク
mcp==1.0.0

# AWS SDK
boto3==1.34.0
botocore==1.34.0

# 機械学習
scikit-learn==1.4.0
xgboost==2.0.0
tensorflow==2.15.0
torch==2.1.0

# 強化学習
ray[rllib]==2.9.0

# データ処理
pandas==2.2.0
numpy==1.26.0
pyarrow==15.0.0

# GitHub API
PyGithub==2.1.1

# 通知
slack-sdk==3.26.0

# ユーティリティ
pydantic==2.5.0
python-dotenv==1.0.0
```

### 6.3 環境変数

```bash
# AWS設定
AWS_REGION=us-east-1
MLOPS_S3_BUCKET=mlops-data-bucket

# Secrets Manager
MLOPS_SECRETS_PREFIX=mlops/

# ログ設定
LOG_LEVEL=INFO
CLOUDWATCH_LOG_GROUP=/aws/mcp/unified-mlops-server
CLOUDWATCH_LOG_STREAM=production

# SageMaker
SAGEMAKER_ROLE_ARN=arn:aws:iam::123456789012:role/SageMakerExecutionRole
```

---

## 7. セキュリティ実装

### 7.1 IAMロールポリシー（CDK実装例）

```python
from aws_cdk import (
    aws_iam as iam,
    aws_ecs as ecs,
)

# ECS Task Role
task_role = iam.Role(
    self, "MCPServerTaskRole",
    assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
    inline_policies={
        "MCPServerPolicy": iam.PolicyDocument(
            statements=[
                # S3アクセス
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:ListBucket"
                    ],
                    resources=[
                        f"arn:aws:s3:::{bucket_name}",
                        f"arn:aws:s3:::{bucket_name}/*"
                    ]
                ),
                # Secrets Managerアクセス
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["secretsmanager:GetSecretValue"],
                    resources=[
                        f"arn:aws:secretsmanager:*:*:secret:mlops/*"
                    ]
                ),
                # SageMakerアクセス
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "sagemaker:CreateTrainingJob",
                        "sagemaker:DescribeTrainingJob",
                        "sagemaker:CreateModel"
                    ],
                    resources=["*"],
                    conditions={
                        "StringEquals": {
                            "aws:RequestedRegion": "us-east-1"
                        }
                    }
                ),
            ]
        )
    }
)
```

---

## 8. 変更履歴

| バージョン | 日付       | 変更内容 | 作成者 |
| ---------- | ---------- | -------- | ------ |
| 0.1        | 2025-12-27 | 初版発行 | -      |
