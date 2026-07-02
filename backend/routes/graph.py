"""
GET /graph — return knowledge graph nodes and edges for visualization.

Exports ALL datasets for the current user and merges them so the graph
shows everything the user has studied, regardless of topic name.
"""

import cognee
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/graph", tags=["graph"])

NODE_COLORS = {
    "Entity":        "#4f8ef7",
    "EntityType":    "#a78bfa",
    "DocumentChunk": "#f97316",
    "TextDocument":  "#94a3b8",
    "TextSummary":   "#34d399",
    "default":       "#64748b",
}


async def _get_all_datasets():
    """Return all dataset names for the default user."""
    try:
        from cognee.modules.users.methods import get_default_user
        from cognee.modules.data.methods.get_datasets import get_datasets
        user = await get_default_user()
        return await get_datasets(user.id)
    except Exception:
        return []


@router.get("")
async def get_graph():
    """
    Export all datasets and return a merged D3-friendly {nodes, links} payload.
    """
    try:
        datasets = await _get_all_datasets()

        all_nodes: dict[str, dict] = {}
        all_links: list[dict] = []

        # Export each dataset and merge; fall back to default export if no datasets found
        targets = [d.name for d in datasets] if datasets else ["main_dataset"]

        for dataset_name in targets:
            try:
                snapshot = await cognee.export(dataset=dataset_name, format="pydantic")
            except Exception:
                continue

            for node in snapshot.nodes:
                nid = str(node.id)
                if nid in all_nodes:
                    continue
                node_type = getattr(node, "type", type(node).__name__)
                label = (
                    getattr(node, "name", None)
                    or getattr(node, "title", None)
                    or (getattr(node, "text", None) or "")[:40]
                    or node_type
                )
                all_nodes[nid] = {
                    "id":    nid,
                    "label": str(label),
                    "type":  str(node_type),
                    "color": NODE_COLORS.get(str(node_type), NODE_COLORS["default"]),
                }

            for edge in snapshot.edges:
                sid = str(edge.source_id)
                tid = str(edge.target_id)
                if sid in all_nodes and tid in all_nodes:
                    all_links.append({
                        "source":   sid,
                        "target":   tid,
                        "relation": edge.relationship,
                    })

        return {"nodes": list(all_nodes.values()), "links": all_links}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
