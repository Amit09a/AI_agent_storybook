"""LangChain tool for generating the character reference and five illustrations."""

from __future__ import annotations

import json
import os

from langchain.tools import tool

from image_generator import generate_character_reference, generate_page_illustrations
from story_generator import validate_story_plan


@tool
def generate_storybook_illustrations(
    story_plan_json: str,
    output_dir: str = "outputs",
) -> str:
    """Generate a character reference and five page illustrations with Replicate Imagen 4.

    Args:
        story_plan_json: Complete story plan serialized as JSON.
        output_dir: Directory where generated image files should be saved.

    Note:
        Imagen 4's Replicate endpoint currently accepts text prompts rather than
        reference-image inputs. Page prompts repeat the character identity details.
    """
    try:
        story_data = json.loads(story_plan_json)
    except json.JSONDecodeError as exc:
        raise ValueError("story_plan_json must contain valid JSON.") from exc

    story_plan = validate_story_plan(story_data)
    demo_mode = (
        os.getenv("STORYBOOK_DEMO_MODE", "false").strip().lower()
        in {"1", "true", "yes"}
    )

    reference_path = generate_character_reference(
        character=story_plan.character,
        output_dir=output_dir,
        demo_mode=demo_mode,
    )
    page_paths = generate_page_illustrations(
        story_plan=story_plan,
        reference_path=reference_path,
        output_dir=output_dir,
        demo_mode=demo_mode,
    )
    if len(page_paths) != 5:
        raise RuntimeError(f"Expected five illustrations, received {len(page_paths)}.")

    result = {
        "character_reference": str(reference_path),
        "page_images": [
            {"page_number": i, "path": str(path)}
            for i, path in enumerate(page_paths, start=1)
        ],
        "image_count": len(page_paths),
        "total_generated_files": len(page_paths) + 1,
        "demo_mode": demo_mode,
    }
    return json.dumps(result, ensure_ascii=False)
