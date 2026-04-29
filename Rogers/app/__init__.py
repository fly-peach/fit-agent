"""App Package"""
import sys
from pathlib import Path

# Ensure src/ is importable before any module imports harness tools
_APP_DIR = Path(__file__).resolve().parent
_src = str(_APP_DIR.parent / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

from .main import app

__all__ = ["app"]
