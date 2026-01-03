"""
Model Monitoring Capability Unit Tests

Model Monitoring toolsのユニットテスト
"""

import json
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

# Add mcp_server to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "mcp_server"))

from capabilities.model_monitoring.tools import (
    collect_model_metrics,
    collect_system_metrics,
    create_cloudwatch_alarm,
    create_monitoring_dashboard,
    delete_cloudwatch_alarm,
    delete_dashboard,
    detect_concept_drift,
    detect_data_drift,
    get_alarm_state,
    update_dashboard,
)


class TestCollectSystemMetrics:
    """
    collect_system_metrics関数のユニットテスト
    """

    @pytest.fixture
    def mock_cloudwatch(self):
        """CloudWatch用モッククライアント"""
        with patch("boto3.client") as mock_client:
            mock_cw = Mock()

            # get_metric_statistics: メトリクス統計を返す
            mock_cw.get_metric_statistics.return_value = {
                "Datapoints": [
                    {
                        "Timestamp": datetime.utcnow() - timedelta(minutes=10),
                        "Average": 45.0,
                        "Minimum": 30.0,
                        "Maximum": 60.0,
                        "Sum": 450.0,
                        "SampleCount": 10,
                    },
                    {
                        "Timestamp": datetime.utcnow() - timedelta(minutes=5),
                        "Average": 50.0,
                        "Minimum": 35.0,
                        "Maximum": 65.0,
                        "Sum": 500.0,
                        "SampleCount": 10,
                    },
                ]
            }

            mock_client.return_value = mock_cw

            yield mock_cw

    def test_collect_system_metrics_success(self, mock_cloudwatch):
        """
        システムメトリクス収集の成功テスト
        """
        result = collect_system_metrics(
            endpoint_name="test-endpoint",
            time_range_minutes=60,
            metric_period_seconds=300,
        )

        # 実行結果の確認
        assert result["status"] == "success"
        assert "metrics_info" in result

        # メトリクス情報の確認
        info = result["metrics_info"]
        assert info["endpoint_name"] == "test-endpoint"
        assert info["period_seconds"] == 300
        assert "time_range" in info
        assert info["time_range"]["duration_minutes"] == 60

        # 各メトリクスが存在することを確認
        assert "CPUUtilization" in info["metrics"]
        assert "MemoryUtilization" in info["metrics"]
        assert "DiskUtilization" in info["metrics"]
        assert "ModelLatency" in info["metrics"]
        assert "OverheadLatency" in info["metrics"]

        # CloudWatch API呼び出しの確認（5つのシステムメトリクス）
        assert mock_cloudwatch.get_metric_statistics.call_count == 5

    def test_collect_system_metrics_with_data(self, mock_cloudwatch):
        """
        データが存在する場合のメトリクス収集テスト
        """
        result = collect_system_metrics(
            endpoint_name="test-endpoint",
            time_range_minutes=30,
        )

        assert result["status"] == "success"
        info = result["metrics_info"]

        # メトリクスデータの確認
        cpu_metric = info["metrics"]["CPUUtilization"]
        assert cpu_metric["available"] is True
        assert cpu_metric["datapoints_count"] == 2
        assert "latest" in cpu_metric
        assert cpu_metric["latest"]["average"] == 50.0

    def test_collect_system_metrics_no_data(self):
        """
        データが存在しない場合のメトリクス収集テスト
        """
        with patch("boto3.client") as mock_client:
            mock_cw = Mock()

            # データポイントなし
            mock_cw.get_metric_statistics.return_value = {"Datapoints": []}

            mock_client.return_value = mock_cw

            result = collect_system_metrics(endpoint_name="test-endpoint")

            assert result["status"] == "success"
            info = result["metrics_info"]

            # データが存在しないことを確認
            cpu_metric = info["metrics"]["CPUUtilization"]
            assert cpu_metric["available"] is False
            assert cpu_metric["datapoints_count"] == 0

    def test_collect_system_metrics_error(self):
        """
        CloudWatchエラーのハンドリングテスト
        個別のメトリクスエラーは警告として処理され、結果には含まれる
        """
        with patch("boto3.client") as mock_client:
            mock_cw = Mock()
            from botocore.exceptions import ClientError

            mock_cw.get_metric_statistics.side_effect = ClientError(
                {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}},
                "get_metric_statistics",
            )

            mock_client.return_value = mock_cw

            # エラーは警告として処理され、関数は成功を返す
            result = collect_system_metrics(endpoint_name="test-endpoint")

            assert result["status"] == "success"
            assert "metrics_info" in result
            # すべてのメトリクスがエラー状態で含まれる
            for metric_name in ["CPUUtilization", "MemoryUtilization", "DiskUtilization"]:
                assert metric_name in result["metrics_info"]["metrics"]
                assert result["metrics_info"]["metrics"][metric_name]["available"] is False


