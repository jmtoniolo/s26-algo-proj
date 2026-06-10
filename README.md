# s26-algo-proj

Tools for generating synthetic vehicle repair job data and comparing job
scheduling algorithms against it.

## Setup

**1. Create and activate a virtual environment**

```bash
python -m venv venv
```

Windows (PowerShell):
```powershell
.\venv\Scripts\Activate.ps1
```

Windows (Command Prompt):
```cmd
venv\Scripts\activate.bat
```

Linux/macOS:
```bash
source venv/bin/activate
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

## Running the scheduler (`main.py`)

Run an algorithm against a job list CSV:

```bash
python main.py <algorithm> <input.csv>
```
Jobs already marked `TRUE` in the CSV `scheduled` column are skipped on subsequent runs. Newly scheduled jobs are written back to the source CSV with `scheduled=TRUE` so the next run ignores them.
`<algorithm>` is one of:

| Algorithm | Description |
|---|---|
| `fifo` | First In, First Out — schedules jobs in the order they appear |
| `priority` | Schedules highest-priority jobs first |
| `sjf` | Shortest Job First — schedules jobs with the lowest `repair_time_hours` first |
| `greedy` | Scores jobs by `priority / repair_time_hours` and schedules the highest scores first |
| `dp` | Solves a 0/1 knapsack-style selection problem: maximize total priority within available technician time |

Example:

```bash
python main.py priority job-list.csv
```

For the `dp` algorithm, you can optionally specify available technician time:

```bash
python main.py dp job-list.csv --capacity 12
```

If `--capacity` is omitted, the dynamic programming scheduler assumes enough time to include all jobs.

Each run computes a `wait_time` for every job (the cumulative `repair_time_hours`
of all jobs scheduled before it, assuming jobs run one at a time) and creates a
timestamped `results<yyyymmddhhmmss>/` directory containing:

- `scheduled_jobs.csv` — the job list in scheduled order with the added `wait_time` column
- `priority_vs_wait_time.png` — a plot of average wait time per priority, with the
  total queue time and overall average wait time shown in the title (the y-axis is
  fixed to `[0, total queue time]` so plots from different algorithms on the same
  dataset are directly comparable)
- `run.log` — a record of the run: timestamp, algorithm, input file, elapsed
  scheduling time, total queue time, and average wait time

The only thing printed to the terminal is the name of the results directory, e.g.:

```
Results created: results20260607182109
```

## Generating & reading data (`datagen.py`)

Run the script directly:

```bash
python datagen.py
```

All data tasks are controlled by editing the `main()` function at the bottom of the script.

### Reading existing data

```python
def main():
    df = read_data("job-list.csv")
    print(df.head())
```

### Generating synthetic data

```python
def main():
    df = generate_synthetic_data()
    print(df.head())
```

By default this generates 100 rows with uniform distributions for both `repair_time_hours` (1–4) and `priority` (1–10).

### Configuring distributions

Use `FieldDistribution` to control the distribution of `repair_time_hours` and `priority`.

**Uniform distribution** — values spread evenly across the range:

```python
FieldDistribution(distribution="uniform", min=1, max=4)
```

**Normal distribution** — values clustered around a mean:

```python
# Mean defaults to the midpoint of min/max
FieldDistribution(distribution="normal", min=1, max=10)

# Explicit mean (e.g. bias towards high priority jobs)
FieldDistribution(distribution="normal", min=1, max=10, mean=7)
```

Pass distributions into `generate_synthetic_data()`:

```python
def main():
    df = generate_synthetic_data(
        num_rows=500,
        repair_time_dist=FieldDistribution(distribution="uniform", min=1, max=8),
        priority_dist=FieldDistribution(distribution="normal", min=1, max=10, mean=7),
        seed=42,  # optional: for reproducible results
    )
    print(df.head())
```

### Saving to CSV

Wrap your `generate_synthetic_data()` call with `write_synthetic_data()` to save the result. The file is automatically timestamped:

```python
def main():
    df = generate_synthetic_data(num_rows=200)
    filename = write_synthetic_data(df)
    print(f"Wrote {len(df)} rows to {filename}")
    # e.g. synthetic_job_list.20260607120000.csv
```

You can also provide a custom base filename:

```python
filename = write_synthetic_data(df, base_filename="high_priority_jobs")
# e.g. high_priority_jobs.20260607120000.csv
```

To record the generation parameters used, pass the distributions to `write_synthetic_data()`:

```python
def main():
    rt_dist = FieldDistribution(distribution="uniform", min=1, max=4)
    p_dist = FieldDistribution(distribution="normal", min=1, max=10, mean=7)
    df = generate_synthetic_data(repair_time_dist=rt_dist, priority_dist=p_dist)
    filename = write_synthetic_data(df, repair_time_dist=rt_dist, priority_dist=p_dist)
```

This writes the parameters as a `#`-prefixed comment line above the CSV header, e.g.:

```
# generation_params: repair_time: uniform(min=1, max=4) | priority: normal(min=1, max=10, mean=7.0, std=1.5)
```

`read_data()` skips comment lines automatically, so the parameters don't show up as a data column when the file is read back.

## Data Schema

| Column | Type | Description |
|---|---|---|
| `job_id` | string | Unique job identifier (e.g. J1, J2, ...) |
| `repair_type` | string | Type of repair |
| `repair_time_hours` | int | Estimated time to complete |
| `priority` | int | Job priority score |
| `scheduled` | string | `TRUE` when the job has been scheduled; empty when unscheduled |
