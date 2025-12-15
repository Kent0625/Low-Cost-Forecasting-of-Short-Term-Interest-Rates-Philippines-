# Low-Cost Forecasting of Short-Term Interest Rates (Philippines)

## Overview
This project builds an automated pipeline to forecast 3-Month Treasury Bill movements using public macroeconomic indicators from the FRED API. It is designed to demonstrate a "Junior Financial Data Scientist" workflow, including data ingestion, cleaning, stationarity testing, and SARIMAX modeling.

**Note on Data:** Due to the unavailability of specific Philippines monthly T-Bill and CPI series on the public FRED API, this project uses **US 3-Month T-Bills (TB3MS)** and **US CPI (CPIAUCSL)** as proxies to demonstrate the *technical pipeline mechanics*. Real-world application would substitute these with proprietary data (Bloomberg/CEIC).

## Architecture
The pipeline is modularized into `src/` scripts:

1.  **Ingestion (`01_ingestion.py`):** Pulls raw data from FRED.
2.  **Cleaning (`02_cleaning.py`):** Resamples to monthly, creates lags (t-1, t-2), and aligns timestamps.
3.  **Diagnostics (`03_eda.py`):** Runs Granger Causality tests (`statsmodels`).
4.  **Stationarity (`04_stationarity.py`):** Performs ADF tests to determine differencing ($d$).
5.  **Modeling (`05_modeling.py`):** Trains Baseline ARIMA vs. SARIMAX (with Regressors) using `pmdarima` (Auto-ARIMA).
6.  **Reporting (`06_reporting.py`):** Generates a strategic memo with coefficient analysis.

## Key Findings
-   **Winner:** Baseline ARIMA (Univariate) outperformed the Macro-based SARIMAX model (RMSE 0.98 vs 1.25).
-   **Macro Sensitivity:**
    -   **CPI (Lag 1):** Significant positive relationship (+0.04).
    -   **Fed Funds (Lag 1):** Significant negative relationship (-0.23).
    -   **FX Rate:** Insignificant in this specific proxy setup.
-   **Strategy:** Trend-following is currently superior to macro-based forecasting for this dataset, but Fed Funds remains a key risk monitor.

## Setup & Usage

### Prerequisites
-   Python 3.x
-   FRED API Key

### Installation
```bash
pip install pandas fredapi openpyxl statsmodels matplotlib scipy pmdarima sklearn joblib
```

### Execution
Run the scripts in order from the project root:
```bash
python src/01_ingestion.py
python src/02_cleaning.py
python src/03_eda.py
python src/04_stationarity.py
python src/05_modeling.py
python src/06_reporting.py
```

## Project Structure
-   `data/`: Stores raw and processed CSVs.
-   `models/`: Stores serialized `.pkl` models.
-   `notebooks/`: Stores generated plots (`eda_plot.png`, `forecast_comparison.png`).
-   `src/`: Source code.

---
*Created by Gemini CLI Agent - Dec 15, 2025*
