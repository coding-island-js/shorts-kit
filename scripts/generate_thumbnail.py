"""generate_thumbnail.py: branded 1080x1920 thumbnail, big headline on a solid brand color.

Design:
  - Solid brand.bg background (no green gradient, no mascot, no gift box)
  - Max-fit headline in brand.text color
  - Subtext below in brand.highlight color
  - Brand-color bar at bottom with domain in contrasting text
  - Auto-flips text color by bg luminance

Usage:
  python scripts/generate_thumbnail.py <slug>
  python scripts/generate_thumbnail.py <slug> --text "NOTES FORGET" --subtext "Here's the fix"

  Text and brand come from the script's THUMBNAIL: and BRAND: lines.
  Writes output/<slug>-thumb.png
"""

import argparse

from common import OUTPUT, load_brand, load_meta, fail

WIDTH, HEIGHT = 1080, 1920
MARGIN_X = 80
HEADLINE_TOP = 240
SUBTEXT_GAP = 40
BAR_HEIGHT = 220
BAR_PADDING = 32


def hex_to_rgb(hex_color):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def luminance(rgb):
    r, g, b = (c / 255.0 for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def pick_contrast(bg_rgb, light=(255, 255, 255), dark=(20, 20, 20)):
    return dark if luminance(bg_rgb) > 0.55 else light


def get_font(size, weight="black"):
    """Impact for headline (black/condensed), Arial Bold for body, Arial for plain."""
    from PIL import ImageFont
    candidates = {
        "black": ["C:/Windows/Fonts/impact.ttf", "/System/Library/Fonts/Supplemental/Impact.ttf",
                  "/Library/Fonts/Impact.ttf", "/usr/share/fonts/truetype/msttcorefonts/Impact.ttf",
                  "C:/Windows/Fonts/arialbd.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                  "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
        "bold": ["C:/Windows/Fonts/arialbd.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
    }
    for path in candidates.get(weight, candidates["bold"]):
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default(size)


def wrap_to_fit(text, max_width, font_size, weight, draw):
    """Return (lines, font_size) that fit within max_width.

    Strategy:
      1. Try as one line at font_size; shrink until fits OR hits min.
      2. If still too wide at min, break into 2 lines on word boundary.
    """
    min_size = 90
    size = font_size
    while size >= min_size:
        font = get_font(size, weight)
        bbox = draw.textbbox((0, 0), text, font=font)
        if bbox[2] - bbox[0] <= max_width:
            return [text], size
        size -= 12

    # Still doesn't fit on one line at min_size — try two lines.
    words = text.split()
    if len(words) >= 2:
        for split in range(len(words) - 1, 0, -1):
            line1 = " ".join(words[:split])
            line2 = " ".join(words[split:])
            size = font_size
            while size >= min_size:
                font = get_font(size, weight)
                w1 = draw.textbbox((0, 0), line1, font=font)[2]
                w2 = draw.textbbox((0, 0), line2, font=font)[2]
                if max(w1, w2) <= max_width:
                    return [line1, line2], size
                size -= 12

    # Last resort — return at min_size as 1 line, accept overflow.
    return [text], min_size


def draw_centered(draw, text, font, color, y):
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    x = (WIDTH - w) // 2
    draw.text((x, y), text, font=font, fill=color)
    return bbox[3] - bbox[1]


def generate(slug, headline, subtext, brand):
    from PIL import Image, ImageDraw

    bg = hex_to_rgb(brand.get("bg", "#FBF7F0"))
    primary = hex_to_rgb(brand.get("text", "#1C1C1A"))
    accent = hex_to_rgb(brand.get("accent", "#5C3A2E"))
    highlight = hex_to_rgb(brand.get("highlight", "#C08B3E"))

    # Auto-flip text color if brand text/bg contrast is bad.
    lum_bg = luminance(bg)
    lum_text = luminance(primary)
    if abs(lum_bg - lum_text) < 0.4:
        primary = pick_contrast(bg)
    # Subtext gets the highlight color; ensure decent contrast.
    if abs(lum_bg - luminance(highlight)) < 0.35:
        highlight = pick_contrast(bg, dark=accent, light=(255, 255, 255))

    img = Image.new("RGB", (WIDTH, HEIGHT), bg)
    draw = ImageDraw.Draw(img)

    # Headline — fill available width, biggest possible
    max_text_width = WIDTH - 2 * MARGIN_X
    headline_clean = headline.upper().strip()
    lines, size = wrap_to_fit(headline_clean, max_text_width, 360, "black", draw)
    font = get_font(size, "black")

    y = HEADLINE_TOP
    for line in lines:
        h = draw_centered(draw, line, font, primary, y)
        y += h + 20

    # Subtext
    if subtext:
        sub_clean = subtext.strip()
        # Subtext is sentence case, smaller, highlight color
        sub_size = max(96, size // 3)
        sub_lines, sub_size = wrap_to_fit(sub_clean, max_text_width, sub_size, "bold", draw)
        sub_font = get_font(sub_size, "bold")
        y += SUBTEXT_GAP
        for line in sub_lines:
            h = draw_centered(draw, line, sub_font, highlight, y)
            y += h + 14

    # Brand bar at bottom
    bar_y = HEIGHT - BAR_HEIGHT
    draw.rectangle([0, bar_y, WIDTH, HEIGHT], fill=accent)
    domain = brand.get("cta") or brand.get("url") or ""
    if domain:
        domain_color = pick_contrast(accent)
        # Fit domain text inside the bar
        bar_text_max = WIDTH - 2 * BAR_PADDING
        domain_lines, domain_size = wrap_to_fit(
            domain, bar_text_max, 120, "bold", draw
        )
        domain_font = get_font(domain_size, "bold")
        # Vertically center within the bar
        line_h = draw.textbbox((0, 0), domain_lines[0], font=domain_font)[3]
        total_h = line_h * len(domain_lines)
        domain_y = bar_y + (BAR_HEIGHT - total_h) // 2
        for line in domain_lines:
            draw_centered(draw, line, domain_font, domain_color, domain_y)
            domain_y += line_h + 4

    OUTPUT.mkdir(exist_ok=True)
    out_path = OUTPUT / f"{slug}-thumb.png"
    img.save(out_path, "PNG")
    print(f"  output/{slug}-thumb.png")
    return out_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("slug")
    parser.add_argument("--text", help="override the script's THUMBNAIL text")
    parser.add_argument("--subtext")
    parser.add_argument("--brand")
    args = parser.parse_args()

    meta = load_meta(args.slug)
    text = args.text or meta.get("thumbnail_text", "")
    if not text:
        fail("no thumbnail text. Add THUMBNAIL: \"HOOK\" to the script or pass --text")
    subtext = args.subtext if args.subtext is not None else meta.get("thumbnail_subtext", "")
    print(f"Thumbnail for {args.slug}: {text!r} / {subtext!r}")
    generate(args.slug, text, subtext, load_brand(args.brand or meta.get("brand", "default")))


if __name__ == "__main__":
    main()
