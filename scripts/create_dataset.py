"""
scripts/create_dataset.py

Generates the AI4I 2020 realistic manufacturing quality control dataset
for IndustrialGuard AI.
"""

import numpy as np
import pandas as pd
from pathlib import Path

def generate_manufacturing_dataset(n_samples: int = 2000, random_state: int = 42):
    np.random.seed(random_state)

    air_temperature = np.random.normal(loc=300.0, scale=2.0, size=n_samples)
    temp_diff = np.random.normal(loc=10.0, scale=1.0, size=n_samples)
    process_temperature = air_temperature + temp_diff

    rotational_speed = np.random.normal(loc=1538.0, scale=160.0, size=n_samples)
    rotational_speed = np.clip(rotational_speed, 1100.0, 2800.0)

    torque = np.random.normal(loc=40.0, scale=10.0, size=n_samples)
    torque = np.clip(torque, 12.0, 78.0)

    tool_wear = np.random.uniform(low=0.0, high=245.0, size=n_samples)

    power = torque * (rotational_speed * 2.0 * np.pi / 60.0)

    # Physical failure modes
    twf = (tool_wear >= 200.0) & (np.random.rand(n_samples) < 0.40)
    hdf = ((process_temperature - air_temperature) < 8.6) & (rotational_speed < 1380.0)
    pwf = (power < 3500.0) | (power > 9000.0)
    osf = (tool_wear * torque) > 11000.0

    target = (twf | hdf | pwf | osf).astype(int)

    df = pd.DataFrame({
        "air_temperature": np.round(air_temperature, 2),
        "process_temperature": np.round(process_temperature, 2),
        "rotational_speed": np.round(rotational_speed, 1),
        "torque": np.round(torque, 2),
        "tool_wear": np.round(tool_wear, 1),
        "target": target,
    })

    out_dir = Path("data/raw")
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "dataset.csv"
    df.to_csv(csv_path, index=False)

    print(f"Generated {len(df)} manufacturing process records to {csv_path}")
    print(f"Defect distribution:\n{df['target'].value_counts(normalize=True)}")
    return df

if __name__ == "__main__":
    generate_manufacturing_dataset()
