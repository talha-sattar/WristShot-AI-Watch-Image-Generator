import json
import shutil
import traceback
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from image_service import ImageService
from prompt_builder import PromptSettings, STYLE_DEFINITIONS

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
GENERATED_DIR = BASE_DIR / "generated_outputs"
STYLE_REFERENCES_DIR = BASE_DIR / "style_references"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
GENERATED_DIR.mkdir(parents=True, exist_ok=True)
STYLE_REFERENCES_DIR.mkdir(parents=True, exist_ok=True)


def log(message: str, data=None) -> None:
    print(f"[FastAPI] {message}", flush=True)
    if data is not None:
        print(f"[FastAPI] {data}", flush=True)


app = FastAPI(title="AlienTime Studio Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://9ba0-39-34-86-235.ngrok-free.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/generated", StaticFiles(directory=GENERATED_DIR), name="generated")
app.mount("/style-reference-images", StaticFiles(directory=STYLE_REFERENCES_DIR), name="style_reference_images")
app.mount("/style_references", StaticFiles(directory=STYLE_REFERENCES_DIR), name="style_references")

image_service = ImageService(generated_dir=GENERATED_DIR, style_references_dir=STYLE_REFERENCES_DIR)


def save_upload_file(upload_file: Optional[UploadFile], target_dir: Path) -> Optional[Path]:
    if upload_file is None:
        return None
    ext = Path(upload_file.filename or "uploaded.png").suffix or ".png"
    file_path = target_dir / f"{uuid.uuid4().hex}{ext}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    log("Uploaded file saved", {
        "original_name": upload_file.filename,
        "saved_path": str(file_path),
        "content_type": upload_file.content_type,
        "size_bytes": file_path.stat().st_size,
    })
    return file_path


def parse_supporting_props(raw: str) -> List[str]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [str(x) for x in parsed]
    except Exception:
        pass
    return [item.strip() for item in raw.split(",") if item.strip()]


def list_style_reference_images(base_url: str) -> List[Dict]:
    valid_exts = {".png", ".jpg", ".jpeg", ".webp"}
    examples = []
    for style_id, meta in STYLE_DEFINITIONS.items():
        style_dir = STYLE_REFERENCES_DIR / style_id
        images = []
        if style_dir.exists() and style_dir.is_dir():
            for path in sorted(style_dir.iterdir()):
                if path.is_file() and path.suffix.lower() in valid_exts:
                    images.append(f"{base_url}/style-reference-images/{style_id}/{path.name}")

        examples.append({
            "id": style_id,
            "name": meta["name"],
            "description": meta["instruction"],
            "images": images,
        })
    return examples


@app.get("/health")
def health_check():
    log("Health check called")
    return {"status": "ok"}


@app.get("/style-references")
def style_references(request: Request):
    base_url = str(request.base_url).rstrip("/")
    examples = list_style_reference_images(base_url)
    log("Style references requested", {"styles": len(examples), "image_counts": {x["id"]: len(x["images"]) for x in examples}})
    return {"styles": examples}


@app.post("/generate")
async def generate(
    request: Request,
    watch_image: UploadFile = File(...),
    branding_image: Optional[UploadFile] = File(None),
    dial_image: Optional[UploadFile] = File(None),
    selected_style: str = Form("velvet-cloth-background"),
    model_provider: str = Form("openai-gpt-image"),
    output_count: int = Form(4),
    creative_direction: str = Form(""),
    brand_mode: str = Form("visual-reference"),
    dial_reference_mode: str = Form("off"),
    product_strength: int = Form(100),
    scene_creativity: int = Form(15),
    background_style: str = Form("green-velvet"),
    custom_background: str = Form(""),
    camera_angle: str = Form("auto"),
    lighting_style: str = Form("soft-studio"),
    supporting_props: str = Form("[]"),
    negative_prompt: str = Form(""),
    aspect_ratio: str = Form("1:1"),
    quality_mode: str = Form("ultra"),
):
    request_id = uuid.uuid4().hex[:10]
    log(f"/generate request received [{request_id}]", {
        "selected_style": selected_style,
        "model_provider": model_provider,
        "output_count": output_count,
        "creative_direction_length": len(creative_direction or ""),
        "brand_mode": brand_mode,
        "dial_reference_mode": dial_reference_mode,
        "product_strength": product_strength,
        "scene_creativity": scene_creativity,
        "background_style": background_style,
        "custom_background": custom_background,
        "camera_angle": camera_angle,
        "lighting_style": lighting_style,
        "supporting_props_raw": supporting_props,
        "negative_prompt_length": len(negative_prompt or ""),
        "aspect_ratio": aspect_ratio,
        "quality_mode": quality_mode,
        "watch_filename": watch_image.filename,
        "branding_filename": branding_image.filename if branding_image else None,
        "dial_filename": dial_image.filename if dial_image else None,
    })

    try:
        watch_path = save_upload_file(watch_image, UPLOAD_DIR)
        branding_path = save_upload_file(branding_image, UPLOAD_DIR)
        dial_path = save_upload_file(dial_image, UPLOAD_DIR)
        parsed_props = parse_supporting_props(supporting_props)
        log(f"Parsed supporting props [{request_id}]", parsed_props)

        settings = PromptSettings(
            selected_style=selected_style,
            model_provider=model_provider,
            creative_direction=creative_direction,
            brand_mode=brand_mode,
            dial_reference_mode=dial_reference_mode,
            has_branding_image=branding_path is not None,
            has_dial_image=dial_path is not None,
            product_strength=product_strength,
            scene_creativity=scene_creativity,
            background_style=background_style,
            custom_background=custom_background,
            camera_angle=camera_angle,
            lighting_style=lighting_style,
            supporting_props=parsed_props,
            negative_prompt=negative_prompt,
            aspect_ratio=aspect_ratio,
            quality_mode=quality_mode,
        )

        generated = image_service.generate_images(
            watch_image_path=watch_path,
            branding_image_path=branding_path,
            dial_image_path=dial_path,
            settings=settings,
            output_count=output_count,
        )

        base_url = str(request.base_url).rstrip("/")
        images = [
            {
                "variant": item["variant"],
                "url": f"{base_url}/generated/{item['filename']}",
                "prompt": item["prompt"],
                "provider": item.get("provider", model_provider),
            }
            for item in generated
        ]

        log(f"/generate completed [{request_id}]", {"count": len(images), "urls": [x["url"] for x in images]})
        return {"images": images, "count": len(images)}

    except Exception as exc:
        tb = traceback.format_exc()
        log(f"/generate failed [{request_id}]", {"error": str(exc), "traceback": tb})
        raise HTTPException(status_code=500, detail=str(exc))
