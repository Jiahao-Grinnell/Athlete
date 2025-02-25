import os
import csv
import requests
from bs4 import BeautifulSoup

# -----------------------------------------------------------------------------
# 1) SETUP: URL, HEADERS, FOLDER
# -----------------------------------------------------------------------------
BASE_URL = "https://riponredhawks.com"
sport="baseball"
START_URL = f"{BASE_URL}/sports/{sport}/schedule"  # The main schedule page
ROOT_FOLDER = "all_seasons_data"

# Spoof a browser User-Agent to avoid 404/blocks on default Python requests
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/87.0.4280.66 Safari/537.36"
    )
}

# Make sure the root folder exists
os.makedirs(ROOT_FOLDER, exist_ok=True)

# -----------------------------------------------------------------------------
# 2) GET MAIN PAGE & FIND DROPDOWN
# -----------------------------------------------------------------------------
response = requests.get(START_URL, headers=headers)
response.raise_for_status()  # if 404 or other error, it will raise here
soup = BeautifulSoup(response.text, "html.parser")

season_select = soup.find("select", id="sidearm-schedule-select-season")
if not season_select:
    print("No season dropdown found on the page.")
    # Stop here if there's no dropdown
    raise SystemExit

# -----------------------------------------------------------------------------
# 3) ITERATE OVER EACH <option> (SEASON)
# -----------------------------------------------------------------------------
options=season_select.find_all("option")
l=[]
for opt in options:
    season_text = opt.get_text(strip=True)
    season_text=season_text[0:4]
    l.append(season_text)
    if not season_text:
        continue  # skip if it's blank or a placeholder

    # Build season URL with ?grid=true
    season_url = f"{BASE_URL}/sports/{sport}/schedule/{season_text}?grid=true"
    print(f"---\nScraping season: '{season_text}' => {season_url}")

    # Fetch season page
    try:
        season_resp = requests.get(season_url, headers=headers)
        season_resp.raise_for_status()
    except requests.HTTPError as err:
        print(f"Failed to fetch {season_url} -- {err}")
        continue

    season_soup = BeautifulSoup(season_resp.text, "html.parser")

    # -------------------------------------------------------------------------
    # 4) SCRAPE "SEASON RECORD"
    # -------------------------------------------------------------------------
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

    # Debug check:
    # print("Record data:", record_data)

    # -------------------------------------------------------------------------
    # 5) SCRAPE SCHEDULE TABLE
    # -------------------------------------------------------------------------
    schedule_data = []  # list of dicts (one per row/game)

    # 1) Find the <table> element (adjust the class if needed):
    schedule_table = season_soup.find(
        "table",
        class_="sidearm-table sidearm-table-grid-template-1 sidearm-table-grid-template-1-breakdown-large dataTable no-footer"
    )
    
    if schedule_table:
        # 2) Extract column headers from <thead>
        headers_row = []
        thead = schedule_table.find("thead")
        if thead:
            th_cells = thead.find_all("th")
            headers_row = [th.get_text(strip=True) for th in th_cells]
    
        # 3) Gather all <tr> in the table *outside* <thead>, as there's no <tbody>
        all_tr = schedule_table.find_all("tr")
        for tr in all_tr:
            # Skip <tr> that appear in <thead> (so we don't parse headers as data)
            if tr.find_parent("thead"):
                continue
    
            # Grab the row’s <td> (or <th>) cells
            cells = tr.find_all(["td", "th"])
            row_texts = [c.get_text(strip=True) for c in cells]
    
            # If the number of headers matches the number of cells, zip them
            if len(headers_row) == len(row_texts):
                row_dict = dict(zip(headers_row, row_texts))
            else:
                # fallback: label columns generically
                row_dict = {f"col_{i}": val for i, val in enumerate(row_texts)}
    
            schedule_data.append(row_dict)
    
    else:
        print("No matching schedule table found on page.")
    
    # Now 'schedule_data' has one dictionary per row/game.
    #print("Schedule data:", schedule_data)


    # Debug check:
    # print("Schedule data:", schedule_data)

    # -------------------------------------------------------------------------
    # 6) WRITE CSV FILES
    # -------------------------------------------------------------------------
    # Create a folder named exactly after this season (to avoid mixing).
    season_text=season_text[0:4]
    season_folder = os.path.join(ROOT_FOLDER, season_text)
    os.makedirs(season_folder, exist_ok=True)

    record_csv_path = os.path.join(season_folder, f"{season_text}_record.csv")
    schedule_csv_path = os.path.join(season_folder, f"{season_text}_schedule.csv")

    # Write record data
    if record_data:
        fieldnames = list(record_data[0].keys())
        with open(record_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in record_data:
                writer.writerow(row)
    else:
        # create empty file
        with open(record_csv_path, "w", newline="", encoding="utf-8") as f:
            f.write("")

    # Write schedule data
    if schedule_data:
        fieldnames = list(schedule_data[0].keys())
        with open(schedule_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in schedule_data:
                writer.writerow(row)
    else:
        # create empty file
        with open(schedule_csv_path, "w", newline="", encoding="utf-8") as f:
            f.write("")

print("Done scraping!")
