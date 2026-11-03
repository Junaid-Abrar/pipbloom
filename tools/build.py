#!/usr/bin/env python3
"""Builds index.html (with the year grid as inline SVG), og.png and favicon.svg.

The grid uses the same geometry and sample data as the app's design system: squircle cells at
28% corner radius, a 20% gap, three bands of 18 weeks, today ringed, days ahead as dots.
Standard library plus Pillow (for og.png only). Run from the repo root: python3 tools/build.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CELL, GAP, BAND_GAP = 10, 2, 16
WEEKS_PER_BAND, BANDS = 18, 3
YEAR_LEADING_PADDING = 3   # 1 Jan 2026 is a Thursday in a Monday-first week
TODAY_INDEX = 306          # 3 Nov 2026, zero-based
DAYS_IN_YEAR = 365
LIGHT = {"paper": "#F6F2EA", "ink": "#1F1B16", "ink2": "#5E574D", "ink3": "#857D71",
         "levels": ["#E9E4DA", "#BDD9B4", "#92BC83", "#699E56", "#45802E"]}


def level(day: int) -> int:
    """Same spread as the app's sample data: about a quarter missed, the rest leaning full."""
    h = ((day * 2_654_435_761) & 0xFFFFFFFF) >> 16
    r = h % 100
    return 0 if r < 25 else 1 if r < 35 else 2 if r < 47 else 3 if r < 62 else 4


def band_cells(band: int):
    """Yields (column, row, kind) for one band; kind is a level 0-4, 'dot' or 'today'."""
    for col in range(WEEKS_PER_BAND):
        week = band * WEEKS_PER_BAND + col
        for row in range(7):
            day = week * 7 + row - YEAR_LEADING_PADDING
            if not 0 <= day < DAYS_IN_YEAR:
                continue
            if day == TODAY_INDEX:
                yield col, row, "today"
            elif day > TODAY_INDEX:
                yield col, row, "dot"
            else:
                yield col, row, level(day)


def grid_svg() -> str:
    pitch = CELL + GAP
    width = WEEKS_PER_BAND * pitch - GAP
    band_h = 7 * pitch - GAP
    height = BANDS * band_h + (BANDS - 1) * BAND_GAP
    parts = [f'    <svg viewBox="0 0 {width} {height}" role="img" '
             f'aria-label="A year habit grid for 2026, drawn in three rows. Most days up to early November are filled in shades of green, with a few empty squares, and small dots mark the days still to come.">']
    radius = CELL * 0.28
    for band in range(BANDS):
        y0 = band * (band_h + BAND_GAP)
        for col, row, kind in band_cells(band):
            x, y = col * pitch, y0 + row * pitch
            if kind == "dot":
                parts.append(f'      <circle class="dot" cx="{x + CELL / 2}" cy="{y + CELL / 2}" r="{CELL * 0.15:.2f}"/>')
            elif kind == "today":
                parts.append(f'      <rect class="l0" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="{radius:.1f}"/>')
                parts.append(f'      <rect class="today" x="{x + .5}" y="{y + .5}" width="{CELL - 1}" height="{CELL - 1}" rx="{radius:.1f}"/>')
            else:
                parts.append(f'      <rect class="l{kind}" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="{radius:.1f}"/>')
    parts.append("    </svg>")
    return "\n".join(parts)


def favicon() -> str:
    rows = [[4, 2, 4], [1, 4, 3], [3, 4, 2]]
    colours = LIGHT["levels"]
    cells = []
    for r, row in enumerate(rows):
        for c, lvl in enumerate(row):
            cells.append(f'<rect x="{4 + c * 8}" y="{4 + r * 8}" width="7" height="7" rx="2" fill="{colours[lvl]}"/>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="7" fill="{LIGHT["paper"]}"/>{"".join(cells)}</svg>\n'


def og_image() -> None:
    """1200x630 link preview: headline on the left, the grid on the right, drawn at 2x for smooth corners."""
    from PIL import Image, ImageDraw, ImageFont
    scale = 2
    W, H = 1200 * scale, 630 * scale
    img = Image.new("RGB", (W, H), LIGHT["paper"])
    draw = ImageDraw.Draw(img)
    cell, gap = 18 * scale, 3.6 * scale
    pitch = cell + gap
    band_h = 7 * pitch - gap
    grid_w = WEEKS_PER_BAND * pitch - gap
    band_gap = 22 * scale
    grid_h = BANDS * band_h + (BANDS - 1) * band_gap
    x0, y_start = W - 72 * scale - grid_w, (H - grid_h) / 2
    for band in range(BANDS):
        by = y_start + band * (band_h + band_gap)
        for col, row, kind in band_cells(band):
            x, y = x0 + col * pitch, by + row * pitch
            if kind == "dot":
                cx, cy = x + cell / 2, y + cell / 2
                r = cell * 0.15
                draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill="#CFC8BB")
            else:
                lvl = 0 if kind == "today" else kind
                draw.rounded_rectangle((x, y, x + cell, y + cell), radius=cell * 0.28, fill=LIGHT["levels"][lvl])
                if kind == "today":
                    draw.rounded_rectangle((x, y, x + cell, y + cell), radius=cell * 0.28, outline=LIGHT["ink"], width=3 * scale)
    try:
        headline = ImageFont.truetype("/System/Library/Fonts/SFNS.ttf", 72 * scale)
        headline.set_variation_by_name("Semibold")
        wordmark = ImageFont.truetype("/System/Library/Fonts/SFNS.ttf", 32 * scale)
        wordmark.set_variation_by_name("Semibold")
    except (OSError, ValueError):
        headline = wordmark = ImageFont.load_default()
    draw.text((72 * scale, 78 * scale), "Pipbloom", font=wordmark, fill=LIGHT["ink2"])
    draw.text((72 * scale, 210 * scale), "Fill in\nyour year,\none tap\na day.", font=headline, fill=LIGHT["ink"], spacing=10 * scale)
    img.resize((1200, 630), Image.LANCZOS).save(ROOT / "og.png", optimize=True)


def main() -> None:
    template = (ROOT / "tools" / "index.template.html").read_text()
    (ROOT / "index.html").write_text(template.replace("{{GRID}}", grid_svg()))
    (ROOT / "favicon.svg").write_text(favicon())
    og_image()
    print("built index.html, favicon.svg, og.png")


if __name__ == "__main__":
    main()
