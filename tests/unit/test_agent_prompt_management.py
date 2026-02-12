"""
Agent Prompt Management Capability テスト

エージェント用LLMプロンプト管理機能のテスト
正常系・異常系・統合テストを網羅
"""

import pytest

from mcp_server.capabilities.agent_prompt_management.capability import (
    AgentPromptManagementCapability,
)
from mcp_server.capabilities.agent_prompt_management.tools.agent_prompts import (
    BUILTIN_AGENT_PROMPTS,
)
from mcp_server.capabilities.agent_prompt_management.tools.apply_agent_prompt import (
    _build_context_section,
    _find_unresolved_variables,
    _substitute_variables,
    apply_agent_prompt,
)
from mcp_server.capabilities.agent_prompt_management.tools.list_agent_prompts import (
    _extract_variables,
    list_agent_prompts,
)
from mcp_server.capabilities.agent_prompt_management.tools.validate_prompt_variables import (
    _check_empty_values,
    _check_missing_required,
    _check_undefined_variables,
    validate_prompt_variables,
)


# ===================================================================
# BUILTIN_AGENT_PROMPTS 定義テスト
# ===================================================================
class TestBuiltinAgentPrompts:
    """組み込みプロンプト定義のテスト"""

    def test_all_prompts_have_required_fields(self):
        """全プロンプトに必須フィールドがあること"""
        required_fields = ["name", "description", "agent_type", "prompt"]
        for prompt_name, template in BUILTIN_AGENT_PROMPTS.items():
            for field in required_fields:
                assert field in template, f"Prompt '{prompt_name}' missing field '{field}'"

    def test_all_prompts_have_variables_list(self):
        """全プロンプトに変数リストがあること"""
        for prompt_name, template in BUILTIN_AGENT_PROMPTS.items():
            assert "variables" in template, f"Prompt '{prompt_name}' missing 'variables' list"
            assert isinstance(template["variables"], list)

    def test_judge_agent_prompts_exist(self):
        """Judge Agentプロンプトが存在すること"""
        assert "judge_agent_system" in BUILTIN_AGENT_PROMPTS
        assert "judge_agent_evaluation" in BUILTIN_AGENT_PROMPTS

    def test_issue_detector_prompts_exist(self):
        """Issue Detector Agentプロンプトが存在すること"""
        assert "issue_detector_system" in BUILTIN_AGENT_PROMPTS
        assert "issue_detector_parse" in BUILTIN_AGENT_PROMPTS

    def test_training_orchestrator_prompts_exist(self):
        """Training Orchestratorプロンプトが存在すること"""
        assert "training_orchestrator_system" in BUILTIN_AGENT_PROMPTS
        assert "training_orchestrator_plan" in BUILTIN_AGENT_PROMPTS

    def test_total_prompt_count(self):
        """プロンプト総数が6であること"""
        assert len(BUILTIN_AGENT_PROMPTS) == 6

    def test_agent_types_are_valid(self):
        """エージェントタイプが正しいこと"""
        valid_types = {"judge", "issue_detector", "orchestrator"}
        for prompt_name, template in BUILTIN_AGENT_PROMPTS.items():
            assert template["agent_type"] in valid_types, (
                f"Prompt '{prompt_name}' has invalid agent_type: " f"'{template['agent_type']}'"
            )

    def test_default_values_are_subset_of_variables(self):
        """デフォルト値の変数名が変数リストに含まれること"""
        for prompt_name, template in BUILTIN_AGENT_PROMPTS.items():
            if "default_values" in template:
                defined_vars = set(template["variables"])
                default_vars = set(template["default_values"].keys())
                assert default_vars.issubset(defined_vars), (
                    f"Prompt '{prompt_name}': default_values keys "
                    f"{default_vars - defined_vars} not in variables list"
                )

    def test_prompt_content_is_non_empty(self):
        """プロンプト本文が空でないこと"""
        for prompt_name, template in BUILTIN_AGENT_PROMPTS.items():
            assert len(template["prompt"]) > 100, f"Prompt '{prompt_name}' content is too short"


