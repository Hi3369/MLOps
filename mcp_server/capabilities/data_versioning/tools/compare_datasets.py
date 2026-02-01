"""
Compare Datasets Tool

データセット比較ツール
"""

import hashlib
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def compare_datasets(
    dataset_name: str,
    version_a: str,
    version_b: str,
    compare_schema: bool = True,
    compare_statistics: bool = True,
    compare_sample: bool = False,
    sample_size: int = 100,
) -> Dict[str, Any]:
    """
    2つのデータセットバージョンを比較する

    Args:
        dataset_name: データセット名
        version_a: 比較元バージョン
        version_b: 比較先バージョン
        compare_schema: スキーマ比較を行うか
        compare_statistics: 統計情報比較を行うか
        compare_sample: サンプルデータ比較を行うか
        sample_size: サンプルサイズ

    Returns:
        比較結果辞書
    """
    logger.info(f"Comparing datasets: {dataset_name} {version_a} vs {version_b}")

    # パラメータ検証
    if not dataset_name:
        raise ValueError("dataset_name must not be empty")

    if not version_a:
        raise ValueError("version_a must not be empty")

    if not version_b:
        raise ValueError("version_b must not be empty")

    if version_a == version_b:
        raise ValueError("version_a and version_b must be different")

    if sample_size < 1:
        raise ValueError("sample_size must be at least 1")

    if sample_size > 10000:
        raise ValueError("sample_size must be 10000 or less")

    try:
        env = os.environ.get("MLOPS_ENV", "development")
        timestamp = datetime.now(timezone.utc).isoformat()
        comparison_id = str(uuid4())[:8]

        # 開発/テスト環境ではモック
        if env in ["development", "test"]:
            return _mock_compare_datasets(
                dataset_name=dataset_name,
                version_a=version_a,
                version_b=version_b,
                compare_schema=compare_schema,
                compare_statistics=compare_statistics,
                compare_sample=compare_sample,
                sample_size=sample_size,
                comparison_id=comparison_id,
                timestamp=timestamp,
            )

        # 本番環境: S3からデータ取得して比較
        return _real_compare_datasets(
            dataset_name=dataset_name,
            version_a=version_a,
            version_b=version_b,
            compare_schema=compare_schema,
            compare_statistics=compare_statistics,
            compare_sample=compare_sample,
            sample_size=sample_size,
            comparison_id=comparison_id,
            timestamp=timestamp,
        )

    except ClientError as e:
        logger.error(f"AWS error comparing datasets: {e}")
        raise ValueError(f"Failed to compare datasets: {e}")
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Failed to compare datasets: {e}")
        raise ValueError(f"Failed to compare datasets: {e}")


def _generate_mock_version_info(dataset_name: str, version: str) -> Dict[str, Any]:
    """モックバージョン情報を生成"""
    seed = int(hashlib.md5(f"{dataset_name}:{version}".encode()).hexdigest()[:8], 16)

    base_columns = ["id", "feature1", "feature2", "feature3", "target"]
    column_types = ["int64", "float64", "float64", "float64", "int64"]

    # バージョンによって微妙に異なるスキーマ
    if seed % 3 == 0:
        base_columns.append("feature4")
        column_types.append("float64")

    row_count = 1000 + (seed % 9000)

    return {
        "version": version,
        "row_count": row_count,
        "column_count": len(base_columns),
        "columns": base_columns,
        "column_types": dict(zip(base_columns, column_types)),
        "file_format": "csv",
        "size_bytes": row_count * len(base_columns) * 8,
        "statistics": {
            col: {
                "mean": round((seed + i * 17) % 100 / 10.0, 4),
                "std": round((seed + i * 23) % 50 / 10.0, 4),
                "min": round((seed + i * 7) % 10 / 10.0, 4),
                "max": round((seed + i * 31) % 100, 4),
                "null_count": (seed + i * 11) % 50,
            }
            for i, col in enumerate(base_columns)
            if col != "id"
        },
    }


def _compute_schema_diff(info_a: Dict[str, Any], info_b: Dict[str, Any]) -> Dict[str, Any]:
    """スキーマの差分を計算"""
    cols_a = set(info_a["columns"])
    cols_b = set(info_b["columns"])

    added = list(cols_b - cols_a)
    removed = list(cols_a - cols_b)
    common = list(cols_a & cols_b)

    # 型変更の検出
    type_changes = {}
    for col in common:
        type_a = info_a["column_types"].get(col)
        type_b = info_b["column_types"].get(col)
        if type_a != type_b:
            type_changes[col] = {"from": type_a, "to": type_b}

    return {
        "columns_added": added,
        "columns_removed": removed,
        "columns_common": common,
        "type_changes": type_changes,
        "schema_compatible": len(removed) == 0 and len(type_changes) == 0,
    }


