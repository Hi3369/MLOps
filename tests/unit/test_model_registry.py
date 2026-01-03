"""
Model Registry Capability Unit Tests

Model Registry toolsのユニットテスト
"""

import io
import json
import os
import sys
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

# Add mcp_server to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "mcp_server"))

from capabilities.model_registry.tools.delete_model import delete_model
from capabilities.model_registry.tools.get_model import get_model
from capabilities.model_registry.tools.list_models import list_models
from capabilities.model_registry.tools.register_model import register_model
from capabilities.model_registry.tools.update_model_status import update_model_status


class TestRegisterModel:
    """
    register_model関数のユニットテスト
    """

    @pytest.fixture
    def mock_s3_register(self):
        """モデル登録用モックS3クライアント"""
        with patch("boto3.client") as mock_client:
            mock_s3 = Mock()

            # head_object: モデルの存在確認
            mock_s3.head_object.return_value = {"ContentLength": 1024}

            # put_object: メタデータの保存
            mock_s3.put_object.return_value = {}

            mock_client.return_value = mock_s3

            yield mock_s3

    def test_register_model_success(self, mock_s3_register):
        """
        モデル登録の成功テスト
        """
        result = register_model(
            model_s3_uri="s3://test-bucket/models/model.pkl",
            model_name="test_model",
            model_version="v1.0",
            metadata={"algorithm": "random_forest", "accuracy": 0.95},
            tags={"env": "production"},
        )

        # 実行結果の確認
        assert result["status"] == "success"
        assert "registration_info" in result

        # 登録情報の確認
        info = result["registration_info"]
        assert info["model_name"] == "test_model"
        assert info["model_version"] == "v1.0"
        assert info["model_s3_uri"] == "s3://test-bucket/models/model.pkl"
        assert "metadata_s3_uri" in info
        assert "registered_at" in info

        # S3呼び出しの確認
        mock_s3_register.head_object.assert_called_once()
        mock_s3_register.put_object.assert_called_once()

    def test_register_model_auto_version(self, mock_s3_register):
        """
        バージョン自動生成のテスト
        """
        result = register_model(
            model_s3_uri="s3://test-bucket/models/model.pkl",
            model_name="test_model",
        )

        assert result["status"] == "success"
        info = result["registration_info"]
        # バージョンが自動生成されている（タイムスタンプ形式）
        assert info["model_version"] is not None
        assert len(info["model_version"]) > 0

    def test_register_model_invalid_uri(self):
        """
        無効なS3 URIのエラーハンドリングテスト
        """
        with pytest.raises(ValueError, match="Invalid S3 URI"):
            register_model(
                model_s3_uri="invalid://bucket/model.pkl",
                model_name="test_model",
            )

    def test_register_model_not_found(self):
        """
        モデルが存在しない場合のエラーハンドリングテスト
        """
        with patch("boto3.client") as mock_client:
            mock_s3 = Mock()
            from botocore.exceptions import ClientError

            # モデルが存在しない
            mock_s3.head_object.side_effect = ClientError(
                {"Error": {"Code": "404", "Message": "Not Found"}}, "head_object"
            )

            mock_client.return_value = mock_s3

            with pytest.raises(ValueError, match="Model not found"):
                register_model(
                    model_s3_uri="s3://test-bucket/models/model.pkl",
                    model_name="test_model",
                )


