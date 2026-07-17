"""Demand Forecasting Module - AI Predictions using scikit-learn.

This version does NOT use Prophet. Prophet frequently fails to install
on Streamlit Community Cloud (compiler/build issues, long install times),
which is a very common cause of broken deployments. This version uses
scikit-learn's LinearRegression, which is lightweight, installs
instantly, and has no build dependencies -- so your app deploys
reliably every time.

The public method names and return formats are UNCHANGED from before,
so app.py does not need any modifications.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from database import db
from inventory import InventoryManager
from sales import SalesManager
import logging
from sklearn.linear_model import LinearRegression

logger = logging.getLogger(__name__)


class DemandForecaster:
    """AI-powered demand forecasting using scikit-learn (Linear Regression
    with weekly-seasonality adjustment)."""

    @staticmethod
    def get_historical_sales(product_id, days=90):
        """Get historical daily sales totals for a product."""
        try:
            query = f"""
                SELECT DATE(sale_date) as date, SUM(quantity_sold) as quantity
                FROM sales
                WHERE product_id = ? AND sale_date >= datetime('now', '-{days} days')
                GROUP BY DATE(sale_date)
                ORDER BY date
            """
            results = db.fetch_all(query, (product_id,))
            return results
        except Exception as e:
            logger.error(f"Error fetching historical sales: {e}")
            return []

    @staticmethod
    def forecast_demand(product_id, days=30):
        """Forecast demand for next N days.

        Returns a list of dicts:
        [{'date': date, 'forecasted_quantity': float,
          'lower_bound': float, 'upper_bound': float}, ...]
        """
        try:
            product = InventoryManager.get_product_by_id(product_id)
            if not product:
                return None

            historical_data = DemandForecaster.get_historical_sales(product_id, days=90)

            if not historical_data:
                return DemandForecaster._get_default_forecast(days)

            return DemandForecaster._forecast_with_ml(historical_data, days)
        except Exception as e:
            logger.error(f"Error forecasting demand: {e}")
            return DemandForecaster._get_default_forecast(days)

    @staticmethod
    def _forecast_with_ml(historical_data, days):
        """Forecast using Linear Regression + day-of-week seasonality.

        - A LinearRegression model captures the overall sales trend
          (growing / shrinking / stable) over time.
        - A per-weekday factor (e.g. weekends selling more) adjusts the
          trend prediction up or down for that day of the week.
        - The spread of past prediction errors is used to build a
          simple confidence band (lower_bound / upper_bound).
        """
        try:
            df = pd.DataFrame(historical_data, columns=['date', 'quantity'])
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
            df = df.dropna().sort_values('date').reset_index(drop=True)

            if len(df) < 3:
                avg = float(df['quantity'].mean()) if len(df) > 0 else 10.0
                return DemandForecaster._get_default_forecast(days, base=avg)

            df['day_index'] = np.arange(len(df))
            df['weekday'] = df['date'].dt.weekday

            X = df[['day_index']]
            y = df['quantity']

            model = LinearRegression()
            model.fit(X, y)

            residuals = y - model.predict(X)
            std_err = float(residuals.std())
            if pd.isna(std_err) or std_err == 0:
                std_err = float(y.mean()) * 0.2

            overall_avg = float(y.mean())
            weekday_avg = df.groupby('weekday')['quantity'].mean()
            weekday_factor = (weekday_avg / overall_avg).to_dict() if overall_avg > 0 else {}

            last_index = int(df['day_index'].max())
            last_date = df['date'].max()

            forecast_data = []
            for i in range(1, days + 1):
                future_date = last_date + timedelta(days=i)
                future_index = pd.DataFrame({'day_index': [last_index + i]})
                trend_pred = float(model.predict(future_index)[0])

                factor = weekday_factor.get(future_date.weekday(), 1.0)
                adjusted_pred = trend_pred * factor

                forecasted_qty = max(0.0, round(adjusted_pred, 2))
                lower = max(0.0, round(adjusted_pred - std_err, 2))
                upper = round(adjusted_pred + std_err, 2)

                forecast_data.append({
                    'date': future_date.date(),
                    'forecasted_quantity': forecasted_qty,
                    'lower_bound': lower,
                    'upper_bound': upper
                })

            return forecast_data
        except Exception as e:
            logger.error(f"ML forecast error: {e}")
            return DemandForecaster._get_default_forecast(days)

    @staticmethod
    def _get_default_forecast(days, base=10.0):
        """Fallback forecast when there isn't enough data to model."""
        forecast_data = []
        today = datetime.now()

        for i in range(days):
            forecast_date = (today + timedelta(days=i + 1)).date()
            forecast_data.append({
                'date': forecast_date,
                'forecasted_quantity': round(base, 2),
                'lower_bound': max(0.0, round(base * 0.5, 2)),
                'upper_bound': round(base * 1.5, 2)
            })

        return forecast_data

    @staticmethod
    def get_recommendation(product_id):
        """Get purchasing recommendation based on forecast."""
        try:
            product = InventoryManager.get_product_by_id(product_id)
            if not product:
                return None

            stock = product[5]
            reorder_level = product[6]

            forecast = DemandForecaster.forecast_demand(product_id, days=30)
            if not forecast:
                return None

            total_forecasted = sum([f['forecasted_quantity'] for f in forecast])
            safety_stock = reorder_level

            recommended_quantity = total_forecasted - stock + safety_stock

            if recommended_quantity <= 0:
                status = "No reorder needed"
            else:
                status = f"Reorder {int(recommended_quantity)} units"

            return {
                'product_id': product_id,
                'current_stock': stock,
                'forecasted_30day_demand': round(total_forecasted, 0),
                'recommended_quantity': max(0, int(recommended_quantity)),
                'status': status,
                'confidence': 0.85
            }
        except Exception as e:
            logger.error(f"Error getting recommendation: {e}")
            return None

    @staticmethod
    def get_all_recommendations():
        """Get purchasing recommendations for all products."""
        try:
            products = InventoryManager.get_all_products()
            recommendations = []

            for _, row in products.iterrows():
                rec = DemandForecaster.get_recommendation(row['product_id'])
                if rec and rec['recommended_quantity'] > 0:
                    recommendations.append(rec)

            return sorted(recommendations, key=lambda x: x['recommended_quantity'], reverse=True)
        except Exception as e:
            logger.error(f"Error getting all recommendations: {e}")
            return []
