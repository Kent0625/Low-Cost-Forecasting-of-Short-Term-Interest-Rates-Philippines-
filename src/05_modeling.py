import pandas as pd
import numpy as np
import pmdarima as pm
from sklearn.metrics import mean_squared_error
import joblib
import matplotlib.pyplot as plt
import os

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
    
    X_cols = ['CPI_lag1', 'FED_lag1', 'FX_lag1']
    X_train = train[X_cols]
    X_test = test[X_cols]
    
    print(f"Train Size: {len(train)}")
    print(f"Test Size: {len(test)}")

    # 3. Baseline Model (Univariate ARIMA)
    print("\n--- Training Baseline (Univariate ARIMA) ---")
    # trace=True to see progress, error_action='ignore' to skip failed fits
    baseline_model = pm.auto_arima(y_train, 
                                   start_p=0, start_q=0,
                                   max_p=5, max_q=5,
                                   d=1, # We found d=1 in stationarity check
                                   seasonal=False,
                                   stepwise=True,
                                   suppress_warnings=True,
                                   error_action='ignore')
    
    print(f"Best Baseline ARIMA Order: {baseline_model.order}")
    
    baseline_preds = baseline_model.predict(n_periods=len(test))
    baseline_rmse = np.sqrt(mean_squared_error(y_test, baseline_preds))
    print(f"Baseline RMSE: {baseline_rmse:.4f}")

    # 4. SARIMAX Model (With Exogenous Regressors)
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

    # 5. Comparison & Selection
    print("\n--- Model Comparison ---")
    if sarimax_rmse < baseline_rmse:
        print(f"WINNER: SARIMAX (Improvement: {baseline_rmse - sarimax_rmse:.4f})")
        best_model = sarimax_model
        best_name = "SARIMAX"
    else:
        print(f"WINNER: Baseline (SARIMAX failed to beat simple history)")
        best_model = baseline_model
        best_name = "Baseline_ARIMA"

    # 6. Save Best Model
    os.makedirs('models', exist_ok=True) # Create models folder
    model_path = os.path.join('models', 'best_rate_model.pkl')
    joblib.dump(best_model, model_path)
    print(f"Saved Best Model to: {model_path}")
    
    # Save SARIMAX specifically for coefficient analysis (Phase 7)
    sarimax_path = os.path.join('models', 'sarimax_model.pkl')
    joblib.dump(sarimax_model, sarimax_path)
    print(f"Saved SARIMAX Model for Analysis to: {sarimax_path}")

    # 7. Visualization
    plt.figure(figsize=(12, 6))
    plt.plot(train.index, y_train, label='Train')
    plt.plot(test.index, y_test, label='Test (Actual)')
    plt.plot(test.index, baseline_preds, label=f'Baseline (RMSE={baseline_rmse:.3f})', linestyle='--')
    plt.plot(test.index, sarimax_preds, label=f'SARIMAX (RMSE={sarimax_rmse:.3f})', linestyle='-.')
    plt.title(f'Forecast Comparison: {best_name} Won')
    plt.legend()
    
    os.makedirs('notebooks', exist_ok=True)
    plot_path = os.path.join('notebooks', 'forecast_comparison.png')
    plt.savefig(plot_path)
    print(f"Saved Forecast Plot to: {plot_path}")
    print("--------------------------------------------------")

if __name__ == "__main__":
    train_models()
