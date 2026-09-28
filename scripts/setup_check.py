"""
setup_check.py: is this machine ready to make Shorts? Prints what is missing and how to fix it.

Usage:
  python scripts/setup_check.py
"""

import importlib.util
import os
import shutil
import subprocess
import sys

from common import ROOT, REMOTION, load_env

ok_all = True


def row(ok, label, fix="", required=True):
    global ok_all
    mark = "OK  " if ok else ("MISS" if required else "--  ")
    print(f"  [{mark}] {label}" + ("" if ok else f"\n         {fix}"))
    if required and not ok:
        ok_all = False


def has_module(name):
    return importlib.util.find_spec(name) is not None


def main():
    load_env()
    print("Shorts Kit setup check\n")

    print("Tools")
    row(sys.version_info >= (3, 10), f"Python {sys.version.split()[0]}", "Install Python 3.10 or newer")
    node = shutil.which("node")
    row(bool(node), "Node.js", "Install the LTS from https://nodejs.org")
    row(bool(shutil.which("ffmpeg")), "ffmpeg (used by the renderer)",
        "Windows: winget install Gyan.FFmpeg | Mac: brew install ffmpeg | Linux: apt install ffmpeg")

    print("\nPython packages")
    missing = [m for m in ("edge_tts", "PIL", "markdown", "playwright", "googleapiclient", "google_auth_oauthlib")
               if not has_module(m)]
    row(not missing, "requirements.txt installed", f"pip install -r requirements.txt   (missing: {', '.join(missing)})")
    if has_module("playwright"):
        probe = subprocess.run([sys.executable, "-c",
                                "from playwright.sync_api import sync_playwright as s\n"
                                "with s() as p: p.chromium.launch().close()"],
                               capture_output=True, text=True)
        row(probe.returncode == 0, "Playwright browser (for site and repo screenshots)",
            "python -m playwright install chromium", required=False)

    print("\nRenderer")
    row((REMOTION / "node_modules").is_dir(), "remotion/node_modules", "cd remotion && npm install")

    print("\nKeys (.env)")
    row((ROOT / ".env").is_file(), ".env file", "Copy .env.example to .env", required=False)
    row(bool(os.environ.get("PEXELS_API_KEY") or os.environ.get("PIXABAY_API_KEY")),
        "PEXELS_API_KEY or PIXABAY_API_KEY (stock b-roll, free)",
        "Free key at https://www.pexels.com/api/ then add PEXELS_API_KEY=... to .env", required=False)
    row(bool(os.environ.get("OPENAI_API_KEY")), "OPENAI_API_KEY (optional premium voice)",
        "Only needed for --engine openai. The free Edge voice works without it.", required=False)

    print("\nYouTube upload")
    row((ROOT / "client_secret.json").is_file(), "client_secret.json",
        "Only needed to upload. See docs/youtube-setup.md", required=False)
    row((ROOT / "token.json").is_file(), "token.json (signed in)",
        "Created the first time you upload.", required=False)

    print("\n" + ("Ready. Try: python make_short.py examples/broll-short.md" if ok_all
                  else "Fix the MISS lines above, then run this again."))
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
