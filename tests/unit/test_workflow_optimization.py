"""
Workflow Optimization Capability Unit Tests

ワークフロー最適化機能の単体テスト
"""

import pytest

from mcp_server.capabilities.workflow_optimization.capability import (
    WorkflowOptimizationCapability,
)
from mcp_server.capabilities.workflow_optimization.tools import (
    analyze_model_characteristics,
    apply_optimizations,
    generate_optimization_proposal,
    retrieve_similar_model_history,
    track_optimization_history,
)


class TestWorkflowOptimizationCapability:
    """WorkflowOptimizationCapability クラスのテスト"""

    def test_initialization(self):
        """初期化テスト"""
        capability = WorkflowOptimizationCapability()
        assert capability is not None
        assert capability._tools is not None
        assert len(capability._tools) == 5

    def test_get_tools(self):
        """ツール取得テスト"""
        capability = WorkflowOptimizationCapability()
        tools = capability.get_tools()

        assert "analyze_model_characteristics" in tools
        assert "generate_optimization_proposal" in tools
        assert "retrieve_similar_model_history" in tools
        assert "apply_optimizations" in tools
        assert "track_optimization_history" in tools

    def test_get_tool_schemas(self):
        """ツールスキーマ取得テスト"""
        capability = WorkflowOptimizationCapability()
        schemas = capability.get_tool_schemas()

        assert len(schemas) == 5
        for tool_name, schema in schemas.items():
            assert "name" in schema
            assert "description" in schema
            assert "parameters" in schema


class TestAnalyzeModelCharacteristics:
    """analyze_model_characteristics ツールのテスト"""

    def test_basic_analysis(self):
        """基本的なモデル特性分析テスト"""
        model_config = {
            "algorithm": "random_forest",
            "hyperparameters": {"n_estimators": 100, "max_depth": 10},
        }

        result = analyze_model_characteristics(model_config)

        assert result["status"] == "success"
        assert "characteristics" in result
        assert result["characteristics"]["algorithm"] == "random_forest"
        assert "resource_requirements" in result["characteristics"]
        assert "estimated_training_time_minutes" in result["characteristics"]

    def test_analysis_with_dataset_info(self):
        """データセット情報付きモデル特性分析テスト"""
        model_config = {
            "algorithm": "xgboost",
            "hyperparameters": {"n_estimators": 200},
        }
        dataset_info = {
            "size": 50000,
            "num_features": 100,
            "num_classes": 3,
        }

        result = analyze_model_characteristics(model_config, dataset_info)

        assert result["status"] == "success"
        chars = result["characteristics"]
        assert "dataset_characteristics" in chars
        assert chars["dataset_characteristics"]["size"] == 50000
        assert chars["dataset_characteristics"]["size_category"] == "medium"

    def test_analysis_deep_learning(self):
        """ディープラーニングモデルの特性分析テスト"""
        model_config = {
            "algorithm": "neural_network",
            "hyperparameters": {"layers": [128, 64, 32], "epochs": 100},
        }

        result = analyze_model_characteristics(model_config)

        assert result["status"] == "success"
        chars = result["characteristics"]
        assert chars["model_category"] == "deep_learning"
        assert chars["resource_requirements"]["gpu"] is True

    def test_analysis_large_dataset(self):
        """大規模データセットの特性分析テスト"""
        model_config = {"algorithm": "gradient_boosting"}
        dataset_info = {"size": 2000000, "num_features": 500}

        result = analyze_model_characteristics(model_config, dataset_info)

        assert result["status"] == "success"
        chars = result["characteristics"]
        assert chars["dataset_characteristics"]["size_category"] == "very_large"
        assert len(chars["optimization_opportunities"]) > 0

    def test_analysis_empty_config_error(self):
        """空のmodel_configでエラーテスト"""
        with pytest.raises(ValueError, match="model_config must not be empty"):
            analyze_model_characteristics({})

    def test_analysis_invalid_config_error(self):
        """不正なmodel_configでエラーテスト"""
        with pytest.raises(ValueError, match="model_config must be a dictionary"):
            analyze_model_characteristics("invalid")


