"""
Calculate LIME Explanation Tool

LIME説明計算ツール - 局所的解釈可能性のための分析
"""

import io
import logging
from typing import Any, Dict, List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def calculate_lime_explanation(
    model_s3_uri: str,
    data_s3_uri: str,
    instance_index: int = 0,
    num_features: int = 10,
    num_samples: int = 5000,
    file_format: str = "csv",
) -> Dict[str, Any]:
    """
    LIMEによる局所的説明を計算

    Args:
        model_s3_uri: モデルのS3 URI (.pkl)
        data_s3_uri: 説明対象データのS3 URI
        instance_index: 説明対象インスタンスのインデックス
        num_features: 表示する特徴量数
        num_samples: サンプリング数
        file_format: ファイルフォーマット (csv, parquet)

    Returns:
        LIME説明結果を含む辞書

    Raises:
        ValueError: 無効なパラメータの場合
    """
    logger.info(f"Calculating LIME explanation for instance {instance_index}")

    # バリデーション
    if not model_s3_uri.startswith("s3://"):
        raise ValueError("Invalid S3 URI: model_s3_uri must start with 's3://'")
    if not data_s3_uri.startswith("s3://"):
        raise ValueError("Invalid S3 URI: data_s3_uri must start with 's3://'")
    if file_format not in ["csv", "parquet"]:
        raise ValueError(f"Unsupported file format: {file_format}")
    if instance_index < 0:
        raise ValueError("Instance index must be non-negative")
    if num_features <= 0:
        raise ValueError("num_features must be positive")
    if num_samples <= 0:
        raise ValueError("num_samples must be positive")

    # モデルとデータの読み込み
    model = _load_model_from_s3(model_s3_uri)
    data = _load_data_from_s3(data_s3_uri, file_format)

    if data.empty:
        raise ValueError("Empty dataset provided")

    # ターゲット列を除外
    if "target" in data.columns:
        X = data.drop(columns=["target"])
    else:
        X = data.iloc[:, :-1]

    # インデックスチェック
    if instance_index >= len(X):
        raise ValueError(f"Instance index out of range: {instance_index} >= {len(X)}")

    # モデルタイプの判定
    model_type = _detect_model_type(model)

    # LIME説明の計算
    explanation_result = _compute_lime_explanation(
        model=model,
        X=X,
        instance_index=instance_index,
        num_features=num_features,
        num_samples=num_samples,
        model_type=model_type,
    )

    logger.info("LIME explanation calculated successfully")

    result = {
        "status": "success",
        "message": "LIME explanation calculated successfully",
        "model_type": model_type,
        "instance_index": instance_index,
        "num_features_requested": num_features,
        "num_samples_used": num_samples,
        "n_features_total": len(X.columns),
        "feature_names": X.columns.tolist(),
        "explanation": explanation_result["explanation"],
        "feature_weights": explanation_result["feature_weights"],
        "top_features": explanation_result["top_features"],
        "local_fidelity_score": explanation_result["local_fidelity_score"],
        "instance_values": X.iloc[instance_index].to_dict(),
    }

    # モデルタイプに応じた追加情報
    if model_type == "classifier":
        result["predicted_class"] = explanation_result["predicted_class"]
        result["prediction_probabilities"] = explanation_result["prediction_probabilities"]
    else:
        result["predicted_value"] = explanation_result["predicted_value"]

    return result


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


def _compute_lime_explanation(
    model: Any,
    X: pd.DataFrame,
    instance_index: int,
    num_features: int,
    num_samples: int,
    model_type: str,
) -> Dict[str, Any]:
    """LIME説明を計算"""
    from lime.lime_tabular import LimeTabularExplainer

    X_array = X.values
    feature_names = X.columns.tolist()
    instance = X_array[instance_index]

    # モデルタイプに応じた設定
    if model_type == "classifier":
        mode = "classification"
        predict_fn = model.predict_proba
    else:
        mode = "regression"
        predict_fn = model.predict

    # LIMEエクスプレイナーの作成
    explainer = LimeTabularExplainer(
        training_data=X_array,
        feature_names=feature_names,
        mode=mode,
        random_state=42,
    )

    # 説明の生成
    if model_type == "classifier":
        explanation = explainer.explain_instance(
            data_row=instance,
            predict_fn=predict_fn,
            num_features=min(num_features, len(feature_names)),
            num_samples=num_samples,
        )

        # 予測クラスと確率
        proba = model.predict_proba([instance])[0]
        predicted_class = int(np.argmax(proba))
        prediction_probabilities = proba.tolist()
    else:
        explanation = explainer.explain_instance(
            data_row=instance,
            predict_fn=predict_fn,
            num_features=min(num_features, len(feature_names)),
            num_samples=num_samples,
        )
        predicted_class = None
        prediction_probabilities = None

    # 特徴量の重みを抽出
    feature_weights = {}
    top_features = []

    for feature_name, weight in explanation.as_list():
        # LIMEはフォーマット「feature_name <= value」などで返すことがある
        # 実際の特徴量名を抽出
        clean_name = _extract_feature_name(feature_name, feature_names)
        feature_weights[clean_name] = float(weight)
        top_features.append(
            {
                "feature": clean_name,
                "weight": float(weight),
                "description": feature_name,
            }
        )

    # 局所的忠実度スコア
    local_fidelity_score = float(explanation.score) if hasattr(explanation, "score") else 0.0

    # interceptの取得（dictまたはlist/arrayの場合に対応）
    intercept_value = 0.0
    if hasattr(explanation, "intercept"):
        intercept = explanation.intercept
        if isinstance(intercept, dict):
            # dictの場合は最初の値を取得
            if intercept:
                intercept_value = float(list(intercept.values())[0])
        elif isinstance(intercept, (list, np.ndarray)):
            if len(intercept) > 1:
                intercept_value = float(intercept[1])
            elif len(intercept) == 1:
                intercept_value = float(intercept[0])
        else:
            intercept_value = float(intercept)

    # local_predの取得
    local_pred_value = None
    if hasattr(explanation, "local_pred"):
        local_pred = explanation.local_pred
        if isinstance(local_pred, (list, np.ndarray)) and len(local_pred) > 0:
            local_pred_value = float(local_pred[0])
        elif isinstance(local_pred, (int, float)):
            local_pred_value = float(local_pred)

    result = {
        "explanation": {
            "intercept": intercept_value,
            "local_prediction": local_pred_value,
        },
        "feature_weights": feature_weights,
        "top_features": top_features[:num_features],
        "local_fidelity_score": local_fidelity_score,
    }

    if model_type == "classifier":
        result["predicted_class"] = predicted_class
        result["prediction_probabilities"] = prediction_probabilities
    else:
        result["predicted_value"] = float(model.predict([instance])[0])

    return result


def _extract_feature_name(lime_feature: str, feature_names: List[str]) -> str:
    """LIMEの特徴量記述から元の特徴量名を抽出"""
    # LIMEは「feature_name <= value」や「value < feature_name」などの形式で返す
    for name in feature_names:
        if name in lime_feature:
            return name

    # 見つからない場合はそのまま返す
    return lime_feature.split()[0] if " " in lime_feature else lime_feature
