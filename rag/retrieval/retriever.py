"""
rag/retrieval/retriever.py

RAG Retrieval module for IndustrialGuard AI.

Provides:
- retrieve(query, top_k) -- returns list of ranked passages with metadata
- Source attribution preserved in every result
- Tier label preserved -- Tier 3 results labeled as project-generated

This module is called by:
- Quality Analysis Agent (RCA evidence retrieval)
- Process Optimization Agent (recommendation evidence retrieval)
- Chat endpoint (AI assistant grounding)
"""

import logging
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

logger = logging.getLogger(__name__)

CHROMA_DIR = Path("rag/vectorstore/chroma_db")
COLLECTION_NAME = "industrialguard_knowledge"

_collection = None


def _get_collection():
    global _collection
    if _collection is not None:
        return _collection

    try:
        import chromadb
        from rag.vectorstore.setup import get_embedding_function

        if not CHROMA_DIR.exists():
            raise FileNotFoundError(
                f"ChromaDB not found at {CHROMA_DIR}. "
                "Run rag/vectorstore/setup.py first."
            )

        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        embed_fn = get_embedding_function()
        kwargs = {"name": COLLECTION_NAME}
        if embed_fn:
            kwargs["embedding_function"] = embed_fn
        _collection = client.get_collection(**kwargs)
        logger.info(f"RAG collection loaded: {_collection.count()} chunks")
        return _collection

    except Exception as e:
        logger.error(f"Failed to load RAG collection: {e}")
        raise


def retrieve(query: str, top_k: int = 3, min_tier: int = 1) -> list[dict]:
    """
    Retrieve top_k relevant passages for a query.

    Args:
        query:    natural language query
        top_k:   number of passages to return
        min_tier: minimum tier to include (1=all, 3=only tier 3)
                  Default 1 = include all tiers

    Returns:
        List of passage dicts with keys:
        - content: retrieved text
        - source: original document filename
        - tier: int (1/2/3)
        - tier_label: human-readable tier name
        - data_source_label: provenance label
        - distance: similarity score (lower = more similar for L2)
        - relevance_note: human-readable note for the dashboard
    """
    if not query or not query.strip():
        return []

    try:
        collection = _get_collection()
    except Exception as e:
        logger.warning(f"RAG unavailable: {e}. Returning empty results.")
        return []

    count = collection.count()
    if count == 0:
        logger.warning("RAG collection is empty. Run rag/vectorstore/setup.py first.")
        return []

    try:
        results = collection.query(
            query_texts=[query],
            n_results=min(top_k, count),
            include=["documents", "metadatas", "distances"],
        )
    except Exception as e:
        logger.error(f"ChromaDB query failed: {e}")
        return []

    passages = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for doc, meta, dist in zip(docs, metas, distances):
        tier = int(meta.get("tier", 3))
        if tier < min_tier:
            continue

        tier_label = meta.get("tier_label", "UNKNOWN")
        is_synthetic = tier == 3

        passages.append({
            "content": doc,
            "source": meta.get("source", "unknown"),
            "tier": tier,
            "tier_label": tier_label,
            "data_source_label": meta.get("data_source_label", "unknown"),
            "distance": round(float(dist), 4),
            "relevance_note": (
                "[Project-generated demonstration knowledge -- not an official standard]"
                if is_synthetic
                else f"[Source: {meta.get('source', 'unknown')} -- {tier_label}]"
            ),
        })

    logger.info(f"RAG retrieved {len(passages)} passages for query: '{query[:60]}...'")
    return passages


def test_retrieval(queries: list[str] | None = None) -> None:
    """
    Quick retrieval test -- used for Experiment 4 (RAG evaluation).
    Prints top passages for each test query.
    """
    if queries is None:
        queries = [
            "temperature deviation manufacturing quality",
            "vibration bearing wear defect",
            "corrective action process parameter adjustment",
        ]

    print("\n=== RAG Retrieval Test ===")
    for q in queries:
        print(f"\nQuery: {q}")
        results = retrieve(q, top_k=2)
        if not results:
            print("  No results -- vector store may be empty.")
            continue
        for i, r in enumerate(results):
            print(f"  Result {i+1}: [{r['tier_label']}] {r['source']}")
            print(f"    Distance: {r['distance']}")
            print(f"    Excerpt: {r['content'][:150]}...")
            print(f"    Note: {r['relevance_note']}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_retrieval()
