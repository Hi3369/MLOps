"""
ML Training Capability Unit Tests

ML Training toolsのユニットテスト
"""

import io
import os
import sys
from unittest.mock import Mock, patch

import pandas as pd
import pytest

# Add mcp_server to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "mcp_server"))

from capabilities.ml_training.tools.train_classification import train_classification
from capabilities.ml_training.tools.train_clustering import train_clustering
from capabilities.ml_training.tools.train_regression import train_regression


class TestTrainClassification:
    """
    train_classification関数のユニットテスト
    """

    @pytest.fixture
    def sample_classification_data(self):
        """分類用テストデータ"""
        return pd.DataFrame(
            {
                "feature1": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
                "feature2": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0],
                "target": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
            }
        )

    @pytest.fixture
    def mock_s3_classification(self, sample_classification_data):
        """分類用モックS3クライアント"""
        with patch("boto3.client") as mock_client:
            csv_buffer = io.StringIO()
            sample_classification_data.to_csv(csv_buffer, index=False)
            csv_bytes = csv_buffer.getvalue().encode("utf-8")

            mock_s3 = Mock()
            mock_s3.get_object.return_value = {
                "Body": io.BytesIO(csv_bytes),
            }
            mock_s3.put_object.return_value = {}
            mock_client.return_value = mock_s3

            yield mock_s3

    def test_train_classification_random_forest(self, mock_s3_classification):
        """
        Random Forestによる分類モデル学習テスト
        """
        result = train_classification(
            train_data_s3_uri="s3://test-bucket/train.csv",
            algorithm="random_forest",
            hyperparameters={"n_estimators": 10},
            model_output_s3_uri="s3://test-bucket/model.pkl",
            file_format="csv",
        )

        # 実行結果の確認
        assert result["status"] == "success"
        assert "training_results" in result

        # 学習結果の確認
        training_results = result["training_results"]
        assert training_results["algorithm"] == "random_forest"
        assert training_results["n_samples"] == 10
        assert training_results["n_features"] == 2
        assert "train_accuracy" in training_results
        assert training_results["n_classes"] == 2

        # S3への保存確認
        assert mock_s3_classification.put_object.call_count == 2  # model + metadata

    def test_train_classification_logistic_regression(self, mock_s3_classification):
        """
        Logistic Regressionによる分類モデル学習テスト
        """
        result = train_classification(
            train_data_s3_uri="s3://test-bucket/train.csv",
            algorithm="logistic_regression",
            model_output_s3_uri="s3://test-bucket/model.pkl",
        )

        assert result["status"] == "success"
        assert result["training_results"]["algorithm"] == "logistic_regression"

    def test_train_classification_invalid_s3_uri(self):
        """
        無効なS3 URIのエラーハンドリングテスト
        """
        with pytest.raises(ValueError, match="Invalid S3 URI"):
            train_classification(
                train_data_s3_uri="invalid://bucket/data.csv",
                model_output_s3_uri="s3://test-bucket/model.pkl",
            )

    def test_train_classification_unsupported_algorithm(self, mock_s3_classification):
        """
        未サポートアルゴリズムのエラーハンドリングテスト
        """
        with pytest.raises(ValueError, match="Unsupported algorithm"):
            train_classification(
                train_data_s3_uri="s3://test-bucket/train.csv",
                algorithm="unsupported_algo",
                model_output_s3_uri="s3://test-bucket/model.pkl",
            )


