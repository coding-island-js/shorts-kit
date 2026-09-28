"""Shared paths and helpers. Every script imports from here."""

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "work"
OUTPUT = ROOT / "output"
REMOTION = ROOT / "remotion"
FPS = 30

# Windows consoles default to cp1252 and choke on arrows and dashes in logs.
for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


def load_env():
    """Read .env in the repo root into os.environ (real env vars win)."""
    path = ROOT / ".env"
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if v and k not in os.environ:
            os.environ[k] = v


def work_dir(slug):
    d = WORK / slug
    d.mkdir(parents=True, exist_ok=True)
    return d


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_meta(slug):
    path = WORK / slug / "meta.json"
    if not path.is_file():
        fail(f"work/{slug}/meta.json not found. Run: python scripts/convert_script.py <script.md>")
    return read_json(path)


def load_brand(key):
    brands = read_json(ROOT / "config" / "brands.json")
    if key not in brands:
        print(f"  Brand '{key}' not in config/brands.json, using 'default'")
    return brands.get(key) or brands["default"]


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60] or "short"


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)