class TestListModels:
    """
    list_models関数のユニットテスト
    """

    @pytest.fixture
    def mock_s3_list(self):
        """モデル一覧用モックS3クライアント"""
        with patch("boto3.client") as mock_client:
            mock_s3 = Mock()

            # レジストリメタデータ
            registry_data_1 = {
                "model_name": "model1",
                "model_version": "v1.0",
                "status": "production",
                "registered_at": "2024-01-01T00:00:00",
            }

            registry_data_2 = {
                "model_name": "model2",
                "model_version": "v1.0",
                "status": "staging",
                "registered_at": "2024-01-02T00:00:00",
            }

            # list_objects_v2のページネーター
            mock_paginator = Mock()
            mock_paginator.paginate.return_value = [
                {
                    "Contents": [
                        {"Key": "models/model1_registry.json"},
                        {"Key": "models/model2_registry.json"},
                    ]
                }
            ]
            mock_s3.get_paginator.return_value = mock_paginator

            # get_object: メタデータの取得
            def get_object_side_effect(Bucket, Key):
                if "model1_registry" in Key:
                    return {"Body": io.BytesIO(json.dumps(registry_data_1).encode("utf-8"))}
                else:
                    return {"Body": io.BytesIO(json.dumps(registry_data_2).encode("utf-8"))}

            mock_s3.get_object.side_effect = get_object_side_effect

            mock_client.return_value = mock_s3

            yield mock_s3

    def test_list_models_success(self, mock_s3_list):
        """
        モデル一覧取得の成功テスト
        """
        result = list_models(registry_s3_uri="s3://test-bucket/models/")

        # 実行結果の確認
        assert result["status"] == "success"
        assert "models" in result
        assert result["total_count"] == 2

        # モデル一覧の確認
        models = result["models"]
        assert len(models) == 2
        # 新しい順にソートされている
        assert models[0]["registered_at"] == "2024-01-02T00:00:00"
        assert models[1]["registered_at"] == "2024-01-01T00:00:00"

    def test_list_models_with_filter(self, mock_s3_list):
        """
        ステータスフィルタ付きモデル一覧取得のテスト
        """
        result = list_models(registry_s3_uri="s3://test-bucket/models/", status_filter="production")

        assert result["status"] == "success"
        # production statusのモデルのみ（model1）
        assert result["total_count"] == 1
        assert result["models"][0]["model_name"] == "model1"

    def test_list_models_invalid_uri(self):
        """
        無効なS3 URIのエラーハンドリングテスト
        """
        with pytest.raises(ValueError, match="Invalid S3 URI"):
            list_models(registry_s3_uri="invalid://bucket/models/")


class TestGetModel:
    """
    get_model関数のユニットテスト
    """

    @pytest.fixture
    def mock_s3_get(self):
        """モデル取得用モックS3クライアント"""
        with patch("boto3.client") as mock_client:
            mock_s3 = Mock()

            # head_object: モデル情報取得
            mock_s3.head_object.return_value = {
                "ContentLength": 2048,
                "LastModified": datetime(2024, 1, 1, 0, 0, 0),
            }

            # get_object: レジストリメタデータ取得
            registry_data = {
                "model_name": "test_model",
                "model_version": "v1.0",
                "status": "production",
            }

            mock_s3.get_object.return_value = {
                "Body": io.BytesIO(json.dumps(registry_data).encode("utf-8"))
            }

            mock_client.return_value = mock_s3

            yield mock_s3

    def test_get_model_success(self, mock_s3_get):
        """
        モデル情報取得の成功テスト
        """
        result = get_model(model_s3_uri="s3://test-bucket/models/model.pkl")

        # 実行結果の確認
        assert result["status"] == "success"
        assert "model_info" in result

        # モデル情報の確認
        info = result["model_info"]
        assert info["model_s3_uri"] == "s3://test-bucket/models/model.pkl"
        assert info["model_size_bytes"] == 2048
        assert "model_last_modified" in info
        assert "registry_metadata" in info
        assert info["registry_metadata"]["model_name"] == "test_model"

    def test_get_model_without_registry(self):
        """
        レジストリメタデータがない場合のテスト
        """
        with patch("boto3.client") as mock_client:
            mock_s3 = Mock()
            from botocore.exceptions import ClientError

            # モデルは存在
            mock_s3.head_object.return_value = {
                "ContentLength": 2048,
                "LastModified": datetime(2024, 1, 1, 0, 0, 0),
            }

            # レジストリメタデータは存在しない
            mock_s3.get_object.side_effect = ClientError(
                {"Error": {"Code": "404", "Message": "Not Found"}}, "get_object"
            )

            mock_client.return_value = mock_s3

            result = get_model(model_s3_uri="s3://test-bucket/models/model.pkl")

            # デフォルトのレジストリメタデータが返される
            assert result["status"] == "success"
            info = result["model_info"]
            assert info["registry_metadata"]["status"] == "unregistered"

    def test_get_model_invalid_uri(self):
        """
        無効なS3 URIのエラーハンドリングテスト
        """
        with pytest.raises(ValueError, match="Invalid S3 URI"):
            get_model(model_s3_uri="invalid://bucket/model.pkl")


