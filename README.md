# Shorts Kit

**Make YouTube Shorts by talking to your AI agent.** Stock-footage Shorts, product demos built from any website or repo, and uploads to your own channel. Free, and it runs on your machine.

<p align="center">
  <img src="docs/assets/preview.gif" width="480" alt="Two Shorts made with the kit: one over stock footage, one built from screenshots of a website">
</p>

I make a lot of Shorts. For my own products, for local businesses, for friends.

So I built the thing I actually use. You give it a script, or your agent writes one, and it turns it into a finished vertical video. The voice is timed to the word. The captions land when the words land. Stock footage or screenshots sit behind them. And it ends on your brand's card, with a thumbnail made to match.

Then it uploads to your channel.

No subscription. No watermark. No editor. And you don't have to open a terminal. You paste one prompt into your agent and it does the setup.

## Start here

**1. Open your AI coding agent.** Any of these works. Use the desktop app or the editor, whichever you already have.

| Agent | Get it |
|---|---|
| Claude Code | [claude.com/claude-code](https://claude.com/claude-code) |
| Codex | [openai.com/codex](https://openai.com/codex) |
| Cursor | [cursor.com](https://cursor.com) (pick any model, including Grok) |
| Gemini CLI | [github.com/google-gemini/gemini-cli](https://github.com/google-gemini/gemini-cli) |

Chat apps like ChatGPT, Claude.ai or Grok on the web can't run things on your computer, so they can't do this part. Grok works fine inside Cursor.

**2. Paste this.** It's the same prompt for every agent.

```text
Set up Shorts Kit for me from https://github.com/coding-island-js/shorts-kit

Clone it into a folder called shorts-kit in my home folder. Then read AGENTS.md
and follow the Setup section. Install anything I'm missing. Run every command
yourself and only stop when you need me to sign up for something or click
something in a browser. When it's done, make the example Short and tell me
where the video is.
```

That's it. It takes about ten minutes the first time, mostly downloads.

Every agent reads the same instructions. Codex, Cursor and Gemini CLI read [`AGENTS.md`](AGENTS.md) on their own. Claude Code reads [`CLAUDE.md`](CLAUDE.md), which loads the same file. So the steps don't change when you switch agents.

## Then ask for a Short

Open your agent in the `shorts-kit` folder and say what you want. Some to copy:

**A Short about anything, with stock footage**
```text
Make a Short about why most people quit the gym in February.
Stock footage, 15 seconds, end on a question.
```

**A demo of your product, from its website**
```text
Make a marketing Short for https://your-product.com.
Use screenshots of the site. Hook on the problem it solves, end on the URL.
```

**A demo of your code, from its repo**
```text
Make a Short that shows off this repo: https://github.com/you/your-repo
It's for developers. Show the README and the live site if it has one.
```

**Your brand on it**
```text
Add my brand. The colors are on https://your-product.com, pull them from there.
The end card should say "your-product.com" and "Free to try".
```

**Upload it**
```text
Connect my YouTube channel and upload the last Short as private.
```

**A week of them**
```text
Write five Shorts about [topic], one idea each. Show me all five scripts
first. After I approve, render them and schedule one a day at 9am my time.
```

Your agent shows you the script before it renders anything. Say "looks good" or tell it what to change.

Finished videos land in `output/`.

## What it costs

Nothing, by default.

| Part | Cost |
|---|---|
| Voice (Microsoft Edge voices) | Free, no key |
| Captions timed to each word | Free, no key |
| Stock footage from [Pexels](https://www.pexels.com/api/) and [Pixabay](https://pixabay.com/api/docs/) | Free key, no card |
| Screenshots of sites and repos | Free |
| Rendering with [Remotion](https://remotion.dev) | Free on your machine ([license below](#licenses-and-credits)) |
| Uploading to YouTube | Free, uses your own Google project |
| Premium voice, if you want it | About a cent per Short with an OpenAI key |

You pay for your AI agent, if it isn't free. That's all.

## Connecting YouTube

Your agent walks you through it with [`docs/youtube-setup.md`](docs/youtube-setup.md). You make your own Google Cloud project, download one file, and sign in once. The videos go straight to your channel, and nobody else holds your login.

Uploads are private by default. You look at it on YouTube first, then flip it to public.

## How it works

```
script.md ─► voice + word timings ─► b-roll or screenshots ─► slides timed to the voice ─► Remotion render ─► thumbnail ─► YouTube
```

A Short is a Markdown file. Each section has a line to say and a note about what to show. [`docs/script-format.md`](docs/script-format.md) has the format.

```text
[0-3s] HOOK
Voice: "You don't need another productivity app."
Visual: Sunrise through a window.

[3-8s] PAYOFF
Voice: "Write three lines before you touch your phone."
Visual: shot:02-pricing.png
```

The free voice reports when every word starts and ends. So the captions line up without a speech-to-text pass, and without a GPU.

<details>
<summary><b>Commands, if you'd rather run it yourself</b></summary>

```bash
# once
pip install -r requirements.txt
python -m playwright install chromium
cd remotion && npm install && cd ..
cp .env.example .env              # add PEXELS_API_KEY for stock footage

python scripts/setup_check.py     # what's missing

# a stock-footage Short
python make_short.py examples/broll-short.md
python make_short.py examples/broll-short.md --premium        # word-by-word captions, animated background

# a Short from a website or repo
python scripts/site_to_short.py https://your-product.com --slug my-demo
#   write scripts-in/my-demo.md from work/my-demo/brief.md, using shot:<file> visuals
python make_short.py scripts-in/my-demo.md --no-broll

# upload
python scripts/youtube_upload.py my-demo                       # private
python scripts/youtube_upload.py my-demo --schedule 2026-10-01T16:00:00Z
```

Every step is its own script in `scripts/`, if you want to run one on its own or swap it out.

</details>

<details>
<summary><b>What's in the repo</b></summary>

| Path | What it is |
|---|---|
| `AGENTS.md` | The instructions your agent follows |
| `make_short.py` | One command, script to finished video |
| `scripts/` | Each step on its own: voice, b-roll, screenshots, timing, render, thumbnail, upload |
| `remotion/src/KineticShort.tsx` | The video itself. Layers, captions, end card. Change this to change the look. |
| `config/brands.json` | Your colors and end-card text |
| `examples/` | Two scripts to start from |
| `docs/` | Script format and YouTube setup |
| `work/<slug>/` | Everything made for one video. Safe to delete. |

</details>

## Make it yours

Fork it. Change anything.

The look lives in one file, [`remotion/src/KineticShort.tsx`](remotion/src/KineticShort.tsx). Run `npm run studio` inside `remotion/` to watch your changes live. Or just ask your agent: *"make the captions bigger and yellow"*.

If you build something good on top of it, tell me. I'm [@codingRaj](https://x.com/codingRaj) on X.

## Licenses and credits

- **This repo:** MIT. Use it for anything.
- **[Remotion](https://remotion.dev) does the rendering.** It's free for individuals and for companies of up to three people. Bigger companies need a [Remotion company license](https://www.remotion.dev/license).
- **Voices** come from Microsoft Edge's read-aloud service through [edge-tts](https://github.com/rany2/edge-tts). It's free, but it isn't an official Microsoft API, so it could change.
- **Stock footage** comes from [Pexels](https://www.pexels.com/license/) and [Pixabay](https://pixabay.com/service/license-summary/). Both are free to use in your videos. The clip credits are saved in `work/<slug>/broll/manifest.json`.
- **Music** is up to you. Only use tracks you have the rights to (`--music path/to/track.mp3`). The YouTube Audio Library is a good place to start.