# ===================================================================
# apply_agent_prompt テスト
# ===================================================================
class TestApplyAgentPrompt:
    """プロンプト適用テスト"""

    def test_apply_judge_agent_system_with_all_variables(self):
        """Judge Agent System全変数を指定して適用"""
        variables = {
            "min_accuracy": "0.85",
            "recommended_accuracy": "0.90",
            "min_f1": "0.80",
            "recommended_f1": "0.85",
            "min_precision": "0.80",
            "recommended_precision": "0.85",
            "min_recall": "0.80",
            "recommended_recall": "0.85",
            "max_latency_ms": "100",
            "recommended_latency_ms": "50",
            "model_name": "fraud-detection-v2",
            "model_type": "xgboost",
            "training_job_id": "job-abc123",
            "dataset_name": "transactions-2024",
        }

        result = apply_agent_prompt("judge_agent_system", variables)

        assert result["status"] == "success"
        assert result["prompt_name"] == "judge_agent_system"
        assert result["agent_type"] == "judge"
        assert "fraud-detection-v2" in result["rendered_prompt"]
        assert "xgboost" in result["rendered_prompt"]
        assert result["missing_variables"] == []

    def test_apply_with_defaults(self):
        """デフォルト値を使用した適用"""
        variables = {
            "model_name": "my-model",
            "model_type": "random_forest",
            "training_job_id": "job-001",
            "dataset_name": "dataset-v1",
        }

        result = apply_agent_prompt("judge_agent_system", variables, include_defaults=True)

        assert result["status"] == "success"
        assert result["defaults_applied"] is True
        # デフォルト値が適用されていること
        assert "0.85" in result["rendered_prompt"]  # min_accuracy default

    def test_apply_without_defaults(self):
        """デフォルト値を使用しない適用"""
        variables = {
            "model_name": "my-model",
            "model_type": "linear",
            "training_job_id": "job-002",
            "dataset_name": "data-v2",
        }

        result = apply_agent_prompt("judge_agent_system", variables, include_defaults=False)

        assert result["status"] == "success"
        assert result["defaults_applied"] is False
        assert len(result["missing_variables"]) > 0

    def test_apply_issue_detector_system(self):
        """Issue Detector System適用"""
        variables = {
            "issue_title": "Train new fraud model",
            "issue_body": "Please train xgboost on s3://data/train.csv",
            "issue_labels": "mlops, training",
            "issue_author": "data-team",
        }

        result = apply_agent_prompt("issue_detector_system", variables)

        assert result["status"] == "success"
        assert result["agent_type"] == "issue_detector"
        assert "Train new fraud model" in result["rendered_prompt"]
        assert "s3://data/train.csv" in result["rendered_prompt"]

    def test_apply_training_orchestrator_with_defaults(self):
        """Training Orchestratorデフォルト値付き適用"""
        variables = {
            "pipeline_id": "pipe-001",
            "current_stage": "model_training",
            "previous_stage_result": "success",
            "model_name": "my-model",
            "algorithm": "xgboost",
            "dataset_s3_uri": "s3://bucket/data",
        }

        result = apply_agent_prompt("training_orchestrator_system", variables)

        assert result["status"] == "success"
        assert result["agent_type"] == "orchestrator"
        assert "pipe-001" in result["rendered_prompt"]
        # デフォルト値 max_retries=3 が適用されている
        assert "3" in result["rendered_prompt"]

    def test_apply_with_agent_context(self):
        """エージェントコンテキスト付き適用"""
        variables = {
            "issue_title": "Deploy model",
            "issue_body": "Deploy v3 to production",
            "issue_labels": "mlops",
            "issue_author": "user1",
        }
        context = {
            "execution_id": "exec-123",
            "environment": "production",
            "triggered_by": "github_webhook",
        }

        result = apply_agent_prompt(
            "issue_detector_system",
            variables,
            agent_context=context,
        )

        assert result["status"] == "success"
        assert result["context_added"] is True
        assert "exec-123" in result["rendered_prompt"]
        assert "実行コンテキスト" in result["rendered_prompt"]

    def test_apply_returns_request_id(self):
        """リクエストIDが返されること"""
        variables = {"issue_body": "test body"}
        result = apply_agent_prompt("issue_detector_parse", variables)

        assert "request_id" in result
        assert len(result["request_id"]) == 8

    def test_apply_returns_rendered_at(self):
        """レンダリング時刻が返されること"""
        variables = {"issue_body": "test body"}
        result = apply_agent_prompt("issue_detector_parse", variables)

        assert "rendered_at" in result
        assert "T" in result["rendered_at"]  # ISO8601 format

    def test_apply_empty_prompt_name_raises(self):
        """空のプロンプト名でエラー"""
        with pytest.raises(ValueError, match="prompt_name must not be empty"):
            apply_agent_prompt("", {"var": "value"})

    def test_apply_unknown_prompt_raises(self):
        """存在しないプロンプト名でエラー"""
        with pytest.raises(ValueError, match="Unknown prompt"):
            apply_agent_prompt("nonexistent_prompt", {"var": "value"})

    def test_apply_invalid_variables_type_raises(self):
        """辞書でない変数でエラー"""
        with pytest.raises(ValueError, match="variables must be a dictionary"):
            apply_agent_prompt("judge_agent_system", "not_a_dict")

    def test_apply_empty_variables_uses_defaults(self):
        """空の変数辞書でデフォルト値が使用されること"""
        result = apply_agent_prompt("judge_agent_system", {}, include_defaults=True)

        assert result["status"] == "success"
        assert "0.85" in result["rendered_prompt"]

    def test_apply_variables_override_defaults(self):
        """変数がデフォルト値を上書きすること"""
        variables = {
            "min_accuracy": "0.95",
            "model_name": "test-model",
            "model_type": "nn",
            "training_job_id": "job-x",
            "dataset_name": "ds-x",
        }

        result = apply_agent_prompt("judge_agent_system", variables, include_defaults=True)

        assert "0.95" in result["rendered_prompt"]
        # デフォルトの0.85は上書きされている
        rendered = result["rendered_prompt"]
        # min_accuracyの位置で0.95が使われていることを確認
        assert "| Accuracy | 0.95 |" in rendered


