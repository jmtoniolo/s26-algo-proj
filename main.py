import argparse
import time
import pandas as pd
from datagen import read_data


def schedule_fifo(jobs: pd.DataFrame) -> pd.DataFrame:
    """First In, First Out: schedule jobs in the order they appear."""
    start = time.perf_counter()

    scheduled = jobs

    elapsed = time.perf_counter() - start
    print(f"[FIFO] Elapsed: {elapsed:.6f}s")
    return scheduled


def schedule_priority(jobs: pd.DataFrame) -> pd.DataFrame:
    """Priority scheduling: schedule highest priority jobs first."""
    start = time.perf_counter()

    scheduled = jobs.sort_values("priority", ascending=False)

    elapsed = time.perf_counter() - start
    print(f"[Priority] Elapsed: {elapsed:.6f}s")
    return scheduled


def schedule_shortest_job_first(jobs: pd.DataFrame) -> pd.DataFrame:
    """Shortest Job First: schedule jobs with the lowest repair time first."""
    start = time.perf_counter()

    scheduled = jobs.sort_values("repair_time_hours", ascending=True)

    elapsed = time.perf_counter() - start
    print(f"[SJF] Elapsed: {elapsed:.6f}s")
    return scheduled


ALGORITHMS = {
    "fifo": schedule_fifo,
    "priority": schedule_priority,
    "sjf": schedule_shortest_job_first,
}


def main():
    parser = argparse.ArgumentParser(description="Job scheduling algorithm runner")
    parser.add_argument("algorithm", choices=ALGORITHMS.keys(), help="Scheduling algorithm to run")
    parser.add_argument("input", help="Path to job list CSV file")
    args = parser.parse_args()

    jobs = read_data(args.input)
    schedule_fn = ALGORITHMS[args.algorithm]
    result = schedule_fn(jobs)

    print(f"\nScheduled order ({len(result)} jobs):")
    columns = list(result.columns)
    widths = {col: max(len(col), result[col].map(lambda v: len(str(v))).max()) for col in columns}

    header = "  ".join(col.ljust(widths[col]) for col in columns)
    print(f"       {header}")
    for i, (_, row) in enumerate(result.iterrows(), 1):
        details = "  ".join(str(row[col]).ljust(widths[col]) for col in columns)
        print(f"  {i:>3}. {details}")


if __name__ == "__main__":
    main()
