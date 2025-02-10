from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
import pandas as pd
import time

# 1. Configure Selenium WebDriver
driver = webdriver.Chrome()  # Make sure ChromeDriver is installed and in your PATH
url = "https://pioneers.grinnell.edu/alltime.aspx?path=wbball&record_type=opponents"
driver.get(url)

# Optional: Give the page a moment to fully load initial resources
time.sleep(5)

# 2. Create a WebDriverWait instance for explicit waits (10 seconds max)
wait = WebDriverWait(driver, 10)

# 3. Locate all rows once to get the count
rows = driver.find_elements(By.CSS_SELECTOR, 'tr[data-identifier="Overall"]')

data = []

# 4. Iterate through each row index
for idx in range(len(rows)):
    try:
        # Re-locate the rows each time in case the DOM changed after closing a modal
        rows = driver.find_elements(By.CSS_SELECTOR, 'tr[data-identifier="Overall"]')
        row = rows[idx]
        print(1)
        # Scroll to the row to ensure it’s within the viewport
        driver.execute_script("arguments[0].scrollIntoView(true);", row)

        # Wait until the row is actually clickable
        wait.until(
            EC.element_to_be_clickable((
                By.XPATH, f'(//tr[@data-identifier="Overall"])[{idx + 1}]'
            ))
        )
        print(2)
        # Use ActionChains for a reliable click
        actions = ActionChains(driver)
        actions.move_to_element(row).click().perform()
        print(3)
        # Wait for the modal’s table to be present
        wait.until(EC.presence_of_element_located((By.ID, 'record_table')))
        print(3)
        # Extract the modal table HTML
        modal_table = driver.find_element(By.ID, 'record_table')
        modal_html = modal_table.get_attribute('outerHTML')
        print(4)
        # Parse the modal content with BeautifulSoup
        soup = BeautifulSoup(modal_html, 'html.parser')
        table_rows = soup.find_all('tr')
        print(5)
        # Extract each row’s text from the table
        table_data = []
        for tr in table_rows:
            cells = [cell.get_text(strip=True) for cell in tr.find_all(['td', 'th'])]
            table_data.append(cells)
        print(6)
        # Store the data in our list
        data.append({
            "Identifier": f"Overall_{idx + 1}",
            "TableData": table_data
        })

        # Close the modal
        close_button = driver.find_element(By.CLASS_NAME, 'ui-dialog-titlebar-close')
        close_button.click()
        print(7)
        # Wait until the modal’s table disappears before moving on
        wait.until(EC.invisibility_of_element_located((By.ID, 'record_table')))

    except Exception as e:
        print(f"Error processing row {idx + 1}: {e}")
        continue

# 5. Save all extracted data to a CSV if we have any
if data:
    # Flatten the data for saving
    flattened_data = []
    for entry in data:
        identifier = entry["Identifier"]
        for row in entry["TableData"]:
            flattened_data.append([identifier] + row)

    # Convert to a DataFrame and save
    df = pd.DataFrame(flattened_data)
    df.to_csv("all_overall_data.csv", index=False, header=False)
    print("Data has been successfully saved to all_overall_data.csv!")
else:
    print("No data extracted.")

# 6. Quit the browser
driver.quit()
