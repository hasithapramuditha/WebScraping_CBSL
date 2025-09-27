# 📊 Central Bank of Sri Lanka Data Dashboard

A comprehensive **Streamlit dashboard** that provides real-time access to economic and financial data published by the **Central Bank of Sri Lanka (CBSL)**. This project automatically scrapes data from various CBSL sources and presents it through interactive visualizations and analysis tools.

---

## 🚀 Features

### Data Modules
- **Exchange Rates**: 
  - Real-time buying and selling rates
  - Historical exchange rate trends
  - Multiple currency support
  - Change analysis and comparisons

- **Money Supply & Market Operations**:
  - Monetary sector indicators
  - Open market operations data
  - Historical trend analysis
  - Daily data updates

- **Policy Rates**: 
  - Latest SDFR, SLFR, OPR, SRR rates
  - Historical policy rate changes
  - Real-time updates from CBSL

- **Inflation Metrics**:
  - CCPI (Colombo Consumer Price Index)
  - NCPI (National Consumer Price Index)
  - Year-on-Year and Month-on-Month changes
  - Inflation press release links

- **SL Prosperity Index**:
  - Economic prosperity indicators
  - Historical trend analysis
  - Multiple index components

- **Prices & Wages**:
  - Employment statistics
  - Wage rate indices
  - Price indicators
  - Comprehensive data visualization

### Technical Features
- Automated data scraping from official CBSL sources
- Interactive Plotly visualizations
- Data export capabilities (CSV format)
- Responsive design with Streamlit
- Automatic data refresh
- Historical data storage
- Error handling and data validation

---

## 🛠️ Tech Stack

- **Python**
- **Streamlit** – for the interactive dashboard
- **BeautifulSoup4** – for web scraping
- **Requests** – for fetching CBSL web pages
- **Altair** – for creating interactive charts
- **NumPy** & **Pandas** – for data processing

---

## 📦 Installation

1. **Clone this repository:**
   ```bash
   git clone https://github.com/hasithapramuditha/WebScraping_CBSL.git
   cd WebScraping_CBSL
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Linux/Mac
   venv\Scripts\activate     # On Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 📋 Requirements

The project uses the following Python packages:

```
beautifulsoup4
python-dotenv
streamlit
pandas
requests
numpy
selenium
```

---

## ▶️ Usage

Run the Streamlit app with:

```bash
python -m streamlit run app.py
```

Then open the link in your browser (default: http://localhost:8501).

---

## 📊 Data Sources

- [CBSL Policy Rates Page](https://www.cbsl.gov.lk/en/rates-and-indicators/policy-rates)
- [CBSL Custom Policy Rates API](https://www.cbsl.gov.lk/cbsl_custom/param/plrates.php)
- Additional CBSL data sources to be integrated (inflation rates, exchange rates, reserves, etc.)

---

## 📌 Project Structure

```
WebScraping_CBSL/
│
├── app.py                         # Main Streamlit application
├── exchangeRatesScraper.py        # Exchange rates scraping module
├── inflationScraper.py           # Inflation data scraping module
├── moneySupply.py                # Money supply data scraping
├── policyRatesScraper.py         # Policy rates scraping module
├── price_wages_employment.py     # Prices and wages data module
├── sl_prosperity_index.py        # SL Prosperity Index module
├── requirements.txt              # Python dependencies
├── README.md                     # Project documentation
│
├── Data/                         # Data storage directory
│   ├── cbsl_inflation_2023_2025.csv
│   ├── cbsl_inflation_press_links.csv
│   ├── exchange_rates.csv
│   └── Data.xls
│
├── Data_moneySupply/            # Money supply data directory
│   └── open_market_operations_clean_direct.csv
│
├── downloads/                    # Temporary download directory
└── plots/                       # Generated plots directory
```

---

## 📅 Project Status

### Completed Features ✅
- Exchange rates dashboard with historical data
- Money supply and market operations tracking
- Policy rates monitoring system
- Inflation rates and CPI tracking
- SL Prosperity Index visualization
- Prices and wages data analysis
- Automated data scraping
- Interactive visualizations
- Data export functionality

### Future Enhancements 🔄
- Government securities rates integration
- Banking sector indicators
- Advanced time series analysis
- Machine learning-based predictions
- Mobile-responsive design improvements
- API endpoint development
- Automated scheduled updates
- Cloud deployment (Streamlit Cloud/Heroku)
- Email/notification alerts for significant changes
- Data caching and performance optimization

---

## 📝 License

This project is for educational purposes only. Data belongs to the Central Bank of Sri Lanka (CBSL).