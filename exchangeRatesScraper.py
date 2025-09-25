from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium.common.exceptions import ElementClickInterceptedException
import os
from datetime import datetime,timedelta
import os
import shutil
from pathlib import Path
import pandas as pd


URL = "https://www.cbsl.lk/eResearch/"


DOWNLOAD_DIR = Path(os.getcwd()) / "Data"

def latest_currency_rates(df,currency):
    """Returns the latest currency rates from the DataFrame."""
    data = df.sort_index(ascending=False)
    latest = data.iloc[0]
    
    date = latest.name
    buying = latest[f"TT Rates -Buying {currency}"]
    selling = latest[f"TT Rates -Selling {currency}"]
    return {
        "date": date.strftime("%Y-%m-%d"),
        "buying": buying,
        "selling": selling
    }

def ensure_clean_folder(folder: Path):
    folder.mkdir(parents=True, exist_ok=True)  # ensure it exists
    for item in folder.iterdir():
        try:
            if item.is_file() or item.is_symlink():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
        except Exception as e:
            print(f"[cleanup] Could not delete {item}: {e}")
            
def clean_data():
    file_path = os.path.join(os.getcwd(), "Data", "data.xls")
    if os.path.exists(file_path):
        try:
            #Since it is downloaded as an xls file, we can use pandas to read it
            #and clean it up
            tables = pd.read_html(file_path)
            
            #Multiple tables are returned, we need to find the one we want
            df = tables[1]
            
            #Removing columns that are completely empty
            df = df.dropna(axis=1, how="all")

            #filtering out only the relavent rows
            df = df[df.iloc[:, 1].astype(str).str.contains("TT Rates", na=False)]

            #changing the index
            df.set_index(df.columns[1], inplace=True)

            #Transposing the DataFrame
            df = df.T[2:]
            
            df.index.name = "Date"

            #Saving the cleaned data to a new file
            df.to_csv(os.path.join(os.getcwd(), "Data", "exchange_rates.csv"))

            
        except Exception as e:
            print(f"Error deleting file: {e}")
    else:
        print(f"File does not exist: {file_path}")

def require(ok: bool, msg: str):
    """Raise an exception if the condition is not met."""
    if not ok:
        raise RuntimeError(msg)

def checkBoxClick(driver, checkbox_id):
    """Checking a checkbox by ID."""
    try:
        el = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, checkbox_id))
        )
        if not el.is_selected():
            el.click()
        return True
    except Exception as e:
        print(f"[checkbox] {checkbox_id} failed: {e}")
        return False

def select_criteria_daily(driver, criteria_id):
    """"Selecting the Daily option criteria from a dropdown by ID."""
    try:
        dropdown = WebDriverWait(driver, 20).until(
            lambda d: d.find_element(By.ID, criteria_id)
        )
        Select(dropdown).select_by_visible_text("Daily")
        return True
    except Exception as e:
        print(f"[daily] failed: {e}")
        return False

def set_date(driver, date_id, date_value):
    """Setting the date for an input field by ID."""
    try:
        date_input = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, date_id))
        )
        date_input.clear()
        date_input.send_keys(date_value)
        return True
    except Exception as e:
        print(f"[date] {date_id} failed: {e}")
        return False

def click_button(driver, button_id):
    """Clicking a button by ID"""
    try:
        btn = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, button_id))
        )
        btn.click()
        return True
    except Exception as e:
        print(f"[click] {button_id} failed: {e}")
        return False

def run_once(driver, from_date, to_date) -> bool:
    """Run the scraper once, in order to download the exchange rates.
    if it fails, it will return False. and run again after 60 seconds."""
    try:
        driver.get(URL)
        
        #making sure the page is fully loaded
        WebDriverWait(driver, 20).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        
        #Clicking on the "Exchange Rates" checkbox
        require(checkBoxClick(driver, "ContentPlaceHolder1_grdSubjects_ExternalSector_chkIsSelect_4"),
                "Exchange Rates checkbox")
        print("Initial checkbox clicked")

        #Selecting the criteria to be daily
        require(select_criteria_daily(driver, "ContentPlaceHolder1_drpFrequency"),
                "Select Daily")

        #setting the from and to dates
        require(set_date(driver, "ContentPlaceHolder1_txtDateFrom", from_date), "From date")
        require(set_date(driver, "ContentPlaceHolder1_txtDateTo", to_date), "To date")
        print("Date range entered")
        
        # Clicking the "Next" button to proceed
        require(click_button(driver, "ContentPlaceHolder1_btnNext2"), "Next2")

        #Clicking on the list all checkbox
        require(checkBoxClick(driver, "ContentPlaceHolder1_chkshowAll"), "List all")

        #Iterating through all the checkboxes to select them
        #Wait time is increased to 200 since loading multiple records can take time for the server to process resulting in delays and making sure a timeout does not happen.
        wait = WebDriverWait(driver, 5000)
        wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[type='checkbox'][id$='chkSelect']"))
        )
        for cb in driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox'][id$='chkSelect']"):
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", cb)
            if cb.is_enabled() and cb.is_displayed() and not cb.is_selected():
                cb.click()
        print("Required Data selected")

        #proceeding to the next step
        require(click_button(driver, "ContentPlaceHolder1_btnNext"), "Next (selection)")
        #Handling the overlay to add data to proceed to the next step
        yes_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "/html/body/div[1]/div[3]/div/button[1]")))
        yes_button.click()
        time.sleep(2)

        #Clicking the "Next" button to confirm the selection
        require(click_button(driver, "ContentPlaceHolder1_btnNext"), "Next (post-confirm)")
        
        
        wait = WebDriverWait(driver, 5000)
        # Download Button
        btn = wait.until(EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_imgDownload")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        driver.execute_script("window.scrollBy(0, -200);")
        wait.until(EC.element_to_be_clickable((By.ID, "ContentPlaceHolder1_imgDownload")))
        try:
            btn.click()
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", btn)
        print("Download started")
        
        #Giving some time for the download to complete otherwise its going to be an incomplete download    
        time.sleep(15)
        

        return True
    except Exception as e:
        print(f"[run] aborting this attempt: {e}")
        return False

def main():
    ensure_clean_folder(DOWNLOAD_DIR)
    to_date = datetime.now().strftime("%Y-%m-%d")
    from_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d") #higher the load the more time the website takes to load
    os.makedirs("Data", exist_ok=True)

    opts = Options()
    opts.add_argument("--window-size=1280,900")
    opts.add_argument("--headless=new")
    opts.add_experimental_option("prefs", {
        "download.default_directory": os.path.join(os.getcwd(), "Data"),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    try:
        return run_once(driver, from_date, to_date)
    finally:
        driver.quit()

if __name__ == "__main__":
    # retry loop
    while True:
        if main():
            print("Exchange rates downloaded successfully.")
            break
        print("Failed; retrying in 60s…")
        time.sleep(60)
    clean_data()