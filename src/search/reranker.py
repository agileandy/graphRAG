"""
Reranker module for improving search results.

This module provides functionality to rerank search results using a cross-encoder model.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple

from src.llm.llm_provider import LLMProvider, create_llm_provider

logger = logging.getLogger(__name__)

class Reranker:
    """
    Reranker for improving search results using a cross-encoder model.
    """
    def __init__(self, llm_provider: Optional[LLMProvider] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize reranker.
        
        Args:
            llm_provider: LLM provider for reranking
            config: Configuration dictionary
        """
        if llm_provider:
            self.provider = llm_provider
        elif config:
            self.provider = create_llm_provider(config)
        else:
            # Load default configuration
            from src.utils.config import load_config
            config = load_config()
            reranker_config = config.get("reranker_provider", {})
            self.provider = create_llm_provider(reranker_config)
    
    def rerank(self, 
              query: str, 
              documents: List[Dict[str, Any]], 
              top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Rerank documents based on relevance to query.
        
        Args:
            query: Query text
            documents: List of documents with text and metadata
            top_k: Number of top results to return
            
        Returns:
            Reranked documents
        """
        if not documents:
            return []
        
        # Extract document texts
        doc_texts = [doc.get("text", "") for doc in documents]
        
        # Create query-document pairs for scoring
        pairs = [(query, text) for text in doc_texts]
        
        # Get scores for each pair
        scores = self._get_scores(pairs)
        
        # Combine documents with scores
        scored_docs = []
        for i, doc in enumerate(documents):
            if i < len(scores):
                scored_doc = doc.copy()
                scored_doc["score"] = scores[i]
                scored_docs.append(scored_doc)
        
        # Sort by score in descending order
        scored_docs.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        # Return top_k results
        return scored_docs[:top_k]
    
    def _get_scores(self, pairs: List[Tuple[str, str]]) -> List[float]:
        """
        Get relevance scores for query-document pairs.
        
        Args:
            pairs: List of (query, document) pairs
            
        Returns:
            List of relevance scores
        """
        # For Ollama models, we need to format the input for the reranker
        formatted_texts = []
        for query, doc in pairs:
            # Format for cross-encoder models
            formatted_text = f"Query: {query}\nDocument: {doc}"
            formatted_texts.append(formatted_text)
        
        try:
            # Use the provider to get embeddings
            # For cross-encoder models, this should return a single score per pair
            # For bi-encoder models, we would need to compute cosine similarity
            embeddings = self.provider.get_embeddings(formatted_texts)
            
            # Extract scores (for cross-encoder models)
            # If the model returns a vector, we take the first element as the score
            scores = []
            for emb in embeddings:
                if isinstance(emb, list) and len(emb) > 0:
                    # If it's a vector, take the first element as the score
                    scores.append(emb[0])
                elif isinstance(emb, (int, float)):
                    # If it's already a scalar, use it directly
                    scores.append(float(emb))
                else:
                    # Fallback
                    scores.append(0.0)
            
            return scores
            
        except Exception as e:
            logger.error(f"Error getting scores from reranker: {e}")
            # Return default scores (all zeros)
            return [0.0] * len(pairs)
