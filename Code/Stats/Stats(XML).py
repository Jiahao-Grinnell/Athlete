import os
import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
from collections import deque

# ------------------------------------------------------------------------------
# 1) CONFIGURATION
# ------------------------------------------------------------------------------
BASE_URL = "https://pioneers.grinnell.edu/sports/baseball/stats"
root_folder = "Baseball"

cookies = {
    '_gid': 'GA1.2.1531733898.1726155099',
    '_gat_tracker0': '1',
    '_gat_tracker1': '1',
    '_gat_UA-180696617-1': '1',
    '_gat_UA-195038689-23': '1',
    '_ga_H93C57BJPL': 'GS1.1.1726155098.1.1.1726155224.0.0.0',
    '_ga': 'GA1.1.281465299.1726155099',
    '_ga_Y29PC3P5S9': 'GS1.1.1726155099.1.1.1726155224.60.0.0',
    '_ga_E0ST6N2X43': 'GS1.2.1726155099.1.1.1726155224.0.0.0',
}

headers = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/85.0.4183.121 Safari/537.36'
    )
}

# ------------------------------------------------------------------------------
# 2) FETCH THE BASE "STATS" PAGE & PARSE THE SEASON DROPDOWN
# ------------------------------------------------------------------------------
print(f"Fetching base page: {BASE_URL}")
base_resp = requests.get(BASE_URL, headers=headers, cookies=cookies)
base_resp.raise_for_status()

base_soup = bs(base_resp.text, 'html.parser')

season_select = base_soup.find("select", {"id": "ctl00_cplhMainContent_seasons_ddl"})
if not season_select:
    raise ValueError("Could not find the season dropdown on the base page.")

options = season_select.find_all("option")
season_urls = []

# Derive a "prefix" from BASE_URL for trimming
# E.g. BASE_URL after 'https://pioneers.grinnell.edu/' is "sports/mens-basketball/stats"
base_prefix = BASE_URL.replace("https://pioneers.grinnell.edu/", "")
# Ensure it doesn't start or end with '/', just in case
base_prefix = base_prefix.strip("/")

print("Base prefix for trimming:", base_prefix)

for opt in options:
    raw_val = (opt.get("value") or "").strip()
    
    # Skip if empty or "Select a Season..."
    if not raw_val or raw_val.lower() == "select a season...":
        continue
    
    # Remove leading slash if present
    raw_val = raw_val.lstrip("/")
    
    # If raw_val starts with the base prefix (like "sports/mens-basketball/stats/..."),
    # remove that prefix so we won't double it in the final URL
    # Example: raw_val = "sports/mens-basketball/stats/2019-20"
    # base_prefix = "sports/mens-basketball/stats"
    # => after removing prefix => "2019-20"
    if raw_val.startswith(base_prefix):
        # remove the prefix from the front
        raw_val = raw_val[len(base_prefix):]
    
    # Also remove any leading slash after that
    raw_val = raw_val.lstrip("/")
    
    # Now raw_val should be something like "2019-20"
    season_url = f"{BASE_URL}/{raw_val}"
    
    # Folder-safe name
    folder_safe_val = raw_val.replace("/", "_")
    
    season_urls.append((folder_safe_val, season_url))

if not season_urls:
    print("No valid season options found in the dropdown.")
    exit()

print("\nFound season options:")
for folder_val, link in season_urls:
    print(f"  - {folder_val} -> {link}")

# ------------------------------------------------------------------------------
# 3) BFS LOGIC: FOR EACH SEASON, PARSE THE PAGE, DISCOVER TABS, EXTRACT TABLES
# ------------------------------------------------------------------------------
os.makedirs(root_folder, exist_ok=True)

for season_val, season_link in season_urls:
    print(f"\n=== Processing season: {season_val} ===")
    
    try:
        season_resp = requests.get(season_link, headers=headers, cookies=cookies)
        if season_resp.status_code != 200:
            print(f"Failed to load {season_link}, status={season_resp.status_code}")
            continue
        season_soup = bs(season_resp.text, 'html.parser')
    except Exception as e:
        print(f"Error retrieving {season_link}: {e}")
        continue

    season_folder = os.path.join(root_folder, season_val)
    os.makedirs(season_folder, exist_ok=True)

    queue = deque()
    visited_paths = set()
    
    # Start BFS with the entire page
    queue.append((season_soup, []))

    while queue:
        current_soup, path_labels = queue.popleft()
        path_tuple = tuple(path_labels)
        if path_tuple in visited_paths:
            continue
        visited_paths.add(path_tuple)

        # Create a folder path for these tabs
        path_folder = os.path.join(
            season_folder,
            *[p.replace("/", "_") for p in path_labels]
        )
        os.makedirs(path_folder, exist_ok=True)

        # ----------------------------------------------------------------------
        # Find sub-tabs in the static HTML
        # ----------------------------------------------------------------------
        sub_tabs = []
        ul_lists = current_soup.find_all("ul", {"role": "tablist"})
        for ul in ul_lists:
            li_tab = ul.find_all("li", {"role": "tab"})
            for li in li_tab:
                a_tag = li.find("a")
                if not a_tag:
                    continue
                label = a_tag.get_text(strip=True)
                print(label)
                href = a_tag.get("href") or ""
                if href.startswith("#"):
                    section_id = href.lstrip("#")
                    sub_section = current_soup.find(id=section_id)
                    if sub_section and label:
                        sub_tabs.append((label, sub_section))

        # Deduplicate
        seen_sub = set()
        unique_sub_tabs = []
        for (lbl, sc) in sub_tabs:
            if (lbl, sc) not in seen_sub:
                unique_sub_tabs.append((lbl, sc))
                seen_sub.add((lbl, sc))

        # ----------------------------------------------------------------------
        # If no sub‐tabs, parse tables in this section
        # ----------------------------------------------------------------------
        if not unique_sub_tabs:
            all_tables = current_soup.find_all("table")
            if not all_tables:
                continue  # No tables, just skip

            for idx, table_elem in enumerate(all_tables, start=1):
                try:
                    df = pd.read_html(str(table_elem))[0]
                except:
                    continue  # skip if can't parse

                # Build filename from <caption> or fallback
                cap_el = table_elem.find("caption")
                if cap_el and cap_el.get_text(strip=True):
                    cap_text = cap_el.get_text(strip=True)
                else:
                    cap_text = f"table_{idx}"
                
                safe_name = (
                    cap_text.replace("/", "_")
                            .replace("\\", "_")
                            .replace(" ", "_")
                )
                
                csv_path = os.path.join(path_folder, f"{safe_name}.csv")
                df.to_csv(csv_path, index=False)
                print(f"Saved table to {csv_path}")

        # ----------------------------------------------------------------------
        # Otherwise, we have deeper sub‐tabs; enqueue them
        # ----------------------------------------------------------------------
        else:
            for (lbl, sc) in unique_sub_tabs:
                new_path = path_labels + [lbl]
                queue.append((sc, new_path))

print("\nAll done!")
