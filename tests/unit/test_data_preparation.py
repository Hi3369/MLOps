"""
Data Preparation Capability Unit Tests

Data Preparation toolsのユニットテスト
"""

import io
import os
import sys
from unittest.mock import Mock, patch

import pandas as pd
import pytest

# Add mcp_server to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "mcp_server"))

from capabilities.data_preparation.tools.load_dataset import load_dataset
from capabilities.data_preparation.tools.preprocess_supervised import preprocess_supervised
from capabilities.data_preparation.tools.validate_data import validate_data


class TestLoadDataset:
    """
    load_dataset関数のユニットテスト
    """

    @pytest.fixture
    def sample_csv_data(self):
        """テスト用CSVデータ"""
        return pd.DataFrame(
            {
                "feature1": [1, 2, 3, 4, 5],
                "feature2": [10.0, 20.0, 30.0, None, 50.0],
                "feature3": ["a", "b", "c", "d", "e"],
                "target": [0, 1, 0, 1, 0],
            }
        )

    @pytest.fixture
    def mock_s3_client(self, sample_csv_data):
        """モックS3クライアント"""
        with patch("boto3.client") as mock_client:
            # CSVデータをバイト列に変換
            csv_buffer = io.StringIO()
            sample_csv_data.to_csv(csv_buffer, index=False)
            csv_bytes = csv_buffer.getvalue().encode("utf-8")

            # S3レスポンスをモック
            mock_s3 = Mock()
            mock_s3.get_object.return_value = {
                "Body": io.BytesIO(csv_bytes),
            }
            mock_client.return_value = mock_s3

            yield mock_s3

    def test_load_dataset_csv_success(self, mock_s3_client, sample_csv_data):
        """
        CSVファイルの正常読み込みテスト
        """
        result = load_dataset(s3_uri="s3://test-bucket/data.csv", file_format="csv")

        # ステータス確認
        assert result["status"] == "success"
        assert result["s3_uri"] == "s3://test-bucket/data.csv"
        assert result["bucket"] == "test-bucket"
        assert result["key"] == "data.csv"
        assert result["file_format"] == "csv"

        # データセット情報確認
        dataset_info = result["dataset_info"]
        assert dataset_info["rows"] == 5
        assert dataset_info["columns"] == 4
        assert set(dataset_info["column_names"]) == {
            "feature1",
            "feature2",
            "feature3",
            "target",
        }

        # 欠損値確認
        assert dataset_info["missing_values"]["feature2"] == 1
        assert dataset_info["missing_values"]["feature1"] == 0

        # S3が正しく呼ばれたか確認
        mock_s3_client.get_object.assert_called_once_with(Bucket="test-bucket", Key="data.csv")

    def test_load_dataset_invalid_s3_uri(self):
        """
        無効なS3 URIのエラーハンドリングテスト
        """
        with pytest.raises(ValueError, match="Invalid S3 URI"):
            load_dataset(s3_uri="invalid://bucket/data.csv")

        with pytest.raises(ValueError, match="Invalid S3 URI format"):
            load_dataset(s3_uri="s3://bucket-only")

    def test_load_dataset_unsupported_format(self, mock_s3_client):
        """
        未サポートファイルフォーマットのエラーハンドリングテスト
        """
        with pytest.raises(ValueError, match="Unsupported file format"):
            load_dataset(s3_uri="s3://test-bucket/data.txt", file_format="unsupported")


class TestValidateData:
    """
    validate_data関数のユニットテスト
    """

    @pytest.fixture
    def sample_data_with_issues(self):
        """問題のあるテスト用データ"""
        return pd.DataFrame(
            {
                "feature1": [1, 2, None, 4, None, 6, 7, 8, 9, 10],  # 20% missing
                "feature2": [None] * 10,  # 100% missing
                "feature3": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"],
                "target": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
            }
        )

    @pytest.fixture
    def mock_s3_for_validation(self, sample_data_with_issues):
        """バリデーション用モックS3クライアント"""
        with patch("boto3.client") as mock_client:
            csv_buffer = io.StringIO()
            sample_data_with_issues.to_csv(csv_buffer, index=False)
            csv_bytes = csv_buffer.getvalue().encode("utf-8")

            mock_s3 = Mock()
            mock_s3.get_object.return_value = {
                "Body": io.BytesIO(csv_bytes),
            }
            mock_client.return_value = mock_s3

            yield mock_s3

    def test_validate_data_with_warnings(self, mock_s3_for_validation):
        """
        欠損値警告のテスト
        """
        result = validate_data(
            s3_uri="s3://test-bucket/data.csv",
            file_format="csv",
            max_missing_ratio=0.5,
        )

        assert result["status"] == "success"
        validation_results = result["validation_results"]

        # feature2は100%欠損なので警告が出る
        assert len(validation_results["warnings"]) > 0
        assert "feature2" in str(validation_results["warnings"])

        # 欠損値チェック結果確認
        high_missing = validation_results["checks"]["missing_values"]["high_missing_columns"]
        assert "feature2" in high_missing
        assert high_missing["feature2"]["ratio"] == 1.0

    def test_validate_data_missing_required_columns(self, mock_s3_for_validation):
        """
        必須カラム不足のエラーテスト
        """
        result = validate_data(
            s3_uri="s3://test-bucket/data.csv",
            file_format="csv",
            required_columns=["feature1", "feature2", "missing_column"],
        )

        validation_results = result["validation_results"]
        assert validation_results["is_valid"] is False
        assert len(validation_results["errors"]) > 0
        assert "missing_column" in str(validation_results["errors"])

    def test_validate_data_empty_dataset(self):
        """
        空データセット（0行）のエラーテスト
        """
        # 列はあるが行がないデータフレーム
        empty_df = pd.DataFrame({"feature1": [], "target": []})

        with patch("boto3.client") as mock_client:
            csv_buffer = io.StringIO()
            empty_df.to_csv(csv_buffer, index=False)
            csv_bytes = csv_buffer.getvalue().encode("utf-8")

            mock_s3 = Mock()
            mock_s3.get_object.return_value = {
                "Body": io.BytesIO(csv_bytes),
            }
            mock_client.return_value = mock_s3

            result = validate_data(s3_uri="s3://test-bucket/empty.csv")

            validation_results = result["validation_results"]
            assert validation_results["is_valid"] is False
            assert any("empty" in str(e).lower() for e in validation_results["errors"])


