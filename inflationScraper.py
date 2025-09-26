# We do NOT use Selenium because the CBSL page is not JS-rendered.
# BeautifulSoup (with requests) is enough to scrape the visible HTML.
# Selenium implmentation is also there, but commented

import requests
import re
from datetime import datetime
from pathlib import Path
import time

import pandas as pd
import streamlit as st
import plotly.express as px
from bs4 import BeautifulSoup as BS

# def _try_import_selenium():
#     try:
#         from selenium import webdriver
#         from selenium.webdriver.chrome.options import Options
#         from selenium.webdriver.support.ui import WebDriverWait
#         return webdriver, Options, WebDriverWait
#     except Exception:
#         return None, None, None

# URLs and settings

TABLE_URL = "https://www.cbsl.gov.lk/cbsl_custom/inflation/inflationwindow.php"
PRESS_URL = "https://www.cbsl.gov.lk/en/measures-of-consumer-price-inflation"

UA = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}

# Month name references
MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]
MONTH_INDEX = {m: i for i, m in enumerate(MONTHS, start=1)}


# Paths for storing cached CSV data
DATA_DIR = Path("Data")
DATA_DIR.mkdir(exist_ok=True)
CSV_OUT = DATA_DIR / "cbsl_inflation_2023_2025.csv"   # inflation data
CSV_PDF = DATA_DIR / "cbsl_inflation_press_links.csv" # press release links

# Helpers for cleaning numbers/text
def norm_minus(s: str) -> str:
    # Normalize minus signs and spaces (web often uses weird unicode chars)
    for bad in ["−", "–", "—", "‒", "﹣", "－"]:
        s = s.replace(bad, "-")
    return s.replace("\u00a0", " ").strip()


def to_float(s: str | None):
    #Convert a string with digits into a float, return None if empty or invalid
    if not s:
        return None
    s = norm_minus(str(s))
    m = re.search(r"-?\d+\.?\d*", s)
    return float(m.group()) if m else None

# Scraper for the inflation numbers
def scrape_text_block() -> str:
#    Fetch visible text from the inflation window page without Selenium
# Retry a few times in case of network hiccups
    for attempt in range(3):
        r = requests.get(TABLE_URL, headers=UA, timeout=30)
        if r.status_code == 200 and r.text.strip():
            break
        time.sleep(1)
    r.raise_for_status()

    soup = BS(r.text, "lxml")

 # Try specific containers first (defensive)
    candidates = [
        soup.select_one("main"),
        soup.select_one("article"),
        soup.select_one("div#content"),
        soup.select_one("div.inflationwindow"),
        soup.select_one("pre"),
    ]
    for node in candidates:
        if node and node.get_text(strip=True):
            return node.get_text("\n", strip=True)

    # Fallback: whole page text
    return soup.get_text("\n", strip=True)

# Selenium scraper
# def scrape_text_block() -> str:
#     """Prefer Selenium to get the full rendered text; fallback to requests+BS."""
#     webdriver, Options, WebDriverWait = _try_import_selenium()
#     if webdriver is not None:
#         try:
#             opts = Options()
#             opts.add_argument("--headless=new")
#             opts.add_argument("--window-size=1280,900")
#             opts.add_argument("--no-sandbox")
#             opts.add_argument("--disable-dev-shm-usage")
#             driver = webdriver.Chrome(options=opts)
#             try:
#                 driver.get(TABLE_URL)
#                 WebDriverWait(driver, 20).until(lambda d: d.execute_script(
#                     "return document.readyState") == "complete")
#                 html = driver.page_source
#                 soup = BS(html, "html.parser")
#                 return soup.get_text("\n", strip=True)
#             finally:
#                 driver.quit()
#         except Exception:
#             pass  # fall back to requests below

#     # Fallback: requests + BS
#     r = requests.get(TABLE_URL, headers=UA, timeout=30)
#     r.raise_for_status()
#     soup = BS(r.text, "lxml")
#     return soup.get_text("\n", strip=True)

