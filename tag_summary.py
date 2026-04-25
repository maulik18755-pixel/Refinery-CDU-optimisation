# tag_summary.py
# Reads plant_data.csv, prints summary statistics for every tag,
# saves any rows where kerosene yield drops below 18% to a CSV alert file,
# and produces a yield trend chart with low-yield points highlighted in red.

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ── 1. Load the data ─────────────────────────────────────────────────────────
# Read the CSV produced by the SCADA historian into a DataFrame.
df = pd.read_csv("plant_data.csv")

print(f"Loaded {len(df)} rows and {len(df.columns)} columns from plant_data.csv\n")

# ── 2. Print summary statistics for every column ──────────────────────────────
# For each tag, show the mean, minimum, and maximum value across the dataset.
print("=" * 60)
print("TAG SUMMARY STATISTICS")
print("=" * 60)

stats = df.describe().loc[["mean", "min", "max"]]

for col in df.select_dtypes(include="number").columns:
    print(f"\n{col}")
    print(f"  Mean : {stats.loc['mean', col]:.4f}")
    print(f"  Min  : {stats.loc['min',  col]:.4f}")
    print(f"  Max  : {stats.loc['max',  col]:.4f}")

# ── 3. Flag rows where kerosene yield is below 18% ───────────────────────────
# Any minute where kerosene_yield_pct < 18 is considered a low-yield event
# and needs to be reviewed by the process engineer.
YIELD_THRESHOLD = 18.0
YIELD_COL = "kerosene_yield_pct"

if YIELD_COL not in df.columns:
    print(f"\nWARNING: Column '{YIELD_COL}' not found in plant_data.csv. "
          "Check the column name and re-run.")
else:
    low_yield = df[df[YIELD_COL] < YIELD_THRESHOLD]

    print(f"\n{'=' * 60}")
    print(f"LOW-YIELD ALERT  (threshold: {YIELD_THRESHOLD}%)")
    print(f"{'=' * 60}")
    print(f"Rows flagged : {len(low_yield)} of {len(df)} "
          f"({100 * len(low_yield) / len(df):.1f}%)")

    # ── 4. Save flagged rows to results/low_yield_alerts.csv ─────────────────
    # Create the results folder if it doesn't already exist, then write the
    # alert rows so the engineer can investigate each low-yield event offline.
    os.makedirs("results", exist_ok=True)
    output_path = os.path.join("results", "low_yield_alerts.csv")
    low_yield.to_csv(output_path, index=False)
    print(f"Alerts saved  : {output_path}")

    # ── 5. Plot kerosene yield over time ──────────────────────────────────────
    # Convert the timestamp column from plain text into real datetime objects
    # so the x-axis on the chart shows proper time labels.
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    fig, ax = plt.subplots(figsize=(14, 5))

    # Draw the full yield trend as a continuous blue line.
    ax.plot(df["timestamp"], df[YIELD_COL],
            color="steelblue", linewidth=1.5, label="Kerosene yield")

    # Overlay the low-yield points as large red dots so they stand out clearly.
    ax.scatter(df.loc[df[YIELD_COL] < YIELD_THRESHOLD, "timestamp"],
               df.loc[df[YIELD_COL] < YIELD_THRESHOLD, YIELD_COL],
               color="red", zorder=5, s=60, label=f"Below {YIELD_THRESHOLD}% (alert)")

    # Draw a dashed red horizontal line at the alert threshold for reference.
    ax.axhline(YIELD_THRESHOLD, color="red", linestyle="--",
               linewidth=1, alpha=0.6, label=f"Threshold ({YIELD_THRESHOLD}%)")

    # Label the axes and add a title.
    ax.set_xlabel("Timestamp")
    ax.set_ylabel("Kerosene yield (% on feed)")
    ax.set_title("CDU Kerosene Yield Trend")

    # Format the x-axis so timestamps are readable and don't overlap.
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    fig.autofmt_xdate(rotation=45)

    ax.legend()
    ax.grid(True, alpha=0.3)

    # Save the chart to the results folder as a PNG image.
    chart_path = os.path.join("results", "yield_trend.png")
    fig.tight_layout()
    fig.savefig(chart_path, dpi=150)
    plt.close(fig)
    print(f"Chart saved   : {chart_path}")
