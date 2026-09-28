"""
site_to_short.py: point it at a website or a code repo, get screenshots and a brief.

Usage:
  python scripts/site_to_short.py https://yourproduct.com
  python scripts/site_to_short.py https://github.com/owner/repo
  python scripts/site_to_short.py ../path/to/local/repo
  python scripts/site_to_short.py https://yourproduct.com --slug launch-short --max-shots 6

Writes:
  work/<slug>/shots/NN-name.png   screenshots sized for the Short's card
  work/<slug>/brief.md            what the product is, in its own words

Next step: write scripts-in/<slug>.md from the brief (your AI agent does this;
see docs/script-format.md), pointing sections at screenshots with
"Visual: shot:01-hero.png", then:
  python make_short.py scripts-in/<slug>.md --no-broll
"""

import argparse
import json
import re
import urllib.request
from pathlib import Path

from common import work_dir, slugify, fail

# The screenshot card in KineticShort is 960 x 883. Capture at that shape, 2x for sharpness.
VIEWPORT = {"width": 960, "height": 883}
UA = {"User-Agent": "shorts-kit/1.0"}

README_CSS = """
body{margin:0;background:#0d1117;color:#e6edf3;font:22px/1.55 -apple-system,Segoe UI,Helvetica,Arial,sans-serif}
main{padding:56px 64px}
h1{font-size:52px;margin:0 0 20px}h2{font-size:38px;margin:44px 0 16px;border-bottom:1px solid #30363d;padding-bottom:10px}
h3{font-size:28px}a{color:#58a6ff}img{max-width:100%}
code{background:#161b22;padding:2px 6px;border-radius:6px;font-size:.9em}
pre{background:#161b22;padding:20px;border-radius:12px;overflow:hidden}pre code{padding:0}
table{border-collapse:collapse}td,th{border:1px solid #30363d;padding:6px 12px}
"""


def fetch_text(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", "replace")


def capture_page(page, out_dir, max_shots, prefix_start=1, first="hero"):
    """Hero shot, then one shot per distinct section heading. Returns shot names."""
    names = []
    page.wait_for_timeout(1200)
    path = out_dir / f"{prefix_start:02d}-{first}.png"
    page.screenshot(path=str(path))
    names.append(path.name)

    headings = page.eval_on_selector_all(
        "h2, section h3",
        "els => els.filter(e => e.offsetParent && e.innerText.trim().length > 2)"
        ".map(e => ({text: e.innerText.trim().slice(0, 60), y: e.getBoundingClientRect().top + window.scrollY}))",
    )
    last_y = 0
    for h in headings:
        if len(names) >= max_shots:
            break
        if h["y"] - last_y < VIEWPORT["height"] * 0.6:
            continue  # too close to the previous shot, would look the same
        page.evaluate(f"window.scrollTo(0, {max(0, h['y'] - 80)})")
        page.wait_for_timeout(500)
        path = out_dir / f"{prefix_start + len(names):02d}-{slugify(h['text'])[:30]}.png"
        page.screenshot(path=str(path))
        names.append(path.name)
        last_y = h["y"]
    return names


def page_facts(page):
    return page.evaluate("""() => {
        const meta = n => (document.querySelector(`meta[name="${n}"], meta[property="${n}"]`) || {}).content || '';
        const txt = sel => [...document.querySelectorAll(sel)].map(e => e.innerText.replace(/\\s+/g, ' ').trim()).filter(Boolean);
        const body = document.body.innerText;
        return {
            title: document.title,
            description: meta('description') || meta('og:description'),
            theme_color: meta('theme-color'),
            h1: txt('h1').slice(0, 3),
            h2: txt('h2').slice(0, 12),
            buttons: [...new Set(txt('a[class*=btn], a[class*=button], button, [role=button]'))].filter(t => t.length < 40).slice(0, 10),
            prices: [...new Set(body.match(/[$€£]\\s?\\d[\\d,.]*(?:\\s?\\/\\s?(?:mo|month|yr|year|week|wk))?/gi) || [])].slice(0, 6),
            paragraphs: txt('main p, section p, p').filter(t => t.length > 60).slice(0, 8),
        };
    }""")


def shoot_url(url, out_dir, max_shots):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT, device_scale_factor=2)
        page.goto(url, wait_until="networkidle", timeout=45000)
        facts = page_facts(page)
        shots = capture_page(page, out_dir, max_shots)
        browser.close()
    return facts, shots


def shoot_html(html, out_dir, max_shots, start):
    from playwright.sync_api import sync_playwright

    # Load from a file, not set_content, so the <base> tag can resolve the README's images.
    html_path = out_dir.parent / "readme.html"
    html_path.write_text(html, encoding="utf-8")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT, device_scale_factor=2)
        page.goto(html_path.as_uri(), wait_until="networkidle")
        shots = capture_page(page, out_dir, max_shots, prefix_start=start, first="readme")
        browser.close()
    return shots


