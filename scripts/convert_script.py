"""
convert_script.py: turn a script .md into work/<slug>/meta.json.

Usage:
  python scripts/convert_script.py scripts-in/my-short.md

The slug is the file name. Format is in docs/script-format.md.
"""

import re
import sys
from pathlib import Path

from common import work_dir, write_json, fail

SECTION = re.compile(
    r'\[(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)s\]\s*([\w-]+)\s*\n'
    r'Voice:\s*"([^"]+)"\s*'
    r'(?:\nVisual:\s*(.+?))?(?=\n\s*\[|\n---|\nMETADATA|\Z)',
    re.DOTALL,
)


def header(content, name, default=""):
    m = re.search(rf"^{name}:\s*(.+)$", content, re.MULTILINE)
    return m.group(1).strip() if m else default


def parse(md_path):
    content = Path(md_path).read_text(encoding="utf-8")

    thumb_raw = header(content, "THUMBNAIL")
    thumb_text = re.search(r'"([^"]+)"', thumb_raw)
    thumb_sub = re.search(r'subtext:\s*"([^"]+)"', thumb_raw)

    sections = []
    for m in SECTION.finditer(content):
        visual = (m.group(5) or "").strip()
        shot = re.search(r"shot:\s*([\w./-]+\.(?:png|jpe?g|webp))", visual, re.IGNORECASE)
        sections.append({
            "start_s": float(m.group(1)),
            "end_s": float(m.group(2)),
            "name": m.group(3).upper(),
            "voice": m.group(4).strip(),
            "visual": visual,
            "shot": shot.group(1) if shot else None,
        })
    if not sections:
        fail(f"no sections found in {md_path}. Each needs a [0-2s] NAME line then Voice: \"...\"")

    tags_m = re.search(r"tags:\s*\[([^\]]+)\]", content)
    tags = [t.strip().strip("\"'") for t in tags_m.group(1).split(",")] if tags_m else []
    cat_m = re.search(r"category_id:\s*(\d+)", content)
    broll = [k.strip() for k in header(content, "BROLL").split(",") if k.strip()]

    title = header(content, "TITLE", "Untitled")
    voice_lines = [s["voice"] for s in sections]
    description = header(content, "DESCRIPTION") or voice_lines[0]
    hashtags = " ".join("#" + re.sub(r"\W", "", t) for t in tags[:5])

    return {
        "title": title,
        "brand": header(content, "BRAND", "default").split()[0],
        "description": f"{description}\n\n{hashtags}".strip(),
        "tags": tags,
        "category_id": cat_m.group(1) if cat_m else "28",
        "thumbnail_text": thumb_text.group(1) if thumb_text else " ".join(title.split()[:3]),
        "thumbnail_subtext": thumb_sub.group(1) if thumb_sub else "",
        "broll_keywords": broll,
        "first_comment": header(content, "COMMENT"),
        "sections": sections,
        "script": " ".join(voice_lines),
    }


def convert(md_path):
    md_path = Path(md_path)
    if not md_path.is_file():
        fail(f"{md_path} not found")
    slug = md_path.stem
    meta = parse(md_path)
    meta["slug"] = slug
    meta["source"] = str(md_path.resolve())
    write_json(work_dir(slug) / "meta.json", meta)

    print(f"Converted {md_path.name} -> work/{slug}/meta.json")
    print(f"  Title: {meta['title']}")
    print(f"  Brand: {meta['brand']}   Sections: {len(meta['sections'])}   Words: {len(meta['script'].split())}")
    shots = [s["shot"] for s in meta["sections"] if s["shot"]]
    if shots:
        print(f"  Screenshots: {', '.join(shots)}")
    return slug


if __name__ == "__main__":
    if len(sys.argv) < 2:
        fail("usage: python scripts/convert_script.py <script.md>")
    convert(sys.argv[1])
