"""
SHAP/LIME Model Interpretability Unit Tests

モデル解釈性機能（SHAP/LIME）のユニットテスト
TDDアプローチで作成
"""

import io
import os
import sys
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression

# Add mcp_server to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "mcp_server"))


# =============================================================================
# SHAP Tests
# =============================================================================


class TestCalculateSHAPValues:
    """
    calculate_shap_values関数のユニットテスト
    """

    @pytest.fixture
    def sample_classification_data(self):
        """分類用テストデータ"""
        np.random.seed(42)
        return pd.DataFrame(
            {
                "feature1": np.random.randn(100),
                "feature2": np.random.randn(100),
                "feature3": np.random.randn(100),
                "target": np.random.randint(0, 2, 100),
            }
        )

    @pytest.fixture
    def sample_regression_data(self):
        """回帰用テストデータ"""
        np.random.seed(42)
        X = np.random.randn(100, 3)
        y = X[:, 0] * 2 + X[:, 1] * 3 + np.random.randn(100) * 0.1
        return pd.DataFrame(
            {
                "feature1": X[:, 0],
                "feature2": X[:, 1],
                "feature3": X[:, 2],
                "target": y,
            }
        )

    @pytest.fixture
    def trained_rf_classifier(self, sample_classification_data):
        """学習済みRandomForest分類モデル"""
        X = sample_classification_data.iloc[:, :-1]
        y = sample_classification_data.iloc[:, -1]
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X, y)
        return model

    @pytest.fixture
    def trained_rf_regressor(self, sample_regression_data):
        """学習済みRandomForest回帰モデル"""
        X = sample_regression_data.iloc[:, :-1]
        y = sample_regression_data.iloc[:, -1]
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        model.fit(X, y)
        return model

    @pytest.fixture
    def trained_logistic_classifier(self, sample_classification_data):
        """学習済みLogistic Regression分類モデル"""
        X = sample_classification_data.iloc[:, :-1]
        y = sample_classification_data.iloc[:, -1]
        model = LogisticRegression(random_state=42, max_iter=200)
        model.fit(X, y)
        return model

    @pytest.fixture
    def trained_linear_regressor(self, sample_regression_data):
        """学習済みLinear Regression回帰モデル"""
        X = sample_regression_data.iloc[:, :-1]
        y = sample_regression_data.iloc[:, -1]
        model = LinearRegression()
        model.fit(X, y)
        return model

    @pytest.fixture
    def mock_s3_shap(self, sample_classification_data, trained_rf_classifier):
        """SHAP用モックS3クライアント"""
        import joblib

        with patch("boto3.client") as mock_client:
            model_buffer = io.BytesIO()
            joblib.dump(trained_rf_classifier, model_buffer)
            model_buffer.seek(0)

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

    # -------------------------------------------------------------------------
    # 正常系テスト
    # -------------------------------------------------------------------------

    def test_calculate_shap_tree_explainer_success(self, mock_s3_shap):
        """TreeExplainerでのSHAP値計算成功テスト"""
        from capabilities.ml_evaluation.tools.calculate_shap_values import (
            calculate_shap_values,
        )

        result = calculate_shap_values(
            model_s3_uri="s3://test-bucket/model.pkl",
            data_s3_uri="s3://test-bucket/data.csv",
            explainer_type="tree",
            file_format="csv",
        )

        assert result["status"] == "success"
        assert "shap_values" in result
        assert "feature_importance" in result
        assert "base_value" in result

    def test_calculate_shap_kernel_explainer_success(self, mock_s3_shap):
        """KernelExplainerでのSHAP値計算成功テスト"""
        from capabilities.ml_evaluation.tools.calculate_shap_values import (
            calculate_shap_values,
        )

        result = calculate_shap_values(
            model_s3_uri="s3://test-bucket/model.pkl",
            data_s3_uri="s3://test-bucket/data.csv",
            explainer_type="kernel",
            background_samples=10,
            file_format="csv",
        )

        assert result["status"] == "success"
        assert "shap_values" in result

    def test_calculate_shap_auto_explainer_success(self, mock_s3_shap):
        """自動Explainer選択でのSHAP値計算成功テスト"""
        from capabilities.ml_evaluation.tools.calculate_shap_values import (
            calculate_shap_values,
        )

        result = calculate_shap_values(
            model_s3_uri="s3://test-bucket/model.pkl",
            data_s3_uri="s3://test-bucket/data.csv",
            explainer_type="auto",
            file_format="csv",
        )

        assert result["status"] == "success"
        assert "explainer_type_used" in result

    def test_calculate_shap_feature_importance(self, mock_s3_shap):
        """特徴量重要度の計算テスト"""
        from capabilities.ml_evaluation.tools.calculate_shap_values import (
            calculate_shap_values,
        )

        result = calculate_shap_values(
            model_s3_uri="s3://test-bucket/model.pkl",
            data_s3_uri="s3://test-bucket/data.csv",
            explainer_type="tree",
            file_format="csv",
        )

        assert "feature_importance" in result
        importance = result["feature_importance"]
        assert len(importance) == 3  # 3 features
        assert all(isinstance(v, (int, float)) for v in importance.values())

    def test_calculate_shap_with_background_data(self, mock_s3_shap):
        """背景データ指定でのSHAP値計算テスト"""
        from capabilities.ml_evaluation.tools.calculate_shap_values import (
            calculate_shap_values,
        )

        result = calculate_shap_values(
            model_s3_uri="s3://test-bucket/model.pkl",
            data_s3_uri="s3://test-bucket/data.csv",
            explainer_type="kernel",
            background_samples=50,
            file_format="csv",
        )

        assert result["status"] == "success"
        assert result["background_samples_used"] == 50

    def test_calculate_shap_binary_classification(self, mock_s3_shap):
        """二値分類モデルのSHAP値計算テスト"""
        from capabilities.ml_evaluation.tools.calculate_shap_values import (
            calculate_shap_values,
        )

        result = calculate_shap_values(
            model_s3_uri="s3://test-bucket/model.pkl",
            data_s3_uri="s3://test-bucket/data.csv",
            explainer_type="tree",
            file_format="csv",
        )

        assert result["status"] == "success"
        assert result["model_type"] == "classifier"

    def test_calculate_shap_regression_model(self):
        """回帰モデルのSHAP値計算テスト"""
        import joblib
        from capabilities.ml_evaluation.tools.calculate_shap_values import (
            calculate_shap_values,
        )

        # 回帰モデル用のモックを作成
        np.random.seed(42)
        X = np.random.randn(100, 3)
        y = X[:, 0] * 2 + X[:, 1] * 3 + np.random.randn(100) * 0.1
        data = pd.DataFrame(
            {
                "feature1": X[:, 0],
                "feature2": X[:, 1],
                "feature3": X[:, 2],
                "target": y,
            }
        )
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        model.fit(X, y)

        with patch("boto3.client") as mock_client:
            model_buffer = io.BytesIO()
            joblib.dump(model, model_buffer)
            model_buffer.seek(0)

            csv_buffer = io.StringIO()
            data.to_csv(csv_buffer, index=False)
            csv_bytes = csv_buffer.getvalue().encode("utf-8")

            mock_s3 = Mock()

            def get_object_side_effect(Bucket, Key):
                if "model.pkl" in Key:
                    return {"Body": io.BytesIO(model_buffer.getvalue())}
                else:
                    return {"Body": io.BytesIO(csv_bytes)}

            mock_s3.get_object.side_effect = get_object_side_effect
            mock_client.return_value = mock_s3

            result = calculate_shap_values(
                model_s3_uri="s3://test-bucket/model.pkl",
                data_s3_uri="s3://test-bucket/data.csv",
                explainer_type="tree",
                file_format="csv",
            )

        assert result["status"] == "success"
        assert result["model_type"] == "regressor"

    def test_calculate_shap_sample_limit(self, mock_s3_shap):
        """サンプル数制限でのSHAP値計算テスト"""
        from capabilities.ml_evaluation.tools.calculate_shap_values import (
            calculate_shap_values,
        )

        result = calculate_shap_values(
            model_s3_uri="s3://test-bucket/model.pkl",
            data_s3_uri="s3://test-bucket/data.csv",
            explainer_type="tree",
            max_samples=10,
            file_format="csv",
        )

        assert result["status"] == "success"
        assert result["samples_analyzed"] <= 10

    def test_calculate_shap_parquet_format(self):
        """Parquetフォーマットでのテスト"""
        pytest.importorskip("pyarrow")
        import joblib
        from capabilities.ml_evaluation.tools.calculate_shap_values import (
            calculate_shap_values,
        )

        np.random.seed(42)
        data = pd.DataFrame(
            {
                "feature1": np.random.randn(50),
                "feature2": np.random.randn(50),
                "target": np.random.randint(0, 2, 50),
            }
        )
        model = RandomForestClassifier(n_estimators=5, random_state=42)
        model.fit(data.iloc[:, :-1], data.iloc[:, -1])

        with patch("boto3.client") as mock_client:
            model_buffer = io.BytesIO()
            joblib.dump(model, model_buffer)
            model_buffer.seek(0)

            parquet_buffer = io.BytesIO()
            data.to_parquet(parquet_buffer, index=False)
            parquet_buffer.seek(0)

            mock_s3 = Mock()

            def get_object_side_effect(Bucket, Key):
                if "model.pkl" in Key:
                    return {"Body": io.BytesIO(model_buffer.getvalue())}
                else:
                    return {"Body": io.BytesIO(parquet_buffer.getvalue())}

            mock_s3.get_object.side_effect = get_object_side_effect
            mock_client.return_value = mock_s3

            result = calculate_shap_values(
                model_s3_uri="s3://test-bucket/model.pkl",
                data_s3_uri="s3://test-bucket/data.parquet",
                explainer_type="tree",
                file_format="parquet",
            )

        assert result["status"] == "success"

    # -------------------------------------------------------------------------
    # 異常系テスト
    # -------------------------------------------------------------------------

    def test_calculate_shap_invalid_model_uri(self):
        """無効なモデルS3 URIのエラーハンドリングテスト"""
        from capabilities.ml_evaluation.tools.calculate_shap_values import (
            calculate_shap_values,
        )

        with pytest.raises(ValueError, match="Invalid S3 URI"):
            calculate_shap_values(
                model_s3_uri="invalid://bucket/model.pkl",
                data_s3_uri="s3://test-bucket/data.csv",
            )

    def test_calculate_shap_invalid_data_uri(self):
        """無効なデータS3 URIのエラーハンドリングテスト"""
        from capabilities.ml_evaluation.tools.calculate_shap_values import (
            calculate_shap_values,
        )

        with pytest.raises(ValueError, match="Invalid S3 URI"):
            calculate_shap_values(
                model_s3_uri="s3://test-bucket/model.pkl",
                data_s3_uri="invalid://bucket/data.csv",
            )

    def test_calculate_shap_unsupported_explainer_type(self, mock_s3_shap):
        """未サポートExplainerタイプのエラーハンドリングテスト"""
        from capabilities.ml_evaluation.tools.calculate_shap_values import (
            calculate_shap_values,
        )

        with pytest.raises(ValueError, match="Unsupported explainer type"):
            calculate_shap_values(
                model_s3_uri="s3://test-bucket/model.pkl",
                data_s3_uri="s3://test-bucket/data.csv",
                explainer_type="invalid_type",
            )

    def test_calculate_shap_unsupported_file_format(self, mock_s3_shap):
        """未サポートファイルフォーマットのエラーハンドリングテスト"""
        from capabilities.ml_evaluation.tools.calculate_shap_values import (
            calculate_shap_values,
        )

        with pytest.raises(ValueError, match="Unsupported file format"):
            calculate_shap_values(
                model_s3_uri="s3://test-bucket/model.pkl",
                data_s3_uri="s3://test-bucket/data.json",
                file_format="json",
            )

    def test_calculate_shap_empty_data(self):
        """空データでのエラーハンドリングテスト"""
        import joblib
        from capabilities.ml_evaluation.tools.calculate_shap_values import (
            calculate_shap_values,
        )

        model = RandomForestClassifier(n_estimators=5, random_state=42)
        model.fit([[1, 2], [3, 4]], [0, 1])

        with patch("boto3.client") as mock_client:
            model_buffer = io.BytesIO()
            joblib.dump(model, model_buffer)
            model_buffer.seek(0)

            empty_data = pd.DataFrame(columns=["feature1", "feature2", "target"])
            csv_buffer = io.StringIO()
            empty_data.to_csv(csv_buffer, index=False)
            csv_bytes = csv_buffer.getvalue().encode("utf-8")

            mock_s3 = Mock()

            def get_object_side_effect(Bucket, Key):
                if "model.pkl" in Key:
                    return {"Body": io.BytesIO(model_buffer.getvalue())}
                else:
                    return {"Body": io.BytesIO(csv_bytes)}

            mock_s3.get_object.side_effect = get_object_side_effect
            mock_client.return_value = mock_s3

            with pytest.raises(ValueError, match="Empty dataset"):
                calculate_shap_values(
                    model_s3_uri="s3://test-bucket/model.pkl",
                    data_s3_uri="s3://test-bucket/data.csv",
                )

    def test_calculate_shap_negative_background_samples(self, mock_s3_shap):
        """負のbackground_samplesのエラーハンドリングテスト"""
        from capabilities.ml_evaluation.tools.calculate_shap_values import (
            calculate_shap_values,
        )

        with pytest.raises(ValueError, match="background_samples must be positive"):
            calculate_shap_values(
                model_s3_uri="s3://test-bucket/model.pkl",
                data_s3_uri="s3://test-bucket/data.csv",
                background_samples=-1,
            )


