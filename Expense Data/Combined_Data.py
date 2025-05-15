#!/usr/bin/env python3
"""combine_athlete_expenses.py
------------------------------------------------
Creates **combined_athlete_expenses.csv** next to this script, aggregating:

    Year | School | Gender | Sport | Total Expense | Operating Expense | Undergrads

Run by clicking Spyder’s ▶ button—no command‑line args needed.
"""
from __future__ import annotations
import re, sys
from pathlib import Path
import pandas as pd

# Filename patterns
EXPENSE_PATTERN   = re.compile(r"Expenses_All_Sports", re.I)
OPERATING_PATTERN = re.compile(r"Operating_Expenses", re.I)
COL_TOTAL_RE      = re.compile(r"(.+?) (Men's|Women's) Team Expenses$", re.I)
# Map combined track to separate categories
TRACK_MAP = {
    "Track": None,  # base placeholder
    "Indoor": "Indoor",
    "Outdoor": "Outdoor",
    "X Country": "X Country",
    "Cross Country": "X Country",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_table(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path) if path.suffix.lower() == ".csv" else pd.read_excel(path)
    except Exception as exc:
        raise RuntimeError(f"Failed to read '{path.name}': {exc}") from exc


def _extract_tidy(df_total: pd.DataFrame, df_oper: pd.DataFrame) -> pd.DataFrame:
    """Turn the *wide* total/operating sheets into long tidy rows."""
    # locate undergrad columns
    ug_m_col = next((c for c in df_total.columns if re.search(r"Male Undergraduates", c, re.I)), None)
    ug_f_col = next((c for c in df_total.columns if re.search(r"Female Undergraduates", c, re.I)), None)
    if not ug_m_col or not ug_f_col:
        raise RuntimeError("could not detect undergrad columns")

    # build lookup for operating expenses by UNITID and Survey Year
    oper_lookup = df_oper.set_index(["UNITID", "Survey Year"]) if "UNITID" in df_oper.columns and "Survey Year" in df_oper.columns else pd.DataFrame()

    records: List[Dict] = []
    for _, row in df_total.iterrows():
        # match to operating record
        key = (row.get("UNITID"), row.get("Survey Year"))
        row_oper = oper_lookup.loc[key] if key in oper_lookup.index else pd.Series(dtype="object")

        school = row.get("Institution Name", pd.NA)
        year = row.get("Survey Year")
        # skip if essential missing
        if pd.isna(year) or pd.isna(school):
            continue
        year = int(year)

        under_M = row.get(ug_m_col, pd.NA)
        under_F = row.get(ug_f_col, pd.NA)

        for col in df_total.columns:
            m = COL_TOTAL_RE.match(col)
            if not m:
                continue
            sport = m.group(1).strip()
            gender_poss = m.group(2)
            gender = "Men" if gender_poss.lower().startswith("men") else "Women"

            total_exp = row[col]
            oper_col = f"{sport} {gender_poss} Team Operating Expenses"
            oper_exp = row_oper.get(oper_col, pd.NA) if not row_oper.empty else pd.NA
            if pd.isna(total_exp) and pd.isna(oper_exp):
                continue  # skip empty rows

            under_count = under_M if gender == "Men" else under_F
            records.append({
                "Year": year,
                "School": school,
                "Gender": gender,
                "Sport": sport,
                "Total Expense": total_exp,
                "Operating Expense": oper_exp,
                "Undergrads": under_count,
            })
    df = pd.DataFrame.from_records(records)
    # drop any rows missing key fields
    df.dropna(subset=["Total Expense", "Operating Expense", "Undergrads"], inplace=True)
    return df

# ---------------------------------------------------------------------------
# Main (no args)
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent
OUT_FILE = ROOT_DIR / "combined_athlete_expenses.csv"

# find pairs
pairs: list[tuple[Path,Path]] = []
def _pair_in_dir(d: Path):
    t = o = None
    for f in d.iterdir():
        if f.is_file():
            if EXPENSE_PATTERN.search(f.name):
                t = f
            elif OPERATING_PATTERN.search(f.name):
                o = f
    if t and o:
        pairs.append((t,o))
    elif t or o:
        print(f"[WARN] Only one expense file in {d.name} – skipping", file=sys.stderr)

_pair_in_dir(ROOT_DIR)
for sub in ROOT_DIR.iterdir():
    if sub.is_dir():
        _pair_in_dir(sub)

if not pairs:
    sys.exit("[FATAL] No matching expense files found – check folder structure.")

frames: list[pd.DataFrame] = []
for total_p, oper_p in pairs:
    try:
        df_total = _load_table(total_p)
        df_oper  = _load_table(oper_p)
        tidy     = _extract_tidy(df_total, df_oper)
        frames.append(tidy)
        print(f"[OK] {total_p.parent.name or '.'}: collected {len(tidy):,} rows")
    except Exception as exc:
        print(f"[WARN] {total_p.parent.name}: {exc}", file=sys.stderr)

if not frames:
    sys.exit("[FATAL] All files failed to process – nothing to write.")

final = pd.concat(frames, ignore_index=True)
final.sort_values(["School","Year","Gender","Sport"], inplace=True)
final.to_csv(OUT_FILE, index=False)
print(f"[DONE] Wrote {len(final):,} rows → {OUT_FILE.name}")
