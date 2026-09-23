"""
scripts/setup_project.py

One-shot setup script for IndustrialGuard AI.
Run this after cloning the repo and before any development work.

What it does:
1. Creates required directories
2. Copies .env.example to .env (if .env does not exist)
3. Validates that required tools are installed
4. Prints Gate checklist
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def check_python():
    ver = sys.version_info
    if ver.major < 3 or ver.minor < 11:
        print(f"[FAIL] Python 3.11+ required. Found: {sys.version}")
        sys.exit(1)
    print(f"[OK] Python {ver.major}.{ver.minor}.{ver.micro}")


def check_node():
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        print(f"[OK] Node.js {result.stdout.strip()}")
    except FileNotFoundError:
        print("[WARN] Node.js not found. Install Node.js 20+ to run the frontend.")


def setup_env():
    env_path = Path(".env")
    example_path = Path(".env.example")
    if not env_path.exists() and example_path.exists():
        shutil.copy(example_path, env_path)
        print("[OK] Created .env from .env.example -- fill in your IBM credentials.")
    elif env_path.exists():
        print("[OK] .env already exists.")
    else:
        print("[WARN] .env.example not found. Create .env manually.")


def print_gate_checklist():
    print("\n" + "=" * 60)
    print("GATE CHECKLIST -- Complete before Day 0 of development")
    print("=" * 60)
    print()
    print("Gate A -- IBM/LangFlow Access:")
    print("  [ ] IBM Cloud account + watsonx.ai access confirmed")
    print("  [ ] Granite model reachable")
    print("  [ ] LangFlow connected")
    print("  [ ] API quotas sufficient")
    print("  [ ] Fallback: Option C (LangChain+RAG+Granite) ready if needed")
    print()
    print("Gate B -- Dataset:")
    print("  [ ] Dataset candidates scored in DATASET.md")
    print("  [ ] Winner selected and documented")
    print("  [ ] Dataset placed in data/raw/")
    print("  [ ] DATASET_FILENAME set in .env")
    print("  [ ] DECISION_LOG.md DECISION-002 filled")
    print()
    print("Gate C -- RAG Sources:")
    print("  [ ] Tier 1/2 documents confirmed available")
    print("  [ ] Documents placed in rag/knowledge_base/")
    print("  [ ] Tier manifest updated in rag/ingestion/ingest.py")
    print("  [ ] DECISION_LOG.md DECISION-003 filled")
    print()
    print("After gates close, run in order:")
    print("  python ml/preprocessing/pipeline.py")
    print("  python ml/models/train.py")
    print("  python ml/anomaly/detector.py")
    print("  python ml/explainability/shap_analysis.py")
    print("  python scripts/generate_operating_ranges.py")
    print("  python rag/ingestion/ingest.py")
    print("  python rag/vectorstore/setup.py")
    print("  uvicorn backend.main:app --reload")
    print("  cd frontend && npm run dev")


if __name__ == "__main__":
    print("IndustrialGuard AI -- Project Setup")
    print("=" * 40)
    check_python()
    check_node()
    setup_env()
    print_gate_checklist()