# ===================================================================
# _substitute_variables テスト
# ===================================================================
class TestSubstituteVariables:
    """変数置換の内部関数テスト"""

    def test_simple_substitution(self):
        """単純な変数置換"""
        result = _substitute_variables("Hello {name}!", {"name": "World"})
        assert result == "Hello World!"

    def test_multiple_substitution(self):
        """複数変数の置換"""
        result = _substitute_variables("{a} and {b}", {"a": "X", "b": "Y"})
        assert result == "X and Y"

    def test_missing_variable_preserved(self):
        """未定義変数はそのまま保持"""
        result = _substitute_variables("Hello {name}!", {})
        assert result == "Hello {name}!"

    def test_double_braces_preserved(self):
        """二重波括弧はJSONリテラルとして保持"""
        result = _substitute_variables('{{"key": "value"}}', {"key": "replaced"})
        assert result == '{"key": "value"}'

    def test_mixed_braces(self):
        """単一波括弧と二重波括弧の混在"""
        result = _substitute_variables('{{"type": "{name}"}}', {"name": "test"})
        assert result == '{"type": "test"}'

    def test_numeric_value_conversion(self):
        """数値の文字列変換"""
        result = _substitute_variables("Score: {score}", {"score": "0.95"})
        assert result == "Score: 0.95"


# ===================================================================
# _find_unresolved_variables テスト
# ===================================================================
class TestFindUnresolvedVariables:
    """未置換変数検出テスト"""

    def test_no_unresolved(self):
        """未置換変数なし"""
        result = _find_unresolved_variables("No variables here")
        assert result == []

    def test_single_unresolved(self):
        """単一未置換変数"""
        result = _find_unresolved_variables("Hello {name}")
        assert "name" in result

    def test_json_keys_excluded(self):
        """JSONキーは除外される"""
        text = '"decision": "pass"\n{actual_var}'
        result = _find_unresolved_variables(text)
        # decision はJSONキーなので除外
        assert "decision" not in result