class TestTrainRegression:
    """
    train_regression関数のユニットテスト
    """

    @pytest.fixture
    def sample_regression_data(self):
        """回帰用テストデータ"""
        return pd.DataFrame(
            {
                "feature1": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
                "feature2": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0],
                "target": [
                    11.0,
                    22.0,
                    33.0,
                    44.0,
                    55.0,
                    66.0,
                    77.0,
                    88.0,
                    99.0,
                    110.0,
                ],
            }
        )

    @pytest.fixture
    def mock_s3_regression(self, sample_regression_data):
        """回帰用モックS3クライアント"""
        with patch("boto3.client") as mock_client:
            csv_buffer = io.StringIO()
            sample_regression_data.to_csv(csv_buffer, index=False)
            csv_bytes = csv_buffer.getvalue().encode("utf-8")

            mock_s3 = Mock()
            mock_s3.get_object.return_value = {
                "Body": io.BytesIO(csv_bytes),
            }
            mock_s3.put_object.return_value = {}
            mock_client.return_value = mock_s3

            yield mock_s3

    def test_train_regression_random_forest(self, mock_s3_regression):
        """
        Random Forestによる回帰モデル学習テスト
        """
        result = train_regression(
            train_data_s3_uri="s3://test-bucket/train.csv",
            algorithm="random_forest",
            hyperparameters={"n_estimators": 10},
            model_output_s3_uri="s3://test-bucket/model.pkl",
            file_format="csv",
        )

        # 実行結果の確認
        assert result["status"] == "success"
        assert "training_results" in result

        # 学習結果の確認
        training_results = result["training_results"]
        assert training_results["algorithm"] == "random_forest"
        assert training_results["n_samples"] == 10
        assert training_results["n_features"] == 2
        assert "train_r2_score" in training_results

        # S3への保存確認
        assert mock_s3_regression.put_object.call_count == 2  # model + metadata

    def test_train_regression_linear(self, mock_s3_regression):
        """
        Linear Regressionによる回帰モデル学習テスト
        """
        result = train_regression(
            train_data_s3_uri="s3://test-bucket/train.csv",
            algorithm="linear_regression",
            model_output_s3_uri="s3://test-bucket/model.pkl",
        )

        assert result["status"] == "success"
        assert result["training_results"]["algorithm"] == "linear_regression"

    def test_train_regression_ridge(self, mock_s3_regression):
        """
        Ridge Regressionによる回帰モデル学習テスト
        """
        result = train_regression(
            train_data_s3_uri="s3://test-bucket/train.csv",
            algorithm="ridge",
            hyperparameters={"alpha": 0.5},
            model_output_s3_uri="s3://test-bucket/model.pkl",
        )

        assert result["status"] == "success"
        assert result["training_results"]["algorithm"] == "ridge"


class TestTrainClassificationExtended:
    """train_classification の拡張テスト（カバレッジ向上）"""

    @pytest.fixture
    def sample_data(self):
        """分類用テストデータ"""
        return pd.DataFrame(
            {
                "f1": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
                "f2": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0],
                "target": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
            }
        )

    @pytest.fixture
    def mock_s3(self, sample_data):
        """モックS3"""
        with patch("boto3.client") as mock_client:
            csv_buffer = io.StringIO()
            sample_data.to_csv(csv_buffer, index=False)
            csv_bytes = csv_buffer.getvalue().encode("utf-8")

            mock_s3 = Mock()
            mock_s3.get_object.return_value = {"Body": io.BytesIO(csv_bytes)}
            mock_s3.put_object.return_value = {}
            mock_client.return_value = mock_s3
            yield mock_s3

    def test_neural_network_classification(self, mock_s3):
        """MLP分類テスト"""
        result = train_classification(
            train_data_s3_uri="s3://test-bucket/train.csv",
            algorithm="neural_network",
            hyperparameters={"hidden_layer_sizes": (10,), "max_iter": 500},
        )

        assert result["status"] == "success"
        assert result["training_results"]["algorithm"] == "neural_network"

    def test_classification_without_model_output(self, mock_s3):
        """モデル保存なしの分類テスト"""
        result = train_classification(
            train_data_s3_uri="s3://test-bucket/train.csv",
            algorithm="random_forest",
            hyperparameters={"n_estimators": 10},
        )

        assert result["status"] == "success"
        assert result["training_results"]["model_s3_uri"] is None
        assert mock_s3.put_object.call_count == 0

    def test_classification_s3_uri_without_key(self):
        """S3 URIにキーがない場合のエラーテスト"""
        with pytest.raises(ValueError, match="Invalid S3 URI format"):
            train_classification(train_data_s3_uri="s3://bucket-only")

    def test_classification_unsupported_file_format(self):
        """未対応ファイルフォーマットのエラーテスト"""
        with patch("boto3.client") as mock_client:
            mock_s3 = Mock()
            mock_s3.get_object.return_value = {"Body": io.BytesIO(b"data")}
            mock_client.return_value = mock_s3

            with pytest.raises(ValueError, match="Unsupported file format"):
                train_classification(
                    train_data_s3_uri="s3://bucket/data.json",
                    file_format="json",
                )

    def test_classification_custom_hyperparameters(self, mock_s3):
        """カスタムハイパーパラメータのテスト"""
        result = train_classification(
            train_data_s3_uri="s3://test-bucket/train.csv",
            algorithm="random_forest",
            hyperparameters={
                "n_estimators": 50,
                "max_depth": 5,
                "min_samples_split": 3,
                "min_samples_leaf": 2,
                "random_state": 0,
            },
        )

        assert result["status"] == "success"
        assert result["training_results"]["hyperparameters"]["n_estimators"] == 50

    def test_classification_has_class_info(self, mock_s3):
        """分類結果にクラス情報が含まれるテスト"""
        result = train_classification(
            train_data_s3_uri="s3://test-bucket/train.csv",
            algorithm="random_forest",
            hyperparameters={"n_estimators": 10},
        )

        training_results = result["training_results"]
        assert "n_classes" in training_results
        assert "classes" in training_results
        assert training_results["n_classes"] == 2

    def test_classification_feature_names(self, mock_s3):
        """特徴量名が含まれるテスト"""
        result = train_classification(
            train_data_s3_uri="s3://test-bucket/train.csv",
            algorithm="logistic_regression",
        )

        assert "feature_names" in result["training_results"]
        assert "f1" in result["training_results"]["feature_names"]
        assert "f2" in result["training_results"]["feature_names"]

    def test_classification_s3_error(self):
        """S3アクセスエラーのテスト"""
        with patch("boto3.client") as mock_client:
            from botocore.exceptions import ClientError

            mock_s3 = Mock()
            mock_s3.get_object.side_effect = ClientError(
                {"Error": {"Code": "NoSuchBucket", "Message": "Not found"}},
                "GetObject",
            )
            mock_client.return_value = mock_s3

            with pytest.raises(ValueError, match="Failed to load data from S3"):
                train_classification(
                    train_data_s3_uri="s3://nonexistent/data.csv",
                )


