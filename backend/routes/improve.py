"""
POST /improve — enrich and deepen the Cognee knowledge graph.

Runs improve() across ALL datasets so every studied topic benefits.
"""

import cognee
from fastapi import APIRouter

router = APIRouter(prefix="/improve", tags=["improve"])


async def _get_all_datasets():
    try:
        from cognee.modules.users.methods import get_default_user
        from cognee.modules.data.methods.get_datasets import get_datasets
        user = await get_default_user()
        return await get_datasets(user.id)
    except Exception:
        return []


@router.post("")
async def improve_memory():
    """
    Run Cognee's improve() pipeline across all datasets — extracts deeper
    relationships, prunes stale data, and strengthens graph connections.
    """
    datasets = await _get_all_datasets()
    targets = [d.name for d in datasets] if datasets else ["main_dataset"]

    for dataset_name in targets:
        try:
            await cognee.improve(dataset=dataset_name)
        except Exception:
            pass  # skip datasets that fail (e.g. empty)

    return {"status": "ok", "message": f"Memory graph enriched ({len(targets)} dataset(s))."}