class TestCollectModelMetrics:
    """
    collect_model_metrics関数のユニットテスト
    """

    @pytest.fixture
    def mock_cloudwatch_model(self):
        """CloudWatch用モッククライアント（モデルメトリクス）"""
        with patch("boto3.client") as mock_client:
            mock_cw = Mock()

            def get_metric_stats(MetricName, **kwargs):
                # Invocationsは合計値を返す
                if MetricName == "Invocations":
                    return {
                        "Datapoints": [
                            {
                                "Timestamp": datetime.utcnow(),
                                "Average": 100.0,
                                "Sum": 1000.0,
                                "Minimum": 50.0,
                                "Maximum": 150.0,
                                "SampleCount": 10,
                            }
                        ]
                    }
                # エラーは少数
                elif "Error" in MetricName:
                    return {
                        "Datapoints": [
                            {
                                "Timestamp": datetime.utcnow(),
                                "Average": 5.0,
                                "Sum": 50.0,
                                "Minimum": 0.0,
                                "Maximum": 10.0,
                                "SampleCount": 10,
                            }
                        ]
                    }
                else:
                    return {
                        "Datapoints": [
                            {
                                "Timestamp": datetime.utcnow(),
                                "Average": 100.0,
                                "Sum": 1000.0,
                                "Minimum": 50.0,
                                "Maximum": 150.0,
                                "SampleCount": 10,
                            }
                        ]
                    }

            mock_cw.get_metric_statistics.side_effect = get_metric_stats

            mock_client.return_value = mock_cw

            yield mock_cw

    def test_collect_model_metrics_success(self, mock_cloudwatch_model):
        """
        モデルメトリクス収集の成功テスト
        """
        result = collect_model_metrics(
            endpoint_name="test-endpoint",
            time_range_minutes=60,
            metric_period_seconds=300,
        )

        # 実行結果の確認
        assert result["status"] == "success"
        assert "metrics_info" in result

        # メトリクス情報の確認
        info = result["metrics_info"]
        assert info["endpoint_name"] == "test-endpoint"
        assert info["period_seconds"] == 300

        # 各メトリクスが存在することを確認
        assert "Invocations" in info["metrics"]
        assert "Invocation4XXErrors" in info["metrics"]
        assert "Invocation5XXErrors" in info["metrics"]
        assert "ModelSetupTime" in info["metrics"]

        # エラー率が計算されていることを確認
        assert "ErrorRates" in info["metrics"]

    def test_collect_model_metrics_with_error_rates(self, mock_cloudwatch_model):
        """
        エラー率計算のテスト
        """
        result = collect_model_metrics(endpoint_name="test-endpoint")

        info = result["metrics_info"]
        error_rates = info["metrics"]["ErrorRates"]

        assert error_rates["available"] is True
        assert error_rates["total_invocations"] == 1000.0
        assert error_rates["4xx_error_rate"] == 5.0  # 50/1000 * 100
        assert error_rates["5xx_error_rate"] == 5.0  # 50/1000 * 100
        assert error_rates["total_error_rate"] == 10.0  # 100/1000 * 100

    def test_collect_model_metrics_no_invocations(self):
        """
        呼び出しがない場合のエラー率計算テスト
        """
        with patch("boto3.client") as mock_client:
            mock_cw = Mock()

            # Invocationsがゼロ
            mock_cw.get_metric_statistics.return_value = {"Datapoints": []}

            mock_client.return_value = mock_cw

            result = collect_model_metrics(endpoint_name="test-endpoint")

            info = result["metrics_info"]
            error_rates = info["metrics"]["ErrorRates"]

            assert error_rates["available"] is False
            assert "message" in error_rates

    def test_collect_model_metrics_error(self):
        """
        CloudWatchエラーのハンドリングテスト
        個別のメトリクスエラーは警告として処理され、結果には含まれる
        """
        with patch("boto3.client") as mock_client:
            mock_cw = Mock()
            from botocore.exceptions import ClientError

            mock_cw.get_metric_statistics.side_effect = ClientError(
                {"Error": {"Code": "InvalidParameterValue", "Message": "Invalid"}},
                "get_metric_statistics",
            )

            mock_client.return_value = mock_cw

            # エラーは警告として処理され、関数は成功を返す
            result = collect_model_metrics(endpoint_name="test-endpoint")

            assert result["status"] == "success"
            assert "metrics_info" in result
            # すべてのメトリクスがエラー状態で含まれる
            for metric_name in ["Invocations", "Invocation4XXErrors", "Invocation5XXErrors"]:
                assert metric_name in result["metrics_info"]["metrics"]
                assert result["metrics_info"]["metrics"][metric_name]["available"] is False
            # エラー率も計算できない
            assert result["metrics_info"]["metrics"]["ErrorRates"]["available"] is False


