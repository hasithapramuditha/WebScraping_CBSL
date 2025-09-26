#!/usr/bin/env python3
"""
scrape_cbsl_prices_wages_employment.py

- Scrapes https://www.cbsl.gov.lk/en/statistics/statistical-tables/real-sector/prices-wages-employment
  for downloadable spreadsheet files (xls, xlsx, xlsm, csv).
- Downloads files to ./downloads/
- Loads each sheet with pandas and attempts to detect a date/time column
  and then plots numeric series using matplotlib (saved to ./plots/).

Requirements:
    pip install requests beautifulsoup4 pandas matplotlib openpyxl xlrd
    # xlrd may be required for older .xls files; openpyxl for .xlsx

Usage:
    python scrape_cbsl_prices_wages_employment.py
"""
import os
import re
import time
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

BASE_PAGE = "https://www.cbsl.gov.lk/en/statistics/statistical-tables/real-sector/prices-wages-employment"
HEADERS = {"User-Agent": "cbsl-excel-scraper/1.0 (+https://example.com/contact)"}

DOWNLOAD_DIR = "downloads"
PLOTS_DIR = "plots"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(PLOTS_DIR, exist_ok=True)

# file extensions to look for
FILE_EXTS = (".xls", ".xlsx", ".xlsm", ".csv")

def get_soup(url):
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "lxml")

def find_file_links(soup, base_url):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        # normalize to absolute URL
        full = urljoin(base_url, href)
        parsed = urlparse(full)
        # only keep same host files (optional)
        if parsed.scheme in ("http", "https"):
            for ext in FILE_EXTS:
                if full.lower().split('?')[0].endswith(ext):
                    links.add(full)
                    break
    return sorted(links)

def sanitize_filename(s):
    s = re.sub(r'[^A-Za-z0-9._\-() ]+', '_', s)
    return s[:200]

