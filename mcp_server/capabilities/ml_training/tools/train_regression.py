"""
Train Regression Model Tool

回帰モデル学習ツール
"""

import io
import json
import logging
from typing import Any, Dict

import boto3
import joblib
import pandas as pd
from botocore.exceptions import ClientError
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.neural_network import MLPRegressor

logger = logging.getLogger(__name__)


def train_regression(
    train_data_s3_uri: str,
    algorithm: str = "random_forest",
    hyperparameters: Dict[str, Any] = None,
    model_output_s3_uri: str = None,
    file_format: str = "csv",
    validation_data_s3_uri: str = None,
) -> Dict[str, Any]:
    """
    回帰モデルを学習

    Args:
        train_data_s3_uri: 学習データのS3 URI (前処理済みデータ)
        algorithm: アルゴリズム (random_forest, linear_regression, ridge, neural_network)
        hyperparameters: ハイパーパラメータ辞書
        model_output_s3_uri: モデル保存先S3 URI
        file_format: ファイルフォーマット (csv, parquet)
        validation_data_s3_uri: 検証データのS3 URI（オーバーフィッティング検出用）

    Returns:
        学習結果辞書
    """
    logger.info(f"Training regression model with algorithm: {algorithm}")

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

        logger.info(f"Loaded training data: {len(df)} samples, {len(df.columns)} features")

    except ClientError as e:
        logger.error(f"S3 access error: {e}")
        raise ValueError(f"Failed to load data from S3: {e}")

    # 特徴量とターゲットの分離 (最後の列がターゲットと仮定)
    X_train = df.iloc[:, :-1]
    y_train = df.iloc[:, -1]

    # ハイパーパラメータのデフォルト設定
    if hyperparameters is None:
        hyperparameters = {}

    # アルゴリズムに応じたモデルの作成
    if algorithm == "random_forest":
        model = RandomForestRegressor(
            n_estimators=hyperparameters.get("n_estimators", 100),
            max_depth=hyperparameters.get("max_depth", None),
            min_samples_split=hyperparameters.get("min_samples_split", 2),
            min_samples_leaf=hyperparameters.get("min_samples_leaf", 1),
            random_state=hyperparameters.get("random_state", 42),
        )
    elif algorithm == "linear_regression":
        model = LinearRegression()
    elif algorithm == "ridge":
        model = Ridge(
            alpha=hyperparameters.get("alpha", 1.0),
            random_state=hyperparameters.get("random_state", 42),
        )
    elif algorithm == "neural_network":
        model = MLPRegressor(
            hidden_layer_sizes=hyperparameters.get("hidden_layer_sizes", (100,)),
            activation=hyperparameters.get("activation", "relu"),
            max_iter=hyperparameters.get("max_iter", 200),
            random_state=hyperparameters.get("random_state", 42),
        )
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")

    # モデル学習
    logger.info(f"Training {algorithm} model...")
    model.fit(X_train, y_train)

    # 学習データでの評価 (R^2スコア)
    train_score = model.score(X_train, y_train)
    logger.info(f"Training R^2 score: {train_score:.4f}")

    # 検証データでの評価（オーバーフィッティング検出）
    validation_score = None
    overfitting_warning = None
    if validation_data_s3_uri:
        try:
            if not validation_data_s3_uri.startswith("s3://"):
                raise ValueError("Invalid validation S3 URI: must start with 's3://'")

            val_parts = validation_data_s3_uri[5:].split("/", 1)
            if len(val_parts) != 2:
                raise ValueError("Invalid validation S3 URI format")

            val_bucket, val_key = val_parts
            val_response = s3_client.get_object(Bucket=val_bucket, Key=val_key)
            val_content = val_response["Body"].read()

            if file_format.lower() == "csv":
                val_df = pd.read_csv(io.BytesIO(val_content))
            elif file_format.lower() == "parquet":
                val_df = pd.read_parquet(io.BytesIO(val_content))
            else:
                raise ValueError(f"Unsupported file format: {file_format}")

            X_val = val_df.iloc[:, :-1]
            y_val = val_df.iloc[:, -1]
            validation_score = model.score(X_val, y_val)
            logger.info(f"Validation R^2 score: {validation_score:.4f}")

            # オーバーフィッティング検出
            score_diff = train_score - validation_score
            if score_diff > 0.1:
                overfitting_warning = (
                    f"Potential overfitting detected: train_r2={train_score:.4f}, "
                    f"validation_r2={validation_score:.4f}, diff={score_diff:.4f}"
                )
                logger.warning(overfitting_warning)

        except ClientError as e:
            logger.warning(f"Failed to load validation data: {e}")

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
            Key=output_key if output_key.endswith(".pkl") else f"{output_key}/model.pkl",
            Body=model_buffer.getvalue(),
        )

        # メタデータも保存
        metadata = {
            "algorithm": algorithm,
            "hyperparameters": hyperparameters,
            "train_r2_score": float(train_score),
            "n_samples": len(X_train),
            "n_features": len(X_train.columns),
            "feature_names": X_train.columns.tolist(),
        }
        if validation_score is not None:
            metadata["validation_r2_score"] = float(validation_score)
        if overfitting_warning:
            metadata["overfitting_warning"] = overfitting_warning

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
        "message": f"Regression model trained successfully with {algorithm}",
        "training_results": {
            "algorithm": algorithm,
            "train_r2_score": float(train_score),
            "n_samples": len(X_train),
            "n_features": len(X_train.columns),
            "feature_names": X_train.columns.tolist(),
            "hyperparameters": hyperparameters,
            "model_s3_uri": model_output_s3_uri,
        },
    }

    if validation_score is not None:
        result["training_results"]["validation_r2_score"] = float(validation_score)
    if overfitting_warning:
        result["training_results"]["overfitting_warning"] = overfitting_warning

    return result
