import os
import csv
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

driver = webdriver.Chrome()
try:
    # 1) Navigate to the roster page
    driver.get("https://pioneers.grinnell.edu/sports/womens-volleyball/roster")
    driver.maximize_window()

    # Make a folder for CSVs
    folder_name = "Volleyball"
    os.makedirs(folder_name, exist_ok=True)

    # 2) Count how many season options there are
    seasons_dropdown = Select(driver.find_element(By.ID, "ddl_past_rosters"))
    total_options = len(seasons_dropdown.options)

    for i in range(total_options):
        # a) Re-locate seasons dropdown each iteration
        seasons_dropdown = Select(driver.find_element(By.ID, "ddl_past_rosters"))
        option = seasons_dropdown.options[i]

        season_text = option.text.strip()
        season_value = option.get_attribute("value")

        # Optionally skip placeholder
        # if not season_value or "choose" in season_text.lower():
        #     continue

        print(f"Processing season: {season_text} (value={season_value})")

        # b) Select the season, click the second "Go" button
        seasons_dropdown.select_by_index(i)
        go_button = driver.find_element(By.XPATH, "//button[@data-bind='click: updateRoster']")
        go_button.click()

        # c) Wait a moment or explicitly wait for page update
        time.sleep(2)  # or use WebDriverWait if needed

        # d) Now RE-SELECT the first dropdown to "Grid" (value="2"),
        #    because it might have reset after the season changed.
        view_dropdown = Select(driver.find_element(By.ID, "sidearm-roster-select-template-dropdown"))
        view_dropdown.select_by_value("2")

        # e) Click the first "Go" button to apply the Grid view
        view_button = driver.find_element(By.ID, "sidearm-roster-select-template-button")
        view_button.click()

        # f) Wait until the grid table reappears
        #    Adjust this selector if needed. Many pages use:
        #    table.sidearm-table-grid-template-1  or  table.table-roster
        try:
            table = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table.sidearm-table-grid-template-1"))
            )
        except:
            print(f"Could not find 'Grid' table for season: {season_text}, skipping.")
            continue

        # g) Scrape the table: caption, thead, and tbody
        # --- Caption ---
        try:
            caption_el = table.find_element(By.TAG_NAME, "caption")
            caption_text = caption_el.text.strip()
        except:
            caption_text = ""

        # --- Headers (<th> in <thead>) ---
        thead_el = table.find_element(By.TAG_NAME, "thead")
        th_elems = thead_el.find_elements(By.TAG_NAME, "th")
        header_texts = [th.text.strip() for th in th_elems]

        # --- Body rows (<tr> in <tbody>) ---
        tbody_el = table.find_element(By.TAG_NAME, "tbody")
        row_els = tbody_el.find_elements(By.TAG_NAME, "tr")

        all_rows = []
        for row_el in row_els:
            cells = row_el.find_elements(By.TAG_NAME, "td")
            row_data = [cell.text.strip() for cell in cells]
            if any(row_data):
                all_rows.append(row_data)

        # h) Build a filename from the season text
        safe_season_name = (
            season_text
            .replace("/", "_")
            .replace("\\", "_")
            .replace(" ", "_")
            .replace(":", "_")
        )
        csv_path = os.path.join(folder_name, f"{safe_season_name}.csv")

        # i) Write to CSV
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            # Optional: put caption as first row
            writer.writerow([caption_text])
            # Next row: column headers
            writer.writerow(header_texts)
            # Then the data rows
            for row_data in all_rows:
                writer.writerow(row_data)

        print(f"Saved CSV for season: {season_text} -> {csv_path}")

finally:
    driver.quit()
