#!/usr/bin/env python3
"""
render_codestats_card.py

Reads the public Code::Stats API for a given username and renders a small
SVG card: total XP + level, and a donut of the top-N languages by all-time
XP (the API only exposes all-time totals per language -- no daily-per-
language breakdown exists, so this can never be a "last 7 days" split).

Usage: python3 render_codestats_card.py <username> <output_svg_path> [top_n]
"""

import json
import math
import sys
import urllib.request

from donut_helpers import draw_donut, donut_legend

API_URL = "https://codestats.net/api/users/{username}"

SURFACE = "#0d1117"
TEXT_PRIMARY = "#e6edf3"
TEXT_SECONDARY = "#8b949e"
OTHER_COLOR = "#4b5563"

# Validated categorical palette (fixed order -- never cycled/reordered), shared
# with the Claude usage card's Opus/Sonnet/Haiku colors so both cards read as
# one visual family.
PALETTE = ["#d9551a", "#2b78dd", "#12a869", "#9c52d6", "#bc890f"]


def fetch(username):
    with urllib.request.urlopen(API_URL.format(username=username)) as resp:
        return json.load(resp)


def level_for(xp):
    return math.floor(0.025 * math.sqrt(xp))


def top_languages(data, top_n):
    langs = sorted(data["languages"].items(), key=lambda x: -x[1]["xps"])
    top = langs[:top_n]
    rest_xp = sum(xps["xps"] for _, xps in langs[top_n:])
    slices = [(name, info["xps"]) for name, info in top]
    if rest_xp > 0:
        slices.append(("Other", rest_xp))
    return slices


def format_xp(xp):
    return f"{xp:,}".replace(",", " ")


def section(total_xp, level, slices, y_off=0):
    """Return (svg_fragment, height) for this card's content, offset by y_off
    so it can be composed inside a larger multi-section SVG."""
    header_h = 70
    bottom_margin = 20
    r, ring_w = 55, 24
    cx = 100
    row_h = 18
    donut_d = 2 * (r + ring_w / 2)
    legend_h = len(slices) * row_h
    content_h = max(donut_d, legend_h)
    height = round(header_h + content_h + bottom_margin)
    cy = y_off + round(header_h + content_h / 2)

    arcs = draw_donut(cx, cy, r, ring_w, slices, PALETTE, OTHER_COLOR)
    legend = donut_legend(
        slices, PALETTE, OTHER_COLOR,
        lx=240, ly=round(cy - legend_h / 2 + row_h / 2), row_h=row_h,
        text_color=TEXT_PRIMARY,
    )

    fragment = f'''<g font-family="Segoe UI, sans-serif">
    <rect x="20" y="{y_off + 20}" width="16" height="16" rx="3" fill="none" stroke="{TEXT_PRIMARY}" stroke-width="1.6" />
    <text x="28" y="{y_off + 32}" font-size="10" font-weight="bold" fill="{TEXT_PRIMARY}" text-anchor="middle">::</text>
    <text x="44" y="{y_off + 33}" font-size="15" font-weight="bold" fill="{TEXT_PRIMARY}">Code::Stats</text>
    <text x="20" y="{y_off + 52}" font-size="11" fill="{TEXT_SECONDARY}">{format_xp(total_xp)} XP &#183; Lvl. {level}</text>
  </g>
  {''.join(arcs)}
  {''.join(legend)}'''

    return fragment, height


def render_svg(username, total_xp, level, slices, out_path):
    width = 420
    fragment, height = section(total_xp, level, slices, y_off=0)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
  <rect width="{width}" height="{height}" rx="10" fill="{SURFACE}" />
  {fragment}
</svg>'''

    with open(out_path, "w") as fh:
        fh.write(svg)


def main():
    username = sys.argv[1] if len(sys.argv) > 1 else "mate2fr"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "codestats-card.svg"
    top_n = int(sys.argv[3]) if len(sys.argv) > 3 else 5

    data = fetch(username)
    total_xp = data["total_xp"]
    level = level_for(total_xp)
    slices = top_languages(data, top_n)
    render_svg(username, total_xp, level, slices, out_path)
    print(f"Rendered {out_path}: {format_xp(total_xp)} XP, Lvl {level}, top {top_n} languages")


if __name__ == "__main__":
    main()
