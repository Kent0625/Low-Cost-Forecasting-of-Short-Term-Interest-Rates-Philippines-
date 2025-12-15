# Automated Rate Forecasting Pipeline (Prototype)

## Executive Summary
This project demonstrates a production-grade **Time-Series Forecasting Pipeline** designed to predict 3-Month Treasury Bill movements. It utilizes a modular architecture (Ingestion -> Cleaning -> Modeling -> Reporting) to ensure reproducibility and scalability.

**Note on Data Source:**
For demonstration purposes, this prototype uses **US Treasury Bill** and **US CPI** data (sourced from FRED) as proxies for the Philippine market. The pipeline is designed to be "Region-Agnostic." To deploy this for the Philippines:
1.  Download the official Treasury Bill rates from the [BSP Website](https://www.bsp.gov.ph).
2.  Save the file as `data/external/manual_ph_rates.csv`.
3.  The pipeline will automatically detect and prioritize this local file over the US proxy.

## Model Performance
We compared two modeling approaches to establish a rigorous benchmark:

| Model | RMSE (Root Mean Squared Error) | Verdict |
| :--- | :--- | :--- |
| **Baseline (Univariate ARIMA)** | **0.9828** | **WINNER** |
| SARIMAX (with Macro Regressors) | 1.2434 | Challenger |

**Conclusion:** The simple history-based model (ARIMA) outperformed the complex macro-model (SARIMAX). This indicates that for the current regime, "Trend Following" is a superior strategy to "Macro Fundamentals."

## Economic Diagnostics (The "Sanity Check")
During the SARIMAX modeling phase, we observed a **Negative Coefficient (-0.23)** for the Fed Funds Rate.
*   **Economic Theory:** Higher Fed Rates -> Higher T-Bill Yields (Positive Correlation).
*   **Model Finding:** Higher Fed Rates -> Lower T-Bill Yields (Negative Correlation).

**Diagnosis:**
This is a statistical artifact caused by **Multicollinearity**. The Auto-Regressive (AR) terms of the model are already capturing the primary upward trend of rates. The Fed Funds variable, being highly correlated with the trend, is forced to fit the residual noise, resulting in a sign inversion. **This coefficient should not be interpreted as a true economic inverse relationship.**

## Key Technical Features
1.  **Look-Ahead Bias Prevention:** Strict lag engineering ($t-2$ for CPI) to account for real-world reporting delays.
2.  **Stationarity Checks:** Automated ADF tests to ensure data is differenced ($d=1$) before modeling.
3.  **Dynamic Feature Selection:** Uses **Granger Causality** tests to automatically drop irrelevant macro variables (e.g., FX Rate was dropped in this run).
4.  **Hybrid Data Pipeline:** Capable of switching between API-pulled data (FRED) and manual local uploads (BSP CSVs) seamlessly.