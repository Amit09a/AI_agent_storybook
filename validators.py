"""Validation helpers for story plans and generated illustration files."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from story_generator import validate_story_plan


def validate_story_output(story_plan) -> None:
    """Validate that the plan contains five complete, sequential story pages."""
    validate_story_plan(story_plan)
    if len(story_plan.pages) != 5:
        raise ValueError("Story must contain exactly five pages.")
    if [page.page_number for page in story_plan.pages] != [1, 2, 3, 4, 5]:
        raise ValueError("Story pages must be numbered 1 to 5.")
    print("Story validation passed.", flush=True)


def validate_illustrations(image_paths: list[str | Path]) -> None:
    """Validate that exactly five page illustration files exist and are readable."""
    if len(image_paths) != 5:
        raise ValueError("Exactly five page illustrations are required.")

    for raw_path in image_paths:
        path = Path(raw_path)
        if not path.is_file():
            raise FileNotFoundError(f"Missing illustration: {path}")
        try:
            with Image.open(path) as image:
                image.verify()
            with Image.open(path) as image:
                if image.width < 1 or image.height < 1:
                    raise ValueError("Invalid image dimensions.")
        except Exception as exc:
            raise ValueError(f"Invalid illustration: {path}") from exc

    print("Illustration validation passed.", flush=True)
