import pandas as pd
import numpy as np
import pmdarima as pm
from sklearn.metrics import mean_squared_error
import joblib
import matplotlib.pyplot as plt
import os
from statsmodels.tsa.stattools import grangercausalitytests
from statsmodels.stats.diagnostic import acorr_ljungbox

def select_features(df, target_col, candidate_cols, maxlag=3):
    """
    Dynamically selects features based on Granger Causality.
    Returns a list of columns where p-value < 0.05.
    """
    print("\n--- Feature Selection (Granger Causality) ---")
    selected = []
    
    for col in candidate_cols:
        if col not in df.columns:
            continue
            
        test_data = df[[target_col, col]].dropna()
        try:
            # verbose=False to suppress huge output
            gc_res = grangercausalitytests(test_data, maxlag=maxlag, verbose=False)
            
            # Check p-values for lags 1 to maxlag
            # gc_res structure: {lag: ({tests}, [objs])}
            # ssr_ftest is index 0 in the tuple of tests
            p_values = [gc_res[i][0]['ssr_ftest'][1] for i in range(1, maxlag+1)]
            min_p = min(p_values)
            
            if min_p < 0.05:
                print(f"   [KEEP] {col} (p={min_p:.4f})")
                selected.append(col)
            else:
                print(f"   [DROP] {col} (p={min_p:.4f})")
                
        except Exception as e:
            print(f"   [ERROR] Could not test {col}: {e}")
            
    return selected

def train_models():
    print("--------------------------------------------------")
    print("Starting Modeling Phase (Baseline vs SARIMAX)...")
    print("--------------------------------------------------")

    # 1. Load Data
    data_path = os.path.join('data', 'processed', 'model_data.csv')
    try:
        df = pd.read_csv(data_path, index_col='date', parse_dates=True)
    except FileNotFoundError:
        print("Processed data not found.")
        return

    # 2. Train/Test Split (Last 24 months for testing to be robust)
    TEST_MONTHS = 24
    train = df.iloc[:-TEST_MONTHS]
    test = df.iloc[-TEST_MONTHS:]
    
    y_train = train['PH_TBILL_3M']
    y_test = test['PH_TBILL_3M']
    
    # 3. Dynamic Feature Selection
    candidate_features = ['CPI_lag1', 'FED_lag1', 'FX_lag1']
    # We run selection on the TRAINING set only to avoid data leakage
    selected_features = select_features(train, 'PH_TBILL_3M', candidate_features)
    
    if not selected_features:
        print("WARNING: No significant features found. SARIMAX will likely degrade to ARIMA.")
        selected_features = candidate_features # Fallback to candidates or handle empty
    
    X_train = train[selected_features]
    X_test = test[selected_features]
    
    print(f"\nFinal Features: {selected_features}")
    print(f"Train Size: {len(train)}")
    print(f"Test Size: {len(test)}")

    # 4. Baseline Model (Univariate ARIMA)
    print("\n--- Training Baseline (Univariate ARIMA) ---")
    baseline_model = pm.auto_arima(y_train, 
                                   start_p=0, start_q=0,
                                   max_p=5, max_q=5,
                                   d=1, 
                                   seasonal=False,
                                   stepwise=True,
                                   suppress_warnings=True,
                                   error_action='ignore')
    
    print(f"Best Baseline ARIMA Order: {baseline_model.order}")
    
    baseline_preds = baseline_model.predict(n_periods=len(test))
    baseline_rmse = np.sqrt(mean_squared_error(y_test, baseline_preds))
    print(f"Baseline RMSE: {baseline_rmse:.4f}")

    # 5. SARIMAX Model (With Exogenous Regressors)
    print("\n--- Training SARIMAX (Macro Regressors) ---")
    sarimax_model = pm.auto_arima(y_train, 
                                  X=X_train,
                                  start_p=0, start_q=0,
                                  max_p=5, max_q=5,
                                  d=1,
                                  seasonal=False,
                                  stepwise=True,
                                  suppress_warnings=True,
                                  error_action='ignore')
    
    print(f"Best SARIMAX Order: {sarimax_model.order}")
    
    sarimax_preds = sarimax_model.predict(n_periods=len(test), X=X_test)
    sarimax_rmse = np.sqrt(mean_squared_error(y_test, sarimax_preds))
    print(f"SARIMAX RMSE: {sarimax_rmse:.4f}")

    # 6. Directional Accuracy (New Metric)
    # Did the model predict the correct sign of change?
    actual_diff = y_test.diff().dropna()
    pred_diff = pd.Series(sarimax_preds, index=y_test.index).diff().dropna()
    
    # Align indices just in case
    common_idx = actual_diff.index.intersection(pred_diff.index)
    actual_dir = np.sign(actual_diff.loc[common_idx])
    pred_dir = np.sign(pred_diff.loc[common_idx])
    
    dir_acc = (actual_dir == pred_dir).mean()
    print(f"SARIMAX Directional Accuracy: {dir_acc:.2%}")

    # 7. Comparison & Selection
    print("\n--- Model Comparison ---")
    if sarimax_rmse < baseline_rmse:
        print(f"WINNER: SARIMAX (Improvement: {baseline_rmse - sarimax_rmse:.4f})")
        best_model = sarimax_model
        best_name = "SARIMAX"
    else:
        print(f"WINNER: Baseline (SARIMAX failed to beat simple history)")
        best_model = baseline_model
        best_name = "Baseline_ARIMA"

    # 8. Residual Diagnostics (Ljung-Box)
    print("\n--- Residual Diagnostics (Ljung-Box Test) ---")
    residuals = best_model.resid()
    lb_test = acorr_ljungbox(residuals, lags=[10], return_df=True)
    lb_pvalue = lb_test['lb_pvalue'].values[0]
    
    print(f"Ljung-Box p-value (lag=10): {lb_pvalue:.4f}")
    if lb_pvalue < 0.05:
        print("WARNING: Residuals are NOT White Noise (p < 0.05). Model has bias/autocorrelation.")
    else:
        print("PASS: Residuals look like White Noise (p >= 0.05).")

    # 9. Save Best Model
    os.makedirs('models', exist_ok=True) 
    model_path = os.path.join('models', 'best_rate_model.pkl')
    joblib.dump(best_model, model_path)
    print(f"Saved Best Model to: {model_path}")
    
    sarimax_path = os.path.join('models', 'sarimax_model.pkl')
    joblib.dump(sarimax_model, sarimax_path)
    print(f"Saved SARIMAX Model for Analysis to: {sarimax_path}")

    # 10. Visualization
    plt.figure(figsize=(12, 6))
    plt.plot(train.index, y_train, label='Train')
    plt.plot(test.index, y_test, label='Test (Actual)')
    plt.plot(test.index, baseline_preds, label=f'Baseline (RMSE={baseline_rmse:.3f})', linestyle='--')
    plt.plot(test.index, sarimax_preds, label=f'SARIMAX (RMSE={sarimax_rmse:.3f}, Acc={dir_acc:.0%})', linestyle='-.')
    plt.title(f'Forecast Comparison: {best_name} Won')
    plt.legend()
    
    os.makedirs('notebooks', exist_ok=True)
    plot_path = os.path.join('notebooks', 'forecast_comparison.png')
    plt.savefig(plot_path)
    print(f"Saved Forecast Plot to: {plot_path}")
    print("--------------------------------------------------")

if __name__ == "__main__":
    train_models()
