"""Utility functions for CodeBase Cartographer"""
import os
from pathlib import Path

def get_relative_path(file_path: str, base_path: str) -> str:
    """Get relative path from base"""
    return os.path.relpath(file_path, base_path)

def should_skip_directory(dir_name: str) -> bool:
    """Check if directory should be skipped"""
    skip_dirs = ['.git', '__pycache__', 'node_modules', 'venv', '.venv', 'dist', 'build']
    return dir_name in skip_dirs

