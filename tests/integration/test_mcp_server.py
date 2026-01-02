"""
MCP Server Integration Tests

MCPサーバーの統合テスト
"""

import io
import os
import sys
from unittest.mock import Mock, patch

import pandas as pd
import pytest

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from mcp_server.server import MLOpsServer


class TestMLOpsServerInitialization:
    """
    MLOpsサーバー初期化のテスト
    """

    def test_server_initialization(self):
        """
        サーバーの正常初期化テスト
        """
        server = MLOpsServer()

        # サーバーインスタンスの確認
        assert server is not None
        assert hasattr(server, "tools")
        assert hasattr(server, "capabilities")

        # Data Preparation Capabilityの登録確認
        assert "data_preparation" in server.capabilities
        assert len(server.tools) > 0

    def test_tools_registration(self):
        """
        ツール登録の確認テスト
        """
        server = MLOpsServer()

        # Data Preparation toolsが登録されていることを確認
        expected_tools = [
            "data_preparation.load_dataset",
            "data_preparation.validate_data",
            "data_preparation.preprocess_supervised",
        ]

        for tool_name in expected_tools:
            assert tool_name in server.tools, f"Tool {tool_name} not registered"

    def test_list_tools(self):
        """
        ツールリスト取得のテスト
        """
        server = MLOpsServer()

        tools = server.list_tools()

        # ツールリストが返されることを確認
        assert isinstance(tools, list)
        assert len(tools) > 0

        # 各ツールが必要な属性を持つことを確認
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool


class TestToolExecution:
    """
    ツール実行のテスト
    """

    @pytest.fixture
    def server(self):
        """テスト用サーバーインスタンス"""
        return MLOpsServer()

    @pytest.fixture
    def sample_csv_data(self):
        """テスト用CSVデータ"""
        return pd.DataFrame(
            {
                "feature1": [1, 2, 3, 4, 5],
                "feature2": [10.0, 20.0, 30.0, 40.0, 50.0],
                "target": [0, 1, 0, 1, 0],
            }
        )

    @pytest.fixture
    def mock_s3(self, sample_csv_data):
        """モックS3クライアント"""
        with patch("boto3.client") as mock_client:
            csv_buffer = io.StringIO()
            sample_csv_data.to_csv(csv_buffer, index=False)
            csv_bytes = csv_buffer.getvalue().encode("utf-8")

            mock_s3_instance = Mock()
            mock_s3_instance.get_object.return_value = {
                "Body": io.BytesIO(csv_bytes),
            }
            mock_s3_instance.put_object.return_value = {}
            mock_client.return_value = mock_s3_instance

            yield mock_s3_instance

    def test_call_load_dataset(self, server, mock_s3):
        """
        load_datasetツールの実行テスト
        """
        result = server.call_tool(
            "data_preparation.load_dataset",
            {"s3_uri": "s3://test-bucket/data.csv", "file_format": "csv"},
        )

        # 実行結果の確認
        assert result["success"] is True
        assert "result" in result

        # ツール実行結果の確認
        tool_result = result["result"]
        assert tool_result["status"] == "success"
        assert "dataset_info" in tool_result
        assert tool_result["dataset_info"]["rows"] == 5
        assert tool_result["dataset_info"]["columns"] == 3

    def test_call_validate_data(self, server, mock_s3):
        """
        validate_dataツールの実行テスト
        """
        result = server.call_tool(
            "data_preparation.validate_data",
            {
                "s3_uri": "s3://test-bucket/data.csv",
                "file_format": "csv",
                "required_columns": ["feature1", "target"],
            },
        )

        # 実行結果の確認
        assert result["success"] is True
        assert "result" in result

        # バリデーション結果の確認
        tool_result = result["result"]
        assert tool_result["status"] == "success"
        assert "validation_results" in tool_result
        assert tool_result["validation_results"]["is_valid"] is True

    def test_call_preprocess_supervised(self, server, mock_s3):
        """
        preprocess_supervisedツールの実行テスト
        """
        result = server.call_tool(
            "data_preparation.preprocess_supervised",
            {
                "s3_uri": "s3://test-bucket/data.csv",
                "target_column": "target",
                "file_format": "csv",
                "test_size": 0.2,
            },
        )

        # 実行結果の確認
        assert result["success"] is True
        assert "result" in result

        # 前処理結果の確認
        tool_result = result["result"]
        assert tool_result["status"] == "success"
        assert "preprocessing_results" in tool_result

        preprocess_info = tool_result["preprocessing_results"]
        assert preprocess_info["target_column"] == "target"
        assert preprocess_info["num_samples"] == 5

    def test_call_nonexistent_tool(self, server):
        """
        存在しないツールの呼び出しエラーテスト
        """
        with pytest.raises(ValueError, match="Tool not found"):
            server.call_tool("nonexistent.tool", {})

    def test_call_tool_with_invalid_arguments(self, server, mock_s3):
        """
        無効な引数でのツール呼び出しエラーテスト
        """
        result = server.call_tool(
            "data_preparation.load_dataset",
            {"s3_uri": "invalid://not-s3-uri"},  # 無効なURI
        )

        # エラーが適切に処理されることを確認
        assert result["success"] is False
        assert "error" in result
        assert "Invalid S3 URI" in result["error"]


