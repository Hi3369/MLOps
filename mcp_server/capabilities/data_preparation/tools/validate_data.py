"""
Validate Data Tool

データバリデーションツール
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def validate_data(
    s3_uri: str,
    file_format: str = "csv",
    required_columns: List[str] = None,
    max_missing_ratio: float = 0.5,
) -> Dict[str, Any]:
    """
    データのバリデーションを実行

    Args:
        s3_uri: S3 URI (例: s3://bucket-name/path/to/file.csv)
        file_format: ファイルフォーマット (csv, parquet, json)
        required_columns: 必須カラムのリスト (Noneの場合はチェックしない)
        max_missing_ratio: 許容する欠損値の割合 (0.0-1.0)

    Returns:
        バリデーション結果

    Raises:
        ValueError: バリデーションエラー
    """
    logger.info(f"Validating data from {s3_uri}")

    # load_datasetツールを使用してデータを読み込み
    from .load_dataset import load_dataset

    load_result = load_dataset(s3_uri=s3_uri, file_format=file_format)
    dataset_info = load_result["dataset_info"]

    validation_results = {
        "is_valid": True,
        "errors": [],
        "warnings": [],
        "checks": {},
    }

    # 1. 必須カラムチェック
    if required_columns:
        missing_columns = set(required_columns) - set(dataset_info["column_names"])
        if missing_columns:
            validation_results["is_valid"] = False
            validation_results["errors"].append(
                f"Missing required columns: {list(missing_columns)}"
            )
        validation_results["checks"]["required_columns"] = {
            "passed": len(missing_columns) == 0,
            "missing": list(missing_columns),
        }

    # 2. 欠損値チェック
    missing_values = dataset_info["missing_values"]
    total_rows = dataset_info["rows"]

    high_missing_columns = {}
    for col, missing_count in missing_values.items():
        if missing_count > 0:
            missing_ratio = missing_count / total_rows
            if missing_ratio > max_missing_ratio:
                high_missing_columns[col] = {
                    "count": int(missing_count),
                    "ratio": round(missing_ratio, 4),
                }

    if high_missing_columns:
        validation_results["warnings"].append(
            f"Columns with high missing values (>{max_missing_ratio * 100}%): "
            f"{list(high_missing_columns.keys())}"
        )

    validation_results["checks"]["missing_values"] = {
        "total_missing": sum(missing_values.values()),
        "high_missing_columns": high_missing_columns,
    }

    # 3. データ型チェック
    dtype_issues = []
    for col, dtype in dataset_info["dtypes"].items():
        # object型は文字列として扱われる可能性が高いが、確認が必要
        if dtype == "object":
            dtype_issues.append(col)

    if dtype_issues:
        validation_results["warnings"].append(
            f"Columns with 'object' dtype (may need type conversion): {dtype_issues}"
        )

    validation_results["checks"]["data_types"] = {
        "object_columns": dtype_issues,
        "total_columns": dataset_info["columns"],
    }

    # 4. データサイズチェック
    if total_rows == 0:
        validation_results["is_valid"] = False
        validation_results["errors"].append("Dataset is empty (0 rows)")

    validation_results["checks"]["data_size"] = {
        "rows": total_rows,
        "columns": dataset_info["columns"],
        "memory_mb": round(dataset_info["memory_usage_mb"], 2),
    }

    # 5. サマリー
    logger.info(
        f"Validation completed: valid={validation_results['is_valid']}, "
        f"errors={len(validation_results['errors'])}, "
        f"warnings={len(validation_results['warnings'])}"
    )

    return {
        "status": "success" if validation_results["is_valid"] else "failed",
        "message": "Data validation completed",
        "s3_uri": s3_uri,
        "validation_results": validation_results,
    }
