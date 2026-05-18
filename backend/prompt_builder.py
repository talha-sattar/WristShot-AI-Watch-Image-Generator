from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class PromptSettings:
    creative_direction: str = ""
    selected_style: str = "velvet-cloth-background"
    model_provider: str = "openai-gpt-image"
    brand_mode: str = "visual-reference"
    dial_reference_mode: str = "off"
    has_branding_image: bool = False
    has_dial_image: bool = False
    product_strength: int = 100
    scene_creativity: int = 15
    background_style: str = "green-velvet"
    custom_background: str = ""
    camera_angle: str = "auto"
    lighting_style: str = "soft-studio"
    supporting_props: List[str] = field(default_factory=list)
    negative_prompt: str = ""
    aspect_ratio: str = "1:1"
    quality_mode: str = "ultra"


def _norm(value: str) -> str:
    return (value or "").strip().lower()


# -----------------------------------------------------------------------------
# Old preset styles are intentionally commented out, not deleted.
# Re-enable later only if the product needs multiple style presets again.
#
# OLD_STYLE_DEFINITIONS = {
#     "flat-lay": {...},
#     "open-box": {...},
#     "dark-studio": {...},
#     "ecommerce": {...},
#     "editorial": {...},
#     "macro-detail": {...},
# }
# -----------------------------------------------------------------------------

STYLE_DEFINITIONS: Dict[str, Dict[str, str]] = {
    "velvet-cloth-background": {
        "name": "Velvet cloth background",
        "instruction": (
            "Use a premium velvet cloth background only. Green velvet is the default. "
            "The watch itself must remain unchanged; only the background/surface should be replaced or refined."
        ),
    },
}


STYLE_ALIASES = {
    "velvet": "velvet-cloth-background",
    "velvet cloth": "velvet-cloth-background",
    "velvet cloth background": "velvet-cloth-background",
    "green velvet": "velvet-cloth-background",
    "green-velvet": "velvet-cloth-background",
    "": "velvet-cloth-background",
    "none": "velvet-cloth-background",
    "no-style": "velvet-cloth-background",
    "no style": "velvet-cloth-background",
    "no preset style": "velvet-cloth-background",

    # Old preset aliases are intentionally mapped away from active use.
    # "flat lay": "flat-lay",
    # "open box": "open-box",
    # "dark studio": "dark-studio",
    # "ecommerce": "ecommerce",
    # "editorial": "editorial",
    # "macro": "macro-detail",
}


def normalize_style(style: str) -> str:
    key = _norm(style)
    if key in STYLE_DEFINITIONS:
        return key
    return STYLE_ALIASES.get(key, "velvet-cloth-background")


def style_name(style: str) -> str:
    style_key = normalize_style(style)
    return STYLE_DEFINITIONS[style_key]["name"]


def normalize_model_provider(provider: str) -> str:
    key = _norm(provider)
    if key.startswith("gpt") or key.startswith("dall") or key.startswith("openai"):
        return "openai-gpt-image"
    if key.startswith("gemini") or key.startswith("imagen") or key.startswith("google") or key.startswith("nano"):
        return "google-nano-banana"
    return "openai-gpt-image"


def is_scenario_1(settings: PromptSettings) -> bool:
    return False


def aspect_ratio_to_size(aspect_ratio: str) -> str:
    key = _norm(aspect_ratio)
    mapping = {
        "1:1": "1024x1024",
        "1:1 square": "1024x1024",
        "4:5": "1024x1536",
        "4:5 instagram portrait": "1024x1536",
        "16:9": "1536x1024",
        "16:9 landscape": "1536x1024",
        "3:2": "1536x1024",
        "3:2 product photo": "1536x1024",
    }
    return mapping.get(key, "1024x1024")


def quality_to_openai(quality_mode: str) -> str:
    key = _norm(quality_mode)
    if key == "standard":
        return "medium"
    return "high"


def _background_description(settings: PromptSettings) -> str:
    key = _norm(settings.background_style)
    if key == "custom" and settings.custom_background.strip():
        return settings.custom_background.strip()
    if key in {"custom", "green-velvet", "green velvet", "velvet-cloth-background", "velvet cloth background"}:
        return "deep emerald green velvet cloth with realistic folds, soft nap texture, and premium luxury fabric depth"
    if key in {"black-velvet", "black velvet"}:
        return "black velvet cloth with realistic folds, soft nap texture, and premium luxury fabric depth"
    if key in {"blue-velvet", "blue velvet"}:
        return "royal blue velvet cloth with realistic folds, soft nap texture, and premium luxury fabric depth"
    if key in {"burgundy-velvet", "burgundy velvet"}:
        return "burgundy velvet cloth with realistic folds, soft nap texture, and premium luxury fabric depth"
    return "deep emerald green velvet cloth with realistic folds, soft nap texture, and premium luxury fabric depth"