def _compute_statistics_diff(info_a: Dict[str, Any], info_b: Dict[str, Any]) -> Dict[str, Any]:
    """統計情報の差分を計算"""
    stats_a = info_a.get("statistics", {})
    stats_b = info_b.get("statistics", {})

    common_cols = set(stats_a.keys()) & set(stats_b.keys())

    column_diffs = {}
    for col in common_cols:
        sa = stats_a[col]
        sb = stats_b[col]
        column_diffs[col] = {
            "mean_change": round(sb.get("mean", 0) - sa.get("mean", 0), 4),
            "std_change": round(sb.get("std", 0) - sa.get("std", 0), 4),
            "null_count_change": sb.get("null_count", 0) - sa.get("null_count", 0),
        }

    return {
        "row_count_change": info_b["row_count"] - info_a["row_count"],
        "column_count_change": info_b["column_count"] - info_a["column_count"],
        "size_change_bytes": info_b["size_bytes"] - info_a["size_bytes"],
        "column_statistics": column_diffs,
    }


def _mock_compare_datasets(
    dataset_name: str,
    version_a: str,
    version_b: str,
    compare_schema: bool,
    compare_statistics: bool,
    compare_sample: bool,
    sample_size: int,
    comparison_id: str,
    timestamp: str,
) -> Dict[str, Any]:
    """モックデータセット比較（開発・テスト用）"""
    logger.info("Using mock dataset comparison")

    info_a = _generate_mock_version_info(dataset_name, version_a)
    info_b = _generate_mock_version_info(dataset_name, version_b)

    result = {
        "status": "success",
        "message": f"Compared {dataset_name}: {version_a} vs {version_b}",
        "comparison_info": {
            "comparison_id": f"dc-{comparison_id}",
            "dataset_name": dataset_name,
            "version_a": info_a,
            "version_b": info_b,
            "compared_at": timestamp,
            "mock": True,
        },
    }

    if compare_schema:
        result["comparison_info"]["schema_diff"] = _compute_schema_diff(info_a, info_b)

    if compare_statistics:
        result["comparison_info"]["statistics_diff"] = _compute_statistics_diff(info_a, info_b)

    if compare_sample:
        result["comparison_info"]["sample_comparison"] = {
            "sample_size": sample_size,
            "matching_rows": sample_size - (sample_size // 10),
            "different_rows": sample_size // 10,
            "match_rate": round(1.0 - (sample_size // 10) / sample_size, 4),
        }

    return result


def _real_compare_datasets(
    dataset_name: str,
    version_a: str,
    version_b: str,
    compare_schema: bool,
    compare_statistics: bool,
    compare_sample: bool,
    sample_size: int,
    comparison_id: str,
    timestamp: str,
) -> Dict[str, Any]:
    """本番データセット比較（S3からデータ取得）"""
    import json

    s3_client = boto3.client("s3")
    bucket = os.environ.get("MLOPS_DATA_VERSION_BUCKET", "mlops-data-versions")

    # 両バージョンのメタデータ取得
    versions_data = {}
    for ver in [version_a, version_b]:
        s3_key = f"datasets/{dataset_name}/versions/{ver}/metadata.json"
        try:
            response = s3_client.get_object(Bucket=bucket, Key=s3_key)
            versions_data[ver] = json.loads(response["Body"].read().decode("utf-8"))
        except ClientError:
            raise ValueError(f"Version metadata not found: {dataset_name} {ver}")

    info_a = versions_data[version_a]
    info_b = versions_data[version_b]

    result = {
        "status": "success",
        "message": f"Compared {dataset_name}: {version_a} vs {version_b}",
        "comparison_info": {
            "comparison_id": f"dc-{comparison_id}",
            "dataset_name": dataset_name,
            "version_a": info_a,
            "version_b": info_b,
            "compared_at": timestamp,
        },
    }

    if compare_schema and "schema" in info_a and "schema" in info_b:
        result["comparison_info"]["schema_diff"] = _compute_schema_diff(info_a, info_b)

    if compare_statistics:
        result["comparison_info"]["statistics_diff"] = _compute_statistics_diff(info_a, info_b)

    # 比較結果をS3に保存
    s3_key = f"comparisons/datasets/{comparison_id}.json"
    s3_client.put_object(
        Bucket=bucket,
        Key=s3_key,
        Body=json.dumps(result["comparison_info"]),
        ContentType="application/json",
    )

    return result
