{%- if cookiecutter.enable_rag %}
from abc import ABC, abstractmethod
from app.rag.models import SearchResult
from app.rag.vectorstore import BaseVectorStore
from app.rag.config import RAGSettings

class BaseRetrievalService(ABC):
    """Abstract base class for retrieval service implementations.
    
    Defines the interface for querying the vector store and retrieving
    relevant document chunks based on a query.
    """
    
    @abstractmethod
    async def retrieve(
        self, 
        query: str, 
        collection_name: str,
        limit: int = 5,
        min_score: float = 0.0,
        filter: str = ""
    ) -> list[SearchResult]:
        """Execute the retrieval pipeline to find relevant chunks.
        
        Args:
            query: The search query text.
            collection_name: Name of the collection to search in.
            limit: Maximum number of results to return.
            min_score: Minimum similarity score threshold (0.0 to 1.0).
            filter: Optional filter expression for the search.
            
        Returns:
            List of SearchResult objects sorted by relevance.
        """
        pass

    @abstractmethod
    async def retrieve_by_document(
        self, 
        query: str, 
        collection_name: str, 
        document_id: str,
        limit: int = 3
    ) -> list[SearchResult]:
        """Specialized retrieval restricted to a single document.
        
        Useful for "Chat with this PDF" functionality where results
        should only come from a specific document.
        
        Args:
            query: The search query text.
            collection_name: Name of the collection to search in.
            document_id: ID of the document to restrict search to.
            limit: Maximum number of results to return.
            
        Returns:
            List of SearchResult objects from the specified document.
        """
        pass

{%- if cookiecutter.use_milvus %}
class MilvusRetrievalService(BaseRetrievalService):
    """High-level service for query processing and multi-stage retrieval using Milvus.
    
    Handles query execution against the Milvus vector store, including
    vector search, score filtering, and post-processing.
    """

    def __init__(self, vector_store: BaseVectorStore, settings: RAGSettings):
        """Initialize the Milvus retrieval service.
        
        Args:
            vector_store: The vector store to query.
            settings: RAG configuration settings.
        """
        self.store = vector_store
        self.settings = settings

    async def retrieve(
        self, 
        query: str, 
        collection_name: str,
        limit: int = 5,
        min_score: float = 0.0,
        filter: str = ""
    ) -> list[SearchResult]:
        """Execute the retrieval pipeline: Vector Search + Threshold Filtering.
        
        Args:
            query: The search query text.
            collection_name: Name of the collection to search in.
            limit: Maximum number of results to return.
            min_score: Minimum similarity score threshold (0.0 to 1.0).
            filter: Optional filter expression for the search.
            
        Returns:
            List of SearchResult objects sorted by relevance.
        """
        # Execute Search via the Vector Store
        raw_results = await self.store.search(
            collection_name=collection_name,
            query=query,
            filter=filter,
            limit=limit * 2 # Retrieve more for post-filtering
        )

        # Post-processing: Filter by score and limit
        # Cosine similarity is higher = better.
        filtered_results = [
            res for res in raw_results 
            if res.score >= min_score
        ]

        # Apply final limit
        return filtered_results[:limit]

    async def retrieve_by_document(
        self, 
        query: str, 
        collection_name: str, 
        document_id: str,
        limit: int = 3
    ) -> list[SearchResult]:
        """Specialized retrieval restricted to a single document.
        
        Useful for "Chat with this PDF" functionality where results
        should only come from a specific document.
        
        Args:
            query: The search query text.
            collection_name: Name of the collection to search in.
            document_id: ID of the document to restrict search to.
            limit: Maximum number of results to return.
            
        Returns:
            List of SearchResult objects from the specified document.
        """
        filter = f'parent_doc_id == "{document_id}"'
        return await self.retrieve(
            query=query, 
            collection_name=collection_name, 
            limit=limit, 
            filter=filter
        )

{%- endif %}
{%- endif %}