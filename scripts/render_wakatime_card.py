#!/usr/bin/env python3
"""
render_wakatime_card.py

Reads the public WakaTime stats API for a given user id and renders a small
SVG card: a donut of the top-N languages (last 7 days) and a stacked bar of
coding categories (AI Coding / Coding / Writing Docs / ...). No API key
needed as long as the WakaTime account has public stats sharing enabled
(Settings -> "Display code stats publicly").

Editors (Claude Code vs VS Code, etc.) are deliberately not shown here --
not a signal a recruiter cares about, unlike the language/category split.

Usage: python3 render_wakatime_card.py <user_id> <output_svg_path> [top_n]
"""

import json
import math
import sys
import urllib.request

from donut_helpers import draw_donut, donut_legend

API_URL = "https://wakatime.com/api/v1/users/{user_id}/stats"

SURFACE = "#0d1117"
TEXT_PRIMARY = "#e6edf3"
TEXT_SECONDARY = "#8b949e"
OTHER_COLOR = "#4b5563"

# Same validated categorical palette as the Claude usage / Code::Stats cards,
# so all cards in the merged profile SVG read as one visual family.
PALETTE = ["#d9551a", "#2b78dd", "#12a869", "#9c52d6", "#bc890f"]


def fetch(user_id):
    with urllib.request.urlopen(API_URL.format(user_id=user_id)) as resp:
        return json.load(resp)["data"]


def _top_entries(entries, top_n):
    # WakaTime already includes its own literal "Other" bucket -- fold it
    # into our overflow bucket instead of keeping two separate "Other" rows.
    named = [e for e in entries if e["name"] != "Other"]
    other_pct = next((e["percent"] for e in entries if e["name"] == "Other"), 0)
    top = named[:top_n]
    rest = sum(e["percent"] for e in named[top_n:]) + other_pct
    slices = [(e["name"], e["percent"]) for e in top]
    if rest > 0:
        slices.append(("Other", rest))
    return slices


def top_languages(data, top_n):
    return _top_entries(data["languages"], top_n)


def categories(data):
    return [(c["name"], c["percent"]) for c in data["categories"]]


def _icon(y_off):
    # Simple invented clock glyph (not WakaTime's real logo -- avoids any
    # brand/logo-reproduction question) in the same icon-box style as the
    # Code::Stats card's "::" glyph.
    cy = y_off + 28
    return (
        f'<rect x="20" y="{y_off + 20}" width="16" height="16" rx="8" fill="none" '
        f'stroke="{TEXT_PRIMARY}" stroke-width="1.6" />'
        f'<line x1="28" y1="{cy}" x2="28" y2="{cy - 4}" stroke="{TEXT_PRIMARY}" stroke-width="1.4" stroke-linecap="round" />'
        f'<line x1="28" y1="{cy}" x2="31" y2="{cy}" stroke="{TEXT_PRIMARY}" stroke-width="1.4" stroke-linecap="round" />'
    )


