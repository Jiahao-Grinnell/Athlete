import os
import re
import pandas as pd

# Folder containing all CSV files for each school
school_expenses_folder = "School Expenses"

# Sports to keep in the final output
valid_sports = {
    "Baseball",
    "Basketball",
    "Cross Country",
    "Football",
    "Golf",
    "Soccer",
    "Swimming and Diving",
    "Tennis",
    "Track and Fields",  # we combine indoor/outdoor
    "Softball",
    "Volleyball"
}

def parse_column_name(col_name):
    """
    Extract (Sport, Gender) from a column header, for example:
      "Track and Field X Country Women's Team Expenses" -> ("Cross Country", "Women")
      "Baseball Men's Team Expenses" -> ("Baseball", "Men")
      "Track and Field Indoor Women's Team Expenses" -> ("Track and Fields", "Women")

    Returns (sport, gender), or (None, None) if not recognized.
    """

    # Normalize curly quotes (’ -> ')
    col_norm = col_name.replace("’", "'").strip()
    col_lower = col_norm.lower()

    # Must end with "team expenses" to be considered
    if not col_lower.endswith("team expenses"):
        return None, None

    # Detect gender (check "women's" first to avoid "woMEN's" substring)
    if "women's" in col_lower:
        gender = "Women"
    elif "men's" in col_lower:
        gender = "Men"
    else:
        return None, None  # could handle "coed" or "total" if needed

    # Strip away trailing "Men's Team Expenses" or "Women's Team Expenses" (case-insensitive)
    pattern = r"(?:Men's|Women's)\s+Team\s+Expenses$"
    base_sport = re.sub(pattern, "", col_norm, flags=re.IGNORECASE).strip()

    # Special cases
    if base_sport.lower() == "track and field x country":
        # rename to Cross Country
        sport = "Cross Country"
    elif base_sport.lower() in ["track and field indoor", "track and field outdoor"]:
        # unify to Track and Fields (we'll sum them later)
        sport = "Track and Fields"
    else:
        sport = base_sport

    return sport, gender


# Collect final rows from all files
all_rows = []

for filename in os.listdir(school_expenses_folder):
    if not filename.lower().endswith(".csv"):
        continue  # Skip non-CSV files
    
    file_path = os.path.join(school_expenses_folder, filename)
    
    # We'll take the base file name (minus ".csv") as the School name
    school_name = os.path.splitext(filename)[0]

    # Read CSV with all columns as text
    df = pd.read_csv(file_path, dtype=str)

    # Find the Survey Year column
    possible_year_cols = [col for col in df.columns if "Survey Year" in col]
    if not possible_year_cols:
        print(f"Skipping {filename}: no column containing 'Survey Year'.")
        continue
    year_col = possible_year_cols[0]

    # Convert year to string (already strings, but let's be sure)
    df[year_col] = df[year_col].astype(str)

    # We will extract expense columns by scanning each column name
    extracted_frames = []
    for col in df.columns:
        sport, gender = parse_column_name(col)
        if sport is None or gender is None:
            continue  # Not a recognized sports-expense column

        # Convert expenses to numeric for summation (especially for track indoor/outdoor)
        expenses = pd.to_numeric(df[col], errors='coerce').fillna(0)

        temp_df = pd.DataFrame({
            "Year": df[year_col],
            "Gender": gender,
            "Sport": sport,
            "School": school_name,
            "Expense": expenses
        })
        extracted_frames.append(temp_df)

    if not extracted_frames:
        # No recognized sports columns in this CSV
        continue

    # Combine columns from this file into one "long" DataFrame
    file_long_df = pd.concat(extracted_frames, ignore_index=True)

    # Combine indoor/outdoor track expenses by grouping 
    # (since they both got labeled "Track and Fields")
    file_long_df = file_long_df.groupby(
        ["Year", "Gender", "Sport", "School"], as_index=False
    )["Expense"].sum()

    # Remove rows with 0 expense
    file_long_df = file_long_df[file_long_df["Expense"] != 0]

    # Keep only the sports we want
    file_long_df = file_long_df[file_long_df["Sport"].isin(valid_sports)]

    # Add to the list of all rows
    all_rows.append(file_long_df)

# Combine everything across all schools
if not all_rows:
    print("No valid expense data found in any file.")
    combined_df = pd.DataFrame(columns=["Year", "Gender", "Sport", "School", "Expense"])
else:
    combined_df = pd.concat(all_rows, ignore_index=True)

# Reorder columns if needed
combined_df = combined_df[["Year", "Gender", "Sport", "School", "Expense"]]

# Also remove any 0 expense rows if they slipped through
combined_df = combined_df[combined_df["Expense"] != 0]

# Save final data to CSV
output_file = "all_expenses.csv"
combined_df.to_csv(output_file, index=False)
print(f"Final combined expenses saved to: {output_file}")
