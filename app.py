"""
app.py -- IndustrialGuard AI

Single entry-point runner.

Usage:
    python app.py              # starts FastAPI backend on :8000
    python app.py --demo       # runs the CLI demo scenario (no server)
    python app.py --pipeline   # runs the full ML pipeline end-to-end
    python app.py --rag        # rebuilds the RAG vector store
    python app.py --test       # runs the integration test suite

This file does not duplicate any logic -- it delegates to the relevant
backend/ml/rag/agent modules. Think of it as the project's main() entry point.
"""

import argparse
import logging
import os
import sys

# Ensure project root is on sys.path regardless of cwd
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Load .env before any os.getenv calls
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv optional at this level; backend loads it separately

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("app")


# ── IBM watsonx.ai Configuration ───────────────────────────────────────────────
#
# Model  : IBM Granite Guardian 8B
# Model ID: ibm/granite-guardian-8b
# Endpoint: https://us-south.ml.cloud.ibm.com
#
# Granite Guardian 8B is used for:
#   - Natural-language narration of ML analysis results
#   - RAG-based knowledge synthesis (grounded in retrieved documents)
#   - Quality incident report generation
#   - Conversational assistant (AI chat tab)
#   - Explanation generation for defect predictions
#
# Granite does NOT perform:
#   - Numerical calculations        (handled by scikit-learn / XGBoost)
#   - Statistical anomaly detection (handled by Isolation Forest + IQR)
#   - Defect predictions            (handled by trained XGBoost model)
#   - Parameter threshold decisions (data-derived, not LLM-generated)
#
# Credentials are read from .env -- never hard-coded here.
# See .env.example for required variable names.
# ──────────────────────────────────────────────────────────────────────────────

WATSONX_CONFIG = {
    "model_id":   os.getenv("GRANITE_MODEL_ID",   "ibm/granite-guardian-8b"),
    "api_url":    os.getenv("WATSONX_API_URL",     "https://us-south.ml.cloud.ibm.com"),
    "project_id": os.getenv("WATSONX_PROJECT_ID",  ""),
    # api_key intentionally not echoed to console -- loaded by granite_client at runtime
    "api_key_set": bool(os.getenv("WATSONX_API_KEY", "")),
    "use_cached": os.getenv("USE_CACHED_GRANITE_RESPONSES", "false").lower() == "true",
}


def _print_watsonx_config():
    """Print IBM watsonx.ai configuration block (no secrets printed)."""
    cfg = WATSONX_CONFIG
    key_status = "[SET]" if cfg["api_key_set"] else "[NOT SET -- set WATSONX_API_KEY in .env]"
    cached_note = "  [CACHE MODE] Using pre-cached responses (IBM API bypassed)" if cfg["use_cached"] else ""

    print()
    print("  IBM watsonx.ai Configuration")
    print("  " + "-" * 44)
    print(f"  Model       : {cfg['model_id']}")
    print(f"  Endpoint    : {cfg['api_url']}")
    print(f"  Project ID  : {cfg['project_id'] or '[NOT SET -- set WATSONX_PROJECT_ID in .env]'}")
    print(f"  API Key     : {key_status}")
    if cached_note:
        print(cached_note)
    print("  " + "-" * 44)
    if not cfg["api_key_set"] and not cfg["use_cached"]:
        print("  [WARN] Granite narration will be unavailable until credentials are set.")
        print("  [WARN] To use cached demo responses: set USE_CACHED_GRANITE_RESPONSES=true in .env")
    print()


# ── Helpers ────────────────────────────────────────────────────────────────────

def _banner():
    print("=" * 60)
    print("  IndustrialGuard AI")
    print("  Agentic Manufacturing Quality Control System")
    print("  IBM Problem Statement #37  --  Decision-support prototype")
    print("=" * 60)


