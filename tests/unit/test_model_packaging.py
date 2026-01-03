"""
Model Packaging Capability Unit Tests

Model Packaging toolsのユニットテスト
"""

import io
import json
import os
import sys
import tarfile
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add mcp_server to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "mcp_server"))

from capabilities.model_packaging.tools.create_dockerfile import create_dockerfile
from capabilities.model_packaging.tools.create_model_package import create_model_package
from capabilities.model_packaging.tools.extract_model_metadata import extract_model_metadata
from capabilities.model_packaging.tools.generate_deployment_config import generate_deployment_config
from capabilities.model_packaging.tools.validate_package import validate_package


class TestCreateModelPackage:
    """
    create_model_package関数のユニットテスト
    """

    @pytest.fixture
    def mock_s3_package(self):
        """パッケージ作成用モックS3クライアント"""
        with patch("boto3.client") as mock_client:
            mock_s3 = Mock()

            # head_object: モデルの存在確認
            mock_s3.head_object.return_value = {"ContentLength": 1024}

            # upload_file: パッケージのアップロード
            mock_s3.upload_file.return_value = None

            # put_object: メタデータの保存
            mock_s3.put_object.return_value = {}

            mock_client.return_value = mock_s3

            yield mock_s3

    def test_create_model_package_success(self, mock_s3_package):
        """
        モデルパッケージ作成の成功テスト
        """
        result = create_model_package(
            model_s3_uri="s3://test-bucket/models/model.pkl",
            package_name="my_model_package",
            framework="sklearn",
            python_version="3.11",
        )

        # 実行結果の確認
        assert result["status"] == "success"
        assert "package_info" in result

        # パッケージ情報の確認
        package_info = result["package_info"]
        assert package_info["package_name"] == "my_model_package"
        assert package_info["framework"] == "sklearn"
        assert package_info["python_version"] == "3.11"
        assert "package_s3_uri" in package_info
        assert "dependencies" in package_info

        # S3呼び出しの確認
        mock_s3_package.head_object.assert_called_once()
        mock_s3_package.upload_file.assert_called_once()
        mock_s3_package.put_object.assert_called_once()

    def test_create_model_package_custom_dependencies(self, mock_s3_package):
        """
        カスタム依存パッケージ指定のテスト
        """
        custom_deps = {
            "scikit-learn": "1.4.0",
            "pandas": "2.2.0",
            "custom-package": "1.0.0",
        }

        result = create_model_package(
            model_s3_uri="s3://test-bucket/models/model.pkl",
            package_name="custom_package",
            dependencies=custom_deps,
        )

        assert result["status"] == "success"
        assert result["package_info"]["dependencies"] == custom_deps

    def test_create_model_package_invalid_uri(self):
        """
        無効なS3 URIのエラーハンドリングテスト
        """
        with pytest.raises(ValueError, match="Invalid S3 URI"):
            create_model_package(
                model_s3_uri="invalid://bucket/model.pkl",
                package_name="test",
            )

    def test_create_model_package_model_not_found(self):
        """
        モデルが存在しない場合のエラーハンドリングテスト
        """
        with patch("boto3.client") as mock_client:
            mock_s3 = Mock()
            from botocore.exceptions import ClientError

            mock_s3.head_object.side_effect = ClientError(
                {"Error": {"Code": "404", "Message": "Not Found"}}, "head_object"
            )

            mock_client.return_value = mock_s3

            with pytest.raises(ValueError, match="Model not found"):
                create_model_package(
                    model_s3_uri="s3://test-bucket/models/model.pkl",
                    package_name="test",
                )


