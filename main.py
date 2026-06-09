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


def schedule_fifo(jobs: pd.DataFrame) -> pd.DataFrame:
    """First In, First Out: schedule jobs in the order they appear."""
    return jobs


def schedule_priority(jobs: pd.DataFrame) -> pd.DataFrame:
    """Priority scheduling: schedule highest priority jobs first."""
    return jobs.sort_values("priority", ascending=False)


def schedule_shortest_job_first(jobs: pd.DataFrame) -> pd.DataFrame:
    """Shortest Job First: schedule jobs with the lowest repair time first."""
    return jobs.sort_values("repair_time_hours", ascending=True)


def schedule_greedy(jobs: pd.DataFrame) -> pd.DataFrame:
    """Greedy scheduling: schedule jobs based on a combined score of priority and repair time."""
    # Example scoring: higher priority and shorter repair time get higher scores
    jobs = jobs.copy()
    if(jobs["repair_time_hours"].min() <= 0):
        print("Warning: Found job(s) with zero (or negative) repair time. Please check your data. Exiting...")
        exit(1)

    jobs["score"] = jobs["priority"] / (jobs["repair_time_hours"])
    return jobs.sort_values("score", ascending=False).drop(columns="score")


def schedule_optimal(jobs: pd.DataFrame, capacity: int | None = None) -> pd.DataFrame:
    """Optimal scheduling via 0/1 knapsack dynamic programming.

    Selects the subset of jobs that maximizes total priority score while
    respecting available technician time.

    Args:
        capacity: Available technician time in integer hours.
    """
    jobs = jobs.reset_index(drop=True)
    n = len(jobs)
    if n == 0:
        return jobs

    weights = jobs["repair_time_hours"].astype(int).tolist()
    values = jobs["priority"].astype(int).tolist()
    total_time = sum(weights)

    if capacity is None:
        capacity = total_time
    if capacity <= 0:
        return jobs.iloc[[]].reset_index(drop=True)

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
    parser.add_argument("--capacity", "-c", type=int, default=None, help="Available technician time in integer hours for dp scheduling")
    args = parser.parse_args()

    jobs = read_data(args.input)
    schedule_fn = ALGORITHMS[args.algorithm]

    start = time.perf_counter()
    if args.algorithm == "dp":
        result = schedule_fn(jobs, args.capacity)
    else:
        result = schedule_fn(jobs)
    elapsed = time.perf_counter() - start

    now = datetime.now()
    results_dir = f"results{now.strftime('%Y%m%d%H%M%S')}"
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
        if args.capacity is not None:
            f.write(f"Capacity: {args.capacity}h\n")
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