class TestGenerateOptimizationProposal:
    """generate_optimization_proposal ツールのテスト"""

    def test_basic_proposal_generation(self):
        """基本的な最適化提案生成テスト"""
        model_characteristics = {
            "algorithm": "random_forest",
            "resource_requirements": {"cpu": 4, "memory_gb": 8, "gpu": False},
            "estimated_training_time_minutes": 30,
            "optimization_opportunities": [],
        }

        result = generate_optimization_proposal(model_characteristics)

        assert result["status"] == "success"
        assert "proposal" in result
        assert "optimization_proposals" in result["proposal"]

    def test_proposal_with_constraints(self):
        """制約条件付き最適化提案生成テスト"""
        model_characteristics = {
            "algorithm": "xgboost",
            "resource_requirements": {"cpu": 4, "memory_gb": 16, "gpu": False},
            "estimated_training_time_minutes": 60,
            "optimization_opportunities": [],
        }
        constraints = {
            "max_training_time_minutes": 120,
            "max_cost_usd": 10.0,
        }

        result = generate_optimization_proposal(model_characteristics, constraints)

        assert result["status"] == "success"
        proposal = result["proposal"]
        assert "total_cost_estimate_usd" in proposal
        assert "total_time_estimate_minutes" in proposal
        assert "constraints_satisfied" in proposal

    def test_proposal_empty_characteristics_error(self):
        """空のmodel_characteristicsでエラーテスト"""
        with pytest.raises(ValueError, match="model_characteristics must not be empty"):
            generate_optimization_proposal({})

    def test_proposal_invalid_characteristics_error(self):
        """不正なmodel_characteristicsでエラーテスト"""
        with pytest.raises(ValueError, match="model_characteristics must be a dictionary"):
            generate_optimization_proposal("invalid")


class TestRetrieveSimilarModelHistory:
    """retrieve_similar_model_history ツールのテスト"""

    def test_basic_history_retrieval(self):
        """基本的な履歴取得テスト（モックデータ）"""
        result = retrieve_similar_model_history("random_forest")

        assert result["status"] == "success"
        assert "history" in result
        assert result["history"]["model_type"] == "random_forest"
        assert "records" in result["history"]
        assert "statistics" in result["history"]

    def test_history_retrieval_with_dataset_size(self):
        """データセットサイズ指定履歴取得テスト"""
        result = retrieve_similar_model_history("xgboost", dataset_size=10000)

        assert result["status"] == "success"
        history = result["history"]
        assert history["model_type"] == "xgboost"

    def test_history_retrieval_with_limit(self):
        """取得件数制限付き履歴取得テスト"""
        result = retrieve_similar_model_history("neural_network", limit=3)

        assert result["status"] == "success"
        history = result["history"]
        assert len(history["records"]) <= 3

    def test_history_retrieval_empty_model_type_error(self):
        """空のmodel_typeでエラーテスト"""
        with pytest.raises(ValueError, match="model_type must not be empty"):
            retrieve_similar_model_history("")

    def test_history_retrieval_invalid_limit_error(self):
        """不正なlimitでエラーテスト"""
        with pytest.raises(ValueError, match="limit must be between 1 and 100"):
            retrieve_similar_model_history("random_forest", limit=0)

        with pytest.raises(ValueError, match="limit must be between 1 and 100"):
            retrieve_similar_model_history("random_forest", limit=101)

    def test_history_statistics(self):
        """履歴統計情報のテスト"""
        result = retrieve_similar_model_history("random_forest")

        statistics = result["history"]["statistics"]
        assert "avg_training_time_minutes" in statistics
        assert "avg_accuracy" in statistics
        assert "avg_cost_usd" in statistics
        assert "most_common_hyperparameters" in statistics


