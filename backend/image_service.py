import base64
import os
import time
import uuid
from contextlib import ExitStack
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional

from openai import OpenAI

from prompt_builder import (
    PromptSettings,
    aspect_ratio_to_size,
    normalize_model_provider,
    quality_to_openai,
)
from prompt_generation_service import PromptGenerationService


def log(message: str, data=None) -> None:
    print(f"[ImageService] {message}", flush=True)
    if data is not None:
        print(f"[ImageService] {data}", flush=True)


class ImageService:
    def __init__(self, generated_dir: Path, style_references_dir: Optional[Path] = None):
        self.generated_dir = generated_dir
        self.generated_dir.mkdir(parents=True, exist_ok=True)

        self.style_references_dir = style_references_dir
        self.openai_model = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")
        self.google_model = os.getenv("GOOGLE_IMAGE_MODEL", os.getenv("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image-preview"))
        self.prompt_service = PromptGenerationService()
        self._openai_client: Optional[OpenAI] = None

        log("Initialized", {
            "openai_model": self.openai_model,
            "google_model": self.google_model,
            "generated_dir": str(self.generated_dir),
            "style_references_dir": str(self.style_references_dir) if self.style_references_dir else None,
            "active_style": "Velvet cloth background",
        })

    def _get_openai_client(self) -> OpenAI:
        if self._openai_client is not None:
            return self._openai_client

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is missing. Add it to backend/.env or your environment variables.")

        self._openai_client = OpenAI(api_key=api_key)
        return self._openai_client

    def _save_b64_image(self, b64_data: str, filename: str) -> Path:
        image_bytes = base64.b64decode(b64_data)
        return self._save_image_bytes(image_bytes=image_bytes, filename=filename)

    def _save_image_bytes(self, image_bytes: bytes, filename: str) -> Path:
        output_path = self.generated_dir / filename
        with open(output_path, "wb") as f:
            f.write(image_bytes)
        log("Saved generated image", {"path": str(output_path), "bytes": len(image_bytes)})
        return output_path

    def _save_prompt(self, image_filename: str, prompt: str, provider: str, model_name: str) -> None:
        prompt_filename = image_filename.replace(".png", "_prompt.txt")
        with open(self.generated_dir / prompt_filename, "w", encoding="utf-8") as f:
            f.write(f"Provider: {provider}\n")
            f.write(f"Model: {model_name}\n\n")
            f.write(prompt)

    def _generate_with_openai(
        self,
        prompt: str,
        watch_image_path: Path,
        branding_image_path: Optional[Path],
        dial_image_path: Optional[Path],
        size: str,
        quality: str,
        model: str,
    ):
        client = self._get_openai_client()
        with ExitStack() as stack:
            image_files = [stack.enter_context(open(watch_image_path, "rb"))]
            if branding_image_path:
                image_files.append(stack.enter_context(open(branding_image_path, "rb")))
            if dial_image_path:
                image_files.append(stack.enter_context(open(dial_image_path, "rb")))

            return client.images.edit(
                model=model,
                image=image_files,
                prompt=prompt,
                size=size,
                quality=quality,
            )

    def _extract_google_image_bytes(self, response) -> bytes:
        parts = []

        response_parts = getattr(response, "parts", None)
        if response_parts:
            parts.extend(response_parts)

        candidates = getattr(response, "candidates", None) or []
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            if content and getattr(content, "parts", None):
                parts.extend(content.parts)

        for part in parts:
            if hasattr(part, "as_image"):
                try:
                    image = part.as_image()
                    if image is not None:
                        buffer = BytesIO()
                        image.save(buffer, format="PNG")
                        return buffer.getvalue()
                except Exception:
                    pass

            inline_data = getattr(part, "inline_data", None) or getattr(part, "inlineData", None)
            if inline_data is not None:
                data = getattr(inline_data, "data", None)
                if data:
                    return data if isinstance(data, bytes) else base64.b64decode(data)

        raise ValueError("No image data returned by Google Nano Banana model.")

    def _generate_with_google(
        self,
        prompt: str,
        watch_image_path: Path,
        branding_image_path: Optional[Path],
        dial_image_path: Optional[Path],
        model: str,
    ) -> bytes:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY is missing. Add it to backend/.env or your environment variables.")

        try:
            from google import genai
            from google.genai import types
            from PIL import Image
        except Exception as exc:
            raise ImportError(
                "Google Nano Banana provider requires dependencies: pip install google-genai pillow"
            ) from exc

        client = genai.Client(api_key=api_key)
        contents = [prompt, Image.open(watch_image_path)]
        if branding_image_path:
            contents.append(Image.open(branding_image_path))
        if dial_image_path:
            contents.append(Image.open(dial_image_path))

        config = types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"])

        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )
        return self._extract_google_image_bytes(response)

    def generate_images(
        self,
        watch_image_path: Path,
        branding_image_path: Optional[Path],
        dial_image_path: Optional[Path],
        settings: PromptSettings,
        output_count: int = 4,
    ) -> List[Dict]:
        output_count = max(1, min(int(output_count), 4))
        provider = normalize_model_provider(settings.model_provider)
        size = aspect_ratio_to_size(settings.aspect_ratio)
        quality = quality_to_openai(settings.quality_mode)

        log("Generation started", {
            "provider": provider,
            "output_count": output_count,
            "selected_style": settings.selected_style,
            "size": size,
            "quality": quality,
            "watch_image_path": str(watch_image_path),
            "branding_image_path": str(branding_image_path) if branding_image_path else None,
            "dial_image_path": str(dial_image_path) if dial_image_path else None,
            "has_branding_image": settings.has_branding_image,
            "has_dial_image": settings.has_dial_image,
            "dial_reference_mode": settings.dial_reference_mode,
        })

        prompts = self.prompt_service.generate_prompt_variations(settings=settings, count=output_count)
        results = []

        for i, prompt in enumerate(prompts):
            variant_number = i + 1
            log(f"Variant {variant_number}/{output_count}: calling image model", {
                "provider": provider,
                "prompt_preview": prompt[:1200],
                "prompt_length": len(prompt),
            })

            start_time = time.time()
            if provider == "openai-gpt-image":
                response = self._generate_with_openai(
                    prompt=prompt,
                    watch_image_path=watch_image_path,
                    branding_image_path=branding_image_path,
                    dial_image_path=dial_image_path,
                    size=size,
                    quality=quality,
                    model=settings.model_provider,
                )
                if not response.data or not response.data[0].b64_json:
                    raise ValueError(f"No image returned for variant {variant_number}")
                image_filename = f"{uuid.uuid4().hex}_variant_{variant_number}.png"
                self._save_b64_image(response.data[0].b64_json, image_filename)
            elif provider == "google-nano-banana":
                image_bytes = self._generate_with_google(
                    prompt=prompt,
                    watch_image_path=watch_image_path,
                    branding_image_path=branding_image_path,
                    dial_image_path=dial_image_path,
                    model=settings.model_provider,
                )
                image_filename = f"{uuid.uuid4().hex}_variant_{variant_number}.png"
                self._save_image_bytes(image_bytes, image_filename)
            else:
                raise ValueError("Unsupported model provider. Use openai-gpt-image or google-nano-banana.")

            elapsed = round(time.time() - start_time, 2)
            log(f"Variant {variant_number}: image response received", {"provider": provider, "elapsed_seconds": elapsed})

            self._save_prompt(image_filename=image_filename, prompt=prompt, provider=provider, model_name=settings.model_provider)
            results.append({
                "filename": image_filename,
                "prompt": prompt,
                "variant": variant_number,
                "provider": settings.model_provider,
            })

        log("Generation completed", {"generated_count": len(results), "provider": provider})
        return results
