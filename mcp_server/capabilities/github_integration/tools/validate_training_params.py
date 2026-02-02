"""
Validate Training Params Tool

学習パラメータバリデーションツール
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


# サポートされるモデルタイプとそのハイパーパラメータ定義
SUPPORTED_MODEL_TYPES = {
    "xgboost": {
        "hyperparameters": {
            "n_estimators": {"type": "int", "min": 1, "max": 10000, "default": 100},
            "max_depth": {"type": "int", "min": 1, "max": 100, "default": 6},
            "learning_rate": {"type": "float", "min": 0.001, "max": 1.0, "default": 0.1},
            "subsample": {"type": "float", "min": 0.1, "max": 1.0, "default": 0.8},
            "colsample_bytree": {
                "type": "float",
                "min": 0.1,
                "max": 1.0,
                "default": 0.8,
            },
            "min_child_weight": {"type": "int", "min": 1, "max": 100, "default": 1},
            "gamma": {"type": "float", "min": 0, "max": 100, "default": 0},
            "reg_alpha": {"type": "float", "min": 0, "max": 100, "default": 0},
            "reg_lambda": {"type": "float", "min": 0, "max": 100, "default": 1},
        },
        "required": [],
    },
    "random_forest": {
        "hyperparameters": {
            "n_estimators": {"type": "int", "min": 1, "max": 10000, "default": 100},
            "max_depth": {
                "type": "int",
                "min": 1,
                "max": 100,
                "default": None,
                "nullable": True,
            },
            "min_samples_split": {"type": "int", "min": 2, "max": 100, "default": 2},
            "min_samples_leaf": {"type": "int", "min": 1, "max": 100, "default": 1},
            "max_features": {
                "type": "string",
                "values": ["auto", "sqrt", "log2"],
                "default": "sqrt",
            },
            "bootstrap": {"type": "bool", "default": True},
        },
        "required": [],
    },
    "neural_network": {
        "hyperparameters": {
            "hidden_layers": {"type": "list", "min_length": 1, "default": [64, 32]},
            "learning_rate": {
                "type": "float",
                "min": 0.00001,
                "max": 1.0,
                "default": 0.001,
            },
            "batch_size": {"type": "int", "min": 1, "max": 10000, "default": 32},
            "epochs": {"type": "int", "min": 1, "max": 10000, "default": 100},
            "dropout": {"type": "float", "min": 0, "max": 0.9, "default": 0.2},
            "activation": {
                "type": "string",
                "values": ["relu", "tanh", "sigmoid", "leaky_relu"],
                "default": "relu",
            },
            "optimizer": {
                "type": "string",
                "values": ["adam", "sgd", "rmsprop", "adagrad"],
                "default": "adam",
            },
        },
        "required": [],
    },
    "logistic_regression": {
        "hyperparameters": {
            "C": {"type": "float", "min": 0.0001, "max": 1000, "default": 1.0},
            "max_iter": {"type": "int", "min": 1, "max": 10000, "default": 100},
            "solver": {
                "type": "string",
                "values": ["lbfgs", "liblinear", "newton-cg", "saga"],
                "default": "lbfgs",
            },
            "penalty": {"type": "string", "values": ["l1", "l2", "none"], "default": "l2"},
        },
        "required": [],
    },
    "lightgbm": {
        "hyperparameters": {
            "n_estimators": {"type": "int", "min": 1, "max": 10000, "default": 100},
            "max_depth": {"type": "int", "min": -1, "max": 100, "default": -1},
            "learning_rate": {"type": "float", "min": 0.001, "max": 1.0, "default": 0.1},
            "num_leaves": {"type": "int", "min": 2, "max": 10000, "default": 31},
            "min_child_samples": {"type": "int", "min": 1, "max": 10000, "default": 20},
            "subsample": {"type": "float", "min": 0.1, "max": 1.0, "default": 1.0},
            "colsample_bytree": {"type": "float", "min": 0.1, "max": 1.0, "default": 1.0},
        },
        "required": [],
    },
}


def validate_training_params(
    training_config: Dict[str, Any],
    strict: bool = False,
) -> Dict[str, Any]:
    """
    学習パラメータをバリデーション

    Args:
        training_config: 学習設定（model_type, hyperparameters, dataset等）
        strict: 厳密モード（True: 不明なパラメータをエラーに）

    Returns:
        バリデーション結果辞書
    """
    logger.info("Validating training parameters")

    # パラメータ検証
    if not training_config:
        raise ValueError("training_config must not be empty")

    if not isinstance(training_config, dict):
        raise ValueError("training_config must be a dictionary")

    try:
        errors = []
        warnings = []
        validated_config = {}

        # モデルタイプの検証
        model_type = training_config.get("model_type")
        if not model_type:
            errors.append(
                {
                    "field": "model_type",
                    "message": "model_type is required",
                    "severity": "error",
                }
            )
        elif model_type not in SUPPORTED_MODEL_TYPES:
            errors.append(
                {
                    "field": "model_type",
                    "message": f"Unsupported model_type: {model_type}. "
                    f"Supported types: {list(SUPPORTED_MODEL_TYPES.keys())}",
                    "severity": "error",
                }
            )
        else:
            validated_config["model_type"] = model_type

        # データセットの検証
        dataset: Dict[str, Any] = training_config.get("dataset", {})
        dataset_validation = _validate_dataset(dataset)
        errors.extend(dataset_validation["errors"])
        warnings.extend(dataset_validation["warnings"])
        if dataset_validation["validated"]:
            validated_config["dataset"] = dataset_validation["validated"]

        # ハイパーパラメータの検証
        if model_type and model_type in SUPPORTED_MODEL_TYPES:
            hyperparameters = training_config.get("hyperparameters", {})
            hp_validation = _validate_hyperparameters(model_type, hyperparameters, strict)
            errors.extend(hp_validation["errors"])
            warnings.extend(hp_validation["warnings"])
            validated_config["hyperparameters"] = hp_validation["validated"]

        # 追加オプションの検証
        if "compute_config" in training_config:
            compute_validation = _validate_compute_config(training_config["compute_config"])
            errors.extend(compute_validation["errors"])
            warnings.extend(compute_validation["warnings"])
            if compute_validation["validated"]:
                validated_config["compute_config"] = compute_validation["validated"]

        # 検証結果の判定
        is_valid = len(errors) == 0

        logger.info(
            f"Validation result: valid={is_valid}, "
            f"errors={len(errors)}, warnings={len(warnings)}"
        )

        return {
            "status": "success" if is_valid else "failed",
            "message": "Validation passed" if is_valid else "Validation failed",
            "validation_result": {
                "is_valid": is_valid,
                "errors": errors,
                "warnings": warnings,
                "validated_config": validated_config if is_valid else None,
                "original_config": training_config,
            },
        }

    except Exception as e:
        logger.error(f"Training params validation error: {e}")
        raise ValueError(f"Failed to validate training params: {e}")


def _validate_dataset(dataset: Dict[str, Any]) -> Dict[str, Any]:
    """データセット設定を検証"""
    errors: list[Dict[str, Any]] = []
    warnings: list[Dict[str, Any]] = []
    validated: Dict[str, Any] = {}

    if not dataset:
        errors.append(
            {
                "field": "dataset",
                "message": "dataset configuration is required",
                "severity": "error",
            }
        )
        return {"errors": errors, "warnings": warnings, "validated": None}

    # S3パスの検証
    s3_path = dataset.get("s3_path")
    if not s3_path:
        errors.append(
            {
                "field": "dataset.s3_path",
                "message": "s3_path is required",
                "severity": "error",
            }
        )
    elif not s3_path.startswith("s3://"):
        errors.append(
            {
                "field": "dataset.s3_path",
                "message": "s3_path must start with 's3://'",
                "severity": "error",
            }
        )
    else:
        validated["s3_path"] = s3_path

    # ターゲットカラムの検証
    target_column = dataset.get("target_column")
    if not target_column:
        errors.append(
            {
                "field": "dataset.target_column",
                "message": "target_column is required",
                "severity": "error",
            }
        )
    else:
        validated["target_column"] = target_column

    # オプションフィールド
    if "feature_columns" in dataset:
        validated["feature_columns"] = dataset["feature_columns"]

    if "train_test_split" in dataset:
        split = dataset["train_test_split"]
        if isinstance(split, (int, float)):
            if not 0.1 <= split <= 0.9:
                warnings.append(
                    {
                        "field": "dataset.train_test_split",
                        "message": "train_test_split should be between 0.1 and 0.9",
                        "severity": "warning",
                    }
                )
            validated["train_test_split"] = split

    return {"errors": errors, "warnings": warnings, "validated": validated}


def _validate_hyperparameters(
    model_type: str, hyperparameters: Dict[str, Any], strict: bool
) -> Dict[str, Any]:
    """ハイパーパラメータを検証"""
    errors = []
    warnings = []
    validated = {}

    model_spec: Dict[str, Any] = SUPPORTED_MODEL_TYPES.get(model_type, {})
    hp_specs: Dict[str, Any] = model_spec.get("hyperparameters", {})
    required_params: list = model_spec.get("required", [])

    # 必須パラメータのチェック
    for param in required_params:
        if param not in hyperparameters:
            errors.append(
                {
                    "field": f"hyperparameters.{param}",
                    "message": f"{param} is required for {model_type}",
                    "severity": "error",
                }
            )

    # 各パラメータの検証
    for param_name, param_value in hyperparameters.items():
        if param_name not in hp_specs:
            if strict:
                errors.append(
                    {
                        "field": f"hyperparameters.{param_name}",
                        "message": f"Unknown parameter: {param_name}",
                        "severity": "error",
                    }
                )
            else:
                warnings.append(
                    {
                        "field": f"hyperparameters.{param_name}",
                        "message": f"Unknown parameter: {param_name} (will be passed through)",
                        "severity": "warning",
                    }
                )
                validated[param_name] = param_value
            continue

        spec = hp_specs[param_name]
        validation = _validate_single_param(param_name, param_value, spec)

        if validation["error"]:
            errors.append(validation["error"])
        elif validation["warning"]:
            warnings.append(validation["warning"])
            validated[param_name] = validation["value"]
        else:
            validated[param_name] = validation["value"]

    # デフォルト値の設定
    for param_name, spec in hp_specs.items():
        if param_name not in validated and "default" in spec:
            validated[param_name] = spec["default"]

    return {"errors": errors, "warnings": warnings, "validated": validated}


def _validate_single_param(name: str, value: Any, spec: Dict[str, Any]) -> Dict[str, Any]:
    """単一パラメータを検証"""
    param_type = spec.get("type")
    result = {"value": value, "error": None, "warning": None}

    # null許容チェック
    if value is None:
        if spec.get("nullable", False):
            return result
        else:
            result["error"] = {
                "field": f"hyperparameters.{name}",
                "message": f"{name} cannot be null",
                "severity": "error",
            }
            return result

    # 型チェック
    if param_type == "int":
        if not isinstance(value, int) or isinstance(value, bool):
            result["error"] = {
                "field": f"hyperparameters.{name}",
                "message": f"{name} must be an integer",
                "severity": "error",
            }
            return result
        if "min" in spec and value < spec["min"]:
            result["error"] = {
                "field": f"hyperparameters.{name}",
                "message": f"{name} must be >= {spec['min']}",
                "severity": "error",
            }
            return result
        if "max" in spec and value > spec["max"]:
            result["error"] = {
                "field": f"hyperparameters.{name}",
                "message": f"{name} must be <= {spec['max']}",
                "severity": "error",
            }
            return result

    elif param_type == "float":
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            result["error"] = {
                "field": f"hyperparameters.{name}",
                "message": f"{name} must be a number",
                "severity": "error",
            }
            return result
        value = float(value)
        result["value"] = value
        if "min" in spec and value < spec["min"]:
            result["error"] = {
                "field": f"hyperparameters.{name}",
                "message": f"{name} must be >= {spec['min']}",
                "severity": "error",
            }
            return result
        if "max" in spec and value > spec["max"]:
            result["error"] = {
                "field": f"hyperparameters.{name}",
                "message": f"{name} must be <= {spec['max']}",
                "severity": "error",
            }
            return result

    elif param_type == "string":
        if not isinstance(value, str):
            result["error"] = {
                "field": f"hyperparameters.{name}",
                "message": f"{name} must be a string",
                "severity": "error",
            }
            return result
        if "values" in spec and value not in spec["values"]:
            result["error"] = {
                "field": f"hyperparameters.{name}",
                "message": f"{name} must be one of {spec['values']}",
                "severity": "error",
            }
            return result

    elif param_type == "bool":
        if not isinstance(value, bool):
            result["error"] = {
                "field": f"hyperparameters.{name}",
                "message": f"{name} must be a boolean",
                "severity": "error",
            }
            return result

    elif param_type == "list":
        if not isinstance(value, list):
            result["error"] = {
                "field": f"hyperparameters.{name}",
                "message": f"{name} must be a list",
                "severity": "error",
            }
            return result
        if "min_length" in spec and len(value) < spec["min_length"]:
            result["error"] = {
                "field": f"hyperparameters.{name}",
                "message": f"{name} must have at least {spec['min_length']} elements",
                "severity": "error",
            }
            return result

    return result


def _validate_compute_config(compute_config: Dict[str, Any]) -> Dict[str, Any]:
    """コンピュート設定を検証"""
    errors = []
    warnings = []
    validated = {}

    # インスタンスタイプの検証
    instance_type = compute_config.get("instance_type")
    if instance_type:
        valid_prefixes = ["ml.", "local"]
        if not any(instance_type.startswith(p) for p in valid_prefixes):
            warnings.append(
                {
                    "field": "compute_config.instance_type",
                    "message": f"Unusual instance_type: {instance_type}",
                    "severity": "warning",
                }
            )
        validated["instance_type"] = instance_type

    # インスタンス数の検証
    instance_count = compute_config.get("instance_count", 1)
    if isinstance(instance_count, int) and instance_count >= 1:
        validated["instance_count"] = instance_count
    else:
        errors.append(
            {
                "field": "compute_config.instance_count",
                "message": "instance_count must be a positive integer",
                "severity": "error",
            }
        )

    # その他のオプション
    for key in ["use_spot_instances", "max_runtime_seconds"]:
        if key in compute_config:
            validated[key] = compute_config[key]

    return {"errors": errors, "warnings": warnings, "validated": validated}
