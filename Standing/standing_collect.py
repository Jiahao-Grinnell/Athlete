import requests
import re
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from requests.utils import requote_uri

# ——— 0) Browser-like headers ———
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/116.0.0.0 Safari/537.36"
    )
}

# ——— 1) Fetch history page ———
history_url = requote_uri(
    "https://midwestconference.org/sports/2010/8/18/GEN_0818103443.aspx?id=86"
)
resp = requests.get(history_url, headers=HEADERS)
resp.raise_for_status()
history_soup = BeautifulSoup(resp.content, "html.parser")

# ——— 2) Discover each “YYYY-YY” link for 2003–2025 (skip 2020) ———
BASE = "https://midwestconference.org"
year_links = {}
for a in history_soup.find_all("a", href=True):
    season = a.get_text(strip=True)
    if re.match(r"^\d{4}-\d{2}$", season):
        start = int(season.split("-")[0])
        if 2003 <= start <= 2025 and start != 2020:
            raw = urljoin(BASE, a["href"])
            year_links[start] = requote_uri(raw)

# ——— 3) Sport code → full name (all keys uppercase) ———
sport_map = {
    "VB":    "Volleyball",
    "SOC":   "Soccer",
    "XC":    "Cross Country",
    "CC":    "Cross Country",      # alternate code
    "TEN":   "Tennis",
    "BKB":   "Basketball",
    "SWIM":  "Swimming",
    "SWM":   "Swimming",           # alternate code
    "ITRK":  "Indoor Track & Field",
    "OTRK":  "Outdoor Track & Field",
    "SB":    "Softball",
    "FB":    "Football",
    "BASE":  "Baseball",
    "BSB":   "Baseball",           # alternate code
    "TOTAL": "Total"               # capture the Total column
}

# ——— 4) Scrape each season’s Men/Women tables ———
records = []
for year in sorted(year_links):
    page = requests.get(year_links[year], headers=HEADERS)
    page.raise_for_status()
    soup = BeautifulSoup(page.content, "html.parser")
    tables = soup.find_all("table")

    for idx, table in enumerate(tables[:2]):
        # first table = Men, second = Women
        gender = "Men" if idx == 0 else "Women"

        # UPDATED: extract header row, catching both <th> and <td> cells
        header_row   = table.find("tr")
        header_cells = header_row.find_all(["th", "td"])
        # skip the first cell (“School”) and uppercase the rest
        codes = [cell.get_text(strip=True).upper() for cell in header_cells[1:]]

        # iterate each data row
        for row in table.find_all("tr")[1:]:
            cells = [td.get_text(strip=True) for td in row.find_all("td")]
            school = cells[0]
            # zip each code with its corresponding rank
            for code, rank in zip(codes, cells[1:]):
                sport_name = sport_map.get(code)
                if sport_name:
                    records.append({
                        "Year":   year,
                        "School": school,
                        "Sport":  sport_name,
                        "Gender": gender,
                        "Rank":   rank
                    })

# ——— 5) Build DataFrame & save ———
df = pd.DataFrame(records)
df.to_csv("midwest_all_sports_standings_2003_2025.csv", index=False)
print(f"Saved {len(df)} rows for {len(year_links)} seasons.")