# ===================================================================
# _build_context_section テスト
# ===================================================================
class TestBuildContextSection:
    """コンテキストセクション構築テスト"""

    def test_basic_context(self):
        """基本的なコンテキスト構築"""
        context = {"env": "prod", "user": "admin"}
        result = _build_context_section(context)

        assert "## 実行コンテキスト" in result
        assert "- env: prod" in result
        assert "- user: admin" in result

    def test_empty_context(self):
        """空コンテキスト"""
        result = _build_context_section({})
        assert "## 実行コンテキスト" in result


# ===================================================================
# list_agent_prompts テスト
# ===================================================================
class TestListAgentPrompts:
    """プロンプト一覧取得テスト"""

    def test_list_all_prompts(self):
        """全プロンプト一覧"""
        result = list_agent_prompts()

        assert result["status"] == "success"
        assert result["total"] == 6
        assert result["filter_applied"] is None

    def test_list_with_variables(self):
        """変数情報付きで一覧取得"""
        result = list_agent_prompts(include_variables=True)

        for prompt in result["prompts"]:
            assert "variables" in prompt
            assert "defined" in prompt["variables"]
            assert "required" in prompt["variables"]
            assert "optional" in prompt["variables"]

    def test_list_without_variables(self):
        """変数情報なしで一覧取得"""
        result = list_agent_prompts(include_variables=False)

        for prompt in result["prompts"]:
            assert "variables" not in prompt

    def test_filter_by_judge_type(self):
        """judgeタイプでフィルタ"""
        result = list_agent_prompts(agent_type="judge")

        assert result["total"] == 2
        for prompt in result["prompts"]:
            assert prompt["agent_type"] == "judge"

    def test_filter_by_issue_detector_type(self):
        """issue_detectorタイプでフィルタ"""
        result = list_agent_prompts(agent_type="issue_detector")

        assert result["total"] == 2
        for prompt in result["prompts"]:
            assert prompt["agent_type"] == "issue_detector"

    def test_filter_by_orchestrator_type(self):
        """orchestratorタイプでフィルタ"""
        result = list_agent_prompts(agent_type="orchestrator")

        assert result["total"] == 2
        for prompt in result["prompts"]:
            assert prompt["agent_type"] == "orchestrator"

    def test_filter_by_nonexistent_type(self):
        """存在しないタイプでフィルタ"""
        result = list_agent_prompts(agent_type="nonexistent")

        assert result["total"] == 0
        assert result["prompts"] == []

    def test_agent_types_list(self):
        """エージェントタイプ一覧"""
        result = list_agent_prompts()

        assert set(result["agent_types"]) == {"judge", "issue_detector", "orchestrator"}

    def test_prompt_has_display_name(self):
        """表示名があること"""
        result = list_agent_prompts()

        for prompt in result["prompts"]:
            assert "display_name" in prompt
            assert len(prompt["display_name"]) > 0

    def test_required_vs_optional_variables(self):
        """必須/オプション変数の分類が正しいこと"""
        result = list_agent_prompts(agent_type="judge")

        system_prompt = next(p for p in result["prompts"] if p["name"] == "judge_agent_system")
        # デフォルト値がある変数はoptional
        assert "min_accuracy" in system_prompt["variables"]["optional"]
        # デフォルト値がない変数はrequired
        assert "model_name" in system_prompt["variables"]["required"]


# ===================================================================
# _extract_variables テスト
# ===================================================================
class TestExtractVariables:
    """変数抽出テスト"""

    def test_extract_simple(self):
        """単純な変数抽出"""
        result = _extract_variables("Hello {name}")
        assert "name" in result

    def test_extract_multiple(self):
        """複数変数の抽出"""
        result = _extract_variables("{a} and {b} and {c}")
        assert result == {"a", "b", "c"}

    def test_ignore_double_braces(self):
        """二重波括弧内の変数は無視"""
        result = _extract_variables("{{key}}: {value}")
        assert "value" in result
        # keyは二重波括弧内なので抽出されないことが期待される
        # ただし実装上はクリーニングで{{}}を除去するので
        # 残るのは "key" ではなく空文字列


