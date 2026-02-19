"""
Client for the external Cerebro Reranker service (FastAPI + Rust).
Implements a sidecar pattern with local fallback.
"""

import logging
import os
import time
from typing import List, Tuple, Optional, Any

import requests

from .rerank import CrossEncoderReranker, get_reranker as get_local_reranker

logger = logging.getLogger(__name__)


class CerebroRerankerClient:
    """
    Client for the external Cerebro Reranker service.
    
    Falls back to local CrossEncoderReranker if the service is unreachable
    or returns an error.
    """

    def __init__(
        self,
        service_url: Optional[str] = None,
        timeout: float = 1.0,
        mode: str = "service",  # 'service', 'local', 'hybrid'
    ):
        """
        Initialize the reranker client.

        Args:
            service_url: URL of the reranker service (default: env CEREBRO_RERANKER_URL or localhost:8000)
            timeout: Request timeout in seconds (default: 1.0s)
            mode: Operation mode.
                  - 'service': Prefer service, fallback to local on error.
                  - 'local': Force local usage (legacy).
                  - 'hybrid': (Reserved for future complex logic).
        """
        self.service_url = service_url or os.getenv(
            "CEREBRO_RERANKER_URL", "http://localhost:8000"
        )
        self.timeout = timeout
        self.mode = mode or os.getenv("CEREBRO_RERANKER_MODE", "service")
        
        # Lazy initialization of local fallback
        self._local_reranker: Optional[CrossEncoderReranker] = None

    @property
    def local_reranker(self) -> CrossEncoderReranker:
        """Get or initialize the local fallback reranker."""
        if self._local_reranker is None:
            logger.info("Initializing local fallback reranker...")
            self._local_reranker = get_local_reranker()
        return self._local_reranker

    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: Optional[int] = None,
    ) -> List[Tuple[int, float, str]]:
        """
        Rerank documents using the service or fallback.

        Returns:
            List of (original_index, score, document_text)
        """
        if not documents:
            return []

        # If forced local mode
        if self.mode == "local":
            return self.local_reranker.rerank(query, documents, top_k=top_k)

        try:
            return self._call_service(query, documents, top_k)
        except (requests.RequestException, ValueError) as e:
            logger.warning(
                "Reranker service unavailable or failed (%s). Falling back to local model.",
                str(e)
            )
            # Circuit breaker could be implemented here (e.g., disable service for X seconds)
            return self.local_reranker.rerank(query, documents, top_k=top_k)

    def _call_service(
        self,
        query: str,
        documents: List[str],
        top_k: Optional[int] = None,
    ) -> List[Tuple[int, float, str]]:
        """
        Call the external FastAPI service.
        Expects endpoint POST /rerank
        Payload: { "query": str, "documents": [str], "top_k": int }
        Response: { "results": [ { "index": int, "score": float, "document": str } ] }
        """
        url = f"{self.service_url}/rerank"
        payload = {
            "query": query,
            "documents": documents,
            "top_k": top_k
        }
        
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        duration = time.time() - start_time
        
        data = response.json()
        results = data.get("results", [])
        
        logger.debug("Reranked %d docs via service in %.4fs", len(documents), duration)
        
        # Convert to expected tuple format: (index, score, document)
        # The service should return this structure, but we validate/transform just in case
        formatted_results = []
        for res in results:
            formatted_results.append((
                res["index"],
                res["score"],
                res.get("document", documents[res["index"]]) # Fallback to looking up doc if not returned
            ))
            
        return formatted_results
