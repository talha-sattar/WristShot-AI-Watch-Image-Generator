from typing import List

from prompt_builder import PromptSettings, build_static_velvet_prompt


def log(message: str, data=None) -> None:
    print(f"[PromptGeneration] {message}", flush=True)
    if data is not None:
        print(f"[PromptGeneration] {data}", flush=True)


class PromptGenerationService:
    """
    Static prompt service for the current single-style pipeline.

    Dynamic text-model prompt generation is intentionally disabled for now because
    the current product requirement is strict watch preservation with only a
    velvet-cloth background change.
    """

    def __init__(self):
        log("Initialized static Velvet cloth background prompt service")

    def generate_prompt_variations(self, settings: PromptSettings, count: int) -> List[str]:
        count = max(1, min(int(count), 4))
        prompts = [
            build_static_velvet_prompt(settings=settings, variant_index=i, total_variants=count)
            for i in range(count)
        ]
        log("Generated static velvet prompt variations", {
            "count": len(prompts),
            "first_prompt_preview": prompts[0][:900] if prompts else "",
        })
        return prompts


# -----------------------------------------------------------------------------
# Old dynamic prompt-generation code is intentionally commented out, not deleted.
# Re-enable later when the API moves from static prompts to dynamic prompting.
#
# import json
# import os
# import re
# from openai import OpenAI
#
# class PromptGenerationService:
#     def __init__(self):
#         api_key = os.getenv("OPENAI_API_KEY")
#         if not api_key:
#             raise ValueError("OPENAI_API_KEY is missing.")
#         self.client = OpenAI(api_key=api_key)
#         self.model = os.getenv("OPENAI_TEXT_MODEL", "gpt-4.1-mini")
#
#     def generate_prompt_variations(self, settings: PromptSettings, count: int) -> List[str]:
#         # Dynamic text-model prompt expansion was here.
#         pass
# -----------------------------------------------------------------------------
