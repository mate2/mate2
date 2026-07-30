#!/usr/bin/env python3
"""
render_card.py

Reads all machine snapshot JSON files from the shared data repo,
aggregates minutes-by-model across machines, and renders a small
SVG card summarizing the past week's Claude model usage split.

Usage: python3 render_card.py <data_dir> <output_svg_path>

Only reads: machine name, minutes_by_model. Nothing else from the
snapshot files is used, so this stays safe to run in a public
GitHub Action even though the source data repo is private.
"""

import json
import glob
import sys
from collections import defaultdict

MODEL_COLORS = {
    "opus": "#c85f2e",
    "sonnet": "#5a8dee",
    "haiku": "#2fa86e",
}
DEFAULT_COLOR = "#999999"
SURFACE = "#0d1117"


def short_name(model):
    m = model.lower()
    if "opus" in m:
        return "opus"
    if "sonnet" in m:
        return "sonnet"
    if "haiku" in m:
        return "haiku"
    return "other"


def aggregate(data_dir):
    totals = defaultdict(float)
    for path in glob.glob(f"{data_dir}/*.json"):
        with open(path) as fh:
            snap = json.load(fh)
        for model, minutes in snap.get("minutes_by_model", {}).items():
            totals[short_name(model)] += minutes
    return totals


def format_duration(minutes):
    h, m = divmod(round(minutes), 60)
    return f"{h}h {m:02d}m" if h else f"{m}m"


def render_svg(totals, out_path):
    grand_total = sum(totals.values()) or 1
    width, height = 420, 120
    bar_x, bar_y, bar_w, bar_h = 20, 70, 380, 22
    gap = 2  # surface-colored gap between stacked segments

    ranked = sorted(totals.items(), key=lambda x: -x[1])

    segments = []
    x_cursor = bar_x
    for i, (model, minutes) in enumerate(ranked):
        frac = minutes / grand_total
        seg_w = frac * bar_w - (gap if i < len(ranked) - 1 else 0)
        seg_w = max(seg_w, 0)
        color = MODEL_COLORS.get(model, DEFAULT_COLOR)
        segments.append(
            f'<rect x="{x_cursor:.1f}" y="{bar_y}" width="{seg_w:.1f}" '
            f'height="{bar_h}" fill="{color}" />'
        )
        x_cursor += seg_w + gap

    legend = []
    ly = 100
    lx = 20
    for model, minutes in ranked:
        pct = 100 * minutes / grand_total
        color = MODEL_COLORS.get(model, DEFAULT_COLOR)
        legend.append(
            f'<circle cx="{lx}" cy="{ly}" r="4" fill="{color}" />'
            f'<text x="{lx+10}" y="{ly+4}" font-size="11" '
            f'font-family="Segoe UI, sans-serif" fill="#e6edf3">'
            f'{model.capitalize()} {pct:.0f}%</text>'
        )
        lx += 110

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
  <defs>
    <clipPath id="bar-clip">
      <rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="4" />
    </clipPath>
  </defs>
  <rect width="{width}" height="{height}" rx="10" fill="{SURFACE}" />
  <text x="20" y="30" font-size="15" font-family="Segoe UI, sans-serif"
        fill="#e6edf3" font-weight="bold">Claude Code — last 7 days</text>
  <text x="20" y="50" font-size="11" font-family="Segoe UI, sans-serif"
        fill="#8b949e">{format_duration(grand_total)} active</text>
  <g clip-path="url(#bar-clip)">{''.join(segments)}</g>
  {''.join(legend)}
</svg>'''

    with open(out_path, "w") as fh:
        fh.write(svg)


def main():
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "data"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "claude-usage.svg"
    totals = aggregate(data_dir)
    render_svg(totals, out_path)
    print(f"Rendered {out_path}")


if __name__ == "__main__":
    main()
