"""
POST /ask — query memory and return an AI-synthesised answer.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import os
import json
from groq import AsyncGroq
from backend.services.memory import query

router = APIRouter(prefix="/ask", tags=["ask"])

client = AsyncGroq(api_key=os.getenv("LLM_API_KEY"))
MODEL = os.getenv("LLM_MODEL", "groq/llama-3.3-70b-versatile").replace("groq/", "")


class AskPayload(BaseModel):
    question: str
    topic: Optional[str] = None  # filter by topic (future use)


@router.post("")
async def ask(payload: AskPayload):
    """
    1. Recall relevant memory chunks for the question.
    2. Pass them as context to the LLM.
    3. Stream back a synthesised answer.
    """
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # Step 1: pull memory
    memory_chunks = await query(payload.question)

    if not memory_chunks:
        return {"answer": "I don't have anything in memory about that yet. Try studying some material first!", "sources": []}

    context = "\n".join(f"- {chunk}" for chunk in memory_chunks[:6])

    # Step 2: synthesise answer via LLM
    system_prompt = (
        "You are a personal study assistant with access to the user's stored notes and knowledge graph. "
        "Your job is to answer questions using ONLY the memory context provided — do not use outside knowledge. "
        "Guidelines:\n"
        "- Be clear, structured, and educational\n"
        "- Use bullet points or numbered steps when helpful\n"
        "- If the context answers the question fully, do so confidently\n"
        "- If the context only partially covers it, answer what you can and note what's missing\n"
        "- If the context is unrelated, say: 'I don't have notes on this yet.'\n"
        "- Never make up facts not in the context"
    )
    user_prompt = (
        f"Here is what I know from my notes:\n\n{context}\n\n"
        f"Question: {payload.question}\n\n"
        "Answer based strictly on the notes above:"
    )

    async def generate():
        stream = await client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            stream=True,
            max_tokens=600,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield f"data: {json.dumps({'token': delta})}\n\n"
        yield f"data: {json.dumps({'done': True, 'sources': memory_chunks[:3]})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
