"""Click & Collect Module.

Lets a customer browse the catalog, build a cart, pick a pickup time
slot, and place an order online -- to be collected in-store later.

Payment/stock is settled at order time (like a normal prepaid online
order): placing the order immediately records the sale (reduces stock,
adds revenue), exactly like a regular Sales/Billing transaction. Staff
then track the order through its pickup stages:

    Placed -> Preparing -> Ready for Pickup -> Picked Up

(Cancelled is also available at the "Placed" stage.)
"""

import logging
from database import db
from sales import SalesManager

logger = logging.getLogger(__name__)

PICKUP_SLOTS = [
    "9:00 AM - 11:00 AM",
    "11:00 AM - 1:00 PM",
    "1:00 PM - 3:00 PM",
    "3:00 PM - 5:00 PM",
    "5:00 PM - 7:00 PM",
    "7:00 PM - 9:00 PM",
]

STATUS_FLOW = ["Placed", "Preparing", "Ready for Pickup", "Picked Up"]


class ClickAndCollectManager:
    """Manages Click & Collect orders."""

    @staticmethod
    def ensure_tables():
        try:
            db.execute_query('''
                CREATE TABLE IF NOT EXISTS cnc_orders (
                    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_name TEXT NOT NULL,
                    phone TEXT,
                    pickup_slot TEXT,
                    status TEXT DEFAULT 'Placed',
                    total_amount REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            db.execute_query('''
                CREATE TABLE IF NOT EXISTS cnc_order_items (
                    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    product_name TEXT,
                    quantity INTEGER,
                    unit_price REAL,
                    line_total REAL
                )
            ''')
        except Exception as e:
            logger.error(f"Error creating Click & Collect tables: {e}")

    # -----------------------------------------------------------------
    # Placing an order
    # -----------------------------------------------------------------
    @staticmethod
    def place_order(customer_name, phone, pickup_slot, cart):
        """cart: list of dicts with product_id, product_name, quantity, unit_price.

        Returns (success: bool, message: str, order_id: int or None)
        """
        if not cart:
            return False, "Cart is empty.", None
        if not customer_name or not pickup_slot:
            return False, "Customer name and pickup slot are required.", None

        total_amount = sum(item['quantity'] * item['unit_price'] for item in cart)

        # Settle the sale immediately (prepaid online order): reduces
        # stock and adds revenue, reusing your existing tested logic.
        for item in cart:
            success = SalesManager.record_sale(item['product_id'], item['quantity'], discount_percent=0)
            if not success:
                return False, f"Failed to reserve {item['product_name']} (insufficient stock?).", None

        try:
            db.execute_query(
                """INSERT INTO cnc_orders (customer_name, phone, pickup_slot, total_amount)
                   VALUES (?, ?, ?, ?)""",
                (customer_name, phone, pickup_slot, total_amount)
            )
            order_row = db.fetch_one("SELECT last_insert_rowid() as id")
            order_id = order_row["id"]

            for item in cart:
                line_total = item['quantity'] * item['unit_price']
                db.execute_query(
                    """INSERT INTO cnc_order_items (order_id, product_id, product_name, quantity, unit_price, line_total)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (order_id, item['product_id'], item['product_name'], item['quantity'], item['unit_price'], line_total)
                )

            return True, f"Order placed! Pickup slot: {pickup_slot}", order_id
        except Exception as e:
            logger.error(f"Error placing Click & Collect order: {e}")
            return False, f"Error: {e}", None

    # -----------------------------------------------------------------
    # Order tracking
    # -----------------------------------------------------------------
    @staticmethod
    def get_order(order_id):
        """Returns (order_dict, items_list) or (None, [])."""
        try:
            order = db.fetch_one("SELECT * FROM cnc_orders WHERE order_id = ?", (order_id,))
            if not order:
                return None, []
            items = db.fetch_all("SELECT * FROM cnc_order_items WHERE order_id = ?", (order_id,))
            return dict(order), [dict(i) for i in items]
        except Exception as e:
            logger.error(f"Error fetching order: {e}")
            return None, []

    @staticmethod
    def get_orders(status=None, limit=100):
        try:
            if status:
                return db.fetch_all(
                    "SELECT * FROM cnc_orders WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                    (status, limit)
                )
            return db.fetch_all("SELECT * FROM cnc_orders ORDER BY created_at DESC LIMIT ?", (limit,))
        except Exception as e:
            logger.error(f"Error fetching orders: {e}")
            return []

    @staticmethod
    def advance_status(order_id):
        """Moves an order to the next stage in STATUS_FLOW. No-op if
        already at the final stage or cancelled."""
        try:
            order = db.fetch_one("SELECT status FROM cnc_orders WHERE order_id = ?", (order_id,))
            if not order:
                return False, "Order not found."

            current = order["status"]
            if current not in STATUS_FLOW:
                return False, f"Order is {current}, cannot advance."

            idx = STATUS_FLOW.index(current)
            if idx >= len(STATUS_FLOW) - 1:
                return False, "Order is already at the final stage."

            new_status = STATUS_FLOW[idx + 1]
            db.execute_query("UPDATE cnc_orders SET status = ? WHERE order_id = ?", (new_status, order_id))
            return True, f"Order moved to '{new_status}'."
        except Exception as e:
            logger.error(f"Error advancing order status: {e}")
            return False, f"Error: {e}"

    @staticmethod
    def cancel_order(order_id):
        try:
            db.execute_query("UPDATE cnc_orders SET status = 'Cancelled' WHERE order_id = ?", (order_id,))
            return True, "Order cancelled."
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return False, f"Error: {e}"
