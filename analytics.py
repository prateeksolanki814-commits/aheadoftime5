"""Analytics Module - Financial and Performance Analytics"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from database import db
from inventory import InventoryManager
from sales import SalesManager
import logging

logger = logging.getLogger(__name__)

class Analytics:
    """Comprehensive analytics and reporting."""
    
    @staticmethod
    def get_kpis(days=30):
        """Get all key performance indicators."""
        try:
            products = InventoryManager.get_all_products()
            
            # Calculate metrics
            total_inventory_value = InventoryManager.calculate_inventory_value()
            total_revenue = SalesManager.calculate_total_revenue(days)
            total_profit = SalesManager.calculate_profit(days)
            profit_margin = SalesManager.calculate_profit_margin(days)
            
            # Count alerts
            low_stock = len(InventoryManager.get_low_stock_items())
            expiring = len(InventoryManager.get_expiring_items())
            
            return {
                'total_inventory_value': round(total_inventory_value, 2),
                'total_revenue': round(total_revenue, 2),
                'total_profit': round(total_profit, 2),
                'profit_margin_percent': round(profit_margin, 2),
                'items_in_low_stock': low_stock,
                'items_near_expiry': expiring,
                'total_products': len(products),
                'total_units': int(products['stock'].sum()) if not products.empty else 0
            }
        except Exception as e:
            logger.error(f"Error calculating KPIs: {e}")
            return {}
    
    @staticmethod
    def get_category_performance():
        """Get performance metrics by category."""
        try:
            query = """
                SELECT i.category, 
                       COUNT(i.product_id) as product_count,
                       SUM(i.stock) as total_stock,
                       SUM(i.stock * i.cost_price) as category_value,
                       SUM(s.total_amount) as revenue,
                       SUM((i.selling_price - i.cost_price) * s.quantity_sold) as profit
                FROM inventory i
                LEFT JOIN sales s ON i.product_id = s.product_id
                GROUP BY i.category
                ORDER BY revenue DESC
            """
            results = db.fetch_all(query)
            
            data = []
            for row in results:
                data.append({
                    'category': row[0],
                    'products': row[1],
                    'stock': row[2],
                    'inventory_value': row[3] or 0,
                    'revenue': row[4] or 0,
                    'profit': row[5] or 0
                })
            return data
        except Exception as e:
            logger.error(f"Error getting category performance: {e}")
            return []
    
    @staticmethod
    def get_top_products(metric='profit', limit=10):
        """Get top products by specified metric."""
        try:
            if metric == 'profit':
                query = f"""
                    SELECT i.product_id, i.product_name,
                           SUM((i.selling_price - i.cost_price) * s.quantity_sold) as value
                    FROM inventory i
                    LEFT JOIN sales s ON i.product_id = s.product_id
                    GROUP BY i.product_id
                    ORDER BY value DESC
                    LIMIT {limit}
                """
            elif metric == 'revenue':
                query = f"""
                    SELECT i.product_id, i.product_name,
                           SUM(s.total_amount) as value
                    FROM inventory i
                    LEFT JOIN sales s ON i.product_id = s.product_id
                    GROUP BY i.product_id
                    ORDER BY value DESC
                    LIMIT {limit}
                """
            elif metric == 'sales_volume':
                query = f"""
                    SELECT i.product_id, i.product_name,
                           SUM(s.quantity_sold) as value
                    FROM inventory i
                    LEFT JOIN sales s ON i.product_id = s.product_id
                    GROUP BY i.product_id
                    ORDER BY value DESC
                    LIMIT {limit}
                """
            else:
                return []
            
            results = db.fetch_all(query)
            data = []
            for i, row in enumerate(results, 1):
                data.append({
                    'rank': i,
                    'product_id': row[0],
                    'product_name': row[1],
                    'value': row[2] or 0
                })
            return data
        except Exception as e:
            logger.error(f"Error getting top products: {e}")
            return []
    
    @staticmethod
    def get_inventory_analysis():
        """Get detailed inventory analysis."""
        try:
            products = InventoryManager.get_all_products()
            if products.empty:
                return {}
            
            total_units = products['stock'].sum()
            total_value = (products['stock'] * products['cost_price']).sum()
            
            # Stock distribution
            healthy = len(products[products['stock'] > products['reorder_level']])
            warning = len(products[(products['stock'] <= products['reorder_level']) & (products['stock'] > 0)])
            critical = len(products[products['stock'] == 0])
            
            return {
                'total_units': int(total_units),
                'total_value': round(total_value, 2),
                'healthy_stock': healthy,
                'warning_stock': warning,
                'critical_stock': critical,
                'average_stock_value': round(total_value / len(products), 2) if len(products) > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error analyzing inventory: {e}")
            return {}
    
    @staticmethod
    def get_sales_trend(days=30):
        """Get sales trend data."""
        try:
            query = f"""
                SELECT DATE(sale_date) as date, 
                       SUM(total_amount) as revenue,
                       COUNT(*) as transactions,
                       SUM(quantity_sold) as units_sold
                FROM sales
                WHERE sale_date >= datetime('now', '-{days} days')
                GROUP BY DATE(sale_date)
                ORDER BY date
            """
            results = db.fetch_all(query)
            
            data = []
            for row in results:
                data.append({
                    'date': row[0],
                    'revenue': row[1] or 0,
                    'transactions': row[2] or 0,
                    'units_sold': row[3] or 0
                })
            return data
        except Exception as e:
            logger.error(f"Error getting sales trend: {e}")
            return []
    
    @staticmethod
    def get_alerts():
        """Get active system alerts."""
        try:
            # Low stock alerts
            low_stock = InventoryManager.get_low_stock_items()
            alerts = []
            
            for product in low_stock:
                alerts.append({
                    'type': 'Low Stock',
                    'product_id': product[0],
                    'product_name': product[1],
                    'severity': 'warning',
                    'message': f"⚠ {product[1]} stock ({product[5]} units) below reorder level ({product[6]} units)"
                })
            
            # Expiry alerts
            expiring = InventoryManager.get_expiring_items()
            for product in expiring:
                days_left = product[9]  # days_to_expiry
                severity = 'critical' if days_left <= 5 else 'warning' if days_left <= 10 else 'info'
                alerts.append({
                    'type': 'Near Expiry',
                    'product_id': product[0],
                    'product_name': product[1],
                    'severity': severity,
                    'message': f"⚠ {product[1]} expires in {int(days_left)} days"
                })
            
            # Expired products
            expired = InventoryManager.get_expired_items()
            for product in expired:
                alerts.append({
                    'type': 'Expired',
                    'product_id': product[0],
                    'product_name': product[1],
                    'severity': 'critical',
                    'message': f"🚨 {product[1]} EXPIRED on {product[7]}"
                })
            
            return sorted(alerts, key=lambda x: {'critical': 0, 'warning': 1, 'info': 2}.get(x['severity'], 3))
        except Exception as e:
            logger.error(f"Error getting alerts: {e}")
            return []
