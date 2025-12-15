import pandas as pd
from fredapi import Fred
import os
from datetime import datetime

# --- CONFIGURATION ---
# TODO: In a production app, use environment variables (e.g., os.getenv('FRED_API_KEY'))
API_KEY = '9976e35cd1d244227ffd8796779aa149' 

# Define the Series IDs we want from FRED
# DICTIONARY FORMAT: {'Descriptive Name': 'FRED_Series_ID'}
INDICATORS = {
    'PH_TBILL_3M': 'TB3MS',              # PLACEHOLDER: Using US 3M T-Bill as PH data is unavailable on FRED
    'PH_CPI': 'CPIAUCSL',                # PLACEHOLDER: Using US CPI as PH data is unavailable on FRED
    'EXCHANGE_RATE': 'DEXBZUS',          # Regressor 2: Philippines / U.S. Foreign Exchange Rate (Daily)
    'US_FED_FUNDS': 'FEDFUNDS'           # Regressor 3: Effective Federal Funds Rate (Global Benchmark)
}

DATE_START = '2010-01-01'
DATE_END = '2024-12-31'

def fetch_data():
    """
    Connects to FRED, pulls specific series, and saves raw CSVs.
    """
    print("--------------------------------------------------")
    print(f"Starting Data Ingestion Job at {datetime.now()}")
    print("--------------------------------------------------")

    # 1. Initialize Client
    try:
        fred = Fred(api_key=API_KEY)
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to initialize FRED API. Check your key. Error: {e}")
        return

    # 2. Iterate through indicators and fetch data
    for name, series_id in INDICATORS.items():
        print(f"Attempting to fetch: {name} ({series_id})...")
        
        try:
            # Pull data
            data = fred.get_series(series_id, observation_start=DATE_START, observation_end=DATE_END)
            
            # Convert Series to DataFrame for better handling
            df = pd.DataFrame(data, columns=['value'])
            df.index.name = 'date'
            
            # 3. Basic Validation Log
            missing_count = df['value'].isna().sum()
            row_count = len(df)
            print(f"   SUCCESS. Rows: {row_count}, Missing: {missing_count}")
            
            if row_count == 0:
                print(f"   WARNING: No data returned for {name}. Check Series ID.")

            # 4. Save to Raw Data Folder
            # Construct file path: data/raw/PH_TBILL_3M.csv
            # Note: We need to go up one level from src if we run from inside src, or run from root
            # The script assumes it's running from project root based on 'data/raw' path.
            output_path = os.path.join('data', 'raw', f'{name}.csv')
            
            # Ensure directory exists (safety check)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            df.to_csv(output_path)
            print(f"   Saved to: {output_path}")
            
        except Exception as e:
            print(f"   ERROR fetching {name}: {e}")

    print("--------------------------------------------------")
    print("Ingestion Complete. Check /data/raw/ for files.")
    print("--------------------------------------------------")

if __name__ == "__main__":
    fetch_data()
