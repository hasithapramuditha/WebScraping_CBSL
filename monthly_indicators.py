"""
scrape_cbsl_monthly_fix_with_table_extract.py

Scrapes the CBSL Monthly Indicators page for PDF links,
downloads the PDFs, extracts tables (using pdfplumber),
and saves them as CSVs under monthly_indicators/<pdf_basename>/table_<n>.csv

Requirements:
    pip install requests beautifulsoup4 lxml PyPDF2 pandas pdfplumber
"""

import os
import time
import random
import json
import csv
import re
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

# Optional for table extraction
try:
    import pandas as pd
    _PANDAS_AVAILABLE = True
except Exception:
    _PANDAS_AVAILABLE = False

# Optional PDF text extraction (PyPDF2)
try:
    import PyPDF2
    _PYPDF2_AVAILABLE = True
except Exception:
    _PYPDF2_AVAILABLE = False

# Optional PDF table extraction
try:
    import pdfplumber
    _PDFPLUMBER_AVAILABLE = True
except Exception:
    _PDFPLUMBER_AVAILABLE = False

BASE = "https://www.cbsl.gov.lk/en/statistics/economic-indicators/monthly-indicators"
ROOT = "https://www.cbsl.gov.lk"
DOMAIN = urlparse(ROOT).netloc

HEADERS = {
    "User-Agent": "cbsl-monthly-scraper/1.0 (+https://example.com/contact) - polite-demo"
}

MAX_PAGES = 1          # visit only the target page for testing
SLEEP_RANGE = (1.0, 2.0)

PDF_DIR = "pdfs"
os.makedirs(PDF_DIR, exist_ok=True)

MONTHLY_DIR = "monthly_indicators"
os.makedirs(MONTHLY_DIR, exist_ok=True)

PDF_EXT_RE = re.compile(r'\.pdf($|\?)', re.IGNORECASE)

def allowed_by_robots(url, user_agent=HEADERS["User-Agent"]):
    robots_url = urljoin(ROOT, "/robots.txt")
    rp = RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
    except Exception as e:
        print(f"[!] Could not read robots.txt ({robots_url}): {e}")
        return True
    return rp.can_fetch(user_agent, url)

def is_internal(link):
    if not link:
        return False
    parsed = urlparse(link)
    return (parsed.netloc == "" or DOMAIN in parsed.netloc)

def normalize_link(href, base):
    if not href:
        return None
    if href.startswith(("javascript:", "mailto:", "tel:")):
        return None
    joined = urljoin(base, href)
    parsed = urlparse(joined)
    return parsed._replace(fragment="").geturl()