def _lighting_description(settings: PromptSettings) -> str:
    key = _norm(settings.lighting_style)
    mapping = {
        "soft-studio": "soft controlled studio lighting with clean specular highlights and natural shadows",
        "soft studio lighting": "soft controlled studio lighting with clean specular highlights and natural shadows",
        "cinematic": "subtle cinematic studio lighting while preserving the original watch colors exactly",
        "bright": "bright clean commercial studio lighting while preserving the original watch colors exactly",
        "warm": "warm luxury studio lighting while preserving the original watch colors exactly",
        "auto": "realistic premium product lighting that best matches the original watch perspective",
    }
    return mapping.get(key, mapping["soft-studio"])


def _camera_description(settings: PromptSettings) -> str:
    key = _norm(settings.camera_angle)
    mapping = {
        "top-down": "keep the watch perspective from the input as much as possible; do not invent a new angle",
        "45-degree": "keep the watch perspective from the input as much as possible; do not rotate the watch into a new angle",
        "front-facing": "keep the watch perspective from the input as much as possible; do not create a box shot",
        "macro": "keep the watch perspective from the input as much as possible; do not crop away important dial or bracelet details",
        "auto": "preserve the original camera angle, crop logic, watch orientation, and perspective as much as possible",
    }
    return mapping.get(key, mapping["auto"])


def _branding_rule(settings: PromptSettings) -> str:
    if not settings.has_branding_image:
        return "No branding or cloth reference image is uploaded. Do not add AlienTime branding, logos, new text, cards, papers, or any branded object."

    key = _norm(settings.brand_mode)
    if key in {"none", "no branding"}:
        return "A cloth/branding image is uploaded but branding is disabled. Do not add visible branding or text anywhere."
    if key in {"subtle", "subtle branding only"}:
        return "If the uploaded cloth/branding image is used, place it only as a very subtle background cloth/detail. Do not put any branding on the watch, dial, case, bracelet, crystal, or bezel."
    if key in {"visible", "place branding clearly on cloth/card"}:
        return "If the uploaded cloth/branding image is used, place branding only on the cloth/background area as a physical cloth or accessory, never on the watch itself."
    return "Use the uploaded cloth/branding image only as an optional background or cloth reference. Do not place branding on the watch itself."


def _dial_reference_block(settings: PromptSettings) -> str:
    mode = _norm(settings.dial_reference_mode)
    if not settings.has_dial_image or mode == "off":
        return (
            "No optional dial close-up reference image is being used. "
            "Still preserve the dial as accurately as possible from the main watch image."
        )

    if mode == "aggressive":
        return (
            "A dial close-up reference image is provided and MUST be used aggressively as the highest-priority fidelity reference for the dial region. "
            "Treat the full watch photo as the master reference for the whole watch, and treat the dial close-up as the master reference for the dial only. "
            "The dial close-up must control the exact brand name text, logo, minute-track lines, inner lines, indices, numerals, subdial printing, date-window typography, micro-text, hand shapes, hand positions, and the exact time shown. "
            "Do not blur, soften, tilt, bend, deform, or rewrite any dial text or line work. The dial must remain zoom-clean and high-definition."
        )

    return (
        "A dial close-up reference image is provided and should be used strongly to improve dial fidelity. "
        "Use it to preserve the exact brand name text, logo, minute-track lines, indices, numerals, micro-text, and the exact hand positions/time while keeping the full watch image as the overall watch reference. "
        "Avoid blurred, tilted, bent, or deformed dial text or line work."
    )


def _default_negative_prompt() -> str:
    return (
        "changed watch design, changed watch identity, changed dial, changed dial text, changed brand name, changed logo, changed numerals, changed indices, "
        "changed minute track, changed inner lines, changed hands, changed time, moved hour hand, moved minute hand, moved seconds hand, altered date window, altered subdial, "
        "changed case shape, changed bezel, changed bracelet, changed strap, changed crown, changed lugs, changed metal color, warped watch face, distorted geometry, melted bracelet, "
        "extra watch, duplicate watch, added logo on watch, removed logo from watch, fake brand text, random text, unreadable dial, blurry dial, low-resolution dial, soft focus, motion blur, "
        "tilted text, bent text, deformed typography, broken minute track, smeared lines, low-detail rendering, messy props, box, papers, cards, booklet, hands, people"
    )