def section(lang_slices, cat_slices, y_off=0):
    """Return (svg_fragment, height) for this card's content, offset by y_off
    so it can be composed inside a larger multi-section SVG."""
    header_h = 70
    row_h = 18

    # -- donut (languages) --
    donut_r, donut_ring_w, donut_cx = 45, 20, 90
    donut_d = 2 * (donut_r + donut_ring_w / 2)
    lang_legend_h = len(lang_slices) * row_h
    donut_block_h = max(donut_d, lang_legend_h)
    donut_cy = y_off + header_h + round(donut_block_h / 2)

    arcs = draw_donut(donut_cx, donut_cy, donut_r, donut_ring_w, lang_slices, PALETTE, OTHER_COLOR)
    lang_legend = donut_legend(
        lang_slices, PALETTE, OTHER_COLOR,
        lx=200, ly=round(donut_cy - lang_legend_h / 2 + row_h / 2), row_h=row_h,
        text_color=TEXT_PRIMARY,
    )

    # -- stacked bar (categories) --
    bar_x, bar_y, bar_w, bar_h = 20, y_off + header_h + donut_block_h + 24, 380, 18
    gap = 2
    grand_cat = sum(v for _, v in cat_slices) or 1

    bar_segments = []
    x_cursor = bar_x
    for i, (name, pct) in enumerate(cat_slices):
        frac = pct / grand_cat
        seg_w = max(frac * bar_w - (gap if i < len(cat_slices) - 1 else 0), 0)
        color = PALETTE[i] if i < len(PALETTE) and name != "Other" else OTHER_COLOR
        bar_segments.append(
            f'<rect x="{x_cursor:.1f}" y="{bar_y}" width="{seg_w:.1f}" height="{bar_h}" fill="{color}" />'
        )
        x_cursor += seg_w + gap

    # 2-column x N-row grid, centered under the bar -- category names are long
    # enough ("Writing Docs", "Writing Tests") that a single row would overflow,
    # and a single left-aligned column left a lot of dead space to its right.
    CHAR_W, DOT_TO_TEXT, COL_GAP = 6.2, 14, 40
    n_cols = 2
    labels = [f"{name} {100 * pct / grand_cat:.0f}%" for name, pct in cat_slices]
    col_widths = [0] * n_cols
    for i, label in enumerate(labels):
        col = i % n_cols
        col_widths[col] = max(col_widths[col], DOT_TO_TEXT + len(label) * CHAR_W)
    grid_w = sum(col_widths) + COL_GAP * (n_cols - 1)
    grid_x0 = bar_x + (bar_w - grid_w) / 2
    col_x = [grid_x0 + sum(col_widths[:c]) + COL_GAP * c for c in range(n_cols)]

    cat_legend = []
    cly = bar_y + bar_h + 18
    n_rows = math.ceil(len(cat_slices) / n_cols)
    for r in range(n_rows):
        row_y = cly + r * row_h
        for c in range(n_cols):
            i = r * n_cols + c
            if i >= len(cat_slices):
                continue
            name, pct = cat_slices[i]
            color = PALETTE[i] if i < len(PALETTE) and name != "Other" else OTHER_COLOR
            cat_legend.append(
                f'<circle cx="{col_x[c]:.1f}" cy="{row_y}" r="4" fill="{color}" />'
                f'<text x="{col_x[c] + 10:.1f}" y="{row_y + 4}" font-size="11" font-family="Segoe UI, sans-serif" '
                f'fill="{TEXT_PRIMARY}">{labels[i]}</text>'
            )

    clip_id = f"wk-bar-clip-{y_off}"
    grid_bottom = cly + (n_rows - 1) * row_h
    height = round((grid_bottom + 20) - y_off)

    fragment = f'''<defs>
    <clipPath id="{clip_id}"><rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="3" /></clipPath>
  </defs>
  <g font-family="Segoe UI, sans-serif">
    {_icon(y_off)}
    <text x="44" y="{y_off + 33}" font-size="15" font-weight="bold" fill="{TEXT_PRIMARY}">WakaTime</text>
    <text x="20" y="{y_off + 52}" font-size="11" fill="{TEXT_SECONDARY}">Last 7 days activity</text>
  </g>
  {''.join(arcs)}
  {''.join(lang_legend)}
  <g clip-path="url(#{clip_id})">{''.join(bar_segments)}</g>
  {''.join(cat_legend)}'''

    return fragment, height


def render_svg(user_id, lang_slices, cat_slices, out_path):
    width = 420
    fragment, height = section(lang_slices, cat_slices, y_off=0)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
  <rect width="{width}" height="{height}" rx="10" fill="{SURFACE}" />
  {fragment}
</svg>'''

    with open(out_path, "w") as fh:
        fh.write(svg)


def main():
    user_id = sys.argv[1] if len(sys.argv) > 1 else "b8bb0b6e-7cc2-43fe-958a-eb92fa6aa446"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "wakatime-card.svg"
    top_n = int(sys.argv[3]) if len(sys.argv) > 3 else 5

    data = fetch(user_id)
    lang_slices = top_languages(data, top_n)
    cat_slices = categories(data)
    render_svg(user_id, lang_slices, cat_slices, out_path)
    print(f"Rendered {out_path}")


if __name__ == "__main__":
    main()
