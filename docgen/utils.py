import os
import shutil
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from docgen.config import config

def get_file_extension(filename: str) -> str:
    """Extract file extension and normalize to lowercase."""
    return Path(filename).suffix.lower()

def is_allowed_extension(filename: str) -> bool:
    """Check if file extension is supported."""
    return get_file_extension(filename) in config.ALLOWED_EXTENSIONS

def get_file_hash(data: bytes) -> str:
    """Generate SHA256 hash of file content."""
    return hashlib.sha256(data).hexdigest()

def cleanup_old_files(directory: str, retention_seconds: int) -> None:
    """Remove files older than retention period."""
    if not os.path.exists(directory):
        return
    
    now = datetime.now()
    cutoff_time = now - timedelta(seconds=retention_seconds)
    
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
            if file_mtime < cutoff_time:
                try:
                    os.remove(filepath)
                except Exception as e:
                    print(f"Failed to delete {filepath}: {e}")

def safe_read_file(filepath: str, encoding: str = "utf-8") -> str:
    """Read file with fallback encoding attempts."""
    encodings = [encoding, "utf-8", "latin-1", "cp1252"]
    
    for enc in encodings:
        try:
            with open(filepath, "r", encoding=enc, errors="replace") as f:
                return f.read()
        except Exception:
            continue
    
    raise ValueError(f"Could not read file {filepath} with any supported encoding")

def estimate_tokens(text: str) -> int:
    """Rough estimate of token count (approximately 1 token per 4 chars)."""
    return len(text) // 4

def format_file_size(size_bytes: int) -> str:
    """Format bytes to human-readable size."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"
