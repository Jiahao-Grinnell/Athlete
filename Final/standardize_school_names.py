# -*- coding: utf-8 -*-
"""
Created on Thu May 15 10:57:53 2025

@author: dengjiahao
"""

#!/usr/bin/env python3
"""
standardize_school_names.py
------------------------------------------------
Create a canonical school name column (`School_std`) in:

  • Score data_ranked.csv
  • combined_athlete_expenses.csv

Outputs:
  • Score data_ranked_std.csv
  • combined_athlete_expenses_std.csv
"""

import pandas as pd
from pathlib import Path

# ---------------------------------------------------------------------------
# 1. Mapping dictionary: variant → canonical
# ---------------------------------------------------------------------------

SCHOOL_MAP = {
    # Beloit
    "Beloit College":        "Beloit College",
    "Beloit":                "Beloit College",

    # Carroll
    "Carroll University":    "Carroll University",
    "Carroll":               "Carroll University",

    # Cornell
    "Cornell College":       "Cornell College",
    "Cornell":               "Cornell College",

    # Grinnell
    "Grinnell College":      "Grinnell College",
    "Grinnell":              "Grinnell College",

    # Illinois
    "Illinois College":      "Illinois College",
    "Illinois C.":           "Illinois College",
    "Illinois Col.":         "Illinois College",

    # Knox
    "Knox College":          "Knox College",
    "Knox":                  "Knox College",
    "Know":                  "Knox College",   # typo

    # Lake Forest
    "Lake Forest College":   "Lake Forest College",
    "Lake Forest":           "Lake Forest College",

    # Lawrence
    "Lawrence University":   "Lawrence University",
    "Lawrence":              "Lawrence University",
    "Lawerence":             "Lawrence University",  # typo

    # Monmouth
    "Monmouth College":      "Monmouth College",
    "Monmouth":              "Monmouth College",

    # Ripon
    "Ripon College":         "Ripon College",
    "Ripon":                 "Ripon College",

    # St / Saint Norbert
    "St. Norbert College":   "St. Norbert College",
    "St. Norbert":           "St. Norbert College",
    "Saint Norbert College": "St. Norbert College",

    # University of Chicago
    "University of Chicago": "University of Chicago",
}

# ---------------------------------------------------------------------------
# 2. Utility
# ---------------------------------------------------------------------------

def standardize_school_column(df, col="School"):
    """
    Return a copy of *df* with a new column `<col>_std` that holds the
    canonical spelling. Unmapped values are left unchanged.
    """
    df = df.copy()
    df[f"{col}_std"] = (
        df[col]
          .astype(str)
          .str.strip()
          .map(SCHOOL_MAP)
          .fillna(df[col])          # keep original if unseen
    )
    return df

# ---------------------------------------------------------------------------
# 3. Main processing
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).parent

FILES = [
    ("Score data_ranked.csv",          "Score data_ranked_std.csv"),
    ("combined_athlete_expenses.csv",  "combined_athlete_expenses_std.csv"),
]

def main():
    for infile, outfile in FILES:
        in_path  = DATA_DIR / infile
        out_path = DATA_DIR / outfile

        if not in_path.exists():
            print(f"[WARN] {infile} not found – skipped")
            continue

        df = pd.read_csv(in_path)
        df = standardize_school_column(df, col="School")
        df.to_csv(out_path, index=False)

        print(f"✓ {infile} → {outfile}  "
              f"({df['School_std'].nunique()} unique schools after cleanup)")

if __name__ == "__main__":
    main()
