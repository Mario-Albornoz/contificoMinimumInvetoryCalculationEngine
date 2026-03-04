import pandas as pd
import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.metrics import mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

class SARIMABenchmark:
    def __init__(self, preprocessor: DataFramePreprocessor):
        self.train_df = preprocessor.train_df
        self.test_df = preprocessor.test_df
        self.results = {}

    def fit_predict_series(self, train_series: pd.Series, test_series: pd.Series):
        """
        Fit SARIMA on a single product+warehouse time series and predict.
        order (p,d,q): AR=1, diff=1, MA=1 — good default
        seasonal_order (P,D,Q,s): s=52 for weekly data (1 year seasonality)
        """
        try:
            model = SARIMAX(
                train_series,
                order=(1, 1, 1),
                seasonal_order=(1, 1, 1, 52),  # 52 weeks seasonality
                enforce_stationarity=False,
                enforce_invertibility=False
            )
            fitted = model.fit(disp=False)
            predictions = fitted.forecast(steps=len(test_series))
            predictions = np.maximum(predictions, 0)  # demand can't be negative
            return predictions
        except Exception as e:
            print(f"SARIMA failed for series: {e}")
            return np.full(len(test_series), train_series.mean())  # fallback: mean

    def run(self):
        """
        Run SARIMA for each (product, warehouse) combination and collect metrics.
        """
        group_keys = ['product_contifico_id', 'warehouse_contifico_id']
        all_actuals = []
        all_predictions = []

        for (product_id, warehouse_id), train_group in self.train_df.groupby(group_keys):
            # Get matching test group
            test_group = self.test_df[
                (self.test_df['product_contifico_id'] == product_id) &
                (self.test_df['warehouse_contifico_id'] == warehouse_id)
            ]

            if test_group.empty or len(train_group) < 20:
                # Skip series with too little data to fit SARIMA
                continue

            # Build time-indexed series
            train_series = (
                train_group.set_index('week')['demand']
                .asfreq('W')
                .fillna(0)
            )
            test_series = (
                test_group.set_index('week')['demand']
                .asfreq('W')
                .fillna(0)
            )

            predictions = self.fit_predict_series(train_series, test_series)

            self.results[(product_id, warehouse_id)] = {
                'actuals': test_series.values,
                'predictions': predictions,
                'mae': mean_absolute_error(test_series.values, predictions),
                'rmse': np.sqrt(mean_squared_error(test_series.values, predictions)),
            }

            all_actuals.extend(test_series.values)
            all_predictions.extend(predictions)

        return self

    def summary(self):
        """Print overall and per-series benchmark metrics."""
        if not self.results:
            print("No results yet. Run .run() first.")
            return

        maes = [v['mae'] for v in self.results.values()]
        rmses = [v['rmse'] for v in self.results.values()]

        print(f"=== SARIMA Benchmark Results ===")
        print(f"Series evaluated:  {len(self.results)}")
        print(f"Mean MAE:          {np.mean(maes):.2f}")
        print(f"Mean RMSE:         {np.mean(rmses):.2f}")
        print(f"Median MAE:        {np.median(maes):.2f}")
        print()

        print("Per series breakdown:")
        for (product_id, warehouse_id), metrics in self.results.items():
            print(f"  {product_id} | {warehouse_id} → MAE: {metrics['mae']:.2f}, RMSE: {metrics['rmse']:.2f}")

    def get_metrics_dataframe(self) -> pd.DataFrame:
        """Return results as a DataFrame for easy comparison with your model."""
        rows = []
        for (product_id, warehouse_id), metrics in self.results.items():
            rows.append({
                'product_contifico_id': product_id,
                'warehouse_contifico_id': warehouse_id,
                'sarima_mae': metrics['mae'],
                'sarima_rmse': metrics['rmse'],
            })
        return pd.DataFrame(rows)
