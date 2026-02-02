"""
MLflow Integration Adapter

MLflow Tracking Serverとの統合を提供します。
実験追跡・モデルレジストリのデータをMLflowと双方向同期します。
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class MLflowAdapter:
    """
    MLflow統合アダプタ

    MLOps MCP Serverの実験追跡・モデルレジストリをMLflowと連携します。

    環境変数:
        MLFLOW_TRACKING_URI: MLflow Tracking Server URI
        MLFLOW_EXPERIMENT_NAME: デフォルト実験名
        MLFLOW_S3_ENDPOINT_URL: S3互換エンドポイント（オプション）
    """

    def __init__(
        self,
        tracking_uri: Optional[str] = None,
        experiment_name: Optional[str] = None,
    ):
        self.tracking_uri = tracking_uri or os.environ.get(
            "MLFLOW_TRACKING_URI", "http://localhost:5000"
        )
        self.experiment_name = experiment_name or os.environ.get(
            "MLFLOW_EXPERIMENT_NAME", "mlops-default"
        )
        self._client: Optional[Any] = None
        logger.info(f"MLflowAdapter initialized: uri={self.tracking_uri}")

    def _get_client(self) -> Any:
        """MLflowクライアントを取得（遅延初期化）"""
        if self._client is None:
            try:
                import mlflow

                mlflow.set_tracking_uri(self.tracking_uri)
                self._client = mlflow.MlflowClient(self.tracking_uri)
            except ImportError:
                raise ImportError("mlflow package is required. Install with: pip install mlflow")
        return self._client

    def sync_experiment(
        self,
        experiment_id: str,
        parameters: Dict[str, Any],
        metrics: Dict[str, float],
        tags: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        実験データをMLflowに同期

        Args:
            experiment_id: MCP Server側の実験ID
            parameters: ハイパーパラメータ
            metrics: メトリクス
            tags: タグ

        Returns:
            同期結果辞書
        """
        if not experiment_id:
            raise ValueError("experiment_id must not be empty")

        logger.info(f"Syncing experiment {experiment_id} to MLflow")

        env = os.environ.get("MLOPS_ENV", "development")
        timestamp = datetime.now(timezone.utc).isoformat()
        sync_id = str(uuid4())[:8]

        if env in ["development", "test"]:
            return _mock_sync_experiment(
                experiment_id=experiment_id,
                parameters=parameters,
                metrics=metrics,
                tags=tags,
                sync_id=sync_id,
                timestamp=timestamp,
            )

        # 本番環境: MLflow APIを呼び出し
        import mlflow

        mlflow.set_tracking_uri(self.tracking_uri)
        mlflow.set_experiment(self.experiment_name)

        with mlflow.start_run(run_name=f"mcp-{experiment_id}") as run:
            mlflow.log_params(parameters)
            mlflow.log_metrics(metrics)
            if tags:
                mlflow.set_tags(tags)
            mlflow.set_tag("mcp_experiment_id", experiment_id)

            return {
                "status": "success",
                "sync_id": sync_id,
                "mlflow_run_id": run.info.run_id,
                "mlflow_experiment_id": run.info.experiment_id,
                "mcp_experiment_id": experiment_id,
                "parameters_synced": len(parameters),
                "metrics_synced": len(metrics),
                "synced_at": timestamp,
            }

    def sync_model(
        self,
        model_name: str,
        model_version: str,
        model_uri: str,
        metrics: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        モデルをMLflowモデルレジストリに登録

        Args:
            model_name: モデル名
            model_version: セマンティックバージョン
            model_uri: モデルアーティファクトのS3 URI
            metrics: 評価メトリクス

        Returns:
            登録結果辞書
        """
        if not model_name:
            raise ValueError("model_name must not be empty")
        if not model_uri:
            raise ValueError("model_uri must not be empty")

        logger.info(f"Syncing model {model_name} v{model_version} to MLflow")

        env = os.environ.get("MLOPS_ENV", "development")
        timestamp = datetime.now(timezone.utc).isoformat()
        sync_id = str(uuid4())[:8]

        if env in ["development", "test"]:
            return _mock_sync_model(
                model_name=model_name,
                model_version=model_version,
                model_uri=model_uri,
                metrics=metrics,
                sync_id=sync_id,
                timestamp=timestamp,
            )

        # 本番環境
        import mlflow

        mlflow.set_tracking_uri(self.tracking_uri)
        mlflow.set_experiment(self.experiment_name)

        with mlflow.start_run(run_name=f"model-{model_name}-{model_version}"):
            if metrics:
                mlflow.log_metrics(metrics)
            mlflow.set_tag("model_version", model_version)
            mlflow.set_tag("model_uri", model_uri)

            result = mlflow.register_model(
                model_uri=model_uri,
                name=model_name,
            )

            return {
                "status": "success",
                "sync_id": sync_id,
                "model_name": model_name,
                "model_version": model_version,
                "mlflow_model_version": result.version,
                "synced_at": timestamp,
            }

    def get_config(self) -> Dict[str, Any]:
        """現在の設定を返す"""
        return {
            "tracking_uri": self.tracking_uri,
            "experiment_name": self.experiment_name,
            "status": "configured",
        }


class WandbAdapter:
    """
    Weights & Biases統合アダプタ

    MLOps MCP Serverの実験追跡をW&Bと連携します。

    環境変数:
        WANDB_API_KEY: W&B APIキー
        WANDB_PROJECT: プロジェクト名
        WANDB_ENTITY: チーム/組織名
    """

    def __init__(
        self,
        project: Optional[str] = None,
        entity: Optional[str] = None,
    ):
        self.project = project or os.environ.get("WANDB_PROJECT", "mlops-pipeline")
        self.entity = entity or os.environ.get("WANDB_ENTITY")
        logger.info(f"WandbAdapter initialized: project={self.project}")

    def sync_experiment(
        self,
        experiment_id: str,
        parameters: Dict[str, Any],
        metrics: Dict[str, float],
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        実験データをW&Bに同期

        Args:
            experiment_id: MCP Server側の実験ID
            parameters: ハイパーパラメータ
            metrics: メトリクス
            tags: タグリスト

        Returns:
            同期結果辞書
        """
        if not experiment_id:
            raise ValueError("experiment_id must not be empty")

        logger.info(f"Syncing experiment {experiment_id} to W&B")

        env = os.environ.get("MLOPS_ENV", "development")
        timestamp = datetime.now(timezone.utc).isoformat()
        sync_id = str(uuid4())[:8]

        if env in ["development", "test"]:
            return _mock_wandb_sync(
                experiment_id=experiment_id,
                parameters=parameters,
                metrics=metrics,
                tags=tags,
                sync_id=sync_id,
                timestamp=timestamp,
                project=self.project,
                entity=self.entity,
            )

        # 本番環境: W&B APIを呼び出し
        try:
            import wandb
        except ImportError:
            raise ImportError("wandb package is required. Install with: pip install wandb")

        run = wandb.init(
            project=self.project,
            entity=self.entity,
            name=f"mcp-{experiment_id}",
            config=parameters,
            tags=tags or [],
        )

        wandb.log(metrics)
        wandb.finish()

        return {
            "status": "success",
            "sync_id": sync_id,
            "wandb_run_id": run.id if run else None,
            "wandb_run_url": run.url if run else None,
            "mcp_experiment_id": experiment_id,
            "project": self.project,
            "parameters_synced": len(parameters),
            "metrics_synced": len(metrics),
            "synced_at": timestamp,
        }

    def get_config(self) -> Dict[str, Any]:
        """現在の設定を返す"""
        return {
            "project": self.project,
            "entity": self.entity,
            "status": "configured",
        }


class DVCAdapter:
    """
    DVC (Data Version Control) 統合アダプタ

    MLOps MCP Serverのデータバージョニングをdvcと連携します。

    環境変数:
        DVC_REMOTE: DVCリモートストレージ名
        DVC_REMOTE_URL: リモートストレージURL
    """

    def __init__(
        self,
        remote_name: Optional[str] = None,
        remote_url: Optional[str] = None,
    ):
        self.remote_name = remote_name or os.environ.get("DVC_REMOTE", "s3remote")
        self.remote_url = remote_url or os.environ.get("DVC_REMOTE_URL", "")
        logger.info(f"DVCAdapter initialized: remote={self.remote_name}")

    def sync_dataset_version(
        self,
        dataset_name: str,
        version: str,
        s3_uri: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        データセットバージョンをDVCと同期

        Args:
            dataset_name: データセット名
            version: バージョン
            s3_uri: S3 URI
            metadata: メタデータ

        Returns:
            同期結果辞書
        """
        if not dataset_name:
            raise ValueError("dataset_name must not be empty")
        if not s3_uri:
            raise ValueError("s3_uri must not be empty")

        logger.info(f"Syncing dataset {dataset_name} v{version} to DVC")

        env = os.environ.get("MLOPS_ENV", "development")
        timestamp = datetime.now(timezone.utc).isoformat()
        sync_id = str(uuid4())[:8]

        if env in ["development", "test"]:
            return _mock_dvc_sync(
                dataset_name=dataset_name,
                version=version,
                s3_uri=s3_uri,
                metadata=metadata,
                sync_id=sync_id,
                timestamp=timestamp,
                remote_name=self.remote_name,
            )

        # 本番環境: DVC CLIを呼び出し
        import subprocess  # nosec B404

        try:
            # dvc add相当の操作
            result = subprocess.run(  # nosec B603 B607
                ["dvc", "import-url", s3_uri, f"data/{dataset_name}/{version}/"],
                capture_output=True,
                text=True,
                timeout=300,
                check=False,
            )

            return {
                "status": "success" if result.returncode == 0 else "error",
                "sync_id": sync_id,
                "dataset_name": dataset_name,
                "version": version,
                "s3_uri": s3_uri,
                "remote_name": self.remote_name,
                "dvc_output": result.stdout[:500] if result.stdout else "",
                "synced_at": timestamp,
            }

        except FileNotFoundError:
            raise ImportError("dvc CLI is required. Install with: pip install dvc[s3]")
        except subprocess.TimeoutExpired:
            raise ValueError("DVC sync timed out")

    def get_config(self) -> Dict[str, Any]:
        """現在の設定を返す"""
        return {
            "remote_name": self.remote_name,
            "remote_url": self.remote_url,
            "status": "configured",
        }


# ===== モック関数 =====


def _mock_sync_experiment(
    experiment_id: str,
    parameters: Dict[str, Any],
    metrics: Dict[str, float],
    tags: Optional[Dict[str, str]],
    sync_id: str,
    timestamp: str,
) -> Dict[str, Any]:
    """モック: MLflow実験同期"""
    return {
        "status": "success",
        "sync_id": sync_id,
        "mlflow_run_id": f"mock-run-{sync_id}",
        "mlflow_experiment_id": f"mock-exp-{sync_id}",
        "mcp_experiment_id": experiment_id,
        "parameters_synced": len(parameters),
        "metrics_synced": len(metrics),
        "synced_at": timestamp,
        "mock": True,
    }


def _mock_sync_model(
    model_name: str,
    model_version: str,
    model_uri: str,
    metrics: Optional[Dict[str, float]],
    sync_id: str,
    timestamp: str,
) -> Dict[str, Any]:
    """モック: MLflowモデル登録"""
    return {
        "status": "success",
        "sync_id": sync_id,
        "model_name": model_name,
        "model_version": model_version,
        "mlflow_model_version": "1",
        "synced_at": timestamp,
        "mock": True,
    }


def _mock_wandb_sync(
    experiment_id: str,
    parameters: Dict[str, Any],
    metrics: Dict[str, float],
    tags: Optional[List[str]],
    sync_id: str,
    timestamp: str,
    project: str,
    entity: Optional[str],
) -> Dict[str, Any]:
    """モック: W&B実験同期"""
    return {
        "status": "success",
        "sync_id": sync_id,
        "wandb_run_id": f"mock-wandb-{sync_id}",
        "wandb_run_url": f"https://wandb.ai/{entity or 'team'}/{project}/runs/mock-{sync_id}",
        "mcp_experiment_id": experiment_id,
        "project": project,
        "parameters_synced": len(parameters),
        "metrics_synced": len(metrics),
        "synced_at": timestamp,
        "mock": True,
    }


def _mock_dvc_sync(
    dataset_name: str,
    version: str,
    s3_uri: str,
    metadata: Optional[Dict[str, Any]],
    sync_id: str,
    timestamp: str,
    remote_name: str,
) -> Dict[str, Any]:
    """モック: DVCデータセット同期"""
    return {
        "status": "success",
        "sync_id": sync_id,
        "dataset_name": dataset_name,
        "version": version,
        "s3_uri": s3_uri,
        "remote_name": remote_name,
        "dvc_output": f"Importing {s3_uri} to data/{dataset_name}/{version}/",
        "synced_at": timestamp,
        "mock": True,
    }
