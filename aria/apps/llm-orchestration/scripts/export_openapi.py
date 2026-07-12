from __future__ import annotations

import json
import os
import sys
from pathlib import Path


SERVICE_DIR = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = SERVICE_DIR.parents[2]
APP_DIR = SERVICE_DIR / "app"
OUTPUT = REPOSITORY_ROOT / "aria-frontend" / "openapi" / "aria.json"

os.environ.setdefault("ARIA_ENV", "test")
sys.path.insert(0, str(APP_DIR))

from main import app  # noqa: E402


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
