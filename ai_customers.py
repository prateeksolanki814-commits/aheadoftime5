"""AI Customer Order Simulator.

Simulates customers messaging the store wanting to buy products.
Staff can review each message and either Fulfill it (which records a
real sale and reduces stock, exactly like the Sales page) or Reject it.

Note: this is a DEMO simulator -- it generates realistic-looking
customer messages using randomized templates, it does not connect to
any real customers or messaging platform. This keeps it fully
self-contained with zero external dependencies, so it always works
on Streamlit Cloud.
"""

import random
import logging
from datetime import datetime, timezone
from database import db
from inventory import InventoryManager
from sales import SalesManager

logger = logging.getLogger(__name__)

CUSTOMER_NAMES = [
    "Amit Sharma", "Priya Verma", "Rahul Mehta", "Sneha Iyer",
    "Vikram Singh", "Anjali Gupta", "Rohan Kapoor", "Neha Reddy",
    "Karan Malhotra", "Pooja Nair", "Arjun Rao", "Divya Menon",
    "Suresh Patil", "Kavita Joshi", "Manish Yadav"
]

MESSAGE_TEMPLATES = [
    "Hi! Do you have {qty} {product} in stock? I'd like to order.",
    "Hello, can I get {qty} {product}? Need it today if possible 🙏",
    "Is {product} available? I want to buy {qty}.",
    "Can you keep {qty} {product} ready for me? I'll pick it up.",
    "Looking for {product}, need about {qty} units. Available?",
    "Hey, please reserve {qty} packs of {product} for me!",
    "Do you deliver? I need {qty} {product} at home.",
    "Quick question — is {product} in stock? Want {qty} of it.",
]


