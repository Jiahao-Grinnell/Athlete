# -*- coding: utf-8 -*-
"""
Created on Mon Feb 10 16:39:26 2025

@author: dengjiahao
"""

import os
import csv

# Path to the top-level folder “Standing”
BASE_DIR = "Standing"

# Final CSV output path
OUTPUT_CSV = "grinnell_rankings.csv"

# We'll store results here as a list of dicts or tuples
results = []

# 1) Traverse the folder structure
#    e.g. Standing/Men/<sport>/<year>.csv
for gender in ["Men", "Women"]:
    gender_path = os.path.join(BASE_DIR, gender)

    # Check that the path exists
    if not os.path.isdir(gender_path):
        continue  # Skip if folder not found

    # Each subfolder is a “sport” name
    for sport_name in os.listdir(gender_path):
        sport_path = os.path.join(gender_path, sport_name)
        if not os.path.isdir(sport_path):
            continue  # skip if it's not a directory

        # Now, each file inside is presumably something like 2021.csv, 2022.csv, etc.
        for csv_file in os.listdir(sport_path):
            if not csv_file.lower().endswith(".csv"):
                continue  # skip non-csv

            # Try to parse the year from filename
            # e.g. '2021.csv' => year = '2021'
            # or '2023_something.csv' => year = '2023'
            filename_no_ext = os.path.splitext(csv_file)[0]
            # Use the first 4 digits if you like, or parse differently
            year = filename_no_ext[:4]  # simplest approach

            csv_path = os.path.join(sport_path, csv_file)

            # 2) Read the CSV file
            rows = []
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                # We expect columns: "School", "CPct.", "Pct." etc.
                # We'll gather all rows in a list
                for r in reader:
                    rows.append(r)

            if not rows:
                # If file is empty, skip it
                continue

            # 3) Convert “CPct.” and “Pct.” to numeric so we can sort
            #    If it fails, you can skip or handle them differently
            for r in rows:
                try:
                    r["CPct."] = float(r["CPct."].strip("%"))  # If there's a % sign, remove it
                except:
                    r["CPct."] = 0.0
                try:
                    r["Pct."] = float(r["Pct."].strip("%"))
                except:
                    r["Pct."] = 0.0

            # 4) Sort the rows: first by CPct. descending, then Pct. descending
            #    We can use the `sorted` function with a tuple key
            rows_sorted = sorted(
                rows,
                key=lambda r: (r["CPct."], r["Pct."]),
                reverse=True
            )

            # 5) Find Grinnell in the sorted list & determine rank
            #    The “rank” is basically index + 1 in the sorted list
            #    We’ll assume the “School” column or “Team” column identifies the row
            grinnell_rank = None
            grinnell_cpct = None
            grinnell_pct = None

            for idx, row_data in enumerate(rows_sorted):
                # Compare in a case-insensitive way if needed
                if "grinnell" in row_data["School"].lower():
                    grinnell_rank = idx + 1  # rank is index+1 in sorted order
                    grinnell_cpct = row_data["CPct."]
                    grinnell_pct = row_data["Pct."]
                    break  # Found it, no need to keep looping

            # If we found Grinnell, store that result in our final list
            if grinnell_rank is not None:
                results.append({
                    "Gender": gender,
                    "Sport": sport_name,
                    "Year": year,
                    "CPct.": grinnell_cpct,
                    "Pct.": grinnell_pct,
                    "Ranking": grinnell_rank
                })
            else:
                # If Grinnell is not found, optionally skip or do something else
                pass

# 6) Write the final output
fieldnames = ["Gender", "Sport", "Year", "CPct.", "Pct.", "Ranking"]

with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as out_f:
    writer = csv.DictWriter(out_f, fieldnames=fieldnames)
    writer.writeheader()

    # For each result in “results”
    for r in results:
        writer.writerow(r)

print(f"Done! Final CSV => {OUTPUT_CSV}")