# Parser for inflation data
def parse_inflationwindow_text(txt: str) -> pd.DataFrame:
    """
    Parse blocks like:
      2025
      January -4.00 1.20 -4.00 -0.20
      ...
    -> date, ccpi_headline_yoy, ccpi_core_yoy, ncpi_headline_yoy, ncpi_core_yoy
    """
    txt = norm_minus(txt)

# Split by year sections
    blocks = {}
    for year in ["2025", "2024", "2023"]:
        m = re.search(rf"{year}\s+(.*?)(?=202\d|\Z)", txt, flags=re.S)
        if m:
            blocks[int(year)] = m.group(1)

    rows = []
    for year, blob in blocks.items():
        # Find month rows with 4 numeric fields
        for mon in MONTHS:
            mm = re.search(
                rf"{mon}\s+([-\d\.\u2212\u2013\u2014\u2012\uFF0D]+)\s+([-\d\.]+)\s+([-\d\.]+|--)\s+([-\d\.]+|--)",
                blob
            )
            if mm:
                ccpi_head = to_float(mm.group(1))
                ccpi_core = to_float(mm.group(2))
                ncpi_head = to_float(mm.group(3)) if mm.group(
                    3) != "--" else None
                ncpi_core = to_float(mm.group(4)) if mm.group(
                    4) != "--" else None
                dt = pd.to_datetime(f"{mon} {year}")
                rows.append({
                    "date": dt,
                    "year": dt.year,
                    "month": mon,
                    "month_num": MONTH_INDEX[mon],
                    "ccpi_headline_yoy": ccpi_head,
                    "ccpi_core_yoy": ccpi_core,
                    "ncpi_headline_yoy": ncpi_head,
                    "ncpi_core_yoy": ncpi_core
                })
    if not rows:
        return pd.DataFrame()

# Final cleaned dataframe
    df = pd.DataFrame(rows).sort_values("date")
    df = df[(df["date"] >= datetime(2023, 1, 1)) & (
        df["date"] <= datetime(2025, 12, 31))].reset_index(drop=True)
    return df


# Scraper for press release links (PDFs)
def fetch_press_links() -> pd.DataFrame:
    r = requests.get(PRESS_URL, headers=UA, timeout=30)
    r.raise_for_status()
    soup = BS(r.text, "lxml")
    out = []
    for a in soup.select("a[href]"):
        t = (a.get_text() or "").strip()
        m = re.match(
            r"Inflation in (January|February|March|April|May|June|July|August|September|October|November|December) (\d{4}) - CCPI", t)
        if not m:
            continue
        month, year = m.group(1).title(), int(m.group(2))
        if 2023 <= year <= 2025:
            href = a["href"]
            if not href.startswith("http"):
                href = "https://www.cbsl.gov.lk" + href
            if href.lower().endswith(".pdf"):
                out.append({"year": year, "month": month, "pdf_url": href})
    return pd.DataFrame(out)

# Check if cached CSV is still valid
def _csv_is_bad(df: pd.DataFrame | None) -> bool:
    if df is None or df.empty:
        return True
    needed = {"ccpi_headline_yoy", "ccpi_core_yoy",
              "ncpi_headline_yoy", "ncpi_core_yoy"}
    if not needed.issubset(df.columns):
        return True
    tmp = df[list(needed)].replace({"": pd.NA, "—": pd.NA, "--": pd.NA})
    return tmp.isna().all().all()

# Load or scrape data
def _load_or_scrape(force: bool = False):
    df = None
    if CSV_OUT.exists() and not force:
        try:
            df = pd.read_csv(CSV_OUT, parse_dates=["date"])
        except Exception:
            df = None

    if force or _csv_is_bad(df):
        text = scrape_text_block()
        df = parse_inflationwindow_text(text)
        df.to_csv(CSV_OUT, index=False)

    if CSV_PDF.exists() and not force:
        try:
            links = pd.read_csv(CSV_PDF)
        except Exception:
            links = fetch_press_links()
            links.to_csv(CSV_PDF, index=False)
    else:
        links = fetch_press_links()
        links.to_csv(CSV_PDF, index=False)

    return df, links


