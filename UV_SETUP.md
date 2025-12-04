# Development setup with uv

## Install uv (if not already installed)

```powershell
pip install uv
```

Or on Windows with Chocolatey:
```powershell
choco install uv
```

## Setup Project with uv

```powershell
cd C:\Users\Sepo Konayuma\DocGen

# Create virtual environment
uv venv venv

# Activate virtual environment
.\venv\Scripts\Activate

# Install dependencies (much faster than pip!)
uv pip install -r requirements.txt

# Or use uv sync for lock file management (optional)
uv sync
```

## Run Application

```powershell
uvicorn docgen.main:app --reload --host 0.0.0.0 --port 8000
```

## Add New Dependencies with uv

```powershell
# Add a package
uv pip install package-name

# Or add to requirements.txt and sync
uv pip install -r requirements.txt
```

## Why uv?

- ⚡ **10-100x faster** than pip
- 🔒 **Deterministic** builds with lockfiles
- 📦 **Parallel** dependency resolution
- 🛡️ **Safer** dependency management
- 🐍 **Python version management** built-in

See: https://github.com/astral-sh/uv
