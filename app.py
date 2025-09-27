import streamlit as st
import pandas as pd
import altair as alt
import matplotlib.pyplot as plt
from policyRatesScraper import scrape_policy_rates
import os
import plotly.express as px
from exchangeRatesScraper import latest_currency_rates,difference_in_exchange_rates

# Set Streamlit page configuration
st.set_page_config(
    page_title="CBSL Data Dashboard",
    page_icon="📊",
    layout="wide"
)

# Title and Sidebar
st.title("Central Bank of Sri Lanka Data Dashboard")

st.sidebar.title("Navigation")
selected_page = st.sidebar.radio("Select Page", ["Home", "Policy Rates","Exchange Rates"])

# --- Home Page ---
if selected_page == "Home":
    st.write("""
    # Welcome to the CBSL Data Dashboard
    This application displays policy interest rate data from the Central Bank of Sri Lanka.
    
    - View the **latest policy rates** (OPR, SRR, SDFR, SLFR)
    - Explore **historical interest rate trends**
    """)

# --- Policy Rates Page ---
elif selected_page == "Policy Rates":
    st.header("Policy Interest Rates")

    # --- Section 1: Real-time Rates ---
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

    # --- Section 2: Historical Rates ---
    st.subheader("📈 Historical Policy Rates (from CBSL Excel File)")

    with st.spinner("Loading historical policy rates..."):
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

        except Exception as e:
            st.error(f"Failed to load historical data: {e}")

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
    
    
    
    
