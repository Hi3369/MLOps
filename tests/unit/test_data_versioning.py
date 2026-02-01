"""
Data Versioning Unit Tests

データバージョニング管理Capabilityのユニットテスト
TDD: Red → Green → Refactor
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from mcp_server.capabilities.data_versioning.capability import (
    DataVersioningCapability,
)
from mcp_server.capabilities.data_versioning.tools import (
    compare_datasets,
    get_dataset_lineage,
    version_dataset,
)
from mcp_server.server import MLOpsServer


# =============================================================================
# Capability クラステスト
# =============================================================================
class TestDataVersioningCapability:
    """DataVersioningCapabilityクラスのテスト"""

    def test_initialization(self):
        """Capability初期化テスト"""
        capability = DataVersioningCapability()
        assert capability is not None
        assert len(capability._tools) == 3

    def test_get_tools(self):
        """ツール取得テスト"""
        capability = DataVersioningCapability()
        tools = capability.get_tools()
        assert "version_dataset" in tools
        assert "get_dataset_lineage" in tools
        assert "compare_datasets" in tools

    def test_get_tool_schemas(self):
        """ツールスキーマ取得テスト"""
        capability = DataVersioningCapability()
        schemas = capability.get_tool_schemas()
        assert len(schemas) == 3
        for name, schema in schemas.items():
            assert "name" in schema
            assert "description" in schema
            assert "parameters" in schema

    def test_server_registration(self):
        """サーバー登録テスト"""
        server = MLOpsServer()
        assert "data_versioning" in server.capabilities
        assert "data_versioning.version_dataset" in server.tools
        assert "data_versioning.get_dataset_lineage" in server.tools
        assert "data_versioning.compare_datasets" in server.tools


# =============================================================================
# version_dataset テスト
# =============================================================================
class TestVersionDataset:
    """version_datasetツールのテスト"""

    def test_version_dataset_basic(self):
        """基本的なバージョン登録テスト"""
        result = version_dataset(
            dataset_name="training-data",
            s3_uri="s3://bucket/data/train.csv",
            version="v1.0.0",
        )
        assert result["status"] == "success"
        assert "version_info" in result
        info = result["version_info"]
        assert info["dataset_name"] == "training-data"
        assert info["version"] == "v1.0.0"
        assert info["version_id"].startswith("dv-")
        assert info["mock"] is True

    def test_version_dataset_with_description(self):
        """説明付きバージョン登録テスト"""
        result = version_dataset(
            dataset_name="test-data",
            s3_uri="s3://bucket/data/test.csv",
            version="v1.0.0",
            description="Initial training dataset with 10k samples",
        )
        assert result["status"] == "success"
        assert result["version_info"]["description"] == (
            "Initial training dataset with 10k samples"
        )

    def test_version_dataset_with_schema(self):
        """スキーマ付きバージョン登録テスト"""
        schema = {
            "id": "int64",
            "feature1": "float64",
            "feature2": "float64",
            "target": "int64",
        }
        result = version_dataset(
            dataset_name="schema-data",
            s3_uri="s3://bucket/data/schema.csv",
            version="v1.0.0",
            schema=schema,
        )
        assert result["status"] == "success"
        assert result["version_info"]["schema"] == schema

    def test_version_dataset_with_tags(self):
        """タグ付きバージョン登録テスト"""
        result = version_dataset(
            dataset_name="tagged-data",
            s3_uri="s3://bucket/data/tagged.csv",
            version="v1.0.0",
            tags=["production", "validated", "2026Q1"],
        )
        assert result["status"] == "success"
        assert result["version_info"]["tags"] == [
            "production",
            "validated",
            "2026Q1",
        ]

    def test_version_dataset_with_parent(self):
        """親バージョン指定のバージョン登録テスト"""
        result = version_dataset(
            dataset_name="derived-data",
            s3_uri="s3://bucket/data/derived.csv",
            version="v1.1.0",
            parent_version="v1.0.0",
        )
        assert result["status"] == "success"
        lineage = result["version_info"]["lineage"]
        assert lineage["parent_version"] == "v1.0.0"

    def test_version_dataset_with_row_count(self):
        """行数指定のバージョン登録テスト"""
        result = version_dataset(
            dataset_name="counted-data",
            s3_uri="s3://bucket/data/counted.csv",
            version="v1.0.0",
            row_count=50000,
        )
        assert result["status"] == "success"
        assert result["version_info"]["row_count"] == 50000

    def test_version_dataset_parquet_format(self):
        """Parquetフォーマットのバージョン登録テスト"""
        result = version_dataset(
            dataset_name="parquet-data",
            s3_uri="s3://bucket/data/data.parquet",
            version="v1.0.0",
            file_format="parquet",
        )
        assert result["status"] == "success"
        assert result["version_info"]["file_format"] == "parquet"

    def test_version_dataset_all_formats(self):
        """全フォーマットのバージョン登録テスト"""
        for fmt in ["csv", "parquet", "json", "orc", "avro"]:
            result = version_dataset(
                dataset_name=f"{fmt}-data",
                s3_uri=f"s3://bucket/data/data.{fmt}",
                version="v1.0.0",
                file_format=fmt,
            )
            assert result["status"] == "success"

    def test_version_dataset_with_metadata(self):
        """メタデータ付きバージョン登録テスト"""
        metadata = {
            "source": "ETL pipeline",
            "pipeline_version": "3.2.1",
            "quality_score": 0.98,
        }
        result = version_dataset(
            dataset_name="meta-data",
            s3_uri="s3://bucket/data/meta.csv",
            version="v1.0.0",
            metadata=metadata,
        )
        assert result["status"] == "success"
        assert result["version_info"]["metadata"] == metadata

    def test_version_dataset_full_params(self):
        """全パラメータ指定のバージョン登録テスト"""
        result = version_dataset(
            dataset_name="full-data",
            s3_uri="s3://bucket/data/full.parquet",
            version="v2.0.0",
            description="Full featured version",
            schema={"col1": "float64", "col2": "int64"},
            tags=["release"],
            parent_version="v1.0.0",
            row_count=100000,
            file_format="parquet",
            metadata={"key": "value"},
        )
        assert result["status"] == "success"
        info = result["version_info"]
        assert info["dataset_name"] == "full-data"
        assert info["file_format"] == "parquet"
        assert info["row_count"] == 100000

    def test_version_dataset_fingerprint(self):
        """フィンガープリント生成テスト"""
        result = version_dataset(
            dataset_name="fp-data",
            s3_uri="s3://bucket/data/fp.csv",
            version="v1.0.0",
        )
        assert result["status"] == "success"
        assert len(result["version_info"]["fingerprint"]) == 16

    def test_version_dataset_fingerprint_deterministic(self):
        """フィンガープリントの決定性テスト"""
        result1 = version_dataset(
            dataset_name="det-data",
            s3_uri="s3://bucket/data/det.csv",
            version="v1.0.0",
        )
        result2 = version_dataset(
            dataset_name="det-data",
            s3_uri="s3://bucket/data/det.csv",
            version="v1.0.0",
        )
        assert result1["version_info"]["fingerprint"] == result2["version_info"]["fingerprint"]

    def test_version_dataset_empty_name_error(self):
        """空のデータセット名エラーテスト"""
        with pytest.raises(ValueError, match="dataset_name must not be empty"):
            version_dataset(dataset_name="", s3_uri="s3://b/d", version="v1")

    def test_version_dataset_empty_s3_uri_error(self):
        """空のS3 URIエラーテスト"""
        with pytest.raises(ValueError, match="s3_uri must not be empty"):
            version_dataset(dataset_name="d", s3_uri="", version="v1")

    def test_version_dataset_invalid_s3_uri_error(self):
        """不正なS3 URIエラーテスト"""
        with pytest.raises(ValueError, match="must start with 's3://'"):
            version_dataset(dataset_name="d", s3_uri="http://wrong", version="v1")

    def test_version_dataset_empty_version_error(self):
        """空のバージョンエラーテスト"""
        with pytest.raises(ValueError, match="version must not be empty"):
            version_dataset(dataset_name="d", s3_uri="s3://b/d", version="")

    def test_version_dataset_invalid_format_error(self):
        """不正なファイル形式エラーテスト"""
        with pytest.raises(ValueError, match="file_format must be one of"):
            version_dataset(
                dataset_name="d",
                s3_uri="s3://b/d",
                version="v1",
                file_format="xlsx",
            )

    def test_version_dataset_negative_row_count_error(self):
        """負の行数エラーテスト"""
        with pytest.raises(ValueError, match="row_count must be a non-negative"):
            version_dataset(
                dataset_name="d",
                s3_uri="s3://b/d",
                version="v1",
                row_count=-1,
            )

    def test_version_dataset_via_server(self):
        """サーバー経由のバージョン登録テスト"""
        server = MLOpsServer()
        result = server.call_tool(
            "data_versioning.version_dataset",
            {
                "dataset_name": "server-test-data",
                "s3_uri": "s3://bucket/data/server.csv",
                "version": "v1.0.0",
            },
        )
        assert result["success"] is True
        assert result["result"]["status"] == "success"


# =============================================================================
# get_dataset_lineage テスト
# =============================================================================
class TestGetDatasetLineage:
    """get_dataset_lineageツールのテスト"""

    def test_get_lineage_basic(self):
        """基本的なリネージ取得テスト"""
        result = get_dataset_lineage(dataset_name="test-data")
        assert result["status"] == "success"
        assert "lineage_info" in result
        info = result["lineage_info"]
        assert info["dataset_name"] == "test-data"
        assert info["lineage_id"].startswith("lin-")
        assert isinstance(info["chain"], list)

    def test_get_lineage_with_version(self):
        """バージョン指定のリネージ取得テスト"""
        result = get_dataset_lineage(dataset_name="versioned-data", version="v2.0.0")
        assert result["status"] == "success"
        assert result["lineage_info"]["requested_version"] == "v2.0.0"

    def test_get_lineage_default_version(self):
        """デフォルトバージョンのリネージ取得テスト"""
        result = get_dataset_lineage(dataset_name="latest-data")
        assert result["status"] == "success"
        assert result["lineage_info"]["requested_version"] == "latest"

    def test_get_lineage_with_depth(self):
        """深さ指定のリネージ取得テスト"""
        result = get_dataset_lineage(dataset_name="deep-data", depth=2)
        assert result["status"] == "success"
        assert result["lineage_info"]["depth"] <= 2

    def test_get_lineage_chain_structure(self):
        """リネージチェーン構造テスト"""
        result = get_dataset_lineage(dataset_name="chain-data", version="v1.2.0")
        assert result["status"] == "success"
        chain = result["lineage_info"]["chain"]
        assert len(chain) > 0
        # 最初のノードは指定バージョン
        assert chain[0]["version"] == "v1.2.0"
        assert chain[0]["dataset_name"] == "chain-data"

    def test_get_lineage_with_transformations(self):
        """変換情報付きリネージ取得テスト"""
        result = get_dataset_lineage(
            dataset_name="transform-data",
            version="v1.2.0",
            include_transformations=True,
        )
        assert result["status"] == "success"
        assert result["lineage_info"]["include_transformations"] is True

    def test_get_lineage_without_transformations(self):
        """変換情報なしリネージ取得テスト"""
        result = get_dataset_lineage(
            dataset_name="no-transform-data",
            include_transformations=False,
        )
        assert result["status"] == "success"
        assert result["lineage_info"]["include_transformations"] is False

    def test_get_lineage_root_dataset(self):
        """ルートデータセット取得テスト"""
        result = get_dataset_lineage(dataset_name="root-data")
        assert result["status"] == "success"
        assert result["lineage_info"]["root_dataset"] is not None

    def test_get_lineage_empty_name_error(self):
        """空のデータセット名エラーテスト"""
        with pytest.raises(ValueError, match="dataset_name must not be empty"):
            get_dataset_lineage(dataset_name="")

    def test_get_lineage_depth_too_small_error(self):
        """深さが小さすぎるエラーテスト"""
        with pytest.raises(ValueError, match="depth must be at least 1"):
            get_dataset_lineage(dataset_name="d", depth=0)

    def test_get_lineage_depth_too_large_error(self):
        """深さが大きすぎるエラーテスト"""
        with pytest.raises(ValueError, match="depth must be 20 or less"):
            get_dataset_lineage(dataset_name="d", depth=21)

    def test_get_lineage_via_server(self):
        """サーバー経由のリネージ取得テスト"""
        server = MLOpsServer()
        result = server.call_tool(
            "data_versioning.get_dataset_lineage",
            {"dataset_name": "server-lineage-data"},
        )
        assert result["success"] is True
        assert result["result"]["status"] == "success"


# =============================================================================
# compare_datasets テスト
# =============================================================================
class TestCompareDatasets:
    """compare_datasetsツールのテスト"""

    def test_compare_basic(self):
        """基本的なデータセット比較テスト"""
        result = compare_datasets(
            dataset_name="compare-data",
            version_a="v1.0.0",
            version_b="v2.0.0",
        )
        assert result["status"] == "success"
        assert "comparison_info" in result
        info = result["comparison_info"]
        assert info["comparison_id"].startswith("dc-")
        assert info["dataset_name"] == "compare-data"

    def test_compare_with_schema_diff(self):
        """スキーマ比較テスト"""
        result = compare_datasets(
            dataset_name="schema-compare",
            version_a="v1.0.0",
            version_b="v2.0.0",
            compare_schema=True,
        )
        assert result["status"] == "success"
        assert "schema_diff" in result["comparison_info"]
        schema_diff = result["comparison_info"]["schema_diff"]
        assert "columns_added" in schema_diff
        assert "columns_removed" in schema_diff
        assert "columns_common" in schema_diff
        assert "schema_compatible" in schema_diff

    def test_compare_with_statistics_diff(self):
        """統計情報比較テスト"""
        result = compare_datasets(
            dataset_name="stats-compare",
            version_a="v1.0.0",
            version_b="v2.0.0",
            compare_statistics=True,
        )
        assert result["status"] == "success"
        assert "statistics_diff" in result["comparison_info"]
        stats = result["comparison_info"]["statistics_diff"]
        assert "row_count_change" in stats
        assert "column_count_change" in stats
        assert "size_change_bytes" in stats

    def test_compare_with_sample(self):
        """サンプル比較テスト"""
        result = compare_datasets(
            dataset_name="sample-compare",
            version_a="v1.0.0",
            version_b="v2.0.0",
            compare_sample=True,
            sample_size=50,
        )
        assert result["status"] == "success"
        sample = result["comparison_info"]["sample_comparison"]
        assert sample["sample_size"] == 50
        assert "matching_rows" in sample
        assert "different_rows" in sample
        assert "match_rate" in sample

    def test_compare_all_options(self):
        """全オプション比較テスト"""
        result = compare_datasets(
            dataset_name="all-compare",
            version_a="v1.0.0",
            version_b="v3.0.0",
            compare_schema=True,
            compare_statistics=True,
            compare_sample=True,
            sample_size=200,
        )
        assert result["status"] == "success"
        info = result["comparison_info"]
        assert "schema_diff" in info
        assert "statistics_diff" in info
        assert "sample_comparison" in info

    def test_compare_without_schema(self):
        """スキーマ比較なしテスト"""
        result = compare_datasets(
            dataset_name="no-schema-compare",
            version_a="v1.0.0",
            version_b="v2.0.0",
            compare_schema=False,
        )
        assert result["status"] == "success"
        assert "schema_diff" not in result["comparison_info"]

    def test_compare_without_statistics(self):
        """統計比較なしテスト"""
        result = compare_datasets(
            dataset_name="no-stats-compare",
            version_a="v1.0.0",
            version_b="v2.0.0",
            compare_statistics=False,
        )
        assert result["status"] == "success"
        assert "statistics_diff" not in result["comparison_info"]

    def test_compare_version_info_structure(self):
        """バージョン情報構造テスト"""
        result = compare_datasets(
            dataset_name="struct-compare",
            version_a="v1.0.0",
            version_b="v2.0.0",
        )
        assert result["status"] == "success"
        for ver_key in ["version_a", "version_b"]:
            ver_info = result["comparison_info"][ver_key]
            assert "version" in ver_info
            assert "row_count" in ver_info
            assert "column_count" in ver_info
            assert "columns" in ver_info

    def test_compare_deterministic(self):
        """決定的な比較結果テスト"""
        r1 = compare_datasets(
            dataset_name="det-compare",
            version_a="v1.0.0",
            version_b="v2.0.0",
        )
        r2 = compare_datasets(
            dataset_name="det-compare",
            version_a="v1.0.0",
            version_b="v2.0.0",
        )
        assert (
            r1["comparison_info"]["version_a"]["row_count"]
            == r2["comparison_info"]["version_a"]["row_count"]
        )

    def test_compare_empty_name_error(self):
        """空のデータセット名エラーテスト"""
        with pytest.raises(ValueError, match="dataset_name must not be empty"):
            compare_datasets(dataset_name="", version_a="v1", version_b="v2")

    def test_compare_empty_version_a_error(self):
        """空のversion_aエラーテスト"""
        with pytest.raises(ValueError, match="version_a must not be empty"):
            compare_datasets(dataset_name="d", version_a="", version_b="v2")

    def test_compare_empty_version_b_error(self):
        """空のversion_bエラーテスト"""
        with pytest.raises(ValueError, match="version_b must not be empty"):
            compare_datasets(dataset_name="d", version_a="v1", version_b="")

    def test_compare_same_version_error(self):
        """同一バージョン比較エラーテスト"""
        with pytest.raises(ValueError, match="must be different"):
            compare_datasets(dataset_name="d", version_a="v1.0.0", version_b="v1.0.0")

    def test_compare_sample_size_too_small_error(self):
        """サンプルサイズ小さすぎエラーテスト"""
        with pytest.raises(ValueError, match="sample_size must be at least 1"):
            compare_datasets(
                dataset_name="d",
                version_a="v1",
                version_b="v2",
                sample_size=0,
            )

    def test_compare_sample_size_too_large_error(self):
        """サンプルサイズ大きすぎエラーテスト"""
        with pytest.raises(ValueError, match="sample_size must be 10000"):
            compare_datasets(
                dataset_name="d",
                version_a="v1",
                version_b="v2",
                sample_size=10001,
            )

    def test_compare_via_server(self):
        """サーバー経由のデータセット比較テスト"""
        server = MLOpsServer()
        result = server.call_tool(
            "data_versioning.compare_datasets",
            {
                "dataset_name": "server-compare",
                "version_a": "v1.0.0",
                "version_b": "v2.0.0",
            },
        )
        assert result["success"] is True
        assert result["result"]["status"] == "success"


# =============================================================================
# 統合テスト
# =============================================================================
class TestDataVersioningIntegration:
    """データバージョニングの統合テスト"""

    @pytest.fixture
    def server(self) -> MLOpsServer:
        """テスト用サーバーインスタンス"""
        return MLOpsServer()

    def test_full_versioning_workflow(self, server: MLOpsServer):
        """バージョニングの完全ワークフローテスト"""
        # Step 1: 初期バージョン登録
        v1_result = server.call_tool(
            "data_versioning.version_dataset",
            {
                "dataset_name": "workflow-data",
                "s3_uri": "s3://bucket/data/v1/train.csv",
                "version": "v1.0.0",
                "description": "Initial dataset",
                "row_count": 10000,
                "file_format": "csv",
                "schema": {"feature1": "float64", "target": "int64"},
            },
        )
        assert v1_result["success"] is True

        # Step 2: 派生バージョン登録
        v2_result = server.call_tool(
            "data_versioning.version_dataset",
            {
                "dataset_name": "workflow-data",
                "s3_uri": "s3://bucket/data/v2/train.csv",
                "version": "v1.1.0",
                "parent_version": "v1.0.0",
                "description": "Added feature engineering",
                "row_count": 10000,
                "tags": ["feature-engineered"],
            },
        )
        assert v2_result["success"] is True
        assert v2_result["result"]["version_info"]["lineage"]["parent_version"] == "v1.0.0"

        # Step 3: リネージ取得
        lineage_result = server.call_tool(
            "data_versioning.get_dataset_lineage",
            {"dataset_name": "workflow-data"},
        )
        assert lineage_result["success"] is True
        assert lineage_result["result"]["lineage_info"]["depth"] > 0

        # Step 4: バージョン比較
        compare_result = server.call_tool(
            "data_versioning.compare_datasets",
            {
                "dataset_name": "workflow-data",
                "version_a": "v1.0.0",
                "version_b": "v1.1.0",
                "compare_schema": True,
                "compare_statistics": True,
            },
        )
        assert compare_result["success"] is True

    def test_multi_version_lineage_tracking(self, server: MLOpsServer):
        """複数バージョンのリネージ追跡テスト"""
        versions = [
            ("v1.0.0", None, "Raw data"),
            ("v1.1.0", "v1.0.0", "Cleaned data"),
            ("v2.0.0", "v1.1.0", "Feature engineered"),
        ]

        for ver, parent, desc in versions:
            result = server.call_tool(
                "data_versioning.version_dataset",
                {
                    "dataset_name": "lineage-tracking-data",
                    "s3_uri": f"s3://bucket/data/{ver}/data.csv",
                    "version": ver,
                    "parent_version": parent,
                    "description": desc,
                },
            )
            assert result["success"] is True

        # リネージを確認
        lineage_result = server.call_tool(
            "data_versioning.get_dataset_lineage",
            {
                "dataset_name": "lineage-tracking-data",
                "version": "v2.0.0",
                "depth": 10,
            },
        )
        assert lineage_result["success"] is True

    def test_data_quality_comparison_workflow(self, server: MLOpsServer):
        """データ品質比較ワークフローテスト"""
        # バージョン登録
        for ver in ["v1.0.0", "v2.0.0"]:
            server.call_tool(
                "data_versioning.version_dataset",
                {
                    "dataset_name": "quality-data",
                    "s3_uri": f"s3://bucket/data/{ver}/data.parquet",
                    "version": ver,
                    "file_format": "parquet",
                    "tags": ["quality-check"],
                },
            )

        # 全オプションで比較
        result = server.call_tool(
            "data_versioning.compare_datasets",
            {
                "dataset_name": "quality-data",
                "version_a": "v1.0.0",
                "version_b": "v2.0.0",
                "compare_schema": True,
                "compare_statistics": True,
                "compare_sample": True,
                "sample_size": 500,
            },
        )
        assert result["success"] is True
        info = result["result"]["comparison_info"]
        assert "schema_diff" in info
        assert "statistics_diff" in info
        assert "sample_comparison" in info
