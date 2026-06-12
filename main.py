import argparse
import math
import os
import time
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
from datagen import read_data


def compute_wait_times(scheduled: pd.DataFrame) -> pd.Series:
    """Cumulative repair time of all jobs scheduled before each job (single-server queue)."""
    return scheduled["repair_time_hours"].cumsum() - scheduled["repair_time_hours"]


def distribute_across_technicians(scheduled: pd.DataFrame, technicians: int) -> pd.DataFrame:
    """Deal the ordered jobs across technicians round-robin and compute per-technician wait time.

    Jobs are handed out one slot at a time: the first job goes to technician 0's slot 0,
    the next to technician 1's slot 0, and so on; once every technician has a job in the
    current slot, the next job starts slot 1 back on technician 0. This keeps the top jobs
    (which the algorithm placed first) spread across technicians instead of stacked onto
    technician 0.

    Each technician is an independent single-server queue, so a job's wait time is the sum
    of the repair times of that technician's earlier jobs. The longest any job waits is
    therefore the longest queue among the technicians, not the whole-shop total.
    """
    scheduled = scheduled.reset_index(drop=True)
    if technicians <= 0 or scheduled.empty:
        return scheduled.iloc[[]].assign(technician=pd.Series(dtype=int), wait_time=pd.Series(dtype=float))

    technician = pd.Series([i % technicians for i in range(len(scheduled))], index=scheduled.index)
    repair = scheduled["repair_time_hours"]
    wait_time = repair.groupby(technician).cumsum() - repair
    return scheduled.assign(technician=technician, wait_time=wait_time)


def filter_jobs_by_technician_daily_limit(jobs: pd.DataFrame, daily_limit: int = 8) -> tuple[pd.DataFrame, pd.DataFrame]:
    jobs = jobs.copy()
    jobs["repair_time_hours"] = jobs["repair_time_hours"].astype(int)
    can_schedule = jobs[jobs["repair_time_hours"] <= daily_limit].reset_index(drop=True)
    over_limit = jobs[jobs["repair_time_hours"] > daily_limit].reset_index(drop=True)
    return can_schedule, over_limit


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

    jobs = read_data(args.input)
    schedule_fn = ALGORITHMS[args.algorithm]

    jobs_fit, jobs_overlimit = filter_jobs_by_technician_daily_limit(jobs)

    if not jobs_overlimit.empty:
        print(
            f"Skipping {len(jobs_overlimit)} job(s) with repair_time_hours > 8h "
            "because they cannot fit within one technician day."
        )

    # Resolve technician count. When --technicians is omitted, use as many as needed to
    # cover all fitting work at 8h per technician.
    fit_hours = int(jobs_fit["repair_time_hours"].astype(int).sum())
    if args.technicians is None:
        technicians = math.ceil(fit_hours / 8) if fit_hours > 0 else 0
    else:
        technicians = args.technicians

    start = time.perf_counter()
    if args.algorithm == "dp":
        # Optimal scheduling stays a single-queue knapsack and is not distributed.
        result = schedule_fn(jobs_fit, args.technicians)
        output = result.assign(wait_time=compute_wait_times(result))
    else:
        result = schedule_fn(jobs_fit)
        output = distribute_across_technicians(result, technicians)
    elapsed = time.perf_counter() - start

    now = datetime.now()
    timestamp = now.strftime('%Y%m%d%H%M%S')
    results_dir = f"results-{args.label}-{timestamp}" if args.label else f"results-{timestamp}"
    os.makedirs(results_dir, exist_ok=True)

    output.to_csv(os.path.join(results_dir, "scheduled_jobs.csv"), index=False)

    avg_wait_by_priority = output.groupby("priority")["wait_time"].mean().sort_index()
    total_time = output["repair_time_hours"].sum()
    avg_wait_time = output["wait_time"].mean() if not output.empty else 0.0
    max_wait_time = output["wait_time"].max() if not output.empty else 0.0

    with open(os.path.join(results_dir, "run.log"), "w") as f:
        f.write(f"Timestamp: {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Algorithm: {args.algorithm}\n")
        f.write(f"Input: {args.input}\n")
        if args.technicians is None:
            f.write(f"Technicians: {technicians} (auto, enough to schedule all fitting jobs at 8h each)\n")
        else:
            f.write(f"Technicians: {technicians} (total {technicians * 8}h/day)\n")
        f.write(f"Elapsed: {elapsed:.6f}s\n")
        f.write(f"Total scheduled hours: {total_time}h\n")
        if "technician" in output.columns and not output.empty:
            load = output.groupby("technician")["repair_time_hours"].sum().sort_index()
            f.write("Per-technician load: " + ", ".join(f"#{tid}:{hrs}h" for tid, hrs in load.items()) + "\n")
        f.write(f"Average wait time: {avg_wait_time:.4f}h\n")
        f.write(f"Max wait time: {max_wait_time:.4f}h\n")

    plt.figure()
    plt.plot(avg_wait_by_priority.index, avg_wait_by_priority.values, marker="o")
    plt.xlabel("Priority")
    plt.ylabel("Average wait time (hours)")
    plt.title(
        f"Priority vs. Average Wait Time ({args.algorithm})\n"
        f"Avg wait: {avg_wait_time:.2f}h | Max wait: {max_wait_time:.2f}h | Technicians: {technicians}"
    )
    plt.grid(True)
    plt.ylim(0, max_wait_time if max_wait_time > 0 else 1)
    plt.savefig(os.path.join(results_dir, "priority_vs_wait_time.png"))
    plt.close()

    print(f"Results created: {results_dir}")


if __name__ == "__main__":
    main()