class TestApplyOptimizations:
    """apply_optimizations ツールのテスト"""

    def test_basic_optimization_application(self):
        """基本的な最適化適用テスト"""
        optimization_proposal = {
            "optimization_proposals": [
                {
                    "type": "hyperparameter_tuning",
                    "priority": "high",
                    "description": "ハイパーパラメータチューニング",
                    "suggestions": {
                        "n_estimators": [100, 200, 300],
                        "max_depth": [10, 20, 30],
                    },
                }
            ]
        }
        target_config = {
            "algorithm": "random_forest",
            "hyperparameters": {},
        }

        result = apply_optimizations(optimization_proposal, target_config)

        assert result["status"] == "success"
        assert "optimization_result" in result
        opt_result = result["optimization_result"]
        assert "optimized_config" in opt_result
        assert "applied_optimizations" in opt_result
        assert len(opt_result["applied_optimizations"]) > 0

    def test_resource_optimization_application(self):
        """リソース最適化適用テスト"""
        optimization_proposal = {
            "optimization_proposals": [
                {
                    "type": "resource_optimization",
                    "priority": "medium",
                    "description": "GPU活用",
                    "suggestions": {
                        "instance_type": "ml.p3.2xlarge",
                        "gpu_enabled": True,
                    },
                }
            ]
        }
        target_config = {
            "algorithm": "neural_network",
        }

        result = apply_optimizations(optimization_proposal, target_config)

        assert result["status"] == "success"
        opt_config = result["optimization_result"]["optimized_config"]
        assert "resource_config" in opt_config
        assert opt_config["resource_config"]["gpu_enabled"] is True

    def test_data_optimization_application(self):
        """データ最適化適用テスト"""
        optimization_proposal = {
            "optimization_proposals": [
                {
                    "type": "data_optimization",
                    "priority": "high",
                    "description": "サンプリング戦略",
                    "suggestions": {
                        "use_sampling": True,
                        "sample_ratio": 0.7,
                    },
                }
            ]
        }
        target_config = {
            "algorithm": "xgboost",
        }

        result = apply_optimizations(optimization_proposal, target_config)

        assert result["status"] == "success"
        opt_config = result["optimization_result"]["optimized_config"]
        assert "data_config" in opt_config
        assert opt_config["data_config"]["use_sampling"] is True

    def test_algorithm_optimization_application(self):
        """アルゴリズム最適化適用テスト"""
        optimization_proposal = {
            "optimization_proposals": [
                {
                    "type": "algorithm_optimization",
                    "priority": "medium",
                    "description": "アルゴリズム変更",
                    "suggestions": {
                        "alternative_algorithms": ["xgboost", "lightgbm"],
                    },
                }
            ]
        }
        target_config = {
            "algorithm": "random_forest",
        }

        result = apply_optimizations(optimization_proposal, target_config)

        assert result["status"] == "success"
        opt_config = result["optimization_result"]["optimized_config"]
        assert opt_config["algorithm"] == "xgboost"

    def test_multiple_optimizations_application(self):
        """複数最適化の適用テスト"""
        optimization_proposal = {
            "optimization_proposals": [
                {
                    "type": "hyperparameter_tuning",
                    "priority": "high",
                    "suggestions": {"n_estimators": [100, 200, 300]},
                },
                {
                    "type": "resource_optimization",
                    "priority": "medium",
                    "suggestions": {"gpu_enabled": True},
                },
            ]
        }
        target_config = {
            "algorithm": "xgboost",
        }

        result = apply_optimizations(optimization_proposal, target_config)

        assert result["status"] == "success"
        opt_result = result["optimization_result"]
        assert opt_result["total_optimizations_applied"] == 2

    def test_config_diff_calculation(self):
        """設定差分計算テスト"""
        optimization_proposal = {
            "optimization_proposals": [
                {
                    "type": "hyperparameter_tuning",
                    "suggestions": {"n_estimators": [100]},
                }
            ]
        }
        target_config = {
            "algorithm": "random_forest",
            "hyperparameters": {"max_depth": 10},
        }

        result = apply_optimizations(optimization_proposal, target_config)

        config_diff = result["optimization_result"]["config_diff"]
        assert "added" in config_diff
        assert "modified" in config_diff
        assert "removed" in config_diff

    def test_apply_empty_proposal_error(self):
        """空の最適化提案でエラーテスト"""
        with pytest.raises(ValueError, match="optimization_proposal must not be empty"):
            apply_optimizations({}, {"algorithm": "rf"})

    def test_apply_empty_config_error(self):
        """空のターゲット設定でエラーテスト"""
        with pytest.raises(ValueError, match="target_config must not be empty"):
            apply_optimizations({"optimization_proposals": []}, {})