class AICustomerManager:
    """Manages simulated AI customer order requests."""

    @staticmethod
    def ensure_table():
        """Create the customer_orders table if it doesn't exist yet."""
        try:
            db.execute_query('''
                CREATE TABLE IF NOT EXISTS customer_orders (
                    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_name TEXT NOT NULL,
                    product_id INTEGER,
                    product_name TEXT,
                    quantity INTEGER,
                    message TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP
                )
            ''')
        except Exception as e:
            logger.error(f"Error creating customer_orders table: {e}")

    @staticmethod
    def get_last_order_time():
        """Returns the timestamp of the most recent customer order, or
        None if there are no orders yet."""
        try:
            result = db.fetch_one("SELECT MAX(created_at) as last_time FROM customer_orders")
            return result["last_time"] if result and result["last_time"] else None
        except Exception as e:
            logger.error(f"Error fetching last order time: {e}")
            return None

    @staticmethod
    def maybe_auto_generate(min_interval_seconds=30):
        """Automatically generates a new simulated customer message if
        enough time has passed since the last one -- so messages keep
        arriving on their own without anyone needing to click a button.

        Call this once near the top of the AI Customers page on every
        run; combined with the page's auto-refresh, new messages will
        keep appearing by themselves roughly every `min_interval_seconds`.

        Returns True if a new message was generated, False otherwise.
        """
        try:
            last_time_str = AICustomerManager.get_last_order_time()

            should_generate = False
            if not last_time_str:
                should_generate = True
            else:
                last_time = datetime.strptime(last_time_str, '%Y-%m-%d %H:%M:%S')
                now = datetime.now(timezone.utc).replace(tzinfo=None)
                elapsed = (now - last_time).total_seconds()
                if elapsed >= min_interval_seconds:
                    should_generate = True

            if should_generate:
                success, _ = AICustomerManager.generate_new_order()
                return success
            return False
        except Exception as e:
            logger.error(f"Error in auto-generate: {e}")
            return False

    @staticmethod
    def generate_new_order():
        """Simulate one new customer message wanting to buy a product.

        Picks a random product that currently has stock, a random
        quantity, a random customer name, and a random message
        template. Returns (success: bool, message: str).
        """
        try:
            products = InventoryManager.get_all_products()
            if products.empty:
                return False, "No products in inventory yet."

            in_stock = products[products['stock'] > 0]
            if in_stock.empty:
                return False, "All products are currently out of stock."

            product = in_stock.sample(1).iloc[0]
            product_id = int(product['product_id'])
            product_name = product['product_name']

            max_qty = max(1, min(5, int(product['stock'])))
            quantity = random.randint(1, max_qty)

            customer_name = random.choice(CUSTOMER_NAMES)
            template = random.choice(MESSAGE_TEMPLATES)
            message_text = template.format(qty=quantity, product=product_name)

            db.execute_query(
                """INSERT INTO customer_orders
                   (customer_name, product_id, product_name, quantity, message)
                   VALUES (?, ?, ?, ?, ?)""",
                (customer_name, product_id, product_name, quantity, message_text)
            )
            return True, f"New message from {customer_name}!"
        except Exception as e:
            logger.error(f"Error generating customer order: {e}")
            return False, f"Error: {e}"

    @staticmethod
    def get_orders(status=None):
        """Get customer orders, optionally filtered by status
        ('pending', 'fulfilled', 'rejected'). Returns list of rows
        (most recent first)."""
        try:
            if status:
                query = "SELECT * FROM customer_orders WHERE status = ? ORDER BY created_at DESC"
                return db.fetch_all(query, (status,))
            else:
                query = "SELECT * FROM customer_orders ORDER BY created_at DESC"
                return db.fetch_all(query)
        except Exception as e:
            logger.error(f"Error fetching customer orders: {e}")
            return []

    @staticmethod
    def get_order_stats():
        """Returns a dict with pending / fulfilled / rejected counts
        and total revenue generated from fulfilled AI customer orders."""
        try:
            pending = db.fetch_one("SELECT COUNT(*) as cnt FROM customer_orders WHERE status='pending'")
            fulfilled = db.fetch_one("SELECT COUNT(*) as cnt FROM customer_orders WHERE status='fulfilled'")
            rejected = db.fetch_one("SELECT COUNT(*) as cnt FROM customer_orders WHERE status='rejected'")

            return {
                "pending": pending["cnt"] if pending else 0,
                "fulfilled": fulfilled["cnt"] if fulfilled else 0,
                "rejected": rejected["cnt"] if rejected else 0,
            }
        except Exception as e:
            logger.error(f"Error fetching order stats: {e}")
            return {"pending": 0, "fulfilled": 0, "rejected": 0}

    @staticmethod
    def fulfill_order(order_id):
        """Fulfill a pending order: records a real sale (reduces stock,
        adds revenue) exactly like the Sales page would.

        Returns (success: bool, message: str)
        """
        try:
            order = db.fetch_one("SELECT * FROM customer_orders WHERE order_id = ?", (order_id,))
            if not order:
                return False, "Order not found."

            product_id = order["product_id"]
            quantity = order["quantity"]

            product = InventoryManager.get_product_by_id(product_id)
            if not product:
                return False, "Product no longer exists."

            current_stock = product[5]
            if current_stock < quantity:
                return False, f"Not enough stock (only {current_stock} left)."

            success = SalesManager.record_sale(product_id, quantity, discount_percent=0)
            if success:
                db.execute_query(
                    "UPDATE customer_orders SET status='fulfilled', resolved_at=CURRENT_TIMESTAMP WHERE order_id=?",
                    (order_id,)
                )
                # Add the sale revenue to available business funds
                revenue = float(product[4]) * quantity
                db.add_business_money(revenue)
                return True, f"Order fulfilled! {quantity} units sold to {order['customer_name']}."
            else:
                return False, "Could not record the sale."
        except Exception as e:
            logger.error(f"Error fulfilling order: {e}")
            return False, f"Error: {e}"

    @staticmethod
    def reject_order(order_id):
        """Mark an order as rejected (e.g. out of stock, can't fulfill)."""
        try:
            db.execute_query(
                "UPDATE customer_orders SET status='rejected', resolved_at=CURRENT_TIMESTAMP WHERE order_id=?",
                (order_id,)
            )
            return True, "Order rejected."
        except Exception as e:
            logger.error(f"Error rejecting order: {e}")
            return False, f"Error: {e}"
