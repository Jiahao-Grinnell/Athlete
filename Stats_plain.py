import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

# Base URL
base_url = "https://pioneers.grinnell.edu/sports/2012/4/14/WGOLF_0414125417.aspx"

# Headers for HTTP requests
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Root folder for storing the data
root_folder = "Golf"
os.makedirs(root_folder, exist_ok=True)

# Step 1: Fetch the main page
response = requests.get(base_url, headers=headers)
if response.status_code != 200:
    print("Failed to fetch the main page")
    exit()
soup = BeautifulSoup(response.text, "html.parser")

# Step 2: Extract season links
season_links = soup.find("div", {"class": "article-content"}).find_all("a")
season_mapping = {link.text.strip(): link["href"] for link in season_links}

# Step 3: Iterate through each season
for season, link in season_mapping.items():
    # Create a folder for the season
    season_folder = os.path.join(root_folder, season.replace(" ", "_"))
    os.makedirs(season_folder, exist_ok=True)

    # Fetch the season page
    season_url = requests.compat.urljoin(base_url, link)
    season_response = requests.get(season_url, headers=headers)
    if season_response.status_code != 200:
        print(f"Failed to fetch season page for {season}")
        continue
    season_soup = BeautifulSoup(season_response.text, "html.parser")

    # Step 4: Process each category
    stat_links = season_soup.find_all("a", text=["Season Statistics", "Team Results", "Individual Results", "Career statistics"])
    for stat_link in stat_links:
        stat_name = stat_link.text.strip().lower()
        print(f"Processing {stat_name} for {season}")

        # Create a folder for the category
        stat_folder = os.path.join(season_folder, stat_name.replace(" ", "_"))
        os.makedirs(stat_folder, exist_ok=True)

        # Fetch the category page
        stat_url = requests.compat.urljoin(season_url, stat_link["href"])
        stat_response = requests.get(stat_url, headers=headers)
        if stat_response.status_code != 200:
            print(f"Failed to fetch {stat_name} page for {season}")
            continue
        stat_soup = BeautifulSoup(stat_response.text, "html.parser")

        # Handle Team Results
        if "team results" in stat_name:
            tables = stat_soup.find_all("table")[1:]  # Skip the first table
            for table in tables:
                title_element = table.find_previous("b")
                if not title_element:
                    print("Missing title for a table, skipping...")
                    continue

                title_text = title_element.text.strip()

                try:
                    # Convert the table to a pandas DataFrame
                    df = pd.read_html(str(table))[0]

                    # Clean the file name using the title
                    file_name = re.sub(r"[^\w\s-]", "", title_text).replace(" ", "_")
                    table_filename = os.path.join(stat_folder, f"{file_name}.csv")

                    # Save the table
                    df.to_csv(table_filename, index=False)
                    print(f"Saved table for {title_text} in {season}")
                except Exception as e:
                    print(f"Failed to process table for {title_text} in {season}: {e}")

        # Handle Individual Results and Career Statistics
        elif "individual results" in stat_name or "career statistics" in stat_name:
            player_sections = stat_soup.find_all("b")
            for section in player_sections:
                player_name = section.text.strip()
                table = section.find_next("table")
                if not table:
                    continue

                try:
                    # Skip invalid names
                    if re.search(r'\d', player_name) or " " not in player_name:
                        print(f"Skipping table for invalid player name: {player_name}")
                        continue

                    # Convert the table to a pandas DataFrame
                    df = pd.read_html(str(table))[0]

                    # Save the table with the player's name
                    table_filename = os.path.join(stat_folder, f"{player_name.replace(' ', '_')}.csv")
                    df.to_csv(table_filename, index=False)
                    print(f"Saved table for player {player_name} in {season}")
                except Exception as e:
                    print(f"Failed to process table for {player_name} in {season}: {e}")

        # Handle Season Statistics
        elif "season statistics" in stat_name:
            tables = stat_soup.find_all("table")
            for idx, table in enumerate(tables):
                try:
                    df = pd.read_html(str(table))[0]
                    table_filename = os.path.join(stat_folder, f"table_{idx + 1}.csv")
                    df.to_csv(table_filename, index=False)
                    print(f"Saved season stats table {idx + 1} in {season}")
                except Exception as e:
                    print(f"Failed to process season stats table {idx + 1} in {season}: {e}")

        else:
            print(f"Unrecognized category {stat_name} for {season}")

print("All data has been processed and saved.")
