import streamlit as st
import pandas as pd
import numpy as np

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

# Main content area
st.write("""
# Welcome to CBSL Data Dashboard
This application displays data from the Central Bank of Sri Lanka.
""")

# Placeholder for future features
st.info("More features coming soon!")
