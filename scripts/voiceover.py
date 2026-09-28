"""
voiceover.py: speak the script and record when every word lands.

Usage:
  python scripts/voiceover.py <slug>                      # free Microsoft Edge voice
  python scripts/voiceover.py <slug> --voice en-US-AvaMultilingualNeural
  python scripts/voiceover.py <slug> --engine openai --voice nova

Writes:
  work/<slug>/voice.mp3
  work/<slug>/words.json   [{word, start, end}] in seconds, drives the captions

Edge is free and needs no key: it reports word timings as it speaks.
OpenAI (OPENAI_API_KEY) sounds a little richer; timings then come from Whisper.
Cost for a 15s Short on OpenAI is well under one cent.
"""

import argparse
import asyncio
import os
import re
import sys

from common import load_env, load_meta, work_dir, write_json, fail

EDGE_DEFAULT = "en-US-AndrewMultilingualNeural"
OPENAI_DEFAULT = "nova"


def speakable(text):
    text = re.sub(r"\[.*?\]", "", text)
    return text.replace("—", ", ").replace("–", ", ").strip()


async def edge(text, voice, rate, mp3_path):
    import edge_tts

    words = []
    comm = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
    with open(mp3_path, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start = chunk["offset"] / 10_000_000  # 100ns ticks
                words.append({
                    "word": chunk["text"],
                    "start": round(start, 3),
                    "end": round(start + chunk["duration"] / 10_000_000, 3),
                })
    return words


def openai_tts(text, voice, mp3_path):
    from openai import OpenAI

    client = OpenAI()
    with client.audio.speech.with_streaming_response.create(
        model="tts-1-hd", voice=voice, input=text
    ) as resp:
        resp.stream_to_file(str(mp3_path))
    with open(mp3_path, "rb") as f:
        result = client.audio.transcriptions.create(
            model="whisper-1", file=f,
            response_format="verbose_json", timestamp_granularities=["word"],
        )
    return [{"word": w.word.strip(), "start": w.start, "end": w.end} for w in result.words]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--engine", choices=["edge", "openai"], default=None)
    ap.add_argument("--voice", default=None)
    ap.add_argument("--rate", default="-5%", help="Edge only, e.g. -10%% or +5%%")
    args = ap.parse_args()

    load_env()
    engine = args.engine or os.environ.get("TTS_ENGINE", "edge")
    meta = load_meta(args.slug)
    text = speakable(meta["script"])
    out = work_dir(args.slug)
    mp3 = out / "voice.mp3"

    if engine == "openai":
        if not os.environ.get("OPENAI_API_KEY"):
            fail("OPENAI_API_KEY is not set in .env. Use --engine edge for the free voice.")
        voice = args.voice or os.environ.get("OPENAI_VOICE", OPENAI_DEFAULT)
        print(f"Voiceover: OpenAI tts-1-hd, voice {voice}")
        words = openai_tts(text, voice, mp3)
    else:
        voice = args.voice or os.environ.get("EDGE_TTS_VOICE", EDGE_DEFAULT)
        print(f"Voiceover: Edge (free), voice {voice}, rate {args.rate}")
        words = asyncio.run(edge(text, voice, args.rate, mp3))

    if not words:
        fail("no word timings came back, so captions cannot sync")
    write_json(out / "words.json", words)
    print(f"  work/{args.slug}/voice.mp3  ({len(words)} words, {words[-1]['end']:.1f}s)")


if __name__ == "__main__":
    main()
