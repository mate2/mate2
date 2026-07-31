#!/usr/bin/env python3
"""
render_profile_card.py

Composes the individual stat cards (Claude Code usage, Code::Stats, WakaTime)
into a SINGLE svg, so the profile README only ever embeds one <img>. Two
separate <img> tags stack or wrap unpredictably depending on the viewer's
width (mobile vs desktop, GitHub's own app); one merged SVG gives full
control over the layout regardless of viewport.

Usage: python3 render_profile_card.py <claude_data_dir> <codestats_username> <wakatime_user_id> <output_svg_path> [top_n]
"""

import sys

import render_card
import render_codestats_card
import render_wakatime_card

SURFACE = "#0d1117"
WIDTH = 420
DIVIDER_GAP = 16
DIVIDER_COLOR = "#21262d"


def _divider(y):
    return f'<line x1="20" y1="{y}" x2="{WIDTH - 20}" y2="{y}" stroke="{DIVIDER_COLOR}" stroke-width="1" />'


def build(claude_data_dir, codestats_username, wakatime_user_id, out_path, top_n=5):
    sections = []
    y_cursor = 0

    claude_totals = render_card.aggregate(claude_data_dir)
    fragment, h = render_card.section(claude_totals, y_off=y_cursor)
    sections.append(fragment)
    y_cursor += h

    cs_data = render_codestats_card.fetch(codestats_username)
    cs_total_xp = cs_data["total_xp"]
    cs_level = render_codestats_card.level_for(cs_total_xp)
    cs_slices = render_codestats_card.top_languages(cs_data, top_n)
    y_cursor += DIVIDER_GAP
    sections.append(_divider(y_cursor - DIVIDER_GAP / 2))
    fragment, h = render_codestats_card.section(cs_total_xp, cs_level, cs_slices, y_off=y_cursor)
    sections.append(fragment)
    y_cursor += h

    wk_data = render_wakatime_card.fetch(wakatime_user_id)
    wk_langs = render_wakatime_card.top_languages(wk_data, top_n)
    wk_cats = render_wakatime_card.categories(wk_data)
    y_cursor += DIVIDER_GAP
    sections.append(_divider(y_cursor - DIVIDER_GAP / 2))
    fragment, h = render_wakatime_card.section(wk_langs, wk_cats, y_off=y_cursor)
    sections.append(fragment)
    y_cursor += h

    total_height = y_cursor

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{total_height}">
  <rect width="{WIDTH}" height="{total_height}" rx="10" fill="{SURFACE}" />
  {''.join(sections)}
</svg>'''

    with open(out_path, "w") as fh:
        fh.write(svg)


def main():
    claude_data_dir = sys.argv[1] if len(sys.argv) > 1 else "data"
    codestats_username = sys.argv[2] if len(sys.argv) > 2 else "mate2fr"
    wakatime_user_id = sys.argv[3] if len(sys.argv) > 3 else "b8bb0b6e-7cc2-43fe-958a-eb92fa6aa446"
    out_path = sys.argv[4] if len(sys.argv) > 4 else "claude-usage.svg"
    top_n = int(sys.argv[5]) if len(sys.argv) > 5 else 5

    build(claude_data_dir, codestats_username, wakatime_user_id, out_path, top_n)
    print(f"Rendered {out_path}")


if __name__ == "__main__":
    main()