def readme_html(md_text, base):
    import markdown
    body = markdown.markdown(md_text, extensions=["fenced_code", "tables", "md_in_html"])
    return (f'<html><head><base href="{base}"><style>{README_CSS}</style></head>'
            f"<body><main>{body}</main></body></html>")


def from_repo(target, out_dir, max_shots):
    """GitHub URL or local folder. Returns (facts, shots, readme_text)."""
    gh = re.match(r"https?://github\.com/([^/]+)/([^/#?]+)", target)
    facts, homepage, readme, base = {}, "", "", ""
    if gh:
        owner, repo = gh.group(1), gh.group(2).removesuffix(".git")
        try:
            info = json.loads(fetch_text(f"https://api.github.com/repos/{owner}/{repo}"))
            facts = {"title": info.get("full_name"), "description": info.get("description") or "",
                     "stars": info.get("stargazers_count"), "topics": info.get("topics", []),
                     "language": info.get("language")}
            homepage = info.get("homepage") or ""
            branch = info.get("default_branch", "main")
        except Exception as e:
            fail(f"could not read {owner}/{repo} from GitHub ({e}). Private repos need a local clone.")
        for name in ("README.md", "readme.md", "README.MD"):
            try:
                readme = fetch_text(f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{name}")
                base = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/"
                break
            except Exception:
                continue
    else:
        root = Path(target).expanduser().resolve()
        if not root.is_dir():
            fail(f"{target} is not a URL or a folder")
        readme_path = next((p for p in root.iterdir() if p.name.lower() == "readme.md"), None)
        readme = readme_path.read_text(encoding="utf-8", errors="replace") if readme_path else ""
        facts = {"title": root.name}
        base = root.as_uri() + "/"
        pkg = root / "package.json"
        if pkg.is_file():
            data = json.loads(pkg.read_text(encoding="utf-8"))
            facts.update({"title": data.get("name", root.name), "description": data.get("description", "")})
            homepage = data.get("homepage", "")
        pyproject = root / "pyproject.toml"
        if pyproject.is_file():
            m = re.search(r'^description\s*=\s*"([^"]+)"', pyproject.read_text(encoding="utf-8"), re.M)
            if m:
                facts.setdefault("description", m.group(1))

    shots = []
    if homepage.startswith("http"):
        print(f"  Live site found: {homepage}")
        site_facts, shots = shoot_url(homepage, out_dir, max(1, max_shots // 2))
        facts["homepage"] = homepage
        facts["site"] = site_facts
    if readme and len(shots) < max_shots:
        shots += shoot_html(readme_html(readme, base), out_dir, max_shots - len(shots), start=len(shots) + 1)
    return facts, shots, readme


def write_brief(path, target, facts, shots, readme):
    lines = [f"# Brief: {facts.get('title') or target}", "", f"Source: {target}", ""]
    site = facts.get("site", facts)
    for key in ("description", "stars", "language", "topics", "homepage", "theme_color"):
        val = facts.get(key) or site.get(key)
        if val:
            lines.append(f"- **{key}**: {val}")
    for key, label in (("h1", "Headline"), ("h2", "Section headings"), ("buttons", "Buttons / CTAs"),
                       ("prices", "Prices on the page"), ("paragraphs", "Body copy")):
        vals = site.get(key)
        if vals:
            lines += ["", f"## {label}", *[f"- {v}" for v in vals]]
    if readme:
        lines += ["", "## README (first 3000 characters)", "", readme[:3000]]
    lines += ["", "## Screenshots", *[f"- shot:{s}" for s in shots]]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", help="https://site, https://github.com/owner/repo, or a local folder")
    ap.add_argument("--slug")
    ap.add_argument("--max-shots", type=int, default=6)
    a = ap.parse_args()

    is_repo = "github.com/" in a.target or not a.target.startswith("http")
    name = a.slug or slugify(re.sub(r"https?://(www\.)?", "", a.target.rstrip("/")).split("/")[-1 if is_repo else 0])
    out = work_dir(name)
    shots_dir = out / "shots"
    shots_dir.mkdir(exist_ok=True)
    for old in shots_dir.glob("*.png"):
        old.unlink()

    print(f"Reading {a.target} ...")
    if is_repo:
        facts, shots, readme = from_repo(a.target, shots_dir, a.max_shots)
    else:
        facts, shots = shoot_url(a.target, shots_dir, a.max_shots)
        readme = ""
    if not shots:
        fail("no screenshots captured")
    write_brief(out / "brief.md", a.target, facts, shots, readme)

    print(f"  {len(shots)} screenshots in work/{name}/shots/")
    for s in shots:
        print(f"    {s}")
    print(f"  Brief: work/{name}/brief.md")
    print(f"\nNext: write scripts-in/{name}.md from the brief (Visual: shot:<file> per section),")
    print(f"      then: python make_short.py scripts-in/{name}.md --no-broll")


if __name__ == "__main__":
    main()