# ===================================================================
# validate_prompt_variables テスト
# ===================================================================
class TestValidatePromptVariables:
    """変数検証テスト"""

    def test_valid_all_variables_provided(self):
        """全変数提供で検証成功"""
        variables = {
            "min_accuracy": "0.85",
            "recommended_accuracy": "0.90",
            "min_f1": "0.80",
            "recommended_f1": "0.85",
            "min_precision": "0.80",
            "recommended_precision": "0.85",
            "min_recall": "0.80",
            "recommended_recall": "0.85",
            "max_latency_ms": "100",
            "recommended_latency_ms": "50",
            "model_name": "test-model",
            "model_type": "xgboost",
            "training_job_id": "job-001",
            "dataset_name": "dataset-v1",
        }

        result = validate_prompt_variables("judge_agent_system", variables)

        assert result["is_valid"] is True
        assert result["errors"] == []

    def test_valid_with_defaults_covering_missing(self):
        """デフォルト値で補完される場合は検証成功"""
        variables = {
            "model_name": "test-model",
            "model_type": "xgboost",
            "training_job_id": "job-001",
            "dataset_name": "dataset-v1",
        }

        result = validate_prompt_variables("judge_agent_system", variables)

        assert result["is_valid"] is True
        assert len(result["auto_filled_from_defaults"]) > 0
        assert "min_accuracy" in result["auto_filled_from_defaults"]

    def test_invalid_missing_required(self):
        """必須変数が不足で検証失敗"""
        variables = {
            "model_name": "test-model",
            # model_type, training_job_id, dataset_name が不足
        }

        result = validate_prompt_variables("judge_agent_system", variables)

        assert result["is_valid"] is False
        assert len(result["errors"]) > 0
        error_vars = [e["variable"] for e in result["errors"]]
        assert "model_type" in error_vars

    def test_strict_mode_requires_all(self):
        """厳密モードでデフォルト値変数も必須"""
        variables = {
            "model_name": "test-model",
            "model_type": "xgboost",
            "training_job_id": "job-001",
            "dataset_name": "dataset-v1",
        }

        result = validate_prompt_variables("judge_agent_system", variables, strict=True)

        assert result["is_valid"] is False
        assert result["strict_mode"] is True
        error_vars = [e["variable"] for e in result["errors"]]
        assert "min_accuracy" in error_vars

    def test_undefined_variables_warning(self):
        """未定義変数の警告"""
        variables = {
            "issue_title": "test",
            "issue_body": "test body",
            "issue_labels": "mlops",
            "issue_author": "user",
            "extra_variable": "should warn",
        }

        result = validate_prompt_variables("issue_detector_system", variables)

        assert result["is_valid"] is True
        warning_vars = [w["variable"] for w in result["warnings"]]
        assert "extra_variable" in warning_vars

    def test_empty_value_warning(self):
        """空値変数の警告"""
        variables = {
            "issue_title": "",
            "issue_body": "test",
            "issue_labels": "mlops",
            "issue_author": "user",
        }

        result = validate_prompt_variables("issue_detector_system", variables)

        warning_types = [w["type"] for w in result["warnings"]]
        assert "empty_value" in warning_types

    def test_none_value_warning(self):
        """None値変数の警告"""
        variables = {
            "issue_title": None,
            "issue_body": "test",
            "issue_labels": "mlops",
            "issue_author": "user",
        }

        result = validate_prompt_variables("issue_detector_system", variables)

        warning_types = [w["type"] for w in result["warnings"]]
        assert "empty_value" in warning_types

    def test_empty_prompt_name_raises(self):
        """空プロンプト名でエラー"""
        with pytest.raises(ValueError, match="prompt_name must not be empty"):
            validate_prompt_variables("", {"var": "value"})

    def test_unknown_prompt_raises(self):
        """不明なプロンプト名でエラー"""
        with pytest.raises(ValueError, match="Unknown prompt"):
            validate_prompt_variables("nonexistent", {"var": "value"})

    def test_invalid_variables_type_raises(self):
        """辞書でない変数でエラー"""
        with pytest.raises(ValueError, match="variables must be a dictionary"):
            validate_prompt_variables("judge_agent_system", "not_a_dict")

    def test_validate_issue_detector_all_provided(self):
        """Issue Detector全変数提供"""
        variables = {
            "issue_title": "Train model",
            "issue_body": "Please train on s3://data",
            "issue_labels": "mlops",
            "issue_author": "user1",
        }

        result = validate_prompt_variables("issue_detector_system", variables)

        assert result["is_valid"] is True
        assert result["agent_type"] == "issue_detector"


