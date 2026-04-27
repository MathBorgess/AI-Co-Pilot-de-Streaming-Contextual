"""RAG Engine using ChromaDB for vector storage and retrieval."""
import os
import uuid
import hashlib
import math
from typing import List, Optional

try:
    import chromadb
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False


def _simple_embedding(text: str, dim: int = 64) -> List[float]:
    """
    Hash-based embedding that works without network access.
    Produces a deterministic fixed-length vector from text.
    """
    words = text.lower().split()
    vec = [0.0] * dim
    for word in words:
        h = int(hashlib.md5(word.encode()).hexdigest(), 16)
        idx = h % dim
        vec[idx] += 1.0
    # L2 normalize
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


class RAGEngine:
    """Retrieval-Augmented Generation engine using ChromaDB."""

    def __init__(self, collection_name: str = None, persist_directory: str = "./chroma_db"):
        # Use a unique name per instance when no name provided to ensure isolation
        self.collection_name = collection_name or f"rag_{uuid.uuid4().hex[:12]}"
        self.persist_directory = persist_directory
        self.client = None
        self.collection = None
        self._chunks_in_memory: List[str] = []  # Fallback when ChromaDB unavailable
        self._initialized = False

    def initialize(self):
        """Initialize ChromaDB client and collection."""
        if self._initialized:
            return

        if not CHROMA_AVAILABLE:
            print("[RAG] ChromaDB not available, using in-memory fallback")
            self._initialized = True
            return

        try:
            # EphemeralClient is the in-memory client (works with ChromaDB 0.4+ and 1.x)
            if hasattr(chromadb, 'EphemeralClient'):
                self.client = chromadb.EphemeralClient()
            else:
                self.client = chromadb.Client()
            # Use cosine space; embeddings are provided manually so no model download needed
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            self._initialized = True
            print(f"[RAG] ChromaDB collection '{self.collection_name}' initialized")
        except Exception as e:
            print(f"[RAG] ChromaDB error: {e}, using in-memory fallback")
            self._initialized = True

    def add_chunk(self, chunk: str, metadata: Optional[dict] = None) -> str:
        """Add a text chunk to the vector store."""
        self.initialize()
        chunk_id = str(uuid.uuid4())

        if self.collection is not None:
            try:
                # ChromaDB 1.x requires non-empty metadata dicts
                actual_metadata = metadata if metadata else {"source": "stream"}
                embedding = _simple_embedding(chunk)
                self.collection.add(
                    documents=[chunk],
                    embeddings=[embedding],
                    metadatas=[actual_metadata],
                    ids=[chunk_id]
                )
            except Exception as e:
                print(f"[RAG] Error adding to ChromaDB: {e}")
                self._chunks_in_memory.append(chunk)
        else:
            self._chunks_in_memory.append(chunk)

        return chunk_id

    def retrieve(self, query: str, n_results: int = 3) -> List[str]:
        """Retrieve relevant chunks for a query."""
        self.initialize()

        if self.collection is not None:
            try:
                count = self.collection.count()
                if count == 0:
                    return []
                actual_n = min(n_results, count)
                query_embedding = _simple_embedding(query)
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=actual_n
                )
                return results["documents"][0] if results["documents"] else []
            except Exception as e:
                print(f"[RAG] Error querying ChromaDB: {e}")
                return self._chunks_in_memory[-n_results:]

        return self._chunks_in_memory[-n_results:]

    def get_all_chunks(self) -> List[str]:
        """Get all stored chunks."""
        self.initialize()

        if self.collection is not None:
            try:
                results = self.collection.get()
                return results["documents"] if results["documents"] else []
            except Exception as e:
                print(f"[RAG] Error getting all chunks: {e}")
                return self._chunks_in_memory

        return self._chunks_in_memory.copy()

    def clear(self):
        """Clear all stored chunks."""
        self._chunks_in_memory.clear()
        if self.client is not None and self.collection is not None:
            try:
                self.client.delete_collection(self.collection_name)
                self.collection = self.client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
            except Exception as e:
                print(f"[RAG] Error clearing collection: {e}")

    def chunk_count(self) -> int:
        """Return the number of stored chunks."""
        if self.collection is not None:
            try:
                return self.collection.count()
            except Exception:
                pass
        return len(self._chunks_in_memory)
