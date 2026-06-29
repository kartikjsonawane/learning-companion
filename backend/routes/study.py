"""
POST /study — ingest text, uploaded file, or a URL into Cognee memory.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional
import httpx
from backend.services.memory import store

router = APIRouter(prefix="/study", tags=["study"])


class TextPayload(BaseModel):
    text: str
    topic: Optional[str] = "default"


@router.post("/text")
async def study_text(payload: TextPayload):
    """Store raw text into memory under an optional topic/dataset."""
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    await store(payload.text, dataset=payload.topic or "default")
    return {"status": "ok", "message": "Text stored in memory.", "topic": payload.topic}


@router.post("/file")
async def study_file(
    file: UploadFile = File(...),
    topic: str = Form(default="default"),
):
    """Upload a .txt or .pdf file and store its contents in memory."""
    allowed = {"text/plain", "application/pdf"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Only .txt and .pdf files are supported.")

    content = await file.read()

    if file.content_type == "text/plain":
        text = content.decode("utf-8", errors="ignore")
    else:
        # Basic PDF text extraction via pypdf (already installed with cognee)
        import io
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(content))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)

    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from file.")

    await store(text, dataset=topic)
    return {"status": "ok", "message": f"File '{file.filename}' stored in memory.", "topic": topic}


@router.post("/url")
async def study_url(url: str = Form(...), topic: str = Form(default="default")):
    """Fetch a URL and store its text content in memory."""
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; LearningCompanion/1.0; +https://github.com/learningcompanion)"
    }
    try:
        async with httpx.AsyncClient(timeout=15, headers=headers) as client:
            resp = await client.get(url, follow_redirects=True)
            resp.raise_for_status()
            text = resp.text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not fetch URL: {e}")

    # Strip HTML tags crudely (good enough for a trial)
    import re
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    if len(text) < 50:
        raise HTTPException(status_code=400, detail="Not enough text content found at URL.")

    await store(text[:8000], dataset=topic)  # cap at 8k chars
    return {"status": "ok", "message": f"URL content stored in memory.", "topic": topic}
