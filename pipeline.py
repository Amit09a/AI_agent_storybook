"""End-to-end story generation, illustration generation, and PDF export."""

from __future__ import annotations

import os
from pathlib import Path

from image_generator import generate_character_reference, generate_page_illustrations
from pdf_generator import create_storybook_pdf
from story_generator import generate_demo_story
from validators import validate_illustrations, validate_story_output


def run_story_pipeline(
    user_prompt: str,
    output_dir: str | Path = "outputs",
    max_revisions: int = 1,
    demo_mode: bool | None = None,
) -> dict:
    """Generate a five-page illustrated story and export the final PDF.

    With ``demo_mode=True``, this function uses a fixed sample story and clearly
    labelled placeholder images; it makes no Gemini or Replicate API calls.
    With ``demo_mode=False``, Gemini generates/reviews the story and Replicate
    Imagen 4 generates the character reference plus five page illustrations.
    """
    if not user_prompt or not user_prompt.strip():
        raise ValueError("Please enter a story prompt.")
    if max_revisions < 0:
        raise ValueError("max_revisions cannot be negative.")

    if demo_mode is None:
        demo_mode = (
            os.getenv("STORYBOOK_DEMO_MODE", "false").strip().lower()
            in {"1", "true", "yes"}
        )

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print("[1/5] Generating and reviewing story...", flush=True)
    if demo_mode:
        story = generate_demo_story(user_prompt)
        result = {"story_plan": story, "review": None, "revision_count": 0}
        print("Demo mode: using the predefined sample story (no Gemini call).", flush=True)
    else:
        # Import only in real mode so the offline demo remains runnable without
        # LangChain's provider packages or API credentials.
        from agent import generate_reviewed_story

        result = generate_reviewed_story(
            user_prompt=user_prompt.strip(),
            max_revisions=max_revisions,
        )
        story = result["story_plan"]

    print("[2/5] Validating story...", flush=True)
    validate_story_output(story)

    print("[3/5] Generating character reference...", flush=True)
    reference_path = generate_character_reference(
        character=story.character,
        output_dir=output_path,
        demo_mode=demo_mode,
    )

    print("[4/5] Generating five page illustrations...", flush=True)
    image_paths = generate_page_illustrations(
        story_plan=story,
        reference_path=reference_path,
        output_dir=output_path,
        demo_mode=demo_mode,
    )
    validate_illustrations(image_paths)

    print("[5/5] Creating PDF...", flush=True)
    pdf_path = create_storybook_pdf(
        story_plan=story,
        image_paths=image_paths,
        output_path=output_path / "storybook.pdf",
    )

    print("Pipeline completed successfully!", flush=True)
    return {
        "story_plan": story,
        "review": result.get("review"),
        "revision_count": result.get("revision_count", 0),
        "character_reference": str(reference_path),
        "image_paths": [str(path) for path in image_paths],
        "pdf_path": str(pdf_path),
        "demo_mode": demo_mode,
    }
