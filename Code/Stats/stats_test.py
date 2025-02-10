import os
import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
from io import StringIO

# ---------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------
BASE_URL = "https://pioneers.grinnell.edu/sports/womens-volleyball/stats"
OUTPUT_FOLDER = "Volleyball"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/85.0.4183.121 Safari/537.36'
}

# ---------------------------------------------------------------
# FETCH BASE PAGE
# ---------------------------------------------------------------
print(f"Fetching {BASE_URL}")
resp = requests.get(BASE_URL, headers=headers)
resp.raise_for_status()

soup = bs(resp.text, "html.parser")

# ---------------------------------------------------------------
# FIND SEASON DROPDOWN
# ---------------------------------------------------------------
season_dropdown = soup.find("select", {"id": "ctl00_cplhMainContent_seasons_ddl"})
if not season_dropdown:
    raise ValueError("Could not find the season dropdown on the page.")

season_options = season_dropdown.find_all("option")
seasons = []

for option in season_options:
    season_value = option.get("value", "").strip()
    season_text = season_value.split('/')[-1]
    #print(season_text)
    #print('------------------------------------')
    if season_value and season_text.lower() != "select a season...":
        # Construct correct URL for the season
        season_url = f"{BASE_URL}/{season_value.split('/')[-1]}"
        seasons.append((season_text, season_url))


# ---------------------------------------------------------------
# ITERATE THROUGH SEASONS
# ---------------------------------------------------------------
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

for season_text, season_url in seasons:
    print(f"\n=== Processing season: {season_text} ===")
    try:
        season_resp = requests.get(season_url, headers=headers)
        season_resp.raise_for_status()
        season_soup = bs(season_resp.text, "html.parser")
    except Exception as e:
        print(f"Failed to fetch season {season_text}: {e}")
        continue

    # -----------------------------------------------------------
    # FIND ALL UL WITH ROLE="TABLIST"
    # -----------------------------------------------------------
    ul_elements = season_soup.find_all("ul")
    print(f"Found {len(ul_elements)} <ul> elements")

    for ul_idx, ul in enumerate(ul_elements, start=1):
        a_elements = ul.find_all("a")
        print(f"<a> #{ul_idx}: Found {len(a_elements)} <a> elements.")

        season_folder = os.path.join(OUTPUT_FOLDER, season_text.replace("/", "_"))
        os.makedirs(season_folder, exist_ok=True)
        for a_i, a in enumerate(a_elements):
            href=a.get("href")
            try:
                if('#' in href):
                    section_id = href.strip("#")
                    current_section = season_soup.find("section", {"id": section_id})
                    table = current_section.find("table")
                    if not table:
                        continue

                    # Parse the table
                    df = pd.read_html(StringIO(str(table)))[0]
                    safe_name = f"{season_text}_{section_id}".replace(" ", "_").replace("/", "_")
                    csv_filename = f"{safe_name}.csv"
                    csv_path = os.path.join(season_folder, csv_filename)
                    df.to_csv(csv_path, index=False)
                    print(f"     -> Saved table to: {csv_path}")

            except Exception as e:
                print(e)
                continue


print("\nAll done!")
