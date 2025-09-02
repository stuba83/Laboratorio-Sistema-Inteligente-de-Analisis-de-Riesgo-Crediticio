#!/usr/bin/env python3
"""
CreditGuard AI Assistant - Embeddings Service
Instructor: Steven Uba - Azure Digital Solution Engineer - Data and AI
Version: 1.0.0
Purpose: Text embeddings and RAG context retrieval using Azure OpenAI
"""

import asyncio
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
import logging
from dataclasses import dataclass, asdict
import hashlib

from openai import AsyncAzureOpenAI
from .ai_search_service import AISearchService


@dataclass
class EmbeddingRequest:
    """Embedding request structure"""
    text: str
    request_id: str
    timestamp: str
    metadata: Dict[str, Any] = None


@dataclass
class EmbeddingResult:
    """Embedding result structure"""
    request_id: str
    text: str
    embedding: List[float]
    token_count: int
    model_used: str
    processing_time: float
    timestamp: str


@dataclass
class ContextDocument:
    """Context document for RAG"""
    id: str
    title: str
    content: str
    source: str
    category: str
    similarity_score: float
    metadata: Dict[str, Any]


class EmbeddingsService:
    """
    Embeddings Service for CreditGuard AI Assistant
    
    Provides text embedding capabilities for:
    - Document vectorization for search
    - Query embeddings for retrieval
    - Semantic similarity calculations
    - RAG context preparation
    - Embedding caching and optimization
    """
    
    def __init__(
        self,
        azure_openai_endpoint: str,
        azure_openai_key: str,
        embeddings_deployment: str,
        ai_search_service: Optional[AISearchService] = None,
        cache_embeddings: bool = True,
        max_tokens_per_request: int = 8000
    ):
        self.azure_openai_endpoint = azure_openai_endpoint
        self.azure_openai_key = azure_openai_key
        self.embeddings_deployment = embeddings_deployment
        self.ai_search_service = ai_search_service
        self.cache_embeddings = cache_embeddings
        self.max_tokens_per_request = max_tokens_per_request
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize Azure OpenAI client
        self.openai_client = AsyncAzureOpenAI(
            api_key=azure_openai_key,
            api_version="2024-02-15-preview",
            azure_endpoint=azure_openai_endpoint
        )
        
        # Embedding cache
        self._embedding_cache = {} if cache_embeddings else None
        
        # Rate limiting
        self._rate_limit_delay = 0.1  # seconds between requests
        self._last_request_time = 0
        
        # Statistics
        self._stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'total_tokens_processed': 0,
            'average_processing_time': 0,
            'errors': 0
        }
        
        self.logger.info(f"EmbeddingsService initialized with deployment: {embeddings_deployment}")
    
    async def get_embedding(
        self,
        text: str,
        request_id: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ) -> EmbeddingResult:
        """
        Get embedding for a single text
        
        Args:
            text: Text to embed
            request_id: Optional request identifier
            metadata: Optional metadata for the request
            
        Returns:
            EmbeddingResult with vector and metadata
        """
        if not request_id:
            request_id = self._generate_request_id(text)
        
        self.logger.info(f"Getting embedding for text: {text[:50]}...")
        
        try:
            start_time = datetime.now()
            
            # Check cache first
            if self._embedding_cache:
                cache_key = self._generate_cache_key(text)
                if cache_key in self._embedding_cache:
                    self._stats['cache_hits'] += 1
                    self.logger.info(f"Cache hit for request: {request_id}")
                    
                    cached_result = self._embedding_cache[cache_key]
                    return EmbeddingResult(
                        request_id=request_id,
                        text=text,
                        embedding=cached_result['embedding'],
                        token_count=cached_result['token_count'],
                        model_used=cached_result['model_used'],
                        processing_time=0.001,  # Cache retrieval time
                        timestamp=datetime.now().isoformat()
                    )
            
            # Rate limiting
            await self._apply_rate_limit()
            
            # Get embedding from Azure OpenAI
            response = await self.openai_client.embeddings.create(
                input=text,
                model=self.embeddings_deployment
            )
            
            # Extract embedding data
            embedding_data = response.data[0]
            embedding_vector = embedding_data.embedding
            token_count = response.usage.total_tokens
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Cache the result
            if self._embedding_cache:
                cache_key = self._generate_cache_key(text)
                self._embedding_cache[cache_key] = {
                    'embedding': embedding_vector,
                    'token_count': token_count,
                    'model_used': self.embeddings_deployment,
                    'timestamp': datetime.now().isoformat()
                }
                self._stats['cache_misses'] += 1
            
            # Update statistics
            self._update_stats(token_count, processing_time)
            
            result = EmbeddingResult(
                request_id=request_id,
                text=text,
                embedding=embedding_vector,
                token_count=token_count,
                model_used=self.embeddings_deployment,
                processing_time=processing_time,
                timestamp=datetime.now().isoformat()
            )
            
            self.logger.info(f"Embedding completed for request: {request_id} ({token_count} tokens, {processing_time:.3f}s)")
            return result
            
        except Exception as e:
            self._stats['errors'] += 1
            self.logger.error(f"Error getting embedding for request {request_id}: {str(e)}")
            raise
    
    async def get_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 16,
        metadata: Dict[str, Any] = None
    ) -> List[EmbeddingResult]:
        """
        Get embeddings for multiple texts in batches
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process per batch
            metadata: Optional metadata for all requests
            
        Returns:
            List of EmbeddingResult objects
        """
        self.logger.info(f"Getting embeddings for {len(texts)} texts in batches of {batch_size}")
        
        try:
            all_results = []
            
            # Process texts in batches
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                batch_start_time = datetime.now()
                
                # Create batch request
                batch_request_id = f"batch_{i//batch_size}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                try:
                    # Rate limiting
                    await self._apply_rate_limit()
                    
                    # Get embeddings for batch
                    response = await self.openai_client.embeddings.create(
                        input=batch,
                        model=self.embeddings_deployment
                    )
                    
                    batch_processing_time = (datetime.now() - batch_start_time).total_seconds()
                    
                    # Process results
                    for j, embedding_data in enumerate(response.data):
                        text = batch[j]
                        request_id = f"{batch_request_id}_item_{j}"
                        
                        result = EmbeddingResult(
                            request_id=request_id,
                            text=text,
                            embedding=embedding_data.embedding,
                            token_count=response.usage.total_tokens // len(batch),  # Approximate
                            model_used=self.embeddings_deployment,
                            processing_time=batch_processing_time / len(batch),
                            timestamp=datetime.now().isoformat()
                        )
                        
                        all_results.append(result)
                        
                        # Cache individual results
                        if self._embedding_cache:
                            cache_key = self._generate_cache_key(text)
                            self._embedding_cache[cache_key] = {
                                'embedding': embedding_data.embedding,
                                'token_count': result.token_count,
                                'model_used': self.embeddings_deployment,
                                'timestamp': datetime.now().isoformat()
                            }
                    
                    # Update statistics
                    self._update_stats(response.usage.total_tokens, batch_processing_time)
                    
                    self.logger.info(f"Batch {i//batch_size + 1} completed: {len(batch)} embeddings in {batch_processing_time:.3f}s")
                    
                except Exception as e:
                    self.logger.error(f"Error processing batch {i//batch_size + 1}: {str(e)}")
                    self._stats['errors'] += 1
                    
                    # Create error results for this batch
                    for j, text in enumerate(batch):
                        error_result = EmbeddingResult(
                            request_id=f"{batch_request_id}_error_{j}",
                            text=text,
                            embedding=[0.0] * 1536,  # Default dimension for Ada-002
                            token_count=0,
                            model_used=self.embeddings_deployment,
                            processing_time=0,
                            timestamp=datetime.now().isoformat()
                        )
                        all_results.append(error_result)
            
            self.logger.info(f"Batch embedding completed: {len(all_results)} total results")
            return all_results
            
        except Exception as e:
            self.logger.error(f"Error in batch embedding: {str(e)}")
            raise
    
    async def get_context_for_query(
        self,
        query: str,
        max_results: int = 5,
        min_similarity: float = 0.7,
        categories: List[str] = None,
        max_context_length: int = 4000
    ) -> List[ContextDocument]:
        """
        Get relevant context documents for a query using RAG
        
        Args:
            query: Search query
            max_results: Maximum number of context documents
            min_similarity: Minimum similarity threshold
            categories: Filter by document categories
            max_context_length: Maximum total context length in tokens
            
        Returns:
            List of relevant context documents
        """
        self.logger.info(f"Getting context for query: {query[:50]}...")
        
        try:
            if not self.ai_search_service:
                self.logger.warning("AI Search service not configured, returning empty context")
                return []
            
            # Get query embedding
            query_embedding = await self.get_embedding(query)
            
            # Build search filters
            filters = None
            if categories:
                category_filter = " or ".join([f"category eq '{cat}'" for cat in categories])
                filters = f"({category_filter})"
            
            # Perform vector search
            search_results = await self.ai_search_service.vector_search(
                query_vector=query_embedding.embedding,
                top_k=max_results * 2,  # Get more results to filter
                filters=filters,
                min_score=min_similarity
            )
            
            # Convert to context documents
            context_docs = []
            total_tokens = 0
            
            for result in search_results:
                # Estimate token count (rough approximation)
                content_tokens = len(result['content'].split()) * 1.3  # Approximate tokens
                
                # Check if adding this document would exceed max context length
                if total_tokens + content_tokens > max_context_length:
                    if not context_docs:  # If this is the first document, truncate it
                        truncated_content = self._truncate_content(
                            result['content'], 
                            max_context_length
                        )
                        content_tokens = len(truncated_content.split()) * 1.3
                        result['content'] = truncated_content
                    else:
                        break  # Stop adding documents
                
                context_doc = ContextDocument(
                    id=result['id'],
                    title=result['title'],
                    content=result['content'],
                    source=result['source'],
                    category=result['category'],
                    similarity_score=result['score'],
                    metadata={
                        'document_type': result.get('document_type', 'unknown'),
                        'last_updated': result.get('last_updated'),
                        'token_count': int(content_tokens)
                    }
                )
                
                context_docs.append(context_doc)
                total_tokens += content_tokens
                
                if len(context_docs) >= max_results:
                    break
            
            self.logger.info(f"Retrieved {len(context_docs)} context documents ({total_tokens:.0f} tokens)")
            return context_docs
            
        except Exception as e:
            self.logger.error(f"Error getting context for query: {str(e)}")
            raise
    
    async def calculate_similarity(
        self,
        text1: str,
        text2: str
    ) -> float:
        """
        Calculate cosine similarity between two texts
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Cosine similarity score (0-1)
        """
        try:
            self.logger.info("Calculating text similarity")
            
            # Get embeddings for both texts
            embedding1 = await self.get_embedding(text1)
            embedding2 = await self.get_embedding(text2)
            
            # Calculate cosine similarity
            similarity = self._cosine_similarity(
                embedding1.embedding,
                embedding2.embedding
            )
            
            self.logger.info(f"Similarity calculated: {similarity:.4f}")
            return similarity
            
        except Exception as e:
            self.logger.error(f"Error calculating similarity: {str(e)}")
            raise
    
    async def find_similar_documents(
        self,
        reference_text: str,
        document_pool: List[str],
        top_k: int = 5,
        min_similarity: float = 0.5
    ) -> List[Tuple[str, float]]:
        """
        Find most similar documents from a pool
        
        Args:
            reference_text: Reference text to compare against
            document_pool: Pool of documents to search
            top_k: Number of most similar documents to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of (document, similarity_score) tuples
        """
        try:
            self.logger.info(f"Finding similar documents from pool of {len(document_pool)}")
            
            # Get reference embedding
            ref_embedding = await self.get_embedding(reference_text)
            
            # Get embeddings for all documents
            doc_embeddings = await self.get_embeddings_batch(document_pool)
            
            # Calculate similarities
            similarities = []
            for i, doc_embedding in enumerate(doc_embeddings):
                if len(doc_embedding.embedding) > 0:  # Valid embedding
                    similarity = self._cosine_similarity(
                        ref_embedding.embedding,
                        doc_embedding.embedding
                    )
                    
                    if similarity >= min_similarity:
                        similarities.append((document_pool[i], similarity))
            
            # Sort by similarity and return top k
            similarities.sort(key=lambda x: x[1], reverse=True)
            result = similarities[:top_k]
            
            self.logger.info(f"Found {len(result)} similar documents above threshold {min_similarity}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error finding similar documents: {str(e)}")
            raise
    
    async def semantic_search_documents(
        self,
        query: str,
        documents: List[Dict[str, str]],
        top_k: int = 10,
        min_similarity: float = 0.6
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search over a collection of documents
        
        Args:
            query: Search query
            documents: List of documents with 'id', 'title', 'content' keys
            top_k: Number of results to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of ranked documents with similarity scores
        """
        try:
            self.logger.info(f"Semantic search over {len(documents)} documents")
            
            # Get query embedding
            query_embedding = await self.get_embedding(query)
            
            # Get embeddings for all documents
            doc_texts = [doc['content'] for doc in documents]
            doc_embeddings = await self.get_embeddings_batch(doc_texts)
            
            # Calculate similarities and rank
            ranked_docs = []
            for i, doc_embedding in enumerate(doc_embeddings):
                if len(doc_embedding.embedding) > 0:  # Valid embedding
                    similarity = self._cosine_similarity(
                        query_embedding.embedding,
                        doc_embedding.embedding
                    )
                    
                    if similarity >= min_similarity:
                        doc_result = {
                            'document': documents[i],
                            'similarity_score': similarity,
                            'embedding_metadata': {
                                'token_count': doc_embedding.token_count,
                                'processing_time': doc_embedding.processing_time
                            }
                        }
                        ranked_docs.append(doc_result)
            
            # Sort by similarity
            ranked_docs.sort(key=lambda x: x['similarity_score'], reverse=True)
            result = ranked_docs[:top_k]
            
            self.logger.info(f"Semantic search returned {len(result)} results")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in semantic search: {str(e)}")
            raise
    
    def _generate_request_id(self, text: str) -> str:
        """Generate unique request ID based on text content"""
        hash_object = hashlib.md5(text.encode())
        return f"req_{hash_object.hexdigest()[:8]}_{datetime.now().strftime('%H%M%S')}"
    
    def _generate_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        return hashlib.sha256(text.encode()).hexdigest()
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        
        # Convert to numpy arrays
        a = np.array(vec1)
        b = np.array(vec2)
        
        # Calculate cosine similarity
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)
    
    def _truncate_content(self, content: str, max_tokens: int) -> str:
        """Truncate content to approximate token limit"""
        
        # Rough approximation: 1 token ≈ 0.75 words
        max_words = int(max_tokens * 0.75)
        words = content.split()
        
        if len(words) <= max_words:
            return content
        
        # Truncate and add ellipsis
        truncated = ' '.join(words[:max_words])
        return truncated + "..."
    
    async def _apply_rate_limit(self):
        """Apply rate limiting between requests"""
        
        current_time = datetime.now().timestamp()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self._rate_limit_delay:
            sleep_time = self._rate_limit_delay - time_since_last
            await asyncio.sleep(sleep_time)
        
        self._last_request_time = datetime.now().timestamp()
    
    def _update_stats(self, token_count: int, processing_time: float):
        """Update service statistics"""
        
        self._stats['total_requests'] += 1
        self._stats['total_tokens_processed'] += token_count
        
        # Update rolling average processing time
        current_avg = self._stats['average_processing_time']
        total_requests = self._stats['total_requests']
        
        self._stats['average_processing_time'] = (
            (current_avg * (total_requests - 1) + processing_time) / total_requests
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get service usage statistics"""
        
        stats = self._stats.copy()
        stats['cache_size'] = len(self._embedding_cache) if self._embedding_cache else 0
        stats['cache_hit_rate'] = (
            self._stats['cache_hits'] / 
            (self._stats['cache_hits'] + self._stats['cache_misses'])
            if (self._stats['cache_hits'] + self._stats['cache_misses']) > 0 
            else 0
        )
        stats['last_updated'] = datetime.now().isoformat()
        
        return stats
    
    def clear_cache(self):
        """Clear the embedding cache"""
        
        if self._embedding_cache:
            cache_size = len(self._embedding_cache)
            self._embedding_cache.clear()
            self.logger.info(f"Embedding cache cleared: {cache_size} entries removed")
    
    async def close(self):
        """Close the embeddings service and cleanup resources"""
        
        try:
            # Clear cache
            if self._embedding_cache:
                self.clear_cache()
            
            # Close OpenAI client
            await self.openai_client.close()
            
            self.logger.info("EmbeddingsService closed")
            
        except Exception as e:
            self.logger.error(f"Error closing EmbeddingsService: {str(e)}")
    
    def __str__(self):
        cache_info = f", cache_size={len(self._embedding_cache)}" if self._embedding_cache else ""
        return f"EmbeddingsService(deployment={self.embeddings_deployment}, requests={self._stats['total_requests']}{cache_info})"