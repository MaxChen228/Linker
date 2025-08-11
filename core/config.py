"""
Configuration for deployment environments
"""
import os
from pathlib import Path


def get_data_dir() -> Path:
    """Get data directory based on environment"""
    # Check if running on Render
    if os.environ.get("RENDER"):
        # On Render, use /opt/render/project/src/data unless disk is mounted
        render_disk = Path("/data")
        if render_disk.exists() and os.access(render_disk, os.W_OK):
            return render_disk
        else:
            # Fall back to project directory
            return Path("/opt/render/project/src/data")

    # Check if custom data dir is specified
    if custom_dir := os.environ.get("DATA_DIR"):
        return Path(custom_dir)

    # Default to local data directory
    return Path(__file__).resolve().parent.parent / "data"

# Global data directory
DATA_DIR = get_data_dir()

# Only create directory if we have permission
try:
    DATA_DIR.mkdir(exist_ok=True, parents=True)
except PermissionError:
    # If we can't create it, assume it exists or will be created by the platform
    pass
