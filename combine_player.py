import os
import pandas as pd

root_dir = 'Roster'  # Top-level folder containing Men and Women
all_dfs = []

for gender in ['Men', 'Women']:
    gender_path = os.path.join(root_dir, gender)
    if not os.path.isdir(gender_path):
        continue

    for sport in os.listdir(gender_path):
        sport_path = os.path.join(gender_path, sport)
        if not os.path.isdir(sport_path):
            continue

        for filename in os.listdir(sport_path):
            if filename.lower().endswith('.csv'):
                file_path = os.path.join(sport_path, filename)

                # Read CSV, skip the first row, read columns as text
                df = pd.read_csv(file_path, skiprows=1, dtype=str)

                # Normalize column names (uppercase, strip spaces)
                df.columns = [col.strip().upper() for col in df.columns]

                # Rename "NAME" -> "FULL NAME" if present
                if 'NAME' in df.columns:
                    df.rename(columns={'NAME': 'FULL NAME'}, inplace=True)

                # Ensure "FULL NAME" exists
                if 'FULL NAME' not in df.columns:
                    print(f"Skipping {file_path}: no 'FULL NAME' or 'NAME' column found.")
                    continue

                # Find the hometown column(s)
                hometown_cols = [
                    col for col in df.columns 
                    if "HOMETOWN" in col and "HIGH SCHOOL" in col
                ]
                if not hometown_cols:
                    print(f"Skipping {file_path}: no 'HOMETOWN / HIGH SCHOOL' column found.")
                    continue
                hometown_col = hometown_cols[0]  # Take the first match

                # Rename it to "HOMETOWN / HIGH SCHOOL"
                df.rename(columns={hometown_col: 'HOMETOWN / HIGH SCHOOL'}, inplace=True)

                # Replace "/" with missing (pd.NA) in the hometown column
                df['HOMETOWN / HIGH SCHOOL'].replace('/', pd.NA, inplace=True)

                # Add identifying columns
                df['Gender'] = gender
                df['Sport'] = sport

                # Keep only the columns we care about
                needed_cols = ['FULL NAME', 'HOMETOWN / HIGH SCHOOL', 'Gender', 'Sport']
                df = df[needed_cols]

                all_dfs.append(df)

if not all_dfs:
    print("No CSV files found with the required columns.")
else:
    combined_df = pd.concat(all_dfs, ignore_index=True)

    # Drop duplicates based on FULL NAME only, keeping the first row
    combined_df.drop_duplicates(subset=['FULL NAME'], keep='first', inplace=True)

    # Save to CSV
    output_file = 'combined_roster.csv'
    combined_df.to_csv(output_file, index=False)
    print(f"Combined roster file created: {output_file}")
