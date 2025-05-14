#!/usr/bin/env python3
"""
rank_scores.py
---------------------------------------------------------
• Drop rows whose Scores are not numeric (e.g., '--', blanks)
• Compute Rank (1 = highest score) within each Year–Sport–Gender bucket
"""

import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent
IN_FILE  = DATA_DIR / "Score data.csv"
OUT_FILE = DATA_DIR / "Score data_ranked.csv"

def main() -> None:
    # Load original data
    df = pd.read_csv(IN_FILE)

    # Convert Scores to numeric; invalid parses → NaN
    df["Scores"] = pd.to_numeric(df["Scores"], errors="coerce")

    # Remove rows where Scores is NaN (non‑numeric originally)
    df = df.dropna(subset=["Scores"]).copy()

    # Rank (higher Scores ⇒ rank 1) per Year–Sport–Gender group
    df["Rank"] = (
        df.groupby(["Year", "Sport", "Gender"])["Scores"]
          .rank(method="min", ascending=False)
          .astype("Int64")
    )

    # Save results
    df.to_csv(OUT_FILE, index=False)
    print(f"✓ Ranked data written to {OUT_FILE.resolve()}")

if __name__ == "__main__":
    main()
