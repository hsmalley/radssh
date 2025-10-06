# Contributing to RadSSH

Thank you for your interest in contributing to RadSSH! This document provides guidelines and information for contributors.

## Code of Conduct

This project adheres to a Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When creating a bug report, please include:

- A clear and descriptive title
- A detailed description of the issue
- Steps to reproduce the behavior
- Expected vs actual behavior
- Environment information (Python version, OS, etc.)
- Relevant error messages or logs

### Suggesting Features

Feature requests are welcome! Please provide:

- A clear and descriptive title
- A detailed description of the proposed feature
- Use cases and examples
- Any implementation ideas you might have

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Make your changes** following the coding standards below
3. **Add tests** for any new functionality
4. **Update documentation** if needed
5. **Ensure all tests pass** locally
6. **Submit a pull request** with a clear description

## Development Setup

### Prerequisites

- Python 3.12 or higher
- Git

### Setup Instructions

```bash
# Clone your fork
git clone https://github.com/yourusername/radssh.git
cd radssh

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e .[dev]

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run quick tests (excludes slow cluster tests)
pytest --ignore=tests/test_cluster_utils.py -v

# Run all tests (may take several minutes)
pytest

# Run with coverage
pytest --cov=radssh --cov-report=html
```

### Code Quality

We use several tools to maintain code quality:

```bash
# Linting and formatting
ruff check .
ruff format .

# Pre-commit hooks (runs automatically on commit)
pre-commit run --all-files
```

## Coding Standards

### Python Style

- Follow PEP 8 style guidelines
- Use type hints where possible
- Write docstrings for public functions and classes
- Keep functions focused and small
- Use meaningful variable and function names

### Testing

- Write tests for all new functionality
- Maintain or improve test coverage
- Use descriptive test names
- Follow the AAA pattern (Arrange, Act, Assert)

### Documentation

- Update relevant documentation for any changes
- Use clear and concise language
- Include code examples where helpful
- Keep the README.md up to date

## Project Structure

```
radssh/
├── radssh/              # Main package
│   ├── core_plugins/    # Core plugin modules
│   └── plugins/         # Plugin system
├── tests/               # Test suite
├── docs/                # Documentation
└── .github/             # GitHub configuration
```

## Release Process

The project follows semantic versioning (SemVer):

- **Major version**: Breaking changes
- **Minor version**: New features (backward compatible)
- **Patch version**: Bug fixes (backward compatible)

Releases are automated through GitHub Actions when tags are pushed.

## Getting Help

If you need help or have questions:

- Check the existing issues and discussions
- Create a new issue with your question
- Tag maintainers if needed (@hsmalley)

## Recognition

Contributors will be recognized in the project's documentation and release notes.

Thank you for contributing to RadSSH!