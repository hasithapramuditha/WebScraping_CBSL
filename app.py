import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from policyRatesScraper import scrape_policy_rates

# Set page configuration
st.set_page_config(
    page_title="CBSL Data Dashboard",
    page_icon="📊",
    layout="wide"
)

# Main title
st.title("Central Bank of Sri Lanka Data Dashboard")

# Add a sidebar
st.sidebar.title("Navigation")
selected_page = st.sidebar.radio("Select Page", ["Home", "Policy Rates"])

if selected_page == "Home":
    # Main content area for home page
    st.write("""
    # Welcome to CBSL Data Dashboard
    This application displays data from the Central Bank of Sri Lanka.
    """)

elif selected_page == "Policy Rates":
    st.header("Policy Interest Rates")
    
    # Add a refresh button
    if st.button("Refresh Data"):
        with st.spinner("Fetching latest rates..."):
            df = scrape_policy_rates()
            if df is not None:
                # Display the data
                st.dataframe(df)

                # Altair bar chart with horizontal x-axis labels
                chart = alt.Chart(df).mark_bar().encode(
                    x=alt.X('Rate Type:N', axis=alt.Axis(labelAngle=0)),  # 0° keeps labels horizontal
                    y='Value:Q',
                    tooltip=['Rate Type', 'Value', 'Last Updated']
                ).properties(
                    width=600,
                    height=400
                )

                st.altair_chart(chart, use_container_width=True)

                # Show last updated time
                st.info(f"Last Updated: {df['Last Updated'].iloc[0]}")
            else:
                st.error("Failed to fetch policy rates. Please try again later.")
