"""Inventory Management Module - Product and Stock Management"""

import pandas as pd
from datetime import datetime, timedelta
from database import db
import logging

logger = logging.getLogger(__name__)

class InventoryManager:
    """Manages inventory operations: add, update, delete, search products."""
    
    @staticmethod
    def add_product(product_name, category, cost_price, selling_price, stock, reorder_level, expiry_date):
        """Add a new product to inventory."""
        try:
            query = """
                INSERT INTO inventory (product_name, category, cost_price, selling_price, stock, reorder_level, expiry_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            db.execute_query(query, (product_name, category, cost_price, selling_price, stock, reorder_level, expiry_date))
            logger.info(f"Product '{product_name}' added successfully")
            return True
        except Exception as e:
            logger.error(f"Error adding product: {e}")
            return False
    
    @staticmethod
    def update_product(product_id, **kwargs):
        """Update product details."""
        try:
            allowed_fields = ['product_name', 'category', 'cost_price', 'selling_price', 'stock', 'reorder_level', 'expiry_date']
            updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            if not updates:
                return False
            
            set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values()) + [product_id]
            query = f"UPDATE inventory SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE product_id = ?"
            db.execute_query(query, values)
            logger.info(f"Product {product_id} updated successfully")
            return True
        except Exception as e:
            logger.error(f"Error updating product: {e}")
            return False
    
    @staticmethod
    def delete_product(product_id):
        """Delete a product from inventory."""
        try:
            query = "DELETE FROM inventory WHERE product_id = ?"
            db.execute_query(query, (product_id,))
            logger.info(f"Product {product_id} deleted successfully")
            return True
        except Exception as e:
            logger.error(f"Error deleting product: {e}")
            return False
    
    @staticmethod
    def search_products(search_term=None, category=None, product_id=None):
        """Search products by name, category, or ID."""
        try:
            query = "SELECT * FROM inventory WHERE 1=1"
            params = []
            
            if product_id:
                query += " AND product_id = ?"
                params.append(product_id)
            if search_term:
                query += " AND product_name LIKE ?"
                params.append(f"%{search_term}%")
            if category:
                query += " AND category = ?"
                params.append(category)
            
            query += " ORDER BY product_name"
            results = db.fetch_all(query, params)
            return results
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            return []
    
    @staticmethod
    def get_all_products():
        """Get all products as DataFrame."""
        return db.get_inventory_df()
    
    @staticmethod
    def get_product_by_id(product_id):
        """Get product details by ID."""
        query = "SELECT * FROM inventory WHERE product_id = ?"
        return db.fetch_one(query, (product_id,))
    
    @staticmethod
    def get_categories():
        """Get all unique product categories."""
        query = "SELECT DISTINCT category FROM inventory ORDER BY category"
        results = db.fetch_all(query)
        return [row[0] for row in results]
    
    @staticmethod
    def get_low_stock_items():
        """Get products with stock at or below reorder level."""
        query = "SELECT * FROM inventory WHERE stock <= reorder_level ORDER BY stock"
        return db.fetch_all(query)
    
    @staticmethod
    def get_expiring_items():
        """Get products expiring within 15 days."""
        query = """
            SELECT *, 
                   julianday(expiry_date) - julianday('now') as days_to_expiry
            FROM inventory 
            WHERE julianday(expiry_date) - julianday('now') <= 15 
            AND julianday(expiry_date) - julianday('now') > 0
            ORDER BY days_to_expiry
        """
        return db.fetch_all(query)
    
    @staticmethod
    def get_expired_items():
        """Get expired products."""
        query = "SELECT * FROM inventory WHERE expiry_date < DATE('now') ORDER BY expiry_date"
        return db.fetch_all(query)
    
    @staticmethod
    def update_stock(product_id, quantity, operation='sell'):
        """Update stock quantity."""
        try:
            product = InventoryManager.get_product_by_id(product_id)
            if not product:
                logger.error(f"Product {product_id} not found")
                return False
            
            current_stock = product[5]  # stock is at index 5
            if operation == 'sell':
                new_stock = current_stock - quantity
            elif operation == 'restock':
                new_stock = current_stock + quantity
            else:
                return False
            
            if new_stock < 0 and operation == 'sell':
                logger.error(f"Insufficient stock for product {product_id}")
                return False
            
            query = "UPDATE inventory SET stock = ?, updated_at = CURRENT_TIMESTAMP WHERE product_id = ?"
            db.execute_query(query, (new_stock, product_id))
            logger.info(f"Stock updated for product {product_id}: {current_stock} -> {new_stock}")
            return True
        except Exception as e:
            logger.error(f"Error updating stock: {e}")
            return False
    
    @staticmethod
    def calculate_inventory_value():
        """Calculate total inventory value at cost."""
        try:
            query = "SELECT SUM(stock * cost_price) as total_value FROM inventory"
            result = db.fetch_one(query)
            return result[0] if result[0] else 0
        except Exception as e:
            logger.error(f"Error calculating inventory value: {e}")
            return 0
