# -*- coding: utf-8 -*-
"""
Created on Tue Feb 25 11:46:26 2025

@author: dengjiahao
"""

import os
import csv
import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# 1) SETUP: BASE URL, HEADERS, SPORT LIST & CORRESPONDING ROOT FOLDERS
# ---------------------------------------------------------------------------
BASE_URL = "https://athletics.uchicago.edu/"


switch=1

# Lists for sports and corresponding folder names

sports = ["baseball", "mens-basketball","football","mens-soccer","mens-tennis"]  # Add additional sports as needed

root_folders = ["Baseball", "Basketball","Football","Soccer","Tennis"]


# Lists for sports and corresponding folder names
if(switch==1):
    sports = ["softball", "womens-basketball","womens-volleyball","womens-soccer","womens-tennis"]  # Add additional sports as needed
    
    root_folders = ["Softball", "Basketball","Volleyball","Soccer","Tennis"]




# Spoof a browser User-Agent to avoid blocks
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/87.0.4280.66 Safari/537.36"
    )
}

# Iterate over each sport and its corresponding root folder
for sport, ROOT_FOLDER in zip(sports, root_folders):
    print(f"\n=== Starting scraping for sport: {sport} ===")
    
    # Make sure the root folder for this sport exists
    os.makedirs(ROOT_FOLDER, exist_ok=True)

    # Build the main schedule page URL for the sport
    START_URL = f"{BASE_URL}/sports/{sport}/schedule"
    response = requests.get(START_URL, headers=headers)
    response.raise_for_status()  # Stop if an error occurs
    soup = BeautifulSoup(response.text, "html.parser")

    # -------------------------------------------------------------------------
    # 2) FIND SEASON DROPDOWN
    # -------------------------------------------------------------------------
    season_select = soup.find("select", id="sidearm-schedule-select-season")
    if not season_select:
        print(f"No season dropdown found on the page for {sport}. Skipping...")
        continue

    options = season_select.find_all("option")
    
    # -------------------------------------------------------------------------
    # 3) ITERATE OVER EACH SEASON
    # -------------------------------------------------------------------------
    for opt in options:
        season_text = opt.get_text(strip=True)
        # Assume season_text starts with the year (e.g., "2022-2023")
        season_year = season_text[0:4]
        if not season_year:
            continue  # skip placeholders or empty entries

        # Build the season URL with grid view enabled
        season_url = f"{BASE_URL}/sports/{sport}/schedule/{season_year}?grid=true"
        print(f"---\nScraping season: '{season_year}' => {season_url}")

        try:
            season_resp = requests.get(season_url, headers=headers)
            season_resp.raise_for_status()
        except requests.HTTPError as err:
            print(f"Failed to fetch {season_url} -- {err}")
            continue

        season_soup = BeautifulSoup(season_resp.text, "html.parser")

        # ---------------------------------------------------------------------
        # 4) SCRAPE "SEASON RECORD"
        # ---------------------------------------------------------------------
        record_data = []  # list of dicts, e.g. [{"Category": "Overall", "Value": "15-6"}, ...]
        record_div = season_soup.find("div", class_="sidearm-schedule-record")
        if record_div:
            ul = record_div.find("ul")
            if ul:
                li_tags = ul.find_all("li")
                for li in li_tags:
                    spans = li.find_all("span", class_="flex-item-1")
                    if len(spans) == 2:
                        category = spans[0].get_text(strip=True)
                        value = spans[1].get_text(strip=True)
                        record_data.append({"Category": category, "Value": value})

        # ---------------------------------------------------------------------
        # 5) SCRAPE SCHEDULE TABLE
        # ---------------------------------------------------------------------
        schedule_data = []  # list of dicts (one per row/game)

        # Locate the schedule table
        schedule_table = season_soup.find(
            "table",
            class_="sidearm-table sidearm-table-grid-template-1 sidearm-table-grid-template-1-breakdown-large dataTable no-footer"
        )
        
        if schedule_table:
            # Extract column headers from <thead>
            headers_row = []
            thead = schedule_table.find("thead")
            if thead:
                th_cells = thead.find_all("th")
                headers_row = [th.get_text(strip=True) for th in th_cells]
            
            # Gather all <tr> outside the <thead>
            all_tr = schedule_table.find_all("tr")
            for tr in all_tr:
                if tr.find_parent("thead"):
                    continue  # skip header row

                cells = tr.find_all(["td", "th"])
                row_texts = [c.get_text(strip=True) for c in cells]
                
                # Zip headers with row cells if they match; else, label columns generically
                if len(headers_row) == len(row_texts):
                    row_dict = dict(zip(headers_row, row_texts))
                else:
                    row_dict = {f"col_{i}": val for i, val in enumerate(row_texts)}
                
                schedule_data.append(row_dict)
        else:
            print(f"No matching schedule table found on page for season {season_year}.")

        # ---------------------------------------------------------------------
        # 6) WRITE CSV FILES FOR THE CURRENT SEASON
        # ---------------------------------------------------------------------
        # Create a folder for this season within the sport's root folder
        season_folder = os.path.join(ROOT_FOLDER, season_year)
        os.makedirs(season_folder, exist_ok=True)

        record_csv_path = os.path.join(season_folder, f"{season_year}_record.csv")
        schedule_csv_path = os.path.join(season_folder, f"{season_year}_schedule.csv")

        # Write record data to CSV if available; otherwise, create an empty file
        if record_data:
            fieldnames = list(record_data[0].keys())
            with open(record_csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for row in record_data:
                    writer.writerow(row)
        else:
            with open(record_csv_path, "w", newline="", encoding="utf-8") as f:
                f.write("")

        # Write schedule data to CSV if available; otherwise, create an empty file
        if schedule_data:
            fieldnames = list(schedule_data[0].keys())
            with open(schedule_csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for row in schedule_data:
                    writer.writerow(row)
        else:
            with open(schedule_csv_path, "w", newline="", encoding="utf-8") as f:
                f.write("")

    print(f"=== Finished scraping for sport: {sport} ===")

print("\nDone scraping all sports!")
