import pandas as pd
from fredapi import Fred
import os
from datetime import datetime
import shutil

# --- CONFIGURATION ---
# SECURITY UPDATE: Use environment variable
API_KEY = os.getenv('FRED_API_KEY')

# Define the Series IDs we want from FRED
# DICTIONARY FORMAT: {'Descriptive Name': 'FRED_Series_ID'}
INDICATORS = {
    'US_TBILL_3M': 'TB3MS',              # PROXY: US 3M T-Bill (Default if Manual File missing)
    'US_CPI': 'CPIAUCSL',                # PROXY: US CPI (Default if Manual File missing)
    'EXCHANGE_RATE': 'DEXBZUS',          # Regressor 2: Philippines / U.S. Foreign Exchange Rate (Daily)
    'US_FED_FUNDS': 'FEDFUNDS'           # Regressor 3: Effective Federal Funds Rate (Global Benchmark)
}

DATE_START = '2010-01-01'
DATE_END = '2024-12-31'

# NEW: External Manual Data Path
MANUAL_SOURCE_FILE = os.path.join('data', 'external', 'manual_ph_rates.csv')

def fetch_data():
    """
    Connects to FRED, pulls specific series, and saves raw CSVs.
    Supports manual override for PH_TBILL_3M via data/external/manual_ph_rates.csv.
    """
    print("--------------------------------------------------")
    print(f"Starting Data Ingestion Job at {datetime.now()}")
    print("--------------------------------------------------")

    # 1. Initialize Client
    if not API_KEY:
        print("CRITICAL ERROR: FRED_API_KEY environment variable not set.")
        print("Please export FRED_API_KEY='your_key_here' before running.")
        return

    try:
        fred = Fred(api_key=API_KEY)
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to initialize FRED API. Error: {e}")
        return

    # 2. Check for Manual Override FIRST
    manual_override_active = False
    if os.path.exists(MANUAL_SOURCE_FILE):
        print(f"\n[PRIORITY] Found Manual PH Data: {MANUAL_SOURCE_FILE}")
        print("   -> Pipeline will use ACTUAL Philippine Rates.")
        
        # Copy manual file to raw folder as the Target
        target_path = os.path.join('data', 'raw', 'PH_TBILL_3M.csv')
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        shutil.copy(MANUAL_SOURCE_FILE, target_path)
        print(f"   -> Copied to: {target_path}")
        manual_override_active = True
    else:
        print("\n[INFO] No Manual PH Data found. Proceeding with US Proxy Data for demonstration.")

    # 3. Iterate through indicators and fetch data
    for name, series_id in INDICATORS.items():
        print(f"Processing: {name}...")
        
        # Determine output path
        output_path = os.path.join('data', 'raw', f'{name}.csv')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Skip US_TBILL if we are using Manual Mode (we already have PH_TBILL)
        # However, we might still want US data as a regressor? 
        # For now, let's keep downloading everything to be safe, but the pipeline downstream needs to know what to use.
        
        print(f"   Fetching from FRED ({series_id})...")
        try:
            # Pull data
            data = fred.get_series(series_id, observation_start=DATE_START, observation_end=DATE_END)
            
            # Convert Series to DataFrame for better handling
            df = pd.DataFrame(data, columns=['value'])
            df.index.name = 'date'
            
            # Basic Validation Log
            missing_count = df['value'].isna().sum()
            row_count = len(df)
            print(f"   SUCCESS. Rows: {row_count}, Missing: {missing_count}")
            
            if row_count == 0:
                print(f"   WARNING: No data returned for {name}. Check Series ID.")

            df.to_csv(output_path)
            print(f"   Saved to: {output_path}")
            
        except Exception as e:
            print(f"   ERROR fetching {name}: {e}")
    
    # If NO manual override, we need to create a copy of US_TBILL as 'PH_TBILL_3M' 
    # so the rest of the pipeline (cleaning/modeling) doesn't break, 
    # BUT we must log this clearly.
    if not manual_override_active:
        print("\n[WARNING] Using US 3M T-Bill as PROXY for PH T-Bill.")
        print("   -> Copying data/raw/US_TBILL_3M.csv to data/raw/PH_TBILL_3M.csv")
        
        src = os.path.join('data', 'raw', 'US_TBILL_3M.csv')
        dst = os.path.join('data', 'raw', 'PH_TBILL_3M.csv')
        
        if os.path.exists(src):
            shutil.copy(src, dst)
        else:
            print("   [ERROR] Could not find US Proxy file to copy!")

    print("--------------------------------------------------")
    print("Ingestion Complete. Check /data/raw/ for files.")
    print("--------------------------------------------------")

if __name__ == "__main__":
    fetch_data()
