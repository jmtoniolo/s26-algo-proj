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



ALGORITHMS = {
    "fifo": schedule_fifo,
    "priority": schedule_priority,
    "sjf": schedule_shortest_job_first,
    "greedy": schedule_greedy,
}


def main():
    parser = argparse.ArgumentParser(description="Job scheduling algorithm runner")
    parser.add_argument("algorithm", choices=ALGORITHMS.keys(), help="Scheduling algorithm to run")
    parser.add_argument("input", help="Path to job list CSV file")
    args = parser.parse_args()

    jobs = read_data(args.input)
    schedule_fn = ALGORITHMS[args.algorithm]

    start = time.perf_counter()
    result = schedule_fn(jobs)
    elapsed = time.perf_counter() - start

    now = datetime.now()
    results_dir = f"results{now.strftime('%Y%m%d%H%M%S')}"
    os.makedirs(results_dir, exist_ok=True)

    log_dir = os.path.join(results_dir, "log")
    os.makedirs(log_dir, exist_ok=True)
    with open(os.path.join(log_dir, "run.log"), "w") as f:
        f.write(f"Timestamp: {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Algorithm: {args.algorithm}\n")
        f.write(f"Input: {args.input}\n")
        f.write(f"Elapsed: {elapsed:.6f}s\n")

    output = result.assign(wait_time=compute_wait_times(result))
    output.to_csv(os.path.join(results_dir, "scheduled_jobs.csv"), index=False)

    avg_wait_by_priority = output.groupby("priority")["wait_time"].mean().sort_index()

    plt.figure()
    plt.plot(avg_wait_by_priority.index, avg_wait_by_priority.values, marker="o")
    plt.xlabel("Priority")
    plt.ylabel("Average wait time (hours)")
    plt.title(f"Priority vs. Average Wait Time ({args.algorithm})")
    plt.grid(True)
    plt.savefig(os.path.join(results_dir, "priority_vs_wait_time.png"))
    plt.close()

    print(f"Results created: {results_dir}")


if __name__ == "__main__":
    main()
