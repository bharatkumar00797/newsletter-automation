# Newsletter Automation (WAT Framework Demo)

A reference implementation of an AI-assisted newsletter pipeline, built to
demonstrate the **WAT framework — Workflows, Agents, Tools** — a pattern for
structuring AI agent systems so that probabilistic reasoning (the LLM) and
deterministic execution (code) stay cleanly separated.

> The WAT framework, and the idea of applying it to a newsletter pipeline,
> came from Nate Herk's YouTube content on AI agent architecture. This repo
> is my own implementation of the pattern, built as a portfolio piece and a
> reference others can read, run, or adapt — it isn't wired up to a live
> production newsletter.

## What it does

Give it a topic, and the pipeline:

1. **Researches** it (web search, done by the agent layer directly — no
   script needed for that part)
2. **Drafts** structured content — headline, sections, stat callouts, sources
3. **Generates data charts** for anything chart-worthy (`tools/generate_chart.py`),
   using a colorblind-validated palette that's deliberately *not* the brand's
   own accent colors (see the "Brand vs. data color" note below)
4. **Generates a header image** with Gemini's image model, "Nano Banana"
   (`tools/generate_image_gemini.py`)
5. **Renders** everything into a branded, dark-mode-native HTML newsletter
   (`tools/render_newsletter.py`, styled by `tools/templates/newsletter_base.html`)
6. **Publishes** the result as a shareable interactive HTML preview — the
   actual deliverable, per this repo's "outputs live in the cloud, not in
   `.tmp/`" rule

The full step-by-step SOP — including how to handle a vague topic, missing
data, or a failed image generation — is in
[`workflows/newsletter.md`](workflows/newsletter.md).

## Why WAT

Chaining LLM calls end-to-end is fragile — if each step is ~90% reliable,
five chained steps compound down to ~59% success. WAT fixes that by giving
each layer one job:

| Layer | Lives in | Responsibility |
|---|---|---|
| **Workflows** | [`workflows/`](workflows/) | Markdown SOPs — the objective, inputs, steps, and edge cases for a task, written like you'd brief a teammate |
| **Agents** | (you, or an automated agent) | Reads a workflow, decides what to run and in what order, handles failures, asks when something's ambiguous |
| **Tools** | [`tools/`](tools/) | Small, deterministic Python scripts — one script per capability, each testable on its own |

## Brand vs. data color

Worth calling out as a design decision, not an oversight: the brand identity
in `brand_assets/` uses a six-hue accent set for *decoration* (masthead,
topic tag, stat-tile numbers, section stripes) — always paired with a text
label. `tools/generate_chart.py` uses a **different**, separately
colorblind-validated 8-hue palette for actual chart data, because several of
the brand's own hues turned out to be indistinguishable under certain color
vision deficiencies when checked against the template's dark surface. Decoration
can get away with looking merely good; data encoding can't. The reasoning and
validation are documented in the "Brand system" section of
[`workflows/newsletter.md`](workflows/newsletter.md).

## Project layout

```
brand_assets/       Logo/identity reference images the template is built around
tools/               Python scripts — one per pipeline step
  templates/          Jinja2 HTML template (newsletter_base.html)
workflows/           SOPs describing when/how to run the tools
.tmp/                Disposable intermediates (drafts, charts, rendered HTML, ...)
.env                 API keys (gitignored — copy from .env.example)
```

## Quickstart

```bash
python -m venv .venv
.venv\Scripts\activate          # or `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
cp .env.example .env            # then fill in GEMINI_API_KEY for header images
```

Then follow [`workflows/newsletter.md`](workflows/newsletter.md) end to end:
research and draft a topic into `.tmp/draft_<slug>.json`, generate any charts
and the header image, render with `tools/render_newsletter.py`, and publish
the result as an interactive HTML preview.

`tools/generate_chart.py` and `tools/render_newsletter.py` have no external
dependencies beyond what's in `requirements.txt` and can be run standalone
against any draft JSON matching the schema documented at the top of
`render_newsletter.py` — useful for testing template changes without
re-running research. `tools/generate_image_gemini.py` needs `GEMINI_API_KEY`
and fails fast (by design) if it's missing, rather than silently skipping
the header image.

## Extending it

Adding a new capability follows the same loop every time: read (or write) the
workflow, check `tools/` for something that already does the job, build a new
tool only if nothing fits, verify it, then update the workflow with what you
learned.