class TestEndToEndWorkflow:
    """
    エンドツーエンドワークフローのテスト
    """

    @pytest.fixture
    def server(self):
        """テスト用サーバーインスタンス"""
        return MLOpsServer()

    @pytest.fixture
    def sample_workflow_data(self):
        """ワークフロー用テストデータ"""
        return pd.DataFrame(
            {
                "numeric_feature": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
                "categorical_feature": [
                    "A",
                    "B",
                    "A",
                    "B",
                    "A",
                    "B",
                    "A",
                    "B",
                    "A",
                    "B",
                ],
                "target": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
            }
        )

    @pytest.fixture
    def mock_s3_workflow(self, sample_workflow_data):
        """ワークフロー用モックS3"""
        with patch("boto3.client") as mock_client:
            csv_buffer = io.StringIO()
            sample_workflow_data.to_csv(csv_buffer, index=False)
            csv_bytes = csv_buffer.getvalue().encode("utf-8")

            mock_s3_instance = Mock()
            # 複数回の呼び出しに対応するため、side_effectを使用
            mock_s3_instance.get_object.side_effect = lambda **kwargs: {
                "Body": io.BytesIO(csv_bytes),
            }
            mock_s3_instance.put_object.return_value = {}
            mock_client.return_value = mock_s3_instance

            yield mock_s3_instance

    def test_data_preparation_workflow(self, server, mock_s3_workflow):
        """
        Data Preparationワークフロー全体のテスト
        load_dataset → validate_data → preprocess_supervised
        """
        s3_uri = "s3://test-bucket/workflow-data.csv"

        # Step 1: データ読み込み
        load_result = server.call_tool(
            "data_preparation.load_dataset",
            {"s3_uri": s3_uri, "file_format": "csv"},
        )

        assert load_result["success"] is True
        dataset_info = load_result["result"]["dataset_info"]
        assert dataset_info["rows"] == 10
        assert dataset_info["columns"] == 3

        # Step 2: データバリデーション
        validate_result = server.call_tool(
            "data_preparation.validate_data",
            {
                "s3_uri": s3_uri,
                "file_format": "csv",
                "required_columns": ["numeric_feature", "categorical_feature", "target"],
            },
        )

        assert validate_result["success"] is True
        validation_info = validate_result["result"]["validation_results"]
        assert validation_info["is_valid"] is True
        assert len(validation_info["errors"]) == 0

        # Step 3: データ前処理
        preprocess_result = server.call_tool(
            "data_preparation.preprocess_supervised",
            {
                "s3_uri": s3_uri,
                "target_column": "target",
                "file_format": "csv",
                "test_size": 0.2,
                "normalize": True,
                "encode_categorical": True,
            },
        )

        assert preprocess_result["success"] is True
        preprocess_info = preprocess_result["result"]["preprocessing_results"]
        assert preprocess_info["num_features"] == 2
        assert preprocess_info["train_samples"] == 8
        assert preprocess_info["test_samples"] == 2
        assert "categorical_feature" in preprocess_info["categorical_columns"]

    def test_workflow_with_validation_failure(self, server):
        """
        バリデーション失敗時のワークフローテスト
        """
        # 空データでバリデーション失敗をシミュレート
        empty_df = pd.DataFrame({"feature1": [], "target": []})

        with patch("boto3.client") as mock_client:
            csv_buffer = io.StringIO()
            empty_df.to_csv(csv_buffer, index=False)
            csv_bytes = csv_buffer.getvalue().encode("utf-8")

            mock_s3_instance = Mock()
            mock_s3_instance.get_object.return_value = {
                "Body": io.BytesIO(csv_bytes),
            }
            mock_client.return_value = mock_s3_instance

            # バリデーション実行
            validate_result = server.call_tool(
                "data_preparation.validate_data",
                {"s3_uri": "s3://test-bucket/empty.csv", "file_format": "csv"},
            )

            # バリデーション失敗を確認
            assert validate_result["success"] is True
            validation_info = validate_result["result"]["validation_results"]
            assert validation_info["is_valid"] is False
            assert len(validation_info["errors"]) > 0


class TestServerCapabilities:
    """
    サーバーのCapability管理テスト
    """

    def test_capabilities_registration(self):
        """
        Capability登録の確認テスト
        """
        server = MLOpsServer()

        # Data Preparation Capabilityが登録されている
        assert "data_preparation" in server.capabilities

        # Capabilityインスタンスの確認
        data_prep_cap = server.capabilities["data_preparation"]
        assert data_prep_cap is not None
        assert hasattr(data_prep_cap, "get_tools")

    def test_capability_tools_mapping(self):
        """
        CapabilityとToolsのマッピング確認テスト
        """
        server = MLOpsServer()

        # Data Preparation Capabilityから直接ツールを取得
        data_prep_cap = server.capabilities["data_preparation"]
        capability_tools = data_prep_cap.get_tools()

        # Capabilityのツールがサーバーに登録されていることを確認
        for tool_name in capability_tools.keys():
            full_tool_name = f"data_preparation.{tool_name}"
            assert full_tool_name in server.tools

    def test_server_extensibility(self):
        """
        サーバーの拡張性テスト（将来のCapability追加を想定）
        """
        server = MLOpsServer()

        # 現在はData Preparationのみ
        assert len(server.capabilities) == 1

        # toolsには3つのツールが登録されている
        assert len(server.tools) == 3

        # 将来的に他のCapabilityが追加されることを想定
        # （このテストは構造の確認のみ）
        assert isinstance(server.capabilities, dict)
        assert isinstance(server.tools, dict)
