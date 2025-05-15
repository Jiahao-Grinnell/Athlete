#!/usr/bin/env python3
# ------------------------------------------------------------
# standardize_sports_and_fix_all.py
# ------------------------------------------------------------
import pandas as pd
from pathlib import Path

# ────────────────────────────────────────────────────────────
# 1) SPORT-NAME MAPPING  (variant ➜ canonical)
# ────────────────────────────────────────────────────────────
SPORT_MAP = {
    # ball sports & others
    "Baseball": "Baseball",
    "Softball": "Softball",
    "Basketball": "Basketball",
    "Football": "Football",
    "Golf": "Golf",
    "Ice Hockey": "Ice Hockey",
    "Lacrosse": "Lacrosse",
    "Soccer": "Soccer",
    "Tennis": "Tennis",
    "Volleyball": "Volleyball",
    "Fencing": "Fencing",
    "Water Polo": "Water Polo",
    "Wrestling": "Wrestling",

    # cross-country / track
    "Cross Country": "Cross Country",
    "Cross_Country": "Cross Country",
    "Track and Field X Country": "Cross Country",
    "Indoor Track & Field": "Track & Field (Indoor)",
    "Track and Field Indoor": "Track & Field (Indoor)",
    "Outdoor Track & Field": "Track & Field (Outdoor)",
    "Track and Field Outdoor": "Track & Field (Outdoor)",
    "Track and Fields": "Track & Field (Outdoor)",
    "All Track Combined": "All Track Combined",

    # swim / dive
    "Swimming": "Swimming & Diving",
    "Diving": "Swimming & Diving",
    "Swimming and Diving": "Swimming & Diving",
    "Swimming & Diving": "Swimming & Diving",

    # total rows
    "Total": "Total",
}

NUMERIC_COLS = ["Total Expense", "Operating Expense"]   # columns to aggregate

# ────────────────────────────────────────────────────────────
# 2) LOAD FILES
# ────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent

score_df  = pd.read_csv(DATA_DIR / "Score data_ranked_std.csv")
exp_df    = pd.read_csv(DATA_DIR / "combined_athlete_expenses_std.csv")
roster_df = pd.read_csv(DATA_DIR / "combined_roster.csv")

# Roster has no School column → inject constant School_std
roster_df["School_std"] = "Grinnell College"

# Ensure School_std exists in the other dataframes
for df in (score_df, exp_df):
    if "School_std" not in df.columns:
        df["School_std"] = df["School"]

# ────────────────────────────────────────────────────────────
# 3) STANDARDISE SPORT NAMES (all three dataframes)
# ────────────────────────────────────────────────────────────
for df in (score_df, exp_df, roster_df):
    df["Sport_std"] = (
        df["Sport"]
          .astype(str)
          .str.strip()
          .map(SPORT_MAP)
          .fillna(df["Sport"])
    )

# ────────────────────────────────────────────────────────────
# 4) EXPENSE-FILE SPECIAL FIXES
# ────────────────────────────────────────────────────────────
clean_blocks = []

for (yr, gender, school), grp in exp_df.groupby(
    ["Year", "Gender", "School_std"], sort=False
):
    grp = grp.copy()

    # 4-A  merge duplicate Swimming & Diving rows
    if (grp["Sport_std"] == "Swimming & Diving").sum() > 1:
        rows = grp[grp["Sport_std"] == "Swimming & Diving"]
        summed = rows[NUMERIC_COLS].sum()
        template = rows.iloc[0].copy()
        template.update(summed)
        grp = grp[grp["Sport_std"] != "Swimming & Diving"]
        grp = pd.concat([grp, template.to_frame().T], ignore_index=True)

    # 4-B  add All Track Combined if missing
    if "All Track Combined" not in grp["Sport_std"].values:
        mask = grp["Sport_std"].isin(
            ["Track & Field (Indoor)", "Track & Field (Outdoor)", "Cross Country"]
        )
        if mask.any():
            summed = grp.loc[mask, NUMERIC_COLS].sum()
            template = grp.iloc[0].copy()
            template["Sport"] = template["Sport_std"] = "All Track Combined"
            template.update(summed)
            grp = pd.concat([grp, template.to_frame().T], ignore_index=True)

    # 4-C  add Total row if missing (avoid double-count)
    if "Total" not in grp["Sport_std"].values:
        exclude = (
            ["Track & Field (Indoor)", "Track & Field (Outdoor)", "Cross Country"]
            if "All Track Combined" in grp["Sport_std"].values
            else []
        )
        sum_mask = ~grp["Sport_std"].isin(["Total"] + exclude)
        summed = grp.loc[sum_mask, NUMERIC_COLS].sum()
        template = grp.iloc[0].copy()
        template["Sport"] = template["Sport_std"] = "Total"
        template.update(summed)
        grp = pd.concat([grp, template.to_frame().T], ignore_index=True)

    clean_blocks.append(grp)

exp_clean = pd.concat(clean_blocks, ignore_index=True)

# ────────────────────────────────────────────────────────────
# 5) SAVE CLEANED DATA
# ────────────────────────────────────────────────────────────
score_df.to_csv(DATA_DIR / "Score data_ranked_clean.csv", index=False)
exp_clean.to_csv(DATA_DIR / "combined_athlete_expenses_clean.csv", index=False)
roster_df.to_csv(DATA_DIR / "combined_roster_clean.csv", index=False)

print("✓ Sport names standardised across scores, expenses, rosters.")
print("✓ Expense file fixed (Swimming & Diving merge, All Track Combined, Total rows).")
print("→  Score data_ranked_clean.csv")
print("→  combined_athlete_expenses_clean.csv")
print("→  combined_roster_clean.csv")