class TestDetectDataDrift:
    """
    detect_data_drift関数のユニットテスト
    """

    @pytest.fixture
    def sample_data(self):
        """サンプルデータ"""
        baseline = {
            "feature1": [1.0, 2.0, 3.0, 4.0, 5.0] * 20,
            "feature2": [10.0, 20.0, 30.0, 40.0, 50.0] * 20,
        }
        # ドリフトなし（同じ分布）
        current_no_drift = {
            "feature1": [1.5, 2.5, 3.5, 4.5, 5.5] * 20,
            "feature2": [15.0, 25.0, 35.0, 45.0, 55.0] * 20,
        }
        # ドリフトあり（異なる分布）
        current_with_drift = {
            "feature1": [100.0, 200.0, 300.0, 400.0, 500.0] * 20,
            "feature2": [1000.0, 2000.0, 3000.0, 4000.0, 5000.0] * 20,
        }

        return baseline, current_no_drift, current_with_drift

    def test_detect_data_drift_no_drift(self, sample_data):
        """
        ドリフトなしの検出テスト
        """
        baseline, current_no_drift, _ = sample_data

        with patch("scipy.stats.ks_2samp") as mock_ks:
            # p値が閾値より大きい（ドリフトなし）
            mock_ks.return_value = (0.1, 0.8)

            result = detect_data_drift(
                baseline_data=baseline,
                current_data=current_no_drift,
                drift_threshold=0.05,
                method="ks_test",
            )

            assert result["status"] == "success"
            assert result["drift_info"]["overall_drift_detected"] is False
            assert result["drift_info"]["drifted_features_count"] == 0
            assert result["drift_info"]["drift_percentage"] == 0.0

    def test_detect_data_drift_with_drift(self, sample_data):
        """
        ドリフトありの検出テスト
        """
        baseline, _, current_with_drift = sample_data

        with patch("scipy.stats.ks_2samp") as mock_ks:
            # p値が閾値より小さい（ドリフトあり）
            mock_ks.return_value = (0.8, 0.001)

            result = detect_data_drift(
                baseline_data=baseline,
                current_data=current_with_drift,
                drift_threshold=0.05,
                method="ks_test",
            )

            assert result["status"] == "success"
            assert result["drift_info"]["overall_drift_detected"] is True
            assert result["drift_info"]["drifted_features_count"] == 2
            assert result["drift_info"]["drift_percentage"] == 100.0
            assert "feature1" in result["drift_info"]["drifted_features"]
            assert "feature2" in result["drift_info"]["drifted_features"]

    def test_detect_data_drift_chi_square(self, sample_data):
        """
        カイ二乗検定を使用したドリフト検出テスト
        """
        baseline, current_no_drift, _ = sample_data

        with patch("scipy.stats.chisquare") as mock_chi:
            # p値が閾値より大きい（ドリフトなし）
            mock_chi.return_value = (5.0, 0.9)

            result = detect_data_drift(
                baseline_data=baseline,
                current_data=current_no_drift,
                drift_threshold=0.05,
                method="chi_square",
            )

            assert result["status"] == "success"
            assert result["drift_info"]["method"] == "chi_square"
            assert result["drift_info"]["overall_drift_detected"] is False

    def test_detect_data_drift_empty_data(self):
        """
        空データのエラーハンドリングテスト
        """
        with pytest.raises(ValueError, match="must not be empty"):
            detect_data_drift(baseline_data={}, current_data={})

    def test_detect_data_drift_invalid_threshold(self):
        """
        無効な閾値のエラーハンドリングテスト
        """
        baseline = {"feature1": [1.0, 2.0, 3.0]}
        current = {"feature1": [4.0, 5.0, 6.0]}

        with pytest.raises(ValueError, match="drift_threshold must be between 0 and 1"):
            detect_data_drift(baseline_data=baseline, current_data=current, drift_threshold=1.5)

    def test_detect_data_drift_invalid_method(self):
        """
        無効な検定方法のエラーハンドリングテスト
        """
        baseline = {"feature1": [1.0, 2.0, 3.0]}
        current = {"feature1": [4.0, 5.0, 6.0]}

        with pytest.raises(ValueError, match="method must be"):
            detect_data_drift(baseline_data=baseline, current_data=current, method="invalid_method")

    def test_detect_data_drift_no_common_features(self):
        """
        共通の特徴量がない場合のエラーハンドリングテスト
        """
        baseline = {"feature1": [1.0, 2.0, 3.0]}
        current = {"feature2": [4.0, 5.0, 6.0]}

        with pytest.raises(ValueError, match="No common features found"):
            detect_data_drift(baseline_data=baseline, current_data=current)


