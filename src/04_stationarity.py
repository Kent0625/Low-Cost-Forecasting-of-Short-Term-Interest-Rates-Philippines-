import pandas as pd
from statsmodels.tsa.stattools import adfuller
import os

def check_stationarity():
    print("--------------------------------------------------")
    print("Starting Stationarity Check (ADF Test)...")
    print("--------------------------------------------------")

    data_path = os.path.join('data', 'processed', 'model_data.csv')
    try:
        df = pd.read_csv(data_path, index_col='date', parse_dates=True)
    except FileNotFoundError:
        print("Processed data not found.")
        return

    series = df['PH_TBILL_3M'].dropna()
    
    # Test Levels (d=0)
    print("Testing Levels (Raw Data)...")
    result = adfuller(series)
    p_value = result[1]
    print(f"   ADF Statistic: {result[0]}")
    print(f"   p-value: {p_value}")
    
    d = 0
    if p_value > 0.05:
        print("   Result: Non-Stationary (p > 0.05). Needs Differencing.")
        
        # Test First Difference (d=1)
        print("\nTesting First Difference (d=1)...")
        diff_series = series.diff().dropna()
        result_diff = adfuller(diff_series)
        p_value_diff = result_diff[1]
        print(f"   ADF Statistic: {result_diff[0]}")
        print(f"   p-value: {p_value_diff}")
        
        if p_value_diff <= 0.05:
            print("   Result: Stationary (p <= 0.05). Use d=1.")
            d = 1
        else:
            print("   Result: Still Non-Stationary. Consider d=2.")
            d = 2
    else:
        print("   Result: Stationary (p <= 0.05). Use d=0.")

    print(f"\nFinal Recommendation: Order of Integration d = {d}")
    print("--------------------------------------------------")

if __name__ == "__main__":
    check_stationarity()
