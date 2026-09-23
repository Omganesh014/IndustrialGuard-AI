"""
ml/models/train.py

Defect prediction model training for IndustrialGuard AI.

Experiment 1: Multi-model comparison (required by problem statement §31).
Models compared on validation set. Winner selected by PR-AUC / F1 (class-imbalance safe).
Final evaluation on test set performed ONCE after model selection.

Only report numbers obtained from actual experiments -- no fabrication.
"""

import json
import logging
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, average_precision_score,
    confusion_matrix, classification_report,
)
from sklearn.pipeline import Pipeline

try:
    import xgboost as xgb
except ImportError:
    xgb = None

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROCESSED_DIR = Path("data/processed")
MODELS_DIR = Path("ml/models")
EVAL_DIR = Path("ml/evaluation")
ARTIFACTS_DIR = MODELS_DIR / "artifacts"

MODELS_DIR.mkdir(parents=True, exist_ok=True)
EVAL_DIR.mkdir(parents=True, exist_ok=True)

TARGET_COLUMN = "target"   # override with actual column name after Gate B
RANDOM_STATE = 42

# Model version metadata -- update when retraining
MODEL_VERSION = "v1.0"


def load_splits():
    """Load preprocessed train/val/test splits."""
    splits = {}
    for name in ("train", "val", "test"):
        path = PROCESSED_DIR / f"{name}.csv"
        if not path.exists():
            raise FileNotFoundError(f"Split not found: {path}. Run ml/preprocessing/pipeline.py first.")
        df = pd.read_csv(path)
        X = df.drop(columns=[TARGET_COLUMN])
        y = df[TARGET_COLUMN]
        splits[name] = (X, y)
        logger.info(f"Loaded {name}: {X.shape[0]} samples, {X.shape[1]} features")
    return splits


def get_candidate_models() -> dict:
    """
    Candidate models for Experiment 1.
    Selection is dataset-dependent -- do not assume all are appropriate.
    Justified in DECISION_LOG.md DECISION-007 after evaluation.
    """
    models = {
        "logistic_regression": LogisticRegression(
            max_iter=1000, random_state=RANDOM_STATE, class_weight="balanced"
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=100, random_state=RANDOM_STATE, class_weight="balanced", n_jobs=-1
        ),
    }
    if xgb is not None:
        models["xgboost"] = xgb.XGBClassifier(
            n_estimators=100, random_state=RANDOM_STATE,
            eval_metric="logloss",
            scale_pos_weight=None,
        )
    return models


def evaluate_model(model, X: pd.DataFrame, y: pd.Series, split_name: str) -> dict:
    """
    Compute classification metrics.
    Uses PR-AUC as primary metric for imbalanced datasets (not accuracy alone).
    """
    y_pred = model.predict(X)
    y_prob = model.predict_proba(X)[:, 1] if hasattr(model, "predict_proba") else None

    metrics = {
        "split": split_name,
        "accuracy": round(float(accuracy_score(y, y_pred)), 4),
        "precision": round(float(precision_score(y, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y, y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y, y_pred, zero_division=0)), 4),
        "confusion_matrix": confusion_matrix(y, y_pred).tolist(),
    }
    if y_prob is not None:
        metrics["roc_auc"] = round(float(roc_auc_score(y, y_prob)), 4)
        metrics["pr_auc"] = round(float(average_precision_score(y, y_prob)), 4)

    logger.info(f"  {split_name}: F1={metrics['f1']}, PR-AUC={metrics.get('pr_auc', 'N/A')}, ROC-AUC={metrics.get('roc_auc', 'N/A')}")
    return metrics


def run_experiment_1(splits: dict) -> dict:
    """
    Experiment 1: Compare candidate models on validation set.
    Select winner based on validation PR-AUC (primary) and F1 (secondary).
    Record all results for DECISION_LOG.md.
    """
    X_train, y_train = splits["train"]
    X_val, y_val = splits["val"]

    models = get_candidate_models()
    results = {}

    logger.info("=" * 60)
    logger.info("EXPERIMENT 1: Multi-model comparison on validation set")
    logger.info("=" * 60)

    for name, model in models.items():
        logger.info(f"\nTraining: {name}")
        model.fit(X_train, y_train)
        train_metrics = evaluate_model(model, X_train, y_train, "train")
        val_metrics = evaluate_model(model, X_val, y_val, "val")
        results[name] = {
            "model": model,
            "train_metrics": train_metrics,
            "val_metrics": val_metrics,
        }

    # Select winner by validation PR-AUC; fall back to F1 if probabilities unavailable
    def selection_key(item):
        vm = item[1]["val_metrics"]
        return vm.get("pr_auc", vm.get("f1", 0))

    best_name, best_result = max(results.items(), key=selection_key)
    logger.info(f"\nSelected model: {best_name} (val PR-AUC={best_result['val_metrics'].get('pr_auc', 'N/A')})")
    logger.info("Update DECISION_LOG.md DECISION-007 with these results.")

    return results, best_name


def final_test_evaluation(model, splits: dict, model_name: str) -> dict:
    """
    Test-set evaluation -- performed ONCE after model selection.
    These are the numbers to report. Never used for model selection.
    """
    X_test, y_test = splits["test"]
    logger.info(f"\nFinal test evaluation for selected model: {model_name}")
    metrics = evaluate_model(model, X_test, y_test, "test")
    metrics["model_name"] = model_name
    metrics["model_version"] = MODEL_VERSION
    metrics["note"] = "Final test metrics. Not used for model selection. Report these numbers only."
    return metrics


def save_model(model, model_name: str, all_results: dict, test_metrics: dict) -> None:
    """Save model artifact and version metadata."""
    model_path = MODELS_DIR / f"defect_predictor_{MODEL_VERSION}.pkl"
    joblib.dump(model, model_path)

    # Save all experiment results
    experiment_log = {}
    for name, res in all_results.items():
        experiment_log[name] = {
            "train_metrics": res["train_metrics"],
            "val_metrics": res["val_metrics"],
        }

    version_meta = {
        "model_version": MODEL_VERSION,
        "selected_model": model_name,
        "selection_criterion": "validation PR-AUC (primary), F1 (secondary)",
        "model_path": str(model_path),
        "experiment_1_results": experiment_log,
        "test_metrics": test_metrics,
        "training_date": pd.Timestamp.now().isoformat(),
        "dataset_version": "[FILL -- dataset version or hash]",
        "hyperparameters": str(model.get_params()) if hasattr(model, "get_params") else "N/A",
    }

    with open(EVAL_DIR / f"model_version_{MODEL_VERSION}.json", "w") as f:
        json.dump(version_meta, f, indent=2)

    logger.info(f"Model saved: {model_path}")
    logger.info(f"Version metadata saved: ml/evaluation/model_version_{MODEL_VERSION}.json")


def run_training():
    """Full training pipeline."""
    splits = load_splits()
    all_results, best_name = run_experiment_1(splits)
    best_model = all_results[best_name]["model"]
    test_metrics = final_test_evaluation(best_model, splits, best_name)
    save_model(best_model, best_name, all_results, test_metrics)
    logger.info("\nTraining complete. Review ml/evaluation/ for results.")
    logger.info("Update DECISION_LOG.md DECISION-007 with experiment findings.")


if __name__ == "__main__":
    run_training()
