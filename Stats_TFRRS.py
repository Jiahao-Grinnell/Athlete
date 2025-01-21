import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

# Base URL
base_url = "https://www.tfrrs.org/teams/xc/IA_college_f_Grinnell.html"

# Headers for HTTP requests
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Root folder for storing the data
root_folder = "Cross Country"
os.makedirs(root_folder, exist_ok=True)

# Step 1: Fetch the main page
response = requests.get(base_url, headers=headers)
if response.status_code != 200:
    print("Failed to fetch the main page")
    exit()
soup = BeautifulSoup(response.text, "html.parser")

# Step 2: Extract dropdown options
dropdown = soup.find("select", {"name": "config_hnd"})
options = dropdown.find_all("option")
season_mapping = {option.text.strip(): option["value"] for option in options}

# Step 3: Iterate through each season
for season, value in season_mapping.items():
    # Create a folder for the season inside the root folder
    season_folder = os.path.join(root_folder, season.replace(" ", "_"))
    os.makedirs(season_folder, exist_ok=True)

    # Simulate a form submission to select the season
    season_url = f"{base_url}?config_hnd={value}"
    season_response = requests.get(season_url, headers=headers)
    if season_response.status_code != 200:
        print(f"Failed to fetch season page for {season}")
        continue
    season_soup = BeautifulSoup(season_response.text, "html.parser")

    # Step 4: Locate buttons by <a> text
    button_texts = ["TOP QUALIFIERS (POP)", "TOP PERFORMANCES", "ALL PERFORMANCES"]
    buttons = []

    for a in season_soup.find_all("a"):
        if a.text.strip().upper() in button_texts:
            buttons.append(a)

    if not buttons:
        print(f"No buttons found for season {season}")
        continue

    # Step 5: Process each button
    for button in buttons:
        button_name = button.text.strip().replace(" ", "_")
        
        # Create a folder for each button under the season folder
        button_folder = os.path.join(season_folder, button_name)
        os.makedirs(button_folder, exist_ok=True)

        # Fetch the linked page
        link = button["href"]
        full_link = requests.compat.urljoin(base_url, link)
        linked_page_response = requests.get(full_link, headers=headers)
        if linked_page_response.status_code != 200:
            print(f"Failed to fetch page for button {button_name} in {season}")
            continue
        linked_page_soup = BeautifulSoup(linked_page_response.text, "html.parser")

        # Step 6: Locate table blocks and extract titles and tables
        table_blocks = linked_page_soup.find_all("div", {"class": "col-lg-12"})
        if not table_blocks:
            print(f"No table blocks found for {button_name} in {season}")
            continue

        for idx, block in enumerate(table_blocks):
            # Extract the title
            title_element = block.find("h3")
            if not title_element:
                print(f"Missing title in table block {idx + 1} for {button_name} in {season}")
                continue
            table_title = title_element.text.strip()

            # Extract the table
            table_element = block.find("table")
            if not table_element:
                print(f"Missing table in table block {idx + 1} for {button_name} in {season}")
                continue

            try:
                # Convert the table to a pandas DataFrame
                df = pd.read_html(str(table_element))[0]

                # Clean and validate the table title for file naming
                table_title = re.sub(r'[<>:"/\\|?*]', '_', table_title)
                csv_filename = os.path.join(button_folder, f"{table_title}.csv")

                # Save the DataFrame to a CSV file
                df.to_csv(csv_filename, index=False)
                print(f"Saved table '{table_title}' for {button_name} in {season}")
            except Exception as e:
                print(f"Failed to process table '{table_title}' for {button_name} in {season}: {e}")

print("All data has been processed and saved.")
