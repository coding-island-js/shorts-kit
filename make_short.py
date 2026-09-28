"""
make_short.py: one command from a script .md to a finished Short.

Usage:
  python make_short.py scripts-in/my-short.md
  python make_short.py scripts-in/my-short.md --premium --music music/bed.mp3
  python make_short.py scripts-in/my-short.md --no-broll          # text + screenshots only
  python make_short.py scripts-in/my-short.md --upload --schedule 2026-10-01T16:00:00Z

Steps: convert -> voiceover -> b-roll -> timing -> render -> thumbnail -> (upload)
Output: output/<slug>.mp4 and output/<slug>-thumb.png
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))

from common import WORK, load_env  # noqa: E402


def step(name, *args):
    print(f"\n== {name} ==", flush=True)
    cmd = [sys.executable, str(ROOT / "scripts" / f"{name}.py"), *args]
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    if subprocess.run(cmd, cwd=ROOT, env=env).returncode != 0:
        print(f"\nStopped at {name}. Fix the error above and run the same command again.")
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script", help="path to the script .md")
    ap.add_argument("--premium", action="store_true", help="word-by-word captions, animated bg, progress bar")
    ap.add_argument("--no-broll", action="store_true", help="skip stock footage")
    ap.add_argument("--keywords", help="b-roll search terms, comma separated")
    ap.add_argument("--voice", help="voice name (Edge or OpenAI)")
    ap.add_argument("--engine", choices=["edge", "openai"])
    ap.add_argument("--music", help="mp3 you have the rights to use")
    ap.add_argument("--upload", action="store_true", help="upload to YouTube (private unless told otherwise)")
    ap.add_argument("--public", action="store_true")
    ap.add_argument("--unlisted", action="store_true")
    ap.add_argument("--schedule", help="publish time, e.g. 2026-10-01T16:00:00Z")
    a = ap.parse_args()

    load_env()
    slug = Path(a.script).stem

    step("convert_script", a.script)

    vo = [slug]
    if a.engine:
        vo += ["--engine", a.engine]
    if a.voice:
        vo += ["--voice", a.voice]
    step("voiceover", *vo)

    has_broll_key = os.environ.get("PEXELS_API_KEY") or os.environ.get("PIXABAY_API_KEY")
    if a.no_broll:
        print("\n== fetch_broll == skipped (--no-broll)", flush=True)
    elif not has_broll_key:
        print("\n== fetch_broll == skipped: no PEXELS_API_KEY in .env (free at pexels.com/api)", flush=True)
    else:
        step("fetch_broll", slug, *(["--keywords", a.keywords] if a.keywords else []))

    build = [slug]
    if a.premium:
        build.append("--premium")
    if a.music:
        build += ["--music", a.music]
    step("build_data", *build)
    step("render", slug)
    step("generate_thumbnail", slug)

    if a.upload:
        up = [slug]
        if a.schedule:
            up += ["--schedule", a.schedule]
        elif a.public:
            up.append("--public")
        elif a.unlisted:
            up.append("--unlisted")
        step("youtube_upload", *up)

    print(f"\nDone: output/{slug}.mp4")
    print(f"      output/{slug}-thumb.png")
    print(f"      work files in {WORK.name}/{slug}/")


if __name__ == "__main__":
    main()
