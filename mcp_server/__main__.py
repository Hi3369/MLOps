"""統合MLOps MCPサーバー エントリーポイント"""
import asyncio
import sys

from .config import Config
from .server import UnifiedMLOpsMCPServer
from .common.logger import get_logger

logger = get_logger(__name__)


async def main():
    """メイン関数"""
    try:
        # 環境変数から設定を読み込む
        config = Config.from_env()
        logger.info("Configuration loaded")

        # サーバー起動
        server = UnifiedMLOpsMCPServer(config)
        await server.run()

    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)

    except Exception as e:
        logger.error("Server failed to start", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
