"""
Cognee memory service — thin wrapper around cognee's 4 core operations.
All functions are async and safe to call from FastAPI route handlers.
"""

import cognee


def _extract_text(result) -> str | None:
    """Extract readable text from any RecallResponse variant."""
    # ResponseQAEntry → use 'answer'
    if hasattr(result, "answer") and result.answer:
        return str(result.answer).strip()
    # ResponseGraphEntry → use 'text'
    if hasattr(result, "text") and result.text:
        return str(result.text).strip()
    # ResponseGraphContextEntry → use 'content'
    if hasattr(result, "content") and result.content:
        return str(result.content).strip()
    return None


async def store(text: str, dataset: str = "main_dataset") -> None:
    """Ingest text into the knowledge graph (remember)."""
    await cognee.remember(text, dataset_name=dataset)


async def query(question: str, dataset: str | None = None) -> list[str]:
    """Semantic + graph search over memory (recall)."""
    kwargs = {}
    if dataset:
        kwargs["datasets"] = [dataset]
    results = await cognee.recall(query_text=question, **kwargs)

    texts = []
    seen = set()
    for r in results:
        t = _extract_text(r)
        if t and t not in seen:
            seen.add(t)
            texts.append(t)
    return texts


async def enrich(dataset: str = "main_dataset") -> None:
    """Deepen connections in the knowledge graph (improve)."""
    await cognee.improve(dataset=dataset)


async def erase(everything: bool = False, dataset: str | None = None) -> None:
    """Remove memory — all of it or a specific dataset (forget)."""
    if everything:
        await cognee.forget(everything=True)
    elif dataset:
        await cognee.forget(dataset=dataset)
    else:
        await cognee.forget(everything=True)