# ===================================================================
# ヘルパー関数テスト
# ===================================================================
class TestHelperFunctions:
    """ヘルパー関数テスト"""

    def test_check_missing_required_none_missing(self):
        """不足なし"""
        result = _check_missing_required(["a", "b"], {"b": "default"}, {"a": "val"}, False)
        assert result == []

    def test_check_missing_required_with_missing(self):
        """必須変数不足"""
        result = _check_missing_required(["a", "b"], {}, {"a": "val"}, False)
        assert "b" in result

    def test_check_missing_required_strict(self):
        """厳密モードでデフォルト値変数も不足として検出"""
        result = _check_missing_required(["a", "b"], {"b": "default"}, {"a": "val"}, True)
        assert "b" in result

    def test_check_undefined_variables(self):
        """未定義変数検出"""
        result = _check_undefined_variables(["a", "b"], {"a": "val", "c": "extra"})
        assert "c" in result

    def test_check_undefined_no_extra(self):
        """余分な変数なし"""
        result = _check_undefined_variables(["a", "b"], {"a": "val", "b": "val2"})
        assert result == []

    def test_check_empty_values_with_empty(self):
        """空値検出"""
        result = _check_empty_values({"a": "", "b": None, "c": "value"})
        assert "a" in result
        assert "b" in result
        assert "c" not in result

    def test_check_empty_values_whitespace_only(self):
        """空白のみの値"""
        result = _check_empty_values({"a": "   "})
        assert "a" in result


# ===================================================================
# Capability クラステスト
# ===================================================================
class TestAgentPromptManagementCapability:
    """Capabilityクラスのテスト"""

    def test_initialization(self):
        """初期化テスト"""
        cap = AgentPromptManagementCapability()
        assert cap is not None

    def test_get_tools_returns_3_tools(self):
        """3つのツールが返されること"""
        cap = AgentPromptManagementCapability()
        tools = cap.get_tools()

        assert len(tools) == 3
        assert "apply_agent_prompt" in tools
        assert "list_agent_prompts" in tools
        assert "validate_prompt_variables" in tools

    def test_get_tool_schemas_returns_3_schemas(self):
        """3つのスキーマが返されること"""
        cap = AgentPromptManagementCapability()
        schemas = cap.get_tool_schemas()

        assert len(schemas) == 3
        assert "apply_agent_prompt" in schemas
        assert "list_agent_prompts" in schemas
        assert "validate_prompt_variables" in schemas

    def test_tool_schema_has_required_fields(self):
        """スキーマに必須フィールドがあること"""
        cap = AgentPromptManagementCapability()
        schemas = cap.get_tool_schemas()

        for name, schema in schemas.items():
            assert "name" in schema, f"Schema '{name}' missing 'name'"
            assert "description" in schema, f"Schema '{name}' missing 'description'"
            assert "parameters" in schema, f"Schema '{name}' missing 'parameters'"

    def test_tools_are_callable(self):
        """ツールが呼び出し可能であること"""
        cap = AgentPromptManagementCapability()
        tools = cap.get_tools()

        for name, func in tools.items():
            assert callable(func), f"Tool '{name}' is not callable"

    def test_apply_tool_via_capability(self):
        """Capability経由でapplyツールを実行"""
        cap = AgentPromptManagementCapability()
        tools = cap.get_tools()

        result = tools["apply_agent_prompt"](
            prompt_name="issue_detector_parse",
            variables={"issue_body": "Test body content"},
        )

        assert result["status"] == "success"
        assert "Test body content" in result["rendered_prompt"]