class TestDetectConceptDrift:
    """
    detect_concept_drift関数のユニットテスト
    """

    @pytest.fixture
    def sample_predictions(self):
        """サンプル予測データ"""
        # 精度が良い予測（ドリフトなし）
        predictions_no_drift = [0, 1, 0, 1, 0] * 40  # 200サンプル
        actual_no_drift = [0, 1, 0, 1, 0] * 40

        # 精度が悪化した予測（ドリフトあり）
        predictions_with_drift = [0, 1, 0, 1, 0] * 20 + [1, 0, 1, 0, 1] * 20  # 後半で反転
        actual_with_drift = [0, 1, 0, 1, 0] * 40

        return predictions_no_drift, actual_no_drift, predictions_with_drift, actual_with_drift

    def test_detect_concept_drift_no_drift(self, sample_predictions):
        """
        コンセプトドリフトなしの検出テスト
        """
        predictions, actual, _, _ = sample_predictions

        result = detect_concept_drift(
            predictions=predictions,
            actual_labels=actual,
            window_size=100,
            drift_threshold=0.1,
        )

        assert result["status"] == "success"
        assert result["drift_info"]["overall_drift_detected"] is False
        assert result["drift_info"]["drifted_windows_count"] == 0
        assert result["drift_info"]["baseline"]["accuracy"] == 1.0

    def test_detect_concept_drift_with_drift(self, sample_predictions):
        """
        コンセプトドリフトありの検出テスト
        """
        _, _, predictions, actual = sample_predictions

        result = detect_concept_drift(
            predictions=predictions,
            actual_labels=actual,
            window_size=100,
            drift_threshold=0.1,
        )

        assert result["status"] == "success"
        assert result["drift_info"]["overall_drift_detected"] is True
        assert result["drift_info"]["drifted_windows_count"] > 0
        assert len(result["drift_info"]["drifted_windows"]) > 0

    def test_detect_concept_drift_with_f1_score(self, sample_predictions):
        """
        F1スコアを含むドリフト検出テスト
        """
        predictions, actual, _, _ = sample_predictions

        result = detect_concept_drift(
            predictions=predictions,
            actual_labels=actual,
            window_size=50,
        )

        assert result["status"] == "success"
        assert "f1_score" in result["drift_info"]["baseline"]
        assert "average_f1_score" in result["drift_info"]["overall_statistics"]
        assert "window_f1_scores" in result["drift_info"]

    def test_detect_concept_drift_empty_data(self):
        """
        空データのエラーハンドリングテスト
        """
        with pytest.raises(ValueError, match="must not be empty"):
            detect_concept_drift(predictions=[], actual_labels=[])

    def test_detect_concept_drift_mismatched_length(self):
        """
        予測値とラベルの長さが異なる場合のエラーハンドリングテスト
        """
        with pytest.raises(ValueError, match="must have the same length"):
            detect_concept_drift(predictions=[0, 1, 0], actual_labels=[0, 1])

    def test_detect_concept_drift_invalid_window_size(self):
        """
        無効なウィンドウサイズのエラーハンドリングテスト
        """
        predictions = [0, 1, 0, 1]
        actual = [0, 1, 0, 1]

        with pytest.raises(ValueError, match="window_size must be at least 2"):
            detect_concept_drift(predictions=predictions, actual_labels=actual, window_size=1)

    def test_detect_concept_drift_invalid_threshold(self):
        """
        無効な閾値のエラーハンドリングテスト
        """
        predictions = [0, 1, 0, 1] * 50
        actual = [0, 1, 0, 1] * 50

        with pytest.raises(ValueError, match="drift_threshold must be between 0 and 1"):
            detect_concept_drift(predictions=predictions, actual_labels=actual, drift_threshold=1.5)

    def test_detect_concept_drift_insufficient_data(self):
        """
        データが不足している場合のエラーハンドリングテスト
        """
        predictions = [0, 1, 0, 1]
        actual = [0, 1, 0, 1]

        with pytest.raises(ValueError, match="Insufficient data"):
            detect_concept_drift(predictions=predictions, actual_labels=actual, window_size=100)


