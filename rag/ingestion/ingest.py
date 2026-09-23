"""
rag/ingestion/ingest.py

RAG Document Ingestion Pipeline for IndustrialGuard AI.

Steps:
1. Load documents from rag/knowledge_base/
2. Validate and label source tier (Tier 1/2/3)
3. Parse and clean text
4. Chunk documents with overlap
5. Assign metadata (source, tier, document_id)
6. Store chunks for embedding

Source tiers (per DECISION_LOG.md DECISION-003):
- Tier 1: Public standards, government/university technical docs
- Tier 2: Manufacturer docs (explicitly public), open-source manuals
- Tier 3: Project-generated demonstration knowledge — labeled, never presented as official

Rule: Tier 3 documents must contain the string "Project-generated demonstration knowledge"
in their filename or frontmatter, and this label is preserved in all metadata.
"""

import json
import logging
import re
from pathlib import Path
from typing import Iterator

logger = logging.getLogger(__name__)

KNOWLEDGE_BASE_DIR = Path("rag/knowledge_base")
CHUNKS_OUTPUT_DIR = Path("rag/vectorstore")
CHUNKS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Chunking configuration
CHUNK_SIZE = 512        # characters (not tokens) — adjust based on embedding model limits
CHUNK_OVERLAP = 64      # character overlap between adjacent chunks

TIER_MANIFEST: dict[str, int] = {
    "iso_13374_condition_monitoring.md": 1,
    "tool_wear_thermal_compensation_guide.md": 2,
    "demo_operating_procedures.md": 3,
}


def detect_tier(filename: str) -> int:
    """
    Detect source tier from filename.
    Falls back to Tier 3 (safest assumption) if not in manifest.
    Logs a warning so the engineer knows to update the manifest.
    """
    name = Path(filename).name
    tier = TIER_MANIFEST.get(name)
    if tier is None:
        logger.warning(
            f"Source tier not found for '{name}'. "
            "Defaulting to Tier 3 (project-generated). "
            "Update TIER_MANIFEST in rag/ingestion/ingest.py after Gate C."
        )
        return 3
    return tier


def load_document(path: Path) -> str:
    """Load text from .txt or .md file. Add PDF support when needed."""
    if path.suffix in (".txt", ".md"):
        return path.read_text(encoding="utf-8", errors="replace")
    elif path.suffix == ".json":
        data = json.loads(path.read_text())
        if isinstance(data, str):
            return data
        if isinstance(data, dict):
            return json.dumps(data, indent=2)
    else:
        logger.warning(f"Unsupported file type: {path.suffix}. Skipping {path.name}.")
        return ""


def clean_text(text: str) -> str:
    """Basic text cleaning — remove excess whitespace and control characters."""
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Split text into overlapping chunks.
    Prefers splitting on paragraph boundaries when possible.
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    paragraphs = text.split("\n\n")
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 <= chunk_size:
            current = (current + "\n\n" + para).strip()
        else:
            if current:
                chunks.append(current)
                # Overlap: include last `overlap` chars of previous chunk
                current = current[-overlap:] + "\n\n" + para
            else:
                # Paragraph itself exceeds chunk size — split by sentences
                sentences = re.split(r"(?<=[.!?])\s+", para)
                for sent in sentences:
                    if len(current) + len(sent) + 1 <= chunk_size:
                        current = (current + " " + sent).strip()
                    else:
                        if current:
                            chunks.append(current)
                            current = current[-overlap:] + " " + sent
                        else:
                            chunks.append(sent[:chunk_size])
                            current = sent[chunk_size - overlap:]

    if current.strip():
        chunks.append(current.strip())

    return [c for c in chunks if len(c.strip()) > 20]


def ingest_document(path: Path) -> list[dict]:
    """
    Ingest a single document.
    Returns list of chunk dicts with metadata.
    """
    tier = detect_tier(path.name)
    tier_label = {1: "TIER_1_PUBLIC_STANDARD", 2: "TIER_2_PUBLIC_MANUFACTURER", 3: "TIER_3_PROJECT_GENERATED"}[tier]

    raw_text = load_document(path)
    if not raw_text.strip():
        logger.warning(f"Empty document: {path.name}. Skipping.")
        return []

    clean = clean_text(raw_text)
    chunks_text = chunk_text(clean)

    chunks = []
    for i, chunk_content in enumerate(chunks_text):
        chunks.append({
            "doc_id": f"{path.stem}",
            "chunk_id": f"{path.stem}_chunk_{i:04d}",
            "content": chunk_content,
            "source": path.name,
            "tier": tier,
            "tier_label": tier_label,
            "char_count": len(chunk_content),
            "chunk_index": i,
            "total_chunks": len(chunks_text),
            "data_source_label": (
                "Project-generated demonstration knowledge"
                if tier == 3
                else "REAL PUBLIC DATA"
            ),
        })

    logger.info(f"Ingested {path.name}: {len(chunks)} chunks (tier={tier_label})")
    return chunks


def run_ingestion() -> list[dict]:
    """
    Ingest all documents in the knowledge base directory.
    Returns list of all chunks.
    """
    if not KNOWLEDGE_BASE_DIR.exists():
        logger.warning(f"Knowledge base directory not found: {KNOWLEDGE_BASE_DIR}")
        logger.warning("Create rag/knowledge_base/ and add documents. See Gate C in DECISION_LOG.md.")
        return []

    docs = list(KNOWLEDGE_BASE_DIR.glob("**/*"))
    docs = [d for d in docs if d.is_file() and d.suffix in (".txt", ".md", ".json")]

    if not docs:
        logger.warning("No documents found in rag/knowledge_base/. Add documents and re-run.")
        return []

    all_chunks = []
    for doc_path in docs:
        chunks = ingest_document(doc_path)
        all_chunks.extend(chunks)

    # Save chunks manifest
    manifest_path = CHUNKS_OUTPUT_DIR / "chunks_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(all_chunks, f, indent=2)

    logger.info(f"\nIngestion complete: {len(all_chunks)} total chunks from {len(docs)} documents")
    logger.info(f"Chunks saved to {manifest_path}")

    # Tier summary
    tier_counts = {}
    for chunk in all_chunks:
        t = chunk["tier_label"]
        tier_counts[t] = tier_counts.get(t, 0) + 1
    for tier, count in tier_counts.items():
        logger.info(f"  {tier}: {count} chunks")

    return all_chunks


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_ingestion()
