import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re
import streamlit as st
import altair as alt
import plotly.express as px
import plotly.graph_objects as go
import time

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


def load_srr_data():
    """
    Load SRR (Statutory Reserve Ratio) data from CBSL Excel file
    Returns cleaned DataFrame with Date and SRR columns
    """
    try:
        url = "https://www.cbsl.gov.lk/sites/default/files/cbslweb_documents/about/20250522_historical_policy_interest_rates.xlsx"
        srr_data = pd.read_excel(
            url,
            sheet_name="SRR",
            usecols="B:C",
            skiprows=3,
            nrows=14  # B5:C18 is 14 rows
        )

        # Rename columns
        srr_data.columns = ['Date', 'SRR']
        srr_data['Date'] = pd.to_datetime(srr_data['Date'], dayfirst=True, errors='coerce')
        srr_data = srr_data.dropna(subset=['Date'])
        
        return srr_data
    except Exception as e:
        st.error(f"Failed to load SRR data: {e}")
        return None


def display_current_rates():
    """
    Display current policy rates section with automatic refresh on page navigation
    """
    st.subheader("📡 Current Policy Rates")
    
    # Track current page to detect navigation
    current_page = "policy_rates"
    
    # Check if we're coming from a different page or first time loading
    if ('last_page' not in st.session_state or 
        st.session_state.last_page != current_page or 
        'current_rates_data' not in st.session_state):
        
        with st.spinner("Fetching latest rates..."):
            df = scrape_policy_rates()
            if df is not None:
                st.session_state.current_rates_data = df
                st.session_state.last_page = current_page
                st.success("✅ Rates fetched successfully!")
            else:
                st.error("❌ Failed to fetch current policy rates.")
                return
    
    # Display the data
    df = st.session_state.current_rates_data
    
    # Display rates as labels in a grid layout
    st.markdown("### Current Rates")
    
    # Create columns for rate display
    col1, col2 = st.columns(2)
    
    for index, row in df.iterrows():
        rate_type = row['Rate Type']
        value = row['Value']
        
        # Assign to columns alternately
        col = col1 if index % 2 == 0 else col2
        
        with col:
            # Create custom styling for each rate
            if "OPR" in rate_type:
                st.metric("🏦 Overnight Policy Rate (OPR)", f"{value}%")
            elif "SRR" in rate_type:
                st.metric("📊 Statutory Reserve Ratio (SRR)", f"{value}%")
            elif "SDFR" in rate_type:
                st.metric("💰 Standing Deposit Facility Rate (SDFR)", f"{value}%")
            elif "SLFR" in rate_type:
                st.metric("💳 Standing Lending Facility Rate (SLFR)", f"{value}%")
    
    # Show only one last update time
    last_update = df['Last Updated'].iloc[0]
    st.info(f"🕒 Last Updated: {last_update}")


def display_historical_rates():
    """
    Display historical policy rates section with data and visualization using Plotly
    """

    with st.spinner("Loading historical policy rates..."):
        rates = load_historical_policy_rates()
        
        if rates is not None:
            # Add checkboxes for rate selection
            st.subheader("📈 Historical Policy Interest Rates")
            col1, col2 = st.columns(2)
            
            with col1:
                show_deposit = st.checkbox("Standing Deposit Facility Rate (SDFR)", value=True, key="deposit_rate")
            with col2:
                show_lending = st.checkbox("Standing Lending Facility Rate (SLFR)", value=True, key="lending_rate")
            
            # Create plotly figure
            fig = go.Figure()
            
            # Add traces based on checkbox selection
            if show_deposit:
                fig.add_trace(go.Scatter(
                    x=rates['Date'], 
                    y=rates['Standing Deposit Facility Rate'],
                    mode='lines+markers',
                    name='Standing Deposit Facility Rate (SDFR)',
                    line=dict(color='#1f77b4', width=2),
                    marker=dict(size=6, symbol='circle'),
                    hovertemplate='<b>SDFR</b><br>Date: %{x}<br>Rate: %{y}%<extra></extra>'
                ))
            
            if show_lending:
                fig.add_trace(go.Scatter(
                    x=rates['Date'], 
                    y=rates['Standing Lending Facility Rate'],
                    mode='lines+markers',
                    name='Standing Lending Facility Rate (SLFR)',
                    line=dict(color='#ff7f0e', width=2),
                    marker=dict(size=6, symbol='square'),
                    hovertemplate='<b>SLFR</b><br>Date: %{x}<br>Rate: %{y}%<extra></extra>'
                ))
            
            # Update layout
            fig.update_layout(
                title={
                    'text': 'CBSL Policy Interest Rates Over Time',
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'size': 18}
                },
                xaxis_title='Date',
                yaxis_title='Interest Rate (%)',
                hovermode='x unified',
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                height=500,
                template='plotly_white'
            )
            
            # Add grid
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
            
            # Display the chart only if at least one checkbox is selected
            if show_deposit or show_lending:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Please select at least one rate to display the chart.")

            # Add slider to show/hide data table (default hidden)
            show_data_table = st.toggle("Show Historical Data Table", value=False, key="show_historical_table")
            
            if show_data_table:
                rates_display = rates.copy()
                rates_display['Date'] = rates_display['Date'].dt.strftime('%Y-%m-%d')
                st.dataframe(rates_display)


def display_srr_chart():
    """
    Display SRR (Statutory Reserve Ratio) chart section
    """
    st.subheader("📊 Historical Statutory Reserve Ratio (SRR)")

    with st.spinner("Loading SRR data..."):
        srr_data = load_srr_data()
        
        if srr_data is not None:
            # Create plotly figure for SRR
            fig_srr = go.Figure()
            
            fig_srr.add_trace(go.Scatter(
                x=srr_data['Date'], 
                y=srr_data['SRR'],
                mode='lines+markers',
                name='Statutory Reserve Ratio (SRR)',
                line=dict(color='#2ca02c', width=3),
                marker=dict(size=8, symbol='diamond'),
                hovertemplate='<b>SRR</b><br>Date: %{x}<br>Ratio: %{y}%<extra></extra>'
            ))
            
            # Update layout for SRR chart
            fig_srr.update_layout(
                title={
                    'text': 'Statutory Reserve Ratio (SRR) Over Time',
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'size': 18}
                },
                xaxis_title='Date',
                yaxis_title='Reserve Ratio (%)',
                hovermode='x unified',
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                height=450,
                template='plotly_white'
            )
            
            # Add grid
            fig_srr.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
            fig_srr.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
            
            # Display the SRR chart
            st.plotly_chart(fig_srr, use_container_width=True)

            # Add slider to show/hide SRR data table (default hidden)
            show_srr_table = st.toggle("Show SRR Data Table", value=False, key="show_srr_table")
            
            if show_srr_table:
                srr_display = srr_data.copy()
                srr_display['Date'] = srr_display['Date'].dt.strftime('%Y-%m-%d')
                st.dataframe(srr_display)


def render_policy_rates_page():
    """
    Main function to render the Policy Rates page
    """
    st.header("Policy Interest Rates")
    
    # Display current rates section with manual refresh
    display_current_rates()
    
    # Display historical rates section
    display_historical_rates()
    
    # Display SRR chart section
    display_srr_chart()