class TestCreateCloudWatchAlarm:
    """
    create_cloudwatch_alarm関数のユニットテスト
    """

    @pytest.fixture
    def mock_cloudwatch_alarm(self):
        """CloudWatchアラーム用モッククライアント"""
        with patch("boto3.client") as mock_client:
            mock_cw = Mock()

            # put_metric_alarm: アラーム作成
            mock_cw.put_metric_alarm.return_value = {}

            mock_client.return_value = mock_cw

            yield mock_cw

    def test_create_cloudwatch_alarm_success(self, mock_cloudwatch_alarm):
        """
        CloudWatchアラーム作成の成功テスト
        """
        result = create_cloudwatch_alarm(
            alarm_name="test-alarm",
            endpoint_name="test-endpoint",
            metric_name="CPUUtilization",
            threshold=80.0,
            comparison_operator="GreaterThanThreshold",
            evaluation_periods=2,
            period_seconds=300,
            statistic="Average",
        )

        # 実行結果の確認
        assert result["status"] == "success"
        assert "alarm_info" in result

        # アラーム情報の確認
        info = result["alarm_info"]
        assert info["alarm_name"] == "test-alarm"
        assert info["endpoint_name"] == "test-endpoint"
        assert info["metric_name"] == "CPUUtilization"
        assert info["threshold"] == 80.0
        assert info["comparison_operator"] == "GreaterThanThreshold"
        assert info["evaluation_periods"] == 2
        assert info["period_seconds"] == 300
        assert info["statistic"] == "Average"

        # CloudWatch API呼び出しの確認
        mock_cloudwatch_alarm.put_metric_alarm.assert_called_once()

    def test_create_cloudwatch_alarm_with_actions(self, mock_cloudwatch_alarm):
        """
        アラームアクション付きのアラーム作成テスト
        """
        alarm_actions = [
            "arn:aws:sns:us-east-1:123456789012:my-topic",
            "arn:aws:sns:us-east-1:123456789012:another-topic",
        ]

        result = create_cloudwatch_alarm(
            alarm_name="test-alarm",
            endpoint_name="test-endpoint",
            metric_name="ModelLatency",
            threshold=1000.0,
            actions_enabled=True,
            alarm_actions=alarm_actions,
        )

        assert result["status"] == "success"
        assert result["alarm_info"]["alarm_actions_count"] == 2

    def test_create_cloudwatch_alarm_invalid_operator(self):
        """
        無効な比較演算子のエラーハンドリングテスト
        """
        with pytest.raises(ValueError, match="Invalid comparison_operator"):
            create_cloudwatch_alarm(
                alarm_name="test-alarm",
                endpoint_name="test-endpoint",
                metric_name="CPUUtilization",
                threshold=80.0,
                comparison_operator="InvalidOperator",
            )

    def test_create_cloudwatch_alarm_invalid_statistic(self):
        """
        無効な統計値のエラーハンドリングテスト
        """
        with pytest.raises(ValueError, match="Invalid statistic"):
            create_cloudwatch_alarm(
                alarm_name="test-alarm",
                endpoint_name="test-endpoint",
                metric_name="CPUUtilization",
                threshold=80.0,
                statistic="InvalidStatistic",
            )

    def test_create_cloudwatch_alarm_invalid_evaluation_periods(self):
        """
        無効な評価期間のエラーハンドリングテスト
        """
        with pytest.raises(ValueError, match="evaluation_periods must be at least 1"):
            create_cloudwatch_alarm(
                alarm_name="test-alarm",
                endpoint_name="test-endpoint",
                metric_name="CPUUtilization",
                threshold=80.0,
                evaluation_periods=0,
            )

    def test_create_cloudwatch_alarm_invalid_period(self):
        """
        無効な期間のエラーハンドリングテスト
        """
        with pytest.raises(ValueError, match="period_seconds must be at least 60"):
            create_cloudwatch_alarm(
                alarm_name="test-alarm",
                endpoint_name="test-endpoint",
                metric_name="CPUUtilization",
                threshold=80.0,
                period_seconds=30,
            )

    def test_create_cloudwatch_alarm_error(self):
        """
        CloudWatchエラーのハンドリングテスト
        """
        with patch("boto3.client") as mock_client:
            mock_cw = Mock()
            from botocore.exceptions import ClientError

            mock_cw.put_metric_alarm.side_effect = ClientError(
                {"Error": {"Code": "LimitExceeded", "Message": "Limit exceeded"}},
                "put_metric_alarm",
            )

            mock_client.return_value = mock_cw

            with pytest.raises(ValueError, match="Failed to create CloudWatch alarm"):
                create_cloudwatch_alarm(
                    alarm_name="test-alarm",
                    endpoint_name="test-endpoint",
                    metric_name="CPUUtilization",
                    threshold=80.0,
                )