def _check_artifacts():
    """Warn if ML artifacts are missing (pipeline has not been run yet)."""
    from pathlib import Path
    missing = []
    checks = {
        "Trained model":       "ml/models/defect_predictor_v1.0.pkl",
        "Anomaly detector":    "ml/models/artifacts/isolation_forest.pkl",
        "Scaler":              "ml/models/artifacts/scaler.pkl",
        "Feature definitions": "data/features/feature_columns.json",
        "Operating ranges":    "ml/evaluation/operating_ranges.json",
        "RAG vector store":    "rag/vectorstore/chroma_db",
    }
    for label, path in checks.items():
        if not Path(path).exists():
            missing.append(f"  [MISSING] {label}: {path}")
    if missing:
        logger.warning("Some ML/RAG artifacts are missing. Run: python app.py --pipeline")
        for m in missing:
            print(m)
    else:
        print("  [OK] All ML and RAG artifacts found.")
    return len(missing) == 0


# ── Modes ──────────────────────────────────────────────────────────────────────

def run_server(host: str = "127.0.0.1", port: int = 8000, reload: bool = False):
    """Start the FastAPI backend with uvicorn."""
    try:
        import uvicorn
    except ImportError:
        print("[ERROR] uvicorn not installed. Run: pip install uvicorn")
        sys.exit(1)

    _banner()
    _print_watsonx_config()
    print(f"  Backend: http://{host}:{port}")
    print(f"  API docs: http://{host}:{port}/docs")
    print(f"  Health:   http://{host}:{port}/health")
    print(f"\n  Dashboard: open index.html in a browser (or run: cd frontend && npm run dev)")
    print("\n  Press CTRL+C to stop.\n")

    _check_artifacts()
    print()

    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )


def run_demo():
    """Run the CLI demo scenario (DEMO_CONTRACT.md Step 1-7, without Granite)."""
    _banner()
    _print_watsonx_config()
    print("  Running Demo Scenario (SIMULATED STREAM data)")
    print("  See DEMO_CONTRACT.md for full 9-step workflow.\n")
    _check_artifacts()
    print()

    from agents.orchestrator.pipeline import run_pipeline

    records = {
        "NORMAL OPERATION": {
            "air_temperature": 300.1,
            "process_temperature": 310.0,
            "rotational_speed": 1525.0,
            "torque": 39.2,
            "tool_wear": 110.0,
        },
        "ELEVATED RISK (high tool wear + torque)": {
            "air_temperature": 304.8,
            "process_temperature": 315.2,
            "rotational_speed": 1180.0,
            "torque": 68.5,
            "tool_wear": 235.0,
        },
        "CRITICAL RISK (extreme deviation)": {
            "air_temperature": 307.5,
            "process_temperature": 317.0,
            "rotational_speed": 1100.0,
            "torque": 75.0,
            "tool_wear": 255.0,
        },
    }

    for label, record in records.items():
        print(f"\n--- {label} ---")
        print(f"Input: {record}")
        result = run_pipeline(record, record_id=f"DEMO_{label[:6].replace(' ','_')}")
        pred = result.get("final_prediction") or {}
        anomaly = (result.get("stages", {})
                       .get("process_monitoring", {})
                       .get("anomaly_detection", {}))
        recs = result.get("final_recommendations", [])

        print(f"  Status      : {result.get('final_status')}")
        print(f"  Risk Level  : {result.get('final_risk_level')}")
        print(f"  Prediction  : {pred.get('predicted_class')}  "
              f"(probability={pred.get('probability')})")
        print(f"  Anomaly     : {anomaly.get('status')}  "
              f"(severity={anomaly.get('severity')})")
        if anomaly.get("statistical_violations"):
            for v in anomaly["statistical_violations"]:
                print(f"    Violation: {v['parameter']} = {v['value']}  "
                      f"[{v['direction']} normal range, "
                      f"{v['deviation_iqr_units']} IQR units]")
        if recs:
            print(f"  Recommendation: {recs[0].get('action')}")
            print(f"    Basis: {recs[0].get('basis')}")

    print("\n  DATA SOURCE: SIMULATED STREAM")
    print("  Not a live factory connection.")
    print("  Predictions require human engineer review before any process action.\n")


