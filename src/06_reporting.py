import joblib
import os
import pandas as pd

def generate_report():
    print("==================================================")
    print("   STRATEGIC RATE FORECAST MEMO (PHILIPPINES)")
    print("==================================================")
    
    # 1. Load Models
    try:
        sarimax = joblib.load(os.path.join('models', 'sarimax_model.pkl'))
        # We could load best_model too, but we know Baseline won.
    except FileNotFoundError:
        print("Models not found. Run previous steps.")
        return

    # 2. Extract Coefficients
    params = sarimax.params()
    pvalues = sarimax.pvalues()
    
    print("\n[EXECUTIVE SUMMARY]")
    print("The best performing model was the BASELINE ARIMA (Univariate).")
    print("This implies that short-term rate movements are currently best predicted by")
    print("historical momentum rather than immediate macro-economic signals (Proxies used).")
    
    print("\n[MACRO SENSITIVITY ANALYSIS]")
    print("However, our structural model (SARIMAX) suggests the following relationships:")
    
    regressors = ['CPI_lag1', 'FED_lag1', 'FX_lag1']
    for reg in regressors:
        if reg in params.index:
            coef = params[reg]
            pval = pvalues[reg]
            significance = "(Significant)" if pval < 0.05 else "(Not Significant)"
            
            print(f"\n> {reg}: {coef:.4f} {significance}")
            print(f"  Interpretation: A 1-unit increase in {reg} is associated with a")
            print(f"  {coef:.4f} change in the 3-Month T-Bill Rate next month.")
    
    print("\n[STRATEGY RECOMMENDATION]")
    print("1. PRIMARY STRATEGY: Mean Reversion / Trend Following.")
    print("   Since the Baseline model (ARIMA) won, traders should focus on recent")
    print("   rate volatility and technical patterns.")
    
    print("2. RISK MONITOR: Fed Funds Rate (FED_lag1).")
    if 'FED_lag1' in params.index and pvalues['FED_lag1'] < 0.05:
         print("   Despite the Baseline winning, the Fed Funds Rate shows a statistically")
         print("   significant impact. Any hawkish surprise from the US Fed should be")
         print("   viewed as a leading indicator for higher PH rates.")
    
    print("\n[DISCLOSURE]")
    print("This analysis used PROXY data for PH T-Bills and CPI due to data availability.")
    print("Real-world application requires subscription to Bloomberg/CEIC for precise local data.")
    print("==================================================")

if __name__ == "__main__":
    generate_report()
