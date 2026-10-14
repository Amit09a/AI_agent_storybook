from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from story_generator import DEFAULT_GEMINI_MODEL, StoryPlan, validate_story_plan
from tools import generate_storybook_illustrations

load_dotenv()


@lru_cache(maxsize=1)
def get_llm() -> ChatGoogleGenerativeAI:
    
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing. Check your .env file.")

    return ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL),
        api_key=api_key,
        max_retries=2,
    )


class StoryReview(BaseModel):
    

    approved: bool = Field(description="Whether the story meets all required criteria.")
    score: int = Field(ge=1, le=10, description="Overall story quality score from 1 to 10.")
    strengths: list[str] = Field(description="What works well in the story.")
    issues: list[str] = Field(description="Specific problems that should be fixed.")
    revision_instructions: str = Field(
        description="Concrete instructions for improving the story."
    )


def build_story_planner_agent():
    
    return create_agent(
        model=get_llm(),
        tools=[],
        name="storybook_planner",
        system_prompt="""
You are an expert children's picture-book author.
Create a complete, age-appropriate story from the user's prompt.
Requirements:
- Exactly five pages, numbered 1, 2, 3, 4, and 5 in order.
- One memorable main character with distinctive visual features.
- Keep the character's appearance consistent across all pages.
- Each page has a clear action, scene, and concise narrative text.
- The story progresses logically from beginning to ending.
- Use age-appropriate writing and a satisfying ending.
- Never leave required fields empty.
- Return the required structured StoryPlan.
""",
        response_format=StoryPlan,
    )


critic_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a strict but constructive critic of children's picture books.
Evaluate the story against these requirements:
1. Exactly five pages numbered 1 through 5 in order.
2. Clear beginning, development, and conclusion.
3. Age-appropriate, coherent narrative.
4. Consistent main-character description.
5. Every page contains enough visual detail for illustration.
6. The story follows the user's original request.
Approve only when it satisfies all required criteria. Give specific corrections
for each important issue. Return the StoryReview schema.""",
        ),
        (
            "human",
            "Original user prompt:\n{user_prompt}\n\nStory plan to review:\n{story_json}",
        ),
    ]
)


def build_story_critic_chain():
    structured_critic = get_llm().with_structured_output(StoryReview, method="json_schema")
    return critic_prompt | structured_critic


revision_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a children's picture-book editor. Revise the provided story
using the critic's feedback while preserving the user's intent and good story
ideas. Mandatory: exactly five pages numbered 1-5; one consistent main character;
age-appropriate writing; clear visual scenes and actions; coherent story and
satisfying ending. Return the complete revised StoryPlan, not only changed pages.""",
        ),
        (
            "human",
            "Original user prompt:\n{user_prompt}\n\nCurrent story:\n{story_json}\n\nCritic feedback:\n{feedback_json}",
        ),
    ]
)


def build_story_revision_chain():
    structured_reviser = get_llm().with_structured_output(StoryPlan, method="json_schema")
    return revision_prompt | structured_reviser


def generate_reviewed_story(user_prompt: str, max_revisions: int = 1) -> dict:
    if not user_prompt or not user_prompt.strip():
        raise ValueError("Please provide a story prompt.")
    if max_revisions < 0:
        raise ValueError("max_revisions cannot be negative.")

    planner = build_story_planner_agent()
    result = planner.invoke(
        {"messages": [{"role": "user", "content": user_prompt.strip()}]}
    )
    plan = result.get("structured_response")
    if plan is None:
        raise RuntimeError("The story planner did not return structured output.")
    plan = validate_story_plan(plan.model_dump())

    critic = build_story_critic_chain()
    reviser = build_story_revision_chain()
    revision_count = 0

    while True:
        review = critic.invoke(
            {"user_prompt": user_prompt, "story_json": plan.model_dump_json(indent=2)}
        )
        if review.approved or revision_count >= max_revisions:
            break
        plan = reviser.invoke(
            {
                "user_prompt": user_prompt,
                "story_json": plan.model_dump_json(indent=2),
                "feedback_json": review.model_dump_json(indent=2),
            }
        )
        plan = validate_story_plan(plan.model_dump())
        revision_count += 1

    return {"story_plan": plan, "review": review, "revision_count": revision_count}


def build_illustration_agent():
    """Create an optional agent that invokes the Replicate illustration tool."""
    return create_agent(
        model=get_llm(),
        tools=[generate_storybook_illustrations],
        name="storybook_illustrator",
        system_prompt="""You coordinate illustrations for children's storybooks.
When provided a complete StoryPlan JSON, call generate_storybook_illustrations
with the complete plan. Do not invent file paths or claim generation succeeded
unless the tool returns successfully. The tool uses Replicate Imagen 4.""",
    )