class TestDeleteCloudWatchAlarm:
    """
    delete_cloudwatch_alarm関数のユニットテスト
    """

    @pytest.fixture
    def mock_cloudwatch_delete(self):
        """CloudWatchアラーム削除用モッククライアント"""
        with patch("boto3.client") as mock_client:
            mock_cw = Mock()

            # delete_alarms: アラーム削除
            mock_cw.delete_alarms.return_value = {}

            mock_client.return_value = mock_cw

            yield mock_cw

    def test_delete_cloudwatch_alarm_success(self, mock_cloudwatch_delete):
        """
        CloudWatchアラーム削除の成功テスト
        """
        result = delete_cloudwatch_alarm(alarm_name="test-alarm")

        # 実行結果の確認
        assert result["status"] == "success"
        assert "deletion_info" in result

        # 削除情報の確認
        info = result["deletion_info"]
        assert info["alarm_name"] == "test-alarm"

        # CloudWatch API呼び出しの確認
        mock_cloudwatch_delete.delete_alarms.assert_called_once_with(AlarmNames=["test-alarm"])

    def test_delete_cloudwatch_alarm_error(self):
        """
        CloudWatchエラーのハンドリングテスト
        """
        with patch("boto3.client") as mock_client:
            mock_cw = Mock()
            from botocore.exceptions import ClientError

            mock_cw.delete_alarms.side_effect = ClientError(
                {"Error": {"Code": "ResourceNotFound", "Message": "Not found"}},
                "delete_alarms",
            )

            mock_client.return_value = mock_cw

            with pytest.raises(ValueError, match="Failed to delete CloudWatch alarm"):
                delete_cloudwatch_alarm(alarm_name="nonexistent-alarm")


