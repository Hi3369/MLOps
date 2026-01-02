"""
ML Evaluation Capability Unit Tests

ML Evaluation toolsのユニットテスト
"""

import io
import os
import sys
from unittest.mock import Mock, patch

import pandas as pd
import pytest
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

# Add mcp_server to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "mcp_server"))

from capabilities.ml_evaluation.tools.evaluate_classification import evaluate_classification
from capabilities.ml_evaluation.tools.evaluate_clustering import evaluate_clustering
from capabilities.ml_evaluation.tools.evaluate_regression import evaluate_regression


class TestEvaluateClassification:
    """
    evaluate_classification関数のユニットテスト
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
    def trained_classification_model(self, sample_classification_data):
        """学習済み分類モデル"""
        X = sample_classification_data.iloc[:, :-1]
        y = sample_classification_data.iloc[:, -1]
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X, y)
        return model

    @pytest.fixture
    def mock_s3_classification(self, sample_classification_data, trained_classification_model):
        """分類用モックS3クライアント"""
        import joblib

        with patch("boto3.client") as mock_client:
            # モデルデータ
            model_buffer = io.BytesIO()
            joblib.dump(trained_classification_model, model_buffer)
            model_buffer.seek(0)

            # テストデータ
            csv_buffer = io.StringIO()
            sample_classification_data.to_csv(csv_buffer, index=False)
            csv_bytes = csv_buffer.getvalue().encode("utf-8")

            mock_s3 = Mock()

            def get_object_side_effect(Bucket, Key):
                if "model.pkl" in Key:
                    return {"Body": io.BytesIO(model_buffer.getvalue())}
                else:
                    return {"Body": io.BytesIO(csv_bytes)}

            mock_s3.get_object.side_effect = get_object_side_effect
            mock_client.return_value = mock_s3

            yield mock_s3

    def test_evaluate_classification_success(self, mock_s3_classification):
        """
        分類モデル評価の成功テスト
        """
        result = evaluate_classification(
            model_s3_uri="s3://test-bucket/model.pkl",
            test_data_s3_uri="s3://test-bucket/test.csv",
            file_format="csv",
            average="weighted",
        )

        # 実行結果の確認
        assert result["status"] == "success"
        assert "evaluation_results" in result

        # 評価結果の確認
        eval_results = result["evaluation_results"]
        assert "accuracy" in eval_results
        assert "precision" in eval_results
        assert "recall" in eval_results
        assert "f1_score" in eval_results
        assert "confusion_matrix" in eval_results
        assert "classification_report" in eval_results
        assert eval_results["n_samples"] == 10
        assert eval_results["n_features"] == 2

    def test_evaluate_classification_invalid_model_uri(self):
        """
        無効なモデルS3 URIのエラーハンドリングテスト
        """
        with pytest.raises(ValueError, match="Invalid S3 URI"):
            evaluate_classification(
                model_s3_uri="invalid://bucket/model.pkl",
                test_data_s3_uri="s3://test-bucket/test.csv",
            )

    def test_evaluate_classification_invalid_data_uri(self):
        """
        無効なデータS3 URIのエラーハンドリングテスト
        """
        with pytest.raises(ValueError, match="Invalid S3 URI"):
            evaluate_classification(
                model_s3_uri="s3://test-bucket/model.pkl",
                test_data_s3_uri="invalid://bucket/test.csv",
            )


class TestEvaluateRegression:
    """
    evaluate_regression関数のユニットテスト
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
    def trained_regression_model(self, sample_regression_data):
        """学習済み回帰モデル"""
        X = sample_regression_data.iloc[:, :-1]
        y = sample_regression_data.iloc[:, -1]
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        model.fit(X, y)
        return model

    @pytest.fixture
    def mock_s3_regression(self, sample_regression_data, trained_regression_model):
        """回帰用モックS3クライアント"""
        import joblib

        with patch("boto3.client") as mock_client:
            # モデルデータ
            model_buffer = io.BytesIO()
            joblib.dump(trained_regression_model, model_buffer)
            model_buffer.seek(0)

            # テストデータ
            csv_buffer = io.StringIO()
            sample_regression_data.to_csv(csv_buffer, index=False)
            csv_bytes = csv_buffer.getvalue().encode("utf-8")

            mock_s3 = Mock()

            def get_object_side_effect(Bucket, Key):
                if "model.pkl" in Key:
                    return {"Body": io.BytesIO(model_buffer.getvalue())}
                else:
                    return {"Body": io.BytesIO(csv_bytes)}

            mock_s3.get_object.side_effect = get_object_side_effect
            mock_client.return_value = mock_s3

            yield mock_s3

    def test_evaluate_regression_success(self, mock_s3_regression):
        """
        回帰モデル評価の成功テスト
        """
        result = evaluate_regression(
            model_s3_uri="s3://test-bucket/model.pkl",
            test_data_s3_uri="s3://test-bucket/test.csv",
            file_format="csv",
        )

        # 実行結果の確認
        assert result["status"] == "success"
        assert "evaluation_results" in result

        # 評価結果の確認
        eval_results = result["evaluation_results"]
        assert "r2_score" in eval_results
        assert "mae" in eval_results
        assert "mse" in eval_results
        assert "rmse" in eval_results
        assert eval_results["n_samples"] == 10
        assert eval_results["n_features"] == 2

    def test_evaluate_regression_invalid_format(self, mock_s3_regression):
        """
        未サポートフォーマットのエラーハンドリングテスト
        """
        with pytest.raises(ValueError, match="Unsupported file format"):
            evaluate_regression(
                model_s3_uri="s3://test-bucket/model.pkl",
                test_data_s3_uri="s3://test-bucket/test.csv",
                file_format="json",
            )


