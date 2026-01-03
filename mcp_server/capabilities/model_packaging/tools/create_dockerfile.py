"""
Create Dockerfile Tool

Dockerfile作成ツール
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def create_dockerfile(
    model_s3_uri: str,
    framework: str = "sklearn",
    python_version: str = "3.11",
    base_image: str = None,
    optimize: bool = True,
) -> Dict[str, Any]:
    """
    モデル用のDockerfileを生成

    Args:
        model_s3_uri: モデルのS3 URI
        framework: フレームワーク (sklearn, tensorflow, pytorch)
        python_version: Pythonバージョン
        base_image: ベースイメージ (省略時は自動選択)
        optimize: 最適化を有効にするか (マルチステージビルド等)

    Returns:
        Dockerfile作成結果辞書
    """
    logger.info(f"Creating Dockerfile for {framework} model")

    # S3 URIのバリデーション
    if not model_s3_uri.startswith("s3://"):
        raise ValueError("Invalid S3 URI: must start with 's3://'")

    # ベースイメージの決定
    if base_image is None:
        base_image = _get_default_base_image(framework, python_version)

    # Dockerfileコンテンツを生成
    if optimize:
        dockerfile_content = _generate_optimized_dockerfile(
            base_image, framework, model_s3_uri, python_version
        )
    else:
        dockerfile_content = _generate_simple_dockerfile(base_image, framework, model_s3_uri)

    logger.info("Dockerfile generated successfully")

    return {
        "status": "success",
        "message": "Dockerfile created successfully",
        "dockerfile": {
            "content": dockerfile_content,
            "base_image": base_image,
            "framework": framework,
            "python_version": python_version,
            "optimized": optimize,
        },
    }


def _get_default_base_image(framework: str, python_version: str) -> str:
    """フレームワークに応じたデフォルトベースイメージを取得"""
    base_images = {
        "sklearn": f"python:{python_version}-slim",
        "tensorflow": f"tensorflow/tensorflow:{python_version}",
        "pytorch": f"pytorch/pytorch:{python_version}-runtime",
    }

    return base_images.get(framework, f"python:{python_version}-slim")


def _generate_optimized_dockerfile(
    base_image: str, framework: str, model_s3_uri: str, python_version: str
) -> str:
    """最適化されたDockerfileを生成（マルチステージビルド）"""
    dockerfile = f"""# Multi-stage build for optimized image size
# Stage 1: Builder
FROM {base_image} AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    gcc \\
    g++ \\
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM {base_image}

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Install AWS CLI (lightweight version)
RUN apt-get update && apt-get install -y --no-install-recommends \\
    curl \\
    unzip \\
    && curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \\
    && unzip awscliv2.zip \\
    && ./aws/install --bin-dir /usr/local/bin --install-dir /usr/local/aws-cli \\
    && rm -rf awscliv2.zip aws \\
    && apt-get purge -y curl unzip \\
    && apt-get autoremove -y \\
    && rm -rf /var/lib/apt/lists/*

# Set PATH for user-installed packages
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY inference.py .
COPY config.json .

# Download model from S3 at build time (optional - can be done at runtime)
# ENV MODEL_S3_URI={model_s3_uri}
# RUN aws s3 cp $MODEL_S3_URI model.pkl

# Expose port for serving
EXPOSE 8080

# Set non-root user for security (optional)
# RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
# USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
    CMD python -c "import sys; sys.exit(0)"

# Run inference server
CMD ["python", "inference.py"]
"""

    return dockerfile


def _generate_simple_dockerfile(base_image: str, framework: str, model_s3_uri: str) -> str:
    """シンプルなDockerfileを生成"""
    dockerfile = f"""FROM {base_image}

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Install AWS CLI
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \\
    && unzip awscliv2.zip \\
    && ./aws/install \\
    && rm -rf awscliv2.zip aws

# Copy application code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY inference.py .
COPY config.json .

# Expose port
EXPOSE 8080

# Run inference server
CMD ["python", "inference.py"]
"""

    return dockerfile
