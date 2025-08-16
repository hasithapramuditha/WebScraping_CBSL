import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re

def scrape_policy_rates():
    """
    Scrape policy rates from CBSL websites including:
    - Overnight Policy Rate (OPR) and Statutory Reserve Ratio (SRR) from the first URL
    - Standing Deposit Facility Rate (SDFR) and Standing Lending Facility Rate (SLFR) from the second URL
    """
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:140.0) Gecko/20100101 Firefox/140.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.cbsl.gov.lk/',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    rates_data = []
    
    # First URL - for OPR and SRR
    url1 = "https://www.cbsl.gov.lk/cbsl_custom/param/plrates.php"
    try:
        response = requests.get(url1, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for row in soup.select("#container tr"):
            cells = row.find_all("td")
            if len(cells) == 2:
                label = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                
                if "Overnight Policy Rate" in label:
                    rates_data.append({
                        "Rate Type": "Overnight Policy Rate (OPR)",
                        "Value": float(value),
                        "Last Updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                elif "Statutory Reserve Ratio" in label:
                    rates_data.append({
                        "Rate Type": "Statutory Reserve Ratio (SRR)",
                        "Value": float(value),
                        "Last Updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                    
    except Exception as e:
        print(f"[ERROR] Failed to fetch rates from first URL: {e}")
    
    # Second URL - for SDFR and SLFR
    url2 = "https://www.cbsl.gov.lk/en/rates-and-indicators/policy-rates"
    try:
        response = requests.get(url2, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for table rows or any element containing the rates
        page_text = soup.get_text()
        
        # Extract SDFR using regex
        sdfr_match = re.search(r'Standing Deposit Facility Rate \(SDFR\)\s*\|\s*([\d.]+)', page_text)
        if sdfr_match:
            rates_data.append({
                "Rate Type": "Standing Deposit Facility Rate (SDFR)",
                "Value": float(sdfr_match.group(1)),
                "Last Updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # Extract SLFR using regex
        slfr_match = re.search(r'Standing Lending Facility Rate \(SLFR\)\s*\|\s*([\d.]+)', page_text)
        if slfr_match:
            rates_data.append({
                "Rate Type": "Standing Lending Facility Rate (SLFR)",
                "Value": float(slfr_match.group(1)),
                "Last Updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            
        # Alternative approach: look for table structure
        if not sdfr_match or not slfr_match:
            # Try to find table rows
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        rate_name = cells[0].get_text(strip=True)
                        rate_value = cells[1].get_text(strip=True)
                        
                        if 'Standing Deposit Facility Rate' in rate_name or 'SDFR' in rate_name:
                            try:
                                value = float(re.search(r'([\d.]+)', rate_value).group(1))
                                rates_data.append({
                                    "Rate Type": "Standing Deposit Facility Rate (SDFR)",
                                    "Value": value,
                                    "Last Updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                })
                            except:
                                pass
                                
                        elif 'Standing Lending Facility Rate' in rate_name or 'SLFR' in rate_name:
                            try:
                                value = float(re.search(r'([\d.]+)', rate_value).group(1))
                                rates_data.append({
                                    "Rate Type": "Standing Lending Facility Rate (SLFR)",
                                    "Value": value,
                                    "Last Updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                })
                            except:
                                pass
                    
    except Exception as e:
        print(f"[ERROR] Failed to fetch rates from second URL: {e}")
    
    return pd.DataFrame(rates_data) if rates_data else None
