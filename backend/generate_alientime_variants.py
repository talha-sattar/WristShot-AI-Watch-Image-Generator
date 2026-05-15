import base64
import os
from io import BytesIO
from pathlib import Path
from typing import List, Optional

from openai import OpenAI

# ============================================================
# CONFIG
# ============================================================
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "openai-gpt-image")
OPENAI_IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")
GOOGLE_IMAGE_MODEL = os.getenv("GOOGLE_IMAGE_MODEL", os.getenv("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image-preview"))

WATCH_IMAGE_PATH = r"C:\Users\Alyan\Desktop\Watch photography\input-watch.jpg.jpeg"
BRANDING_IMAGE_PATH = ""  # optional cloth / branding reference
DIAL_IMAGE_PATH = ""      # optional dial close-up for maximum dial accuracy

OUTPUT_DIR = Path("generated_outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

IMAGE_SIZE = "1024x1024"
IMAGE_QUALITY = "high"

# -----------------------------------------------------------------------------
# Old variant directions are intentionally commented out, not deleted.
# Old styles:
# - open-box
# - flat-lay
# - dark-studio
# - ecommerce
# - editorial
# - macro-detail
# -----------------------------------------------------------------------------


def build_base_prompt() -> str:
    dial_block = ""
    if DIAL_IMAGE_PATH.strip():
        dial_block = """
DIAL CLOSE-UP RULE:
- A dial close-up reference image is provided and must be used aggressively as the highest-priority fidelity reference for the dial region.
- Use it to preserve the exact brand name text, exact logo, exact minute-track lines, exact inner lines, exact numerals, exact indices, exact micro-text, and the exact hand positions/time.
- The dial must remain zoom-clean, ultra-sharp, and free from blurred, tilted, bent, or deformed text.
""".strip()
    else:
        dial_block = "No optional dial close-up reference image is being used. Still preserve the dial as accurately as possible from the main watch image."

    return f"""
Edit the uploaded watch image as a strict background-replacement product photo.

TASK:
Replace or refine ONLY the background/surface behind and around the watch with deep emerald green velvet cloth.
The output should look like premium luxury watch product photography on realistic velvet fabric.

ABSOLUTE WATCH PRESERVATION RULES:
- Preserve the exact watch from the input image with maximum fidelity.
- Do not redesign, restyle, redraw, repaint, recolor, rotate, resize, stretch, compress, simplify, or reinterpret the watch.
- Preserve the exact case shape, bezel geometry, bracelet/strap links, lugs, crown, pushers, crystal, metal color, reflections, and finishing.
- Preserve the exact dial color, exact dial text, exact brand name, exact logo, exact minute-track lines, exact inner lines, exact numbers, exact markers, exact date window, exact subdial, exact hands, exact seconds hand, and exact typography.
- Preserve the exact time shown on the watch in the input image. Do not move, rotate, shorten, lengthen, or redraw the hour hand, minute hand, or seconds hand.
- Preserve the date value shown in the date window exactly.
- Preserve the original camera perspective, lens compression, watch angle, crop logic, and watch placement as much as possible.
- The model may improve background realism only; the model must not improve or invent watch details.

DIAL ACCURACY:
- {dial_block}
- The dial must remain high-definition and clean under zoom.
- The brand name text must be perfectly written, aligned, and not tilted or deformed.

BACKGROUND RULES:
- Use only green velvet cloth as the background/surface.
- Velvet should have realistic folds, soft fabric nap, gentle highlights, natural texture, and believable contact shadows.
- The velvet should wrap behind and around the watch naturally without covering, hiding, or altering any watch component.
- Do not add a watch box, papers, cards, booklets, certificates, human hands, jewelry, tools, or extra accessories.

LIGHTING AND QUALITY:
- Use soft controlled studio lighting with clean specular highlights and natural shadows.
- Keep the watch sharp, crisp, and highly detailed, especially the dial and hands.
- Maintain realistic shadows and reflections consistent with the unchanged watch.

NEGATIVE CONSTRAINTS:
changed watch design, changed watch identity, changed dial, changed dial text, changed brand name, changed logo, changed minute track, changed inner lines, changed numerals, changed indices, changed hands, changed time, moved hour hand, moved minute hand, moved seconds hand, altered date window, altered subdial, changed case shape, changed bezel, changed bracelet, changed strap, changed crown, warped watch face, distorted geometry, melted bracelet, extra watch, duplicate watch, added logo on watch, removed logo from watch, fake brand text, random text, unreadable dial, blurry dial, low-resolution dial, soft focus, motion blur, tilted text, bent text, deformed typography, messy props, box, papers, cards, booklet, hands, people.

FINAL OUTPUT:
Ultra-realistic luxury watch product photography on green velvet cloth, background changed only, watch identity unchanged, exact dial/time/date preserved, sharp commercial quality.
""".strip()


def build_variant_prompts() -> List[str]:
    base = build_base_prompt()
    variants = [
        base + "\n\nVARIANT 1: Clean hero composition. Keep the original watch centered and place it naturally on softly folded green velvet cloth.",
        base + "\n\nVARIANT 2: Slightly richer velvet folds. Keep the same watch scale, same orientation, and same dial/time; add deeper fabric texture behind and around the watch only.",
        base + "\n\nVARIANT 3: More premium shadow depth. Preserve the watch exactly and use elegant velvet drapery with realistic contact shadows under the watch.",
        base + "\n\nVARIANT 4: Cleaner commercial version. Preserve the watch exactly and use a refined green velvet cloth background with minimal folds and strong product clarity.",
    ]
    return variants


def save_image_from_b64(b64_data: str, save_path: Path):
    image_bytes = base64.b64decode(b64_data)
    with open(save_path, "wb") as f:
        f.write(image_bytes)


def save_image_bytes(image_bytes: bytes, save_path: Path):
    with open(save_path, "wb") as f:
        f.write(image_bytes)


def generate_openai_variant(client: OpenAI, prompt: str, watch_image_path: str, branding_image_path: Optional[str], dial_image_path: Optional[str]):
    files = []
    opened = []
    try:
        watch_file = open(watch_image_path, "rb")
        opened.append(watch_file)
        files.append(watch_file)
        if branding_image_path:
            branding_file = open(branding_image_path, "rb")
            opened.append(branding_file)
            files.append(branding_file)
        if dial_image_path:
            dial_file = open(dial_image_path, "rb")
            opened.append(dial_file)
            files.append(dial_file)
        return client.images.edit(
            model=OPENAI_IMAGE_MODEL,
            image=files,
            prompt=prompt,
            size=IMAGE_SIZE,
            quality=IMAGE_QUALITY,
        )
    finally:
        for f in opened:
            f.close()


def generate_google_variant(prompt: str, watch_image_path: str, branding_image_path: Optional[str], dial_image_path: Optional[str]) -> bytes:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY is missing.")

    try:
        from google import genai
        from google.genai import types
        from PIL import Image
    except Exception as exc:
        raise ImportError("Google provider requires: pip install google-genai pillow") from exc

    client = genai.Client(api_key=api_key)
    contents = [prompt, Image.open(watch_image_path)]
    if branding_image_path:
        contents.append(Image.open(branding_image_path))
    if dial_image_path:
        contents.append(Image.open(dial_image_path))

    response = client.models.generate_content(
        model=GOOGLE_IMAGE_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
    )

    parts = list(getattr(response, "parts", []) or [])
    for candidate in getattr(response, "candidates", []) or []:
        content = getattr(candidate, "content", None)
        if content and getattr(content, "parts", None):
            parts.extend(content.parts)

    for part in parts:
        if hasattr(part, "as_image"):
            image = part.as_image()
            if image is not None:
                buffer = BytesIO()
                image.save(buffer, format="PNG")
                return buffer.getvalue()
        inline_data = getattr(part, "inline_data", None) or getattr(part, "inlineData", None)
        if inline_data is not None:
            data = getattr(inline_data, "data", None)
            if data:
                return data if isinstance(data, bytes) else base64.b64decode(data)

    raise ValueError("No image data returned by Google Nano Banana model.")


def main():
    if not os.path.exists(WATCH_IMAGE_PATH):
        raise FileNotFoundError(f"Watch image not found: {WATCH_IMAGE_PATH}")

    branding_path = BRANDING_IMAGE_PATH.strip() or None
    if branding_path and not os.path.exists(branding_path):
        raise FileNotFoundError(f"Branding/reference image not found: {branding_path}")

    dial_path = DIAL_IMAGE_PATH.strip() or None
    if dial_path and not os.path.exists(dial_path):
        raise FileNotFoundError(f"Dial reference image not found: {dial_path}")

    prompts = build_variant_prompts()
    provider = MODEL_PROVIDER.strip().lower()

    print(f"Starting generation of {len(prompts)} velvet-background variants using {provider}...\n")

    openai_client = None
    if provider == "openai-gpt-image":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not found.")
        openai_client = OpenAI(api_key=api_key)

    for i, prompt in enumerate(prompts, start=1):
        print(f"[{i}/{len(prompts)}] Generating variant {i}...")
        try:
            output_path = OUTPUT_DIR / f"velvet_background_variant_{i}.png"

            if provider == "openai-gpt-image":
                result = generate_openai_variant(openai_client, prompt, WATCH_IMAGE_PATH, branding_path, dial_path)
                if not result.data or not result.data[0].b64_json:
                    raise ValueError(f"No image data returned for variant {i}")
                save_image_from_b64(result.data[0].b64_json, output_path)
            elif provider == "google-nano-banana":
                image_bytes = generate_google_variant(prompt, WATCH_IMAGE_PATH, branding_path, dial_path)
                save_image_bytes(image_bytes, output_path)
            else:
                raise ValueError("MODEL_PROVIDER must be openai-gpt-image or google-nano-banana")

            prompt_path = OUTPUT_DIR / f"velvet_background_variant_{i}_prompt.txt"
            with open(prompt_path, "w", encoding="utf-8") as f:
                f.write(prompt)

            print(f"Saved variant {i} to: {output_path}")
        except Exception as e:
            print(f"Error generating variant {i}: {e}")

    print("\nDone.")


if __name__ == "__main__":
    main()
