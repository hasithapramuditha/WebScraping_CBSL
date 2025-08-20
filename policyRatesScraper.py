import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re
import streamlit as st
import altair as alt
import matplotlib.pyplot as plt

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


def load_historical_policy_rates():
    """
    Load historical policy rates from CBSL Excel file
    Returns cleaned DataFrame with Date, Standing Deposit Facility Rate, and Standing Lending Facility Rate
    """
    try:
        url = "https://www.cbsl.gov.lk/sites/default/files/cbslweb_documents/about/20250522_historical_policy_interest_rates.xlsx"
        rates = pd.read_excel(
            url,
            sheet_name="Historical Policy Rates",
            usecols="B:D",
            skiprows=3,
            nrows=100
        )

        # Rename and clean
        rates.columns = ['Date', 'Standing Deposit Facility Rate', 'Standing Lending Facility Rate']
        rates['Date'] = pd.to_datetime(rates['Date'], dayfirst=True, errors='coerce')
        rates = rates.dropna(subset=['Date'])
        
        return rates
    except Exception as e:
        st.error(f"Failed to load historical data: {e}")
        return None


def display_current_rates():
    """
    Display current policy rates section with refresh button and visualization
    """
    st.subheader("📡 Current Policy Rates (Live)")

    if st.button("Refresh Current Rates"):
        with st.spinner("Fetching latest rates..."):
            df = scrape_policy_rates()
            if df is not None:
                # Display data table
                st.dataframe(df)

                # Altair bar chart
                chart = alt.Chart(df).mark_bar().encode(
                    x=alt.X('Rate Type:N', axis=alt.Axis(labelAngle=0)),
                    y='Value:Q',
                    tooltip=['Rate Type', 'Value', 'Last Updated']
                ).properties(
                    width=600,
                    height=400
                )

                st.altair_chart(chart, use_container_width=True)
                st.info(f"Last Updated: {df['Last Updated'].iloc[0]}")
            else:
                st.error("Failed to fetch current policy rates. Please try again later.")


def display_historical_rates():
    """
    Display historical policy rates section with data and visualization
    """
    st.subheader("📈 Historical Policy Rates (from CBSL Excel File)")

    with st.spinner("Loading historical policy rates..."):
        rates = load_historical_policy_rates()
        
        if rates is not None:
            # Show data
            rates_display = rates.copy()
            rates_display['Date'] = rates_display['Date'].dt.strftime('%Y-%m-%d')
            st.dataframe(rates_display)

            # Plot using matplotlib
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(rates['Date'], rates['Standing Deposit Facility Rate'], label='Deposit Rate', marker='o')
            ax.plot(rates['Date'], rates['Standing Lending Facility Rate'], label='Lending Rate', marker='s')
            ax.set_title('CBSL Policy Interest Rates Over Time')
            ax.set_xlabel('Date')
            ax.set_ylabel('Interest Rate (%)')
            ax.grid(True)
            ax.legend()
            plt.tight_layout()

            st.pyplot(fig)


def render_policy_rates_page():
    """
    Main function to render the Policy Rates page
    """
    st.header("Policy Interest Rates")
    
    # Display current rates section
    display_current_rates()
    
    # Display historical rates section
    display_historical_rates()