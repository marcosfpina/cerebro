"""
VectorStoreProvider Interface

Defines the abstract base class for Vector Store providers.
Implementations should handle:
- Storing and retrieving vectors
- Similarity search
- Document management
"""

from abc import ABC, abstractmethod
from typing import Any


class VectorStoreProvider(ABC):
    """
    Abstract base class for Vector Store providers.
    
    Implementations must provide methods for:
    - Adding documents with embeddings
    - Searching for similar documents
    - Deleting documents
    - Health checks
    """

    @abstractmethod
    def add_documents(
        self,
        documents: list[dict[str, Any]],
        embeddings: list[list[float]],
        **kwargs
    ) -> int:
        """
        Add documents with their embeddings to the vector store.
        
        Args:
            documents: List of document dictionaries with metadata
            embeddings: List of embedding vectors corresponding to documents
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Number of documents successfully added
        """

    @abstractmethod
    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        **kwargs
    ) -> list[dict[str, Any]]:
        """
        Search for documents similar to the query embedding.
        
        Args:
            query_embedding: The query embedding vector
            top_k: Number of top results to return
            **kwargs: Additional provider-specific parameters
            
        Returns:
            List of documents with similarity scores, sorted by relevance
        """

    @abstractmethod
    def delete_documents(self, document_ids: list[str]) -> int:
        """
        Delete documents from the vector store.
        
        Args:
            document_ids: List of document IDs to delete
            
        Returns:
            Number of documents successfully deleted
        """

    @abstractmethod
    def clear(self) -> None:
        """
        Clear all documents from the vector store.
        """

    @abstractmethod
    def get_document_count(self) -> int:
        """
        Get the total number of documents in the vector store.
        
        Returns:
            Number of documents
        """

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if the vector store is healthy and accessible.
        
        Returns:
            True if healthy, False otherwise
        """
