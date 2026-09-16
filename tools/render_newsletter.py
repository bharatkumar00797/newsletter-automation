"""
Renders a drafted newsletter (structured JSON) against
tools/templates/newsletter_base.html into a standalone HTML file.

Usage:
    python tools/render_newsletter.py --draft .tmp/draft_ai-regulation.json --slug ai-regulation

Draft JSON schema — see tools/templates/newsletter_base.html for how each
field is used:
{
  "masthead_name": "THE BRIEF",              // optional, defaults below
  "topic_tag": "AI Policy",                  // optional
  "issue_date": "September 14, 2026",        // optional, defaults to today
  "title": "Headline for this issue",
  "dek": "One-sentence subtitle.",
  "hero_image": {"src": "images/header.png", "alt": "...", "caption": "..."},   // optional
  "stats": [{"value": "42%", "label": "of X report Y"}],                        // optional, 2-4 items
  "sections": [
    {
      "eyebrow": "BACKGROUND",               // optional
      "heading": "Section heading",          // optional
      "paragraphs": ["...", "..."],
      "pull_quote": "...",                   // optional
      "chart": {"src": "charts/x.png", "alt": "...", "caption": "..."}          // optional
    }
  ],
  "sources": [{"title": "...", "url": "..."}]
}

Image/chart `src` paths are relative to the output HTML file — by convention
charts live in .tmp/charts/ and images in .tmp/images/, both siblings of the
.tmp/ directory this script writes into, so "charts/x.png" and "images/x.png"
resolve correctly without copying anything.
"""

import argparse
import json
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = REPO_ROOT / "tools" / "templates"
OUTPUT_DIR = REPO_ROOT / ".tmp"

DEFAULT_MASTHEAD_NAME = "THE BRIEF"


def _today_formatted() -> str:
    # cross-platform equivalent of "%B %-d, %Y" (no leading zero on the day;
    # %-d isn't supported by strftime on Windows)
    today = date.today()
    return f"{today:%B} {today.day}, {today:%Y}"


def render_newsletter(draft: dict, slug: str) -> Path:
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=False)
    template = env.get_template("newsletter_base.html")

    context = {
        "masthead_name": draft.get("masthead_name", DEFAULT_MASTHEAD_NAME),
        "topic_tag": draft.get("topic_tag"),
        "issue_date": draft.get("issue_date", _today_formatted()),
        "title": draft["title"],
        "dek": draft.get("dek"),
        "hero_image": draft.get("hero_image"),
        "stats": draft.get("stats", []),
        "sections": draft.get("sections", []),
        "sources": draft.get("sources", []),
    }

    html = template.render(**context)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"newsletter_{slug}.html"
    out_path.write_text(html, encoding="utf-8")
    return out_path


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--draft", required=True, help="Path to the draft JSON file")
    parser.add_argument("--slug", required=True, help="Short slug used for the output filename")
    args = parser.parse_args()

    draft = json.loads(Path(args.draft).read_text(encoding="utf-8"))
    out_path = render_newsletter(draft, args.slug)
    print(out_path)


if __name__ == "__main__":
    main()
