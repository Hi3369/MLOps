"""
Train Clustering Model Tool

クラスタリングモデル学習ツール
"""

import io
import json
import logging
from typing import Any, Dict

import boto3
import joblib
import pandas as pd
from botocore.exceptions import ClientError
from sklearn.cluster import DBSCAN, KMeans
from sklearn.decomposition import PCA

logger = logging.getLogger(__name__)


def train_clustering(
    train_data_s3_uri: str,
    algorithm: str = "kmeans",
    hyperparameters: Dict[str, Any] = None,
    model_output_s3_uri: str = None,
    file_format: str = "csv",
) -> Dict[str, Any]:
    """
    クラスタリングモデルを学習

    Args:
        train_data_s3_uri: 学習データのS3 URI (前処理済みデータ)
        algorithm: アルゴリズム (kmeans, dbscan, pca)
        hyperparameters: ハイパーパラメータ辞書
        model_output_s3_uri: モデル保存先S3 URI
        file_format: ファイルフォーマット (csv, parquet)

    Returns:
        学習結果辞書
    """
    logger.info(f"Training clustering model with algorithm: {algorithm}")

    # S3 URIの解析
    if not train_data_s3_uri.startswith("s3://"):
        raise ValueError("Invalid S3 URI: must start with 's3://'")

    parts = train_data_s3_uri[5:].split("/", 1)
    if len(parts) != 2:
        raise ValueError("Invalid S3 URI format: s3://bucket/key required")

    bucket, key = parts

    # S3からデータ読み込み
    s3_client = boto3.client("s3")

    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        file_content = response["Body"].read()

        # データ読み込み
        if file_format.lower() == "csv":
            df = pd.read_csv(io.BytesIO(file_content))
        elif file_format.lower() == "parquet":
            df = pd.read_parquet(io.BytesIO(file_content))
        else:
            raise ValueError(f"Unsupported file format: {file_format}")

        logger.info(
            f"Loaded training data: {len(df)} samples, {len(df.columns)} features"
        )

    except ClientError as e:
        logger.error(f"S3 access error: {e}")
        raise ValueError(f"Failed to load data from S3: {e}")

    # 全データを特徴量として使用
    X_train = df

    # ハイパーパラメータのデフォルト設定
    if hyperparameters is None:
        hyperparameters = {}

    # アルゴリズムに応じたモデルの作成
    if algorithm == "kmeans":
        model = KMeans(
            n_clusters=hyperparameters.get("n_clusters", 3),
            random_state=hyperparameters.get("random_state", 42),
            n_init=hyperparameters.get("n_init", 10),
        )
    elif algorithm == "dbscan":
        model = DBSCAN(
            eps=hyperparameters.get("eps", 0.5),
            min_samples=hyperparameters.get("min_samples", 5),
        )
    elif algorithm == "pca":
        model = PCA(
            n_components=hyperparameters.get("n_components", 2),
            random_state=hyperparameters.get("random_state", 42),
        )
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")

    # モデル学習/適用
    logger.info(f"Training {algorithm} model...")

    if algorithm == "pca":
        # PCAは変換
        _transformed = model.fit_transform(X_train)  # noqa: F841
        labels = None
        n_clusters = hyperparameters.get("n_components", 2)
        logger.info(f"PCA transformed data to {n_clusters} components")
    else:
        # クラスタリングはラベル予測
        labels = model.fit_predict(X_train)
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)  # -1はノイズ点（DBSCANの場合）
        logger.info(f"Found {n_clusters} clusters")

    # モデルの保存
    if model_output_s3_uri:
        # モデルをシリアライズ
        model_buffer = io.BytesIO()
        joblib.dump(model, model_buffer)
        model_buffer.seek(0)

        # S3に保存
        output_parts = model_output_s3_uri[5:].split("/", 1)
        output_bucket, output_key = output_parts

        s3_client.put_object(
            Bucket=output_bucket,
            Key=output_key
            if output_key.endswith(".pkl")
            else f"{output_key}/model.pkl",
            Body=model_buffer.getvalue(),
        )

        # メタデータも保存
        metadata = {
            "algorithm": algorithm,
            "hyperparameters": hyperparameters,
            "n_samples": len(X_train),
            "n_features": len(X_train.columns),
            "feature_names": X_train.columns.tolist(),
            "n_clusters": int(n_clusters),
        }

        if labels is not None:
            # クラスタごとのサンプル数
            unique, counts = (
                pd.Series(labels).value_counts().sort_index().index,
                pd.Series(labels).value_counts().sort_index().values,
            )
            metadata["cluster_distribution"] = {
                int(cluster): int(count) for cluster, count in zip(unique, counts)
            }

        metadata_key = (
            output_key.replace(".pkl", "_metadata.json")
            if output_key.endswith(".pkl")
            else f"{output_key}/metadata.json"
        )
        s3_client.put_object(
            Bucket=output_bucket,
            Key=metadata_key,
            Body=json.dumps(metadata, indent=2),
        )

        logger.info(f"Saved model to {model_output_s3_uri}")

    result = {
        "status": "success",
        "message": f"Clustering model trained successfully with {algorithm}",
        "training_results": {
            "algorithm": algorithm,
            "n_samples": len(X_train),
            "n_features": len(X_train.columns),
            "feature_names": X_train.columns.tolist(),
            "n_clusters": int(n_clusters),
            "hyperparameters": hyperparameters,
            "model_s3_uri": model_output_s3_uri,
        },
    }

    if labels is not None:
        unique, counts = (
            pd.Series(labels).value_counts().sort_index().index,
            pd.Series(labels).value_counts().sort_index().values,
        )
        result["training_results"]["cluster_distribution"] = {
            int(cluster): int(count) for cluster, count in zip(unique, counts)
        }

    return result
