"""
DELETE /forget — remove memory (all or a specific topic/dataset).
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from backend.services.memory import erase

router = APIRouter(prefix="/forget", tags=["forget"])


class ForgetPayload(BaseModel):
    topic: Optional[str] = None   # if None, erases everything
    everything: Optional[bool] = False


@router.delete("")
async def forget(payload: ForgetPayload):
    """
    Erase memory. Pass topic to remove a specific subject,
    or everything=true to wipe the entire memory graph.
    """
    if payload.everything or not payload.topic:
        await erase(everything=True)
        return {"status": "ok", "message": "All memory erased."}
    else:
        await erase(dataset=payload.topic)
        return {"status": "ok", "message": f"Memory for topic '{payload.topic}' erased."}
