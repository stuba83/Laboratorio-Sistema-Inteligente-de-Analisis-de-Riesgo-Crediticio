#!/usr/bin/env python3
"""
CreditGuard AI Assistant - Azure AI Search Service
Instructor: Steven Uba - Azure Digital Solution Engineer - Data and AI
Version: 1.0.0
Purpose: Azure AI Search integration for vector search and RAG capabilities
"""

import asyncio
import json
import aiohttp
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import logging
from dataclasses import dataclass, asdict

from azure.search.documents.aio import SearchClient
from azure.search.documents.indexes.aio import SearchIndexClient
from azure.search.documents.models import VectorizedQuery
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SemanticConfiguration,
    SemanticSearch,
    SemanticPrioritizedFields,
    SemanticField,
    SearchField,
    SearchFieldDataType
)
from azure.core.credentials import AzureKeyCredential


@dataclass
class SearchConfig:
    """Search service configuration"""
    index_name: str = "creditguard-policies"
    vector_dimensions: int = 1536  # Ada-002 embedding dimensions
    semantic_config_name: str = "creditguard-semantic-config"
    vector_profile_name: str = "creditguard-vector-profile"


class AISearchService:
    """
    Azure AI Search Service for CreditGuard AI Assistant
    
    Provides vector search capabilities for:
    - Policy document retrieval (RAG)
    - Procedure manual search
    - Regulatory compliance lookup
    - Historical decision patterns
    - Semantic search across bank documentation
    """
    
    def __init__(
        self,
        endpoint: str,
        key: str,
        config: Optional[SearchConfig] = None
    ):
        self.endpoint = endpoint
        self.key = key
        self.config = config or SearchConfig()
        self.credential = AzureKeyCredential(key)
        self.logger = logging.getLogger(__name__)
        
        # Initialize clients
        self.search_client = SearchClient(
            endpoint=endpoint,
            index_name=self.config.index_name,
            credential=self.credential
        )
        
        self.index_client = SearchIndexClient(
            endpoint=endpoint,
            credential=self.credential
        )
        
        # Search configuration
        self.default_search_params = {
            'top': 10,
            'include_total_count': True,
            'scoring_profile': None,
            'query_type': 'semantic'
        }
        
        # Index status
        self._index_exists = False
        
        self.logger.info(f"AISearchService initialized for index: {self.config.index_name}")
    
    async def initialize_index(self) -> bool:
        """
        Create or update the search index with proper schema
        
        Returns:
            True if index was created/updated successfully
        """
        try:
            self.logger.info("Initializing search index...")
            
            # Check if index already exists
            try:
                existing_index = await self.index_client.get_index(self.config.index_name)
                self.logger.info(f"Index {self.config.index_name} already exists")
                self._index_exists = True
                return True
            except Exception:
                pass  # Index doesn't exist, will create it
            
            # Create search index
            fields = [
                SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                SearchableField(name="title", type=SearchFieldDataType.String),
                SearchableField(name="content", type=SearchFieldDataType.String),
                SimpleField(name="document_type", type=SearchFieldDataType.String, filterable=True),
                SimpleField(name="category", type=SearchFieldDataType.String, filterable=True),
                SimpleField(name="source", type=SearchFieldDataType.String, filterable=True),
                SimpleField(name="last_updated", type=SearchFieldDataType.DateTimeOffset, filterable=True),
                SimpleField(name="importance_level", type=SearchFieldDataType.Int32, filterable=True, sortable=True),
                SearchableField(name="keywords", type=SearchFieldDataType.Collection(SearchFieldDataType.String)),
                SearchField(
                    name="content_vector",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    searchable=True,
                    vector_search_dimensions=self.config.vector_dimensions,
                    vector_search_profile_name=self.config.vector_profile_name
                )
            ]
            
            # Configure vector search
            vector_search = VectorSearch(
                algorithms=[
                    HnswAlgorithmConfiguration(name="creditguard-hnsw")
                ],
                profiles=[
                    VectorSearchProfile(
                        name=self.config.vector_profile_name,
                        algorithm_configuration_name="creditguard-hnsw"
                    )
                ]
            )
            
            # Configure semantic search
            semantic_search = SemanticSearch(
                configurations=[
                    SemanticConfiguration(
                        name=self.config.semantic_config_name,
                        prioritized_fields=SemanticPrioritizedFields(
                            title_field=SemanticField(field_name="title"),
                            keywords_fields=[SemanticField(field_name="keywords")],
                            content_fields=[SemanticField(field_name="content")]
                        )
                    )
                ]
            )
            
            # Create index
            index = SearchIndex(
                name=self.config.index_name,
                fields=fields,
                vector_search=vector_search,
                semantic_search=semantic_search
            )
            
            result = await self.index_client.create_or_update_index(index)
            self._index_exists = True
            
            self.logger.info(f"Search index created successfully: {result.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing search index: {str(e)}")
            return False
    
    async def upload_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Upload documents to search index
        
        Args:
            documents: List of documents to upload
            
        Returns:
            Upload results summary
        """
        try:
            self.logger.info(f"Uploading {len(documents)} documents to search index...")
            
            if not self._index_exists:
                await self.initialize_index()
            
            # Prepare documents for upload
            prepared_docs = []
            for doc in documents:
                prepared_doc = {
                    'id': doc.get('id', f"doc_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(prepared_docs)}"),
                    'title': doc.get('title', ''),
                    'content': doc.get('content', ''),
                    'document_type': doc.get('document_type', 'policy'),
                    'category': doc.get('category', 'general'),
                    'source': doc.get('source', 'unknown'),
                    'last_updated': doc.get('last_updated', datetime.now().isoformat()),
                    'importance_level': doc.get('importance_level', 5),
                    'keywords': doc.get('keywords', []),
                    'content_vector': doc.get('content_vector', [])
                }
                prepared_docs.append(prepared_doc)
            
            # Upload in batches to avoid size limits
            batch_size = 100
            upload_results = []
            
            for i in range(0, len(prepared_docs), batch_size):
                batch = prepared_docs[i:i + batch_size]
                
                try:
                    result = await self.search_client.upload_documents(documents=batch)
                    upload_results.extend(result)
                    self.logger.info(f"Uploaded batch {i//batch_size + 1}: {len(batch)} documents")
                except Exception as e:
                    self.logger.error(f"Error uploading batch {i//batch_size + 1}: {str(e)}")
                    upload_results.append({'succeeded': False, 'error': str(e)})
            
            # Summarize results
            succeeded = sum(1 for result in upload_results if result.get('succeeded', True))
            failed = len(upload_results) - succeeded
            
            summary = {
                'total_documents': len(documents),
                'succeeded': succeeded,
                'failed': failed,
                'success_rate': succeeded / len(documents) * 100 if documents else 0,
                'upload_timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"Document upload completed: {succeeded}/{len(documents)} successful")
            return summary
            
        except Exception as e:
            self.logger.error(f"Error uploading documents: {str(e)}")
            raise
    
    async def vector_search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filters: str = None,
        min_score: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search
        
        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            filters: OData filter expression
            min_score: Minimum similarity score threshold
            
        Returns:
            List of matching documents with scores
        """
        try:
            self.logger.info(f"Performing vector search with top_k={top_k}")
            
            if not self._index_exists:
                await self.initialize_index()
            
            # Create vector query
            vector_query = VectorizedQuery(
                vector=query_vector,
                k_nearest_neighbors=top_k,
                fields="content_vector"
            )
            
            # Execute search
            results = await self.search_client.search(
                search_text=None,
                vector_queries=[vector_query],
                filter=filters,
                top=top_k,
                include_total_count=True
            )
            
            # Process results
            documents = []
            async for result in results:
                # Apply score threshold
                if result['@search.score'] >= min_score:
                    doc = {
                        'id': result['id'],
                        'title': result['title'],
                        'content': result['content'],
                        'document_type': result['document_type'],
                        'category': result['category'],
                        'source': result['source'],
                        'score': result['@search.score'],
                        'last_updated': result['last_updated']
                    }
                    documents.append(doc)
            
            self.logger.info(f"Vector search returned {len(documents)} results above threshold {min_score}")
            return documents
            
        except Exception as e:
            self.logger.error(f"Error in vector search: {str(e)}")
            raise
    
    async def semantic_search(
        self,
        query_text: str,
        top_k: int = 10,
        filters: str = None
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search using natural language query
        
        Args:
            query_text: Natural language search query
            top_k: Number of results to return
            filters: OData filter expression
            
        Returns:
            List of semantically relevant documents
        """
        try:
            self.logger.info(f"Performing semantic search: {query_text[:50]}...")
            
            if not self._index_exists:
                await self.initialize_index()
            
            # Execute semantic search
            results = await self.search_client.search(
                search_text=query_text,
                query_type="semantic",
                semantic_configuration_name=self.config.semantic_config_name,
                query_caption="extractive",
                query_answer="extractive",
                filter=filters,
                top=top_k,
                include_total_count=True
            )
            
            # Process results
            documents = []
            async for result in results:
                doc = {
                    'id': result['id'],
                    'title': result['title'],
                    'content': result['content'],
                    'document_type': result['document_type'],
                    'category': result['category'],
                    'source': result['source'],
                    'score': result['@search.score'],
                    'last_updated': result['last_updated']
                }
                
                # Add semantic extras if available
                if '@search.captions' in result:
                    doc['captions'] = [
                        {
                            'text': caption['text'],
                            'highlights': caption.get('highlights', '')
                        }
                        for caption in result['@search.captions']
                    ]
                
                if '@search.answers' in result:
                    doc['answers'] = [
                        {
                            'text': answer['text'],
                            'score': answer.get('score', 0)
                        }
                        for answer in result['@search.answers']
                    ]
                
                documents.append(doc)
            
            self.logger.info(f"Semantic search returned {len(documents)} results")
            return documents
            
        except Exception as e:
            self.logger.error(f"Error in semantic search: {str(e)}")
            raise
    
    async def hybrid_search(
        self,
        query_text: str,
        query_vector: List[float],
        top_k: int = 10,
        filters: str = None,
        alpha: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining vector and text search
        
        Args:
            query_text: Text query for keyword search
            query_vector: Vector for similarity search
            top_k: Number of results to return
            filters: OData filter expression
            alpha: Weighting between vector (0) and text (1) search
            
        Returns:
            List of hybrid search results
        """
        try:
            self.logger.info(f"Performing hybrid search: {query_text[:50]}...")
            
            if not self._index_exists:
                await self.initialize_index()
            
            # Create vector query
            vector_query = VectorizedQuery(
                vector=query_vector,
                k_nearest_neighbors=top_k,
                fields="content_vector"
            )
            
            # Execute hybrid search
            results = await self.search_client.search(
                search_text=query_text,
                vector_queries=[vector_query],
                query_type="semantic",
                semantic_configuration_name=self.config.semantic_config_name,
                filter=filters,
                top=top_k,
                include_total_count=True
            )
            
            # Process and rank results
            documents = []
            async for result in results:
                doc = {
                    'id': result['id'],
                    'title': result['title'],
                    'content': result['content'],
                    'document_type': result['document_type'],
                    'category': result['category'],
                    'source': result['source'],
                    'score': result['@search.score'],
                    'last_updated': result['last_updated']
                }
                documents.append(doc)
            
            # Re-rank based on alpha weighting (simplified approach)
            # In production, you might use a more sophisticated ranking algorithm
            for doc in documents:
                # This is a simplified re-ranking - in practice you'd need
                # separate vector and text scores to properly apply alpha
                doc['hybrid_score'] = doc['score']  # Placeholder
            
            # Sort by hybrid score
            documents.sort(key=lambda x: x['hybrid_score'], reverse=True)
            
            self.logger.info(f"Hybrid search returned {len(documents)} results")
            return documents
            
        except Exception as e:
            self.logger.error(f"Error in hybrid search: {str(e)}")
            raise
    
    async def search_by_category(
        self,
        category: str,
        query_text: str = None,
        top_k: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search documents within a specific category
        
        Args:
            category: Document category to search
            query_text: Optional text query
            top_k: Number of results to return
            
        Returns:
            List of documents in the specified category
        """
        try:
            self.logger.info(f"Searching category '{category}' with query: {query_text or 'None'}")
            
            # Build filter
            filter_expr = f"category eq '{category}'"
            
            if query_text:
                # Use semantic search with category filter
                results = await self.semantic_search(
                    query_text=query_text,
                    top_k=top_k,
                    filters=filter_expr
                )
            else:
                # Get all documents in category, sorted by importance
                results = await self.search_client.search(
                    search_text="*",
                    filter=filter_expr,
                    order_by="importance_level desc",
                    top=top_k
                )
                
                documents = []
                async for result in results:
                    doc = {
                        'id': result['id'],
                        'title': result['title'],
                        'content': result['content'],
                        'document_type': result['document_type'],
                        'category': result['category'],
                        'source': result['source'],
                        'importance_level': result['importance_level'],
                        'last_updated': result['last_updated']
                    }
                    documents.append(doc)
                
                results = documents
            
            self.logger.info(f"Category search returned {len(results)} results")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in category search: {str(e)}")
            raise
    
    async def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific document by ID
        
        Args:
            doc_id: Document identifier
            
        Returns:
            Document data or None if not found
        """
        try:
            self.logger.info(f"Retrieving document: {doc_id}")
            
            document = await self.search_client.get_document(key=doc_id)
            
            if document:
                # Remove vector field for cleaner response
                doc_copy = dict(document)
                doc_copy.pop('content_vector', None)
                return doc_copy
            
            return None
            
        except Exception as e:
            if "not found" in str(e).lower():
                self.logger.info(f"Document not found: {doc_id}")
                return None
            else:
                self.logger.error(f"Error retrieving document: {str(e)}")
                raise
    
    async def delete_documents(self, document_ids: List[str]) -> Dict[str, Any]:
        """
        Delete documents from the search index
        
        Args:
            document_ids: List of document IDs to delete
            
        Returns:
            Deletion results summary
        """
        try:
            self.logger.info(f"Deleting {len(document_ids)} documents from index")
            
            # Prepare documents for deletion
            documents_to_delete = [{"id": doc_id} for doc_id in document_ids]
            
            # Execute deletion
            results = await self.search_client.delete_documents(documents=documents_to_delete)
            
            # Summarize results
            succeeded = sum(1 for result in results if result.succeeded)
            failed = len(results) - succeeded
            
            summary = {
                'total_requested': len(document_ids),
                'succeeded': succeeded,
                'failed': failed,
                'success_rate': succeeded / len(document_ids) * 100 if document_ids else 0,
                'deletion_timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"Document deletion completed: {succeeded}/{len(document_ids)} successful")
            return summary
            
        except Exception as e:
            self.logger.error(f"Error deleting documents: {str(e)}")
            raise
    
    async def get_index_statistics(self) -> Dict[str, Any]:
        """
        Get search index statistics and health metrics
        
        Returns:
            Index statistics and metrics
        """
        try:
            self.logger.info("Retrieving index statistics")
            
            # Get index definition
            index = await self.index_client.get_index(self.config.index_name)
            
            # Get document count (approximation via search)
            count_results = await self.search_client.search(
                search_text="*",
                include_total_count=True,
                top=0
            )
            
            document_count = 0
            async for _ in count_results:
                pass  # Just iterate to get the count
            
            # Get statistics by category
            category_stats = await self._get_category_statistics()
            
            statistics = {
                'index_name': self.config.index_name,
                'total_documents': getattr(count_results, 'get_count', lambda: 0)(),
                'last_updated': datetime.now().isoformat(),
                'vector_dimensions': self.config.vector_dimensions,
                'field_count': len(index.fields),
                'category_breakdown': category_stats,
                'index_size_estimate': 'Available via Azure Portal'
            }
            
            return statistics
            
        except Exception as e:
            self.logger.error(f"Error getting index statistics: {str(e)}")
            raise
    
    async def _get_category_statistics(self) -> Dict[str, int]:
        """Get document count by category"""
        
        try:
            # Get unique categories
            categories = ['credit_policies', 'procedures', 'compliance', 'products', 'general']
            category_stats = {}
            
            for category in categories:
                # Count documents in each category
                results = await self.search_client.search(
                    search_text="*",
                    filter=f"category eq '{category}'",
                    include_total_count=True,
                    top=0
                )
                
                count = 0
                async for _ in results:
                    count += 1
                
                category_stats[category] = count
            
            return category_stats
            
        except Exception as e:
            self.logger.warning(f"Error getting category statistics: {str(e)}")
            return {}
    
    async def suggest_similar_documents(
        self,
        document_id: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find documents similar to the specified document
        
        Args:
            document_id: Reference document ID
            top_k: Number of similar documents to return
            
        Returns:
            List of similar documents
        """
        try:
            self.logger.info(f"Finding documents similar to: {document_id}")
            
            # Get the reference document
            reference_doc = await self.get_document_by_id(document_id)
            if not reference_doc:
                return []
            
            # Use its vector for similarity search (if available)
            # This would require getting the vector from the document
            # For now, we'll use category and content-based search
            
            similar_docs = await self.search_by_category(
                category=reference_doc.get('category', 'general'),
                query_text=reference_doc.get('title', ''),
                top_k=top_k + 1  # +1 to exclude the original document
            )
            
            # Remove the reference document from results
            similar_docs = [doc for doc in similar_docs if doc['id'] != document_id][:top_k]
            
            self.logger.info(f"Found {len(similar_docs)} similar documents")
            return similar_docs
            
        except Exception as e:
            self.logger.error(f"Error finding similar documents: {str(e)}")
            raise
    
    async def close(self):
        """Close search service connections"""
        
        try:
            if self.search_client:
                await self.search_client.close()
            
            if self.index_client:
                await self.index_client.close()
            
            self.logger.info("AI Search service connections closed")
            
        except Exception as e:
            self.logger.error(f"Error closing search connections: {str(e)}")
    
    def __str__(self):
        return f"AISearchService(index={self.config.index_name}, dimensions={self.config.vector_dimensions}, initialized={self._index_exists})"