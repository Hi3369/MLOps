"""
Preprocess Supervised Learning Data Tool

教師あり学習用のデータ前処理ツール
"""

import io
import json
import logging
from datetime import datetime
from typing import Any, Dict, Literal, Optional

import boto3
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler

logger = logging.getLogger(__name__)


def preprocess_supervised(
    s3_uri: str,
    target_column: str,
    task_type: Literal["classification", "regression"] = "classification",
    file_format: str = "csv",
    test_size: float = 0.2,
    normalize: bool = True,
    handle_missing: str = "drop",
    encode_categorical: bool = True,
    output_s3_uri: Optional[str] = None,
    output_format: Literal["csv", "parquet"] = "csv",
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    教師あり学習用のデータ前処理を実行

    Args:
        s3_uri: S3 URI (例: s3://bucket-name/path/to/file.csv)
        target_column: ターゲット列名
        task_type: タスクタイプ (classification または regression)
        file_format: ファイルフォーマット (csv, parquet, json)
        test_size: テストデータの割合 (0.0-1.0)
        normalize: 数値変数を正規化するか
        handle_missing: 欠損値の処理方法 (drop, mean, median, mode)
        encode_categorical: カテゴリ変数をエンコードするか
        output_s3_uri: 出力先S3 URI (Noneの場合は自動生成)
        output_format: 出力ファイルフォーマット (csv または parquet)
        random_state: 乱数シード（再現性確保用）

    Returns:
        前処理結果

    Note:
        実装済みの前処理:
        - 欠損値処理
        - カテゴリ変数エンコーディング
        - 数値変数の正規化/標準化
        - 特徴量とターゲットの分割
        - Train/Test split
        - 日時ベースのパーティショニング
        - メタデータ保存
    """
    logger.info(
        f"Preprocessing data for supervised learning "
        f"(target: {target_column}, task_type: {task_type})"
    )

    # S3から実際のデータを再読み込み（pandasで処理するため）
    parts = s3_uri[5:].split("/", 1)
    bucket, key = parts

    s3_client = boto3.client("s3")
    response = s3_client.get_object(Bucket=bucket, Key=key)
    file_content = response["Body"].read()

    if file_format.lower() == "csv":
        df = pd.read_csv(io.BytesIO(file_content))
    elif file_format.lower() == "parquet":
        df = pd.read_parquet(io.BytesIO(file_content))
    elif file_format.lower() == "json":
        df = pd.read_json(io.BytesIO(file_content))
    else:
        raise ValueError(f"Unsupported file format: {file_format}")

    # ターゲット列の存在確認
    if target_column not in df.columns:
        raise ValueError(
            f"Target column '{target_column}' not found in dataset. "
            f"Available columns: {df.columns.tolist()}"
        )

    logger.info(f"Original dataset shape: {df.shape}")

    # 1. 欠損値処理
    initial_rows = len(df)
    if handle_missing == "drop":
        df = df.dropna()
        logger.info(f"Dropped {initial_rows - len(df)} rows with missing values")
    elif handle_missing == "mean":
        numeric_cols = df.select_dtypes(include=["number"]).columns
        df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
    elif handle_missing == "median":
        numeric_cols = df.select_dtypes(include=["number"]).columns
        df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
    elif handle_missing == "mode":
        for col in df.columns:
            df[col] = df[col].fillna(df[col].mode()[0] if not df[col].mode().empty else None)

    # 2. 特徴量とターゲットの分割
    X = df.drop(columns=[target_column])
    y = df[target_column]

    # 3. カテゴリ変数のエンコーディング
    categorical_cols = []
    label_encoders = {}

    if encode_categorical:
        categorical_cols = X.select_dtypes(include=["object"]).columns.tolist()
        for col in categorical_cols:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
            label_encoders[col] = {
                "classes": le.classes_.tolist(),
            }
        logger.info(f"Encoded {len(categorical_cols)} categorical columns")

    # ターゲットがカテゴリの場合もエンコード（分類タスクの場合のみ）
    target_encoder = None
    target_scaler = None
    if task_type == "classification" and y.dtype == "object":
        target_encoder = LabelEncoder()
        y = target_encoder.fit_transform(y)
        logger.info(f"Encoded target column with {len(target_encoder.classes_)} classes")
    elif task_type == "regression" and normalize:
        # 回帰タスクの場合、ターゲットも正規化オプション
        target_scaler = StandardScaler()
        y = target_scaler.fit_transform(y.values.reshape(-1, 1)).flatten()
        logger.info("Applied StandardScaler to regression target")

    # 4. Train/Test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    logger.info(f"Split dataset: train={len(X_train)}, test={len(X_test)}")

    # 5. 数値変数の正規化/標準化
    scaler = None
    if normalize:
        scaler = StandardScaler()
        X_train = pd.DataFrame(
            scaler.fit_transform(X_train),
            columns=X_train.columns,
            index=X_train.index,
        )
        X_test = pd.DataFrame(
            scaler.transform(X_test),
            columns=X_test.columns,
            index=X_test.index,
        )
        logger.info("Applied StandardScaler normalization")

    # 6. S3に保存（日時ベースパーティショニング）
    now = datetime.utcnow()
    date_partition = now.strftime("%Y/%m/%d")
    job_id = now.strftime("%Y%m%d_%H%M%S")

    if output_s3_uri is None:
        # 自動生成: 日時パーティション付き
        output_s3_uri = f"s3://{bucket}/processed/{date_partition}/{job_id}/"

    output_parts = output_s3_uri[5:].rstrip("/").split("/", 1)
    output_bucket = output_parts[0]
    output_prefix = output_parts[1] if len(output_parts) > 1 else ""

    # ファイル拡張子を決定
    file_ext = "parquet" if output_format == "parquet" else "csv"

    # 各データセットを保存
    for name, data_x, data_y in [
        ("train", X_train, y_train),
        ("test", X_test, y_test),
    ]:
        # 特徴量とターゲットを結合
        combined = data_x.copy()
        combined[target_column] = data_y

        output_key = f"{output_prefix}/{name}.{file_ext}"

        if output_format == "parquet":
            # Parquet形式で保存
            parquet_buffer = io.BytesIO()
            combined.to_parquet(parquet_buffer, index=False)
            s3_client.put_object(
                Bucket=output_bucket,
                Key=output_key,
                Body=parquet_buffer.getvalue(),
            )
        else:
            # CSV形式で保存
            csv_buffer = io.StringIO()
            combined.to_csv(csv_buffer, index=False)
            s3_client.put_object(
                Bucket=output_bucket,
                Key=output_key,
                Body=csv_buffer.getvalue(),
            )

        logger.info(f"Saved {name} dataset to s3://{output_bucket}/{output_key}")

    # 7. メタデータを保存
    metadata = {
        "job_id": job_id,
        "created_at": now.isoformat(),
        "source_s3_uri": s3_uri,
        "task_type": task_type,
        "target_column": target_column,
        "feature_names": X_train.columns.tolist(),
        "categorical_columns": categorical_cols,
        "label_encoders": label_encoders,
        "target_encoder_classes": target_encoder.classes_.tolist() if target_encoder else None,
        "target_scaler_params": (
            {
                "mean": float(target_scaler.mean_[0]),
                "scale": float(target_scaler.scale_[0]),
            }
            if target_scaler
            else None
        ),
        "scaler_params": (
            {
                "mean": scaler.mean_.tolist(),
                "scale": scaler.scale_.tolist(),
            }
            if scaler
            else None
        ),
        "preprocessing_config": {
            "normalize": normalize,
            "handle_missing": handle_missing,
            "encode_categorical": encode_categorical,
            "test_size": test_size,
            "random_state": random_state,
            "output_format": output_format,
        },
        "dataset_stats": {
            "original_rows": initial_rows,
            "processed_rows": len(df),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "num_features": len(X_train.columns),
        },
    }

    metadata_key = f"{output_prefix}/metadata.json"
    s3_client.put_object(
        Bucket=output_bucket,
        Key=metadata_key,
        Body=json.dumps(metadata, indent=2, ensure_ascii=False),
        ContentType="application/json",
    )
    logger.info(f"Saved metadata to s3://{output_bucket}/{metadata_key}")

    return {
        "status": "success",
        "message": "Data preprocessed for supervised learning",
        "preprocessing_results": {
            "job_id": job_id,
            "task_type": task_type,
            "target_column": target_column,
            "num_features": len(X_train.columns),
            "feature_names": X_train.columns.tolist(),
            "num_samples": len(df),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "categorical_columns": categorical_cols,
            "normalized": normalize,
            "random_state": random_state,
            "output_format": output_format,
            "target_classes": target_encoder.classes_.tolist() if target_encoder else None,
            "output_s3_uri": output_s3_uri,
            "metadata_uri": f"s3://{output_bucket}/{metadata_key}",
        },
    }
