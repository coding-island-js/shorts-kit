"""
build_data.py: line the slides up with the voice and wire in the visuals.

Usage:
  python scripts/build_data.py <slug> [--premium] [--music music/track.mp3]

Reads  work/<slug>/meta.json, words.json, broll/manifest.json, shots/*.png
Writes work/<slug>/data.json (the props for the Remotion render) and copies
the audio, clips and screenshots into work/<slug>/public/, which the render
uses as its public folder.

One slide per sentence (two per section at most), timed to where the voice
actually says it. A section whose Visual: names shot:file.png gets that
screenshot; every other section gets the next b-roll clip, in script order.
"""

import argparse
import re
import shutil
from pathlib import Path

from common import ROOT, FPS, WORK, load_brand, load_meta, read_json, write_json, fail

AUDIO_DELAY_FRAMES = 22   # matches KineticShort.tsx
ENTRANCE_PREROLL = 8      # show text a hair early so the entrance lands on the word
ENTRANCES = {
    "HOOK": ["scale-pop"],
    "PROBLEM": ["slide-up", "fade"],
    "STAKES": ["slide-left", "fade"],
    "PAYOFF": ["scale-pop", "fade"],
    "SOLUTION": ["scale-pop", "fade"],
}


def norm(w):
    return re.sub(r"[^\w]", "", w).lower()


def frame(sec):
    return max(0, AUDIO_DELAY_FRAMES + int(round(sec * FPS)) - ENTRANCE_PREROLL)


def sentences(text):
    parts = [p.strip() for p in re.split(r"(?<=[.?!])\s+", text.strip()) if p.strip()]
    return parts if len(parts) <= 2 else [parts[0], " ".join(parts[1:])]


def locate(phrase, words, cursor):
    """Find a phrase in the timed words at or after cursor. Returns (start, end, cursor)."""
    target = [norm(w) for w in phrase.split() if norm(w)]
    if not target:
        return None, None, cursor
    start = next((i for i in range(cursor, len(words)) if norm(words[i]["word"]) == target[0]), None)
    if start is None:
        return None, None, cursor
    # Anchor on the phrase's last word: speech engines write "200" where the script
    # says "two hundred", so counting tokens overshoots into the next section.
    end = min(start + len(target) - 1, len(words) - 1)
    for j in range(start, min(start + len(target) + 3, len(words))):
        if norm(words[j]["word"]) == target[-1]:
            end = j
            break
    return words[start]["start"], words[end]["start"] + 0.4, end + 1


def build_slides(sections, words, cta_seconds):
    slides, cursor, last_end = [], 0, 0.0
    for sec_idx, sec in enumerate(sections):
        if sec["name"] == "CTA":
            continue
        entrances = ENTRANCES.get(sec["name"], ["fade"])
        for i, sent in enumerate(sentences(sec["voice"])):
            start, end, cursor = locate(sent, words, cursor)
            if start is None or start < last_end:
                start = last_end + 0.1
                end = start + max(1.5, len(sent.split()) * 0.32)
            last_end = end
            slides.append({
                "section": sec["name"],
                "text": sent,
                "entrance": entrances[i % len(entrances)],
                "startFrame": frame(start),
                "durationInFrames": max(15, frame(end) - frame(start)),
                "_shot": sec.get("shot"),
                "_sec": sec_idx,
            })
    for a, b in zip(slides, slides[1:]):
        a["durationInFrames"] = b["startFrame"] - a["startFrame"]
    cta_start = slides[-1]["startFrame"] + slides[-1]["durationInFrames"] if slides else AUDIO_DELAY_FRAMES
    slides.append({"section": "CTA", "text": "", "entrance": "fade",
                   "startFrame": cta_start, "durationInFrames": int(cta_seconds * FPS)})
    return slides


def caption_chunks(words, script_text, max_words, cutoff):
    """Group timed words into short still phrases, breaking on the script's punctuation."""
    tokens, ti = script_text.split(), 0
    for w in words:
        w["_end"] = False
        for k in range(ti, min(ti + 4, len(tokens))):
            if norm(tokens[k]) == norm(w["word"]):
                w["_end"] = tokens[k].rstrip("\"'")[-1:] in ".?!,;:"
                ti = k + 1
                break

    to_f = lambda s: int(round(s * FPS)) + AUDIO_DELAY_FRAMES
    chunks, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= max_words or w["_end"]:
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)

    out = [{"start": to_f(c[0]["start"]), "end": to_f(c[-1]["end"]),
            "words": [{"text": w["word"], "ws": to_f(w["start"]), "we": to_f(w["end"])} for w in c]}
           for c in chunks]
    for a, b in zip(out, out[1:]):
        a["end"] = b["start"]
    if out:
        out[-1]["end"] += 8
    out = [c for c in out if c["start"] < cutoff - 4]
    for c in out:
        c["end"] = min(c["end"], cutoff - 2)
    return out


