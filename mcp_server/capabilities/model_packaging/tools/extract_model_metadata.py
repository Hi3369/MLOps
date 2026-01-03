"""
Extract Model Metadata Tool

モデルメタデータ抽出ツール
"""

import io
import logging
from typing import Any, Dict

import boto3
import joblib
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def extract_model_metadata(
    model_s3_uri: str,
) -> Dict[str, Any]:
    """
    モデルからメタデータを抽出

    Args:
        model_s3_uri: モデルのS3 URI (.pkl)

    Returns:
        メタデータ辞書
    """
    logger.info(f"Extracting metadata from model: {model_s3_uri}")

    # S3 URIのバリデーション
    if not model_s3_uri.startswith("s3://"):
        raise ValueError("Invalid S3 URI: must start with 's3://'")

    model_parts = model_s3_uri[5:].split("/", 1)
    if len(model_parts) != 2:
        raise ValueError("Invalid S3 URI format: s3://bucket/key required")

    # S3クライアント
    s3_client = boto3.client("s3")

    model_bucket, model_key = model_parts

    # モデルファイルをダウンロードしてロード
    try:
        response = s3_client.get_object(Bucket=model_bucket, Key=model_key)
        model_content = response["Body"].read()
        model = joblib.load(io.BytesIO(model_content))
        logger.info("Model loaded successfully")

    except ClientError as e:
        logger.error(f"S3 access error: {e}")
        raise ValueError(f"Model not found at S3 URI: {model_s3_uri}")

    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise ValueError(f"Failed to load model: {e}")

    # モデルからメタデータを抽出
    metadata = _extract_metadata_from_model(model)

    # S3メタデータも取得
    try:
        head_response = s3_client.head_object(Bucket=model_bucket, Key=model_key)
        s3_metadata = {
            "size_bytes": head_response.get("ContentLength", 0),
            "last_modified": head_response.get("LastModified", "").isoformat()
            if head_response.get("LastModified")
            else None,
            "content_type": head_response.get("ContentType", ""),
        }
    except Exception as e:
        logger.warning(f"Failed to get S3 metadata: {e}")
        s3_metadata = {}

    logger.info("Metadata extraction completed")

    return {
        "status": "success",
        "message": "Model metadata extracted successfully",
        "metadata": {
            "model_s3_uri": model_s3_uri,
            "model_info": metadata,
            "s3_metadata": s3_metadata,
        },
    }


def _extract_metadata_from_model(model: Any) -> Dict[str, Any]:
    """モデルオブジェクトからメタデータを抽出"""
    metadata = {
        "model_type": type(model).__name__,
        "module": type(model).__module__,
    }

    # sklearn モデルの場合
    if hasattr(model, "get_params"):
        try:
            metadata["parameters"] = model.get_params()
        except Exception:
            pass

    # 特徴量数の取得
    if hasattr(model, "n_features_in_"):
        metadata["n_features_in"] = int(model.n_features_in_)

    if hasattr(model, "feature_names_in_"):
        metadata["feature_names_in"] = model.feature_names_in_.tolist()

    # クラス数の取得（分類モデルの場合）
    if hasattr(model, "n_classes_"):
        metadata["n_classes"] = int(model.n_classes_)

    if hasattr(model, "classes_"):
        metadata["classes"] = model.classes_.tolist()

    # ツリーベースモデルの情報
    if hasattr(model, "n_estimators"):
        metadata["n_estimators"] = int(model.n_estimators)

    if hasattr(model, "n_trees_"):
        metadata["n_trees"] = int(model.n_trees_)

    # 特徴量重要度
    if hasattr(model, "feature_importances_"):
        metadata["feature_importances"] = model.feature_importances_.tolist()

    # モデルサイズの推定
    try:
        import sys

        metadata["estimated_memory_bytes"] = sys.getsizeof(model)
    except Exception:
        pass

    return metadata
