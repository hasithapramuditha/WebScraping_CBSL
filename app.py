import streamlit as st
import pandas as pd
import os
import plotly.express as px
from exchangeRatesScraper import latest_currency_rates,difference_in_exchange_rates
from policyRatesScraper import render_policy_rates_page
from inflationScraper import render_inflation_page
from sl_prosperity_index import show_sl_prosperity_index
from price_wages_employment import render_prices_wages_page
from moneySupply import render_money_supply_page



# Set Streamlit page configuration
st.set_page_config(
    page_title="CBSL Data Dashboard",
    page_icon="📊",
    layout="wide"
)

# Title and Sidebar
st.title("Central Bank of Sri Lanka Data Dashboard")

st.sidebar.title("Navigation")
selected_page = st.sidebar.radio("Select Page", ["Home", "Exchange Rates", "Money Supply", "Policy Rates", "Inflation", "SL Prosperity Index", "Prices & Wages"])

# --- Home Page ---
if selected_page == "Home":
    st.write("""
    # Welcome to the CBSL Data Dashboard
    This comprehensive dashboard provides real-time economic and financial data from the Central Bank of Sri Lanka.
    
    ### Available Data:
    - 📈 **Exchange Rates**: Latest buying and selling rates with historical trends
    - 💰 **Money Supply**: Track monetary sector indicators and market operations
    - 🏦 **Policy Rates**: Current and historical policy rates (OPR, SRR, SDFR, SLFR)
    - 📊 **Inflation**: CCPI and NCPI data with historical analysis
    - 📉 **SL Prosperity Index**: Track Sri Lanka's economic prosperity indicators
    - 💹 **Prices & Wages**: Employment data, wage indices, and price indicators
    
    ### Features:
    - Real-time data from CBSL official sources
    - Interactive charts and visualizations
    - Historical trend analysis
    - Data export capabilities
    - Automated data updates
    """)
    
    # Add website update time
    st.sidebar.markdown("---")
    st.sidebar.write("Last Updated:", pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))

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
        differece = difference_in_exchange_rates(df, curr)
        st.subheader(f"Latest Rates for {curr} as of {latest_rates['date']}")
        
        col1, col2 = st.columns(2)
        col1.metric(
            "Buying Rate",
            f"Rs.{latest_rates['buying']}",
            differece['buying_diff'],
            delta_color="inverse"  # green if positive, red if negative
        )

        col2.metric(
            "Selling Rate",
            f"Rs.{latest_rates['selling']}",
            differece['selling_diff'],
            delta_color="inverse"
        )
    
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

# --- SL Prosperity Index Page ---
elif selected_page == "SL Prosperity Index":
    show_sl_prosperity_index()
    
# --- Prices & Wages Page ---
elif selected_page == "Prices & Wages":
    render_prices_wages_page()

# --- Money Supply Page ---
elif selected_page == "Money Supply":
    render_money_supply_page()
