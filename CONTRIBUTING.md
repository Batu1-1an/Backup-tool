# Contributing to Backup Tool

Thank you for considering contributing to Backup Tool. This document outlines the process for contributing code, reporting issues, and proposing features.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)
- [Feature Requests](#feature-requests)

## Code of Conduct

This project is committed to providing a welcoming and inclusive experience for everyone. By participating, you agree to:

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Accept constructive criticism gracefully
- Focus on what is best for the community

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Backup-tool.git
   cd Backup-tool
   ```
3. Add the upstream remote:
   ```bash
   git remote add upstream https://github.com/Batu1-1an/Backup-tool.git
   ```

## Development Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Install testing tools
pip install pytest
```

## Coding Standards

- **Python**: Follow [PEP 8](https://peps.python.org/pep-0008/) style guide
- **Line length**: 120 characters maximum
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_CASE` for constants
- **Type hints**: Use type annotations for all function signatures
- **Docstrings**: Use Google-style docstrings for all public functions and classes
- **Imports**: Group imports as standard library, third-party, local; separate groups with a blank line
- **Error handling**: Use custom exception classes (e.g., `BackupError`, `NetworkError`, `ConfigError`)

Consistent patterns used throughout the codebase:

```python
"""Module docstring."""

import os
import logging

from . import config

logger = logging.getLogger("backup_tool")


class CustomError(Exception):
    """Custom exception for module-specific errors."""
    pass


def public_function(param: str) -> dict:
    """Short description.

    Args:
        param: Description of parameter.

    Returns:
        Description of return value.

    Raises:
        CustomError: If something goes wrong.
    """
    pass
```

## Testing

All tests use `pytest` with `unittest.mock` for mocking external dependencies.

```bash
# Run full test suite
pytest -v

# Run specific test module
pytest tests/test_config.py -v

# Run with coverage
pytest --cov=backup_tool tests/
```

Guidelines:

- Write tests for all new functionality
- Mock network operations (SMB/NFS connections) to avoid external dependencies
- Use descriptive test function names (`test_function_name_scenario`)
- Place test fixtures in the test module or shared `conftest.py`

## Pull Request Process

1. **Create an issue** describing the bug or feature before starting work
2. **Sync your fork** with upstream:
   ```bash
   git fetch upstream
   git rebase upstream/master
   ```
3. **Create a feature branch**:
   ```bash
   git checkout -b feat/your-feature-name
   ```
4. **Make changes** with clear, atomic commits following [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` — New feature
   - `fix:` — Bug fix
   - `docs:` — Documentation changes
   - `refactor:` — Code refactoring (no functional change)
   - `test:` — Adding or updating tests
   - `chore:` — Build/config changes
5. **Run tests** locally and ensure they pass
6. **Push and open a pull request** against the `master` branch
7. **Describe your changes** in the PR body — what, why, and how to test

### PR Review Checklist

- [ ] Tests pass (`pytest -v`)
- [ ] New code includes tests where applicable
- [ ] Docstrings and type hints added for new public functions
- [ ] No hardcoded secrets or credentials
- [ ] Error paths are handled and logged
- [ ] Changes are backward compatible (or breaking changes are clearly documented)

## Reporting Issues

When reporting a bug, include:

- **Operating system** (Windows, Linux) and version
- **Python version** (`python --version`)
- **Share type** (SMB or NFS)
- **Full error message and traceback**
- **Steps to reproduce**
- **Configuration** (redact sensitive values)

## Feature Requests

Open an issue with the `enhancement` tag. Describe:

- The problem you want to solve
- How you envision the solution
- Any alternative approaches considered
- Whether you are willing to implement it
