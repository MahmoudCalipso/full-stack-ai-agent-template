{%- if cookiecutter.enable_rag %}
"""RAG tool for agent knowledge base search."""

import asyncio
from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.rag.retrieval import BaseRetrievalService


@lru_cache(maxsize=1)
def _get_retrieval_service_cached() -> "BaseRetrievalService":
    """Get cached retrieval service singleton.

    This function uses lru_cache to create a cached singleton of the
    RetrievalService. The cache is initialized on first call and reused
    for subsequent calls.

    Returns:
        Configured BaseRetrievalService instance.
    """
    # Import here to avoid circular imports at module load time
{%- if cookiecutter.use_milvus %}
    from app.rag.retrieval import MilvusRetrievalService
    from app.rag.vectorstore import MilvusVectorStore
{%- else %}
    raise RuntimeError("RAG requires Milvus vector store. Please enable use_milvus.")
{%- endif %}
    from app.rag.embeddings import EmbeddingService
    from app.rag.config import RAGSettings

    settings = RAGSettings()
    embedding_service = EmbeddingService(settings)
    vector_store = MilvusVectorStore(settings, embedding_service)
    return MilvusRetrievalService(vector_store, settings)


def get_retrieval_service() -> "BaseRetrievalService":
    """Get the cached RetrievalService instance.

    This function provides access to a cached RetrievalService singleton.
    It uses lru_cache for proper caching behavior.

    Returns:
        Configured BaseRetrievalService instance.
    """
    return _get_retrieval_service_cached()


async def search_knowledge_base(
    query: str,
    collection: str = "default",
    top_k: int = 5,
) -> str:
    """Search the knowledge base and return formatted results.

    Args:
        query: The search query string.
        collection: Name of the collection to search (default: "default").
        top_k: Number of top results to retrieve (default: 5).

    Returns:
        Formatted string with search results, including content and scores.
        Each result is formatted as:
        "Document [doc_id]: [content] (score: [score])"
    """
    service = get_retrieval_service()

    results = await service.retrieve(
        query=query,
        collection_name=collection,
        limit=top_k,
    )

    if not results:
        return "No relevant documents found in the knowledge base."

    # Format results as a readable string
    formatted_results = []
    for i, result in enumerate(results, start=1):
        doc_info = ""
        if result.metadata.get("filename"):
            doc_info = f" (source: {result.metadata['filename']})"

        formatted_results.append(
            f"[{i}] Score: {result.score:.3f}{doc_info}\n"
            f"Content: {result.content}"
        )

    return "\n\n".join(formatted_results)


def search_knowledge_base_sync(
    query: str,
    collection: str = "default",
    top_k: int = 5,
) -> str:
    """Synchronous wrapper for search_knowledge_base.

    Use this function in CrewAI agents where async tools need to run
    in a synchronous context.

    Args:
        query: The search query string.
        collection: Name of the collection to search (default: "default").
        top_k: Number of top results to retrieve (default: 5).

    Returns:
        Formatted string with search results.
    """
    return asyncio.run(search_knowledge_base(query, collection, top_k))


__all__ = ["search_knowledge_base", "search_knowledge_base_sync"]

{%- else %}
"""RAG tool - not configured."""
{%- endif %}
