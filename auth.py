"""Authentication Module - Username/Password Login & Registration.

Uses only Python's built-in hashlib/secrets (no extra dependencies,
so it stays safe for Streamlit Cloud deployment). Passwords are never
stored in plain text -- each user gets a random salt, and we store
only the salted hash.
"""

import hashlib
import secrets
import logging
from database import db

logger = logging.getLogger(__name__)


class AuthManager:
    """Handles user registration, login, and the users table."""

    @staticmethod
    def ensure_users_table():
        """Creates the users table if it doesn't already exist.
        Safe to call every time the app starts."""
        try:
            db.execute_query('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    full_name TEXT,
                    role TEXT DEFAULT 'staff',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        except Exception as e:
            logger.error(f"Error creating users table: {e}")

    @staticmethod
    def _hash_password(password, salt):
        """Combine password + salt and hash with SHA-256."""
        return hashlib.sha256((salt + password).encode('utf-8')).hexdigest()

    @staticmethod
    def register_user(username, password, full_name="", role="staff"):
        """Create a new user account.

        Returns (success: bool, message: str)
        """
        username = username.strip()
        if not username or not password:
            return False, "Username and password are required."

        if len(password) < 4:
            return False, "Password must be at least 4 characters."

        salt = secrets.token_hex(16)
        password_hash = AuthManager._hash_password(password, salt)

        try:
            db.execute_query(
                """INSERT INTO users (username, password_hash, salt, full_name, role)
                   VALUES (?, ?, ?, ?, ?)""",
                (username, password_hash, salt, full_name, role)
            )
            return True, "Account created successfully! Please log in."
        except Exception as e:
            # Most common case: username already taken (UNIQUE constraint)
            logger.error(f"Registration error: {e}")
            return False, "That username is already taken. Please choose another."

    @staticmethod
    def login_user(username, password):
        """Verify username/password.

        Returns (success: bool, user_dict_or_None)
        user_dict has: user_id, username, full_name, role
        """
        username = username.strip()
        try:
            row = db.fetch_one(
                "SELECT * FROM users WHERE username = ?", (username,)
            )
            if not row:
                return False, None

            expected_hash = AuthManager._hash_password(password, row["salt"])

            if secrets.compare_digest(expected_hash, row["password_hash"]):
                user = {
                    "user_id": row["user_id"],
                    "username": row["username"],
                    "full_name": row["full_name"],
                    "role": row["role"],
                }
                return True, user

            return False, None
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False, None
