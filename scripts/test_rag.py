import chromadb
from pathlib import Path

client = chromadb.PersistentClient(path="rag/vectorstore/chroma_db")
try:
    col = client.get_collection("industrialguard_knowledge")
    print("Collection count:", col.count())
    r = col.query(query_texts=["tool wear torque defect"], n_results=2, include=["documents","metadatas"])
    print("Query OK, results:", len(r["documents"][0]))
    for doc, meta in zip(r["documents"][0], r["metadatas"][0]):
        tier = meta.get("tier_label", "?")
        src = meta.get("source", "?")
        print(f"  [{tier}] {src}: {doc[:80]}")
except Exception as e:
    print("Error:", type(e).__name__, e)
