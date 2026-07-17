"""Database Module - SQLite Database Management for Retail System"""

import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = Path("data/retail_system.db")

class DatabaseManager:
    """Manages all database operations for the retail system."""
    
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
    
    def get_connection(self):
        """Get database connection."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    def init_database(self):
        """Initialize database tables."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Inventory Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS inventory (
                    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_name TEXT NOT NULL UNIQUE,
                    category TEXT NOT NULL,
                    cost_price REAL NOT NULL,
                    selling_price REAL NOT NULL,
                    stock INTEGER NOT NULL DEFAULT 0,
                    reorder_level INTEGER NOT NULL,
                    expiry_date DATE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Sales Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sales (
                    sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    quantity_sold INTEGER NOT NULL,
                    sale_price REAL NOT NULL,
                    discount_applied REAL DEFAULT 0,
                    total_amount REAL NOT NULL,
                    sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(product_id) REFERENCES inventory(product_id)
                )
            ''')
            
            # Purchase/Restock Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS purchases (
                    purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    quantity_purchased INTEGER NOT NULL,
                    cost_per_unit REAL NOT NULL,
                    total_cost REAL NOT NULL,
                    purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(product_id) REFERENCES inventory(product_id)
                )
            ''')
            
            # Alerts Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    alert_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    severity TEXT DEFAULT 'warning',
                    is_resolved INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(product_id) REFERENCES inventory(product_id)
                )
            ''')
            
            # Financial Transactions Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS financials (
                    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    product_id INTEGER,
                    description TEXT,
                    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(product_id) REFERENCES inventory(product_id)
                )
            ''')
            
            # Demand Forecast Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS demand_forecast (
                    forecast_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    forecast_date DATE NOT NULL,
                    forecasted_quantity REAL NOT NULL,
                    confidence_interval REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(product_id) REFERENCES inventory(product_id)
                )
            ''')

            # Business Capital Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS business_capital (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    total_money REAL NOT NULL DEFAULT 0
                )
            ''')

            # Create default record
            cursor.execute('''
                INSERT OR IGNORE INTO business_capital (id, total_money)
                VALUES (1, 0)
            ''')

            conn.commit()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def execute_query(self, query, params=None):
        """Execute a database query."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def fetch_all(self, query, params=None):
        """Fetch all results from a query."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Fetch error: {e}")
            raise
        finally:
            conn.close()
    
    def fetch_one(self, query, params=None):
        """Fetch one result from a query."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchone()
        except Exception as e:
            logger.error(f"Fetch error: {e}")
            raise
        finally:
            conn.close()
    
    def get_inventory_df(self):
        """Get inventory as pandas DataFrame."""
        query = "SELECT * FROM inventory ORDER BY product_id"
        return pd.read_sql(query, sqlite3.connect(str(self.db_path)))
    
    def get_sales_df(self, days=30):
        """Get sales data as pandas DataFrame."""
        query = f"""
            SELECT * FROM sales 
            WHERE sale_date >= datetime('now', '-{days} days')
            ORDER BY sale_date DESC
        """
        return pd.read_sql(query, sqlite3.connect(str(self.db_path)))
    
    def close_all_connections(self):
        """Close all database connections."""
        pass  # SQLite handles this automatically
    def get_business_money(self):
        result = self.fetch_one(
        "SELECT total_money FROM business_capital WHERE id=1"
    )
        return result["total_money"] if result else 0


    def set_business_money(self, amount):
        self.execute_query(
            "UPDATE business_capital SET total_money=? WHERE id=1",
            (amount,)
    )


    def add_business_money(self, amount):
        current = self.get_business_money()
        self.set_business_money(current + amount)


    def deduct_business_money(self, amount):
        current = self.get_business_money()
        self.set_business_money(current - amount)

# Global database instance
db = DatabaseManager()
