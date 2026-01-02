"""
Evaluate Regression Model Tool

回帰モデル評価ツール
"""

import io
import logging
from typing import Any, Dict

import boto3
import joblib
import pandas as pd
from botocore.exceptions import ClientError
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

logger = logging.getLogger(__name__)


def evaluate_regression(
    model_s3_uri: str,
    test_data_s3_uri: str,
    file_format: str = "csv",
) -> Dict[str, Any]:
    """
    回帰モデルを評価

    Args:
        model_s3_uri: モデルのS3 URI (.pkl)
        test_data_s3_uri: テストデータのS3 URI (前処理済みデータ)
        file_format: ファイルフォーマット (csv, parquet)

    Returns:
        評価結果辞書
    """
    logger.info(f"Evaluating regression model from {model_s3_uri}")

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

    # 特徴量とターゲットの分離 (最後の列がターゲットと仮定)
    X_test = df.iloc[:, :-1]
    y_test = df.iloc[:, -1]

    # 予測
    logger.info("Making predictions...")
    y_pred = model.predict(X_test)

    # 評価メトリクスの計算
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = mse**0.5

    logger.info(f"Evaluation completed: R²={r2:.4f}, RMSE={rmse:.4f}")

    return {
        "status": "success",
        "message": "Regression model evaluated successfully",
        "evaluation_results": {
            "r2_score": float(r2),
            "mae": float(mae),
            "mse": float(mse),
            "rmse": float(rmse),
            "n_samples": len(X_test),
            "n_features": len(X_test.columns),
            "feature_names": X_test.columns.tolist(),
            "model_s3_uri": model_s3_uri,
            "test_data_s3_uri": test_data_s3_uri,
        },
    }