class TestTrainRegressionExtended:
    """train_regression の拡張テスト（カバレッジ向上）"""

    @pytest.fixture
    def sample_data(self):
        """回帰用テストデータ"""
        return pd.DataFrame(
            {
                "f1": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
                "f2": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0],
                "target": [11.0, 22.0, 33.0, 44.0, 55.0, 66.0, 77.0, 88.0, 99.0, 110.0],
            }
        )

    @pytest.fixture
    def mock_s3(self, sample_data):
        """モックS3"""
        with patch("boto3.client") as mock_client:
            csv_buffer = io.StringIO()
            sample_data.to_csv(csv_buffer, index=False)
            csv_bytes = csv_buffer.getvalue().encode("utf-8")

            mock_s3 = Mock()
            mock_s3.get_object.return_value = {"Body": io.BytesIO(csv_bytes)}
            mock_s3.put_object.return_value = {}
            mock_client.return_value = mock_s3
            yield mock_s3

    def test_neural_network_regression(self, mock_s3):
        """MLP回帰テスト"""
        result = train_regression(
            train_data_s3_uri="s3://test-bucket/train.csv",
            algorithm="neural_network",
            hyperparameters={"hidden_layer_sizes": (10,), "max_iter": 500},
        )

        assert result["status"] == "success"
        assert result["training_results"]["algorithm"] == "neural_network"

    def test_regression_unsupported_algorithm(self, mock_s3):
        """未サポートアルゴリズムのエラーテスト"""
        with pytest.raises(ValueError, match="Unsupported algorithm"):
            train_regression(
                train_data_s3_uri="s3://test-bucket/train.csv",
                algorithm="unsupported",
            )

    def test_regression_invalid_s3_uri(self):
        """無効なS3 URIのエラーテスト"""
        with pytest.raises(ValueError, match="Invalid S3 URI"):
            train_regression(train_data_s3_uri="invalid://bucket/data")

    def test_regression_s3_uri_without_key(self):
        """S3 URIにキーがない場合のエラーテスト"""
        with pytest.raises(ValueError, match="Invalid S3 URI format"):
            train_regression(train_data_s3_uri="s3://bucket-only")

    def test_regression_unsupported_file_format(self):
        """未対応ファイルフォーマットのエラーテスト"""
        with patch("boto3.client") as mock_client:
            mock_s3 = Mock()
            mock_s3.get_object.return_value = {"Body": io.BytesIO(b"data")}
            mock_client.return_value = mock_s3

            with pytest.raises(ValueError, match="Unsupported file format"):
                train_regression(
                    train_data_s3_uri="s3://bucket/data.json",
                    file_format="json",
                )

    def test_regression_without_model_output(self, mock_s3):
        """モデル保存なしの回帰テスト"""
        result = train_regression(
            train_data_s3_uri="s3://test-bucket/train.csv",
            algorithm="linear_regression",
        )

        assert result["status"] == "success"
        assert result["training_results"]["model_s3_uri"] is None
        assert mock_s3.put_object.call_count == 0

    def test_regression_feature_names(self, mock_s3):
        """特徴量名が結果に含まれるテスト"""
        result = train_regression(
            train_data_s3_uri="s3://test-bucket/train.csv",
            algorithm="random_forest",
            hyperparameters={"n_estimators": 10},
        )

        assert "feature_names" in result["training_results"]
        assert "f1" in result["training_results"]["feature_names"]

    def test_regression_s3_error(self):
        """S3アクセスエラーのテスト"""
        with patch("boto3.client") as mock_client:
            from botocore.exceptions import ClientError

            mock_s3 = Mock()
            mock_s3.get_object.side_effect = ClientError(
                {"Error": {"Code": "NoSuchBucket", "Message": "Not found"}},
                "GetObject",
            )
            mock_client.return_value = mock_s3

            with pytest.raises(ValueError, match="Failed to load data from S3"):
                train_regression(train_data_s3_uri="s3://nonexistent/data.csv")

    def test_regression_custom_hyperparameters_ridge(self, mock_s3):
        """Ridgeカスタムハイパーパラメータテスト"""
        result = train_regression(
            train_data_s3_uri="s3://test-bucket/train.csv",
            algorithm="ridge",
            hyperparameters={"alpha": 2.0, "random_state": 0},
        )

        assert result["status"] == "success"
        assert result["training_results"]["hyperparameters"]["alpha"] == 2.0

    def test_regression_model_save_with_pkl_extension(self, mock_s3):
        """.pkl拡張子でのモデル保存テスト"""
        result = train_regression(
            train_data_s3_uri="s3://test-bucket/train.csv",
            algorithm="linear_regression",
            model_output_s3_uri="s3://test-bucket/model.pkl",
        )

        assert result["status"] == "success"
        assert mock_s3.put_object.call_count == 2

    def test_regression_model_save_without_pkl_extension(self, mock_s3):
        """拡張子なしでのモデル保存テスト"""
        result = train_regression(
            train_data_s3_uri="s3://test-bucket/train.csv",
            algorithm="linear_regression",
            model_output_s3_uri="s3://test-bucket/models/my-model",
        )

        assert result["status"] == "success"
        assert mock_s3.put_object.call_count == 2


