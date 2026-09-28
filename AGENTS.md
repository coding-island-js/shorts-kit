# Instructions for AI coding agents

You are helping someone make YouTube Shorts with this repo. They may never have opened a terminal. You run every command yourself. Never hand them a command to paste unless you truly cannot run it (a browser sign-in, a key only they can copy).

## Rules

1. **Never commit or print secrets.** `.env`, `client_secret.json` and `token.json` stay local. They're gitignored, so keep it that way. Don't echo key values back into the chat.
2. **Show the script before you render.** Write the script, show it, and wait for a yes or for edits. Rendering is the slow part.
3. **Uploads are private unless the person says otherwise.** Ask before `--public`. Confirm the date and time zone before `--schedule`.
4. **Say what costs money before you spend it.** Everything here is free by default. Only `--engine openai` costs anything (about a cent per Short), and only if they add an OpenAI key.
5. **Explain in plain words.** Say "I'm installing the video renderer", not "running npm install in remotion/".

## Setup (first time)

Work through this in order and skip anything already done. `python scripts/setup_check.py` shows what's missing at any point.

1. **Python 3.10+.** Windows: `winget install Python.Python.3.12`. Mac: `brew install python`. Linux: the package manager.
2. **Node.js LTS.** Windows: `winget install OpenJS.NodeJS.LTS`. Mac: `brew install node`.
3. **ffmpeg.** Windows: `winget install Gyan.FFmpeg`. Mac: `brew install ffmpeg`. Linux: `apt install ffmpeg`.
   On Windows, open a new shell afterwards so PATH picks it up.
4. `pip install -r requirements.txt` (use a virtualenv if the person already has one set up).
5. `python -m playwright install chromium` (needed for site and repo screenshots).
6. `cd remotion && npm install` (the renderer). The first render also downloads a headless Chrome.
7. Copy `.env.example` to `.env`.
8. **Stock footage key (optional, free).** Walk them through it: go to https://www.pexels.com/api/, sign up, click "Your API Key", copy it. Then you write it into `.env` as `PEXELS_API_KEY=...`. Without it, b-roll Shorts fall back to animated text on a gradient.
9. Run `python scripts/setup_check.py` and fix anything marked MISS.
10. Prove it works: `python make_short.py examples/broll-short.md`, then tell them where the file is (`output/broll-short.mp4`) and open it if you can.

## Recipe 1: a Short about any topic, with stock footage

1. Ask for the topic and, if it's for a product, the URL they want in the end card.
2. If they have a brand, add it to `config/brands.json` (copy the `example` block) and ask for their colors, or pull them from their site.
3. Write `scripts-in/<slug>.md` in the format in `docs/script-format.md`, with a `BROLL:` line that has one concrete, filmable search term per section ("hands typing on laptop", not "productivity").
4. Show the script. Wait for approval.
5. `python make_short.py scripts-in/<slug>.md` (add `--premium` for word-by-word captions and an animated background).
6. Look at the result: pull a few frames with ffmpeg (`ffmpeg -ss 2 -i output/<slug>.mp4 -frames:v 1 frame.png`) and check them before you tell the person it's done. If a clip doesn't fit its line, change that `BROLL` term and run again.

## Recipe 2: a marketing Short from a website or a repo

1. `python scripts/site_to_short.py <url | github url | local folder> --slug <slug>`
   It saves screenshots to `work/<slug>/shots/` and writes `work/<slug>/brief.md` with the product's own headline, sections, buttons and prices.
2. Read the brief. Open two or three of the screenshots and look at them, so you know what each one shows.
3. Write `scripts-in/<slug>.md`. **The file name must match the slug** or the screenshots won't be found. Point each section at the screenshot that proves what the voice says: `Visual: shot:03-pricing.png`. Use only claims the brief supports. Don't invent features, numbers or customers.
4. Show the script. Wait for approval.
5. `python make_short.py scripts-in/<slug>.md --no-broll`
6. Check frames as in Recipe 1.

Private repo on GitHub? Clone it locally first and pass the folder path.

## Recipe 3: upload to YouTube

1. If `client_secret.json` isn't in the repo root, walk them through `docs/youtube-setup.md` one step at a time. Wait for each step before the next. They do the clicking in Google Cloud. You do everything else.
2. `python scripts/youtube_upload.py <slug>` (private), `--unlisted`, `--public`, or `--schedule 2026-10-01T16:00:00Z` (UTC, so convert their local time and say both).
3. The first run opens a browser for them to sign in. Tell them Google will warn that the app is unverified, and that that's expected because it's their own app.
4. Report the link. If Google locked the upload to private (unaudited project), tell them to flip it to Public in YouTube Studio.

## Map

| Path | What it is |
|---|---|
| `make_short.py` | One command: script to finished mp4 (and optional upload) |
| `scripts/convert_script.py` | Script .md to `work/<slug>/meta.json` |
| `scripts/voiceover.py` | Voice mp3 + word timings (free Edge, or OpenAI) |
| `scripts/fetch_broll.py` | Vertical stock clips from Pexels / Pixabay |
| `scripts/site_to_short.py` | Screenshots + brief from a site or repo |
| `scripts/build_data.py` | Times slides to the voice and wires in the visuals |
| `scripts/render.py` | Remotion render to `output/<slug>.mp4` |
| `scripts/generate_thumbnail.py` | `output/<slug>-thumb.png` |
| `scripts/youtube_upload.py` | Upload to the person's own channel |
| `remotion/src/KineticShort.tsx` | The video itself: layers, captions, end card |
| `config/brands.json` | Colors and end-card text per brand |
| `work/<slug>/` | Everything generated for one video. Safe to delete. |

## When something breaks

- **Anything at all:** run `python scripts/setup_check.py` first.
- **`npx` or `ffmpeg` not found after installing:** the shell needs restarting to see the new PATH.
- **Render fails on a video file:** a stock clip downloaded incomplete. Delete `work/<slug>/broll/` and run again.
- **Captions drift from the voice:** the Voice line has symbols the speech engine reads differently ("$5k", "w/"). Write it out the way it's said.
- **Upload says `invalid_grant`:** delete `token.json` and upload again to sign back in.
