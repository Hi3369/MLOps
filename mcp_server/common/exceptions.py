"""カスタム例外定義"""


class MCPServerError(Exception):
    """MCPサーバーの基底例外"""

    pass


class ToolNotFoundError(MCPServerError):
    """ツールが見つからない"""

    pass


class ConfigurationError(MCPServerError):
    """設定エラー"""

    pass


class DataValidationError(MCPServerError):
    """データバリデーションエラー"""

    pass


class S3Error(MCPServerError):
    """S3操作エラー"""

    pass


class SageMakerError(MCPServerError):
    """SageMaker操作エラー"""

    pass


class GitHubAPIError(MCPServerError):
    """GitHub API エラー"""

    pass


class NotificationError(MCPServerError):
    """通知エラー"""

    pass


class ModelRegistryError(MCPServerError):
    """モデルレジストリエラー"""

    pass


class GPUOutOfMemoryError(MCPServerError):
    """GPU Out of Memory エラー

    学習時にGPUメモリ不足が発生した場合にスローされる。
    通常、バッチサイズを半減してリトライすることで解決可能。
    """

    pass


class SpotInstanceInterruptionError(MCPServerError):
    """Spot Instance 中断エラー

    AWS Spot Instanceが中断された場合にスローされる。
    オンデマンドインスタンスにフォールバックすることで解決可能。
    """

    pass


class GPUOutOfMemoryError(MCPServerError):
    """GPU Out of Memory エラー

    学習時にGPUメモリ不足が発生した場合にスローされる。
    通常、バッチサイズを半減してリトライすることで解決可能。
    """
    pass


class SpotInstanceInterruptionError(MCPServerError):
    """Spot Instance 中断エラー

    AWS Spot Instanceが中断された場合にスローされる。
    オンデマンドインスタンスにフォールバックすることで解決可能。
    """
    pass
