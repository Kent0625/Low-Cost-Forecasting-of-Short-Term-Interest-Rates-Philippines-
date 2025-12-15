import pandas as pd
import os

def process_data():
    print("--------------------------------------------------")
    print("Starting Data Cleaning & Feature Engineering...")
    print("--------------------------------------------------")

    # 1. Load Raw Data
    # Parse dates as index
    try:
        df_target = pd.read_csv(os.path.join('data', 'raw', 'PH_TBILL_3M.csv'), index_col='date', parse_dates=True)
        df_cpi = pd.read_csv(os.path.join('data', 'raw', 'PH_CPI.csv'), index_col='date', parse_dates=True)
        df_fx = pd.read_csv(os.path.join('data', 'raw', 'EXCHANGE_RATE.csv'), index_col='date', parse_dates=True)
        df_fed = pd.read_csv(os.path.join('data', 'raw', 'US_FED_FUNDS.csv'), index_col='date', parse_dates=True)
    except FileNotFoundError as e:
        print(f"CRITICAL ERROR: Missing raw files. Run ingestion first. {e}")
        return

    # 2. Resampling & alignment (Month End)
    # Target (already monthly, but let's ensure end-of-month index)
    df_target = df_target.resample('ME').last() # Interest rates are usually snapshots or averages. 'last' is fine for T-Bill yields.
    df_target.columns = ['PH_TBILL_3M']

    # CPI (Monthly) - Use Lag 1 and Lag 2
    # Note: CPI release is lagged. We use t-1 or t-2 to predict t.
    df_cpi = df_cpi.resample('ME').last()
    df_cpi.columns = ['CPI']
    df_cpi['CPI_lag1'] = df_cpi['CPI'].shift(1)
    df_cpi['CPI_lag2'] = df_cpi['CPI'].shift(2)

    # FX (Daily) -> Monthly Average
    df_fx = df_fx.resample('ME').mean()
    df_fx.columns = ['FX_RATE']
    df_fx['FX_lag1'] = df_fx['FX_RATE'].shift(1)

    # Fed Funds (Monthly) -> Lag 1
    df_fed = df_fed.resample('ME').last()
    df_fed.columns = ['FED_FUNDS']
    df_fed['FED_lag1'] = df_fed['FED_FUNDS'].shift(1)

    # 3. Merge All
    # We want to predict PH_TBILL_3M(t) using lagged regressors.
    master_df = pd.concat([df_target, df_cpi, df_fx, df_fed], axis=1)

    # 4. Filter & Clean
    # Drop rows where Target is NaN (we can't train on them)
    master_df = master_df.dropna(subset=['PH_TBILL_3M'])
    
    # Drop rows where regressors are NaN (due to lags)
    # We lose the first 2 months because of CPI_lag2
    original_len = len(master_df)
    master_df = master_df.dropna()
    final_len = len(master_df)
    
    print(f"Data Merged. Rows: {original_len} -> {final_len} (after dropping NaNs)")

    # 5. Save
    output_path = os.path.join('data', 'processed', 'model_data.csv')
    master_df.to_csv(output_path)
    print(f"Saved Processed Data to: {output_path}")
    print(master_df.head())
    print("--------------------------------------------------")

if __name__ == "__main__":
    process_data()