class TestUpdateModelStatus:
    """
    update_model_status関数のユニットテスト
    """

    @pytest.fixture
    def mock_s3_update(self):
        """ステータス更新用モックS3クライアント"""
        with patch("boto3.client") as mock_client:
            mock_s3 = Mock()

            # get_object: 現在のメタデータ取得
            current_metadata = {
                "model_name": "test_model",
                "model_version": "v1.0",
                "status": "staging",
                "registered_at": "2024-01-01T00:00:00",
            }

            mock_s3.get_object.return_value = {
                "Body": io.BytesIO(json.dumps(current_metadata).encode("utf-8"))
            }

            # put_object: 更新後のメタデータ保存
            mock_s3.put_object.return_value = {}

            mock_client.return_value = mock_s3

            yield mock_s3

    def test_update_model_status_success(self, mock_s3_update):
        """
        ステータス更新の成功テスト
        """
        result = update_model_status(
            model_s3_uri="s3://test-bucket/models/model.pkl", status="production"
        )

        # 実行結果の確認
        assert result["status"] == "success"
        assert "update_info" in result

        # 更新情報の確認
        info = result["update_info"]
        assert info["old_status"] == "staging"
        assert info["new_status"] == "production"
        assert "updated_at" in info

        # S3呼び出しの確認
        mock_s3_update.get_object.assert_called_once()
        mock_s3_update.put_object.assert_called_once()

    def test_update_model_status_invalid_status(self):
        """
        無効なステータスのエラーハンドリングテスト
        """
        with pytest.raises(ValueError, match="Invalid status"):
            update_model_status(model_s3_uri="s3://test-bucket/models/model.pkl", status="invalid")

    def test_update_model_status_invalid_uri(self):
        """
        無効なS3 URIのエラーハンドリングテスト
        """
        with pytest.raises(ValueError, match="Invalid S3 URI"):
            update_model_status(model_s3_uri="invalid://bucket/model.pkl", status="production")


class TestDeleteModel:
    """
    delete_model関数のユニットテスト
    """

    @pytest.fixture
    def mock_s3_delete(self):
        """モデル削除用モックS3クライアント"""
        with patch("boto3.client") as mock_client:
            mock_s3 = Mock()

            # delete_object: ファイル削除
            mock_s3.delete_object.return_value = {}

            # head_object: 学習メタデータの存在確認
            mock_s3.head_object.return_value = {"ContentLength": 512}

            mock_client.return_value = mock_s3

            yield mock_s3

    def test_delete_model_success(self, mock_s3_delete):
        """
        モデル削除の成功テスト（メタデータも削除）
        """
        result = delete_model(
            model_s3_uri="s3://test-bucket/models/model.pkl", delete_metadata=True
        )

        # 実行結果の確認
        assert result["status"] == "success"
        assert "deletion_info" in result

        # 削除情報の確認
        info = result["deletion_info"]
        assert info["model_s3_uri"] == "s3://test-bucket/models/model.pkl"
        assert len(info["deleted_objects"]) >= 1  # モデルファイルは必ず削除
        assert info["total_deleted"] >= 1

        # S3呼び出しの確認（複数回delete_objectが呼ばれる）
        assert mock_s3_delete.delete_object.call_count >= 1

    def test_delete_model_without_metadata(self, mock_s3_delete):
        """
        モデル削除（メタデータは削除しない）
        """
        result = delete_model(
            model_s3_uri="s3://test-bucket/models/model.pkl", delete_metadata=False
        )

        # モデルファイルのみ削除
        assert result["status"] == "success"
        info = result["deletion_info"]
        assert len(info["deleted_objects"]) == 1
        assert info["deleted_objects"][0] == "s3://test-bucket/models/model.pkl"

    def test_delete_model_invalid_uri(self):
        """
        無効なS3 URIのエラーハンドリングテスト
        """
        with pytest.raises(ValueError, match="Invalid S3 URI"):
            delete_model(model_s3_uri="invalid://bucket/model.pkl")
