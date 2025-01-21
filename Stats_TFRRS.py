import os
import requests
from bs4 import BeautifulSoup
import pandas as pd

# Base URL
base_url = "https://www.tfrrs.org/teams/tf/IA_college_f_Grinnell.html"

# Headers for the HTTP requests
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Step 1: Define root folder
root_folder = "Track and Field"
os.makedirs(root_folder, exist_ok=True)

# Step 2: Fetch the main page
response = requests.get(base_url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

# Step 3: Extract dropdown options
dropdown = soup.find("select", {"name": "config_hnd"})
options = dropdown.find_all("option")
season_mapping = {option.text.strip(): option["value"] for option in options}

# Step 4: Iterate through each season
for season, value in season_mapping.items():
    # Create a folder for the season inside the root folder
    season_folder = os.path.join(root_folder, season.replace(" ", "_"))
    os.makedirs(season_folder, exist_ok=True)

    # Simulate a form submission to select the season
    season_url = f"{base_url}?season_hnd={value}"
    season_response = requests.get(season_url, headers=headers)
    season_soup = BeautifulSoup(season_response.text, "html.parser")

    # Step 5: Extract buttons and their hyperlinks
    buttons = season_soup.find_all("a", {"class": "btn-panel-lg"})
    for button in buttons:
        button_name = button.text.strip().replace(" ", "_")
        
        # Create a folder for each button under the season folder
        button_folder = os.path.join(season_folder, button_name)
        os.makedirs(button_folder, exist_ok=True)

        link = button["href"]

        # Fetch the linked page
        full_link = requests.compat.urljoin(base_url, link)
        linked_page_response = requests.get(full_link, headers=headers)
        linked_page_soup = BeautifulSoup(linked_page_response.text, "html.parser")

        # Step 6: Extract all tables
        tables = linked_page_soup.find_all("table")
        table_titles = linked_page_soup.find_all("div", {"class": "custom-table-title"})
        
        for idx, (table, title_div) in enumerate(zip(tables, table_titles)):
            # Extract the table title
            table_title = title_div.find("h3", {"class": "font-weight-500"}).text.strip()
            
            # Convert table to a pandas DataFrame
            df = pd.read_html(str(table))[0]

            # Save the DataFrame to a CSV file using the table title
            csv_filename = os.path.join(button_folder, f"{table_title}.csv")
            df.to_csv(csv_filename, index=False)

        print(f"Processed {button_name} for season {season}.")
