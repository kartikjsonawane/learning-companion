"""
POST /quiz — generate quiz questions from memory on a given topic.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import json
from groq import AsyncGroq
from backend.services.memory import query

router = APIRouter(prefix="/quiz", tags=["quiz"])

client = AsyncGroq(api_key=os.getenv("LLM_API_KEY"))
MODEL = os.getenv("LLM_MODEL", "groq/llama-3.3-70b-versatile").replace("groq/", "")


class QuizPayload(BaseModel):
    topic: str
    count: Optional[int] = 5  # number of questions to generate


@router.post("")
async def generate_quiz(payload: QuizPayload):
    """
    Recall memory about a topic, then ask the LLM to generate
    multiple-choice quiz questions from it.
    """
    if not payload.topic.strip():
        raise HTTPException(status_code=400, detail="Topic cannot be empty.")

    count = min(max(payload.count or 5, 1), 10)  # clamp 1-10

    # Pull relevant memory
    memory_chunks = await query(payload.topic)
    if not memory_chunks:
        raise HTTPException(
            status_code=404,
            detail=f"No memory found for topic '{payload.topic}'. Study it first!"
        )

    context = "\n".join(f"- {chunk}" for chunk in memory_chunks[:8])

    system_prompt = (
        "You are a precise quiz generator. Given study notes, create multiple-choice questions that test genuine understanding.\n"
        "Rules:\n"
        "- Questions must be grounded strictly in the provided notes\n"
        "- Each question has exactly 4 options labeled A, B, C, D\n"
        "- Exactly one option is correct; distractors should be plausible but clearly wrong to someone who studied\n"
        "- Vary difficulty: some recall, some application, some inference\n"
        "- Answer field contains ONLY the letter (A, B, C, or D)\n"
        "- Output ONLY a valid JSON array. No markdown, no explanation, no commentary.\n"
        "Format: [{\"question\": \"...\", \"options\": [\"A. ...\", \"B. ...\", \"C. ...\", \"D. ...\"], \"answer\": \"A\"}, ...]"
    )
    user_prompt = (
        f"Study notes on '{payload.topic}':\n{context}\n\n"
        f"Generate exactly {count} multiple-choice questions. Output JSON array only:"
    )

    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=1200,
        temperature=0.3,
    )

    raw = response.choices[0].message.content.strip()

    # Parse JSON — handle markdown code fences if LLM wraps it
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        questions = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="LLM returned malformed quiz JSON. Try again.")

    return {"topic": payload.topic, "questions": questions}