class TestPreprocessSupervised:
    """
    preprocess_supervised関数のユニットテスト
    """

    @pytest.fixture
    def sample_training_data(self):
        """学習用テストデータ"""
        return pd.DataFrame(
            {
                "numeric_feature": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
                "categorical_feature": ["A", "B", "A", "B", "A", "B", "A", "B", "A", "B"],
                "target": [
                    "class1",
                    "class2",
                    "class1",
                    "class2",
                    "class1",
                    "class2",
                    "class1",
                    "class2",
                    "class1",
                    "class2",
                ],
            }
        )

    @pytest.fixture
    def mock_s3_for_preprocessing(self, sample_training_data):
        """前処理用モックS3クライアント"""
        with patch("boto3.client") as mock_client:
            csv_buffer = io.StringIO()
            sample_training_data.to_csv(csv_buffer, index=False)
            csv_bytes = csv_buffer.getvalue().encode("utf-8")

            mock_s3 = Mock()
            mock_s3.get_object.return_value = {
                "Body": io.BytesIO(csv_bytes),
            }
            mock_s3.put_object.return_value = {}
            mock_client.return_value = mock_s3

            yield mock_s3

    def test_preprocess_supervised_basic(self, mock_s3_for_preprocessing):
        """
        基本的な前処理パイプラインのテスト
        """
        result = preprocess_supervised(
            s3_uri="s3://test-bucket/train.csv",
            target_column="target",
            file_format="csv",
            test_size=0.2,
            normalize=True,
            encode_categorical=True,
            output_s3_uri="s3://test-bucket/processed/",
        )

        assert result["status"] == "success"
        preprocessing_results = result["preprocessing_results"]

        # 特徴量確認
        assert preprocessing_results["num_features"] == 2
        assert "numeric_feature" in preprocessing_results["feature_names"]
        assert "categorical_feature" in preprocessing_results["feature_names"]

        # サンプル数確認
        assert preprocessing_results["num_samples"] == 10
        assert preprocessing_results["train_samples"] == 8
        assert preprocessing_results["test_samples"] == 2

        # カテゴリ変数エンコーディング確認
        assert "categorical_feature" in preprocessing_results["categorical_columns"]

        # ターゲットエンコーディング確認
        assert preprocessing_results["target_classes"] is not None
        assert len(preprocessing_results["target_classes"]) == 2

        # S3への保存確認
        assert mock_s3_for_preprocessing.put_object.call_count == 2  # train + test

    def test_preprocess_supervised_missing_target_column(self, mock_s3_for_preprocessing):
        """
        ターゲットカラム不在のエラーテスト
        """
        with pytest.raises(ValueError, match="Target column.*not found"):
            preprocess_supervised(
                s3_uri="s3://test-bucket/train.csv",
                target_column="nonexistent_target",
                file_format="csv",
            )

    def test_preprocess_supervised_with_missing_values(self):
        """
        欠損値処理のテスト
        """
        data_with_missing = pd.DataFrame(
            {
                "feature1": [1.0, 2.0, None, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
                "feature2": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0],
                "target": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
            }
        )

        with patch("boto3.client") as mock_client:
            csv_buffer = io.StringIO()
            data_with_missing.to_csv(csv_buffer, index=False)
            csv_bytes = csv_buffer.getvalue().encode("utf-8")

            mock_s3 = Mock()
            mock_s3.get_object.return_value = {
                "Body": io.BytesIO(csv_bytes),
            }
            mock_s3.put_object.return_value = {}
            mock_client.return_value = mock_s3

            # dropモードでテスト
            result = preprocess_supervised(
                s3_uri="s3://test-bucket/train.csv",
                target_column="target",
                handle_missing="drop",
            )

            preprocessing_results = result["preprocessing_results"]
            # 欠損値を含む行が削除されるので、9サンプルになる
            assert preprocessing_results["num_samples"] == 9

    def test_preprocess_supervised_no_normalization(self, mock_s3_for_preprocessing):
        """
        正規化なしの前処理テスト
        """
        result = preprocess_supervised(
            s3_uri="s3://test-bucket/train.csv",
            target_column="target",
            normalize=False,
        )

        preprocessing_results = result["preprocessing_results"]
        assert preprocessing_results["normalized"] is False