def build_static_velvet_prompt(settings: PromptSettings, variant_index: int = 0, total_variants: int = 4) -> str:
    background = _background_description(settings)
    lighting = _lighting_description(settings)
    camera = _camera_description(settings)
    branding = _branding_rule(settings)
    dial_reference = _dial_reference_block(settings)
    negative_prompt = settings.negative_prompt.strip() or _default_negative_prompt()

    variant_rules = [
        "Variant 1: Clean hero composition. Keep the original watch centered and place it naturally on softly folded velvet cloth.",
        "Variant 2: Slightly richer velvet folds. Keep the same watch scale, same orientation, and same dial/time; add deeper fabric texture behind and around the watch only.",
        "Variant 3: More premium shadow depth. Preserve the watch exactly and use elegant velvet drapery with realistic contact shadows under the watch.",
        "Variant 4: Cleaner commercial version. Preserve the watch exactly and use a refined velvet cloth background with minimal folds and strong product clarity.",
    ]
    variant_rule = variant_rules[variant_index % len(variant_rules)]

    user_direction = settings.creative_direction.strip()
    user_direction_text = ""
    if user_direction:
        user_direction_text = (
            "\nUser direction, apply only if it does not conflict with preserving the watch exactly:\n"
            f"- {user_direction}\n"
        )

    if settings.has_branding_image and settings.has_dial_image:
        reference_roles = (
            "REFERENCE IMAGES:\n"
            "- Image A = the full watch/product image. This is the master reference for the whole watch and composition.\n"
            "- Image B = the optional cloth/branding image. Use it only as a cloth/background or branding reference.\n"
            "- Image C = the optional dial close-up image. This is the master fidelity reference for the dial only.\n"
        )
    elif settings.has_dial_image:
        reference_roles = (
            "REFERENCE IMAGES:\n"
            "- Image A = the full watch/product image. This is the master reference for the whole watch and composition.\n"
            "- Image B = the optional dial close-up image. This is the master fidelity reference for the dial only.\n"
        )
    elif settings.has_branding_image:
        reference_roles = (
            "REFERENCE IMAGES:\n"
            "- Image A = the full watch/product image. This is the master reference for the whole watch and composition.\n"
            "- Image B = the optional cloth/branding image. Use it only as a cloth/background or branding reference.\n"
        )
    else:
        reference_roles = (
            "REFERENCE IMAGES:\n"
            "- Image A = the full watch/product image. This is the master reference for the whole watch and composition.\n"
        )

    return f"""
Edit the uploaded watch image as a strict background-replacement product photo.

{reference_roles}
TASK:
Replace or refine ONLY the background/surface behind and around the watch with: {background}.
The output should look like premium luxury watch product photography on velvet cloth.

ABSOLUTE WATCH PRESERVATION RULES:
- Preserve the exact watch from the input image with maximum fidelity.
- Do not redesign, restyle, redraw, repaint, recolor, rotate, resize, stretch, compress, simplify, or reinterpret the watch.
- Preserve the exact case shape, bezel geometry, bracelet/strap links, lugs, crown, pushers, crystal, metal color, reflections, and finishing.
- Preserve the exact dial color, exact dial texture, exact dial text, exact brand name, exact logo, exact numbers, exact minute-track lines, exact inner lines, exact markers, exact date window, exact subdial, exact hands, exact seconds hand, and exact typography.
- Preserve the exact time shown on the watch in the input image. Do not move, rotate, shorten, lengthen, or redraw the hour hand, minute hand, or seconds hand.
- Preserve the date value shown in the date window exactly.
- Preserve the original camera perspective, lens compression, watch angle, crop logic, and watch placement as much as possible.
- The model may improve background realism only; the model must not improve, invent, rewrite, blur, or hallucinate watch details.

DIAL ACCURACY RULE:
- {dial_reference}
- The dial must remain very high-definition, crisp under zoom, and suitable for close inspection.
- The brand name text on the dial must be perfectly written, perfectly aligned, and not tilted, bent, stretched, or deformed.
- The minute-track lines, inner line work, indices, and micro typography must stay razor-sharp and legible.

BACKGROUND RULES:
- Use only velvet cloth as the background/surface.
- The exact velvet color and texture must strictly follow the requested background description: {background}.
- Velvet should have realistic folds, soft fabric nap, gentle highlights, natural texture, and believable contact shadows.
- The velvet should wrap behind and around the watch naturally without covering, hiding, or altering any watch component.
- Do not add a watch box, papers, cards, booklets, certificates, human hands, jewelry, tools, or extra accessories.

LIGHTING AND CAMERA:
- {lighting}.
- {camera}.
- Keep the watch sharp, crisp, and highly detailed, especially the dial and hands.
- Maintain realistic shadows and reflections consistent with the unchanged watch.

CLOTH / BRANDING RULE:
- {branding}

VARIANT RULE:
- {variant_rule}
{user_direction_text}
NEGATIVE CONSTRAINTS:
- {negative_prompt}

FINAL OUTPUT:
Ultra-realistic luxury watch product photography on velvet cloth, background changed only, watch identity unchanged, exact dial/time/date preserved, dial micro-detail preserved, text perfectly legible, sharp commercial quality.
""".strip()


def build_scenario_1_prompt(settings: PromptSettings, variant_index: int = 0, total_variants: int = 1) -> str:
    return build_static_velvet_prompt(settings, variant_index=variant_index, total_variants=total_variants)


def build_prompt_brief(settings: PromptSettings) -> str:
    return build_static_velvet_prompt(settings, variant_index=0, total_variants=1)


def build_prompt(settings: PromptSettings, variant_index: int = 0, total_variants: int = 1) -> str:
    return build_static_velvet_prompt(settings, variant_index=variant_index, total_variants=total_variants)
