# Script format

A Short is one Markdown file. The file name becomes the slug, so `scripts-in/morning-routine.md` renders to `output/morning-routine.mp4`.

```
TITLE: You Don't Need Another App. You Need a Morning. #Shorts
THUMBNAIL: "ONE MORNING" | subtext: "Not one more app"
BRAND: default
BROLL: sunrise window, coffee pouring, notebook writing
DESCRIPTION: Optional first line of the YouTube description.

---

[0-3s] HOOK
Voice: "You don't need another productivity app."
Visual: Sunrise through a window.

[3-8s] PROBLEM
Voice: "You have nine already. Every one of them starts at ten a.m."
Visual: Coffee pouring into a mug.

[8-13s] PAYOFF
Voice: "Write three lines before you touch your phone. That's the whole system."
Visual: shot:02-pricing.png

[13-16s] CTA
Voice: "Try it tomorrow."
Visual: End card.

---

METADATA:
  tags: [morning routine, productivity, journaling]
  category_id: 22
```

## Header lines

| Line | Required | What it does |
|---|---|---|
| `TITLE:` | yes | YouTube title. Keep it under 60 characters so it isn't cut off. |
| `THUMBNAIL:` | no | Big text in quotes, optional `subtext: "..."`. Defaults to the first three words of the title. |
| `BRAND:` | no | A key from `config/brands.json`. Sets colors and the end card. Defaults to `default`. |
| `BROLL:` | no | Stock footage search terms, comma separated, one per section. Without it, the words in each `Visual:` line are used. |
| `DESCRIPTION:` | no | First line of the YouTube description. Tags become hashtags under it. |
| `COMMENT:` | no | Posted as the first comment when you upload as public. Pin it in YouTube Studio. |

## Sections

Each section is three lines: `[start-end s] NAME`, then `Voice: "..."`, then `Visual: ...`.

- **Voice** is what gets spoken, and it is also the on-screen text. One or two sentences per section.
- **The timings are a guide, not a contract.** The real timing comes from the voice, word by word.
- **NAME** sets the text entrance. `HOOK`, `PROBLEM`, `STAKES`, `PAYOFF` and `SOLUTION` each animate differently. `CTA` is always last and shows the brand end card.
- **Visual** is a note for stock footage, or `shot:<file>.png` to use a screenshot from `work/<slug>/shots/`.

Keep double quotes out of the Voice line. Use single quotes inside it.

## Writing one that works

- The first sentence is the whole video. Say the problem or the surprise in under two seconds. No "hey guys", no "in this video".
- 10 to 20 seconds total. Shorts are judged on how many people watch to the end.
- One idea per Short. If there are two, make two Shorts.
- Write for the ear. Say "ten a.m.", not "10am". Say "dot com", not ".com".
- The CTA is one action: a URL, "follow", or a question. Never all three.

## Brands

`config/brands.json` holds the colors. Copy the `example` block, rename the key, change the hex values and the `cta` / `ctaUrl` / `ctaSubtext` lines, then use the key in `BRAND:`.
