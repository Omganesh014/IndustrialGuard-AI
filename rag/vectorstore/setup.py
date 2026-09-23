"""
rag/vectorstore/setup.py

Vector store setup for IndustrialGuard AI RAG pipeline.

Uses ChromaDB in embedded (local disk) mode.
No external server required -- matches the lightweight architecture decision (DECISION-005).

To upgrade to a hosted vector DB later: swap the client initialization here only.
The retrieval interface (rag/retrieval/retriever.py) remains unchanged.
"""

import json
import logging
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

logger = logging.getLogger(__name__)

CHROMA_DIR = Path("rag/vectorstore/chroma_db")
CHUNKS_MANIFEST = Path("rag/vectorstore/chunks_manifest.json")
COLLECTION_NAME = "industrialguard_knowledge"

# Embedding model -- update after confirming IBM watsonx embedding availability
# Default: use a lightweight local model for MVP; swap to IBM embedding at integration
EMBEDDING_MODEL = "all-MiniLM-L6-v2"   # sentence-transformers; swap to IBM embedding model


def get_chroma_client():
    """Initialize ChromaDB client (embedded mode)."""
    try:
        import chromadb
        from chromadb.config import Settings

        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        return client
    except ImportError:
        raise ImportError(
            "chromadb not installed. Run: pip install chromadb"
        )


def get_embedding_function():
    """
    Return embedding function.
    Returns None to use ChromaDB's built-in default embedding (all-MiniLM-L6-v2 via onnx).
    Swap to IBM watsonx embedding when integration is confirmed -- change here only,
    retriever interface stays unchanged.
    """
    # Using ChromaDB default embedding for consistency across setup and retrieval.
    # ChromaDB bundles onnx-based all-MiniLM-L6-v2 -- no external model server required.
    return None


def build_vector_store(force_rebuild: bool = False) -> None:
    """
    Build ChromaDB vector store from chunks manifest.

    Args:
        force_rebuild: if True, drop and recreate the collection.
    """
    if not CHUNKS_MANIFEST.exists():
        raise FileNotFoundError(
            f"Chunks manifest not found: {CHUNKS_MANIFEST}. "
            "Run rag/ingestion/ingest.py first."
        )

    with open(CHUNKS_MANIFEST) as f:
        chunks = json.load(f)

    if not chunks:
        logger.warning("No chunks to index. Check knowledge base documents.")
        return

    client = get_chroma_client()
    embed_fn = get_embedding_function()

    # Drop existing collection if rebuilding
    if force_rebuild:
        try:
            client.delete_collection(COLLECTION_NAME)
            logger.info(f"Dropped existing collection: {COLLECTION_NAME}")
        except Exception:
            pass

    # Create or get collection
    kwargs = {"name": COLLECTION_NAME}
    if embed_fn:
        kwargs["embedding_function"] = embed_fn
    collection = client.get_or_create_collection(**kwargs)

    # Batch upsert
    batch_size = 100
    total = 0
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        collection.upsert(
            ids=[c["chunk_id"] for c in batch],
            documents=[c["content"] for c in batch],
            metadatas=[
                {
                    "source": c["source"],
                    "tier": str(c["tier"]),
                    "tier_label": c["tier_label"],
                    "doc_id": c["doc_id"],
                    "data_source_label": c["data_source_label"],
                    "chunk_index": str(c["chunk_index"]),
                }
                for c in batch
            ],
        )
        total += len(batch)
        logger.info(f"Indexed {total}/{len(chunks)} chunks...")

    logger.info(f"Vector store built: {total} chunks in collection '{COLLECTION_NAME}'")
    logger.info(f"Stored at: {CHROMA_DIR}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    build_vector_store(force_rebuild=True)
