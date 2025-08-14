"""
Configuration for deployment environments
"""

import os
from pathlib import Path

# 載入 .env 文件
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # 如果沒有 python-dotenv，忽略
    pass


def get_data_dir() -> Path:
    """Get data directory based on environment"""
    # Check if running on Render
    if os.environ.get("RENDER"):
        # On Render, use /opt/render/project/src/data unless disk is mounted
        render_disk = Path("/data")
        if render_disk.exists() and os.access(render_disk, os.W_OK):
            return render_disk
        # Fall back to project directory
        return Path("/opt/render/project/src/data")

    # Check if custom data dir is specified
    if custom_dir := os.environ.get("DATA_DIR"):
        return Path(custom_dir)

    # Default to local data directory
    return Path(__file__).resolve().parent.parent / "data"


# Global data directory
DATA_DIR = get_data_dir()

# Database configuration
USE_DATABASE = os.getenv("USE_DATABASE", "false").lower() == "true"
ENABLE_DUAL_WRITE = os.getenv("ENABLE_DUAL_WRITE", "false").lower() == "true"

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/linker")

# Only create directory if we have permission
try:
    DATA_DIR.mkdir(exist_ok=True, parents=True)
except PermissionError:
    # If we can't create it, assume it exists or will be created by the platform
    pass
