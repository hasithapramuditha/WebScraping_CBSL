from __future__ import annotations
import re
from io import BytesIO
from urllib.parse import urljoin

import requests
import pdfplumber
import pandas as pd
from bs4 import BeautifulSoup
import streamlit as st

# URLs
PAGE_URL = "https://www.cbsl.gov.lk/statistics/economic-indicators/srilanka-prosperity-index"
PDF_BASE_URL = "https://www.cbsl.gov.lk/sites/default/files/cbslweb_documents/statistics/note_sri_lanka_prosperity_index_{}_e.pdf"  # 2015..2020
PDF_2021_URL = "https://www.cbsl.gov.lk/sites/default/files/cbslweb_documents/press/pr/press_20221230_sri_lanka_prosperity_index_2021_e.pdf"
YEARS_15_20 = list(range(2015, 2021))

HTTP_TIMEOUT = 30
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}


def fetch_page_soup(url: str = PAGE_URL) -> BeautifulSoup:
    resp = requests.get(url, timeout=HTTP_TIMEOUT, headers=HEADERS)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")

# Extracting title 
def extract_title(soup: BeautifulSoup) -> str | None:
    # Primary selector (your original)
    h1 = soup.select_one("div.field-item.odd h1")
    if h1:
        return h1.get_text(strip=True)
    h1 = soup.find("h1")
    return h1.get_text(strip=True) if h1 else None

# Extracting image
def extract_image_url(soup: BeautifulSoup, base_url: str = PAGE_URL) -> str | None:
    img = soup.select_one("div.field-item.odd img") or soup.find("img")
    if not img or not img.get("src"):
        return None
    return urljoin(base_url, img["src"])

# List of reports 
def extract_report_list(soup: BeautifulSoup) -> list[str]:
    items = soup.select("div.field-item.odd li")
    return [i.get_text(strip=True) for i in items]

# Extracting SLPIS of different years
def extract_slpi_from_text_15_20(text: str, year: int) -> float | None:
    # Whitespace normalization
    t = " ".join((text or "").split())
# regex patterns to locate the SLPIs
    m = re.search(r"Sri Lanka Prosperity Index[^\d]+(\d+\.\d+)\s+(\d+\.\d+)", t, flags=re.IGNORECASE)
    if m:
        return float(m.group(2))

    m = re.search(rf"(\d+\.\d+)\s+in\s+{year}", t, flags=re.IGNORECASE)
    if m:
        return float(m.group(1))

    m = re.search(rf"{year}\s+(\d+\.\d+)", t, flags=re.IGNORECASE)
    if m:
        return float(m.group(1))

    return None

def fetch_slpi_2015_2020() -> dict[int, float]:
    """Return {year: slpi} for 2015..2020 using first-page text (matches your baseline)."""
    results: dict[int, float] = {}
    for year in YEARS_15_20:
        pdf_url = PDF_BASE_URL.format(year)
        try:
            r = requests.get(pdf_url, timeout=HTTP_TIMEOUT, headers=HEADERS)
            r.raise_for_status()
            with pdfplumber.open(BytesIO(r.content)) as pdf:
                page1 = pdf.pages[0]
                text = page1.extract_text() or ""
            val = extract_slpi_from_text_15_20(text, year)
            if val is not None:
                results[year] = val
        except Exception as e:
            pass
    return results

def fetch_slpi_2021() -> float | None:
    """Extract overall SLPI for 2021 from the press PDF (robust but compact)."""
    r = requests.get(PDF_2021_URL, timeout=HTTP_TIMEOUT, headers=HEADERS)
    r.raise_for_status()

    with pdfplumber.open(BytesIO(r.content)) as pdf:
        text = " ".join((p.extract_text() or "") for p in pdf.pages)

    t = re.sub(r"\s+", " ", (text or "").replace("\u00A0", " ")).strip()
    t = re.sub(r"\(\s*SLPI\s*\)\s*\d+", "(SLPI)", t, flags=re.IGNORECASE)

    num = r"(?P<num>\d+(?:\s*[.,]\s*\d+)?)"

    m = re.search(rf"index\s+value\s+of\s+{num}\s+in\s*2021", t, flags=re.IGNORECASE)
    if not m:
        m = re.search(rf"{num}\s+(?:index\s*points?\s+)?in\s*2021", t, flags=re.IGNORECASE) \
            or re.search(rf"(?:in|for)\s*2021.{{0,80}}?(?:slpi|prosperity\s+index).{{0,40}}?{num}", t, flags=re.IGNORECASE)
    if not m:
        return None

    val = float(m.group("num").replace(" ", "").replace(",", ""))
    return val if 0 < val < 10 else None

# Combining years and values into a DataFrame
def build_slpi_dataframe() -> pd.DataFrame:
    """Return a DataFrame with columns: Year, SLPI (2015..2021)."""
    data = []
    # 2015-2020
    vals_15_20 = fetch_slpi_2015_2020()
    for y in YEARS_15_20:
        data.append({"Year": y, "SLPI": vals_15_20.get(y, None)})
    # 2021
    v2021 = fetch_slpi_2021()
    data.append({"Year": 2021, "SLPI": v2021})

    df = pd.DataFrame(data).sort_values("Year").reset_index(drop=True)
    return df

def show_sl_prosperity_index():
    """Streamlit-rendered page: Title -> Image -> Table of Year & SLPI."""
    # Fetch page content
    soup = fetch_page_soup(PAGE_URL)
    title = extract_title(soup) or "Sri Lanka Prosperity Index"
    img_url = extract_image_url(soup, PAGE_URL)

    # Layout
    st.title(title)

    if img_url:
        st.image(img_url, use_container_width=True)

    st.markdown("### Overall SLPI by Year")
    df = build_slpi_dataframe()
    st.dataframe(df, use_container_width=True)

    # quick summary
    if df["SLPI"].notna().any():
        avg = df["SLPI"].dropna().mean()
        st.caption(f"Average SLPI ({int(df['Year'].min())}–{int(df['Year'].max())}): **{avg:.3f}**")
    else:
        st.caption("No SLPI values could be extracted.")