def download_file(url, out_dir=DOWNLOAD_DIR, max_tries=3):
    fname = sanitize_filename(os.path.basename(urlparse(url).path) or "file")
    dest = os.path.join(out_dir, fname)
    # avoid clobbering by adding counter
    base, ext = os.path.splitext(dest)
    i = 1
    while os.path.exists(dest):
        dest = f"{base}_{i}{ext}"
        i += 1
    tries = 0
    while tries < max_tries:
        try:
            with requests.get(url, headers=HEADERS, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(dest, "wb") as f:
                    for chunk in r.iter_content(8192):
                        if chunk:
                            f.write(chunk)
            print(f"[+] Downloaded: {url} -> {dest}")
            return dest
        except Exception as e:
            tries += 1
            print(f"[!] Download error ({tries}/{max_tries}) for {url}: {e}")
            time.sleep(1 + tries)
    raise RuntimeError(f"Failed to download {url}")

# Heuristic: detect date-like column
def detect_date_column(df):
    """
    Return the name of a detected date column or None.
    Strategy:
      - If column dtype is datetime, return it.
      - Try pandas.to_datetime on each column (coerce); if a high fraction parses, pick column.
      - Also look for column names containing 'date', 'month', 'year', 'period', 'time'
      - If a column is integer-looking and within 1900-2100, consider it 'Year'
    """
    if df is None or df.empty:
        return None
    candidates = []
    nrows = len(df)
    name_scores = {}
    for col in df.columns:
        ser = df[col]
        # 1) dtype datetime-like
        if np.issubdtype(ser.dtype, np.datetime64):
            return col
        # 2) name hint
        lname = str(col).lower()
        name_hint = any(k in lname for k in ("date", "month", "year", "period", "time"))
        # 3) try to coerce to datetime
        coerced = pd.to_datetime(ser.astype(str).replace(r'^\s*$', pd.NaT, regex=True),
                                  errors="coerce", dayfirst=True)
        parsed_frac = coerced.notna().sum() / max(1, nrows)
        # 4) integer year column check
        int_like = False
        if ser.dropna().shape[0] > 0:
            try:
                ints = pd.to_numeric(ser.dropna(), errors="coerce").dropna().astype(int)
                if ints.between(1900, 2100).any():
                    int_like = True
            except Exception:
                int_like = False
        score = parsed_frac + (0.3 if name_hint else 0) + (0.2 if int_like else 0)
        name_scores[col] = score
    # choose best-scoring column above a threshold
    best_col, best_score = max(name_scores.items(), key=lambda x: x[1])
    if best_score >= 0.35:
        return best_col
    return None

def prepare_dataframe_for_plot(df):
    """
    Clean df minimally:
      - strip columns
      - drop fully-empty rows/cols
      - try to parse index to datetime if possible
    Returns (df_clean, date_col_name or None)
    """
    # convert columns to str names
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    # drop fully empty
    df = df.dropna(axis=0, how='all').dropna(axis=1, how='all')
    if df.empty:
        return df, None
    date_col = detect_date_column(df)
    if date_col:
        coerced = pd.to_datetime(df[date_col].astype(str).replace(r'^\s*$', pd.NaT, regex=True),
                                 errors="coerce", dayfirst=True)
        # if many non-nulls, set index
        if coerced.notna().sum() >= max(1, int(0.3 * len(coerced))):
            df = df.assign(_parsed_date_=coerced)
            df = df.set_index("_parsed_date_").sort_index()
            # drop the original date column if it's identical to index or keep it
            return df, date_col
    # If Year-like integer column: convert to datetime at year-start
    for col in df.columns:
        try:
            ints = pd.to_numeric(df[col], errors="coerce")
            if ints.notna().sum() >= max(1, int(0.6 * len(ints))):
                # check if values look like years
                vals = ints.dropna().astype(int)
                if vals.between(1900, 2100).any():
                    # build a datetime index
                    df = df.assign(_year_=vals)
                    df = df.set_index(pd.to_datetime(df["_year_"].astype(int).astype(str) + "-01-01"))
                    df = df.drop(columns=["_year_"])
                    return df, col
        except Exception:
            pass
    return df, None

def plot_dataframe(df, source_name, sheet_name=None):
    """
    Plot numeric columns in df.
    If df has a DateTimeIndex, x-axis will be dates; else x = integer index.
    Saves PNG to plots directory.
    """
    if df is None or df.empty:
        return
    numeric = df.select_dtypes(include=[np.number])
    if numeric.empty:
        # maybe numeric columns are strings with commas -> try coercion
        coerced = df.apply(lambda col: pd.to_numeric(col.astype(str).str.replace(',',''), errors='coerce'))
        numeric = coerced.select_dtypes(include=[np.number]).dropna(axis=1, how='all')
        if numeric.empty:
            print(f"[!] No numeric columns to plot in {source_name} ({sheet_name})")
            return
        else:
            df_num = numeric
    else:
        df_num = numeric

    title = f"{os.path.basename(source_name)}" + (f" - {sheet_name}" if sheet_name else "")
    plt.figure(figsize=(10, 5))
    ax = plt.gca()
    # if index is datetime-like -> plot vs index, else use index numbers
    if np.issubdtype(df_num.index.dtype, np.datetime64):
        df_num.plot(ax=ax, linewidth=1)
        ax.xaxis.set_tick_params(rotation=30)
    else:
        # use index as x
        df_num.plot(ax=ax, linewidth=1)
        ax.set_xlabel("row index")
    ax.set_title(title)
    ax.grid(True, linestyle=":", linewidth=0.6)
    # save file
    safe_name = sanitize_filename(os.path.splitext(os.path.basename(source_name))[0])
    sheet_part = f"_{sanitize_filename(sheet_name)}" if sheet_name else ""
    outpath = os.path.join(PLOTS_DIR, f"{safe_name}{sheet_part}.png")
    plt.tight_layout()
    plt.savefig(outpath, dpi=150)
    print(f"[+] Saved plot: {outpath}")
    try:
        plt.show()
    except Exception:
        # in headless environments, plt.show() may not display; that's okay
        plt.close()

def process_file(path_or_url):
    """
    Load given file path (local) and process its sheets or CSV.
    """
    # use file extension
    lower = path_or_url.lower()
    try:
        if lower.endswith(".csv"):
            df = pd.read_csv(path_or_url)
            df2, date_col = prepare_dataframe_for_plot(df)
            plot_dataframe(df2, path_or_url, None)
        elif lower.endswith((".xls", ".xlsx", ".xlsm")):
            # read all sheets
            xl = pd.read_excel(path_or_url, sheet_name=None, engine=None)
            for sheet_name, df in xl.items():
                if isinstance(df, pd.DataFrame):
                    df2, date_col = prepare_dataframe_for_plot(df)
                    plot_dataframe(df2, path_or_url, sheet_name)
        else:
            print(f"[!] Unsupported file type for {path_or_url}")
    except Exception as e:
        print(f"[!] Failed to process {path_or_url}: {e}")

def main():
    print("[*] Fetching page and scanning for files...")
    soup = get_soup(BASE_PAGE)
    file_links = find_file_links(soup, BASE_PAGE)
    if not file_links:
        print("[!] No spreadsheet links found on the page.")
        return
    print(f"[+] Found {len(file_links)} files:")
    for f in file_links:
        print("   -", f)
    # Download and process each
    for link in file_links:
        try:
            local = download_file(link)
            process_file(local)
            time.sleep(0.5)
        except Exception as e:
            print(f"[!] Skipping {link}: {e}")

if __name__ == "__main__":
    main()