# Streamlit Dashboard
def render_inflation_page():
    st.header("Inflation (CCPI / NCPI) — Y-o-Y (2023–2025)")
    
     # Load data (cached or scraped)
    df, links = _load_or_scrape(force=False)

    # Show when data was last updated (CSV timestamp)
    if CSV_OUT.exists():
        last_updated = datetime.fromtimestamp(CSV_OUT.stat().st_mtime)
        st.caption(f"Last updated: {last_updated.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        st.caption("Last updated: Not available (no CSV found)")
        
        
    # --- Filters ----
    c1, c2, c3 = st.columns(3)
    with c1:
        years = sorted(df["year"].unique())
        year_sel = st.multiselect("Year", years, default=years)
    with c2:
        index_sel = st.radio("Index", ["CCPI", "NCPI"], horizontal=True)
    with c3:
        measure_sel = st.radio(
            "Measure", ["Headline (Y-o-Y)", "Core (Y-o-Y)"], horizontal=True)

    # Choose correct column based on filters
    d = df[df["year"].isin(year_sel)].copy()
    if index_sel == "CCPI" and measure_sel.startswith("Headline"):
        ycol = "ccpi_headline_yoy"
    elif index_sel == "CCPI":
        ycol = "ccpi_core_yoy"
    elif index_sel == "NCPI" and measure_sel.startswith("Headline"):
        ycol = "ncpi_headline_yoy"
    else:
        ycol = "ncpi_core_yoy"

    # ---------- KPIs ----------
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Average (%)", f"{d[ycol].mean():.2f}")
    k2.metric("Std. Dev.", f"{d[ycol].std():.2f}")
    idx_max = d[ycol].idxmax()
    idx_min = d[ycol].idxmin()
    k3.metric(
        "Max", f"{d.loc[idx_max,ycol]:.2f} ({d.loc[idx_max,'month']} {int(d.loc[idx_max,'year'])})")
    k4.metric(
        "Min", f"{d.loc[idx_min,ycol]:.2f} ({d.loc[idx_min,'month']} {int(d.loc[idx_min,'year'])})")

    # ---------- Charts ----------
    st.subheader(f"{index_sel} — {measure_sel}")
    d["month_label"] = d["month_num"].map(
        {i+1: m[:3] for i, m in enumerate(MONTHS)})
    fig = px.line(
        d.sort_values(["year", "month_num"]),
        x="month_label", y=ycol, color="year",
        markers=True,
        labels={ycol: "Y-o-Y (%)", "month_label": "Month", "year": "Year"},
        height=320
    )
    st.plotly_chart(fig, use_container_width=True)


    # ---------- Table + PDF link ----------
    st.subheader("Monthly table & press release")
    d["month"] = d["month"].str.title()
    if not links.empty:
        links["month"] = links["month"].str.title()
    table = d.merge(links, on=["year", "month"], how="left")
    st.dataframe(
        table[["year", "month", "ccpi_headline_yoy", "ccpi_core_yoy",
               "ncpi_headline_yoy", "ncpi_core_yoy", "pdf_url"]],
        use_container_width=True
    )

    with st.expander("Open official press release (PDF)"):
        y = st.selectbox("Year", sorted(table["year"].unique()))
        months = table[table["year"] == y]["month"].unique().tolist()
        if months:
            m = st.selectbox("Month", months)
            r = table[(table["year"] == y) & (table["month"] == m)]
            url = None if r.empty else r["pdf_url"].iloc[0]
            if pd.notna(url):
                st.markdown(f"[Open PDF for {m} {y}]({url})")
            else:
                st.info("No link captured for this month.")
