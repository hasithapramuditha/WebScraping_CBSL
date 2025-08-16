# 📊 Central Bank of Sri Lanka Data Dashboard

A comprehensive **Streamlit dashboard** to visualize **economic indicators and financial data** published by the **Central Bank of Sri Lanka (CBSL)**.

This project scrapes real-time data from CBSL websites and displays them in interactive dashboards. Currently features policy rates (SDFR, SLFR, OPR, SRR) with plans to expand to other key economic indicators.

---

## 🚀 Features

- Fetches **latest CBSL economic data** directly from official sources
- **Policy Rates Module**: SDFR, SLFR, OPR, SRR with real-time updates
- Displays data in **table view** and **interactive charts**
- Supports **on-demand refresh** for up-to-date values
- Sidebar navigation for multiple data sections
- Tooltips and detailed insights for each economic indicator

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
├── main.py                   # Main Streamlit app
├── requirements.txt          # Python dependencies
├── README.md                 # Project documentation
├── policyRatesScraper.py     # Policy rates scraper module
├── inflation_scraper.py      # (Planned)
├── exchange_scraper.py       # (Planned)
└── reserves_scraper.py       # (Planned)
```

---

## 📅 Roadmap

### Phase 1 (Current)
- ✅ Policy rates dashboard (SDFR, SLFR, OPR, SRR)

### Phase 2 (In Development)
- 🔄 Inflation rates and consumer price index
- 🔄 Exchange rates (LKR vs major currencies)
- 🔄 Foreign reserves data

### Phase 3 (Planned)
- 📋 Government securities rates
- 📋 Banking sector indicators
- 📋 Historical data analysis and trends
- 📋 Automated daily updates with scheduling
- 📋 Deploy online (Streamlit Cloud or Heroku)

---

## 📝 License

This project is for educational purposes only. Data belongs to the Central Bank of Sri Lanka (CBSL).