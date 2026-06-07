# datagen.py

A script for reading and generating synthetic vehicle repair job data.

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

## Usage

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

To embed generation parameters in the CSV, pass the distributions to `write_synthetic_data()`:

```python
def main():
    rt_dist = FieldDistribution(distribution="uniform", min=1, max=4)
    p_dist = FieldDistribution(distribution="normal", min=1, max=10, mean=7)
    df = generate_synthetic_data(repair_time_dist=rt_dist, priority_dist=p_dist)
    filename = write_synthetic_data(df, repair_time_dist=rt_dist, priority_dist=p_dist)
```

This adds a `generation_params` column populated only on the first row, e.g.:

```
repair_time: uniform(min=1, max=4) | priority: normal(min=1, max=10, mean=7.0, std=1.5)
```

All other rows leave the column blank so it does not affect data processing.

## Data Schema

| Column | Type | Description |
|---|---|---|
| `job_id` | string | Unique job identifier (e.g. J1, J2, ...) |
| `repair_type` | string | Type of repair |
| `repair_time_hours` | int | Estimated time to complete |
| `priority` | int | Job priority score |
| `generation_params` | string | *(synthetic files only)* Distribution parameters used to generate the data. Populated on the first row only; blank for all other rows. |
