import json
import chromadb
from pathlib import Path

CHROMA_DIR = "rag/vectorstore/chroma_db"
CHUNKS_PATH = "rag/vectorstore/chunks_manifest.json"
COLLECTION_NAME = "industrialguard_knowledge"

with open(CHUNKS_PATH) as f:
    chunks = json.load(f)

print(f"Chunks to index: {len(chunks)}")

client = chromadb.PersistentClient(path=CHROMA_DIR)

# Drop and recreate with NO custom embedding (use ChromaDB default)
try:
    client.delete_collection(COLLECTION_NAME)
    print("Dropped existing collection")
except Exception:
    pass

collection = client.create_collection(COLLECTION_NAME)

# Batch upsert
batch_size = 50
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

print(f"Indexed {total} chunks. Collection count: {collection.count()}")

# Quick test query
r = collection.query(query_texts=["tool wear defect quality"], n_results=2,
                     include=["documents", "metadatas"])
print("\nTest query: 'tool wear defect quality'")
for doc, meta in zip(r["documents"][0], r["metadatas"][0]):
    print(f"  [{meta['tier_label']}] {meta['source']}")
    print(f"  {doc[:120]}\n")
