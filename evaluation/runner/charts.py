"""Charts, drawn from the same values the tables carry.

`docs/canonical/06_evaluation_plan.md` makes "chart values match the JSON" an acceptance
criterion, and the usual way that fails is a chart built from a second, slightly different
computation. So these functions take the **already-computed** values — the same objects that go
into `metrics.json` — and never compute anything.

The numbers are also written into the SVG as text, which makes the criterion checkable rather
than assumed: `tests/test_charts.py` reads every number back out of the rendered chart and
asserts it appears in `metrics.json`.

Plain SVG rather than a plotting library: it adds no dependency, renders identically on every
machine — which the artifact-hash comparison requires — and stays readable in a diff.
"""
from __future__ import annotations

from collections.abc import Sequence

BAR_HEIGHT = 26
BAR_GAP = 12
LABEL_WIDTH = 210
VALUE_WIDTH = 90
PLOT_WIDTH = 360
MARGIN = 20

INK = "#1c1c1c"
MUTED = "#6b6b6b"
BAR = "#2f5d8a"
GRID = "#d8d8d8"
UNDEFINED_LABEL = "tidak terukur"
"""Shown where a value is undefined. Never a zero-length bar, which would read as a measured 0."""


def bar_chart(title: str, subtitle: str, rows: Sequence[tuple[str, float | None]]) -> str:
    """A horizontal bar chart. Rows whose value is `None` are labelled, never drawn as zero."""
    measured = [value for _, value in rows if value is not None]
    ceiling = max(measured) if measured else 1.0
    ceiling = ceiling if ceiling > 0 else 1.0

    height = MARGIN * 3 + len(rows) * (BAR_HEIGHT + BAR_GAP)
    width = MARGIN * 2 + LABEL_WIDTH + PLOT_WIDTH + VALUE_WIDTH

    parts = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-label="{_escape(title)}">'
        ),
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
        (
            f'<text x="{MARGIN}" y="{MARGIN + 4}" font-family="system-ui, sans-serif" '
            f'font-size="14" font-weight="600" fill="{INK}">{_escape(title)}</text>'
        ),
        (
            f'<text x="{MARGIN}" y="{MARGIN + 22}" font-family="system-ui, sans-serif" '
            f'font-size="11" fill="{MUTED}">{_escape(subtitle)}</text>'
        ),
    ]

    top = MARGIN * 2 + 12
    for index, (label, value) in enumerate(rows):
        y = top + index * (BAR_HEIGHT + BAR_GAP)
        parts.append(
            f'<text x="{MARGIN}" y="{y + BAR_HEIGHT - 8}" '
            f'font-family="system-ui, sans-serif" font-size="12" '
            f'fill="{INK}">{_escape(label)}</text>'
        )
        plot_x = MARGIN + LABEL_WIDTH
        parts.append(
            f'<rect x="{plot_x}" y="{y}" width="{PLOT_WIDTH}" height="{BAR_HEIGHT}" '
            f'fill="none" stroke="{GRID}"/>'
        )
        if value is None:
            parts.append(
                f'<text x="{plot_x + 8}" y="{y + BAR_HEIGHT - 8}" '
                f'font-family="system-ui, sans-serif" font-size="11" fill="{MUTED}">'
                f"{UNDEFINED_LABEL}</text>"
            )
            continue
        bar_width = max(1, round(PLOT_WIDTH * value / ceiling))
        parts.append(
            f'<rect x="{plot_x}" y="{y}" width="{bar_width}" height="{BAR_HEIGHT}" fill="{BAR}"/>'
        )
        parts.append(
            f'<text x="{plot_x + PLOT_WIDTH + 10}" y="{y + BAR_HEIGHT - 8}" '
            f'font-family="system-ui, sans-serif" font-size="12" fill="{INK}">'
            f"{format_value(value)}</text>"
        )

    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def format_value(value: float) -> str:
    """One rendering of a number, used by charts and tables alike so they cannot disagree."""
    return f"{value:.4f}"


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
