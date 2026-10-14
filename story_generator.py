"""Story data models, validation, and direct Gemini story generation."""

from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError

load_dotenv()

DEFAULT_GEMINI_MODEL = "gemini-3.5-flash-lite"


# ---------- Data models ----------

class StoryPage(BaseModel):
    page_number: int = Field(ge=1, le=5)
    narrative_text: str
    scene_description: str
    character_action: str
    environment: str
    mood: str


class CharacterConcept(BaseModel):
    name: str
    species: str
    appearance: str
    personality: str
    signature_features: list[str]


class StoryPlan(BaseModel):
    title: str
    target_age: str
    theme: str
    moral: str
    character: CharacterConcept
    pages: list[StoryPage]


# ---------- Story validation ----------

def validate_story_plan(data: dict[str, Any] | StoryPlan) -> StoryPlan:
    """Validate required content, exactly five pages, and sequential numbering."""
    plan = data if isinstance(data, StoryPlan) else StoryPlan.model_validate(data)

    if len(plan.pages) != 5:
        raise ValueError("The story must contain exactly five pages.")

    expected_numbers = [1, 2, 3, 4, 5]
    actual_numbers = [page.page_number for page in plan.pages]
    if actual_numbers != expected_numbers:
        raise ValueError("Pages must be numbered sequentially from 1 to 5.")

    required_story_fields = {
        "title": plan.title,
        "target_age": plan.target_age,
        "theme": plan.theme,
        "moral": plan.moral,
        "character name": plan.character.name,
        "character species": plan.character.species,
        "character appearance": plan.character.appearance,
        "character personality": plan.character.personality,
    }
    for field_name, value in required_story_fields.items():
        if not value or not value.strip():
            raise ValueError(f"Required story field is empty: {field_name}.")

    if not plan.character.signature_features:
        raise ValueError("The main character needs at least one signature feature.")
    if any(not feature or not feature.strip() for feature in plan.character.signature_features):
        raise ValueError("Character signature features cannot be empty.")

    for page in plan.pages:
        fields = {
            "narrative_text": page.narrative_text,
            "scene_description": page.scene_description,
            "character_action": page.character_action,
            "environment": page.environment,
            "mood": page.mood,
        }
        empty_fields = [
            field_name for field_name, value in fields.items()
            if not value or not value.strip()
        ]
        if empty_fields:
            raise ValueError(
                f"Page {page.page_number} has empty required field(s): "
                + ", ".join(empty_fields)
            )

    return plan


# ---------- Demo mode: no API key required ----------

def generate_demo_story(prompt: str) -> StoryPlan:
    """Return a predefined sample story for offline testing; not LLM-generated."""
    del prompt  # Demo mode deliberately uses a fixed, predictable sample.

    character = CharacterConcept(
        name="Pip",
        species="fox",
        appearance=(
            "A small orange fox with a cream muzzle and chest, "
            "green eyes, and a blue scarf."
        ),
        personality="Curious, playful, and kind-hearted",
        signature_features=[
            "orange fur",
            "cream muzzle and chest",
            "green eyes",
            "blue scarf",
            "small rounded body",
        ],
    )

    page_data = [
        (
            "Pip loved exploring the magical forest.",
            "Pip discovers a sparkling apple tree.",
            "Pip looks up at the tree in wonder.",
            "A sunny forest clearing with a sparkling apple tree.",
            "Curious",
        ),
        (
            "One morning, Pip found a tree full of shiny red apples.",
            "Pip gathers a few apples into a little basket.",
            "Pip carefully collects the apples.",
            "An apple tree surrounded by soft green grass.",
            "Excited",
        ),
        (
            "Two hungry rabbits asked Pip if they could have an apple.",
            "Pip notices the hungry rabbits beside the tree.",
            "Pip pauses and looks at the apples in the basket.",
            "A quiet woodland path near the apple tree.",
            "Thoughtful",
        ),
        (
            "Pip smiled and shared the apples with the rabbits.",
            "Pip offers apples to both rabbit friends.",
            "Pip shares the apples with a happy smile.",
            "A bright forest clearing with flowers and leafy trees.",
            "Warm and joyful",
        ),
        (
            "The friends enjoyed their snack together and discovered that sharing made the day even brighter.",
            "Pip and the rabbits enjoy apples together.",
            "Pip celebrates with both friends.",
            "A sunny forest picnic beneath the apple tree.",
            "Happy and peaceful",
        ),
    ]

    pages = [
        StoryPage(
            page_number=index,
            narrative_text=narrative,
            scene_description=scene,
            character_action=action,
            environment=environment,
            mood=mood,
        )
        for index, (narrative, scene, action, environment, mood)
        in enumerate(page_data, start=1)
    ]

    return validate_story_plan(
        StoryPlan(
            title="Pip and the Sharing Tree",
            target_age="4-7",
            theme="Sharing and friendship",
            moral="Sharing can make good things even better.",
            character=character,
            pages=pages,
        )
    )


