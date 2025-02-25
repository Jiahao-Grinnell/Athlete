import os
import pandas as pd

root_dir = 'Ripon'
combined_dfs = []

for gender in ['Men', 'Women']:
    gender_path = os.path.join(root_dir, gender)
    if not os.path.isdir(gender_path):
        continue

    for sport in os.listdir(gender_path):
        sport_path = os.path.join(gender_path, sport)
        if not os.path.isdir(sport_path):
            continue

        for year in os.listdir(sport_path):
            year_path = os.path.join(sport_path, year)
            if not os.path.isdir(year_path):
                continue

            for filename in os.listdir(year_path):
                # Check if the file is a CSV containing "record"
                if "record" in filename.lower() and filename.lower().endswith('.csv'):
                    file_path = os.path.join(year_path, filename)
                    
                    # Read all columns as text
                    df = pd.read_csv(file_path, dtype=str)

                    if 'Category' not in df.columns or 'Value' not in df.columns:
                        print(f"Skipping {file_path}: missing 'Category'/'Value' columns.")
                        continue

                    # Drop duplicates in 'Category', keeping the first occurrence
                    df = df.drop_duplicates(subset=['Category'], keep='first')

                    # Pivot: each Category becomes one column, and the single row is its Value
                    # If there's still a duplicate, pivoting will fail, but presumably we fixed that.
                    df_wide = df.set_index('Category')['Value'].to_frame().T
                    df_wide.reset_index(drop=True, inplace=True)

                    # Add identifying columns
                    df_wide['Gender'] = gender
                    df_wide['Sport'] = sport
                    df_wide['Year'] = year

                    combined_dfs.append(df_wide)

# Concatenate all "wide" DataFrames
if combined_dfs:
    combined_df = pd.concat(combined_dfs, ignore_index=True)
    combined_df.to_csv('combined_records.csv', index=False)
    print("Combined CSV file created: combined_records.csv")
else:
    print("No valid data to combine.")
