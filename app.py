import streamlit as st
import pandas as pd
import os
import plotly.express as px
from policyRatesScraper import render_policy_rates_page
from exchangeRatesScraper import latest_currency_rates
from inflationScraper import render_inflation_page

# Set Streamlit page configuration
st.set_page_config(
    page_title="CBSL Data Dashboard",
    page_icon="📊",
    layout="wide"
)

# Title and Sidebar
st.title("Central Bank of Sri Lanka Data Dashboard")

st.sidebar.title("Navigation")
selected_page = st.sidebar.radio("Select Page", ["Home", "Policy Rates", "Exchange Rates", "Inflation"])

# --- Home Page ---
if selected_page == "Home":
    st.write("""
    # Welcome to the CBSL Data Dashboard
    This application displays policy interest rate data from the Central Bank of Sri Lanka.
    
    - View the **latest policy rates** (OPR, SRR, SDFR, SLFR)
    - Explore **historical interest rate trends**
    - Analyze **exchange rate movements**
    """)

# --- Policy Rates Page ---
elif selected_page == "Policy Rates":
    render_policy_rates_page()

# --- Exchange Rates Page ---
elif selected_page == "Exchange Rates":
    st.header("Exchange Rates")

    df = pd.read_csv(os.path.join("Data", "exchange_rates.csv"))
    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')
    df.set_index('Date', inplace=True)
    
    currencies = [col[-4:].strip() for col in df.columns if col != "Date"]
    curr = st.selectbox("Select Currency", set(currencies))
    
    if curr:
        latest_rates = latest_currency_rates(df, curr)
        st.subheader(f"Latest Rates for {curr} as of {latest_rates['date']}")
        
        col1, col2 = st.columns(2)
        col1.metric("Buying Rate", f"Rs.{latest_rates['buying']}")
        col2.metric("Selling Rate", f"Rs.{latest_rates['selling']}")
    
    st.subheader("Historical Exchange Rates")
    
    tab1, tab2 = st.tabs(["Buying", "Selling"])
    
    plot_data = df.reset_index()
    plot_data['Date'] = plot_data['Date'].dt.strftime('%Y-%m-%d')

    with tab1:
        if curr:
            fig = px.line(plot_data, x="Date", y=f"TT Rates -Buying {curr}", title=f"{curr} Over Time")
            st.plotly_chart(fig, use_container_width=True)
            
    with tab2:
        if curr:
            fig = px.line(plot_data, x="Date", y=f"TT Rates -Selling {curr}", title=f"{curr} Over Time")
            st.plotly_chart(fig, use_container_width=True)

# --- Inflation Page ---
elif selected_page == "Inflation":
    render_inflation_page()
