from fredapi import Fred
import os

# API Key
API_KEY = '9976e35cd1d244227ffd8796779aa149'
fred = Fred(api_key=API_KEY)

def check_id(series_id):
    print(f"Checking ID: {series_id}")
    try:
        s = fred.get_series(series_id, observation_start='2020-01-01', observation_end='2020-02-01')
        print(f"Found! Length: {len(s)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_id('IRSTCI01PHM156N')
    check_id('CPALTT01PHM657N')
    check_id('PHLCPIALLMINMEI') # The original one
