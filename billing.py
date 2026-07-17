"""Billing & Checkout Module.

Provides a full point-of-sale style billing flow on top of your
existing Sales system:
- Fast Billing: build a cart of multiple products, then check out in
  one go (reuses SalesManager.record_sale for each item, so stock and
  the sales table stay perfectly consistent with the rest of the app).
- Multiple payment methods: Cash / UPI / Card / Wallet.
- GST invoice calculation (subtotal, GST amount, grand total).
- Thermal receipt formatting (narrow monospace text, ready to print
  on a thermal printer or download as .txt).
- QR code generation (for UPI payment or as a bill reference code) --
  requires the `qrcode` package (added to requirements.txt).
- Refunds & Returns: look up a past bill, return some/all of an item,
  automatically restocks the product and deducts the refund from your
  business funds.
"""

import io
import logging
from database import db
from inventory import InventoryManager
from sales import SalesManager

logger = logging.getLogger(__name__)

try:
    import qrcode
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False
    logger.warning("qrcode package not installed -- QR code generation will be disabled.")


class BillingManager:
    """Manages bills, bill items, and returns."""

    @staticmethod
    def ensure_tables():
        """Create the billing tables if they don't exist yet."""
        try:
            db.execute_query('''
                CREATE TABLE IF NOT EXISTS bills (
                    bill_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_name TEXT,
                    payment_method TEXT,
                    subtotal REAL,
                    gst_percent REAL,
                    gst_amount REAL,
                    total_amount REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            db.execute_query('''
                CREATE TABLE IF NOT EXISTS bill_items (
                    bill_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bill_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    product_name TEXT,
                    quantity INTEGER,
                    unit_price REAL,
                    line_total REAL,
                    returned_quantity INTEGER DEFAULT 0,
                    FOREIGN KEY(bill_id) REFERENCES bills(bill_id)
                )
            ''')
            db.execute_query('''
                CREATE TABLE IF NOT EXISTS returns (
                    return_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bill_item_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER,
                    refund_amount REAL,
                    reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        except Exception as e:
            logger.error(f"Error creating billing tables: {e}")

    # -----------------------------------------------------------------
    # Checkout
    # -----------------------------------------------------------------
    @staticmethod
    def checkout(cart, payment_method, gst_percent=5.0, customer_name=""):
        """Finalize a bill from a cart.

        cart: list of dicts, each with product_id, product_name,
              quantity, unit_price.
        payment_method: "Cash" / "UPI" / "Card" / "Wallet"

        Returns (success: bool, message: str, bill_id: int or None)
        """
        if not cart:
            return False, "Cart is empty.", None

        subtotal = sum(item['quantity'] * item['unit_price'] for item in cart)
        gst_amount = round(subtotal * gst_percent / 100, 2)
        total_amount = round(subtotal + gst_amount, 2)

        # Record each item as a real sale first (reuses your existing,
        # already-tested stock + sales logic). If any item fails
        # (e.g. insufficient stock), we stop before creating the bill.
        for item in cart:
            success = SalesManager.record_sale(item['product_id'], item['quantity'], discount_percent=0)
            if not success:
                return False, f"Failed to sell {item['product_name']} (insufficient stock?).", None

        try:
            db.execute_query(
                """INSERT INTO bills (customer_name, payment_method, subtotal, gst_percent, gst_amount, total_amount)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (customer_name, payment_method, subtotal, gst_percent, gst_amount, total_amount)
            )
            bill_row = db.fetch_one("SELECT last_insert_rowid() as id")
            bill_id = bill_row["id"]

            for item in cart:
                line_total = round(item['quantity'] * item['unit_price'], 2)
                db.execute_query(
                    """INSERT INTO bill_items (bill_id, product_id, product_name, quantity, unit_price, line_total)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (bill_id, item['product_id'], item['product_name'], item['quantity'], item['unit_price'], line_total)
                )

            # Revenue (including GST collected) goes into business funds
            db.add_business_money(total_amount)

            return True, "Bill created successfully.", bill_id
        except Exception as e:
            logger.error(f"Error creating bill: {e}")
            return False, f"Error creating bill: {e}", None

    # -----------------------------------------------------------------
    # Lookups
    # -----------------------------------------------------------------
    @staticmethod
    def get_bill(bill_id):
        """Returns (bill_dict, items_list) or (None, []) if not found."""
        try:
            bill = db.fetch_one("SELECT * FROM bills WHERE bill_id = ?", (bill_id,))
            if not bill:
                return None, []
            items = db.fetch_all("SELECT * FROM bill_items WHERE bill_id = ?", (bill_id,))
            return dict(bill), [dict(i) for i in items]
        except Exception as e:
            logger.error(f"Error fetching bill: {e}")
            return None, []

    @staticmethod
    def get_recent_bills(limit=20):
        """Returns a list of recent bills (most recent first)."""
        try:
            return db.fetch_all("SELECT * FROM bills ORDER BY created_at DESC LIMIT ?", (limit,))
        except Exception as e:
            logger.error(f"Error fetching recent bills: {e}")
            return []

    @staticmethod
    def get_recent_returns(limit=20):
        """Returns a list of recent returns (most recent first)."""
        try:
            return db.fetch_all("SELECT * FROM returns ORDER BY created_at DESC LIMIT ?", (limit,))
        except Exception as e:
            logger.error(f"Error fetching returns: {e}")
            return []

    # -----------------------------------------------------------------
    # Returns / Refunds
    # -----------------------------------------------------------------
    @staticmethod
    def process_return(bill_item_id, quantity, reason=""):
        """Return `quantity` units of a bill item: restocks the
        product and deducts the refund amount from business funds.

        Returns (success: bool, message: str)
        """
        try:
            item = db.fetch_one("SELECT * FROM bill_items WHERE bill_item_id = ?", (bill_item_id,))
            if not item:
                return False, "Bill item not found."

            already_returned = item["returned_quantity"] or 0
            remaining = item["quantity"] - already_returned

            if quantity <= 0:
                return False, "Return quantity must be greater than zero."
            if quantity > remaining:
                return False, f"Cannot return more than {remaining} remaining unit(s)."

            refund_amount = round(quantity * item["unit_price"], 2)

            # Put the stock back
            InventoryManager.update_stock(item["product_id"], quantity, 'restock')

            # Money goes back to the customer, out of business funds
            db.deduct_business_money(refund_amount)

            new_returned = already_returned + quantity
            db.execute_query(
                "UPDATE bill_items SET returned_quantity = ? WHERE bill_item_id = ?",
                (new_returned, bill_item_id)
            )

            db.execute_query(
                """INSERT INTO returns (bill_item_id, product_id, quantity, refund_amount, reason)
                   VALUES (?, ?, ?, ?, ?)""",
                (bill_item_id, item["product_id"], quantity, refund_amount, reason)
            )

            return True, f"Refunded ₹{refund_amount:,.2f} for {quantity} unit(s)."
        except Exception as e:
            logger.error(f"Error processing return: {e}")
            return False, f"Error: {e}"

    # -----------------------------------------------------------------
    # Receipt / Invoice formatting
    # -----------------------------------------------------------------
    @staticmethod
    def generate_thermal_receipt_text(bill, items):
        """Returns a narrow, monospace-formatted receipt string,
        similar to what a thermal till receipt looks like."""
        width = 32
        lines = []
        lines.append("MVA MART".center(width))
        lines.append("Supermarket Receipt".center(width))
        lines.append("-" * width)
        lines.append(f"Bill #{bill['bill_id']}")
        lines.append(f"{bill['created_at']}")
        if bill.get('customer_name'):
            lines.append(f"Customer: {bill['customer_name']}")
        lines.append("-" * width)

        for item in items:
            name = item['product_name'][:width]
            lines.append(name)
            qty_price = f"{item['quantity']} x Rs{item['unit_price']:.2f}"
            line_total = f"Rs{item['line_total']:.2f}"
            lines.append(f"  {qty_price:<20}{line_total:>10}")

        lines.append("-" * width)
        lines.append(f"{'Subtotal':<20}{'Rs' + format(bill['subtotal'], ',.2f'):>12}")
        lines.append(f"GST ({bill['gst_percent']}%){'':<10}{'Rs' + format(bill['gst_amount'], ',.2f'):>8}")
        lines.append(f"{'TOTAL':<20}{'Rs' + format(bill['total_amount'], ',.2f'):>12}")
        lines.append("-" * width)
        lines.append(f"Payment: {bill['payment_method']}")
        lines.append("")
        lines.append("Thank you for shopping!".center(width))
        return "\n".join(lines)

    @staticmethod
    def generate_qr_code_bytes(data: str):
        """Generates a QR code PNG (as raw bytes) encoding `data`.
        Returns None if the qrcode package isn't installed."""
        if not QRCODE_AVAILABLE:
            return None
        try:
            img = qrcode.make(data)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return buf.getvalue()
        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            return None

    @staticmethod
    def build_upi_qr_string(upi_id: str, payee_name: str, amount: float, bill_id: int):
        """Builds a standard UPI deep-link string that most UPI apps
        (PhonePe/GPay/Paytm) can scan to pre-fill a payment."""
        return (
            f"upi://pay?pa={upi_id}&pn={payee_name.replace(' ', '%20')}"
            f"&am={amount:.2f}&cu=INR&tn=MVA%20Mart%20Bill%20{bill_id}"
        )
