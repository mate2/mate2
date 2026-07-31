"""Shared donut-ring arc drawing, used by both the Code::Stats and WakaTime
cards so the two donuts stay visually identical (same gap/cap/rotation math)."""

import math


def draw_donut(cx, cy, r, ring_w, slices, palette, other_color, gap_deg=1.1, linecap="butt"):
    """slices: list of (name, value) pairs. Returns a list of <circle> arc fragments."""
    grand = sum(v for _, v in slices) or 1
    circumference = 2 * math.pi * r

    arcs = []
    angle_cursor = 0.0
    for i, (name, value) in enumerate(slices):
        frac = value / grand
        sweep_deg = max(frac * 360 - gap_deg, 0)
        color = palette[i] if i < len(palette) and name != "Other" else other_color
        seg_len = (sweep_deg / 360) * circumference
        dashoffset = -(angle_cursor / 360) * circumference
        arcs.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" '
            f'stroke-width="{ring_w}" stroke-linecap="{linecap}" '
            f'stroke-dasharray="{seg_len:.2f} {circumference - seg_len:.2f}" '
            f'stroke-dashoffset="{dashoffset:.2f}" '
            f'transform="rotate(-90 {cx} {cy})" />'
        )
        angle_cursor += frac * 360
    return arcs


def donut_legend(slices, palette, other_color, lx, ly, row_h, text_color, font_family="Segoe UI, sans-serif"):
    """Right-aligned column legend: one dot + label per slice, starting at (lx, ly)."""
    grand = sum(v for _, v in slices) or 1
    lines = []
    y = ly
    for i, (name, value) in enumerate(slices):
        pct = 100 * value / grand
        color = palette[i] if i < len(palette) and name != "Other" else other_color
        lines.append(
            f'<circle cx="{lx}" cy="{y}" r="4" fill="{color}" />'
            f'<text x="{lx + 10}" y="{y + 4}" font-size="11" '
            f'font-family="{font_family}" fill="{text_color}">{name} {pct:.0f}%</text>'
        )
        y += row_h
    return lines
