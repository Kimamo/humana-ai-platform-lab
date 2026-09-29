from dataclasses import dataclass

from rag.retriever import search_clinical_guidance


MIN_RELEVANCE_SCORE = 0.40


@dataclass
class RAGContext:
    context: str
    sources: list[str]
    top_score: float | None
    grounded: bool


def retrieve_context(
    question: str,
    k: int = 3,
) -> RAGContext:

    results = search_clinical_guidance(
        question,
        k=k,
    )

    if not results:
        return RAGContext(
            context="",
            sources=[],
            top_score=None,
            grounded=False,
        )

    top_score = results[0]["score"]

    if top_score < MIN_RELEVANCE_SCORE:
        return RAGContext(
            context="",
            sources=[],
            top_score=top_score,
            grounded=False,
        )

    context_parts = []
    sources = []

    for result in results:
        # Don't pass weak chunks to the model just because
        # another chunk happened to pass the threshold.
        if result["score"] < MIN_RELEVANCE_SCORE:
            continue

        context_parts.append(result["content"])

        source = result.get("source")

        if source and source not in sources:
            sources.append(source)

    return RAGContext(
        context="\n\n".join(context_parts),
        sources=sources,
        top_score=top_score,
        grounded=True,
    )