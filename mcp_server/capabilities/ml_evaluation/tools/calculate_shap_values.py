"""
Calculate SHAP Values Tool

SHAP値計算ツール - モデル解釈性のためのSHAP分析
"""

import io
import logging
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def calculate_shap_values(
    model_s3_uri: str,
    data_s3_uri: str,
    explainer_type: str = "auto",
    background_samples: int = 100,
    max_samples: Optional[int] = None,
    file_format: str = "csv",
) -> Dict[str, Any]:
    """
    SHAP値を計算してモデルの予測を説明

    Args:
        model_s3_uri: モデルのS3 URI (.pkl)
        data_s3_uri: 説明対象データのS3 URI
        explainer_type: Explainerタイプ (auto, tree, kernel, deep)
        background_samples: 背景データのサンプル数（KernelExplainer用）
        max_samples: 分析するサンプルの最大数
        file_format: ファイルフォーマット (csv, parquet)

    Returns:
        SHAP値計算結果を含む辞書

    Raises:
        ValueError: 無効なパラメータの場合
    """
    logger.info(f"Calculating SHAP values with {explainer_type} explainer")

    # バリデーション
    if not model_s3_uri.startswith("s3://"):
        raise ValueError("Invalid S3 URI: model_s3_uri must start with 's3://'")
    if not data_s3_uri.startswith("s3://"):
        raise ValueError("Invalid S3 URI: data_s3_uri must start with 's3://'")
    if explainer_type not in ["auto", "tree", "kernel", "deep"]:
        raise ValueError(f"Unsupported explainer type: {explainer_type}")
    if file_format not in ["csv", "parquet"]:
        raise ValueError(f"Unsupported file format: {file_format}")
    if background_samples <= 0:
        raise ValueError("background_samples must be positive")

    # モデルとデータの読み込み
    model = _load_model_from_s3(model_s3_uri)
    data = _load_data_from_s3(data_s3_uri, file_format)

    if data.empty:
        raise ValueError("Empty dataset provided")

    # ターゲット列を除外（最後の列がターゲットと仮定）
    if "target" in data.columns:
        X = data.drop(columns=["target"])
    else:
        X = data.iloc[:, :-1]

    # サンプル数制限
    samples_analyzed = len(X)
    if max_samples is not None and len(X) > max_samples:
        X = X.iloc[:max_samples]
        samples_analyzed = max_samples

    # モデルタイプの判定
    model_type = _detect_model_type(model)

    # Explainerの選択と実行
    explainer_type_used = explainer_type
    if explainer_type == "auto":
        explainer_type_used = _auto_select_explainer(model)

    shap_values, base_value = _compute_shap_values(
        model=model,
        X=X,
        explainer_type=explainer_type_used,
        background_samples=min(background_samples, len(X)),
    )

    # 特徴量重要度の計算
    feature_importance = _calculate_feature_importance(shap_values, X.columns.tolist())

    logger.info("SHAP values calculated successfully")

    return {
        "status": "success",
        "message": "SHAP values calculated successfully",
        "model_type": model_type,
        "explainer_type_used": explainer_type_used,
        "samples_analyzed": samples_analyzed,
        "background_samples_used": min(background_samples, len(X)),
        "n_features": len(X.columns),
        "feature_names": X.columns.tolist(),
        "shap_values": _serialize_shap_values(shap_values),
        "base_value": float(base_value) if np.isscalar(base_value) else base_value.tolist(),  # type: ignore[arg-type]
        "feature_importance": feature_importance,
        "summary": {
            "mean_abs_shap": _calculate_mean_abs_shap(shap_values, X.columns.tolist()),
        },
    }


def _load_model_from_s3(s3_uri: str) -> Any:
    """S3からモデルを読み込む"""
    import boto3
    import joblib

    bucket, key = _parse_s3_uri(s3_uri)
    s3_client = boto3.client("s3")

    response = s3_client.get_object(Bucket=bucket, Key=key)
    model_bytes = response["Body"].read()
    model = joblib.load(io.BytesIO(model_bytes))

    return model


def _load_data_from_s3(s3_uri: str, file_format: str) -> pd.DataFrame:
    """S3からデータを読み込む"""
    import boto3

    bucket, key = _parse_s3_uri(s3_uri)
    s3_client = boto3.client("s3")

    response = s3_client.get_object(Bucket=bucket, Key=key)
    data_bytes = response["Body"].read()

    if file_format == "csv":
        return pd.read_csv(io.BytesIO(data_bytes))
    elif file_format == "parquet":
        return pd.read_parquet(io.BytesIO(data_bytes))
    else:
        raise ValueError(f"Unsupported file format: {file_format}")


