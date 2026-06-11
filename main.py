import argparse
import os
import time
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
from datagen import read_data


def compute_wait_times(scheduled: pd.DataFrame) -> pd.Series:
    """Cumulative repair time of all jobs scheduled before each job (single-server queue)."""
    return scheduled["repair_time_hours"].cumsum() - scheduled["repair_time_hours"]


def normalize_scheduled_flag(series: pd.Series) -> pd.Series:
    return series.astype("string").fillna("").str.strip().str.upper().eq("TRUE")


def filter_jobs_by_technician_daily_limit(jobs: pd.DataFrame, daily_limit: int = 8) -> tuple[pd.DataFrame, pd.DataFrame]:
    jobs = jobs.copy()
    jobs["repair_time_hours"] = jobs["repair_time_hours"].astype(int)
    can_schedule = jobs[jobs["repair_time_hours"] <= daily_limit].reset_index(drop=True)
    over_limit = jobs[jobs["repair_time_hours"] > daily_limit].reset_index(drop=True)
    return can_schedule, over_limit


def apply_capacity_limit(jobs: pd.DataFrame, capacity: int) -> pd.DataFrame:
    accepted_rows = []
    total = 0
    for _, row in jobs.iterrows():
        duration = int(row["repair_time_hours"])
        if total + duration <= capacity:
            accepted_rows.append(row)
            total += duration
        else:
            break
    if accepted_rows:
        return pd.DataFrame(accepted_rows).reset_index(drop=True)
    return jobs.iloc[[]].copy()


def read_job_list_with_comments(filepath: str) -> tuple[pd.DataFrame, list[str]]:
    comment_lines: list[str] = []
    with open(filepath, "r", newline="", encoding="utf-8") as f:
        while True:
            pos = f.tell()
            line = f.readline()
            if not line or not line.startswith("#"):
                f.seek(pos)
                break
            comment_lines.append(line)

    jobs = read_data(filepath)
    jobs["scheduled"] = jobs["scheduled"].astype("string").fillna("")
    return jobs, comment_lines


def schedule_fifo(jobs: pd.DataFrame) -> pd.DataFrame:
    """First In, First Out: schedule jobs in the order they appear."""
    return jobs


def schedule_priority(jobs: pd.DataFrame) -> pd.DataFrame:
    """Priority scheduling: schedule highest priority jobs first.

    Ties (same priority) keep their original submission order via a stable sort.
    """
    return jobs.sort_values("priority", ascending=False, kind="stable")


def schedule_shortest_job_first(jobs: pd.DataFrame) -> pd.DataFrame:
    """Shortest Job First: schedule jobs with the lowest repair time first.

    Ties (same repair time) keep their original submission order via a stable sort.
    """
    return jobs.sort_values("repair_time_hours", ascending=True, kind="stable")


def schedule_greedy(jobs: pd.DataFrame) -> pd.DataFrame:
    """Greedy scheduling: schedule jobs based on a combined score of priority and repair time."""
    # Example scoring: higher priority and shorter repair time get higher scores
    jobs = jobs.copy()
    if(jobs["repair_time_hours"].min() <= 0):
        print("Warning: Found job(s) with zero (or negative) repair time. Please check your data. Exiting...")
        exit(1)

    jobs["score"] = jobs["priority"] / (jobs["repair_time_hours"])
    return jobs.sort_values("score", ascending=False).drop(columns="score")


