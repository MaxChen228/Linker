"""
Configuration for deployment environments
"""
import os
from pathlib import Path

def get_data_dir() -> Path:
    """Get data directory based on environment"""
    # Check if running on Render (has persistent disk)
    if os.environ.get("RENDER"):
        return Path("/data")
    
    # Check if custom data dir is specified
    if custom_dir := os.environ.get("DATA_DIR"):
        return Path(custom_dir)
    
    # Default to local data directory
    return Path(__file__).resolve().parent.parent / "data"

# Global data directory
DATA_DIR = get_data_dir()
DATA_DIR.mkdir(exist_ok=True, parents=True)