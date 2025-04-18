import os
import pandas as pd

def get_pct_cpct_from_record(csv_path):
    """
    Reads the record CSV (which has 9 rows, 2 columns).
    Returns (pct, cpct) from:
      - 3rd row (1-based) ⇒ df.iloc[2] in 0-based => 'Pct'
      - 5th row (1-based) ⇒ df.iloc[4] in 0-based => 'CPct'
    Returns None, None if the file is empty or invalid.
    """
    try:
        df = pd.read_csv(csv_path, header=None)
        # If the CSV is empty or doesn't have enough rows/cols, skip it
        if df.shape[0] < 5 or df.shape[1] < 2:
            return None, None
        
        pct = df.iloc[2, 1]
        cpct = df.iloc[4, 1]

        # Attempt conversion to float (skip if fails)
        return float(pct), float(cpct)

    except Exception as e:
        print(f"Error reading '{csv_path}': {e}")
        return None, None

def dense_rank_cpct_pct(group):
    """
    Performs a 'dense rank' on the group, which must already be sorted by 
    CPct descending, then Pct descending.
    
    If (CPct,Pct) changes, increment rank; if they are the same, keep the same rank.
    """
    ranks = []
    rank_val = 1
    last_cpct, last_pct = None, None

    for idx, row in group.iterrows():
        cpct_val = row["CPct"]
        pct_val  = row["Pct"]
        if (cpct_val, pct_val) != (last_cpct, last_pct):
            # new combination => increment rank
            ranks.append(rank_val)
            rank_val += 1
            last_cpct, last_pct = cpct_val, pct_val
        else:
            # same combination => same rank
            ranks.append(rank_val - 1)

    group["Ranking"] = ranks
    return group

def main():
    # Root directory that contains all the schools
    SCHEDULE_DIR = "Schedule"

    # We'll store each row of final data in a list of dicts
    records_list = []

    # --- 1) Traverse the folder structure ---
    # Schedule/SchoolName/Gender/Sport/Year/record.csv
    for school_name in os.listdir(SCHEDULE_DIR):
        school_path = os.path.join(SCHEDULE_DIR, school_name)
        if not os.path.isdir(school_path):
            continue

        for gender_name in os.listdir(school_path):
            gender_path = os.path.join(school_path, gender_name)
            if not os.path.isdir(gender_path):
                continue

            for sport_name in os.listdir(gender_path):
                sport_path = os.path.join(gender_path, sport_name)
                if not os.path.isdir(sport_path):
                    continue

                for year_folder in os.listdir(sport_path):
                    year_path = os.path.join(sport_path, year_folder)
                    if not os.path.isdir(year_path):
                        continue

                    # Find the CSV that has "record" in its name
                    for file_name in os.listdir(year_path):
                        if "record" in file_name.lower() and file_name.lower().endswith(".csv"):
                            record_csv = os.path.join(year_path, file_name)
                            pct, cpct = get_pct_cpct_from_record(record_csv)

                            # Append data if valid
                            if pct is not None and cpct is not None:
                                records_list.append({
                                    "School": school_name,
                                    "Gender": gender_name,
                                    "Sport": sport_name,
                                    "Year": year_folder,
                                    "Pct": pct,
                                    "CPct": cpct
                                })

    # --- 2) Build a DataFrame ---
    df = pd.DataFrame(records_list)
    if df.empty:
        print("No valid record data found.")
        return

    # --- 3) Sort by (Gender, Sport, Year, CPct desc, Pct desc) ---
    df.sort_values(
        by=["Gender", "Sport", "Year", "CPct", "Pct"],
        ascending=[True, True, True, False, False],
        inplace=True
    )

    # --- 4) Group by (Gender, Sport, Year) and apply a custom dense rank ---
    # We must not change the order inside each group when we apply the function,
    # so use group_keys=False and let the group remain in the sorted order:
    df = df.groupby(["Gender", "Sport", "Year"], group_keys=False).apply(dense_rank_cpct_pct)

    # If desired, re-sort by (Gender, Sport, Year, Ranking) for final readability
    df.sort_values(
        by=["Gender", "Sport", "Year", "Ranking"],
        ascending=[True, True, True, True],
        inplace=True
    )

    # --- 5) Write to Excel or CSV ---
    output_excel_path = "all_schools_rankings.xlsx"
    df.to_excel(output_excel_path, index=False)

    output_csv_path = "all_schools_rankings.csv"
    df.to_csv(output_csv_path, index=False)

    print(f"Done! Compiled data saved to:\n  {output_excel_path}\n  {output_csv_path}")

if __name__ == "__main__":
    main()
