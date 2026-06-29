"""
POST /improve — enrich and deepen the Cognee knowledge graph.
"""

from fastapi import APIRouter
from backend.services.memory import enrich

router = APIRouter(prefix="/improve", tags=["improve"])


@router.post("")
async def improve_memory():
    """
    Run Cognee's improve() pipeline — extracts deeper relationships,
    prunes stale data, and strengthens graph connections.
    This is best called after a study session with multiple topics.
    """
    await enrich()
    return {"status": "ok", "message": "Memory graph enriched successfully."}
