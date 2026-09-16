"""
Generates a header image for a newsletter issue using Google's Gemini image
model ("Nano Banana").

Fails fast if GEMINI_API_KEY is missing or the model call errors — per
workflows/newsletter.md, the calling agent should catch that and ship the
issue without a header image rather than block on it; this script itself
doesn't guess at a fallback.

Usage:
    python tools/generate_image_gemini.py --prompt "<description>" --out header.png
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
IMAGES_DIR = REPO_ROOT / ".tmp" / "images"

# Nano Banana's model id has moved before (gemini-2.5-flash-image ->
# gemini-3.1-flash-image as of this writing). If generation starts failing
# with an "unrecognized model" error, check
# https://ai.google.dev/gemini-api/docs/image-generation and update this.
DEFAULT_MODEL = "gemini-3.1-flash-image"


def generate_image(prompt: str, out_name: str) -> Path:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print(
            "GEMINI_API_KEY is not set. Get a key at https://aistudio.google.com/apikey "
            "and add it to .env before running this tool.",
            file=sys.stderr,
        )
        sys.exit(1)

    from google import genai

    model = os.environ.get("GEMINI_IMAGE_MODEL", DEFAULT_MODEL)
    client = genai.Client(api_key=api_key)

    try:
        response = client.models.generate_content(model=model, contents=prompt)
    except Exception as exc:  # noqa: BLE001 — surfaced to the caller as a clear, actionable failure
        print(
            f"Gemini image generation failed with model '{model}': {exc}\n"
            "If this looks like an unrecognized-model error, Nano Banana's model id "
            "may have moved again — check "
            "https://ai.google.dev/gemini-api/docs/image-generation and update "
            "DEFAULT_MODEL in this script.",
            file=sys.stderr,
        )
        sys.exit(1)

    image_bytes = None
    for part in response.candidates[0].content.parts:
        if getattr(part, "inline_data", None) is not None:
            image_bytes = part.inline_data.data
            break

    if image_bytes is None:
        print(f"Gemini returned no image data for model '{model}'.", file=sys.stderr)
        sys.exit(1)

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = IMAGES_DIR / out_name
    out_path.write_bytes(image_bytes)
    return out_path


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--prompt", required=True, help="Image generation prompt")
    parser.add_argument("--out", default="header.png", help="Output filename under .tmp/images/ (default: header.png)")
    args = parser.parse_args()

    load_dotenv()
    out_path = generate_image(args.prompt, args.out)
    print(out_path)


if __name__ == "__main__":
    main()
