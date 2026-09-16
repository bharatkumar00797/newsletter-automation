"""
Renders a single chart (bar or line) to a PNG for embedding in the newsletter.

Deterministic by design: it draws exactly the numbers it's given, using a
fixed, pre-validated color palette (see workflows/newsletter.md for where the
palette came from). It never invents or estimates data — that judgment call
belongs to the agent layer, before this script is ever called.

Usage:
    python tools/generate_chart.py --spec path/to/spec.json
    python tools/generate_chart.py --spec -            # read spec JSON from stdin

Spec schema (JSON):
{
  "type": "bar" | "line",
  "title": "Chart title",
  "out": "adoption_by_region.png",   // filename written under .tmp/charts/
  "ylabel": "optional y-axis label",
  "value_suffix": "%",               // optional, appended to data labels

  // "bar" — each label is treated as its own category (fixed palette order):
  "labels": ["A", "B", "C"],
  "values": [10, 20, 30],

  // "line" — single series:
  "labels": ["2021", "2022", "2023"],
  "values": [10, 20, 30],

  // "line" — multiple series instead of "values":
  "series": [
    {"name": "US", "values": [10, 20, 30]},
    {"name": "EU", "values": [5, 12, 18]}
  ]
}
"""

import argparse
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parent.parent
CHARTS_DIR = REPO_ROOT / ".tmp" / "charts"

# Categorical palette, fixed order — never cycled, never reassigned by rank.
# Source: dataviz skill reference palette (dark-mode steps), re-validated with
# scripts/validate_palette.js against this project's brand dark surface
# (#171d2c) — all 8 checks pass (see workflows/newsletter.md).
#
# NOTE: this is deliberately NOT the brand's own six accent hues (cyan/
# purple/teal/amber/pink/coral) from brand_assets/ — those failed the
# validator's CVD and normal-vision checks (adjacent pairs too close to tell
# apart). The brand hues are used for decoration in the HTML template
# instead, always paired with a text label; actual chart data needs colors
# that are the *sole* channel readers rely on, so it uses this set instead.
CATEGORICAL = [
    "#3987e5",  # 1 blue
    "#d95926",  # 2 orange
    "#199e70",  # 3 aqua
    "#c98500",  # 4 yellow
    "#d55181",  # 5 magenta
    "#008300",  # 6 green
    "#9085e9",  # 7 violet
    "#e66767",  # 8 red
]

# Chart surface + ink match the newsletter template's dark brand palette
# (tools/templates/newsletter_base.html) so embedded charts blend in rather
# than looking like a mismatched light widget on a dark page.
CHART_SURFACE = "#171d2c"
INK_PRIMARY = "#f5f7fb"
INK_SECONDARY = "#b6bfd1"
INK_MUTED = "#7c869c"
GRIDLINE = "#2a3244"
BASELINE = "#3a4258"

plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Arial"],
        "figure.facecolor": CHART_SURFACE,
        "axes.facecolor": CHART_SURFACE,
        "axes.edgecolor": BASELINE,
        "text.color": INK_PRIMARY,
        "axes.labelcolor": INK_SECONDARY,
        "xtick.color": INK_MUTED,
        "ytick.color": INK_MUTED,
    }
)


def _style_axes(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color(BASELINE)
    ax.spines["bottom"].set_linewidth(1)
    ax.yaxis.grid(True, color=GRIDLINE, linewidth=1, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)


def _fmt(value, suffix):
    text = f"{value:g}"
    return f"{text}{suffix}" if suffix else text


def render_bar(spec):
    labels = spec["labels"]
    values = spec["values"]
    suffix = spec.get("value_suffix", "")
    if len(labels) > len(CATEGORICAL):
        raise ValueError(
            f"bar chart has {len(labels)} categories but the validated palette "
            f"only covers {len(CATEGORICAL)} — fold the rest into 'Other' before "
            "calling this tool."
        )
    colors = CATEGORICAL[: len(labels)]

    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
    bars = ax.bar(labels, values, color=colors, width=0.55, zorder=3)
    _style_axes(ax)
    ax.spines["bottom"].set_visible(True)
    if spec.get("ylabel"):
        ax.set_ylabel(spec["ylabel"])

    top = max(values) if values else 0
    ax.set_ylim(0, top * 1.18 if top else 1)
    for rect, value in zip(bars, values):
        ax.annotate(
            _fmt(value, suffix),
            (rect.get_x() + rect.get_width() / 2, rect.get_height()),
            xytext=(0, 6),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=11,
            color=INK_PRIMARY,
            fontweight="bold",
        )

    if spec.get("title"):
        ax.set_title(spec["title"], fontsize=14, color=INK_PRIMARY, pad=16, loc="left")
    fig.tight_layout()
    return fig


def render_line(spec):
    labels = spec["labels"]
    suffix = spec.get("value_suffix", "")
    series = spec.get("series")
    if not series:
        series = [{"name": None, "values": spec["values"]}]
    if len(series) > len(CATEGORICAL):
        raise ValueError(
            f"line chart has {len(series)} series but the validated palette only "
            f"covers {len(CATEGORICAL)} — facet instead of adding more series."
        )

    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
    for s, color in zip(series, CATEGORICAL):
        ax.plot(
            labels,
            s["values"],
            color=color,
            linewidth=2,
            marker="o",
            markersize=8,
            markerfacecolor=color,
            markeredgecolor=CHART_SURFACE,
            markeredgewidth=1.5,
            zorder=3,
            label=s.get("name"),
        )
        last_value = s["values"][-1]
        ax.annotate(
            _fmt(last_value, suffix),
            (len(labels) - 1, last_value),
            xytext=(8, 0),
            textcoords="offset points",
            ha="left",
            va="center",
            fontsize=11,
            color=color,
            fontweight="bold",
        )

    _style_axes(ax)
    if spec.get("ylabel"):
        ax.set_ylabel(spec["ylabel"])
    if any(s.get("name") for s in series):
        ax.legend(frameon=False, loc="upper left", labelcolor=INK_SECONDARY)
    if spec.get("title"):
        ax.set_title(spec["title"], fontsize=14, color=INK_PRIMARY, pad=16, loc="left")

    # room on the right for the direct end-labels
    xmin, xmax = ax.get_xlim()
    ax.set_xlim(xmin, xmax + (xmax - xmin) * 0.12)
    fig.tight_layout()
    return fig


RENDERERS = {"bar": render_bar, "line": render_line}


def generate_chart(spec: dict) -> Path:
    chart_type = spec.get("type")
    if chart_type not in RENDERERS:
        raise ValueError(f"unsupported chart type {chart_type!r} — use 'bar' or 'line'")

    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    out_name = spec.get("out") or "chart.png"
    out_path = CHARTS_DIR / out_name

    fig = RENDERERS[chart_type](spec)
    fig.savefig(out_path, facecolor=CHART_SURFACE)
    plt.close(fig)
    return out_path


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--spec", required=True, help="Path to a chart spec JSON file, or '-' for stdin")
    args = parser.parse_args()

    if args.spec == "-":
        spec = json.load(sys.stdin)
    else:
        spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))

    out_path = generate_chart(spec)
    print(out_path)


if __name__ == "__main__":
    main()