class TestTrackOptimizationHistory:
    """track_optimization_history ツールのテスト"""

    def test_basic_tracking(self):
        """基本的な履歴記録テスト"""
        optimization_id = "opt-12345"
        results = {
            "status": "success",
            "optimization_result": {
                "total_optimizations_applied": 3,
                "applied_optimizations": [
                    {"type": "hyperparameter_tuning"},
                    {"type": "resource_optimization"},
                    {"type": "data_optimization"},
                ],
                "config_diff": {"added": {}, "modified": {}, "removed": {}},
            },
        }

        result = track_optimization_history(optimization_id, results)

        assert result["status"] == "success"
        assert "tracking_info" in result
        tracking = result["tracking_info"]
        assert tracking["optimization_id"] == optimization_id
        assert "timestamp" in tracking
        assert "metrics" in tracking

    def test_tracking_metrics_extraction(self):
        """メトリクス抽出テスト"""
        optimization_id = "opt-67890"
        results = {
            "status": "success",
            "optimization_result": {
                "total_optimizations_applied": 2,
                "applied_optimizations": [
                    {"type": "hyperparameter_tuning"},
                    {"type": "hyperparameter_tuning"},
                ],
                "config_diff": {
                    "added": {"key1": "value1"},
                    "modified": {"key2": {"old": "v1", "new": "v2"}},
                    "removed": {},
                },
            },
        }

        result = track_optimization_history(optimization_id, results)

        metrics = result["tracking_info"]["metrics"]
        assert metrics["total_optimizations_applied"] == 2
        assert metrics["optimization_types"]["hyperparameter_tuning"] == 2
        assert metrics["config_changes"]["added"] == 1
        assert metrics["config_changes"]["modified"] == 1

    def test_tracking_empty_id_error(self):
        """空のoptimization_idでエラーテスト"""
        with pytest.raises(ValueError, match="optimization_id must not be empty"):
            track_optimization_history("", {"status": "success"})

    def test_tracking_empty_results_error(self):
        """空のresultsでエラーテスト"""
        with pytest.raises(ValueError, match="results must not be empty"):
            track_optimization_history("opt-12345", {})

    def test_tracking_invalid_results_error(self):
        """不正なresultsでエラーテスト"""
        with pytest.raises(ValueError, match="results must be a dictionary"):
            track_optimization_history("opt-12345", "invalid")


class TestIntegrationWorkflow:
    """ワークフロー統合テスト"""

    def test_full_optimization_workflow(self):
        """完全な最適化ワークフローテスト"""
        # Step 1: モデル特性分析
        model_config = {
            "algorithm": "random_forest",
            "hyperparameters": {"n_estimators": 50},
        }
        dataset_info = {"size": 100000, "num_features": 50}

        analysis_result = analyze_model_characteristics(model_config, dataset_info)
        assert analysis_result["status"] == "success"

        # Step 2: 類似モデル履歴取得
        history_result = retrieve_similar_model_history("random_forest", dataset_size=100000)
        assert history_result["status"] == "success"

        # Step 3: 最適化提案生成
        proposal_result = generate_optimization_proposal(
            analysis_result["characteristics"],
            constraints={"max_training_time_minutes": 60},
        )
        assert proposal_result["status"] == "success"

        # Step 4: 最適化適用
        if proposal_result["proposal"]["optimization_proposals"]:
            apply_result = apply_optimizations(
                proposal_result["proposal"],
                model_config,
            )
            assert apply_result["status"] == "success"

            # Step 5: 履歴記録
            track_result = track_optimization_history(
                "workflow-test-001",
                apply_result,
            )
            assert track_result["status"] == "success"