class TestGetAlarmState:
    """
    get_alarm_state関数のユニットテスト
    """

    @pytest.fixture
    def mock_cloudwatch_state(self):
        """CloudWatchアラーム状態取得用モッククライアント"""
        with patch("boto3.client") as mock_client:
            mock_cw = Mock()

            # describe_alarms: アラーム情報取得
            mock_cw.describe_alarms.return_value = {
                "MetricAlarms": [
                    {
                        "AlarmName": "test-alarm",
                        "StateValue": "OK",
                        "StateReason": "Threshold not exceeded",
                        "StateUpdatedTimestamp": datetime(2024, 1, 1, 12, 0, 0),
                        "ActionsEnabled": True,
                        "AlarmArn": "arn:aws:cloudwatch:us-east-1:123456789012:alarm:test-alarm",
                    }
                ]
            }

            mock_client.return_value = mock_cw

            yield mock_cw

    def test_get_alarm_state_success(self, mock_cloudwatch_state):
        """
        アラーム状態取得の成功テスト
        """
        result = get_alarm_state(alarm_name="test-alarm")

        # 実行結果の確認
        assert result["status"] == "success"
        assert "alarm_state" in result

        # アラーム状態の確認
        state = result["alarm_state"]
        assert state["alarm_name"] == "test-alarm"
        assert state["state_value"] == "OK"
        assert state["state_reason"] == "Threshold not exceeded"
        assert state["actions_enabled"] is True
        assert "alarm_arn" in state

        # CloudWatch API呼び出しの確認
        mock_cloudwatch_state.describe_alarms.assert_called_once_with(AlarmNames=["test-alarm"])

    def test_get_alarm_state_alarm_state(self):
        """
        ALARM状態のアラーム取得テスト
        """
        with patch("boto3.client") as mock_client:
            mock_cw = Mock()

            mock_cw.describe_alarms.return_value = {
                "MetricAlarms": [
                    {
                        "AlarmName": "test-alarm",
                        "StateValue": "ALARM",
                        "StateReason": "Threshold exceeded",
                        "StateUpdatedTimestamp": datetime(2024, 1, 1, 12, 0, 0),
                        "ActionsEnabled": True,
                        "AlarmArn": "arn:aws:cloudwatch:us-east-1:123456789012:alarm:test-alarm",
                    }
                ]
            }

            mock_client.return_value = mock_cw

            result = get_alarm_state(alarm_name="test-alarm")

            assert result["status"] == "success"
            assert result["alarm_state"]["state_value"] == "ALARM"

    def test_get_alarm_state_not_found(self):
        """
        アラームが存在しない場合のエラーハンドリングテスト
        """
        with patch("boto3.client") as mock_client:
            mock_cw = Mock()

            # アラームが存在しない
            mock_cw.describe_alarms.return_value = {"MetricAlarms": []}

            mock_client.return_value = mock_cw

            with pytest.raises(ValueError, match="Alarm not found"):
                get_alarm_state(alarm_name="nonexistent-alarm")

    def test_get_alarm_state_error(self):
        """
        CloudWatchエラーのハンドリングテスト
        """
        with patch("boto3.client") as mock_client:
            mock_cw = Mock()
            from botocore.exceptions import ClientError

            mock_cw.describe_alarms.side_effect = ClientError(
                {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}},
                "describe_alarms",
            )

            mock_client.return_value = mock_cw

            with pytest.raises(ValueError, match="Failed to get alarm state"):
                get_alarm_state(alarm_name="test-alarm")


class TestUpdateDashboard:
    """
    update_dashboard関数のユニットテスト
    """

    @pytest.fixture
    def mock_cloudwatch_dashboard(self):
        """CloudWatchダッシュボード用モッククライアント"""
        with patch("boto3.client") as mock_client:
            mock_cw = Mock()

            # put_dashboard: ダッシュボード作成/更新
            mock_cw.put_dashboard.return_value = {}

            mock_client.return_value = mock_cw

            yield mock_cw

    @pytest.fixture
    def sample_dashboard_body(self):
        """サンプルダッシュボード本体"""
        return {
            "widgets": [
                {
                    "type": "metric",
                    "properties": {
                        "metrics": [["AWS/SageMaker", "Invocations"]],
                        "period": 300,
                        "stat": "Sum",
                        "region": "us-east-1",
                        "title": "Invocations",
                    },
                }
            ]
        }

    def test_update_dashboard_success(self, mock_cloudwatch_dashboard, sample_dashboard_body):
        """
        ダッシュボード更新の成功テスト
        """
        result = update_dashboard(
            dashboard_name="test-dashboard",
            dashboard_body=sample_dashboard_body,
        )

        # 実行結果の確認
        assert result["status"] == "success"
        assert "dashboard_info" in result

        # ダッシュボード情報の確認
        info = result["dashboard_info"]
        assert info["dashboard_name"] == "test-dashboard"
        assert info["widgets_count"] == 1

        # CloudWatch API呼び出しの確認
        mock_cloudwatch_dashboard.put_dashboard.assert_called_once()

        # JSON形式でダッシュボード本体が送信されたか確認
        call_args = mock_cloudwatch_dashboard.put_dashboard.call_args
        assert call_args[1]["DashboardName"] == "test-dashboard"
        assert isinstance(call_args[1]["DashboardBody"], str)

    def test_update_dashboard_error(self, sample_dashboard_body):
        """
        CloudWatchエラーのハンドリングテスト
        """
        with patch("boto3.client") as mock_client:
            mock_cw = Mock()
            from botocore.exceptions import ClientError

            mock_cw.put_dashboard.side_effect = ClientError(
                {"Error": {"Code": "InvalidParameterValue", "Message": "Invalid"}},
                "put_dashboard",
            )

            mock_client.return_value = mock_cw

            with pytest.raises(ValueError, match="Failed to update dashboard"):
                update_dashboard(
                    dashboard_name="test-dashboard",
                    dashboard_body=sample_dashboard_body,
                )


