# Using uv for Python Package Management

This guide explains how to use `uv` for Python package management in Agent Squad.

## What is uv?

`uv` is an extremely fast Python package installer and resolver, written in Rust by Astral (creators of Ruff). It's 10-100x faster than pip and aims to replace pip, pip-tools, and virtualenv.

### Why uv?

- ⚡ **10-100x faster** than pip
- 🔒 **Deterministic installs** with lockfiles
- 🎯 **Drop-in replacement** for pip
- 🦀 **Written in Rust** for maximum performance
- 🧩 **Compatible with** pip, requirements.txt, and pyproject.toml

## Installation

### macOS/Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Windows

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### With pip (if you already have Python)

```bash
pip install uv
```

## Basic Usage

### Install Dependencies

```bash
# Install from requirements.txt
uv pip install -r requirements.txt

# Install specific package
uv pip install fastapi

# Install with extras
uv pip install "uvicorn[standard]"

# Install development dependencies
uv pip install -r requirements.txt
uv pip install black ruff mypy pytest
```

### Install to System Python

In Docker or when you want to install to the system Python:

```bash
uv pip install --system -r requirements.txt
```

### Create and Use Virtual Environments

```bash
# Create a virtual environment
uv venv

# Activate it (same as regular venv)
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Install dependencies
uv pip install -r requirements.txt

# Deactivate
deactivate
```

### Sync Dependencies

uv can sync your environment to match requirements exactly:

```bash
# Install/update to match requirements.txt exactly
uv pip sync requirements.txt
```

## Common Commands

### Package Management

```bash
# Install package
uv pip install package_name

# Install specific version
uv pip install "package_name==1.0.0"

# Install with version constraint
uv pip install "package_name>=1.0.0,<2.0.0"

# Uninstall package
uv pip uninstall package_name

# List installed packages
uv pip list

# Show package info
uv pip show package_name

# Freeze installed packages
uv pip freeze > requirements.txt
```

### Virtual Environments

```bash
# Create venv with specific Python version
uv venv --python 3.11

# Create venv in specific location
uv venv /path/to/venv

# Create venv with system packages
uv venv --system-site-packages
```

## Agent Squad Workflow

### Initial Setup

```bash
cd backend

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment (optional, recommended for local dev)
uv venv

# Activate virtual environment
source .venv/bin/activate

# Install all dependencies
uv pip install -r requirements.txt

# Install dev dependencies
uv pip install black ruff mypy pytest pytest-cov
```

### Daily Development

```bash
# Update dependencies
uv pip install -r requirements.txt

# Add a new package
uv pip install new-package

# Update requirements.txt
uv pip freeze > requirements.txt

# Run tests
pytest

# Format code
black .

# Lint
ruff check .
```

### Docker (System Install)

In Dockerfile, we use `--system` flag:

```dockerfile
RUN uv pip install --system -r requirements.txt
```

This installs packages directly to the system Python without creating a venv.

## Comparison: uv vs pip vs Poetry

### Speed

```bash
# uv (fastest)
$ time uv pip install -r requirements.txt
# ~2 seconds

# pip
$ time pip install -r requirements.txt
# ~30 seconds

# Poetry
$ time poetry install
# ~45 seconds
```

### Commands

| Task | uv | pip | Poetry |
|------|----|----|--------|
| Install deps | `uv pip install -r requirements.txt` | `pip install -r requirements.txt` | `poetry install` |
| Add package | `uv pip install pkg` | `pip install pkg` | `poetry add pkg` |
| Remove package | `uv pip uninstall pkg` | `pip uninstall pkg` | `poetry remove pkg` |
| List packages | `uv pip list` | `pip list` | `poetry show` |
| Create venv | `uv venv` | `python -m venv .venv` | `poetry env` |

## Advanced Usage

### Using with pyproject.toml

uv can read dependencies from pyproject.toml:

```bash
# Install dependencies from pyproject.toml
uv pip install -e .

# Or install specific groups
uv pip install -e ".[dev]"
```

### Resolution Strategies

```bash
# Use lowest compatible versions (for testing compatibility)
uv pip install -r requirements.txt --resolution lowest

# Use latest compatible versions
uv pip install -r requirements.txt --resolution highest
```

### Offline Mode

```bash
# Install without network access (from cache)
uv pip install -r requirements.txt --offline
```

### Cache Management

```bash
# Show cache directory
uv cache dir

# Clean cache
uv cache clean
```

## Troubleshooting

### uv not found

```bash
# Reload shell configuration
source ~/.bashrc  # or ~/.zshrc

# Or add to PATH manually
export PATH="$HOME/.cargo/bin:$PATH"
```

### Permission Errors

```bash
# Use --system flag in Docker/containers
uv pip install --system -r requirements.txt

# Or use venv for local development
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### Package Conflicts

```bash
# Force reinstall
uv pip install --force-reinstall package_name

# Sync to exact requirements
uv pip sync requirements.txt
```

### Slow First Install

First install downloads and caches packages. Subsequent installs will be much faster.

```bash
# Warm up cache
uv pip install -r requirements.txt

# Second install is ~10x faster
uv pip install -r requirements.txt
```

## Best Practices

### 1. Use requirements.txt as Source of Truth

```bash
# Generate requirements.txt
uv pip freeze > requirements.txt

# Install from requirements.txt
uv pip install -r requirements.txt
```

### 2. Pin Exact Versions in Production

```bash
# Development: use flexible versions
fastapi>=0.104.1

# Production: pin exact versions
fastapi==0.104.1
```

### 3. Separate Dev Dependencies

```bash
# requirements.txt (production)
fastapi==0.104.1
sqlalchemy==2.0.23

# requirements-dev.txt (development)
-r requirements.txt
pytest>=7.4.3
black>=23.12.0
ruff>=0.1.7
```

Install with:
```bash
uv pip install -r requirements-dev.txt
```

### 4. Use Virtual Environments Locally

```bash
# Always use venv for local development
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 5. Use --system in Docker

```bash
# In Dockerfile
RUN uv pip install --system -r requirements.txt
```

## Migration from Poetry

Already done! The project now uses:
- `requirements.txt` for dependencies
- `pyproject.toml` for tool configuration (black, ruff, mypy)
- `uv` for fast package management

Old Poetry commands → New uv commands:

```bash
# poetry install
uv pip install -r requirements.txt

# poetry add package
uv pip install package && uv pip freeze > requirements.txt

# poetry remove package
uv pip uninstall package && uv pip freeze > requirements.txt

# poetry show
uv pip list

# poetry run pytest
pytest  # (after activating venv)
```

## Resources

- **uv Documentation**: https://github.com/astral-sh/uv
- **uv Installation**: https://astral.sh/uv
- **Ruff (by Astral)**: https://docs.astral.sh/ruff/

## Summary

uv is the recommended way to manage Python packages in Agent Squad because:

1. ⚡ **Speed**: 10-100x faster than pip
2. 🎯 **Compatibility**: Drop-in pip replacement
3. 🔒 **Reliability**: Deterministic installs
4. 🦀 **Performance**: Written in Rust
5. 🚀 **Active Development**: Modern tooling from Astral

Use it for all Python package management in this project!
