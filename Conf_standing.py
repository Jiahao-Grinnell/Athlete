# -*- coding: utf-8 -*-
"""
Created on Mon Feb 10 15:33:07 2025

@author: dengjiahao
"""

import os
import csv
import requests
from bs4 import BeautifulSoup

# -------------------------------------------------------------------
# 1) SETUP
# -------------------------------------------------------------------
BASE_URL = "https://midwestconference.org"
START_URL = f"{BASE_URL}/standings.aspx?path=wvball"
ROOT_FOLDER = "Volleyball"

# Spoof a browser User-Agent to avoid blocks
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/87.0.4280.66 Safari/537.36"
    )
}

os.makedirs(ROOT_FOLDER, exist_ok=True)

# -------------------------------------------------------------------
# 2) FETCH THE MAIN PAGE & FIND THE SEASON DROPDOWN
# -------------------------------------------------------------------
response = requests.get(START_URL, headers=HEADERS)
response.raise_for_status()
soup = BeautifulSoup(response.text, "html.parser")

# The dropdown has id="ctl00_cplhMainContent_ddl_past_standings"
season_select = soup.find("select", id="ctl00_cplhMainContent_ddl_past_standings")
if not season_select:
    print("No season dropdown found.")
    raise SystemExit

options = season_select.find_all("option")

# -------------------------------------------------------------------
# 3) LOOP OVER EACH <option> (SEASON)
# -------------------------------------------------------------------
for opt in options:
    # The text might look like '2023-24 Men's Basketball Standings'
    season_text = opt.get_text(strip=True)
    # The value might be something like '327'
    standings_value = opt.get("value", "").strip()
    
    # Skip if it's an empty or placeholder option
    if not standings_value:
        continue

    # Build the season‐specific URL, e.g. ?standings=327
    season_url = f"{BASE_URL}/standings.aspx?standings={standings_value}"
    print(f"Scraping '{season_text}' => {season_url}")

    # Fetch that season page
    resp = requests.get(season_url, headers=HEADERS)
    resp.raise_for_status()
    season_soup = BeautifulSoup(resp.text, "html.parser")

    # -----------------------------------------------------------------
    # 4) FIND THE STANDINGS TABLE
    # -----------------------------------------------------------------
    table = season_soup.find("table", class_="sidearm-table sidearm-standings-table")
    if not table:
        print(f"No standings table found for {season_text}. Skipping.")
        continue

    # -----------------------------------------------------------------
    # 5) EXTRACT HEADERS
    # -----------------------------------------------------------------
    headers_row = []
    thead = table.find("thead")
    if thead:
        ths = thead.find_all("th")
        headers_row = [th.get_text(strip=True) for th in ths]

    # -----------------------------------------------------------------
    # 6) SCRAPE <tbody> ROWS
    # -----------------------------------------------------------------
    rows_data = []
    tbody = table.find("tbody")
    if not tbody:
        print(f"No <tbody> in table for {season_text}.")
        continue

    # Go through each row
    all_tr = tbody.find_all("tr")
    for tr in all_tr:
        tds = tr.find_all("td")
        row_texts = [td.get_text(strip=True) for td in tds]

        # If the number of columns doesn't match the header length, skip
        if len(row_texts) != len(headers_row):
            # Skipping avoids dict‐field mismatch in the CSV
            print("Skipping a row that doesn't match header columns.")
            continue

        # Otherwise build a dict mapping each header -> the cell text
        row_dict = dict(zip(headers_row, row_texts))
        rows_data.append(row_dict)

    # -----------------------------------------------------------------
    # 7) WRITE THIS SEASON'S RESULTS TO CSV
    # -----------------------------------------------------------------
    # Safely format the season text for a filename
    # e.g. '2023-24 Men's Basketball Standings' => '2023'
    safe_season_text = season_text.replace(" ", "_").replace("’", "")[:4]
    csv_filename = os.path.join(ROOT_FOLDER, f"{safe_season_text}.csv")

    if rows_data:
        fieldnames = list(rows_data[0].keys())
        with open(csv_filename, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows_data:
                writer.writerow(row)
        print(f"Saved CSV => {csv_filename}")
    else:
        with open(csv_filename, "w", encoding="utf-8") as f:
            f.write("")
        print(f"Empty table. Wrote empty CSV => {csv_filename}")

print("Done scraping!")