class TestCreateDockerfile:
    """
    create_dockerfile関数のユニットテスト
    """

    def test_create_dockerfile_success(self):
        """
        Dockerfile生成の成功テスト
        """
        result = create_dockerfile(
            model_s3_uri="s3://test-bucket/models/model.pkl",
            framework="sklearn",
            python_version="3.11",
        )

        # 実行結果の確認
        assert result["status"] == "success"
        assert "dockerfile" in result

        # Dockerfile情報の確認
        dockerfile_info = result["dockerfile"]
        assert "content" in dockerfile_info
        assert dockerfile_info["framework"] == "sklearn"
        assert dockerfile_info["python_version"] == "3.11"
        assert "python:3.11" in dockerfile_info["base_image"]

        # Dockerfile内容の確認
        content = dockerfile_info["content"]
        assert "FROM" in content
        assert "WORKDIR" in content
        assert "CMD" in content

    def test_create_dockerfile_optimized(self):
        """
        最適化されたDockerfile生成のテスト
        """
        result = create_dockerfile(
            model_s3_uri="s3://test-bucket/models/model.pkl",
            framework="sklearn",
            optimize=True,
        )

        assert result["status"] == "success"
        assert result["dockerfile"]["optimized"] is True

        # マルチステージビルドが含まれているか確認
        content = result["dockerfile"]["content"]
        assert "AS builder" in content or "Multi-stage" in content

    def test_create_dockerfile_custom_base_image(self):
        """
        カスタムベースイメージ指定のテスト
        """
        custom_image = "my-custom-base:latest"

        result = create_dockerfile(
            model_s3_uri="s3://test-bucket/models/model.pkl",
            base_image=custom_image,
        )

        assert result["status"] == "success"
        assert result["dockerfile"]["base_image"] == custom_image
        assert f"FROM {custom_image}" in result["dockerfile"]["content"]

    def test_create_dockerfile_invalid_uri(self):
        """
        無効なS3 URIのエラーハンドリングテスト
        """
        with pytest.raises(ValueError, match="Invalid S3 URI"):
            create_dockerfile(model_s3_uri="invalid://bucket/model.pkl")


class TestValidatePackage:
    """
    validate_package関数のユニットテスト
    """

    @pytest.fixture
    def create_valid_package(self):
        """有効なパッケージファイルを作成"""

        def _create(tmp_dir):
            # パッケージディレクトリを作成
            package_dir = Path(tmp_dir) / "test_package"
            package_dir.mkdir()

            # 必須ファイルを作成
            (package_dir / "requirements.txt").write_text("scikit-learn==1.3.2\n")

            config = {
                "model_s3_uri": "s3://test-bucket/model.pkl",
                "framework": "sklearn",
                "entrypoint": "inference.py",
            }
            (package_dir / "config.json").write_text(json.dumps(config))

            (package_dir / "inference.py").write_text(
                "def load_model(): pass\ndef predict(model, data): pass\n"
            )

            # tar.gzに圧縮
            package_file = Path(tmp_dir) / "package.tar.gz"
            with tarfile.open(package_file, "w:gz") as tar:
                tar.add(package_dir, arcname=package_dir.name)

            return package_file.read_bytes()

        return _create

    @pytest.fixture
    def mock_s3_validate(self, create_valid_package):
        """パッケージ検証用モックS3クライアント"""
        with patch("boto3.client") as mock_client:
            with tempfile.TemporaryDirectory() as tmp_dir:
                package_content = create_valid_package(tmp_dir)

                mock_s3 = Mock()
                mock_s3.get_object.return_value = {"Body": io.BytesIO(package_content)}

                mock_client.return_value = mock_s3

                yield mock_s3

    def test_validate_package_success(self, mock_s3_validate):
        """
        有効なパッケージの検証成功テスト
        """
        result = validate_package(package_s3_uri="s3://test-bucket/package.tar.gz")

        # 実行結果の確認
        assert result["status"] == "success"
        assert "validation_results" in result

        # 検証結果の確認
        validation = result["validation_results"]
        assert validation["is_valid"] is True
        assert len(validation["errors"]) == 0
        assert "requirements.txt" in validation["files_found"]
        assert "config.json" in validation["files_found"]
        assert "inference.py" in validation["files_found"]

    def test_validate_package_invalid_uri(self):
        """
        無効なS3 URIのエラーハンドリングテスト
        """
        with pytest.raises(ValueError, match="Invalid S3 URI"):
            validate_package(package_s3_uri="invalid://bucket/package.tar.gz")


