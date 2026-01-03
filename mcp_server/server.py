"""
MLOps Integrated MCP Server

統合MCPサーバーのメイン実装。
全capabilityのツールを登録し、ルーティングを行います。
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class MLOpsServer:
    """
    統合MLOps MCPサーバー

    12個のcapabilityを統合し、単一のMCPサーバーとして提供します。
    Phase 1では Data Preparation Capability のみ実装済み。
    """

    def __init__(self):
        """サーバーの初期化"""
        self.tools: Dict[str, Any] = {}
        self.capabilities: Dict[str, Any] = {}
        logger.info("MLOps MCP Server initializing...")

        # Capabilityの登録
        self._register_capabilities()

    def _register_capabilities(self):
        """
        全capabilityを登録

        Phase 1 Week 1-2では Data Preparation のみ登録
        """
        # Data Preparation Capability
        try:
            from .capabilities.data_preparation.capability import DataPreparationCapability

            data_prep = DataPreparationCapability()
            self.capabilities["data_preparation"] = data_prep

            # ツールをグローバルツールリストに登録
            for tool_name, tool_func in data_prep.get_tools().items():
                full_tool_name = f"data_preparation.{tool_name}"
                self.tools[full_tool_name] = tool_func
                logger.info(f"Registered tool: {full_tool_name}")

        except ImportError as e:
            logger.warning(f"Data Preparation Capability not available: {e}")

        # ML Training Capability
        try:
            from .capabilities.ml_training.capability import MLTrainingCapability

            ml_training = MLTrainingCapability()
            self.capabilities["ml_training"] = ml_training

            # ツールをグローバルツールリストに登録
            for tool_name, tool_func in ml_training.get_tools().items():
                full_tool_name = f"ml_training.{tool_name}"
                self.tools[full_tool_name] = tool_func
                logger.info(f"Registered tool: {full_tool_name}")

        except ImportError as e:
            logger.warning(f"ML Training Capability not available: {e}")

        # ML Evaluation Capability
        try:
            from .capabilities.ml_evaluation.capability import MLEvaluationCapability

            ml_evaluation = MLEvaluationCapability()
            self.capabilities["ml_evaluation"] = ml_evaluation

            # ツールをグローバルツールリストに登録
            for tool_name, tool_func in ml_evaluation.get_tools().items():
                full_tool_name = f"ml_evaluation.{tool_name}"
                self.tools[full_tool_name] = tool_func
                logger.info(f"Registered tool: {full_tool_name}")

        except ImportError as e:
            logger.warning(f"ML Evaluation Capability not available: {e}")

        # Model Registry Capability
        try:
            from .capabilities.model_registry.capability import ModelRegistryCapability

            model_registry = ModelRegistryCapability()
            self.capabilities["model_registry"] = model_registry

            # ツールをグローバルツールリストに登録
            for tool_name, tool_func in model_registry.get_tools().items():
                full_tool_name = f"model_registry.{tool_name}"
                self.tools[full_tool_name] = tool_func
                logger.info(f"Registered tool: {full_tool_name}")

        except ImportError as e:
            logger.warning(f"Model Registry Capability not available: {e}")

        # Model Packaging Capability
        try:
            from .capabilities.model_packaging.capability import ModelPackagingCapability

            model_packaging = ModelPackagingCapability()
            self.capabilities["model_packaging"] = model_packaging

            # ツールをグローバルツールリストに登録
            for tool_name, tool_func in model_packaging.get_tools().items():
                full_tool_name = f"model_packaging.{tool_name}"
                self.tools[full_tool_name] = tool_func
                logger.info(f"Registered tool: {full_tool_name}")

        except ImportError as e:
            logger.warning(f"Model Packaging Capability not available: {e}")

        # Model Deployment Capability
        try:
            from .capabilities.model_deployment.capability import ModelDeploymentCapability

            model_deployment = ModelDeploymentCapability()
            self.capabilities["model_deployment"] = model_deployment

            # ツールをグローバルツールリストに登録
            for tool_name, tool_func in model_deployment.get_tools().items():
                full_tool_name = f"model_deployment.{tool_name}"
                self.tools[full_tool_name] = tool_func
                logger.info(f"Registered tool: {full_tool_name}")

        except ImportError as e:
            logger.warning(f"Model Deployment Capability not available: {e}")

        logger.info(f"Total {len(self.tools)} tools registered")

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        利用可能なツールのリストを返す

        Returns:
            ツール定義のリスト（MCP仕様準拠）
        """
        tool_list = []
        for tool_name in self.tools.keys():
            # ツールのメタデータを取得（簡易実装）
            tool_list.append(
                {
                    "name": tool_name,
                    "description": self._get_tool_description(tool_name),
                    "inputSchema": self._get_tool_input_schema(tool_name),
                }
            )
        return tool_list

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        指定されたツールを実行

        Args:
            tool_name: ツール名（例: "data_preparation.load_dataset"）
            arguments: ツールへの引数

        Returns:
            ツールの実行結果

        Raises:
            ValueError: ツールが見つからない場合
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool not found: {tool_name}")

        logger.info(f"Calling tool: {tool_name}")
        logger.debug(f"Arguments: {arguments}")

        try:
            tool_func = self.tools[tool_name]
            result = tool_func(**arguments)
            logger.info(f"Tool {tool_name} executed successfully")
            return {"success": True, "result": result}

        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _get_tool_description(self, tool_name: str) -> str:
        """ツールの説明を取得（簡易実装）"""
        tool_func = self.tools.get(tool_name)
        if tool_func and hasattr(tool_func, "__doc__"):
            return tool_func.__doc__ or "No description available"
        return "No description available"

    def _get_tool_input_schema(self, tool_name: str) -> Dict[str, Any]:
        """
        ツールの入力スキーマを取得（簡易実装）

        実際の実装では、関数のシグネチャやデコレーターから
        JSON Schemaを自動生成します。
        """
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    def get_server_info(self) -> Dict[str, Any]:
        """サーバー情報を返す"""
        return {
            "name": "MLOps Integrated MCP Server",
            "version": "0.1.0",
            "capabilities": list(self.capabilities.keys()),
            "total_tools": len(self.tools),
        }
