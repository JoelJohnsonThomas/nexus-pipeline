"""
Vector embedding generation using sentence-transformers.
Creates embeddings for semantic search and similarity matching.
"""
import os
import logging
from typing import List, Optional
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None
    logging.warning("sentence-transformers not installed. Embeddings will not work.")

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generate vector embeddings for semantic search"""
    
    def __init__(self, model_name: str = None):
        """
        Initialize embedding generator.
        
        Args:
            model_name: Name of sentence-transformers model
                       (default: all-MiniLM-L6-v2, 384 dimensions)
        """
        if SentenceTransformer is None:
            raise ImportError("sentence-transformers package is required for embeddings")
        
        self.model_name = model_name or os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
        
        try:
            self.model = SentenceTransformer(self.model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"Initialized embedding model: {self.model_name} ({self.dimension} dimensions)")
        except Exception as e:
            logger.error(f"Failed to load embedding model {self.model_name}: {e}")
            raise
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding vector for a single text.
        
        Args:
            text: Text to embed
        
        Returns:
            List of floats representing the embedding, or None if failed
        """
        try:
            if not text or not text.strip():
                logger.warning("Empty text provided for embedding")
                return None
            
            # Truncate if too long (model has max sequence length)
            max_chars = 5000  # Safe limit for most models
            if len(text) > max_chars:
                text = text[:max_chars]
                logger.debug(f"Text truncated to {max_chars} characters for embedding")
            
            # Generate embedding
            embedding = self.model.encode(text, convert_to_numpy=True)
            
            # Convert to list
            return embedding.tolist()
        
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts (more efficient than one-by-one).
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of embedding vectors (same order as input)
        """
        try:
            if not texts:
                return []
            
            # Filter out empty texts but track indices
            valid_texts = []
            valid_indices = []
            for i, text in enumerate(texts):
                if text and text.strip():
                    valid_texts.append(text[:5000])  # Truncate
                    valid_indices.append(i)
            
            if not valid_texts:
                logger.warning("No valid texts to embed")
                return [None] * len(texts)
            
            # Generate embeddings in batch
            embeddings = self.model.encode(valid_texts, convert_to_numpy=True, show_progress_bar=False)
            
            # Map back to original order
            result = [None] * len(texts)
            for i, embedding in zip(valid_indices, embeddings):
                result[i] = embedding.tolist()
            
            return result
        
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            return [None] * len(texts)
    
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
        
        Returns:
            Similarity score between -1 and 1 (higher = more similar)
        """
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Cosine similarity
            similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
            return float(similarity)
        
        except Exception as e:
            logger.error(f"Failed to compute similarity: {e}")
            return 0.0
    
    def find_similar(
        self, 
        query_embedding: List[float], 
        candidate_embeddings: List[List[float]], 
        top_k: int = 5
    ) -> List[tuple]:
        """
        Find most similar embeddings to a query.
        
        Args:
            query_embedding: Query embedding vector
            candidate_embeddings: List of candidate embeddings
            top_k: Number of top similar embeddings to return
        
        Returns:
            List of (index, similarity_score) tuples, sorted by similarity (descending)
        """
        try:
            query_vec = np.array(query_embedding)
            candidates = np.array(candidate_embeddings)
            
            # Compute similarities
            similarities = np.dot(candidates, query_vec) / (
                np.linalg.norm(candidates, axis=1) * np.linalg.norm(query_vec)
            )
            
            # Get top k indices
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            
            # Return (index, score) pairs
            return [(int(idx), float(similarities[idx])) for idx in top_indices]
        
        except Exception as e:
            logger.error(f"Failed to find similar embeddings: {e}")
            return []
    
    def get_model_info(self) -> dict:
        """Get information about the embedding model"""
        return {
            'model_name': self.model_name,
            'dimension': self.dimension,
            'max_sequence_length': self.model.max_seq_length if hasattr(self.model, 'max_seq_length') else 'unknown'
        }
