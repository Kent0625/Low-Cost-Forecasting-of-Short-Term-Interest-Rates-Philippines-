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
    Implements Metadata Watermarking for Data Lineage.
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
        
        # Load Manual Data, Add Watermark, Save as Target
        try:
            target_path = os.path.join('data', 'raw', 'PH_TBILL_3M.csv')
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            df_manual = pd.read_csv(MANUAL_SOURCE_FILE, index_col=0, parse_dates=True)
            # WATERMARKING: Tag the source
            df_manual['data_source_type'] = 'MANUAL_PH_DATA'
            
            df_manual.to_csv(target_path)
            print(f"   -> Watermarked & Saved to: {target_path}")
            manual_override_active = True
        except Exception as e:
            print(f"   [ERROR] Failed to process manual file: {e}")
    else:
        print("\n[INFO] No Manual PH Data found. Proceeding with US Proxy Data for demonstration.")

    # 3. Iterate through indicators and fetch data
    for name, series_id in INDICATORS.items():
        print(f"Processing: {name}...")
        
        # Determine output path
        output_path = os.path.join('data', 'raw', f'{name}.csv')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        print(f"   Fetching from FRED ({series_id})...")
        try:
            # Pull data
            data = fred.get_series(series_id, observation_start=DATE_START, observation_end=DATE_END)
            
            # Convert Series to DataFrame for better handling
            df = pd.DataFrame(data, columns=['value'])
            df.index.name = 'date'
            
            # WATERMARKING: Tag the source
            # If it's one of our proxies, label it as such. Otherwise, standard API data.
            if name in ['US_TBILL_3M', 'US_CPI']:
                df['data_source_type'] = 'PROXY_US_DATA'
            else:
                df['data_source_type'] = 'FRED_API_DATA'
            
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
    
    # If NO manual override, use the PROXY as the Target
    if not manual_override_active:
        print("\n[WARNING] Using US 3M T-Bill as PROXY for PH T-Bill.")
        print("   -> Copying data/raw/US_TBILL_3M.csv to data/raw/PH_TBILL_3M.csv")
        
        src = os.path.join('data', 'raw', 'US_TBILL_3M.csv')
        dst = os.path.join('data', 'raw', 'PH_TBILL_3M.csv')
        
        if os.path.exists(src):
            # Read, confirm watermark, and save to target location
            try:
                df_proxy = pd.read_csv(src, index_col='date', parse_dates=True)
                # Ensure it's marked as proxy (should be already, but double check)
                df_proxy['data_source_type'] = 'PROXY_US_DATA' 
                df_proxy.to_csv(dst)
                print(f"   -> Copied & Verified Watermark at: {dst}")
            except Exception as e:
                print(f"   [ERROR] Failed to copy proxy file: {e}")
        else:
            print("   [ERROR] Could not find US Proxy file to copy!")

    print("--------------------------------------------------")
    print("Ingestion Complete. Check /data/raw/ for files.")
    print("--------------------------------------------------")

if __name__ == "__main__":
    fetch_data()