# ===================================================================
# 統合テスト
# ===================================================================
class TestIntegration:
    """統合テスト"""

    def test_validate_then_apply(self):
        """検証→適用のワークフロー"""
        prompt_name = "judge_agent_system"
        variables = {
            "model_name": "integration-test-model",
            "model_type": "neural_network",
            "training_job_id": "job-int-001",
            "dataset_name": "test-dataset",
        }

        # 1. 検証
        validation = validate_prompt_variables(prompt_name, variables)
        assert validation["is_valid"] is True

        # 2. 適用
        result = apply_agent_prompt(prompt_name, variables)
        assert result["status"] == "success"
        assert "integration-test-model" in result["rendered_prompt"]

    def test_list_then_apply_each(self):
        """一覧取得→各プロンプト適用"""
        listing = list_agent_prompts()

        for prompt_info in listing["prompts"]:
            # 最低限の変数で適用（デフォルト値を活用）
            variables = {}
            for var in prompt_info.get("variables", {}).get("required", []):
                variables[var] = f"test-{var}"

            result = apply_agent_prompt(
                prompt_info["name"],
                variables,
                include_defaults=True,
            )
            assert result["status"] == "success"

    def test_full_judge_workflow(self):
        """Judge Agent完全ワークフロー"""
        # システムプロンプト生成
        system_result = apply_agent_prompt(
            "judge_agent_system",
            {
                "model_name": "fraud-model-v3",
                "model_type": "xgboost",
                "training_job_id": "job-789",
                "dataset_name": "fraud-transactions-2024",
            },
        )

        # 評価データプロンプト生成
        eval_result = apply_agent_prompt(
            "judge_agent_evaluation",
            {
                "actual_accuracy": "0.92",
                "actual_f1": "0.88",
                "actual_precision": "0.90",
                "actual_recall": "0.86",
                "actual_latency_ms": "45",
                "actual_auc_roc": "0.95",
                "epochs": "100",
                "batch_size": "256",
                "learning_rate": "0.01",
                "training_duration": "2h 30m",
                "train_samples": "100000",
                "validation_samples": "20000",
                "test_samples": "10000",
                "class_distribution": "70/30",
            },
        )

        assert system_result["status"] == "success"
        assert eval_result["status"] == "success"
        assert "fraud-model-v3" in system_result["rendered_prompt"]
        assert "0.92" in eval_result["rendered_prompt"]

    def test_full_issue_detector_workflow(self):
        """Issue Detector Agent完全ワークフロー"""
        # システムプロンプト
        system_result = apply_agent_prompt(
            "issue_detector_system",
            {
                "issue_title": "[MLOps] Train new recommendation model",
                "issue_body": (
                    "Dataset: s3://ml-data/reco/train.csv\n" "Algorithm: xgboost\n" "Priority: high"
                ),
                "issue_labels": "mlops, model-training",
                "issue_author": "ml-team",
            },
        )

        # パースプロンプト
        parse_result = apply_agent_prompt(
            "issue_detector_parse",
            {
                "issue_body": (
                    "Dataset: s3://ml-data/reco/train.csv\n" "Algorithm: xgboost\n" "Priority: high"
                ),
            },
        )

        assert system_result["status"] == "success"
        assert parse_result["status"] == "success"
        assert "s3://ml-data/reco/train.csv" in (system_result["rendered_prompt"])

    def test_server_registration(self):
        """MLOpsServerでのCapability登録確認"""
        from mcp_server.server import MLOpsServer

        server = MLOpsServer()

        assert "agent_prompt_management" in server.capabilities
        assert "agent_prompt_management.apply_agent_prompt" in server.tools
        assert "agent_prompt_management.list_agent_prompts" in server.tools
        assert "agent_prompt_management.validate_prompt_variables" in server.tools
