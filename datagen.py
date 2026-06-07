import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

REPAIR_TYPES = [
    "Brake inspection", "Oil change", "Battery replacement", "Tire replacement",
    "Engine diagnostic scan", "Transmission inspection", "Coolant system service",
    "ABS warning light diagnosis", "Wheel alignment", "Alternator inspection",
    "Brake pad replacement", "Spark plug replacement", "Suspension noise diagnosis",
    "Check engine light diagnosis", "Tire pressure sensor reset",
]


@dataclass
class FieldDistribution:
    # Example instantiation -> FieldDistribution(distribution="normal", min=1, max=10, mean=7)
    distribution: Literal["uniform", "normal"]
    min: float
    max: float
    # For normal distributions: mean and std are derived from min/max by default,
    # but can be overridden explicitly.
    mean: float = field(default=None)
    std: float = field(default=None)

    def __post_init__(self):
        if self.distribution == "normal":
            if self.mean is None:
                self.mean = (self.min + self.max) / 2 # Gets center of your min/max
            if self.std is None:
                self.std = (self.max - self.min) / 6  # ~99.7% within [min, max] because dividing by 6 is getting us 3 standard deviations from the mean

    def describe(self) -> str:
        if self.distribution == "uniform":
            return f"uniform(min={self.min}, max={self.max})"
        else:
            return f"normal(min={self.min}, max={self.max}, mean={self.mean}, std={round(self.std, 4)})"

    def sample(self, n: int, rng: np.random.Generator) -> np.ndarray:
        if self.distribution == "uniform":
            values = rng.uniform(self.min, self.max, size=n)
        else:
            values = rng.normal(self.mean, self.std, size=n)
        # clip will ensure all values outside min/max are removed
        # since we may use distributions that produce outliers.
        return np.clip(values, self.min, self.max)


def read_data(filepath: str = "job-list.csv") -> pd.DataFrame:
    """Read the job list CSV into a DataFrame.
    This is wrapped just to abstract the csv read.
    """
    df = pd.read_csv(filepath)
    return df


def generate_synthetic_data(
    num_rows: int = 100,
    repair_time_dist: FieldDistribution = FieldDistribution("uniform", min=1, max=4),
    priority_dist: FieldDistribution = FieldDistribution("uniform", min=1, max=10),
    seed: int = None,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    job_ids = [f"J{i + 1}" for i in range(num_rows)]
    repair_types = rng.choice(REPAIR_TYPES, size=num_rows)
    repair_times = repair_time_dist.sample(num_rows, rng).round(0).astype(int)
    priorities = priority_dist.sample(num_rows, rng).round(0).astype(int)

    return pd.DataFrame({
        "job_id": job_ids,
        "repair_type": repair_types,
        "repair_time_hours": repair_times,
        "priority": priorities,
    })


def write_synthetic_data(
    df: pd.DataFrame,
    base_filename: str = "synthetic_job_list",
    repair_time_dist: FieldDistribution = FieldDistribution("uniform", min=1, max=4),
    priority_dist: FieldDistribution = FieldDistribution("uniform", min=1, max=10),
) -> str:
    """Write dataframe to CSV with timestamp in filename (yyyymmddhhss format).
    If distributions are provided, their parameters are recorded in a
    'generation_params' column on the first row.

    Args:
        df: DataFrame to write
        base_filename: Base name without extension (default: "synthetic_job_list")
        repair_time_dist: Distribution used for repair_time_hours (optional)
        priority_dist: Distribution used for priority (optional)

    Returns:
        The filename that was written
    """
    out = df.copy()
    parts = [
        f"repair_time: {repair_time_dist.describe()}",
        f"priority: {priority_dist.describe()}",
    ]
    out["generation_params"] = ""
    out.at[0, "generation_params"] = " | ".join(parts)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{base_filename}.{timestamp}.csv"
    out.to_csv(filename, index=False)
    return filename


def main():
    dataframe = read_data("synthetic_job_list.20260607110941.csv")
    print(dataframe.head())

    # Example setup to generate fresh synthetic data
    # df = generate_synthetic_data()
    # filename = write_synthetic_data(df)
    # print(f"Wrote {len(df)} rows to {filename}") 
    # print(df.head())


if __name__ == "__main__":
    main()
