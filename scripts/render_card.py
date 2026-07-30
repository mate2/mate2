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
    "opus": "#d97757",
    "sonnet": "#5a8dee",
    "haiku": "#7fd8a6",
}
DEFAULT_COLOR = "#999999"


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
    machines = []
    for path in glob.glob(f"{data_dir}/*.json"):
        with open(path) as fh:
            snap = json.load(fh)
        machines.append(snap.get("machine", "?"))
        for model, minutes in snap.get("minutes_by_model", {}).items():
            totals[short_name(model)] += minutes
    return totals, machines


def render_svg(totals, machines, out_path):
    grand_total = sum(totals.values()) or 1
    width, height = 420, 120
    bar_x, bar_y, bar_w, bar_h = 20, 70, 380, 22

    segments = []
    x_cursor = bar_x
    for model, minutes in sorted(totals.items(), key=lambda x: -x[1]):
        frac = minutes / grand_total
        seg_w = frac * bar_w
        color = MODEL_COLORS.get(model, DEFAULT_COLOR)
        segments.append(
            f'<rect x="{x_cursor:.1f}" y="{bar_y}" width="{seg_w:.1f}" '
            f'height="{bar_h}" fill="{color}" />'
        )
        x_cursor += seg_w

    legend = []
    ly = 100
    lx = 20
    for model, minutes in sorted(totals.items(), key=lambda x: -x[1]):
        pct = 100 * minutes / grand_total
        color = MODEL_COLORS.get(model, DEFAULT_COLOR)
        legend.append(
            f'<circle cx="{lx}" cy="{ly}" r="4" fill="{color}" />'
            f'<text x="{lx+10}" y="{ly+4}" font-size="11" '
            f'font-family="Segoe UI, sans-serif" fill="#333">'
            f'{model.capitalize()} {pct:.0f}%</text>'
        )
        lx += 110

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
  <rect width="{width}" height="{height}" rx="10" fill="#0d1117" />
  <text x="20" y="30" font-size="15" font-family="Segoe UI, sans-serif"
        fill="#e6edf3" font-weight="bold">Claude Code — last 7 days</text>
  <text x="20" y="50" font-size="11" font-family="Segoe UI, sans-serif"
        fill="#8b949e">{len(machines)} machine(s) &#183; {grand_total:.0f} min active</text>
  {''.join(segments)}
  {''.join(legend)}
</svg>'''

    with open(out_path, "w") as fh:
        fh.write(svg)


def main():
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "data"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "claude-usage.svg"
    totals, machines = aggregate(data_dir)
    render_svg(totals, machines, out_path)
    print(f"Rendered {out_path} from {len(machines)} machine(s)")


if __name__ == "__main__":
    main()