def get_soup(url):
    """Fetch URL and return (soup, response)."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        print(f"[!] Failed to GET {url}: {e}")
        return None, None

    try:
        soup = BeautifulSoup(resp.text, "lxml")
    except Exception:
        soup = BeautifulSoup(resp.text, "html.parser")
    return soup, resp

def find_pdf_links_on_page(soup, page_url):
    pdfs = set()
    if soup is None:
        return []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        norm = normalize_link(href, page_url)
        if not norm:
            continue
        if PDF_EXT_RE.search(norm) or norm.lower().endswith(".pdf"):
            pdfs.add(norm)
    return sorted(pdfs)

def sanitize_filename(name: str) -> str:
    name = re.sub(r'[^A-Za-z0-9_\-\. ]+', '_', name)
    name = name.replace(' ', '_')
    return name[:200]

def download_pdf(pdf_url, out_dir=PDF_DIR, max_tries=3):
    local_filename = sanitize_filename(os.path.basename(urlparse(pdf_url).path) or "download.pdf")
    dest_path = os.path.join(out_dir, local_filename)
    base, ext = os.path.splitext(dest_path)
    counter = 1
    while os.path.exists(dest_path):
        dest_path = f"{base}_{counter}{ext}"
        counter += 1

    tries = 0
    while tries < max_tries:
        try:
            with requests.get(pdf_url, headers=HEADERS, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(dest_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            size = os.path.getsize(dest_path)
            print(f"Downloaded {pdf_url} -> {dest_path} ({size} bytes)")
            return {"pdf_url": pdf_url, "local_path": dest_path, "size_bytes": size}
        except Exception as e:
            tries += 1
            print(f"[!] Error downloading {pdf_url} (try {tries}/{max_tries}): {e}")
            time.sleep(1 + tries)
    print(f"[!] Failed to download {pdf_url}")
    return None

def extract_text_from_pdf(path):
    if not _PYPDF2_AVAILABLE:
        return ""
    text_parts = []
    try:
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                try:
                    page_text = page.extract_text() or ""
                except Exception:
                    page_text = ""
                if page_text:
                    text_parts.append(page_text)
    except Exception as e:
        print(f"[!] PyPDF2 failed on {path}: {e}")
        return ""
    return "\n".join(text_parts)

def looks_like_monthly_pdf(pdf_url, local_path):
    url_lower = (pdf_url or "").lower()
    name_lower = os.path.basename(local_path or "").lower()
    if "/statistics/mei/" in url_lower:
        return True
    if "mei_" in name_lower or name_lower.startswith("mei"):
        return True
    if "monthly" in name_lower or "mei" in name_lower:
        return True
    return False

_NUMBER_RE = re.compile(r'[-+]?\d{1,3}(?:[,\s]\d{3})*(?:\.\d+)?%?|\d+\.\d+%?')

def table_has_numeric(df):
    if df is None or df.empty:
        return False
    try:
        for col in df.columns:
            s = df[col].astype(str).str.strip().fillna("")
            if s.apply(lambda x: bool(_NUMBER_RE.search(x))).any():
                return True
    except Exception:
        return False
    return False

def extract_monthly_indicators_from_pdf(local_path, pdf_url=None, out_root=MONTHLY_DIR):
    saved_csvs = []
    pdf_basename = sanitize_filename(os.path.splitext(os.path.basename(local_path))[0])
    target_dir = os.path.join(out_root, pdf_basename)
    os.makedirs(target_dir, exist_ok=True)

    if not _PDFPLUMBER_AVAILABLE:
        print(f"[!] pdfplumber not installed. Falling back to text snippet for {local_path}")
        text = extract_text_from_pdf(local_path)
        if text:
            snippet_path = os.path.join(target_dir, f"{pdf_basename}_text_snippet.txt")
            with open(snippet_path, "w", encoding="utf-8") as f:
                f.write(text[:20000])
            saved_csvs.append(snippet_path)
        return saved_csvs

    try:
        with pdfplumber.open(local_path) as pdf:
            table_count = 0
            for page_no, page in enumerate(pdf.pages, start=1):
                tables = page.extract_tables()
                if not tables:
                    continue
                for t_idx, table in enumerate(tables, start=1):
                    try:
                        df = pd.DataFrame(table)
                    except Exception:
                        if not _PANDAS_AVAILABLE:
                            csv_path = os.path.join(target_dir, f"table_p{page_no}_{t_idx}.csv")
                            with open(csv_path, "w", newline="", encoding="utf-8") as cf:
                                writer = csv.writer(cf)
                                for r in table:
                                    writer.writerow([cell or "" for cell in r])
                            saved_csvs.append(csv_path)
                            table_count += 1
                        continue

                    df2 = df.replace({None: ""}).applymap(lambda x: x.strip() if isinstance(x, str) else x)
                    first_row = df2.iloc[0].astype(str)
                    if first_row.str.len().sum() > 0 and first_row.apply(lambda x: len(str(x).strip()) > 0).sum() >= 2:
                        df_clean = df2.copy()
                        df_clean.columns = df2.iloc[0].fillna("").astype(str)
                        df_clean = df_clean.drop(df_clean.index[0]).reset_index(drop=True)
                    else:
                        df_clean = df2.copy().reset_index(drop=True)

                    if df_clean.dropna(how="all").empty:
                        continue

                    if table_has_numeric(df_clean):
                        table_count += 1
                        csv_path = os.path.join(target_dir, f"{pdf_basename}table_p{page_no}{t_idx}.csv")
                        if _PANDAS_AVAILABLE:
                            try:
                                df_clean.to_csv(csv_path, index=False, encoding="utf-8")
                            except Exception:
                                df_clean.to_csv(csv_path, index=False, encoding="utf-8", sep=",")
                        else:
                            with open(csv_path, "w", newline="", encoding="utf-8") as cf:
                                writer = csv.writer(cf)
                                for r in df_clean.values.tolist():
                                    writer.writerow([cell or "" for cell in r])
                        saved_csvs.append(csv_path)

            if table_count == 0:
                text = extract_text_from_pdf(local_path)
                if text:
                    snippet_path = os.path.join(target_dir, f"{pdf_basename}_text_snippet.txt")
                    with open(snippet_path, "w", encoding="utf-8") as f:
                        f.write(text[:20000])
                    saved_csvs.append(snippet_path)

    except Exception as e:
        print(f"[!] pdfplumber failed on {local_path}: {e}")
        text = extract_text_from_pdf(local_path)
        if text:
            snippet_path = os.path.join(target_dir, f"{pdf_basename}_text_snippet.txt")
            with open(snippet_path, "w", encoding="utf-8") as f:
                f.write(text[:20000])
            saved_csvs.append(snippet_path)

    return saved_csvs

def crawl_for_pdfs(start_url=BASE, max_pages=MAX_PAGES):
    if not allowed_by_robots(start_url):
        print("Robots.txt disallows scraping this start URL. Aborting.")
        return {}

    to_visit = [start_url]
    visited = set()
    found_pdfs = {}

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue
        print(f"Fetching ({len(visited)+1}/{max_pages}): {url}")
        soup, resp = get_soup(url)
        visited.add(url)
        if soup is None:
            time.sleep(random.uniform(*SLEEP_RANGE))
            continue

        pdf_links = find_pdf_links_on_page(soup, url)
        for p in pdf_links:
            if p not in found_pdfs:
                found_pdfs[p] = {"found_on": url}

        if max_pages > 1:
            for a in soup.find_all("a", href=True):
                norm = normalize_link(a["href"], url)
                if not norm:
                    continue
                if is_internal(norm) and norm not in visited and norm not in to_visit:
                    parsed = urlparse(norm)
                    if parsed.netloc and DOMAIN in parsed.netloc:
                        to_visit.append(norm)

        time.sleep(random.uniform(*SLEEP_RANGE))

    print(f"Visited {len(visited)} pages, found {len(found_pdfs)} unique PDF links.")
    return found_pdfs

def main():
    found = crawl_for_pdfs()
    results = []
    monthly_index = {}

    for pdf_url, meta in found.items():
        info = {"pdf_url": pdf_url, "found_on": meta.get("found_on")}
        dl = download_pdf(pdf_url)
        if dl:
            info.update(dl)
            txt = extract_text_from_pdf(dl["local_path"])
            if txt:
                info["text_snippet"] = txt[:2000]

            saved = extract_monthly_indicators_from_pdf(dl["local_path"], pdf_url=pdf_url)
            if saved:
                saved_rel = [os.path.relpath(p) for p in saved]
                monthly_index[pdf_url] = saved_rel
                info["monthly_files"] = saved_rel

            results.append(info)
            time.sleep(random.uniform(*SLEEP_RANGE))

    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("Saved results.json")

    with open("results.csv", "w", newline="", encoding="utf-8") as cf:
        writer = csv.writer(cf)
        header = ["pdf_url", "found_on", "local_path", "size_bytes", "text_snippet", "monthly_files"]
        writer.writerow(header)
        for r in results:
            writer.writerow([
                r.get("pdf_url"),
                r.get("found_on"),
                r.get("local_path"),
                r.get("size_bytes"),
                (r.get("text_snippet") or "")[:1000],
                " | ".join(r.get("monthly_files", []))
            ])
    print("Saved results.csv")

    with open(os.path.join(MONTHLY_DIR, "index.json"), "w", encoding="utf-8") as f:
        json.dump(monthly_index, f, ensure_ascii=False, indent=2)
    print(f"Saved monthly index -> {os.path.join(MONTHLY_DIR, 'index.json')}")

    combined_rows = []
    for pdf_url, files in monthly_index.items():
        for fpath in files:
            combined_rows.append({"pdf_url": pdf_url, "extracted_file": fpath})
    if combined_rows:
        combined_csv = os.path.join(MONTHLY_DIR, "monthly_extracted_files.csv")
        with open(combined_csv, "w", newline="", encoding="utf-8") as cf:
            writer = csv.DictWriter(cf, fieldnames=["pdf_url", "extracted_file"])
            writer.writeheader()
            writer.writerows(combined_rows)
        print(f"Saved combined extracted files list -> {combined_csv}")

if __name__ == "__main__":
    main()