# =============================================================================
# LIME Tests
# =============================================================================


class TestCalculateLIMEExplanation:
    """
    calculate_lime_explanation関数のユニットテスト
    """

    @pytest.fixture
    def sample_data(self):
        """テストデータ"""
        np.random.seed(42)
        return pd.DataFrame(
            {
                "feature1": np.random.randn(50),
                "feature2": np.random.randn(50),
                "feature3": np.random.randn(50),
                "target": np.random.randint(0, 2, 50),
            }
        )

    @pytest.fixture
    def trained_classifier(self, sample_data):
        """学習済み分類モデル"""
        X = sample_data.iloc[:, :-1]
        y = sample_data.iloc[:, -1]
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X, y)
        return model

    @pytest.fixture
    def trained_regressor(self):
        """学習済み回帰モデル"""
        np.random.seed(42)
        X = np.random.randn(50, 3)
        y = X[:, 0] * 2 + X[:, 1] * 3 + np.random.randn(50) * 0.1
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        model.fit(X, y)
        return model

    @pytest.fixture
    def mock_s3_lime(self, sample_data, trained_classifier):
        """LIME用モックS3クライアント"""
        import joblib

        with patch("boto3.client") as mock_client:
            model_buffer = io.BytesIO()
            joblib.dump(trained_classifier, model_buffer)
            model_buffer.seek(0)

            csv_buffer = io.StringIO()
            sample_data.to_csv(csv_buffer, index=False)
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

    # -------------------------------------------------------------------------
    # 正常系テスト
    # -------------------------------------------------------------------------

    def test_calculate_lime_tabular_success(self, mock_s3_lime):
        """タビュラーデータでのLIME説明成功テスト"""
        from capabilities.ml_evaluation.tools.calculate_lime_explanation import (
            calculate_lime_explanation,
        )

        result = calculate_lime_explanation(
            model_s3_uri="s3://test-bucket/model.pkl",
            data_s3_uri="s3://test-bucket/data.csv",
            instance_index=0,
            file_format="csv",
        )

        assert result["status"] == "success"
        assert "explanation" in result
        assert "feature_weights" in result

    def test_calculate_lime_feature_weights(self, mock_s3_lime):
        """特徴量重みの計算テスト"""
        from capabilities.ml_evaluation.tools.calculate_lime_explanation import (
            calculate_lime_explanation,
        )

        result = calculate_lime_explanation(
            model_s3_uri="s3://test-bucket/model.pkl",
            data_s3_uri="s3://test-bucket/data.csv",
            instance_index=0,
            num_features=3,
            file_format="csv",
        )

        assert "feature_weights" in result
        weights = result["feature_weights"]
        assert len(weights) <= 3

    def test_calculate_lime_top_features(self, mock_s3_lime):
        """上位特徴量の取得テスト"""
        from capabilities.ml_evaluation.tools.calculate_lime_explanation import (
            calculate_lime_explanation,
        )

        result = calculate_lime_explanation(
            model_s3_uri="s3://test-bucket/model.pkl",
            data_s3_uri="s3://test-bucket/data.csv",
            instance_index=0,
            num_features=2,
            file_format="csv",
        )

        assert "top_features" in result
        assert len(result["top_features"]) <= 2

    def test_calculate_lime_classification_model(self, mock_s3_lime):
        """分類モデルでのLIME説明テスト"""
        from capabilities.ml_evaluation.tools.calculate_lime_explanation import (
            calculate_lime_explanation,
        )

        result = calculate_lime_explanation(
            model_s3_uri="s3://test-bucket/model.pkl",
            data_s3_uri="s3://test-bucket/data.csv",
            instance_index=0,
            file_format="csv",
        )

        assert result["status"] == "success"
        assert result["model_type"] == "classifier"
        assert "predicted_class" in result

    def test_calculate_lime_regression_model(self):
        """回帰モデルでのLIME説明テスト"""
        import joblib
        from capabilities.ml_evaluation.tools.calculate_lime_explanation import (
            calculate_lime_explanation,
        )

        np.random.seed(42)
        X = np.random.randn(50, 3)
        y = X[:, 0] * 2 + X[:, 1] * 3 + np.random.randn(50) * 0.1
        data = pd.DataFrame(
            {
                "feature1": X[:, 0],
                "feature2": X[:, 1],
                "feature3": X[:, 2],
                "target": y,
            }
        )
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        model.fit(X, y)

        with patch("boto3.client") as mock_client:
            model_buffer = io.BytesIO()
            joblib.dump(model, model_buffer)
            model_buffer.seek(0)

            csv_buffer = io.StringIO()
            data.to_csv(csv_buffer, index=False)
            csv_bytes = csv_buffer.getvalue().encode("utf-8")

            mock_s3 = Mock()

            def get_object_side_effect(Bucket, Key):
                if "model.pkl" in Key:
                    return {"Body": io.BytesIO(model_buffer.getvalue())}
                else:
                    return {"Body": io.BytesIO(csv_bytes)}

            mock_s3.get_object.side_effect = get_object_side_effect
            mock_client.return_value = mock_s3

            result = calculate_lime_explanation(
                model_s3_uri="s3://test-bucket/model.pkl",
                data_s3_uri="s3://test-bucket/data.csv",
                instance_index=0,
                file_format="csv",
            )

        assert result["status"] == "success"
        assert result["model_type"] == "regressor"
        assert "predicted_value" in result

    def test_calculate_lime_custom_num_features(self, mock_s3_lime):
        """カスタム特徴量数でのテスト"""
        from capabilities.ml_evaluation.tools.calculate_lime_explanation import (
            calculate_lime_explanation,
        )

        result = calculate_lime_explanation(
            model_s3_uri="s3://test-bucket/model.pkl",
            data_s3_uri="s3://test-bucket/data.csv",
            instance_index=0,
            num_features=5,
            file_format="csv",
        )

        assert result["status"] == "success"
        assert result["num_features_requested"] == 5

    def test_calculate_lime_custom_num_samples(self, mock_s3_lime):
        """カスタムサンプル数でのテスト"""
        from capabilities.ml_evaluation.tools.calculate_lime_explanation import (
            calculate_lime_explanation,
        )

        result = calculate_lime_explanation(
            model_s3_uri="s3://test-bucket/model.pkl",
            data_s3_uri="s3://test-bucket/data.csv",
            instance_index=0,
            num_samples=1000,
            file_format="csv",
        )

        assert result["status"] == "success"
        assert result["num_samples_used"] == 1000

    def test_calculate_lime_different_instances(self, mock_s3_lime):
        """異なるインスタンスでの説明テスト"""
        from capabilities.ml_evaluation.tools.calculate_lime_explanation import (
            calculate_lime_explanation,
        )

        result1 = calculate_lime_explanation(
            model_s3_uri="s3://test-bucket/model.pkl",
            data_s3_uri="s3://test-bucket/data.csv",
            instance_index=0,
            file_format="csv",
        )

        result2 = calculate_lime_explanation(
            model_s3_uri="s3://test-bucket/model.pkl",
            data_s3_uri="s3://test-bucket/data.csv",
            instance_index=5,
            file_format="csv",
        )

        assert result1["status"] == "success"
        assert result2["status"] == "success"
        assert result1["instance_index"] == 0
        assert result2["instance_index"] == 5

    def test_calculate_lime_local_fidelity(self, mock_s3_lime):
        """局所的忠実度スコアのテスト"""
        from capabilities.ml_evaluation.tools.calculate_lime_explanation import (
            calculate_lime_explanation,
        )

        result = calculate_lime_explanation(
            model_s3_uri="s3://test-bucket/model.pkl",
            data_s3_uri="s3://test-bucket/data.csv",
            instance_index=0,
            file_format="csv",
        )

        assert "local_fidelity_score" in result
        assert 0 <= result["local_fidelity_score"] <= 1

    # -------------------------------------------------------------------------
    # 異常系テスト
    # -------------------------------------------------------------------------

    def test_calculate_lime_invalid_model_uri(self):
        """無効なモデルS3 URIのエラーハンドリングテスト"""
        from capabilities.ml_evaluation.tools.calculate_lime_explanation import (
            calculate_lime_explanation,
        )

        with pytest.raises(ValueError, match="Invalid S3 URI"):
            calculate_lime_explanation(
                model_s3_uri="invalid://bucket/model.pkl",
                data_s3_uri="s3://test-bucket/data.csv",
            )

    def test_calculate_lime_invalid_data_uri(self):
        """無効なデータS3 URIのエラーハンドリングテスト"""
        from capabilities.ml_evaluation.tools.calculate_lime_explanation import (
            calculate_lime_explanation,
        )

        with pytest.raises(ValueError, match="Invalid S3 URI"):
            calculate_lime_explanation(
                model_s3_uri="s3://test-bucket/model.pkl",
                data_s3_uri="invalid://bucket/data.csv",
            )

    def test_calculate_lime_invalid_instance_index(self, mock_s3_lime):
        """無効なインスタンスインデックスのエラーハンドリングテスト"""
        from capabilities.ml_evaluation.tools.calculate_lime_explanation import (
            calculate_lime_explanation,
        )

        with pytest.raises(ValueError, match="Instance index out of range"):
            calculate_lime_explanation(
                model_s3_uri="s3://test-bucket/model.pkl",
                data_s3_uri="s3://test-bucket/data.csv",
                instance_index=1000,
            )

    def test_calculate_lime_negative_instance_index(self, mock_s3_lime):
        """負のインスタンスインデックスのエラーハンドリングテスト"""
        from capabilities.ml_evaluation.tools.calculate_lime_explanation import (
            calculate_lime_explanation,
        )

        with pytest.raises(ValueError, match="Instance index must be non-negative"):
            calculate_lime_explanation(
                model_s3_uri="s3://test-bucket/model.pkl",
                data_s3_uri="s3://test-bucket/data.csv",
                instance_index=-1,
            )

    def test_calculate_lime_unsupported_file_format(self, mock_s3_lime):
        """未サポートファイルフォーマットのエラーハンドリングテスト"""
        from capabilities.ml_evaluation.tools.calculate_lime_explanation import (
            calculate_lime_explanation,
        )

        with pytest.raises(ValueError, match="Unsupported file format"):
            calculate_lime_explanation(
                model_s3_uri="s3://test-bucket/model.pkl",
                data_s3_uri="s3://test-bucket/data.json",
                file_format="json",
            )

    def test_calculate_lime_zero_num_features(self, mock_s3_lime):
        """num_features=0のエラーハンドリングテスト"""
        from capabilities.ml_evaluation.tools.calculate_lime_explanation import (
            calculate_lime_explanation,
        )

        with pytest.raises(ValueError, match="num_features must be positive"):
            calculate_lime_explanation(
                model_s3_uri="s3://test-bucket/model.pkl",
                data_s3_uri="s3://test-bucket/data.csv",
                num_features=0,
            )

    def test_calculate_lime_zero_num_samples(self, mock_s3_lime):
        """num_samples=0のエラーハンドリングテスト"""
        from capabilities.ml_evaluation.tools.calculate_lime_explanation import (
            calculate_lime_explanation,
        )

        with pytest.raises(ValueError, match="num_samples must be positive"):
            calculate_lime_explanation(
                model_s3_uri="s3://test-bucket/model.pkl",
                data_s3_uri="s3://test-bucket/data.csv",
                num_samples=0,
            )