def _parse_s3_uri(s3_uri: str) -> tuple:
    """S3 URIをバケットとキーに分解"""
    path = s3_uri.replace("s3://", "")
    parts = path.split("/", 1)
    bucket = parts[0]
    key = parts[1] if len(parts) > 1 else ""
    return bucket, key


def _detect_model_type(model: Any) -> str:
    """モデルが分類器か回帰器か判定"""
    if hasattr(model, "predict_proba"):
        return "classifier"
    elif hasattr(model, "predict"):
        return "regressor"
    else:
        return "unknown"


def _auto_select_explainer(model: Any) -> str:
    """モデルに適したExplainerを自動選択"""
    model_class_name = type(model).__name__.lower()

    # Tree-based models
    tree_models = [
        "randomforest",
        "gradientboosting",
        "xgb",
        "lgbm",
        "catboost",
        "decisiontree",
        "extratrees",
    ]

    for tree_model in tree_models:
        if tree_model in model_class_name:
            return "tree"

    # Neural networks would use deep explainer
    nn_models = ["mlp", "neural", "keras", "torch"]
    for nn_model in nn_models:
        if nn_model in model_class_name:
            return "kernel"  # Use kernel as fallback since deep requires specific setup

    # Default to kernel for other models
    return "kernel"


def _compute_shap_values(
    model: Any,
    X: pd.DataFrame,
    explainer_type: str,
    background_samples: int,
) -> tuple:
    """SHAP値を計算"""
    import shap

    X_array = X.values

    if explainer_type == "tree":
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_array)
        base_value = explainer.expected_value

        # 分類器の場合、正クラスのSHAP値を使用
        if isinstance(shap_values, list):
            shap_values = shap_values[1]  # 正クラス
            if isinstance(base_value, (list, np.ndarray)):
                base_value = base_value[1]

    elif explainer_type == "kernel":
        # 背景データのサンプリング
        if len(X_array) > background_samples:
            background = shap.sample(X_array, background_samples)
        else:
            background = X_array

        # 予測関数の設定
        def _predict_proba_positive(x):
            return model.predict_proba(x)[:, 1]

        if hasattr(model, "predict_proba"):
            predict_fn = _predict_proba_positive
        else:
            predict_fn = model.predict

        explainer = shap.KernelExplainer(predict_fn, background)
        shap_values = explainer.shap_values(X_array[: min(100, len(X_array))])
        base_value = explainer.expected_value

    elif explainer_type == "deep":
        # DeepExplainerはKeras/PyTorchモデル用
        # フォールバックとしてKernelExplainerを使用
        return _compute_shap_values(model, X, "kernel", background_samples)

    else:
        raise ValueError(f"Unsupported explainer type: {explainer_type}")

    return shap_values, base_value


def _calculate_feature_importance(shap_values: np.ndarray, feature_names: list) -> Dict[str, float]:
    """SHAP値から特徴量重要度を計算"""
    # SHAP値が3次元の場合（マルチクラス）、2次元に変換
    if len(shap_values.shape) == 3:
        # 全クラスの絶対値の平均を取る
        shap_values = np.mean(np.abs(shap_values), axis=2)

    mean_abs_shap = np.mean(np.abs(shap_values), axis=0)

    importance = {}
    for i, name in enumerate(feature_names):
        val = mean_abs_shap[i]
        # 配列の場合は平均値を取る
        if isinstance(val, np.ndarray):
            val = float(np.mean(val))
        else:
            val = float(val)
        importance[name] = val

    # 重要度順にソート
    importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))

    return importance


def _calculate_mean_abs_shap(shap_values: np.ndarray, feature_names: list) -> Dict[str, float]:
    """各特徴量の平均絶対SHAP値を計算"""
    # SHAP値が3次元の場合（マルチクラス）、2次元に変換
    if len(shap_values.shape) == 3:
        shap_values = np.mean(np.abs(shap_values), axis=2)

    result = {}
    for i, col in enumerate(feature_names):
        val = np.mean(np.abs(shap_values[:, i]))
        if isinstance(val, np.ndarray):
            val = float(np.mean(val))
        else:
            val = float(val)
        result[col] = val
    return result


def _serialize_shap_values(shap_values: np.ndarray) -> Dict[str, Any]:
    """SHAP値をシリアライズ可能な形式に変換"""
    return {
        "shape": list(shap_values.shape),
        "mean": float(np.mean(shap_values)),
        "std": float(np.std(shap_values)),
        "min": float(np.min(shap_values)),
        "max": float(np.max(shap_values)),
        # 完全な値は大きすぎるので統計情報のみ返す
        # 必要に応じてS3に保存する実装を追加可能
    }
