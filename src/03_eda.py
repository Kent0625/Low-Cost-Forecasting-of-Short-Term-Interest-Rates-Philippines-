import pandas as pd
import matplotlib.pyplot as plt
import os
from statsmodels.tsa.stattools import grangercausalitytests

def run_diagnostics():
    print("--------------------------------------------------")
    print("Starting Economic Diagnostics (Granger Causality)...")
    print("--------------------------------------------------")

    # 1. Load Data
    data_path = os.path.join('data', 'processed', 'model_data.csv')
    try:
        df = pd.read_csv(data_path, index_col='date', parse_dates=True)
    except FileNotFoundError:
        print("Processed data not found.")
        return

    # 2. Visual EDA (Save to file)
    print("Generating Time Series Plot...")
    plt.figure(figsize=(12, 6))
    plt.plot(df.index, df['PH_TBILL_3M'], label='Target (T-Bill)', linewidth=2)
    plt.plot(df.index, df['FED_FUNDS'], label='US Fed Funds', linestyle='--')
    plt.plot(df.index, df['FX_RATE'], label='FX Rate (Scaled)', alpha=0.5) # Scale issues but just for trend
    plt.title('PH T-Bill vs Regressors (Proxy Data)')
    plt.legend()
    
    # Ensure notebooks folder exists for plots
    os.makedirs('notebooks', exist_ok=True)
    plot_path = os.path.join('notebooks', 'eda_plot.png')
    plt.savefig(plot_path)
    print(f"   Saved plot to: {plot_path}")

    # 3. Granger Causality
    # "Does X cause Y?" -> Matrix [Y, X]
    target = 'PH_TBILL_3M'
    regressors = ['CPI_lag1', 'FX_lag1', 'FED_lag1']
    
    for reg in regressors:
        print(f"\n--- Testing: Does {reg} Granger-Cause {target}? ---")
        # Check if we have enough data
        if reg not in df.columns:
            print(f"   Skipping {reg} (Not in columns)")
            continue
            
        # Data for test: [Target, Regressor]
        test_data = df[[target, reg]].dropna()
        
        try:
            # Run test for lags 1 to 3
            gc_res = grangercausalitytests(test_data, maxlag=3, verbose=False)
            
            # Extract p-values for 'ssr_ftest' (F-test)
            p_values = [gc_res[i][0]['ssr_ftest'][1] for i in range(1, 4)]
            min_p = min(p_values)
            
            print(f"   P-Values (Lags 1,2,3): {[round(p, 4) for p in p_values]}")
            if min_p < 0.05:
                print(f"   RESULT: SIGNIFICANT (p < 0.05). Keep {reg} in model.")
            else:
                print(f"   RESULT: INSIGNIFICANT (p >= 0.05). Consider dropping {reg}.")
                
        except Exception as e:
            print(f"   Error running test: {e}")

    print("--------------------------------------------------")
    print("Diagnostics Complete.")
    print("--------------------------------------------------")

if __name__ == "__main__":
    run_diagnostics()