class TestTrainClustering:
    """
    train_clustering関数のユニットテスト
    """

    @pytest.fixture
    def sample_clustering_data(self):
        """クラスタリング用テストデータ"""
        return pd.DataFrame(
            {
                "feature1": [1.0, 1.5, 2.0, 8.0, 8.5, 9.0, 1.2, 8.2, 1.8, 9.1],
                "feature2": [1.0, 1.5, 2.0, 8.0, 8.5, 9.0, 1.3, 8.3, 1.7, 8.9],
            }
        )

    @pytest.fixture
    def mock_s3_clustering(self, sample_clustering_data):
        """クラスタリング用モックS3クライアント"""
        with patch("boto3.client") as mock_client:
            csv_buffer = io.StringIO()
            sample_clustering_data.to_csv(csv_buffer, index=False)
            csv_bytes = csv_buffer.getvalue().encode("utf-8")

            mock_s3 = Mock()
            mock_s3.get_object.return_value = {
                "Body": io.BytesIO(csv_bytes),
            }
            mock_s3.put_object.return_value = {}
            mock_client.return_value = mock_s3

            yield mock_s3

    def test_train_clustering_kmeans(self, mock_s3_clustering):
        """
        KMeansによるクラスタリングテスト
        """
        result = train_clustering(
            train_data_s3_uri="s3://test-bucket/data.csv",
            algorithm="kmeans",
            hyperparameters={"n_clusters": 2},
            model_output_s3_uri="s3://test-bucket/model.pkl",
            file_format="csv",
        )

        # 実行結果の確認
        assert result["status"] == "success"
        assert "training_results" in result

        # クラスタリング結果の確認
        training_results = result["training_results"]
        assert training_results["algorithm"] == "kmeans"
        assert training_results["n_samples"] == 10
        assert training_results["n_features"] == 2
        assert training_results["n_clusters"] == 2
        assert "cluster_distribution" in training_results

        # S3への保存確認
        assert mock_s3_clustering.put_object.call_count == 2  # model + metadata

    def test_train_clustering_dbscan(self, mock_s3_clustering):
        """
        DBSCANによるクラスタリングテスト
        """
        result = train_clustering(
            train_data_s3_uri="s3://test-bucket/data.csv",
            algorithm="dbscan",
            hyperparameters={"eps": 1.0, "min_samples": 2},
            model_output_s3_uri="s3://test-bucket/model.pkl",
        )

        assert result["status"] == "success"
        assert result["training_results"]["algorithm"] == "dbscan"

    def test_train_clustering_pca(self, mock_s3_clustering):
        """
        PCAによる次元削減テスト
        """
        result = train_clustering(
            train_data_s3_uri="s3://test-bucket/data.csv",
            algorithm="pca",
            hyperparameters={"n_components": 1},
            model_output_s3_uri="s3://test-bucket/model.pkl",
        )

        assert result["status"] == "success"
        assert result["training_results"]["algorithm"] == "pca"
        assert result["training_results"]["n_clusters"] == 1