def stage(src, slug, name):
    """Copy a file into work/<slug>/public/ and return its staticFile() path."""
    dst = WORK / slug / "public" / name
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.is_file() or dst.stat().st_size != Path(src).stat().st_size:
        shutil.copy2(src, dst)
    return name


def wire_visuals(slides, slug):
    wd = WORK / slug
    manifest = wd / "broll" / "manifest.json"
    clips = [c["file"] for c in read_json(manifest)["clips"]] if manifest.is_file() else []
    shot_dir = wd / "shots"
    shots = sorted(p.name for p in shot_dir.glob("*.png")) if shot_dir.is_dir() else []
    # Each section keeps one visual. Clips and screenshots count separately, so a
    # shot: section doesn't use up a BROLL keyword meant for the next section.
    clip_of, shot_of = {}, {}
    for s in slides:
        shot = s.pop("_shot", None)
        sec = s.pop("_sec", None)
        if s["section"] == "CTA":
            continue
        if shot and not (shot_dir / shot).is_file():
            print(f"  WARNING: shot:{shot} not in work/{slug}/shots/, using the next visual instead")
            shot = None
        if shot:
            s["backgroundImage"] = stage(shot_dir / shot, slug, f"shots/{shot}")
        elif clips:
            clip = clips[clip_of.setdefault(sec, len(clip_of)) % len(clips)]
            s["backgroundVideo"] = stage(wd / "broll" / clip, slug, f"broll/{clip}")
            s["backgroundVideoStart"] = 0
        elif shots:
            pick = shots[shot_of.setdefault(sec, len(shot_of)) % len(shots)]
            s["backgroundImage"] = stage(shot_dir / pick, slug, f"shots/{pick}")
    return len(clips), len(shots)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--premium", action="store_true",
                    help="word-by-word captions, animated background, progress bar")
    ap.add_argument("--music", help="path to an mp3 you have the rights to")
    ap.add_argument("--music-volume", type=float, default=0.04)
    ap.add_argument("--cta-seconds", type=float, default=3.0)
    ap.add_argument("--caption-words", type=int, default=3)
    args = ap.parse_args()

    slug = args.slug
    meta = load_meta(slug)
    words_path = WORK / slug / "words.json"
    if not words_path.is_file():
        fail(f"work/{slug}/words.json not found. Run: python scripts/voiceover.py {slug}")
    words = read_json(words_path)

    slides = build_slides(meta["sections"], words, args.cta_seconds)
    n_clips, n_shots = wire_visuals(slides, slug)
    cta = slides[-1]
    total = cta["startFrame"] + cta["durationInFrames"] + 20

    data = {
        "title": meta["title"],
        "slug": slug,
        "fps": FPS,
        "width": 1080,
        "height": 1920,
        "totalDurationInFrames": total,
        "audioFile": stage(WORK / slug / "voice.mp3", slug, "voice.mp3"),
        "slides": slides,
        "brand": load_brand(meta["brand"]),
        "wordCaptions": args.premium,
        # With no footage or screenshots a static gradient looks unfinished, so animate it.
        "animatedBg": args.premium or not (n_clips or n_shots),
        "showProgress": args.premium,
        "captions": caption_chunks(words, meta["script"], args.caption_words, cta["startFrame"]) if args.premium else [],
    }
    if args.music:
        music = Path(args.music) if Path(args.music).is_absolute() else ROOT / args.music
        if not music.is_file():
            fail(f"music file not found: {args.music}")
        data["musicFile"] = stage(music, slug, "music" + music.suffix)
        data["musicVolume"] = args.music_volume

    write_json(WORK / slug / "data.json", data)
    print(f"Built work/{slug}/data.json: {len(slides)} slides, {total / FPS:.1f}s, "
          f"{n_clips} clips, {n_shots} screenshots{', premium' if args.premium else ''}")
    for s in slides:
        bg = s.get("backgroundImage") or s.get("backgroundVideo") or ""
        print(f"  {s['section']:9} {s['startFrame'] / FPS:5.1f}s  {(s['text'] or '(end card)')[:44]:44}  {bg.split('/')[-1]}")


if __name__ == "__main__":
    main()
