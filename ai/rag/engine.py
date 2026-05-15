"""RAG Engine using ChromaDB for vector storage and retrieval."""
import os
import uuid
import hashlib
import math
import re
from typing import List, Optional

try:
    import chromadb
    CHROMA_AVAILABLE = True
except Exception:
    chromadb = None
    CHROMA_AVAILABLE = False


def _load_chromadb() -> bool:
    """Return whether chromadb should be used.

    This centralizes checks and respects the DISABLE_CHROMA env var.
    It does NOT attempt to import chromadb (that already happened at module import).
    """
    if os.getenv("DISABLE_CHROMA", "false").lower() == "true":
        print("[RAG] DISABLE_CHROMA=true detected — running in-memory semantic context mode")
        return False
    if not CHROMA_AVAILABLE:
        print("[RAG] chromadb package not available — running in-memory semantic context mode")
        return False
    return True


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


_STOPWORDS = {
    "the", "and", "for", "with", "this", "that", "from", "they", "their", "you", "your", "are",
    "was", "were", "have", "has", "had", "but", "not", "will", "just", "into", "over", "when",
    "what", "which", "then", "than", "them", "we", "our", "its", "can", "cannot", "should", "could",
    "uma", "uma", "que", "para", "como", "com", "por", "mais", "menos", "foi", "era", "ser", "nao",
    "sim", "isso", "essa", "este", "esta", "essas", "esses", "nos", "nossa", "nosso", "deles",
}


def _extract_focus_terms(texts: List[str], max_terms: int = 6) -> List[str]:
    """Extract repeated, meaningful keywords from recent chunks."""
    counts = {}
    for text in texts:
        for word in re.findall(r"[a-zA-Z][a-zA-Z\-]{3,}", text.lower()):
            if word in _STOPWORDS:
                continue
            counts[word] = counts.get(word, 0) + 1

    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [word for word, _ in ranked[:max_terms]]


class RAGEngine:
    """Retrieval-Augmented Generation engine using ChromaDB."""

    def __init__(self, collection_name: str = None, persist_directory: str = "./chroma_db"):
        # Use a unique name per instance when no name provided to ensure isolation
        self.collection_name = collection_name or f"rag_{uuid.uuid4().hex[:12]}"
        self.persist_directory = persist_directory
        self.client = None
        self.collection = None
        # Fallback when ChromaDB unavailable
        self._chunks_in_memory: List[str] = []
        # Ordered insertion history for recency boost
        self._recent_chunks: List[str] = []
        # Extracted keywords for reinforcement
        self._focus_terms: List[str] = []
        self._initialized = False

    def initialize(self):
        """Initialize ChromaDB client and collection."""
        if self._initialized:
            return
        # Decide whether to use chromadb based on environment and availability
        if not _load_chromadb():
            # Explicit log printed by _load_chromadb
            self._initialized = True
            return

        try:
            # EphemeralClient is an in-memory client offered by chromadb
            if hasattr(chromadb, 'EphemeralClient'):
                self.client = chromadb.EphemeralClient()
            else:
                # Older/newer chroma builds might expose Client()
                self.client = chromadb.Client()

            # Create or reuse a collection; embeddings supplied manually so set cosine
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            self._initialized = True
            print(f"[RAG] ChromaDB collection '{self.collection_name}' initialized")
        except Exception as e:
            print(f"[RAG] ChromaDB initialization error: {e}. Falling back to in-memory mode.")
            # Ensure we do not leave self.collection in a bad state
            self.client = None
            self.collection = None
            self._initialized = True

    def add_chunk(self, chunk: str, metadata: Optional[dict] = None) -> str:
        """Add a text chunk to the vector store."""
        self.initialize()
        chunk_id = str(uuid.uuid4())

        if self.collection is not None:
            try:
                # ChromaDB 1.x requires non-empty metadata dicts
                actual_metadata = metadata if metadata else {
                    "source": "stream"}
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

        # Track recency order (keep last 8)
        self._recent_chunks.append(chunk)
        if len(self._recent_chunks) > 8:
            self._recent_chunks.pop(0)

        # Update focus terms from recent chunks
        self._focus_terms = _extract_focus_terms(self._recent_chunks)

        return chunk_id

    def retrieve(self, query: str, n_results: int = 3) -> List[str]:
        """
        Retrieve relevant chunks for a query with recency boost.
        The most recently added chunk is always prepended to the result
        so agents always have immediate context, even when similarity
        scores favour older entries.
        """
        self.initialize()

        similarity_results: List[str] = []
        focus_terms = self._focus_terms or _extract_focus_terms(
            self._recent_chunks)
        enhanced_query = query
        if focus_terms:
            enhanced_query = f"{query} {' '.join(focus_terms)}"

        if self.collection is not None:
            try:
                count = self.collection.count()
                if count > 0:
                    actual_n = min(n_results, count)
                    query_embedding = _simple_embedding(enhanced_query)
                    results = self.collection.query(
                        query_embeddings=[query_embedding],
                        n_results=actual_n
                    )
                    similarity_results = results["documents"][0] if results["documents"] else [
                    ]
            except Exception as e:
                print(f"[RAG] Error querying ChromaDB: {e}")
                similarity_results = self._chunks_in_memory[-n_results:]
        else:
            if not self._chunks_in_memory:
                similarity_results = []
            elif focus_terms:
                scored = []
                for idx, chunk in enumerate(self._chunks_in_memory):
                    hits = sum(
                        1 for term in focus_terms if term in chunk.lower())
                    scored.append((hits, idx, chunk))
                scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
                similarity_results = [chunk for hits, _,
                                      chunk in scored if hits > 0][:n_results]
                if len(similarity_results) < n_results:
                    fallback = [
                        chunk for _, _, chunk in scored if chunk not in similarity_results]
                    similarity_results += fallback[: max(
                        0, n_results - len(similarity_results))]
            else:
                similarity_results = self._chunks_in_memory[-n_results:]

        # Recency boost: prepend the most recent chunk when not already included
        recent = self._recent_chunks[-1:] if self._recent_chunks else []
        seen: set = set()
        merged: List[str] = []
        for chunk in recent + similarity_results:
            if chunk not in seen:
                seen.add(chunk)
                merged.append(chunk)

        # allow 1 extra slot for the recency entry
        return merged[:n_results + 1]

    def get_focus_terms(self) -> List[str]:
        """Return the current focus terms derived from recent chunks."""
        return self._focus_terms.copy()

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
        self._recent_chunks.clear()
        self._focus_terms.clear()
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
