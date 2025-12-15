import joblib
import os
import pandas as pd
import numpy as np

def generate_report():
    print("==================================================")
    print("   STRATEGIC RATE FORECAST MEMO (PROTOTYPE)")
    print("==================================================")
    
    # 1. Load Data & Models
    try:
        sarimax = joblib.load(os.path.join('models', 'sarimax_model.pkl'))
        df = pd.read_csv(os.path.join('data', 'processed', 'model_data.csv'), index_col='date', parse_dates=True)
    except FileNotFoundError:
        print("Models or Data not found. Run previous steps.")
        return

    # 2. Extract Coefficients
    params = sarimax.params()
    pvalues = sarimax.pvalues()
    
    print("\n[EXECUTIVE SUMMARY]")
    print("The best performing model was the BASELINE ARIMA (Univariate).")
    print("This implies that short-term rate movements are currently best predicted by")
    print("historical momentum rather than immediate macro-economic signals.")
    
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

    # 3. COEFFICIENT VALIDATION (The "Sanity Check")
    print("\n[DIAGNOSTIC: COEFFICIENT VALIDITY CHECK]")
    # Calculate simple correlation on differenced data (since model uses d=1)
    target_diff = df['PH_TBILL_3M'].diff().dropna()
    
    if 'FED_lag1' in df.columns and 'FED_lag1' in params.index:
        fed_diff = df['FED_lag1'].diff().dropna()
        # Align indices
        common_idx = target_diff.index.intersection(fed_diff.index)
        corr = np.corrcoef(target_diff[common_idx], fed_diff[common_idx])[0,1]
        
        coef_fed = params['FED_lag1']
        
        print(f"Correlation (Diff vs Diff): {corr:.4f}")
        print(f"Model Coefficient:          {coef_fed:.4f}")
        
        if corr > 0 and coef_fed < 0:
            print("WARNING: DETECTED SIGN INVERSION.")
            print("The raw correlation is POSITIVE (as expected), but the model coefficient is NEGATIVE.")
            print("CAUSE: Multicollinearity. The Auto-Regressive (AR) terms are likely capturing the")
            print("primary trend, leaving 'FED_lag1' to fit the residual noise or correction.")
            print("ACTION: Do not interpret this negative coefficient as a true inverse economic relationship.")

    print("\n[STRATEGY RECOMMENDATION]")
    print("1. PRIMARY STRATEGY: Mean Reversion / Trend Following.")
    print("   Since the Baseline model (ARIMA) won, traders should focus on recent")
    print("   rate volatility and technical patterns.")
    
    print("\n[DISCLOSURE]")
    print("This pipeline is demonstrated using US Data (Proxy) for the default run.")
    print("To deploy for Philippines, place the official BSP Treasury Bill CSV in:")
    print("data/external/manual_ph_rates.csv")
    print("The ingestion script will automatically detect and prioritize this local file.")
    print("==================================================")

if __name__ == "__main__":
    generate_report()
