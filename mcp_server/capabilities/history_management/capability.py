"""
History Management Capability

履歴管理機能のCapability実装
学習履歴記録・保存・GitHub連携・バージョン追跡を提供
"""

import logging
from typing import Any, Callable, Dict

from .tools import (
    format_training_history,
    post_issue_comment,
    save_training_history,
    track_version_history,
)

logger = logging.getLogger(__name__)


class HistoryManagementCapability:
    """
    履歴管理Capability

    以下のツールを提供:
    - format_training_history: 学習履歴フォーマット
    - save_training_history: 学習履歴保存
    - post_issue_comment: GitHub Issueコメント投稿
    - track_version_history: バージョン履歴追跡
    """

    def __init__(self):
        """Capabilityの初期化"""
        self._tools: Dict[str, Callable] = {
            "format_training_history": format_training_history,
            "save_training_history": save_training_history,
            "post_issue_comment": post_issue_comment,
            "track_version_history": track_version_history,
        }

        self._tool_schemas: Dict[str, Dict[str, Any]] = {
            "format_training_history": {
                "name": "format_training_history",
                "description": "学習履歴をMarkdown/JSON/テキスト形式でフォーマットします",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "training_job_name": {
                            "type": "string",
                            "description": "学習ジョブ名",
                        },
                        "metrics": {
                            "type": "object",
                            "description": "メトリクス辞書（accuracy, loss等）",
                        },
                        "hyperparameters": {
                            "type": "object",
                            "description": "ハイパーパラメータ辞書",
                        },
                        "model_name": {
                            "type": "string",
                            "description": "モデル名",
                        },
                        "model_version": {
                            "type": "string",
                            "description": "モデルバージョン",
                        },
                        "dataset_info": {
                            "type": "object",
                            "description": "データセット情報",
                        },
                        "training_time_seconds": {
                            "type": "number",
                            "description": "学習時間（秒）",
                        },
                        "instance_type": {
                            "type": "string",
                            "description": "インスタンスタイプ",
                        },
                        "output_format": {
                            "type": "string",
                            "enum": ["markdown", "json", "text"],
                            "description": "出力形式",
                            "default": "markdown",
                        },
                    },
                    "required": ["training_job_name", "metrics"],
                },
            },
            "save_training_history": {
                "name": "save_training_history",
                "description": "フォーマット済み学習履歴をS3またはローカルに保存します",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "training_job_name": {
                            "type": "string",
                            "description": "学習ジョブ名",
                        },
                        "formatted_history": {
                            "type": "string",
                            "description": "フォーマット済み履歴コンテンツ",
                        },
                        "storage_type": {
                            "type": "string",
                            "enum": ["s3", "local"],
                            "description": "ストレージタイプ",
                            "default": "s3",
                        },
                        "s3_bucket": {
                            "type": "string",
                            "description": "S3バケット名",
                        },
                        "s3_prefix": {
                            "type": "string",
                            "description": "S3プレフィックス",
                            "default": "training_history/",
                        },
                        "local_path": {
                            "type": "string",
                            "description": "ローカル保存パス",
                        },
                        "file_format": {
                            "type": "string",
                            "enum": ["md", "json", "txt"],
                            "description": "ファイル形式",
                            "default": "md",
                        },
                    },
                    "required": ["training_job_name", "formatted_history"],
                },
            },
            "post_issue_comment": {
                "name": "post_issue_comment",
                "description": "GitHub Issueに進捗・結果コメントを投稿します",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "repository": {
                            "type": "string",
                            "description": "リポジトリ（owner/repo形式）",
                        },
                        "issue_number": {
                            "type": "integer",
                            "description": "Issue番号",
                        },
                        "comment": {
                            "type": "string",
                            "description": "コメント本文",
                        },
                        "comment_type": {
                            "type": "string",
                            "enum": ["progress", "result", "error", "info"],
                            "description": "コメントタイプ",
                            "default": "progress",
                        },
                        "include_timestamp": {
                            "type": "boolean",
                            "description": "タイムスタンプを含めるか",
                            "default": True,
                        },
                    },
                    "required": ["repository", "issue_number", "comment"],
                },
            },
            "track_version_history": {
                "name": "track_version_history",
                "description": "モデルバージョン履歴を追跡・記録します",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "model_name": {
                            "type": "string",
                            "description": "モデル名",
                        },
                        "version": {
                            "type": "string",
                            "description": "バージョン（v1.0.0形式推奨）",
                        },
                        "metadata": {
                            "type": "object",
                            "description": "追加メタデータ",
                        },
                        "parent_version": {
                            "type": "string",
                            "description": "親バージョン（派生元）",
                        },
                        "training_job_name": {
                            "type": "string",
                            "description": "関連する学習ジョブ名",
                        },
                        "training_data_version": {
                            "type": "string",
                            "description": "学習データバージョン",
                        },
                        "code_version": {
                            "type": "string",
                            "description": "コードバージョン（gitコミットハッシュ等）",
                        },
                        "status": {
                            "type": "string",
                            "enum": ["development", "staging", "production", "deprecated"],
                            "description": "ステータス",
                            "default": "development",
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "タグリスト",
                        },
                    },
                    "required": ["model_name", "version"],
                },
            },
        }

        logger.info("HistoryManagementCapability initialized with 4 tools")

    def get_tools(self) -> Dict[str, Callable]:
        """
        ツール関数のマッピングを返す

        Returns:
            ツール名から関数へのマッピング辞書
        """
        return self._tools

    def get_tool_schemas(self) -> Dict[str, Dict[str, Any]]:
        """
        ツールスキーマのマッピングを返す

        Returns:
            ツール名からスキーマ辞書へのマッピング
        """
        return self._tool_schemas
