"""
Evaluate Clustering Model Tool

クラスタリングモデル評価ツール
"""

import io
import logging
from typing import Any, Dict

import boto3
import joblib
import pandas as pd
from botocore.exceptions import ClientError
from sklearn.metrics import davies_bouldin_score, silhouette_score

logger = logging.getLogger(__name__)


def evaluate_clustering(
    model_s3_uri: str,
    test_data_s3_uri: str,
    file_format: str = "csv",
) -> Dict[str, Any]:
    """
    クラスタリングモデルを評価

    Args:
        model_s3_uri: モデルのS3 URI (.pkl)
        test_data_s3_uri: テストデータのS3 URI
        file_format: ファイルフォーマット (csv, parquet)

    Returns:
        評価結果辞書
    """
    logger.info(f"Evaluating clustering model from {model_s3_uri}")

    # S3 URIのバリデーション（先に全てチェック）
    if not model_s3_uri.startswith("s3://"):
        raise ValueError("Invalid S3 URI: must start with 's3://'")

    model_parts = model_s3_uri[5:].split("/", 1)
    if len(model_parts) != 2:
        raise ValueError("Invalid S3 URI format: s3://bucket/key required")

    if not test_data_s3_uri.startswith("s3://"):
        raise ValueError("Invalid S3 URI: must start with 's3://'")

    data_parts = test_data_s3_uri[5:].split("/", 1)
    if len(data_parts) != 2:
        raise ValueError("Invalid S3 URI format: s3://bucket/key required")

    # S3クライアント
    s3_client = boto3.client("s3")

    # モデルのロード
    model_bucket, model_key = model_parts

    try:
        model_response = s3_client.get_object(Bucket=model_bucket, Key=model_key)
        model_content = model_response["Body"].read()
        model = joblib.load(io.BytesIO(model_content))
        logger.info(f"Loaded model from {model_s3_uri}")

    except ClientError as e:
        logger.error(f"S3 access error for model: {e}")
        raise ValueError(f"Failed to load model from S3: {e}")

    # テストデータのロード
    data_bucket, data_key = data_parts

    try:
        data_response = s3_client.get_object(Bucket=data_bucket, Key=data_key)
        data_content = data_response["Body"].read()

        # データ読み込み
        if file_format.lower() == "csv":
            df = pd.read_csv(io.BytesIO(data_content))
        elif file_format.lower() == "parquet":
            df = pd.read_parquet(io.BytesIO(data_content))
        else:
            raise ValueError(f"Unsupported file format: {file_format}")

        logger.info(f"Loaded test data: {len(df)} samples, {len(df.columns)} features")

    except ClientError as e:
        logger.error(f"S3 access error for data: {e}")
        raise ValueError(f"Failed to load data from S3: {e}")

    # 全データを特徴量として使用
    X_test = df

    # 予測（クラスタラベル）
    logger.info("Predicting cluster labels...")

    # モデルタイプに応じた予測
    if hasattr(model, "predict"):
        labels = model.predict(X_test)
    elif hasattr(model, "fit_predict"):
        # DBSCANの場合
        labels = model.fit_predict(X_test)
    else:
        raise ValueError("Model does not support prediction")

    # クラスタ数の計算（-1はノイズ点）
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)

    # 評価メトリクスの計算
    # シルエットスコア（-1が含まれる場合は計算できない）
    if -1 not in labels and n_clusters > 1:
        silhouette = silhouette_score(X_test, labels)
        davies_bouldin = davies_bouldin_score(X_test, labels)
    else:
        silhouette = None
        davies_bouldin = None
        logger.warning(
            "Silhouette score cannot be computed (noise points present or single cluster)"
        )

    # クラスタ分布
    unique, counts = (
        pd.Series(labels).value_counts().sort_index().index,
        pd.Series(labels).value_counts().sort_index().values,
    )
    cluster_distribution = {int(cluster): int(count) for cluster, count in zip(unique, counts)}

    logger.info(f"Evaluation completed: {n_clusters} clusters, Silhouette={silhouette}")

    evaluation_results = {
        "n_clusters": int(n_clusters),
        "n_samples": len(X_test),
        "n_features": len(X_test.columns),
        "feature_names": X_test.columns.tolist(),
        "cluster_distribution": cluster_distribution,
        "model_s3_uri": model_s3_uri,
        "test_data_s3_uri": test_data_s3_uri,
    }

    # メトリクスを追加（計算可能な場合のみ）
    if silhouette is not None:
        evaluation_results["silhouette_score"] = float(silhouette)
    if davies_bouldin is not None:
        evaluation_results["davies_bouldin_score"] = float(davies_bouldin)

    return {
        "status": "success",
        "message": "Clustering model evaluated successfully",
        "evaluation_results": evaluation_results,
    }
