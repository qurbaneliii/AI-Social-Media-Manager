from __future__ import annotations

import os
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP_DIR))
os.environ.setdefault("ARIA_ENV", "test")
os.environ.setdefault("AI_MOCK_MODE", "true")

