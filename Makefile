.PHONY: help setup lint format test coverage clean

# デフォルトターゲット
help:
	@echo "Available commands:"
	@echo "  make setup     - Setup development environment (create venv and install deps)"
	@echo "  make lint      - Run all linters (flake8, black check, isort check)"
	@echo "  make format    - Format code (black, isort)"
	@echo "  make test      - Run tests"
	@echo "  make coverage  - Run tests with coverage report"
	@echo "  make clean     - Clean up generated files"

# 開発環境セットアップ
setup:
	@echo "🔧 Setting up development environment..."
	@bash setup_dev.sh

# Lintチェック（エラーがあれば終了）
lint: lint-flake8 lint-black lint-isort
	@echo "✅ All lint checks passed!"

lint-flake8:
	@echo "🔍 Running flake8..."
	@if command -v flake8 >/dev/null 2>&1; then \
		flake8 agents/ tests/; \
	else \
		echo "⚠️  flake8 not found. Run 'make setup' or activate venv first."; \
		exit 1; \
	fi

lint-black:
	@echo "🔍 Running black (check only)..."
	@if command -v black >/dev/null 2>&1; then \
		black --check agents/ tests/; \
	else \
		echo "⚠️  black not found. Run 'make setup' or activate venv first."; \
		exit 1; \
	fi

lint-isort:
	@echo "🔍 Running isort (check only)..."
	@if command -v isort >/dev/null 2>&1; then \
		isort --check-only agents/ tests/; \
	else \
		echo "⚠️  isort not found. Run 'make setup' or activate venv first."; \
		exit 1; \
	fi

# コード整形
format: format-black format-isort
	@echo "✅ Code formatting complete!"

format-black:
	@echo "✨ Formatting with black..."
	@if command -v black >/dev/null 2>&1; then \
		black agents/ tests/; \
	else \
		echo "⚠️  black not found. Run 'make setup' or activate venv first."; \
		exit 1; \
	fi

format-isort:
	@echo "✨ Sorting imports with isort..."
	@if command -v isort >/dev/null 2>&1; then \
		isort agents/ tests/; \
	else \
		echo "⚠️  isort not found. Run 'make setup' or activate venv first."; \
		exit 1; \
	fi

# テスト実行
test:
	@echo "🧪 Running tests..."
	@if command -v pytest >/dev/null 2>&1; then \
		pytest tests/; \
	else \
		echo "⚠️  pytest not found. Run 'make setup' or activate venv first."; \
		exit 1; \
	fi

# カバレッジ付きテスト
coverage:
	@echo "🧪 Running tests with coverage..."
	@if command -v pytest >/dev/null 2>&1; then \
		pytest --cov=agents --cov-report=html --cov-report=term tests/; \
		@echo ""; \
		@echo "📊 Coverage report generated: htmlcov/index.html"; \
	else \
		echo "⚠️  pytest not found. Run 'make setup' or activate venv first."; \
		exit 1; \
	fi

# クリーンアップ
clean:
	@echo "🧹 Cleaning up..."
	@rm -rf __pycache__ .pytest_cache .mypy_cache htmlcov .coverage
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Cleanup complete!"
