"""Seasonal Analytics Module.

Compares sales performance across:
- Season: Summer (Mar-Jun), Winter (Nov-Feb), Monsoon (Jul-Oct)
- Festival: user-defined festival date ranges (e.g. Diwali, Holi) --
  since festival dates change every year and vary by region, you
  define these yourself rather than relying on hardcoded dates.
- Day type: Weekend (Sat/Sun) vs Weekday

A sale that falls within a defined festival period is counted as
"Festival" (taking priority over its season), so the 4 season-related
categories are mutually exclusive: Summer / Winter / Monsoon / Festival.
Weekend vs Weekday is a separate, independent comparison.
"""

import logging
import pandas as pd
from database import db

logger = logging.getLogger(__name__)


def get_season(month: int) -> str:
    """Returns Summer / Winter / Monsoon for a given calendar month (1-12)."""
    if month in (3, 4, 5, 6):
        return "Summer"
    elif month in (11, 12, 1, 2):
        return "Winter"
    else:
        return "Monsoon"


class SeasonalAnalytics:
    """Manages festival periods and seasonal sales comparisons."""

    @staticmethod
    def ensure_tables():
        try:
            db.execute_query('''
                CREATE TABLE IF NOT EXISTS festival_periods (
                    festival_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        except Exception as e:
            logger.error(f"Error creating festival_periods table: {e}")

    @staticmethod
    def add_festival_period(name, start_date, end_date):
        try:
            db.execute_query(
                "INSERT INTO festival_periods (name, start_date, end_date) VALUES (?, ?, ?)",
                (name, start_date, end_date)
            )
            return True, "Festival period added."
        except Exception as e:
            logger.error(f"Error adding festival period: {e}")
            return False, f"Error: {e}"

    @staticmethod
    def get_festival_periods():
        try:
            return db.fetch_all("SELECT * FROM festival_periods ORDER BY start_date")
        except Exception as e:
            logger.error(f"Error fetching festival periods: {e}")
            return []

    @staticmethod
    def delete_festival_period(festival_id):
        try:
            db.execute_query("DELETE FROM festival_periods WHERE festival_id = ?", (festival_id,))
            return True, "Festival period removed."
        except Exception as e:
            logger.error(f"Error deleting festival period: {e}")
            return False, f"Error: {e}"

    @staticmethod
    def _is_festival(sale_date, festival_periods):
        d = sale_date.date()
        for f in festival_periods:
            try:
                start = pd.to_datetime(f["start_date"]).date()
                end = pd.to_datetime(f["end_date"]).date()
                if start <= d <= end:
                    return True, f["name"]
            except Exception:
                continue
        return False, None

    @staticmethod
    def classify_sales(sales_df):
        """Takes a sales DataFrame (must have 'sale_date' and
        'total_amount' and 'quantity_sold' columns) and adds:
        day_type (Weekend/Weekday), season (Summer/Winter/Monsoon),
        is_festival, festival_name, category (Festival takes priority
        over season).

        Returns the enriched DataFrame.
        """
        if sales_df.empty:
            return sales_df

        df = sales_df.copy()
        df['sale_date'] = pd.to_datetime(df['sale_date'])

        df['weekday_num'] = df['sale_date'].dt.weekday
        df['day_type'] = df['weekday_num'].apply(lambda x: 'Weekend' if x >= 5 else 'Weekday')
        df['season'] = df['sale_date'].dt.month.apply(get_season)

        festival_periods = SeasonalAnalytics.get_festival_periods()
        festival_results = df['sale_date'].apply(lambda d: SeasonalAnalytics._is_festival(d, festival_periods))
        df['is_festival'] = festival_results.apply(lambda x: x[0])
        df['festival_name'] = festival_results.apply(lambda x: x[1])

        df['category'] = df.apply(lambda r: 'Festival' if r['is_festival'] else r['season'], axis=1)
        return df

    @staticmethod
    def get_season_comparison(sales_df):
        """Returns a DataFrame summarizing revenue, units sold, and
        transaction count per category (Summer/Winter/Monsoon/Festival)."""
        df = SeasonalAnalytics.classify_sales(sales_df)
        if df.empty:
            return pd.DataFrame(columns=['category', 'revenue', 'units_sold', 'transactions', 'avg_sale_value'])

        summary = df.groupby('category').agg(
            revenue=('total_amount', 'sum'),
            units_sold=('quantity_sold', 'sum'),
            transactions=('total_amount', 'count'),
        ).reset_index()
        summary['avg_sale_value'] = (summary['revenue'] / summary['transactions']).round(2)
        return summary.sort_values('revenue', ascending=False)

    @staticmethod
    def get_weekend_weekday_comparison(sales_df):
        """Returns a DataFrame summarizing revenue, units sold, and
        transaction count for Weekend vs Weekday."""
        df = SeasonalAnalytics.classify_sales(sales_df)
        if df.empty:
            return pd.DataFrame(columns=['day_type', 'revenue', 'units_sold', 'transactions', 'avg_sale_value'])

        summary = df.groupby('day_type').agg(
            revenue=('total_amount', 'sum'),
            units_sold=('quantity_sold', 'sum'),
            transactions=('total_amount', 'count'),
        ).reset_index()
        summary['avg_sale_value'] = (summary['revenue'] / summary['transactions']).round(2)
        return summary
