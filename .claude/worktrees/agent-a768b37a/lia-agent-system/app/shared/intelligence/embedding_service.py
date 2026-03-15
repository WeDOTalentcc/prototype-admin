"""
Embedding service for generating text embeddings.
Uses Gemini text-embedding-004 via Replit AI Integrations.
"""
import logging
import os
from typing import List, Optional

logger = logging.getLogger(__name__)

EMBEDDING_DIMENSION = 768
MAX_BATCH_SIZE = 100


class EmbeddingService:
    """Service for generating text embeddings using available providers."""
    
    def __init__(self):
        self._gemini_client = None
    
    @property
    def gemini_client(self):
        """Get Gemini client via Replit AI Integration."""
        if not self._gemini_client:
            from google import genai
            
            api_key = os.environ.get("AI_INTEGRATIONS_GEMINI_API_KEY")
            base_url = os.environ.get("AI_INTEGRATIONS_GEMINI_BASE_URL")
            
            if not api_key or not base_url:
                raise ValueError("AI_INTEGRATIONS_GEMINI_API_KEY or AI_INTEGRATIONS_GEMINI_BASE_URL not configured")
            
            self._gemini_client = genai.Client(
                api_key=api_key,
                http_options={
                    'api_version': '',
                    'base_url': base_url
                }
            )
        
        return self._gemini_client
    
    async def generate_embedding(
        self,
        text: str,
        provider: str = "gemini"
    ) -> List[float]:
        """
        Generate embedding for text.
        
        Args:
            text: The text to embed
            provider: Embedding provider to use ("gemini")
            
        Returns:
            List of floats representing the embedding vector
        """
        if not text or not text.strip():
            return [0.0] * EMBEDDING_DIMENSION
        
        text = text.strip()[:8000]
        
        if provider == "gemini":
            return await self._generate_gemini_embedding(text)
        else:
            raise ValueError(f"Unknown embedding provider: {provider}")
    
    async def _generate_gemini_embedding(self, text: str) -> List[float]:
        """Generate embedding using Gemini text-embedding-004."""
        try:
            client = self.gemini_client
            
            response = client.models.embed_content(
                model="text-embedding-004",
                contents=text
            )
            
            if response and response.embeddings:
                embedding = response.embeddings[0].values
                if len(embedding) != EMBEDDING_DIMENSION:
                    logger.warning(f"Unexpected embedding dimension: {len(embedding)}, expected {EMBEDDING_DIMENSION}")
                return list(embedding)
            
            logger.error("Empty embedding response from Gemini")
            return [0.0] * EMBEDDING_DIMENSION
            
        except Exception as e:
            logger.error(f"Error generating Gemini embedding: {e}")
            raise
    
    async def generate_batch_embeddings(
        self,
        texts: List[str],
        provider: str = "gemini"
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            provider: Embedding provider to use
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        embeddings = []
        
        for i in range(0, len(texts), MAX_BATCH_SIZE):
            batch = texts[i:i + MAX_BATCH_SIZE]
            
            if provider == "gemini":
                batch_embeddings = await self._generate_batch_gemini_embeddings(batch)
            else:
                batch_embeddings = [await self.generate_embedding(t, provider) for t in batch]
            
            embeddings.extend(batch_embeddings)
        
        return embeddings
    
    async def _generate_batch_gemini_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate batch embeddings using Gemini."""
        try:
            client = self.gemini_client
            
            clean_texts = [t.strip()[:8000] if t and t.strip() else "" for t in texts]
            
            results = []
            for text in clean_texts:
                if not text:
                    results.append([0.0] * EMBEDDING_DIMENSION)
                    continue
                
                response = client.models.embed_content(
                    model="text-embedding-004",
                    contents=text
                )
                
                if response and response.embeddings:
                    results.append(list(response.embeddings[0].values))
                else:
                    results.append([0.0] * EMBEDDING_DIMENSION)
            
            return results
            
        except Exception as e:
            logger.error(f"Error generating batch Gemini embeddings: {e}")
            raise
    
    def chunk_text(
        self,
        text: str,
        chunk_size: int = 1000,
        overlap: int = 100
    ) -> List[str]:
        """
        Split text into overlapping chunks for embedding.
        
        Args:
            text: The text to chunk
            chunk_size: Maximum characters per chunk
            overlap: Number of characters to overlap between chunks
            
        Returns:
            List of text chunks
        """
        if not text or len(text) <= chunk_size:
            return [text] if text else []
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            if end < len(text):
                last_period = text.rfind('.', start, end)
                last_newline = text.rfind('\n', start, end)
                break_point = max(last_period, last_newline)
                
                if break_point > start + chunk_size // 2:
                    end = break_point + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
        
        return chunks


embedding_service = EmbeddingService()
