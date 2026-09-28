"""
render.py: render work/<slug>/data.json to output/<slug>.mp4 with Remotion.

Usage:
  python scripts/render.py <slug>

First run installs the renderer (remotion/node_modules) and downloads a
headless Chrome, which takes a few minutes. After that a 15s Short renders
in about a minute.
"""

import shutil
import subprocess
import sys

from common import OUTPUT, REMOTION, WORK, fail


def npx():
    exe = shutil.which("npx") or shutil.which("npx.cmd")
    if not exe:
        fail("Node.js is not installed (npx not found). Install the LTS from nodejs.org")
    return exe


def render(slug):
    props = WORK / slug / "data.json"
    if not props.is_file():
        fail(f"work/{slug}/data.json not found. Run: python scripts/build_data.py {slug}")
    if not (REMOTION / "node_modules").is_dir():
        print("Installing the renderer (one time)...")
        npm = shutil.which("npm") or shutil.which("npm.cmd")
        subprocess.run([npm, "install", "--no-audit", "--no-fund"], cwd=REMOTION, check=True)

    OUTPUT.mkdir(exist_ok=True)
    out = OUTPUT / f"{slug}.mp4"
    cmd = [npx(), "remotion", "render", "src/index.ts", "KineticShort", str(out),
           f"--props={props}", f"--public-dir={WORK / slug / 'public'}", "--log=warn"]
    print(f"Rendering {slug}...")
    if subprocess.run(cmd, cwd=REMOTION).returncode != 0:
        fail("render failed (see the Remotion error above)")
    print(f"  output/{slug}.mp4  ({out.stat().st_size / 1_048_576:.1f} MB)")
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        fail("usage: python scripts/render.py <slug>")
    render(sys.argv[1])
