"""Discount Optimization Engine - AI-Powered Discount Recommendations"""

import pandas as pd
from datetime import datetime, timedelta
from database import db
from inventory import InventoryManager
from sales import SalesManager
import logging

logger = logging.getLogger(__name__)

class DiscountEngine:
    """AI-driven discount recommendation system based on expiry and stock levels."""
    
    @staticmethod
    def get_discount_recommendation(product_id):
        """Get discount recommendation for a product based on expiry and stock."""
        try:
            product = InventoryManager.get_product_by_id(product_id)
            if not product:
                return None
            
            expiry_date = product[7]  # expiry_date at index 7
            stock = product[5]  # stock at index 5
            reorder_level = product[6]  # reorder_level at index 6
            selling_price = product[4]  # selling_price at index 4
            
            # Calculate days to expiry
            exp_date = datetime.strptime(expiry_date, '%Y-%m-%d')
            days_to_expiry = (exp_date - datetime.now()).days
            
            discount = 0
            recommendation = "No discount needed"
            urgency = "Normal"
            
            # Discount based on expiry
            if days_to_expiry <= 0:
                discount = 50
                recommendation = "CRITICAL: Product expired. Heavy discount advised."
                urgency = "CRITICAL"
            elif days_to_expiry <= 5:
                discount = 25
                recommendation = "Product expires within 5 days. Recommend 25% discount."
                urgency = "HIGH"
            elif days_to_expiry <= 10:
                discount = 15
                recommendation = "Product expires in 5-10 days. Recommend 15% discount."
                urgency = "MEDIUM"
            elif days_to_expiry <= 15:
                discount = 10
                recommendation = "Product expires in 10-15 days. Recommend 10% discount."
                urgency = "LOW"
            
            # Adjust discount based on stock level
            if stock > reorder_level * 2:
                discount = min(discount + 10, 50)
                recommendation += " High stock levels - increase discount."
            
            expected_sales_increase = DiscountEngine.estimate_sales_increase(discount)
            estimated_profit = DiscountEngine.estimate_profit_recovery(product_id, discount, expected_sales_increase)
            
            return {
                'product_id': product_id,
                'discount': discount,
                'days_to_expiry': days_to_expiry,
                'stock': stock,
                'recommendation': recommendation,
                'urgency': urgency,
                'expected_sales_increase': expected_sales_increase,
                'estimated_profit_recovery': estimated_profit,
                'selling_price': selling_price,
                'discounted_price': selling_price * (1 - discount/100)
            }
        except Exception as e:
            logger.error(f"Error getting discount recommendation: {e}")
            return None
    
    @staticmethod
    def estimate_sales_increase(discount_percent):
        """Estimate sales increase based on discount percentage."""
        # Simple demand elasticity model
        # Every 10% discount increases sales by ~20%
        return min((discount_percent / 10) * 20, 100)
    
    @staticmethod
    def estimate_profit_recovery(product_id, discount_percent, expected_sales_increase):
        """Estimate profit recovery with discount."""
        try:
            product = InventoryManager.get_product_by_id(product_id)
            if not product:
                return 0
            
            selling_price = product[4]
            cost_price = product[3]
            stock = product[5]
            
            margin_per_unit = selling_price - cost_price
            
            # Without discount - assume average historical conversion
            units_sold_normal = min(stock * 0.1, stock)  # 10% typical sell-through
            profit_without_discount = units_sold_normal * margin_per_unit
            
            # With discount
            units_with_discount = units_sold_normal * (1 + (expected_sales_increase / 100))
            units_with_discount = min(units_with_discount, stock)
            discounted_margin = margin_per_unit * (1 - discount_percent / 100)
            profit_with_discount = units_with_discount * discounted_margin
            
            return max(profit_with_discount - profit_without_discount, 0)
        except Exception as e:
            logger.error(f"Error estimating profit recovery: {e}")
            return 0
    
    @staticmethod
    def get_all_recommendations():
        """Get discount recommendations for all products."""
        try:
            products = InventoryManager.get_all_products()
            recommendations = []
            
            for _, row in products.iterrows():
                rec = DiscountEngine.get_discount_recommendation(row['product_id'])
                if rec and rec['discount'] > 0:
                    recommendations.append(rec)
            
            return sorted(recommendations, key=lambda x: x['urgency'] in ['CRITICAL', 'HIGH'], reverse=True)
        except Exception as e:
            logger.error(f"Error getting all recommendations: {e}")
            return []
    
    @staticmethod
    def apply_discount_recommendation(product_id, discount_percent, reason=""):
        """Record applied discount recommendation."""
        try:
            query = """
                INSERT INTO alerts (product_id, alert_type, message, severity)
                VALUES (?, ?, ?, ?)
            """
            message = f"Discount {discount_percent}% applied. Reason: {reason}"
            db.execute_query(query, (product_id, 'discount_applied', message, 'info'))
            logger.info(f"Discount {discount_percent}% applied to product {product_id}")
            return True
        except Exception as e:
            logger.error(f"Error applying discount: {e}")
            return False
