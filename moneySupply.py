from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta
import time
import os
from pathlib import Path
import pandas as pd
from bs4 import BeautifulSoup
from io import StringIO
from exchangeRatesScraper import ensure_clean_folder,require,checkBoxClick,set_date,click_button


URL = "https://www.cbsl.lk/eResearch/"
DOWNLOAD_DIR = Path(os.getcwd()) / "Data_moneySupply"


def select_daily(driver, criteria_id):
    try:
        dropdown = WebDriverWait(driver, 60).until(
            lambda d: d.find_element(By.ID, criteria_id)
        )
        Select(dropdown).select_by_value("D")  # "D" = Daily
        return True
    except Exception as e:
        print(f"[daily] failed: {e}")
        return False


def run_once(driver, from_date, to_date) -> bool:
    try:
        driver.get(URL)

        WebDriverWait(driver, 60).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        # Step 1: Checkbox
        require(checkBoxClick(driver,
                "ContentPlaceHolder1_grdSubjects_MonitorySector_chkIsSelect_0"),
                "Monetary Sector checkbox")
        print("Step 1: Initial checkbox clicked")

        # Step 2: Frequency = Daily
        require(select_daily(driver, "ContentPlaceHolder1_drpFrequency"),
                "Select Daily")
        print("Step 2: Daily frequency selected")

        # Step 3: Date range
        require(set_date(driver, "ContentPlaceHolder1_txtDateFrom", from_date), "From date")
        require(set_date(driver, "ContentPlaceHolder1_txtDateTo", to_date), "To date")
        print("Step 3: Date range entered")

        # Step 4: Next button
        require(click_button(driver, "ContentPlaceHolder1_btnNext2"), "Next2")
        print("Step 4: Clicked Next")

        # Step 5: Show All (JS click to avoid Selenium issues)
        el = WebDriverWait(driver, 60).until(
         EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_chkshowAll"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true); arguments[0].click();", el)
        print("Step 5: Show All clicked (JS)")

        # Step 6: Select all checkboxes
        wait = WebDriverWait(driver, 60)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='checkbox'][id='chkSelect']")))
        for cb in driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox'][id='chkSelect']"):
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", cb)
            if cb.is_enabled() and cb.is_displayed() and not cb.is_selected():
                cb.click()
        print("Step 6: All chkSelect clicked")

        # Step 7: Add button
        require(click_button(driver, "add"), "Add button")
        print("Step 7: Add clicked")

        # Step 8: Next button
        require(click_button(driver, "ContentPlaceHolder1_btnNext"), "Final Next")
        print("Step 8: Next clicked")

        return True
    except Exception as e:
        print(f"[run] aborting this attempt: {e}")
        return False


def clean_data_direct(driver):
    """Scrape the table directly from the page after adding items (skipping Excel download)."""
    try:
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        table = soup.find("table", {"id": "ContentPlaceHolder1_grdResult"})
        if not table:
            print("No table found on the page.")
            return None

        df = pd.read_html(StringIO(str(table)), header=0)[0]
        df = df.dropna(axis=1, how="all")

        # Keep only rows where at least one data column has numeric values
        data_cols = df.columns[1:]  # all except first column
        df = df[df[data_cols].apply(lambda row: pd.to_numeric(row, errors='coerce').notna().any(), axis=1)]

        # Melt wide -> long format
        df_long = df.melt(id_vars=[df.columns[0]], var_name="Date", value_name="Value")
        df_long.rename(columns={df.columns[0]: "Indicator"}, inplace=True)

        # Convert Value to numeric, drop rows that are still non-numeric
        df_long["Value"] = pd.to_numeric(df_long["Value"], errors="coerce")
        df_long = df_long.dropna(subset=["Value"])

        # Parse dates
        df_long["Date"] = pd.to_datetime(df_long["Date"], errors="coerce")

        # Save CSV
        output_path = DOWNLOAD_DIR / "open_market_operations_clean_direct.csv"
        df_long.to_csv(output_path, index=False)
        print(f"💾 Cleaned CSV saved at: {output_path}")

        return df_long

    except Exception as e:
        print(f"Failed to process table directly: {e}")
        return None


def main():
    ensure_clean_folder(DOWNLOAD_DIR)
    to_date = datetime.now().strftime("%Y-%m-%d")
    from_date = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
    os.makedirs("Data", exist_ok=True)

    opts = Options()
    opts.add_argument("--window-size=1280,900")
    opts.add_argument("--headless=new")
    opts.add_experimental_option("prefs", {
        "download.default_directory": str(DOWNLOAD_DIR),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    try:
        if run_once(driver, from_date, to_date):
            print("✅ Table ready, scraping directly…")
            df_clean = clean_data_direct(driver)  # ✅ Only pass driver
            if df_clean is not None:
                print("📊 Cleaned DataFrame preview:")
                print(df_clean.head())
        else:
            print("❌ Failed to run scraping.")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