def run_pipeline():
    """Run the complete ML + RAG pipeline from scratch."""
    _banner()
    print("\n  Running full ML + RAG pipeline...\n")

    steps = [
        ("Preprocessing",       "ml.preprocessing.pipeline",    "run_pipeline"),
        ("Model Training",      "ml.models.train",              "run_training"),
        ("Anomaly Detection",   "ml.anomaly.detector",          "train_anomaly_detector"),
        ("Explainability",      "ml.explainability.shap_analysis", "run_explainability_analysis"),
        ("Operating Ranges",    "scripts.generate_operating_ranges", "generate_ranges"),
        ("RAG Ingestion",       "rag.ingestion.ingest",         "run_ingestion"),
        ("RAG Vector Store",    "scripts.rebuild_vectorstore",   None),
    ]

    for name, module_path, func_name in steps:
        print(f"  [{name}]...")
        try:
            mod = __import__(module_path, fromlist=[""])
            if func_name:
                fn = getattr(mod, func_name)
                fn()
            else:
                # rebuild_vectorstore runs as __main__ style -- import and exec directly
                import importlib
                spec = importlib.util.spec_from_file_location(
                    "rebuild_vs", "scripts/rebuild_vectorstore.py"
                )
                m = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(m)
            print(f"  [OK] {name}")
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            logger.exception(f"{name} failed")
            print(f"  Pipeline aborted at [{name}]. Fix the error and re-run.")
            sys.exit(1)

    print("\n  Pipeline complete. All artifacts ready.")
    print("  Run: python app.py   to start the backend.\n")


def run_rag():
    """Rebuild the RAG vector store from knowledge_base documents."""
    _banner()
    print("\n  Rebuilding RAG vector store...\n")
    try:
        from rag.ingestion.ingest import run_ingestion
        chunks = run_ingestion()
        print(f"  [OK] Ingested {len(chunks)} chunks")
    except Exception as e:
        print(f"  [FAIL] Ingestion: {e}")
        sys.exit(1)

    try:
        import json
        import chromadb

        with open("rag/vectorstore/chunks_manifest.json") as f:
            chunks = json.load(f)

        client = chromadb.PersistentClient(path="rag/vectorstore/chroma_db")
        try:
            client.delete_collection("industrialguard_knowledge")
        except Exception:
            pass
        col = client.create_collection("industrialguard_knowledge")
        col.upsert(
            ids=[c["chunk_id"] for c in chunks],
            documents=[c["content"] for c in chunks],
            metadatas=[{
                "source": c["source"], "tier": str(c["tier"]),
                "tier_label": c["tier_label"], "doc_id": c["doc_id"],
                "data_source_label": c["data_source_label"],
                "chunk_index": str(c["chunk_index"]),
            } for c in chunks],
        )
        print(f"  [OK] Vector store: {col.count()} chunks indexed")
    except Exception as e:
        print(f"  [FAIL] Vector store: {e}")
        sys.exit(1)

    print("\n  RAG pipeline complete.\n")


def run_tests():
    """Run the integration test suite."""
    _banner()
    print("\n  Running tests...\n")
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
        cwd=ROOT,
    )
    sys.exit(result.returncode)


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="IndustrialGuard AI -- entry point",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python app.py                  Start the FastAPI backend on :8000
  python app.py --port 8080      Start on a different port
  python app.py --reload         Start with auto-reload (development)
  python app.py --demo           Run CLI demo scenario
  python app.py --pipeline       Run full ML + RAG pipeline
  python app.py --rag            Rebuild RAG vector store only
  python app.py --test           Run test suite
        """,
    )
    parser.add_argument("--host",     default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port",     type=int, default=8000, help="Bind port (default: 8000)")
    parser.add_argument("--reload",   action="store_true", help="Enable auto-reload (dev)")
    parser.add_argument("--demo",     action="store_true", help="Run CLI demo scenario")
    parser.add_argument("--pipeline", action="store_true", help="Run full ML + RAG pipeline")
    parser.add_argument("--rag",      action="store_true", help="Rebuild RAG vector store")
    parser.add_argument("--test",     action="store_true", help="Run test suite")

    args = parser.parse_args()

    if args.demo:
        run_demo()
    elif args.pipeline:
        run_pipeline()
    elif args.rag:
        run_rag()
    elif args.test:
        run_tests()
    else:
        run_server(host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