class TestEvaluateClustering:
    """
    evaluate_clustering関数のユニットテスト
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
    def trained_clustering_model(self, sample_clustering_data):
        """学習済みクラスタリングモデル"""
        model = KMeans(n_clusters=2, random_state=42, n_init=10)
        model.fit(sample_clustering_data)
        return model

    @pytest.fixture
    def mock_s3_clustering(self, sample_clustering_data, trained_clustering_model):
        """クラスタリング用モックS3クライアント"""
        import joblib

        with patch("boto3.client") as mock_client:
            # モデルデータ
            model_buffer = io.BytesIO()
            joblib.dump(trained_clustering_model, model_buffer)
            model_buffer.seek(0)

            # テストデータ
            csv_buffer = io.StringIO()
            sample_clustering_data.to_csv(csv_buffer, index=False)
            csv_bytes = csv_buffer.getvalue().encode("utf-8")

            mock_s3 = Mock()

            def get_object_side_effect(Bucket, Key):
                if "model.pkl" in Key:
                    return {"Body": io.BytesIO(model_buffer.getvalue())}
                else:
                    return {"Body": io.BytesIO(csv_bytes)}

            mock_s3.get_object.side_effect = get_object_side_effect
            mock_client.return_value = mock_s3

            yield mock_s3

    def test_evaluate_clustering_success(self, mock_s3_clustering):
        """
        クラスタリングモデル評価の成功テスト
        """
        result = evaluate_clustering(
            model_s3_uri="s3://test-bucket/model.pkl",
            test_data_s3_uri="s3://test-bucket/test.csv",
            file_format="csv",
        )

        # 実行結果の確認
        assert result["status"] == "success"
        assert "evaluation_results" in result

        # 評価結果の確認
        eval_results = result["evaluation_results"]
        assert "n_clusters" in eval_results
        assert "silhouette_score" in eval_results
        assert "davies_bouldin_score" in eval_results
        assert "cluster_distribution" in eval_results
        assert eval_results["n_samples"] == 10
        assert eval_results["n_features"] == 2
        assert eval_results["n_clusters"] == 2

    def test_evaluate_clustering_invalid_uri(self):
        """
        無効なS3 URIのエラーハンドリングテスト
        """
        with pytest.raises(ValueError, match="Invalid S3 URI"):
            evaluate_clustering(
                model_s3_uri="invalid://bucket/model.pkl",
                test_data_s3_uri="s3://test-bucket/test.csv",
            )