class TestGenerateDeploymentConfig:
    """
    generate_deployment_config関数のユニットテスト
    """

    def test_generate_sagemaker_config(self):
        """
        SageMakerデプロイ設定生成のテスト
        """
        result = generate_deployment_config(
            model_s3_uri="s3://test-bucket/models/model.pkl",
            deployment_type="sagemaker",
            instance_type="ml.t3.medium",
            instance_count=2,
        )

        # 実行結果の確認
        assert result["status"] == "success"
        assert "deployment_config" in result

        # 設定内容の確認
        config = result["deployment_config"]
        assert config["deployment_type"] == "sagemaker"
        assert config["instance_type"] == "ml.t3.medium"
        assert config["initial_instance_count"] == 2
        assert "endpoint_config" in config

    def test_generate_ecs_config(self):
        """
        ECSデプロイ設定生成のテスト
        """
        result = generate_deployment_config(
            model_s3_uri="s3://test-bucket/models/model.pkl",
            deployment_type="ecs",
            instance_type="t3.medium",
            instance_count=1,
        )

        assert result["status"] == "success"
        config = result["deployment_config"]
        assert config["deployment_type"] == "ecs"
        assert "task_definition" in config
        assert "service" in config

    def test_generate_lambda_config(self):
        """
        Lambdaデプロイ設定生成のテスト
        """
        result = generate_deployment_config(
            model_s3_uri="s3://test-bucket/models/model.pkl",
            deployment_type="lambda",
        )

        assert result["status"] == "success"
        config = result["deployment_config"]
        assert config["deployment_type"] == "lambda"
        assert "function_config" in config
        assert config["function_config"]["runtime"] == "python3.11"

    def test_generate_config_with_autoscaling(self):
        """
        オートスケーリング有効化のテスト
        """
        result = generate_deployment_config(
            model_s3_uri="s3://test-bucket/models/model.pkl",
            deployment_type="sagemaker",
            auto_scaling=True,
        )

        assert result["status"] == "success"
        config = result["deployment_config"]
        assert "auto_scaling" in config
        assert config["auto_scaling"]["enabled"] is True

    def test_generate_config_invalid_deployment_type(self):
        """
        無効なデプロイタイプのエラーハンドリングテスト
        """
        with pytest.raises(ValueError, match="Invalid deployment_type"):
            generate_deployment_config(
                model_s3_uri="s3://test-bucket/models/model.pkl",
                deployment_type="invalid_type",
            )

    def test_generate_config_invalid_uri(self):
        """
        無効なS3 URIのエラーハンドリングテスト
        """
        with pytest.raises(ValueError, match="Invalid S3 URI"):
            generate_deployment_config(model_s3_uri="invalid://bucket/model.pkl")


class TestExtractModelMetadata:
    """
    extract_model_metadata関数のユニットテスト
    """

    @pytest.fixture
    def mock_s3_extract(self):
        """メタデータ抽出用モックS3クライアント"""
        import joblib
        from sklearn.ensemble import RandomForestClassifier

        # サンプルモデルを作成
        model = RandomForestClassifier(n_estimators=10, random_state=42)

        # モデルをシリアライズ
        model_buffer = io.BytesIO()
        joblib.dump(model, model_buffer)
        model_buffer.seek(0)

        with patch("boto3.client") as mock_client:
            mock_s3 = Mock()

            # get_object: モデルデータ
            mock_s3.get_object.return_value = {"Body": io.BytesIO(model_buffer.getvalue())}

            # head_object: S3メタデータ
            from datetime import datetime

            mock_s3.head_object.return_value = {
                "ContentLength": 2048,
                "LastModified": datetime(2024, 1, 1, 0, 0, 0),
                "ContentType": "application/octet-stream",
            }

            mock_client.return_value = mock_s3

            yield mock_s3

    def test_extract_model_metadata_success(self, mock_s3_extract):
        """
        メタデータ抽出の成功テスト
        """
        result = extract_model_metadata(model_s3_uri="s3://test-bucket/models/model.pkl")

        # 実行結果の確認
        assert result["status"] == "success"
        assert "metadata" in result

        # メタデータの確認
        metadata = result["metadata"]
        assert metadata["model_s3_uri"] == "s3://test-bucket/models/model.pkl"
        assert "model_info" in metadata
        assert "s3_metadata" in metadata

        # モデル情報の確認
        model_info = metadata["model_info"]
        assert model_info["model_type"] == "RandomForestClassifier"
        assert "module" in model_info

        # S3メタデータの確認
        s3_metadata = metadata["s3_metadata"]
        assert s3_metadata["size_bytes"] == 2048

    def test_extract_model_metadata_invalid_uri(self):
        """
        無効なS3 URIのエラーハンドリングテスト
        """
        with pytest.raises(ValueError, match="Invalid S3 URI"):
            extract_model_metadata(model_s3_uri="invalid://bucket/model.pkl")
