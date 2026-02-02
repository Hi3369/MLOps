<!-- markdownlint-disable MD041 -->
## Summary

<!-- What does this PR do? Keep it to 1-3 bullet points. -->

-

## Changes

<!-- List the main changes made in this PR. -->

-

## Test Plan

- [ ] `pytest tests/ -v` passes
- [ ] `flake8 mcp_server/ tests/ --max-line-length=100` passes
- [ ] `mypy mcp_server/ --ignore-missing-imports` passes
- [ ] `bandit -r mcp_server/ -c pyproject.toml` passes
- [ ] `black --check mcp_server/ tests/` passes
- [ ] `isort --check-only --profile black mcp_server/ tests/` passes

## Coverage

- [ ] Coverage >= 80%

## Related Issues

<!-- Link to related issues: Closes #123, Fixes #456 -->
