"""
fetch_broll.py: download free vertical stock clips for a Short.

Usage:
  python scripts/fetch_broll.py <slug>
  python scripts/fetch_broll.py <slug> --keywords "laptop typing,city night,coffee"

Keywords come from --keywords, else the script's BROLL: line, else its Visual: lines.
Pexels first (portrait clips), Pixabay as a fallback. Both are free:
  PEXELS_API_KEY   https://www.pexels.com/api/
  PIXABAY_API_KEY  https://pixabay.com/api/docs/

Writes work/<slug>/broll/*.mp4 and work/<slug>/broll/manifest.json
"""

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

from common import load_env, load_meta, work_dir, write_json, fail

UA = {"User-Agent": "shorts-kit/1.0 (+https://github.com)"}
STOP = set("a an the and or but with of to in on for at by from is are it this that your my our show shows showing".split())


def get_json(url, headers=None):
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"    request failed: {e}")
        return {}


def keywords_from_visuals(meta, limit=6):
    """Turn 'Visual: close-up of hands typing on a laptop' into 'hands typing laptop'."""
    out = []
    for s in meta["sections"]:
        if s["name"] == "CTA" or s.get("shot"):
            continue
        words = [w for w in re.findall(r"[a-z]+", s["visual"].lower()) if w not in STOP and len(w) > 2]
        if words:
            out.append(" ".join(words[:3]))
    return out[:limit]


def search_pexels(query, key):
    q = urllib.parse.urlencode({"query": query, "per_page": 5, "orientation": "portrait"})
    data = get_json(f"https://api.pexels.com/videos/search?{q}", {"Authorization": key})
    for video in data.get("videos", []):
        files = [f for f in video.get("video_files", []) if f.get("height", 0) >= 1280]
        files = files or video.get("video_files", [])
        if not files:
            continue
        best = min(files, key=lambda f: abs(f.get("height", 0) - 1920))
        return {"source": "pexels", "url": best["link"], "duration": video.get("duration", 0),
                "credit": video.get("user", {}).get("name", ""), "page": video.get("url", "")}
    return None


def search_pixabay(query, key):
    q = urllib.parse.urlencode({"key": key, "q": query, "video_type": "film", "per_page": 5, "safesearch": "true"})
    data = get_json(f"https://pixabay.com/api/videos/?{q}")
    for hit in data.get("hits", []):
        for size in ("large", "medium", "small"):
            v = hit.get("videos", {}).get(size, {})
            if v.get("url"):
                return {"source": "pixabay", "url": v["url"], "duration": hit.get("duration", 0),
                        "credit": hit.get("user", ""), "page": hit.get("pageURL", "")}
    return None


def download(url, path):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r, open(path, "wb") as f:
        f.write(r.read())
    return path.stat().st_size / 1_048_576


def fetch(slug, keywords=None):
    load_env()
    pexels, pixabay = os.environ.get("PEXELS_API_KEY"), os.environ.get("PIXABAY_API_KEY")
    if not pexels and not pixabay:
        fail("add PEXELS_API_KEY (or PIXABAY_API_KEY) to .env. Both are free.")

    meta = load_meta(slug)
    keywords = keywords or meta.get("broll_keywords") or keywords_from_visuals(meta)
    if not keywords:
        fail("no keywords. Add a BROLL: line to the script or pass --keywords")

    out = work_dir(slug) / "broll"
    out.mkdir(exist_ok=True)
    clips = []
    print(f"B-roll for {slug}: {', '.join(keywords)}")
    for i, kw in enumerate(keywords, 1):
        hit = (pexels and search_pexels(kw, pexels)) or (pixabay and search_pixabay(kw, pixabay))
        if not hit:
            print(f"  [{i}] {kw}: nothing found")
            continue
        path = out / f"{i:02d}-{re.sub(r'[^a-z0-9]+', '-', kw.lower()).strip('-')}.mp4"
        try:
            mb = download(hit["url"], path)
        except Exception as e:
            print(f"  [{i}] {kw}: download failed ({e})")
            continue
        clips.append({"keyword": kw, "file": path.name, **hit})
        print(f"  [{i}] {kw}: {hit['source']}, {mb:.1f} MB")
        time.sleep(0.3)

    write_json(out / "manifest.json", {"slug": slug, "clips": clips})
    if not clips:
        fail("no clips downloaded")
    print(f"  {len(clips)} clips in work/{slug}/broll/")
    return clips


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--keywords", help="comma separated")
    a = ap.parse_args()
    kws = [k.strip() for k in a.keywords.split(",") if k.strip()] if a.keywords else None
    fetch(a.slug, kws)
