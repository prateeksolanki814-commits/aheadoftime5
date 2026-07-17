"""Discount Log Module.

Tracks every discount applied through the app (both AI recommendations
and manual/custom discounts) so the Executive Dashboard can show a
live feed of recently applied discounts.
"""

import logging
from database import db

logger = logging.getLogger(__name__)


class DiscountLogManager:
    """Manages the discount_log table."""

    @staticmethod
    def ensure_table():
        """Create the discount_log table if it doesn't exist yet."""
        try:
            db.execute_query('''
                CREATE TABLE IF NOT EXISTS discount_log (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    product_name TEXT,
                    discount_percent REAL NOT NULL,
                    original_price REAL,
                    discounted_price REAL,
                    reason TEXT,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        except Exception as e:
            logger.error(f"Error creating discount_log table: {e}")

    @staticmethod
    def log_discount(product_id, product_name, discount_percent, original_price, discounted_price, reason=""):
        """Record that a discount was applied to a product."""
        try:
            db.execute_query(
                """INSERT INTO discount_log
                   (product_id, product_name, discount_percent, original_price, discounted_price, reason)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (product_id, product_name, discount_percent, original_price, discounted_price, reason)
            )
            return True
        except Exception as e:
            logger.error(f"Error logging discount: {e}")
            return False

    @staticmethod
    def get_recent_discounts(limit=10):
        """Get the most recently applied discounts."""
        try:
            query = "SELECT * FROM discount_log ORDER BY applied_at DESC LIMIT ?"
            return db.fetch_all(query, (limit,))
        except Exception as e:
            logger.error(f"Error fetching discount log: {e}")
            return []

    @staticmethod
    def count_recent_discounts(days=30):
        """Count how many discounts were applied in the last N days."""
        try:
            query = f"""
                SELECT COUNT(*) as cnt FROM discount_log
                WHERE applied_at >= datetime('now', '-{days} days')
            """
            result = db.fetch_one(query)
            return result["cnt"] if result else 0
        except Exception as e:
            logger.error(f"Error counting discounts: {e}")
            return 0
