import unittest
from unittest.mock import patch, MagicMock, call
import os
import pandas as pd
import sys
import importlib.util

# Helper to load the script as a module
def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

# Load the ingestion script
ingestion = load_module("ingestion", os.path.join("src", "01_ingestion.py"))

class TestIngestion(unittest.TestCase):

    def setUp(self):
        # Inject a dummy API key so the script doesn't exit early
        ingestion.API_KEY = 'test_key'

    def test_manual_override_detected(self):
        """
        Test that if manual file exists, it is loaded and watermarked.
        """
        manual_path = ingestion.MANUAL_SOURCE_FILE
        
        # Mocking
        with patch('os.path.exists') as mock_exists, \
             patch('pandas.read_csv') as mock_read, \
             patch('pandas.DataFrame.to_csv') as mock_to_csv, \
             patch.object(ingestion, 'Fred') as mock_fred:
            
            # 1. Setup Manual File Exists
            def side_effect_exists(path):
                if path == manual_path:
                    return True
                return False # Let directory creation checks pass/fail naturally or mock them? 
                # Better: return True for manual, False for others, OR just True for manual.
                # The script also checks for proxy file existence later if manual fails.
                
            mock_exists.side_effect = lambda p: True if p == manual_path else False
            
            # 2. Setup Dummy Data
            mock_df = pd.DataFrame({'value': [100]}, index=['2020-01-01'])
            mock_read.return_value = mock_df
            
            # 3. Run
            ingestion.fetch_data()
            
            # 4. Assertions
            # Should have read the manual file
            mock_read.assert_any_call(manual_path, index_col=0, parse_dates=True)
            
            # Should have watermarked it
            self.assertIn('data_source_type', mock_df.columns)
            self.assertEqual(mock_df['data_source_type'].iloc[0], 'MANUAL_PH_DATA')
            
            # Should NOT have initialized Fred (optimization) or at least not used it for the target
            # The script logic iterates INDICATORS. If manual override is active, 
            # it might still fetch others. 
            # But specific to the Target PH_TBILL, it should use the manual file.
            pass

    def test_proxy_fallback(self):
        """
        Test that if manual file missing, we fetch from FRED and tag as PROXY.
        """
        with patch('os.path.exists') as mock_exists, \
             patch('pandas.DataFrame') as mock_df_cls, \
             patch.object(ingestion, 'Fred') as mock_fred_cls:
            
            # 1. Setup: No manual file
            def side_effect_exists(path):
                if 'manual' in path:
                    return False
                if 'US_TBILL_3M.csv' in path: 
                    return True
                return False
            mock_exists.side_effect = side_effect_exists
            
            # 2. Mock Fred Response
            mock_fred_instance = mock_fred_cls.return_value
            mock_fred_instance.get_series.return_value = [5.5]
            
            # 3. Setup Mock DataFrame behavior
            mock_df = mock_df_cls.return_value
            # When read_csv is called (which is pd.read_csv, handled by pandas.DataFrame if we patch read_csv?)
            # Wait, the script calls `pd.read_csv`. 
            # If I patch `pandas.DataFrame`, `pd.read_csv` is NOT patched.
            # But the script uses `pd.DataFrame(data)` for the loop.
            # And `pd.read_csv` for the COPY step.
            
            # I need to patch `read_csv` as well to return the SAME mock_df (or another mock).
            # To simplify, let's make read_csv return mock_df too.
            
            with patch('pandas.read_csv') as mock_read:
                mock_read.return_value = mock_df
                
                # 4. Run
                ingestion.fetch_data()
                
                # 5. Verify Call Order
                # We expect:
                # ...
                # df['data_source_type'] = 'PROXY_US_DATA'
                # df.to_csv(...US_TBILL_3M.csv)
                # ...
                
                success = False
                found_watermark = False
                
                # Iterate through all calls on the mock_df instance
                for name, args, kwargs in mock_df.mock_calls:
                    
                    if name == '__setitem__' and args[0] == 'data_source_type':
                        if args[1] == 'PROXY_US_DATA':
                            found_watermark = True
                        else:
                            # If we switch to another type (like FRED_API), reset unless we already found success
                            # Actually, we treat each file independently.
                            pass
                                
                    if name == 'to_csv':
                        path = args[0]
                        if 'US_TBILL_3M.csv' in str(path):
                            if found_watermark:
                                success = True
                                break # Found our target, stop checking
                
                self.assertTrue(success, "Sequence (Set PROXY -> Save US_TBILL) not found!")

if __name__ == '__main__':
    unittest.main()
