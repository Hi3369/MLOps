"""
MLOps MCP Server Entry Point

MCPサーバーを起動するエントリーポイント。
"""

import logging
import sys

from .server import MLOpsServer

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def main():
    """MCPサーバーのメインエントリーポイント"""
    try:
        logger.info("Starting MLOps MCP Server...")

        # サーバーインスタンスの作成
        server = MLOpsServer()

        # サーバー情報の表示
        info = server.get_server_info()
        logger.info(f"Server Info: {info}")

        # ツールリストの表示
        tools = server.list_tools()
        logger.info(f"Available tools: {len(tools)}")
        for tool in tools:
            logger.info(f"  - {tool['name']}: {tool['description']}")

        logger.info("MLOps MCP Server started successfully")
        logger.info("Server is ready to accept tool calls")

        # 実際の実装ではここでMCPプロトコルのリスナーを起動
        # 現時点では初期化のみで終了
        return 0

    except Exception as e:
        logger.error(f"Failed to start server: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
