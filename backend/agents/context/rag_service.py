"""
RAG Service

The RAG Service manages vector search and storage using Pinecone.
Uses a unified index with namespaces for different knowledge types:
- {squad_id}:code - Code from Git repositories
- {squad_id}:tickets - Jira tickets & resolutions
- {squad_id}:docs - Confluence, Notion, Google Docs
- {squad_id}:conversations - Past agent discussions
- {squad_id}:decisions - Architecture Decision Records

This provides squad-isolated knowledge bases with efficient retrieval.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
import os
import asyncio
from functools import lru_cache

from pinecone import Pinecone, ServerlessSpec
import openai


class RAGService:
    """
    RAG Service - Vector Search with Pinecone

    Responsibilities:
    - Store documents in Pinecone with embeddings
    - Query relevant documents via semantic search
    - Manage namespaces for different knowledge types
    - Handle squad isolation
    - Generate embeddings via OpenAI

    Namespace Strategy:
    - Format: {squad_id}:{knowledge_type}
    - Knowledge types: code, tickets, docs, conversations, decisions
    - Enables squad isolation and efficient filtering
    """

    def __init__(
        self,
        index_name: str = "agent-squad",
        embedding_model: str = "text-embedding-3-small",
        embedding_dimension: int = 1536,
    ):
        """
        Initialize RAG Service

        Args:
            index_name: Pinecone index name
            embedding_model: OpenAI embedding model
            embedding_dimension: Embedding vector dimension
        """
        self.index_name = index_name
        self.embedding_model = embedding_model
        self.embedding_dimension = embedding_dimension

        # Initialize Pinecone
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise ValueError("PINECONE_API_KEY environment variable not set")

        self.pc = Pinecone(api_key=api_key)

        # Initialize OpenAI for embeddings
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        self.openai_client = openai.AsyncOpenAI(api_key=openai_key)

        # Get or create index
        self._ensure_index_exists()
        self.index = self.pc.Index(self.index_name)

    def _ensure_index_exists(self) -> None:
        """Create Pinecone index if it doesn't exist"""
        existing_indexes = [idx.name for idx in self.pc.list_indexes()]

        if self.index_name not in existing_indexes:
            # Create serverless index
            self.pc.create_index(
                name=self.index_name,
                dimension=self.embedding_dimension,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region=os.getenv("PINECONE_REGION", "us-east-1"),
                ),
            )

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using OpenAI.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        response = await self.openai_client.embeddings.create(
            model=self.embedding_model,
            input=text,
        )
        return response.data[0].embedding

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch).

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        # OpenAI supports batching up to 2048 texts
        batch_size = 2048
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = await self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=batch,
            )
            embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(embeddings)

        return all_embeddings

    def _build_namespace(self, squad_id: UUID, namespace: str) -> str:
        """
        Build namespaced key for squad isolation.

        Args:
            squad_id: Squad UUID
            namespace: Namespace type (code, tickets, docs, conversations, decisions)

        Returns:
            Formatted namespace: {squad_id}:{namespace}
        """
        return f"{squad_id}:{namespace}"

    async def upsert(
        self,
        squad_id: UUID,
        namespace: str,
        documents: List[Dict[str, Any]],
    ) -> None:
        """
        Store documents in Pinecone with embeddings.

        Args:
            squad_id: Squad UUID
            namespace: Namespace type (code, tickets, docs, etc.)
            documents: List of documents with format:
                {
                    "id": "unique_id",
                    "text": "document text",
                    "metadata": {"key": "value", ...}
                }
        """
        if not documents:
            return

        # Generate embeddings for all documents
        texts = [doc["text"] for doc in documents]
        embeddings = await self.generate_embeddings(texts)

        # Build vectors for Pinecone
        namespace_key = self._build_namespace(squad_id, namespace)
        vectors = []

        for doc, embedding in zip(documents, embeddings):
            vectors.append({
                "id": doc["id"],
                "values": embedding,
                "metadata": {
                    **doc.get("metadata", {}),
                    "text": doc["text"][:1000],  # Store truncated text in metadata
                    "squad_id": str(squad_id),
                    "namespace_type": namespace,
                },
            })

        # Upsert in batches of 100 (Pinecone limit)
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            self.index.upsert(
                vectors=batch,
                namespace=namespace_key,
            )

    async def query(
        self,
        squad_id: UUID,
        namespace: str,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query relevant documents from Pinecone.

        Args:
            squad_id: Squad UUID
            namespace: Namespace type (code, tickets, docs, etc.)
            query: Query string
            top_k: Number of results to return
            filter_metadata: Optional metadata filters

        Returns:
            List of relevant documents with scores
        """
        # Generate query embedding
        query_embedding = await self.generate_embedding(query)

        # Query Pinecone
        namespace_key = self._build_namespace(squad_id, namespace)

        # Build filter
        filter_dict = filter_metadata or {}
        filter_dict["squad_id"] = str(squad_id)
        filter_dict["namespace_type"] = namespace

        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            namespace=namespace_key,
            filter=filter_dict,
            include_metadata=True,
        )

        # Format results
        documents = []
        for match in results.matches:
            documents.append({
                "id": match.id,
                "score": match.score,
                "text": match.metadata.get("text", ""),
                "metadata": {
                    k: v for k, v in match.metadata.items()
                    if k not in ["text", "squad_id", "namespace_type"]
                },
            })

        return documents

    async def query_multiple_namespaces(
        self,
        squad_id: UUID,
        namespaces: List[str],
        query: str,
        top_k_per_namespace: int = 3,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Query multiple namespaces in parallel.

        Args:
            squad_id: Squad UUID
            namespaces: List of namespace types
            query: Query string
            top_k_per_namespace: Results per namespace

        Returns:
            Dictionary mapping namespace to results
        """
        # Query all namespaces in parallel
        tasks = [
            self.query(
                squad_id=squad_id,
                namespace=ns,
                query=query,
                top_k=top_k_per_namespace,
            )
            for ns in namespaces
        ]

        results = await asyncio.gather(*tasks)

        # Map results to namespaces
        return {
            ns: result
            for ns, result in zip(namespaces, results)
        }

    async def delete(
        self,
        squad_id: UUID,
        namespace: str,
        document_ids: List[str],
    ) -> None:
        """
        Delete documents from Pinecone.

        Args:
            squad_id: Squad UUID
            namespace: Namespace type
            document_ids: List of document IDs to delete
        """
        namespace_key = self._build_namespace(squad_id, namespace)
        self.index.delete(
            ids=document_ids,
            namespace=namespace_key,
        )

    async def delete_namespace(
        self,
        squad_id: UUID,
        namespace: str,
    ) -> None:
        """
        Delete entire namespace (all documents).

        Args:
            squad_id: Squad UUID
            namespace: Namespace type
        """
        namespace_key = self._build_namespace(squad_id, namespace)
        self.index.delete(
            delete_all=True,
            namespace=namespace_key,
        )

    async def get_namespace_stats(
        self,
        squad_id: UUID,
        namespace: str,
    ) -> Dict[str, Any]:
        """
        Get statistics for a namespace.

        Args:
            squad_id: Squad UUID
            namespace: Namespace type

        Returns:
            Statistics (vector count, etc.)
        """
        namespace_key = self._build_namespace(squad_id, namespace)
        stats = self.index.describe_index_stats()

        namespace_stats = stats.namespaces.get(namespace_key, {})

        return {
            "namespace": namespace_key,
            "vector_count": namespace_stats.get("vector_count", 0),
        }

    # Specialized methods for different knowledge types

    async def index_code_file(
        self,
        squad_id: UUID,
        file_path: str,
        content: str,
        repository: str,
        branch: str = "main",
        commit_hash: Optional[str] = None,
    ) -> None:
        """
        Index a code file from a repository.

        Args:
            squad_id: Squad UUID
            file_path: File path in repository
            content: File content
            repository: Repository name
            branch: Branch name
            commit_hash: Optional commit hash
        """
        await self.upsert(
            squad_id=squad_id,
            namespace="code",
            documents=[{
                "id": f"code_{repository}_{file_path}",
                "text": content,
                "metadata": {
                    "file_path": file_path,
                    "repository": repository,
                    "branch": branch,
                    "commit_hash": commit_hash,
                    "indexed_at": asyncio.get_event_loop().time(),
                },
            }],
        )

    async def index_ticket(
        self,
        squad_id: UUID,
        ticket_id: str,
        title: str,
        description: str,
        resolution: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Index a Jira ticket.

        Args:
            squad_id: Squad UUID
            ticket_id: Ticket ID (e.g., PROJ-123)
            title: Ticket title
            description: Ticket description
            resolution: Optional resolution notes
            metadata: Optional metadata (assignee, priority, etc.)
        """
        text = f"{title}\n\n{description}"
        if resolution:
            text += f"\n\nResolution:\n{resolution}"

        await self.upsert(
            squad_id=squad_id,
            namespace="tickets",
            documents=[{
                "id": f"ticket_{ticket_id}",
                "text": text,
                "metadata": {
                    "ticket_id": ticket_id,
                    "title": title,
                    **(metadata or {}),
                },
            }],
        )

    async def index_document(
        self,
        squad_id: UUID,
        document_id: str,
        title: str,
        content: str,
        source: str,  # confluence, notion, google_docs
        url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Index a document from Confluence, Notion, Google Docs, etc.

        Args:
            squad_id: Squad UUID
            document_id: Document ID
            title: Document title
            content: Document content
            source: Source system (confluence, notion, google_docs)
            url: Optional document URL
            metadata: Optional metadata
        """
        text = f"{title}\n\n{content}"

        await self.upsert(
            squad_id=squad_id,
            namespace="docs",
            documents=[{
                "id": f"doc_{source}_{document_id}",
                "text": text,
                "metadata": {
                    "document_id": document_id,
                    "title": title,
                    "source": source,
                    "url": url,
                    **(metadata or {}),
                },
            }],
        )
