# -*- coding: utf-8 -*-
"""
Created on Tue Feb 11 10:44:28 2025

@author: dengjiahao
"""

import os
import csv
import re

# Path to the top-level folder “Standing”
BASE_DIR = "Standing"

# Final CSV output path
OUTPUT_CSV = "all_schools_rankings.csv"

# We'll store all results here. Each entry will be a dict:
# {
#   "Gender": ...,
#   "Sport": ...,
#   "Year": ...,
#   "School": ...,
#   "CPct.": ...,
#   "Pct.": ...,
#   "Ranking": ...
# }
results = []

# 1) Traverse the folder structure
for gender in ["Men", "Women"]:
    gender_path = os.path.join(BASE_DIR, gender)
    if not os.path.isdir(gender_path):
        continue  # skip if folder doesn't exist
    
    # Each subfolder is presumably a “Sport”
    for sport_name in os.listdir(gender_path):
        sport_path = os.path.join(gender_path, sport_name)
        if not os.path.isdir(sport_path):
            continue
        
        # CSV files for each year
        for csv_file in os.listdir(sport_path):
            if not csv_file.lower().endswith(".csv"):
                continue
            
            # Extract year from filename. For example: "2021.csv" => "2021"
            year = os.path.splitext(csv_file)[0]
            
            csv_path = os.path.join(sport_path, csv_file)
            
            # 2) Read CSV
            rows = []
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    rows.append(r)
            
            if not rows:
                continue  # skip empty CSV files
            
            # 3) Convert CPct. and Pct. to float
            for r in rows:
                # If your data might have "55%" in CPct. or Pct., strip it
                cpct_raw = r.get("CPct.", "").replace("%", "")
                pct_raw  = r.get("Pct.", "").replace("%", "")
                try:
                    r["CPct."] = float(cpct_raw)
                except ValueError:
                    r["CPct."] = 0.0
                try:
                    r["Pct."] = float(pct_raw)
                except ValueError:
                    r["Pct."] = 0.0
            
            # 4) Sort rows (descending) by CPct. first, then Pct.
            rows_sorted = sorted(
                rows, 
                key=lambda x: (x["CPct."], x["Pct."]),
                reverse=True
            )
            
            # 5) For each row in sorted order, assign a rank
            for idx, row_data in enumerate(rows_sorted):
                rank = idx + 1
                # Remove special characters in school names
                raw_school = row_data.get("School", "")
                # For example, remove anything not word-char or whitespace:
                cleaned_school = re.sub(r"[^\w\s]", "", raw_school)
                
                # Build the final record
                record = {
                    "Gender": gender,
                    "Sport": sport_name,
                    "Year": year,
                    "School": cleaned_school,
                    "CPct.": row_data["CPct."],
                    "Pct.": row_data["Pct."],
                    "Ranking": rank
                }
                results.append(record)

# 6) Write the final CSV with all schools
fieldnames = ["Gender", "Sport", "Year", "School", "CPct.", "Pct.", "Ranking"]
with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as out_f:
    writer = csv.DictWriter(out_f, fieldnames=fieldnames)
    writer.writeheader()
    for row in results:
        writer.writerow(row)

print(f"Done! Wrote data for all schools to '{OUTPUT_CSV}'.")
