"""Sales Management Module - Transaction and Revenue Tracking"""

import pandas as pd
from datetime import datetime, timedelta
from database import db
from inventory import InventoryManager
import logging

logger = logging.getLogger(__name__)

class SalesManager:
    """Manages sales transactions and revenue tracking."""
    
    @staticmethod
    def record_sale(product_id, quantity, discount_percent=0):
        """Record a sales transaction."""
        try:
            product = InventoryManager.get_product_by_id(product_id)
            if not product:
                logger.error(f"Product {product_id} not found")
                return False
            
            selling_price = product[4]  # selling_price at index 4
            cost_price = product[3]  # cost_price at index 3
            current_stock = product[5]  # stock at index 5
            
            if current_stock < quantity:
                logger.error(f"Insufficient stock for product {product_id}")
                return False
            
            # Calculate amounts
            base_amount = selling_price * quantity
            discount_amount = (base_amount * discount_percent) / 100
            total_amount = base_amount - discount_amount
            
            # Record sale
            sale_query = """
                INSERT INTO sales (product_id, quantity_sold, sale_price, discount_applied, total_amount)
                VALUES (?, ?, ?, ?, ?)
            """
            db.execute_query(sale_query, (product_id, quantity, selling_price, discount_amount, total_amount))
            
            # Update inventory
            InventoryManager.update_stock(product_id, quantity, 'sell')
            
            # Record financial transaction
            profit = (selling_price - cost_price) * quantity
            fin_query = """
                INSERT INTO financials (transaction_type, amount, product_id, description)
                VALUES (?, ?, ?, ?)
            """
            db.execute_query(fin_query, ('sale', total_amount, product_id, f'Sale of {quantity} units'))
            
            logger.info(f"Sale recorded: Product {product_id}, Qty {quantity}, Amount {total_amount}")
            return True
        except Exception as e:
            logger.error(f"Error recording sale: {e}")
            return False
    
    @staticmethod
    def get_sales_data(days=30):
        """Get sales data for specified days."""
        try:
            return db.get_sales_df(days)
        except Exception as e:
            logger.error(f"Error fetching sales data: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def calculate_total_revenue(days=None):
        """Calculate total revenue."""
        try:
            if days:
                query = f"""
                    SELECT SUM(total_amount) as revenue 
                    FROM sales 
                    WHERE sale_date >= datetime('now', '-{days} days')
                """
            else:
                query = "SELECT SUM(total_amount) as revenue FROM sales"
            
            result = db.fetch_one(query)
            return result[0] if result[0] else 0
        except Exception as e:
            logger.error(f"Error calculating revenue: {e}")
            return 0
    
    @staticmethod
    def calculate_total_cost(days=None):
        """Calculate total cost of sold items."""
        try:
            if days:
                query = f"""
                    SELECT SUM(s.quantity_sold * i.cost_price) as cost 
                    FROM sales s
                    JOIN inventory i ON s.product_id = i.product_id
                    WHERE s.sale_date >= datetime('now', '-{days} days')
                """
            else:
                query = """
                    SELECT SUM(s.quantity_sold * i.cost_price) as cost 
                    FROM sales s
                    JOIN inventory i ON s.product_id = i.product_id
                """
            
            result = db.fetch_one(query)
            return result[0] if result[0] else 0
        except Exception as e:
            logger.error(f"Error calculating cost: {e}")
            return 0
    
    @staticmethod
    def calculate_profit(days=None):
        """Calculate total profit."""
        revenue = SalesManager.calculate_total_revenue(days)
        cost = SalesManager.calculate_total_cost(days)
        return revenue - cost
    
    @staticmethod
    def calculate_profit_margin(days=None):
        """Calculate profit margin percentage."""
        revenue = SalesManager.calculate_total_revenue(days)
        if revenue == 0:
            return 0
        profit = SalesManager.calculate_profit(days)
        return (profit / revenue) * 100
    
    @staticmethod
    def get_daily_sales():
        """Get daily sales aggregated data."""
        try:
            query = """
                SELECT DATE(sale_date) as date, SUM(total_amount) as daily_revenue, COUNT(*) as transactions
                FROM sales
                GROUP BY DATE(sale_date)
                ORDER BY date DESC
                LIMIT 30
            """
            results = db.fetch_all(query)
            return results
        except Exception as e:
            logger.error(f"Error fetching daily sales: {e}")
            return []
    
    @staticmethod
    def get_product_sales_contribution():
        """Get profit contribution by product."""
        try:
            query = """
                SELECT i.product_id, i.product_name, 
                       SUM(s.total_amount) as revenue,
                       SUM((i.selling_price - i.cost_price) * s.quantity_sold) as profit
                FROM sales s
                JOIN inventory i ON s.product_id = i.product_id
                GROUP BY i.product_id
                ORDER BY profit DESC
            """
            results = db.fetch_all(query)
            return results
        except Exception as e:
            logger.error(f"Error fetching product sales: {e}")
            return []