# ---------- Real LLM mode: Gemini ----------

def generate_with_gemini(prompt: str) -> StoryPlan:
    """Generate a structured story plan using the Gemini API."""
    from google import genai
    from google.genai import types

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    client = genai.Client(api_key=api_key)
    instructions = f"""
You are a children's picture-book story planner.

Create a complete story plan based on this single user prompt:
{prompt}

Requirements:
- Produce exactly five pages, numbered 1 through 5.
- Write for children aged approximately 4-7 unless the prompt specifies another age group.
- Create a coherent beginning, development, conflict, resolution, and ending.
- Use simple, age-appropriate language and concise page text.
- Keep the main character's visual identity stable across all pages.
- The character must have a name, species, appearance, personality, and distinctive visual features.
- Every page must have non-empty narrative_text, scene_description, character_action, environment, and mood.
- Scene descriptions must be suitable for generating illustrations.
- Return ONLY valid JSON matching this structure, with exactly five objects in pages:

{{
  "title": "Story title",
  "target_age": "4-7",
  "theme": "Story theme",
  "moral": "Story lesson",
  "character": {{
    "name": "Character name",
    "species": "Species",
    "appearance": "Detailed visual description",
    "personality": "Personality traits",
    "signature_features": ["feature 1", "feature 2"]
  }},
  "pages": [
    {{"page_number": 1, "narrative_text": "...", "scene_description": "...", "character_action": "...", "environment": "...", "mood": "..."}},
    {{"page_number": 2, "narrative_text": "...", "scene_description": "...", "character_action": "...", "environment": "...", "mood": "..."}},
    {{"page_number": 3, "narrative_text": "...", "scene_description": "...", "character_action": "...", "environment": "...", "mood": "..."}},
    {{"page_number": 4, "narrative_text": "...", "scene_description": "...", "character_action": "...", "environment": "...", "mood": "..."}},
    {{"page_number": 5, "narrative_text": "...", "scene_description": "...", "character_action": "...", "environment": "...", "mood": "..."}}
  ]
}}
"""

    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL),
        contents=instructions,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    if not response.text:
        raise ValueError("Gemini returned an empty response.")

    try:
        data = json.loads(response.text)
    except json.JSONDecodeError as exc:
        raise ValueError("Gemini returned invalid JSON for the story plan.") from exc
    return validate_story_plan(data)


def generate_story_plan(prompt: str, demo_mode: bool = False) -> StoryPlan:
    """Generate a validated five-page story; use the fixed sample in demo mode."""
    if not prompt or not prompt.strip():
        raise ValueError("Please enter a story prompt.")
    if demo_mode:
        return generate_demo_story(prompt)

    try:
        return generate_with_gemini(prompt.strip())
    except (ValidationError, json.JSONDecodeError):
        raise
    except Exception as exc:
        raise RuntimeError(f"Story generation failed: {exc}") from exc


if __name__ == "__main__":
    sample_prompt = "Create a funny story about a little fox who learns to share in a magical forest."
    plan = generate_story_plan(sample_prompt, demo_mode=True)
    print(f"\nTitle: {plan.title}")
    print(f"Character: {plan.character.name}")
    print(f"Number of pages: {len(plan.pages)}")
    for page in plan.pages:
        print(f"\nPage {page.page_number}: {page.narrative_text}")
