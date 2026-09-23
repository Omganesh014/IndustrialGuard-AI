"""
scripts/generate_operating_ranges.py

Generate validated operating ranges for Process Optimization Agent.

Called after preprocessing. Computes normal-class percentile ranges from training data.
These ranges are DATA-DERIVED -- never fabricated from "industry standards."

Output: ml/evaluation/operating_ranges.json
"""

import json
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

PROCESSED_DIR = Path("data/processed")
FEATURES_DIR = Path("data/features")
OUTPUT_PATH = Path("ml/evaluation/operating_ranges.json")

# Percentile bounds for "normal" operating range
LOWER_PERCENTILE = 5.0   # 5th percentile of normal-class data
UPPER_PERCENTILE = 95.0  # 95th percentile of normal-class data


def generate_ranges():
    train_path = PROCESSED_DIR / "train_raw.csv"
    if not train_path.exists():
        train_path = PROCESSED_DIR / "train.csv"
    if not train_path.exists():
        raise FileNotFoundError("Train split not found. Run preprocessing first.")

    df = pd.read_csv(train_path)
    with open(FEATURES_DIR / "feature_columns.json") as f:
        feature_def = json.load(f)

    feature_cols = feature_def["features"]
    target_col = feature_def.get("target")

    # Use normal-class records only
    if target_col and target_col in df.columns:
        normal_df = df[df[target_col] == 0][feature_cols]
        logger.info(f"Computing ranges from {len(normal_df)} normal-class training records")
    else:
        normal_df = df[feature_cols]
        logger.info(f"No target column -- computing ranges from all {len(normal_df)} training records")

    ranges = {}
    for col in feature_cols:
        low = float(normal_df[col].quantile(LOWER_PERCENTILE / 100))
        high = float(normal_df[col].quantile(UPPER_PERCENTILE / 100))
        ranges[col] = {
            "normal_low": round(low, 4),
            "normal_high": round(high, 4),
            "percentile_low": LOWER_PERCENTILE,
            "percentile_high": UPPER_PERCENTILE,
            "data_derived": True,
            "source": "training_data_normal_class",
            "note": (
                f"Range = [{LOWER_PERCENTILE}th, {UPPER_PERCENTILE}th] percentile "
                f"of normal-class training data. "
                f"Not a certified industrial safety threshold."
            ),
        }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(ranges, f, indent=2)

    logger.info(f"Operating ranges saved: {OUTPUT_PATH} ({len(ranges)} features)")
    logger.info("Update DECISION_LOG.md if these ranges differ significantly from expectations.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_ranges()
