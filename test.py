from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
import pandas as pd
import time

# =====================
# 1. SETUP THE DRIVER
# =====================
options = webdriver.ChromeOptions()

# OPTIONAL (especially in Docker or Linux):
# options.add_argument("--no-sandbox")            # NEW (uncomment if needed)
# options.add_argument("--disable-dev-shm-usage") # NEW (uncomment if needed)

# OPTIONAL: Run headless with a large window size if desired:
# options.add_argument("--headless")              # NEW
# options.add_argument("--window-size=1920,1080") # NEW

# Otherwise, maximize the window so the entire page is visible:
options.add_argument("--start-maximized")  # CHANGED

# Instantiate the driver with our options
driver = webdriver.Chrome(options=options)

# Navigate to the webpage
url = "https://pioneers.grinnell.edu/alltime.aspx?path=wvball&record_type=opponents"
file_name='Volleyball.csv'
driver.get(url)

# Give the page a moment to load all resources
time.sleep(5)  # CHANGED (adjust based on your network/browser speed)
wait = WebDriverWait(driver, 10)

# List/dictionary for storing extracted data
data = []

# =====================
# 2. MAIN SCRAPING LOOP
# =====================

# Get the initial list of rows (the script re-finds them each iteration)
all_rows = driver.find_elements(By.CSS_SELECTOR, 'tr[data-identifier="Overall"]')
print(f"Found {len(all_rows)} total 'Overall' rows.")

for idx in range(len(all_rows)):
    try:
        # Re-find rows each iteration to avoid stale references
        all_rows = driver.find_elements(By.CSS_SELECTOR, 'tr[data-identifier="Overall"]')
        row = all_rows[idx]

        # Scroll the row into view (avoid hidden or overlapped elements)
        driver.execute_script("arguments[0].scrollIntoView(true);", row)  # CHANGED

        # Wait for this row to be clickable
        wait.until(EC.element_to_be_clickable((
            By.XPATH, f'(//tr[@data-identifier="Overall"])[{idx+1}]'
        )))

        # Click the row to open its modal
        ActionChains(driver).move_to_element(row).click().perform()

        # Wait for the modal container to appear
        wait.until(EC.presence_of_element_located((By.ID, 'record_table')))

        # ========== NEW BLOCK: Wait for at least 1 row in the table if it exists ==========
        try:
            # We'll wait up to 5 seconds for at least one <tr> to appear inside #record_table
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#record_table table tr"))
            )
        except:
            # If no rows appear within 5 seconds, we assume the table is legitimately empty.
            pass
        # =================================================================================

        # Now grab the HTML of #record_table
        modal_table = driver.find_element(By.ID, 'record_table')
        modal_html = modal_table.get_attribute('outerHTML')

        # Parse the modal content with BeautifulSoup
        soup = BeautifulSoup(modal_html, 'html.parser')

        # Select all table rows within the modal's <table>
        table_rows = soup.select('table tr')  # CHANGED
        table_data = []

        for tr in table_rows:
            # Extract text from each cell
            cells = [cell.get_text(strip=True) for cell in tr.find_all(['td', 'th'])]
            table_data.append(cells)

        # Log how many rows we found in the modal
        print(f"Row {idx+1}: Found {len(table_rows)} rows in modal.")  # NEW

        # If no rows were found, print partial HTML for debugging
        if not table_rows:
            print(f"Row {idx+1}: Modal HTML snippet:\n{modal_html[:500]}...\n")  # NEW

        # Append the extracted data to our master list
        data.append({
            "Identifier": f"Overall_{idx + 1}",
            "TableData": table_data
        })

        # =====================
        # CLOSING THE MODAL
        # =====================
        try:
            # Wait for the close button to be clickable
            close_button = wait.until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'ui-dialog-titlebar-close'))
            )

            # Scroll the close button into view, then do a short pause for transitions
            driver.execute_script("arguments[0].scrollIntoView(true);", close_button)  # CHANGED
            time.sleep(0.5)  # NEW: small buffer in case of CSS transitions

            # Force-click with JS to bypass "Element click intercepted" errors
            driver.execute_script("arguments[0].click();", close_button)  # CHANGED

            # Wait until the modal disappears
            wait.until(EC.invisibility_of_element_located((By.ID, 'record_table')))

        except Exception as close_err:
            print(f"[WARNING] Could not close modal at row {idx+1}: {close_err}")

        print(f"Row {idx+1} processed successfully.\n")

    except Exception as e:
        print(f"Error processing row {idx+1}: {e}")
        # If the browser is lost or crashed, you might want to break:
        # break

# =====================
# 3. SAVE TO CSV
# =====================
if data:
    flattened_data = []
    for entry in data:
        identifier = entry["Identifier"]
        for row_data in entry["TableData"]:
            flattened_data.append([identifier] + row_data)

    df = pd.DataFrame(flattened_data)
    df.to_csv(file_name, index=False, header=False)
    print("Data has been successfully saved to all_overall_data.csv!")
else:
    print("No data extracted.")

# =====================
# 4. QUIT THE DRIVER
# =====================
driver.quit()