class TestCreateMonitoringDashboard:
    """
    create_monitoring_dashboard関数のユニットテスト
    """

    @pytest.fixture
    def mock_cloudwatch_create_dashboard(self):
        """CloudWatchダッシュボード作成用モッククライアント"""
        with patch("boto3.client") as mock_client:
            mock_cw = Mock()

            # put_dashboard: ダッシュボード作成
            mock_cw.put_dashboard.return_value = {}

            mock_client.return_value = mock_cw

            yield mock_cw

    def test_create_monitoring_dashboard_success(self, mock_cloudwatch_create_dashboard):
        """
        モニタリングダッシュボード作成の成功テスト
        """
        result = create_monitoring_dashboard(
            dashboard_name="test-monitoring-dashboard",
            endpoint_name="test-endpoint",
            region="us-east-1",
        )

        # 実行結果の確認
        assert result["status"] == "success"
        assert "dashboard_info" in result

        # ダッシュボード情報の確認
        info = result["dashboard_info"]
        assert info["dashboard_name"] == "test-monitoring-dashboard"
        assert info["widgets_count"] == 5  # 5つのウィジェット

        # CloudWatch API呼び出しの確認
        mock_cloudwatch_create_dashboard.put_dashboard.assert_called_once()

    def test_create_monitoring_dashboard_different_region(self, mock_cloudwatch_create_dashboard):
        """
        異なるリージョンでのダッシュボード作成テスト
        """
        result = create_monitoring_dashboard(
            dashboard_name="test-dashboard",
            endpoint_name="test-endpoint",
            region="ap-northeast-1",
        )

        assert result["status"] == "success"

        # put_dashboardが呼ばれたことを確認
        call_args = mock_cloudwatch_create_dashboard.put_dashboard.call_args
        dashboard_body = json.loads(call_args[1]["DashboardBody"])

        # リージョンが正しく設定されているか確認
        for widget in dashboard_body["widgets"]:
            assert widget["properties"]["region"] == "ap-northeast-1"


class TestDeleteDashboard:
    """
    delete_dashboard関数のユニットテスト
    """

    @pytest.fixture
    def mock_cloudwatch_delete_dashboard(self):
        """CloudWatchダッシュボード削除用モッククライアント"""
        with patch("boto3.client") as mock_client:
            mock_cw = Mock()

            # delete_dashboards: ダッシュボード削除
            mock_cw.delete_dashboards.return_value = {}

            mock_client.return_value = mock_cw

            yield mock_cw

    def test_delete_dashboard_success(self, mock_cloudwatch_delete_dashboard):
        """
        ダッシュボード削除の成功テスト
        """
        result = delete_dashboard(dashboard_name="test-dashboard")

        # 実行結果の確認
        assert result["status"] == "success"
        assert "deletion_info" in result

        # 削除情報の確認
        info = result["deletion_info"]
        assert info["dashboard_name"] == "test-dashboard"

        # CloudWatch API呼び出しの確認
        mock_cloudwatch_delete_dashboard.delete_dashboards.assert_called_once_with(
            DashboardNames=["test-dashboard"]
        )

    def test_delete_dashboard_error(self):
        """
        CloudWatchエラーのハンドリングテスト
        """
        with patch("boto3.client") as mock_client:
            mock_cw = Mock()
            from botocore.exceptions import ClientError

            mock_cw.delete_dashboards.side_effect = ClientError(
                {"Error": {"Code": "ResourceNotFound", "Message": "Not found"}},
                "delete_dashboards",
            )

            mock_client.return_value = mock_cw

            with pytest.raises(ValueError, match="Failed to delete dashboard"):
                delete_dashboard(dashboard_name="nonexistent-dashboard")
