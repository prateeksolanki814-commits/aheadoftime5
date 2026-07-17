"""Employee Management Module.

Covers:
- Employee directory with 4 roles: Admin, Manager, Cashier, Store Keeper
- Attendance tracking (Present / Absent / Half Day / Leave)
- Salary management (monthly salary + payment records, Pending/Paid)
- Shift scheduling (Morning / Afternoon / Evening / Night)

This is independent of (but complementary to) the existing login system
in auth.py -- an employee record can optionally be linked to a
username for reference, but this module manages the HR side (profile,
attendance, salary, shifts), while auth.py continues to manage actual
login credentials.
"""

import logging
from datetime import datetime
from database import db

logger = logging.getLogger(__name__)

ROLES = ["Admin", "Manager", "Cashier", "Store Keeper"]
ATTENDANCE_STATUSES = ["Present", "Absent", "Half Day", "Leave"]
SHIFT_NAMES = ["Morning", "Afternoon", "Evening", "Night"]


class EmployeeManager:
    """Manages employees, attendance, salary payments, and shifts."""

    # -----------------------------------------------------------------
    # Setup
    # -----------------------------------------------------------------
    @staticmethod
    def ensure_tables():
        try:
            db.execute_query('''
                CREATE TABLE IF NOT EXISTS employees (
                    employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    phone TEXT,
                    email TEXT,
                    monthly_salary REAL DEFAULT 0,
                    join_date DATE,
                    username TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            db.execute_query('''
                CREATE TABLE IF NOT EXISTS attendance (
                    attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER NOT NULL,
                    attendance_date DATE NOT NULL,
                    status TEXT NOT NULL,
                    check_in TEXT,
                    check_out TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(employee_id, attendance_date)
                )
            ''')
            db.execute_query('''
                CREATE TABLE IF NOT EXISTS shifts (
                    shift_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER NOT NULL,
                    shift_date DATE NOT NULL,
                    shift_name TEXT NOT NULL,
                    start_time TEXT,
                    end_time TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            db.execute_query('''
                CREATE TABLE IF NOT EXISTS salary_payments (
                    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    pay_month INTEGER,
                    pay_year INTEGER,
                    status TEXT DEFAULT 'Pending',
                    payment_date TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        except Exception as e:
            logger.error(f"Error creating employee management tables: {e}")

    # -----------------------------------------------------------------
    # Employees
    # -----------------------------------------------------------------
    @staticmethod
    def add_employee(full_name, role, phone="", email="", monthly_salary=0.0, join_date=None, username=""):
        try:
            db.execute_query(
                """INSERT INTO employees (full_name, role, phone, email, monthly_salary, join_date, username)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (full_name, role, phone, email, monthly_salary, join_date, username)
            )
            return True, "Employee added successfully."
        except Exception as e:
            logger.error(f"Error adding employee: {e}")
            return False, f"Error: {e}"

    @staticmethod
    def get_all_employees(active_only=True):
        try:
            if active_only:
                return db.fetch_all("SELECT * FROM employees WHERE is_active = 1 ORDER BY full_name")
            return db.fetch_all("SELECT * FROM employees ORDER BY full_name")
        except Exception as e:
            logger.error(f"Error fetching employees: {e}")
            return []

    @staticmethod
    def get_employee_by_id(employee_id):
        try:
            return db.fetch_one("SELECT * FROM employees WHERE employee_id = ?", (employee_id,))
        except Exception as e:
            logger.error(f"Error fetching employee: {e}")
            return None

    @staticmethod
    def update_employee(employee_id, full_name=None, role=None, phone=None, email=None, monthly_salary=None):
        try:
            employee = EmployeeManager.get_employee_by_id(employee_id)
            if not employee:
                return False, "Employee not found."

            db.execute_query(
                """UPDATE employees SET full_name=?, role=?, phone=?, email=?, monthly_salary=?
                   WHERE employee_id=?""",
                (
                    full_name if full_name is not None else employee["full_name"],
                    role if role is not None else employee["role"],
                    phone if phone is not None else employee["phone"],
                    email if email is not None else employee["email"],
                    monthly_salary if monthly_salary is not None else employee["monthly_salary"],
                    employee_id
                )
            )
            return True, "Employee updated successfully."
        except Exception as e:
            logger.error(f"Error updating employee: {e}")
            return False, f"Error: {e}"

    @staticmethod
    def deactivate_employee(employee_id):
        try:
            db.execute_query("UPDATE employees SET is_active = 0 WHERE employee_id = ?", (employee_id,))
            return True, "Employee deactivated."
        except Exception as e:
            logger.error(f"Error deactivating employee: {e}")
            return False, f"Error: {e}"

    # -----------------------------------------------------------------
    # Attendance
    # -----------------------------------------------------------------
    @staticmethod
    def mark_attendance(employee_id, attendance_date, status, check_in="", check_out=""):
        """Marks (or updates, if already marked) attendance for one
        employee on one date."""
        try:
            db.execute_query(
                """INSERT INTO attendance (employee_id, attendance_date, status, check_in, check_out)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(employee_id, attendance_date)
                   DO UPDATE SET status=excluded.status, check_in=excluded.check_in, check_out=excluded.check_out""",
                (employee_id, attendance_date, status, check_in, check_out)
            )
            return True, "Attendance recorded."
        except Exception as e:
            logger.error(f"Error marking attendance: {e}")
            return False, f"Error: {e}"

    @staticmethod
    def get_attendance(attendance_date=None, employee_id=None, days=30):
        try:
            if attendance_date:
                if employee_id:
                    return db.fetch_all(
                        "SELECT * FROM attendance WHERE attendance_date = ? AND employee_id = ?",
                        (attendance_date, employee_id)
                    )
                return db.fetch_all("SELECT * FROM attendance WHERE attendance_date = ?", (attendance_date,))

            if employee_id:
                query = f"""
                    SELECT * FROM attendance
                    WHERE employee_id = ? AND attendance_date >= date('now', '-{days} days')
                    ORDER BY attendance_date DESC
                """
                return db.fetch_all(query, (employee_id,))

            query = f"""
                SELECT * FROM attendance
                WHERE attendance_date >= date('now', '-{days} days')
                ORDER BY attendance_date DESC
            """
            return db.fetch_all(query)
        except Exception as e:
            logger.error(f"Error fetching attendance: {e}")
            return []

    @staticmethod
    def get_attendance_summary(employee_id, days=30):
        """Returns counts of Present/Absent/Half Day/Leave for an
        employee over the last N days."""
        records = EmployeeManager.get_attendance(employee_id=employee_id, days=days)
        summary = {status: 0 for status in ATTENDANCE_STATUSES}
        for r in records:
            if r["status"] in summary:
                summary[r["status"]] += 1
        return summary

    # -----------------------------------------------------------------
    # Shifts
    # -----------------------------------------------------------------
    @staticmethod
    def assign_shift(employee_id, shift_date, shift_name, start_time="", end_time=""):
        try:
            db.execute_query(
                """INSERT INTO shifts (employee_id, shift_date, shift_name, start_time, end_time)
                   VALUES (?, ?, ?, ?, ?)""",
                (employee_id, shift_date, shift_name, start_time, end_time)
            )
            return True, "Shift assigned."
        except Exception as e:
            logger.error(f"Error assigning shift: {e}")
            return False, f"Error: {e}"

    @staticmethod
    def get_shifts(employee_id=None, days=7):
        try:
            if employee_id:
                query = f"""
                    SELECT * FROM shifts
                    WHERE employee_id = ? AND shift_date >= date('now', '-1 days')
                    ORDER BY shift_date ASC LIMIT 50
                """
                return db.fetch_all(query, (employee_id,))
            query = """
                SELECT * FROM shifts
                WHERE shift_date >= date('now', '-1 days')
                ORDER BY shift_date ASC LIMIT 100
            """
            return db.fetch_all(query)
        except Exception as e:
            logger.error(f"Error fetching shifts: {e}")
            return []

    # -----------------------------------------------------------------
    # Salary
    # -----------------------------------------------------------------
    @staticmethod
    def record_salary_payment(employee_id, amount, pay_month, pay_year, status="Pending"):
        try:
            payment_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S') if status == "Paid" else None
            db.execute_query(
                """INSERT INTO salary_payments (employee_id, amount, pay_month, pay_year, status, payment_date)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (employee_id, amount, pay_month, pay_year, status, payment_date)
            )
            return True, "Salary record created."
        except Exception as e:
            logger.error(f"Error recording salary payment: {e}")
            return False, f"Error: {e}"

    @staticmethod
    def mark_salary_paid(payment_id):
        try:
            db.execute_query(
                "UPDATE salary_payments SET status='Paid', payment_date=? WHERE payment_id=?",
                (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), payment_id)
            )
            return True, "Marked as paid."
        except Exception as e:
            logger.error(f"Error marking salary paid: {e}")
            return False, f"Error: {e}"

    @staticmethod
    def get_salary_history(employee_id=None, limit=50):
        try:
            if employee_id:
                return db.fetch_all(
                    "SELECT * FROM salary_payments WHERE employee_id = ? ORDER BY created_at DESC LIMIT ?",
                    (employee_id, limit)
                )
            return db.fetch_all("SELECT * FROM salary_payments ORDER BY created_at DESC LIMIT ?", (limit,))
        except Exception as e:
            logger.error(f"Error fetching salary history: {e}")
            return []

    @staticmethod
    def get_pending_salaries():
        try:
            return db.fetch_all("SELECT * FROM salary_payments WHERE status = 'Pending' ORDER BY created_at DESC")
        except Exception as e:
            logger.error(f"Error fetching pending salaries: {e}")
            return []
