"""
Parse Issue Config Tool

Issue本文のYAML/JSON設定パースツール
"""

import json
import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def parse_issue_config(
    issue_body: str,
    config_format: str = "auto",
) -> Dict[str, Any]:
    """
    Issue本文からYAML/JSON設定をパース

    Args:
        issue_body: Issue本文
        config_format: 設定フォーマット（auto, yaml, json）

    Returns:
        パースされた設定辞書
    """
    logger.info("Parsing issue config")

    # パラメータ検証
    if not issue_body:
        raise ValueError("issue_body must not be empty")

    if config_format not in ["auto", "yaml", "json"]:
        raise ValueError("config_format must be 'auto', 'yaml', or 'json'")

    try:
        # コードブロックを抽出
        config_blocks = _extract_config_blocks(issue_body)

        if not config_blocks:
            logger.warning("No config blocks found in issue body")
            return {
                "status": "warning",
                "message": "No configuration blocks found in issue body",
                "config": None,
                "parse_result": {
                    "found_blocks": 0,
                    "parsed_configs": [],
                },
            }

        # 設定をパース
        parsed_configs = []
        for block in config_blocks:
            block_format = block.get("format", "unknown")

            # フォーマット指定がある場合はフィルタリング
            if config_format != "auto" and block_format != config_format:
                continue

            try:
                config = _parse_config_block(block)
                if config:
                    parsed_configs.append(
                        {
                            "format": block_format,
                            "config": config,
                            "block_type": block.get("block_type", "unknown"),
                        }
                    )
            except Exception as e:
                logger.warning(f"Failed to parse config block: {e}")
                parsed_configs.append(
                    {
                        "format": block_format,
                        "config": None,
                        "error": str(e),
                        "block_type": block.get("block_type", "unknown"),
                    }
                )

        # メイン設定を抽出（最初の有効な設定）
        main_config = None
        for pc in parsed_configs:
            if pc.get("config") is not None:
                main_config = pc["config"]
                break

        # 設定の正規化
        if main_config:
            normalized_config = _normalize_config(main_config)
        else:
            normalized_config = None

        logger.info(f"Parsed {len(parsed_configs)} config blocks")

        return {
            "status": "success" if main_config else "warning",
            "message": f"Parsed {len(parsed_configs)} configuration blocks",
            "config": normalized_config,
            "parse_result": {
                "found_blocks": len(config_blocks),
                "parsed_configs": parsed_configs,
                "main_config": main_config,
            },
        }

    except Exception as e:
        logger.error(f"Issue config parse error: {e}")
        raise ValueError(f"Failed to parse issue config: {e}")


def _extract_config_blocks(body: str) -> List[Dict[str, Any]]:
    """Issue本文からコードブロックを抽出"""
    blocks = []

    # YAMLブロックの抽出
    yaml_pattern = r"```ya?ml\s*\n(.*?)```"
    yaml_matches = re.findall(yaml_pattern, body, re.DOTALL | re.IGNORECASE)
    for match in yaml_matches:
        blocks.append(
            {
                "format": "yaml",
                "content": match.strip(),
                "block_type": "fenced_code",
            }
        )

    # JSONブロックの抽出
    json_pattern = r"```json\s*\n(.*?)```"
    json_matches = re.findall(json_pattern, body, re.DOTALL | re.IGNORECASE)
    for match in json_matches:
        blocks.append(
            {
                "format": "json",
                "content": match.strip(),
                "block_type": "fenced_code",
            }
        )

    # インラインJSONの検出（{}で囲まれた部分）
    inline_json_pattern = r"(?<!`)\{[^`]*?\"[^`]*?\}(?!`)"
    inline_matches = re.findall(inline_json_pattern, body, re.DOTALL)
    for match in inline_matches:
        # 既にパースされたブロックと重複しないかチェック
        if match.strip() not in [b["content"] for b in blocks]:
            blocks.append(
                {
                    "format": "json",
                    "content": match.strip(),
                    "block_type": "inline",
                }
            )

    return blocks


def _parse_config_block(block: Dict[str, Any]) -> Dict[str, Any]:
    """設定ブロックをパース"""
    content = block.get("content", "")
    fmt = block.get("format", "unknown")

    if fmt == "yaml":
        return _parse_yaml(content)
    elif fmt == "json":
        return _parse_json(content)
    else:
        # 自動検出
        try:
            return _parse_json(content)
        except Exception:
            return _parse_yaml(content)


def _parse_yaml(content: str) -> Dict[str, Any]:
    """YAML文字列をパース"""
    try:
        import yaml

        return yaml.safe_load(content)
    except ImportError:
        # yamlモジュールがない場合は簡易パース
        logger.warning("PyYAML not available, using simple parser")
        return _simple_yaml_parse(content)
    except Exception as e:
        raise ValueError(f"YAML parse error: {e}")


def _simple_yaml_parse(content: str) -> Dict[str, Any]:
    """簡易YAMLパーサー（基本的なキー:値のみ対応）"""
    result = {}
    stack = [(result, 0)]

    lines = content.strip().split("\n")

    for line in lines:
        if not line.strip() or line.strip().startswith("#"):
            continue

        # インデント計算
        indent = len(line) - len(line.lstrip())

        # キー:値を抽出
        if ":" in line:
            parts = line.strip().split(":", 1)
            key = parts[0].strip()
            value = parts[1].strip() if len(parts) > 1 else ""

            # 適切なネストレベルを見つける
            while stack and stack[-1][1] >= indent and len(stack) > 1:
                stack.pop()

            current_dict = stack[-1][0]

            if value:
                # 値がある場合
                current_dict[key] = _parse_yaml_value(value)
            else:
                # 値がない場合（ネストされたオブジェクト）
                current_dict[key] = {}
                stack.append((current_dict[key], indent))

    return result


def _parse_yaml_value(value: str) -> Any:
    """YAML値をPython型に変換"""
    if value.lower() == "true":
        return True
    elif value.lower() == "false":
        return False
    elif value.lower() == "null" or value.lower() == "~":
        return None

    try:
        return int(value)
    except ValueError:
        pass

    try:
        return float(value)
    except ValueError:
        pass

    # 文字列（クォートを除去）
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]

    return value


def _parse_json(content: str) -> Dict[str, Any]:
    """JSON文字列をパース"""
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON parse error: {e}")


def _normalize_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """設定を正規化"""
    normalized = {}

    # 一般的な設定キーのマッピング
    key_mappings = {
        "training_config": "training",
        "trainingConfig": "training",
        "model_config": "model",
        "modelConfig": "model",
        "dataset_config": "dataset",
        "datasetConfig": "dataset",
        "hyperparameters": "hyperparameters",
        "hyperParams": "hyperparameters",
        "hyper_params": "hyperparameters",
    }

    for key, value in config.items():
        # キーの正規化
        normalized_key = key_mappings.get(key, key)

        if isinstance(value, dict):
            # 再帰的に正規化
            normalized[normalized_key] = _normalize_config(value)
        else:
            normalized[normalized_key] = value

    # トップレベルの設定を抽出
    if "training" in normalized:
        training = normalized["training"]
        if "model_type" in training and "model_type" not in normalized:
            normalized["model_type"] = training["model_type"]
        if "dataset" in training and "dataset" not in normalized:
            normalized["dataset"] = training["dataset"]
        if "hyperparameters" in training and "hyperparameters" not in normalized:
            normalized["hyperparameters"] = training["hyperparameters"]

    return normalized
