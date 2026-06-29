"""
GET /graph — return knowledge graph nodes and edges for visualization.

Uses cognee.export() which reuses the existing DB connection rather than
opening a second one (which would cause a file-lock conflict).
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


@router.get("")
async def get_graph():
    """
    Export the knowledge graph via cognee.export() and return
    a D3-friendly {nodes, links} payload.
    """
    try:
        snapshot = await cognee.export(format="pydantic")

        nodes = []
        node_ids = set()

        for node in snapshot.nodes:
            nid = str(node.id)
            node_type = getattr(node, "type", type(node).__name__)
            # Try common label fields in order of preference
            label = (
                getattr(node, "name", None)
                or getattr(node, "title", None)
                or (getattr(node, "text", None) or "")[:40]
                or node_type
            )
            nodes.append({
                "id":    nid,
                "label": str(label),
                "type":  str(node_type),
                "color": NODE_COLORS.get(str(node_type), NODE_COLORS["default"]),
            })
            node_ids.add(nid)

        links = []
        for edge in snapshot.edges:
            sid = str(edge.source_id)
            tid = str(edge.target_id)
            if sid in node_ids and tid in node_ids:
                links.append({
                    "source":   sid,
                    "target":   tid,
                    "relation": edge.relationship,
                })

        return {"nodes": nodes, "links": links}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
