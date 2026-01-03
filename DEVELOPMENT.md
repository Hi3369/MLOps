# Development Guide

This guide explains how to set up the development environment and run code quality checks.

## Prerequisites

- Python 3.12+
- pip or pip3
- make (optional, for convenience commands)

## Setup Development Environment

### Option 1: Using setup script (Recommended)

```bash
# Run the setup script
bash setup_dev.sh

# Activate the virtual environment
source venv/bin/activate
```

### Option 2: Using Makefile

```bash
make setup
source venv/bin/activate
```

### Option 3: Manual setup

If the automatic setup fails due to system restrictions, you can install tools system-wide:

```bash
# Install python3-venv first
sudo apt install python3.12-venv

# Then create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Code Quality Tools

### Flake8 (Syntax and Style Check)

Check Python code for syntax errors and PEP 8 style violations:

```bash
# Check all code
flake8 agents/ tests/

# Check specific file
flake8 agents/judge_agent/lambda_function.py
```

Configuration: `.flake8`

### Black (Code Formatter)

Format Python code automatically:

```bash
# Check formatting (dry run)
black --check agents/ tests/

# Format code (modifies files)
black agents/ tests/

# Format specific file
black agents/judge_agent/lambda_function.py
```

Configuration: `pyproject.toml` ([tool.black])

### isort (Import Sorter)

Sort Python imports automatically:

```bash
# Check import order (dry run)
isort --check-only agents/ tests/

# Sort imports (modifies files)
isort agents/ tests/

# Sort specific file
isort agents/judge_agent/lambda_function.py
```

Configuration: `pyproject.toml` ([tool.isort])

## Using Makefile Commands

The Makefile provides convenient shortcuts:

```bash
# Show all available commands
make help

# Run all linters (flake8 + black check + isort check)
make lint

# Format all code (black + isort)
make format

# Run tests
make test

# Run tests with coverage report
make coverage

# Clean up generated files
make clean
```

## Testing

### Run all tests

```bash
pytest tests/
```

### Run specific test file

```bash
pytest tests/unit/test_judge_agent.py
```

### Run specific test case

```bash
pytest tests/unit/test_judge_agent.py::TestJudgeAgent::test_judge_acceptable_classification
```

### Run with coverage

```bash
pytest --cov=agents --cov-report=html --cov-report=term tests/
```

Coverage report will be generated in `htmlcov/index.html`.

## Recommended Workflow

1. **Before coding**: Activate virtual environment

   ```bash
   source venv/bin/activate
   ```

2. **While coding**: Run linters frequently

   ```bash
   make lint
   ```

3. **Before commit**: Format code and run tests

   ```bash
   make format
   make test
   make lint
   ```

4. **After commit**: Clean up

   ```bash
   make clean
   deactivate  # Exit virtual environment
   ```

## Configuration Files

- `.flake8` - flake8 configuration
- `pyproject.toml` - black, isort, mypy configuration
- `pytest.ini` - pytest configuration
- `requirements.txt` - Python dependencies

## Troubleshooting

### "externally-managed-environment" error

This is due to PEP 668 restrictions on Debian/Ubuntu systems. Use virtual environment instead:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### "python3-venv not found" error

Install the python3-venv package:

```bash
sudo apt install python3.12-venv
```

### Linter not found

Make sure you've activated the virtual environment:

```bash
source venv/bin/activate
```

Or run the setup again:

```bash
bash setup_dev.sh
```

## CI/CD Integration

The code quality tools can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run linters
  run: |
    source venv/bin/activate
    make lint

- name: Run tests
  run: |
    source venv/bin/activate
    make coverage
```

## References

- [PEP 8 - Style Guide for Python Code](https://pep8.org/)
- [Black - The uncompromising code formatter](https://black.readthedocs.io/)
- [Flake8 - Python linting tool](https://flake8.pycqa.org/)
- [isort - Python import sorter](https://pycqa.github.io/isort/)
- [pytest - Testing framework](https://docs.pytest.org/)
