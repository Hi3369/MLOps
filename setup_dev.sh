#!/bin/bash
# 開発環境セットアップスクリプト
# PEP 668制約を回避してPython開発ツールをインストール

set -e

echo "=== MLOps Development Environment Setup ==="
echo ""

# Python3の確認
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found"
    exit 1
fi

echo "✓ Python version: $(python3 --version)"
echo ""

# 仮想環境の作成（python3-venvが必要）
echo "📦 Setting up virtual environment..."
if [ ! -d "venv" ]; then
    if python3 -m venv venv 2>/dev/null; then
        echo "✓ Virtual environment created: venv/"
    else
        echo "⚠️  Virtual environment creation failed."
        echo "   To install python3-venv, run:"
        echo "   sudo apt install python3.12-venv"
        echo ""
        echo "   Or use system packages:"
        echo "   sudo apt install python3-flake8 python3-black python3-isort python3-pytest"
        exit 1
    fi
else
    echo "✓ Virtual environment already exists: venv/"
fi

# 仮想環境のアクティベート
echo ""
echo "📦 Installing dependencies..."
source venv/bin/activate

# pip のアップグレード
pip install --upgrade pip

# 開発ツールのインストール
echo ""
echo "🔧 Installing development tools..."
pip install flake8==7.0.0 black==23.12.1 isort==5.13.2

# テストツールのインストール
echo ""
echo "🧪 Installing test tools..."
pip install pytest==7.4.4 pytest-cov==4.1.0 pytest-mock==3.12.0

# その他の依存関係（必要に応じて）
echo ""
echo "📚 Installing other dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "To activate the virtual environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "Available commands:"
echo "  flake8 agents/ tests/        # Syntax and style check"
echo "  black agents/ tests/         # Code formatting"
echo "  isort agents/ tests/         # Import sorting"
echo "  pytest tests/                # Run tests"
echo "  pytest --cov=agents tests/   # Run tests with coverage"
