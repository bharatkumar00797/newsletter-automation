# Newsletter Automation

## Objective

Given a topic (and optionally an angle or audience), produce a researched,
on-brand HTML newsletter issue with data charts and an illustrative header
image, and publish it as a shareable Claude Artifact.

## Brand system

The template (`tools/templates/newsletter_base.html`) is built around the
identity in `brand_assets/` (envelope mark as the logo; dark-navy ground;
a six-hue accent set — cyan/purple/teal/amber/pink/coral; Poppins as the
bold display face). This is baked into the template once, not redecided per
issue — don't restyle it per topic.

**Important nuance**: the six brand hues are used only as *decoration*
(masthead, topic tag, stat-tile numbers, section accent stripes) — always
next to a text label, never the only way to tell two things apart. When
those exact hues were run through the `dataviz` skill's
`scripts/validate_palette.js` against the brand's dark surface (`#0f1420`),
several adjacent pairs failed the colorblind-safety checks (e.g. the
blue-ish cyan and the purple read as the same color under protanopia).
So `tools/generate_chart.py` uses a *different*, separately-validated 8-hue
set for actual chart data (still styled to sit on the same dark surface —
see its module docstring for the exact colors and the validator command
that confirmed it). If the brand assets are ever updated, re-run the
validator before changing either palette — don't eyeball it.

## Required inputs

- **Topic** — what the issue is about. If it's vague ("AI news"), ask the
  user to narrow it (a specific angle, time window, or audience) before
  starting research.
- **Masthead name** (optional) — the newsletter's series name, e.g. "THE
  BRIEF". Defaults to "THE BRIEF" if the user hasn't named their newsletter.

## Steps

1. **Clarify** the topic/angle/audience with the user if the request is
   ambiguous. Don't guess at scope for a topic that could mean several
   different things.

2. **Research** using WebSearch/WebFetch directly (no tool script — this is
   reasoning work). Gather facts, figures, and source URLs. Save working
   notes to `.tmp/research_<slug>.md` so the draft step has something to
   pull from. Only cite numbers you can attribute to a real source.

3. **Draft** the structured content as a JSON file at
   `.tmp/draft_<slug>.json`, matching the schema documented at the top of
   `tools/render_newsletter.py`: headline, dek, 3-6 sections (each with an
   eyebrow/heading/paragraphs, optionally a pull-quote and/or a chart), 2-4
   stat-tile entries for standout numbers, and a sources list. Identify
   which stats deserve a full chart (a trend or a multi-item comparison)
   versus a simple stat tile (a single standout number needs no chart —
   see the stat-strip in the template).

4. **Generate charts** — for each chart-worthy data point, write a small
   spec (see the docstring in `tools/generate_chart.py`) and run:
   ```
   python tools/generate_chart.py --spec <spec.json>
   ```
   This writes a PNG to `.tmp/charts/`. Reference that filename as
   `"charts/<name>.png"` in the matching section's `chart.src` field in the
   draft JSON (paths are relative to where the final HTML lives, see step 6).

5. **Generate the header image** via Google AI Studio's Gemini API (Nano
   Banana):
   ```
   python tools/generate_image_gemini.py --prompt "<description>" --out header.png
   ```
   Requires `GEMINI_API_KEY` in `.env`. Writes to `.tmp/images/header.png`.
   Reference it as `"images/header.png"` in the draft's `hero_image.src`.
   For visual consistency with the brand, steer the prompt toward the same
   world as the template — dark navy tones, a flat/vector illustration
   style, cyan as the dominant accent — rather than leaving style unstated.

6. **Render the HTML**:
   ```
   python tools/render_newsletter.py --draft .tmp/draft_<slug>.json --slug <slug>
   ```
   Writes `.tmp/newsletter_<slug>.html`.

7. **Publish as a Claude Artifact.** Read the rendered HTML, then use the
   Artifact tool with `file_path` set to the rendered HTML and `files` set to
   the chart PNGs and header image, published at the same relative paths used
   in the draft (`charts/<name>.png`, `images/header.png`) so the `<img>` tags
   resolve without any rewriting. This is the deliverable — a shareable link,
   per CLAUDE.md's rule that outputs the user needs live in a cloud service,
   not `.tmp/`.

8. **Report the Artifact link back to the user.**

## Expected outputs

- A published Artifact (styled HTML newsletter issue with embedded charts and
  header image) — the deliverable.
- `.tmp/research_<slug>.md`, `.tmp/draft_<slug>.json`,
  `.tmp/newsletter_<slug>.html`, `.tmp/charts/*.png`, `.tmp/images/*.png` —
  disposable intermediates, regenerated each run.

## Edge cases

- **No reliable data for a claimed stat** — skip the chart/stat tile rather
  than inventing numbers. A qualitative newsletter with fewer charts beats
  one with fabricated ones.
- **Conflicting figures across sources** — flag the discrepancy in the text
  (e.g. "estimates range from X to Y") instead of silently picking one.
- **`generate_chart.py` raises "too many categories/series"** — the fixed
  8-slot palette is a hard cap by design (colorblind-safety only validates
  up to 8 adjacent categories). Fold extra categories into "Other" or split
  into two charts rather than extending the palette.
- **Gemini image generation fails, or rejects the model string** — ship the
  newsletter without the header image rather than blocking on it. Nano
  Banana's model id has moved before (`gemini-2.5-flash-image` ->
  `gemini-3.1-flash-image` as of this writing) — check
  https://ai.google.dev/gemini-api/docs/image-generation and update
  `DEFAULT_MODEL` in `tools/generate_image_gemini.py` if it errors on an
  unrecognized model.
- **`GEMINI_API_KEY` missing** — `generate_image_gemini.py` fails fast with
  a clear message; ask the user for a key from
  https://aistudio.google.com/apikey rather than guessing.