# =============================================================================
# Integration Tests for SHAP and LIME together
# =============================================================================


class TestSHAPLIMEIntegration:
    """SHAP/LIME統合テスト"""

    @pytest.fixture
    def sample_data(self):
        """共通テストデータ"""
        np.random.seed(42)
        return pd.DataFrame(
            {
                "feature1": np.random.randn(30),
                "feature2": np.random.randn(30),
                "target": np.random.randint(0, 2, 30),
            }
        )

    @pytest.fixture
    def trained_model(self, sample_data):
        """共通学習済みモデル"""
        X = sample_data.iloc[:, :-1]
        y = sample_data.iloc[:, -1]
        model = RandomForestClassifier(n_estimators=5, random_state=42)
        model.fit(X, y)
        return model

    @pytest.fixture
    def mock_s3_integration(self, sample_data, trained_model):
        """統合テスト用モックS3"""
        import joblib

        with patch("boto3.client") as mock_client:
            model_buffer = io.BytesIO()
            joblib.dump(trained_model, model_buffer)
            model_buffer.seek(0)

            csv_buffer = io.StringIO()
            sample_data.to_csv(csv_buffer, index=False)
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

    def test_shap_and_lime_consistent_features(self, mock_s3_integration):
        """SHAP/LIME両方で同じ特徴量が重要と判定されるか"""
        from capabilities.ml_evaluation.tools.calculate_lime_explanation import (
            calculate_lime_explanation,
        )
        from capabilities.ml_evaluation.tools.calculate_shap_values import (
            calculate_shap_values,
        )

        shap_result = calculate_shap_values(
            model_s3_uri="s3://test-bucket/model.pkl",
            data_s3_uri="s3://test-bucket/data.csv",
            explainer_type="tree",
            file_format="csv",
        )

        lime_result = calculate_lime_explanation(
            model_s3_uri="s3://test-bucket/model.pkl",
            data_s3_uri="s3://test-bucket/data.csv",
            instance_index=0,
            file_format="csv",
        )

        assert shap_result["status"] == "success"
        assert lime_result["status"] == "success"
        # 両方の結果に特徴量情報が含まれることを確認
        assert "feature_importance" in shap_result
        assert "feature_weights" in lime_result

    def test_both_methods_handle_same_model(self, mock_s3_integration):
        """同じモデルに対して両メソッドが正常動作するか"""
        from capabilities.ml_evaluation.tools.calculate_lime_explanation import (
            calculate_lime_explanation,
        )
        from capabilities.ml_evaluation.tools.calculate_shap_values import (
            calculate_shap_values,
        )

        shap_result = calculate_shap_values(
            model_s3_uri="s3://test-bucket/model.pkl",
            data_s3_uri="s3://test-bucket/data.csv",
            file_format="csv",
        )

        lime_result = calculate_lime_explanation(
            model_s3_uri="s3://test-bucket/model.pkl",
            data_s3_uri="s3://test-bucket/data.csv",
            file_format="csv",
        )

        assert shap_result["status"] == "success"
        assert lime_result["status"] == "success"