def schedule_optimal(jobs: pd.DataFrame, technicians: int | None = None) -> pd.DataFrame:
    """Optimal scheduling via 0/1 knapsack dynamic programming.

    Selects the subset of jobs that maximizes total priority score while
    respecting available technician capacity per day.

    Args:
        technicians: Number of technicians available. Each technician has 8 hours per day.
    """
    jobs = jobs.reset_index(drop=True)
    n = len(jobs)
    if n == 0:
        return jobs

    weights = jobs["repair_time_hours"].astype(int).tolist()
    values = jobs["priority"].astype(int).tolist()
    total_time = sum(weights)

    if technicians is None:
        capacity = total_time
    else:
        if technicians <= 0:
            return jobs.iloc[[]].reset_index(drop=True)
        capacity = technicians * 8

    capacity = min(capacity, total_time)

    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    take = [[False] * (capacity + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        w = weights[i - 1]
        v = values[i - 1]
        for t in range(capacity + 1):
            if w <= t:
                if dp[i - 1][t - w] + v > dp[i - 1][t]:
                    dp[i][t] = dp[i - 1][t - w] + v
                    take[i][t] = True
                else:
                    dp[i][t] = dp[i - 1][t]
            else:
                dp[i][t] = dp[i - 1][t]

    selected_indices = []
    t = capacity
    for i in range(n, 0, -1):
        if take[i][t]:
            selected_indices.append(i - 1)
            t -= weights[i - 1]

    selected_indices.reverse()
    return jobs.iloc[selected_indices].reset_index(drop=True)


ALGORITHMS = {
    "fifo": schedule_fifo,
    "priority": schedule_priority,
    "sjf": schedule_shortest_job_first,
    "greedy": schedule_greedy,
    "dp": schedule_optimal,
}


def main():
    parser = argparse.ArgumentParser(description="Job scheduling algorithm runner")
    parser.add_argument("algorithm", choices=ALGORITHMS.keys(), help="Scheduling algorithm to run")
    parser.add_argument("input", help="Path to job list CSV file")
    parser.add_argument(
        "--technicians",
        "-t",
        dest="technicians",
        type=int,
        default=None,
        help="Number of technicians available; each technician contributes 8 hours/day",
    )
    parser.add_argument(
        "--label",
        default=None,
        help="Optional label inserted into the results dir name: results-<label>-YYYYMMDDHHMMSS",
    )
    args = parser.parse_args()

    jobs, comment_lines = read_job_list_with_comments(args.input)
    schedule_fn = ALGORITHMS[args.algorithm]

    unscheduled = jobs[~normalize_scheduled_flag(jobs["scheduled"])].copy()
    unscheduled_fit, unscheduled_overlimit = filter_jobs_by_technician_daily_limit(unscheduled)

    if not unscheduled_overlimit.empty:
        print(
            f"Skipping {len(unscheduled_overlimit)} job(s) with repair_time_hours > 8h "
            "because they cannot fit within one technician day."
        )

    total_capacity = None if args.technicians is None else args.technicians * 8

    start = time.perf_counter()
    if args.algorithm == "dp":
        result = schedule_fn(unscheduled_fit, args.technicians)
    else:
        result = schedule_fn(unscheduled_fit)
        if total_capacity is not None:
            result = apply_capacity_limit(result, total_capacity)
    elapsed = time.perf_counter() - start

    if not result.empty:
        jobs.loc[jobs["job_id"].isin(result["job_id"]), "scheduled"] = "TRUE"

    with open(args.input, "w", newline="", encoding="utf-8") as f:
        for line in comment_lines:
            f.write(line)
        jobs.to_csv(f, index=False)

    now = datetime.now()
    timestamp = now.strftime('%Y%m%d%H%M%S')
    results_dir = f"results-{args.label}-{timestamp}" if args.label else f"results-{timestamp}"
    os.makedirs(results_dir, exist_ok=True)

    output = result.assign(wait_time=compute_wait_times(result))
    output.to_csv(os.path.join(results_dir, "scheduled_jobs.csv"), index=False)

    avg_wait_by_priority = output.groupby("priority")["wait_time"].mean().sort_index()
    total_time = output["repair_time_hours"].sum()
    avg_wait_time = output["wait_time"].mean()

    with open(os.path.join(results_dir, "run.log"), "w") as f:
        f.write(f"Timestamp: {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Algorithm: {args.algorithm}\n")
        f.write(f"Input: {args.input}\n")
        if args.technicians is not None:
            f.write(f"Technicians: {args.technicians} (total {args.technicians * 8}h/day)\n")
        f.write(f"Elapsed: {elapsed:.6f}s\n")
        f.write(f"Total queue time: {total_time}h\n")
        f.write(f"Average wait time: {avg_wait_time:.4f}h\n")

    plt.figure()
    plt.plot(avg_wait_by_priority.index, avg_wait_by_priority.values, marker="o")
    plt.xlabel("Priority")
    plt.ylabel("Average wait time (hours)")
    plt.title(
        f"Priority vs. Average Wait Time ({args.algorithm})\n"
        f"Total queue time: {total_time}h | Average wait time: {avg_wait_time:.2f}h"
    )
    plt.grid(True)
    plt.ylim(0, total_time)
    plt.savefig(os.path.join(results_dir, "priority_vs_wait_time.png"))
    plt.close()

    print(f"Results created: {results_dir}")


if __name__ == "__main__":
    main()
