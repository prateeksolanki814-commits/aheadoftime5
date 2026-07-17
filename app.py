"""
AI-Driven Smart Inventory & Financial Analytics Dashboard
Main Streamlit Application
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import urllib.parse
import html as html_lib
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from forecasting import DemandForecaster

# Import custom modules
from database import db, DatabaseManager
from inventory import InventoryManager
from sales import SalesManager
from analytics import Analytics
from discount_engine import DiscountEngine
from forecasting import DemandForecaster
from auth import AuthManager
from ai_customers import AICustomerManager
from discount_log import DiscountLogManager
from translations import t
from chatbot import get_bot_response
from billing import BillingManager
from employee_management import EmployeeManager, ROLES, ATTENDANCE_STATUSES, SHIFT_NAMES
# Page configuration
st.set_page_config(
    page_title="MVA MART",
    page_icon="🕰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS (existing styles + live animated background)
st.markdown("""
    <style>
    /* ---------- Live animated background ---------- */
    .stApp {
        background: linear-gradient(-45deg, #0f2027, #203a43, #2c5364, #1f4037, #99f2c8);
        background-size: 400% 400%;
        animation: gradientBG 18s ease infinite;
    }
    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    /* keep content readable on top of the moving background */
    section.main > div {
        background-color: rgba(255, 255, 255, 0.92);
        border-radius: 14px;
        padding: 1.2rem;
    }
    [data-testid="stSidebar"] {
        background-color: rgba(15, 32, 39, 0.92);
    }

    /* ---------- Existing styles ---------- */
    [data-testid="stMetricValue"] {
        font-size: 28px;
    }
    .main {
        padding-top: 0rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
    }
    .alert-critical {
        background-color: #ffcccc;
        border-left: 4px solid #da1e28;
        padding: 10px;
        border-radius: 4px;
        margin: 5px 0;
    }
    .alert-warning {
        background-color: #fff4e6;
        border-left: 4px solid #f1c21b;
        padding: 10px;
        border-radius: 4px;
        margin: 5px 0;
    }
    .alert-info {
        background-color: #e3f2fd;
        border-left: 4px solid #0f62fe;
        padding: 10px;
        border-radius: 4px;
        margin: 5px 0;
    }

    /* ---------- Login page hero banner ---------- */
    .login-hero {
        background: linear-gradient(135deg, #ff7e5f 0%, #d63447 60%, #b0206b 100%);
        border-radius: 0 0 60px 60px;
        padding: 50px 20px 60px 20px;
        text-align: center;
        color: white;
        margin: -1.2rem -1.2rem 2rem -1.2rem;
        box-shadow: 0 8px 24px rgba(214, 52, 71, 0.35);
    }
    .login-hero-icon {
        font-size: 56px;
        line-height: 1;
        margin-bottom: 8px;
    }
    .login-hero-title {
        font-size: 30px;
        font-weight: 800;
        letter-spacing: 1px;
        margin: 6px 0 4px 0;
    }
    .login-hero-tag {
        font-size: 15px;
        opacity: 0.95;
        margin: 0;
    }
    .login-hero-deco {
        position: absolute;
        font-size: 22px;
        opacity: 0.25;
    }
    .login-hero {
        position: relative;
        overflow: hidden;
    }

    /* ---------- Gradient pill buttons (Sign In / Sign Up / etc.) ---------- */
    .stButton > button, .stFormSubmitButton > button {
        background: linear-gradient(135deg, #ff7e5f 0%, #d63447 100%);
        color: white;
        border: none;
        border-radius: 30px;
        padding: 10px 24px;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(214, 52, 71, 0.35);
        transition: transform 0.15s ease;
    }
    .stButton > button:hover, .stFormSubmitButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(214, 52, 71, 0.45);
        color: white;
    }

    /* ---------- Executive Dashboard (dark theme) ---------- */
    .st-key-exec_dashboard {
        background: linear-gradient(180deg, #0b1220 0%, #111a2e 100%);
        border-radius: 20px;
        padding: 22px 24px 30px 24px;
    }
    .st-key-inventory_dashboard {
        background: linear-gradient(180deg, #0b1220 0%, #111a2e 100%);
        border-radius: 20px;
        padding: 22px 24px 30px 24px;
    }
    .st-key-sales_dashboard {
        background: linear-gradient(180deg, #0b1220 0%, #111a2e 100%);
        border-radius: 20px;
        padding: 22px 24px 30px 24px;
    }
    .st-key-billing_dashboard {
        background: linear-gradient(180deg, #0b1220 0%, #111a2e 100%);
        border-radius: 20px;
        padding: 22px 24px 30px 24px;
    }
    .st-key-employees_dashboard {
        background: linear-gradient(180deg, #0b1220 0%, #111a2e 100%);
        border-radius: 20px;
        padding: 22px 24px 30px 24px;
    }
    .st-key-analytics_dashboard {
        background: linear-gradient(180deg, #0b1220 0%, #111a2e 100%);
        border-radius: 20px;
        padding: 22px 24px 30px 24px;
    }
    .st-key-forecasting_dashboard {
        background: linear-gradient(180deg, #0b1220 0%, #111a2e 100%);
        border-radius: 20px;
        padding: 22px 24px 30px 24px;
    }
    .st-key-alerts_dashboard {
        background: linear-gradient(180deg, #0b1220 0%, #111a2e 100%);
        border-radius: 20px;
        padding: 22px 24px 30px 24px;
    }
    .st-key-restock_dashboard {
        background: linear-gradient(180deg, #0b1220 0%, #111a2e 100%);
        border-radius: 20px;
        padding: 22px 24px 30px 24px;
    }
    .st-key-discounts_dashboard {
        background: linear-gradient(180deg, #0b1220 0%, #111a2e 100%);
        border-radius: 20px;
        padding: 22px 24px 30px 24px;
    }
    .st-key-reports_dashboard {
        background: linear-gradient(180deg, #0b1220 0%, #111a2e 100%);
        border-radius: 20px;
        padding: 22px 24px 30px 24px;
    }
    .st-key-ai_customers_dashboard {
        background: linear-gradient(180deg, #0b1220 0%, #111a2e 100%);
        border-radius: 20px;
        padding: 22px 24px 30px 24px;
    }
    .dash-header {
        display: flex;
        align-items: center;
        gap: 14px;
        background: linear-gradient(90deg, #1b2540, #0f172a);
        border-radius: 14px;
        padding: 16px 20px;
        margin-bottom: 20px;
        border-left: 5px solid #5b7bf7;
    }
    .dash-header-icon { font-size: 30px; }
    .dash-header-title {
        font-size: 24px;
        font-weight: 800;
        color: #ffffff;
        margin: 0;
    }
    .kpi-row {
        display: flex;
        flex-wrap: wrap;
        gap: 14px;
        margin-bottom: 22px;
    }
    .kpi-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 14px 18px;
        flex: 1;
        min-width: 150px;
    }
    .kpi-icon {
        width: 34px;
        height: 34px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        margin-bottom: 8px;
    }
    .kpi-label {
        font-size: 12px;
        font-weight: 700;
        color: #c7cbe0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    .kpi-value {
        font-size: 24px;
        font-weight: 800;
    }
    .kpi-sub {
        font-size: 11px;
        color: #8b93ad;
        margin-top: 4px;
    }
    .section-title {
        font-size: 15px;
        font-weight: 800;
        color: #ffffff;
        margin: 8px 0 10px 0;
        padding-bottom: 6px;
        border-bottom: 2px solid rgba(255,255,255,0.15);
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'refresh' not in st.session_state:
    st.session_state.refresh = False
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'language' not in st.session_state:
    st.session_state.language = 'en'

# Make sure the users table exists
AuthManager.ensure_users_table()
AICustomerManager.ensure_table()
DiscountLogManager.ensure_table()
BillingManager.ensure_tables()
EmployeeManager.ensure_tables()


def show_language_switcher():
    """Top-right language selector (English / हिंदी) for the login page.
    Changes apply across the whole app immediately."""
    lang_col1, lang_col2 = st.columns([5, 1])
    with lang_col2:
        current_lang_label = "English" if st.session_state.language == "en" else "हिंदी"
        chosen = st.selectbox(
            t("language_label"),
            options=["English", "हिंदी"],
            index=0 if st.session_state.language == "en" else 1,
            key="language_selector",
            label_visibility="visible"
        )
        new_lang = "en" if chosen == "English" else "hi"
        if new_lang != st.session_state.language:
            st.session_state.language = new_lang
            st.rerun()


def show_top_bar():
    """Top bar shown on every logged-in page: language switcher, the
    Funds widget, and the AI Assistant chatbot -- all in the top-right
    area using the same reliable popover pattern."""
    col_spacer, col_lang, col_funds, col_chat = st.columns([3.2, 1.3, 1.6, 0.9])

    with col_lang:
        chosen = st.selectbox(
            t("language_label"),
            options=["English", "हिंदी"],
            index=0 if st.session_state.language == "en" else 1,
            key="top_bar_language_selector",
            label_visibility="visible"
        )
        new_lang = "en" if chosen == "English" else "hi"
        if new_lang != st.session_state.language:
            st.session_state.language = new_lang
            st.rerun()

    with col_funds:
        try:
            current_funds = db.get_business_money()
        except Exception:
            current_funds = 0

        with st.popover(f"{t('funds_label')}: ₹{current_funds:,.0f}", use_container_width=True):
            st.write(f"**{t('current_funds')}:** ₹{current_funds:,.2f}")
            new_funds = st.number_input(
                t("set_total_funds"),
                min_value=0.0,
                value=float(current_funds),
                step=100.0,
                key="funds_input_value"
            )
            if st.button(t("update_funds_btn"), key="update_funds_action", use_container_width=True):
                db.set_business_money(new_funds)
                st.success(t("funds_updated"))
                st.rerun()

    with col_chat:
        if 'chatbot_history' not in st.session_state:
            st.session_state.chatbot_history = []

        with st.popover("🤖", use_container_width=True):
            st.markdown("**🤖 MVA Mart Assistant**")
            st.caption("Ask me anything about this project, no limit on questions!")

            history_box = st.container(height=280)
            with history_box:
                if not st.session_state.chatbot_history:
                    with st.chat_message("assistant", avatar="🤖"):
                        st.write("Hi! Ask me anything about MVA Mart — products, sales, discounts, forecasting, funds, or how any feature works.")
                for role, msg in st.session_state.chatbot_history:
                    avatar = "🤖" if role == "assistant" else "🙂"
                    with st.chat_message(role, avatar=avatar):
                        st.write(msg)

            with st.form("chatbot_form", clear_on_submit=True):
                user_question = st.text_input(
                    "Your question", placeholder="e.g. How do I add a product?",
                    label_visibility="collapsed"
                )
                submitted = st.form_submit_button("Send", use_container_width=True)
                if submitted and user_question.strip():
                    with st.spinner("Thinking..."):
                        answer = get_bot_response(user_question, history=st.session_state.chatbot_history)
                    st.session_state.chatbot_history.append(("user", user_question))
                    st.session_state.chatbot_history.append(("assistant", answer))
                    st.rerun()

            if st.session_state.chatbot_history:
                if st.button("🗑️ Clear chat", key="clear_chatbot", use_container_width=True):
                    st.session_state.chatbot_history = []
                    st.rerun()


def show_login_page():
    """Login + Register screen. Blocks the rest of the app until the
    user is authenticated."""

    show_language_switcher()

    st.markdown(
        f"""
        <div class="login-hero">
            <span class="login-hero-deco" style="top:15px; left:8%;">🍎</span>
            <span class="login-hero-deco" style="top:60px; left:80%;">🥕</span>
            <span class="login-hero-deco" style="top:110px; left:15%;">🍞</span>
            <span class="login-hero-deco" style="top:20px; left:45%;">🥛</span>
            <span class="login-hero-deco" style="top:130px; left:70%;">🍇</span>
            <span class="login-hero-deco" style="top:70px; left:3%;">🧅</span>
            <div class="login-hero-icon">🛒</div>
            <div class="login-hero-title">{t("app_name")}</div>
            <p class="login-hero-tag">{t("app_tagline").replace(chr(10), "<br>")}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        st.markdown(
            """
            <div style="margin-top:60px;">
            <svg viewBox="0 0 220 300" xmlns="http://www.w3.org/2000/svg">
              <defs>
                <linearGradient id="blobGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stop-color="#ff9a76"/>
                  <stop offset="100%" stop-color="#d63447"/>
                </linearGradient>
                <linearGradient id="basketGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stop-color="#fff3e0"/>
                  <stop offset="100%" stop-color="#ffe0b2"/>
                </linearGradient>
              </defs>
              <ellipse cx="110" cy="190" rx="100" ry="90" fill="url(#blobGrad)" opacity="0.18"/>
              <path d="M 60 160 Q 110 80 160 160" stroke="#c9975a" stroke-width="10" fill="none" stroke-linecap="round"/>
              <path d="M 45 165 L 175 165 L 160 260 Q 110 275 60 260 Z" fill="url(#basketGrad)" stroke="#d9a86c" stroke-width="3"/>
              <line x1="55" y1="180" x2="165" y2="180" stroke="#d9a86c" stroke-width="2" opacity="0.6"/>
              <line x1="58" y1="200" x2="162" y2="200" stroke="#d9a86c" stroke-width="2" opacity="0.6"/>
              <line x1="61" y1="220" x2="159" y2="220" stroke="#d9a86c" stroke-width="2" opacity="0.6"/>
              <line x1="65" y1="240" x2="155" y2="240" stroke="#d9a86c" stroke-width="2" opacity="0.6"/>
              <circle cx="80" cy="150" r="20" fill="#e63946"/>
              <path d="M 80 130 Q 84 122 92 124" stroke="#4b7a3a" stroke-width="4" fill="none" stroke-linecap="round"/>
              <rect x="105" y="130" width="55" height="35" rx="16" fill="#c9853f"/>
              <path d="M 118 132 Q 132 122 146 132" stroke="#8a5a24" stroke-width="3" fill="none" stroke-linecap="round"/>
              <path d="M 55 150 Q 40 130 55 110 Q 70 100 75 115" stroke="#f4c430" stroke-width="12" fill="none" stroke-linecap="round"/>
              <rect x="140" y="105" width="18" height="45" rx="4" fill="#5a9e6f"/>
              <rect x="145" y="95" width="8" height="14" rx="2" fill="#3d7a52"/>
            </svg>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            """
            <div style="margin-top:60px;">
            <svg viewBox="0 0 220 300" xmlns="http://www.w3.org/2000/svg">
              <defs>
                <linearGradient id="blobGrad2" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stop-color="#ff9a76"/>
                  <stop offset="100%" stop-color="#b0206b"/>
                </linearGradient>
                <linearGradient id="bagGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stop-color="#d9a86c"/>
                  <stop offset="100%" stop-color="#b9824a"/>
                </linearGradient>
              </defs>
              <ellipse cx="110" cy="180" rx="100" ry="95" fill="url(#blobGrad2)" opacity="0.18"/>
              <path d="M 65 130 L 155 130 L 165 265 Q 110 280 55 265 Z" fill="url(#bagGrad)"/>
              <path d="M 65 130 L 70 110 L 150 110 L 155 130 Z" fill="#c9975a"/>
              <rect x="95" y="95" width="10" height="20" rx="4" fill="#8a5a24"/>
              <rect x="115" y="95" width="10" height="20" rx="4" fill="#8a5a24"/>
              <path d="M 70 150 L 150 150" stroke="#8a5a24" stroke-width="2" opacity="0.5"/>
              <ellipse cx="45" cy="220" rx="30" ry="45" fill="#c9853f" transform="rotate(-18 45 220)"/>
              <path d="M 30 195 Q 45 185 60 195" stroke="#8a5a24" stroke-width="3" fill="none" stroke-linecap="round" transform="rotate(-18 45 220)"/>
              <path d="M 28 210 Q 45 200 62 210" stroke="#8a5a24" stroke-width="3" fill="none" stroke-linecap="round" transform="rotate(-18 45 220)"/>
              <path d="M 95 130 Q 90 105 105 90" stroke="#4b7a3a" stroke-width="8" fill="none" stroke-linecap="round"/>
              <path d="M 108 130 Q 112 100 130 85" stroke="#5c9c4a" stroke-width="8" fill="none" stroke-linecap="round"/>
              <path d="M 120 130 Q 128 108 140 100" stroke="#4b7a3a" stroke-width="8" fill="none" stroke-linecap="round"/>
              <circle cx="165" cy="210" r="16" fill="#e63946"/>
              <path d="M 160 197 Q 165 190 172 195" stroke="#4b7a3a" stroke-width="3" fill="none" stroke-linecap="round"/>
            </svg>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        with st.container(border=True):
            login_tab, register_tab = st.tabs([t("sign_in_tab"), t("sign_up_tab")])

            with login_tab:
                with st.form("login_form"):
                    username = st.text_input(t("username"), placeholder="Enter your username")
                    password = st.text_input(t("password"), type="password", placeholder="Enter your password")
                    submitted = st.form_submit_button(t("sign_in_btn"), use_container_width=True)

                    if submitted:
                        success, user = AuthManager.login_user(username, password)
                        if success:
                            st.session_state.logged_in = True
                            st.session_state.user = user
                            st.success(f"Welcome back, {user['full_name'] or user['username']}!")
                            st.rerun()
                        else:
                            st.error("❌ Invalid username or password.")

                st.markdown(
                    f"<p style='text-align:center; color:#666; margin-top:10px;'>{t('no_account_msg')}</p>",
                    unsafe_allow_html=True
                )

            with register_tab:
                with st.form("register_form"):
                    new_full_name = st.text_input(t("full_name"), placeholder="Your full name")
                    new_username = st.text_input(t("choose_username"), placeholder="Pick a username")
                    new_password = st.text_input(t("choose_password"), type="password", placeholder="At least 4 characters")
                    confirm_password = st.text_input(t("confirm_password"), type="password", placeholder="Re-enter password")
                    new_role = st.selectbox(t("role"), ROLES)
                    register_submitted = st.form_submit_button(t("create_account_btn"), use_container_width=True)

                    if register_submitted:
                        if new_password != confirm_password:
                            st.error("❌ Passwords do not match.")
                        else:
                            success, message = AuthManager.register_user(
                                new_username, new_password, new_full_name, new_role
                            )
                            if success:
                                st.success(f"✅ {message}")
                            else:
                                st.error(f"❌ {message}")


# Block the rest of the app until logged in
if not st.session_state.logged_in:
    show_login_page()
    st.stop()

# Top bar - language switcher, funds widget, and AI Assistant chatbot (top right corner)
show_top_bar()

# Quietly check if a new AI customer message should arrive (based on
# elapsed time). This runs on every normal Streamlit rerun -- it never
# reloads the browser, so it never affects your login session.
AICustomerManager.maybe_auto_generate(min_interval_seconds=30)


def create_sample_data():
    """Create sample inventory data."""
    sample_products = [
        ("Colgate", "Personal Care", 80, 120, 150, 50, (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d')),
        ("Amul Milk", "Dairy", 40, 60, 200, 100, (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')),
        ("Britannia Bread", "Bakery", 25, 40, 100, 40, (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')),
        ("Parle-G", "Biscuits", 20, 35, 300, 100, (datetime.now() + timedelta(days=120)).strftime('%Y-%m-%d')),
        ("Maggi", "Instant Foods", 8, 15, 400, 150, (datetime.now() + timedelta(days=180)).strftime('%Y-%m-%d')),
        ("Surf Excel", "Detergent", 200, 300, 80, 30, (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')),
        ("Tata Salt", "Condiments", 15, 25, 250, 80, (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')),
        ("Aashirvaad Atta", "Staples", 350, 450, 60, 20, (datetime.now() + timedelta(days=200)).strftime('%Y-%m-%d')),
        ("Lay's Chips", "Snacks", 30, 50, 180, 60, (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d')),
        ("Coca-Cola", "Beverages", 40, 70, 220, 80, (datetime.now() + timedelta(days=150)).strftime('%Y-%m-%d')),
    ]
    
    for product in sample_products:
        try:
            InventoryManager.add_product(*product)
        except:
            pass  # Product already exists

# Maps each internal (English) page identifier to its translation key.
# The internal identifiers never change with language -- only the
# displayed label does -- so none of the `if page == "..."` checks
# elsewhere in this file need to change.
NAV_LABELS = {
    "📊 Dashboard": "nav_dashboard",
    "📦 Inventory": "nav_inventory",
    "🛒 Sales": "nav_sales",
    "🧾 Billing": "nav_billing",
    "👥 Employees": "nav_employees",
    "🤖 AI Customers": "nav_ai_customers",
    "📈 Analytics": "nav_analytics",
    "🔮 Forecasting": "nav_forecasting",
    "⚠️ Alerts": "nav_alerts",
    "📥 Restock": "nav_restock",
    "💰 Discounts": "nav_discounts",
    "📋 Reports": "nav_reports",
}

# Sidebar Navigation
with st.sidebar:
    st.title(f"🕰️ {t('app_name')}")

    user = st.session_state.user
    st.caption(f"{t('logged_in_as')} **{user['full_name'] or user['username']}** ({user['role']})")
    if st.button(t("logout"), use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.rerun()

    st.markdown("---")

    page = st.radio(
        "Navigate",
        list(NAV_LABELS.keys()),
        format_func=lambda x: t(NAV_LABELS[x]),
        label_visibility="collapsed"
    )
    st.markdown("---")
    
    # Quick actions
    st.subheader(t("quick_actions"))
    
    if st.button(t("refresh_data")):
        st.session_state.refresh = True
        st.rerun()
    
    if st.button(t("load_sample_data")):
        create_sample_data()
        st.success("Sample data loaded!")
        st.rerun()
    
    st.markdown("---")
    st.caption("AI-Driven Inventory Management System")
    st.caption("HCL Jigsaw Innovation Challenge")

# Main content based on page selection
if page == "📊 Dashboard":
    kpis = Analytics.get_kpis(days=30)

    with st.container(key="exec_dashboard"):
        # ---- Header bar ----
        st.markdown(
            '<div class="dash-header"><div class="dash-header-icon">🕰️</div>'
            f'<div class="dash-header-title">{t("dashboard_header")}</div></div>',
            unsafe_allow_html=True
        )

        if kpis:
            inv_value = kpis.get('total_inventory_value', 0)
            revenue = kpis.get('total_revenue', 0)
            profit = kpis.get('total_profit', 0)
            margin = kpis.get('profit_margin_percent', 0)
            low_stock = kpis.get('items_in_low_stock', 0)
            near_expiry = kpis.get('items_near_expiry', 0)

            try:
                dash_ai_recommendations = DemandForecaster.get_all_recommendations()
                dash_ai_reorder_count = len(dash_ai_recommendations)
            except Exception:
                dash_ai_reorder_count = 0

            dash_discounts_30d = DiscountLogManager.count_recent_discounts(days=30)

            # ---- KPI cards (built from your real project data) ----
            kpi_cards = [
                ("💼", "#5b7bf7", t("kpi_inventory_value"), f"₹{inv_value:,.0f}", t("sub_stock_cost_price")),
                ("💰", "#2ecc91", t("kpi_revenue"), f"₹{revenue:,.0f}", t("sub_last_30_days")),
                ("📈", "#22c1c3", t("kpi_profit"), f"₹{profit:,.0f}", t("sub_last_30_days")),
                ("📊", "#f6a623", t("kpi_profit_margin"), f"{margin:.1f}%", t("sub_revenue_based")),
                ("⚠️", "#ff5c6a", t("kpi_low_stock"), f"{low_stock}", t("sub_below_reorder")),
                ("⏰", "#9b6bff", t("kpi_near_expiry"), f"{near_expiry}", t("sub_expiring_soon")),
                ("🤖", "#4cc9f0", t("kpi_ai_reorder_needed"), f"{dash_ai_reorder_count}", t("sub_predicted_by_ai")),
                ("🏷️", "#ff8fab", t("kpi_discounts_applied"), f"{dash_discounts_30d}", t("sub_last_30_days")),
            ]

            cards_html = '<div class="kpi-row">'
            for icon, color, label, value, sub in kpi_cards:
                cards_html += (
                    '<div class="kpi-card">'
                    f'<div class="kpi-icon" style="background:{color}22; color:{color};">{icon}</div>'
                    f'<div class="kpi-label">{label}</div>'
                    f'<div class="kpi-value" style="color:{color};">{value}</div>'
                    f'<div class="kpi-sub">{sub}</div>'
                    '</div>'
                )
            cards_html += '</div>'
            st.markdown(cards_html, unsafe_allow_html=True)

            # ---- Sales trend (full width) ----
            st.markdown('<div class="section-title">📊 Sales Trend (Last 30 Days)</div>', unsafe_allow_html=True)
            try:
                trend_data = Analytics.get_sales_trend(days=30)
                if trend_data:
                    df = pd.DataFrame(trend_data)
                    df['date'] = pd.to_datetime(df['date'])

                    fig = make_subplots(specs=[[{"secondary_y": True}]])
                    fig.add_trace(
                        go.Scatter(x=df['date'], y=df['revenue'], name="Revenue",
                                   mode='lines+markers', line=dict(color='#5b7bf7', width=3)),
                        secondary_y=False
                    )
                    fig.add_trace(
                        go.Bar(x=df['date'], y=df['units_sold'], name="Units Sold",
                               marker_color='#22c1c3', opacity=0.5),
                        secondary_y=True
                    )
                    fig.update_layout(
                        template="plotly_dark",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        xaxis_title="Date", yaxis_title="Revenue (₹)",
                        hovermode='x unified', height=350,
                        margin=dict(l=10, r=10, t=20, b=10),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02)
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No sales yet — record a sale to see the trend here.")
            except Exception as e:
                st.error(f"Error loading trend: {e}")

            # ---- 2x2 chart grid ----
            row1_col1, row1_col2 = st.columns(2)

            with row1_col1:
                st.markdown('<div class="section-title">📦 Stock Levels</div>', unsafe_allow_html=True)
                try:
                    products = InventoryManager.get_all_products()
                    if not products.empty:
                        fig = px.bar(
                            products, x='product_name', y='stock',
                            labels={'stock': 'Quantity', 'product_name': 'Product'},
                            color='stock', color_continuous_scale='Tealgrn'
                        )
                        fig.add_hline(y=products['reorder_level'].mean(),
                                      line_dash="dash", line_color="#ff5c6a",
                                      annotation_text="Reorder Level")
                        fig.update_layout(
                            template="plotly_dark",
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            height=320, margin=dict(l=10, r=10, t=20, b=10)
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No products yet.")
                except Exception as e:
                    st.error(f"Error loading chart: {e}")

            with row1_col2:
                st.markdown('<div class="section-title">🗂️ Revenue by Category</div>', unsafe_allow_html=True)
                try:
                    category_data = Analytics.get_category_performance()
                    if category_data:
                        df = pd.DataFrame(category_data)
                        fig = px.pie(
                            df, values='revenue', names='category', hole=0.6,
                            color_discrete_sequence=['#5b7bf7', '#2ecc91', '#f6a623', '#22c1c3',
                                                      '#9b6bff', '#ff5c6a', '#ffd166', '#4cc9f0']
                        )
                        fig.update_layout(
                            template="plotly_dark",
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            height=320, margin=dict(l=10, r=10, t=20, b=10),
                            showlegend=True
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No category data yet.")
                except Exception as e:
                    st.error(f"Error loading chart: {e}")

            row2_col1, row2_col2 = st.columns(2)

            with row2_col1:
                st.markdown('<div class="section-title">💹 Profit by Product</div>', unsafe_allow_html=True)
                try:
                    sales_contrib = SalesManager.get_product_sales_contribution()
                    if sales_contrib:
                        df = pd.DataFrame(sales_contrib, columns=['product_id', 'product_name', 'revenue', 'profit'])
                        fig = px.pie(
                            df, values='profit', names='product_name', hole=0.6,
                            color_discrete_sequence=['#2ecc91', '#5b7bf7', '#f6a623', '#22c1c3',
                                                      '#9b6bff', '#ff5c6a', '#ffd166', '#4cc9f0']
                        )
                        fig.update_layout(
                            template="plotly_dark",
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            height=320, margin=dict(l=10, r=10, t=20, b=10)
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No sales yet.")
                except Exception as e:
                    st.error(f"Error loading chart: {e}")

            with row2_col2:
                st.markdown('<div class="section-title">🏆 Top Products by Revenue</div>', unsafe_allow_html=True)
                try:
                    top_products = Analytics.get_top_products(metric='revenue', limit=8)
                    if top_products:
                        df = pd.DataFrame(top_products)
                        fig = px.bar(
                            df, x='product_name', y='value',
                            color='value', color_continuous_scale='Bluyl'
                        )
                        fig.update_layout(
                            template="plotly_dark",
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            height=320, margin=dict(l=10, r=10, t=20, b=10),
                            xaxis_title="", yaxis_title="Revenue (₹)"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No sales yet.")
                except Exception as e:
                    st.error(f"Error loading chart: {e}")

            # ---- Recently Applied Discounts (updates live whenever you apply a discount) ----
            st.markdown('<div class="section-title">🏷️ Recently Applied Discounts</div>', unsafe_allow_html=True)
            recent_discounts = DiscountLogManager.get_recent_discounts(limit=10)
            if recent_discounts:
                disc_df = pd.DataFrame([dict(d) for d in recent_discounts])
                disc_df = disc_df.rename(columns={
                    'product_name': 'Product', 'discount_percent': 'Discount %',
                    'original_price': 'Original Price (₹)', 'discounted_price': 'New Price (₹)',
                    'reason': 'Reason', 'applied_at': 'Applied At'
                })
                st.dataframe(
                    disc_df[['Product', 'Discount %', 'Original Price (₹)', 'New Price (₹)', 'Reason', 'Applied At']],
                    use_container_width=True
                )
            else:
                st.info("No discounts applied yet. Apply one from the 💰 Discounts page and it will show up here.")
        else:
            st.info("📌 Load sample data from sidebar to see KPIs")

elif page == "📦 Inventory":
    with st.container(key="inventory_dashboard"):
        st.markdown(
            '<div class="dash-header"><div class="dash-header-icon">📦</div>'
            f'<div class="dash-header-title">{t("inventory_header")}</div></div>',
            unsafe_allow_html=True
        )

        try:
            products = InventoryManager.get_all_products()
        except Exception as e:
            products = pd.DataFrame()
            st.error(f"Error loading inventory: {e}")

        if not products.empty:
            total_products = len(products)
            total_units = int(products['stock'].sum())
            low_stock_count = int((products['stock'] <= products['reorder_level']).sum())
            category_count = products['category'].nunique()
        else:
            total_products = total_units = low_stock_count = category_count = 0

        inv_kpi_cards = [
            ("🏷️", "#5b7bf7", t("kpi_total_products"), f"{total_products}", t("sub_unique_skus")),
            ("📦", "#2ecc91", t("kpi_total_stock_units"), f"{total_units:,}", t("sub_across_products")),
            ("⚠️", "#ff5c6a", t("kpi_low_stock_items"), f"{low_stock_count}", t("sub_at_below_reorder")),
            ("🗂️", "#f6a623", t("kpi_categories"), f"{category_count}", t("sub_product_categories")),
        ]
        inv_cards_html = '<div class="kpi-row">'
        for icon, color, label, value, sub in inv_kpi_cards:
            inv_cards_html += (
                '<div class="kpi-card">'
                f'<div class="kpi-icon" style="background:{color}22; color:{color};">{icon}</div>'
                f'<div class="kpi-label">{label}</div>'
                f'<div class="kpi-value" style="color:{color};">{value}</div>'
                f'<div class="kpi-sub">{sub}</div>'
                '</div>'
            )
        inv_cards_html += '</div>'
        st.markdown(inv_cards_html, unsafe_allow_html=True)

        tab1, tab2, tab3, tab4 = st.tabs([t("tab_view"), t("tab_add_product"), t("tab_update"), t("tab_search")])

        with tab1:
            st.markdown('<div class="section-title">Current Inventory</div>', unsafe_allow_html=True)
            if not products.empty:
                st.dataframe(products, use_container_width=True)

                st.markdown('<div class="section-title">📊 Stock by Category</div>', unsafe_allow_html=True)
                cat_stock = products.groupby('category')['stock'].sum().reset_index()
                fig = px.bar(
                    cat_stock, x='category', y='stock',
                    color='stock', color_continuous_scale='Tealgrn'
                )
                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    height=320, margin=dict(l=10, r=10, t=20, b=10),
                    xaxis_title="", yaxis_title="Units in Stock"
                )
                st.plotly_chart(fig, use_container_width=True)

                st.markdown('<div class="section-title">🤖 AI Restock Recommendations</div>', unsafe_allow_html=True)
                try:
                    inv_ai_recs = DemandForecaster.get_all_recommendations()
                    if inv_ai_recs:
                        ai_df = pd.DataFrame(inv_ai_recs)
                        ai_df = ai_df.merge(
                            products[['product_id', 'product_name']], on='product_id', how='left'
                        )
                        ai_df = ai_df.rename(columns={
                            'product_name': 'Product', 'current_stock': 'Current Stock',
                            'forecasted_30day_demand': 'Predicted 30-Day Demand',
                            'recommended_quantity': 'Recommended Reorder Qty', 'status': 'Status'
                        })
                        st.dataframe(
                            ai_df[['Product', 'Current Stock', 'Predicted 30-Day Demand', 'Recommended Reorder Qty', 'Status']],
                            use_container_width=True
                        )
                    else:
                        st.info("🤖 AI predicts no restocking is needed right now.")
                except Exception as e:
                    st.error(f"Error loading AI recommendations: {e}")
            else:
                st.info("No products in inventory. Add products to get started!")

        with tab2:
            st.markdown('<div class="section-title">Add New Product</div>', unsafe_allow_html=True)
            with st.form("add_product_form"):
                col1, col2 = st.columns(2)

                with col1:
                    product_name = st.text_input(t("field_product_name"))
                    cost_price = st.number_input(t("field_cost_price"), min_value=0.0, step=10.0)
                    stock = st.number_input(t("field_initial_stock"), min_value=0, step=10)

                with col2:
                    category = st.selectbox(t("field_category"),
                        ["Personal Care", "Dairy", "Bakery", "Biscuits", "Instant Foods",
                         "Detergent", "Condiments", "Staples", "Snacks", "Beverages", "Other"])
                    selling_price = st.number_input(t("field_selling_price"), min_value=0.0, step=10.0)
                    reorder_level = st.number_input(t("field_reorder_level"), min_value=1, step=5)

                expiry_date = st.date_input(t("field_expiry_date"), value=datetime.now() + timedelta(days=90))

                if st.form_submit_button(t("btn_add_product")):
                    if product_name and cost_price > 0 and selling_price > cost_price:
                        initial_stock_cost = cost_price * stock
                        available_funds = db.get_business_money()

                        if initial_stock_cost > available_funds:
                            st.error(t("not_enough_money").format(
                                available=f"{available_funds:,.2f}",
                                required=f"{initial_stock_cost:,.2f}"
                            ))
                        elif InventoryManager.add_product(
                            product_name, category, cost_price, selling_price,
                            stock, reorder_level, expiry_date.strftime('%Y-%m-%d')
                        ):
                            db.deduct_business_money(initial_stock_cost)
                            st.success(f"✅ Product '{product_name}' added successfully! ₹{initial_stock_cost:,.2f} deducted from funds.")
                            st.rerun()
                        else:
                            st.error("❌ Failed to add product (may already exist)")
                    else:
                        st.error("❌ Invalid input: Check prices and fields")

        with tab3:
            st.markdown('<div class="section-title">Update Product</div>', unsafe_allow_html=True)
            try:
                if not products.empty:
                    product_id = st.selectbox(t("field_select_product"),
                        options=products['product_id'],
                        format_func=lambda x: products[products['product_id']==x]['product_name'].values[0])

                    product = InventoryManager.get_product_by_id(product_id)
                    if product:
                        col1, col2 = st.columns(2)
                        with col1:
                            new_stock = st.number_input("Stock", value=product[5], step=1)
                            new_cost = st.number_input("Cost Price", value=float(product[3]), step=1.0)
                        with col2:
                            new_selling = st.number_input("Selling Price", value=float(product[4]), step=1.0)
                            new_expiry = st.date_input(t("field_expiry_date"), value=datetime.strptime(product[7], '%Y-%m-%d'))

                        if st.button("💾 Update Product"):
                            InventoryManager.update_product(
                                product_id,
                                stock=new_stock,
                                cost_price=new_cost,
                                selling_price=new_selling,
                                expiry_date=new_expiry.strftime('%Y-%m-%d')
                            )
                            st.success("✅ Product updated!")
                            st.rerun()
                else:
                    st.info("No products in inventory yet.")
            except Exception as e:
                st.error(f"Error: {e}")

        with tab4:
            st.markdown('<div class="section-title">Search Products</div>', unsafe_allow_html=True)
            search_term = st.text_input(t("field_search_by_name"))
            category_filter = st.selectbox(t("field_filter_category"),
                ["All"] + InventoryManager.get_categories())

            if st.button(t("btn_search")):
                results = InventoryManager.search_products(
                    search_term=search_term if search_term else None,
                    category=category_filter if category_filter != "All" else None
                )
                if results:
                    df = pd.DataFrame(results, columns=['ID', 'Name', 'Category', 'Cost', 'Selling', 'Stock', 'Reorder', 'Expiry', 'Created', 'Updated'])
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No products found")

elif page == "🛒 Sales":
    with st.container(key="sales_dashboard"):
        st.markdown(
            '<div class="dash-header"><div class="dash-header-icon">🛒</div>'
            f'<div class="dash-header-title">{t("sales_header")}</div></div>',
            unsafe_allow_html=True
        )

        try:
            sales_kpi_df = SalesManager.get_sales_data(days=30)
        except Exception as e:
            sales_kpi_df = pd.DataFrame()
            st.error(f"Error loading sales: {e}")

        if not sales_kpi_df.empty:
            total_sales_count = len(sales_kpi_df)
            total_revenue_30 = sales_kpi_df['total_amount'].sum()
            total_discounts_30 = sales_kpi_df['discount_applied'].sum()
            total_units_30 = int(sales_kpi_df['quantity_sold'].sum())
        else:
            total_sales_count = total_revenue_30 = total_discounts_30 = total_units_30 = 0

        sales_kpi_cards = [
            ("🧾", "#5b7bf7", t("kpi_total_sales"), f"{total_sales_count}", t("sub_last_30_days")),
            ("💰", "#2ecc91", t("kpi_revenue"), f"₹{total_revenue_30:,.0f}", t("sub_last_30_days")),
            ("📦", "#22c1c3", t("kpi_units_sold"), f"{total_units_30:,}", t("sub_last_30_days")),
            ("🏷️", "#f6a623", t("kpi_discounts_given"), f"₹{total_discounts_30:,.0f}", t("sub_last_30_days")),
        ]
        sales_cards_html = '<div class="kpi-row">'
        for icon, color, label, value, sub in sales_kpi_cards:
            sales_cards_html += (
                '<div class="kpi-card">'
                f'<div class="kpi-icon" style="background:{color}22; color:{color};">{icon}</div>'
                f'<div class="kpi-label">{label}</div>'
                f'<div class="kpi-value" style="color:{color};">{value}</div>'
                f'<div class="kpi-sub">{sub}</div>'
                '</div>'
            )
        sales_cards_html += '</div>'
        st.markdown(sales_cards_html, unsafe_allow_html=True)

        # ---- AI Insight callout ----
        try:
            sales_ai_recs = DemandForecaster.get_all_recommendations()
            if sales_ai_recs:
                top_needs = sales_ai_recs[:3]
                products_for_names = InventoryManager.get_all_products()
                names = []
                for r in top_needs:
                    match = products_for_names[products_for_names['product_id'] == r['product_id']]
                    if not match.empty:
                        names.append(match['product_name'].values[0])
                if names:
                    st.info(f"🤖 **AI Insight:** {', '.join(names)} — trending low, AI recommends restocking soon (see 🔮 Forecasting for details).")
        except Exception:
            pass

        tab1, tab2 = st.tabs([t("tab_record_sale"), t("tab_sales_history")])

        with tab1:
            st.markdown('<div class="section-title">Record New Sale</div>', unsafe_allow_html=True)
            try:
                products = InventoryManager.get_all_products()
                if not products.empty:
                    with st.form("sales_form"):
                        product_id = st.selectbox(t("field_select_product"),
                            options=products['product_id'],
                            format_func=lambda x: products[products['product_id']==x]['product_name'].values[0])

                        quantity = st.number_input(t("field_quantity_sold"), min_value=1, step=1)
                        discount = st.slider(t("field_discount_percent"), 0, 50, 0)

                        if st.form_submit_button(t("btn_record_sale")):
                            if SalesManager.record_sale(product_id, quantity, discount):
                                sold_product = InventoryManager.get_product_by_id(product_id)
                                if sold_product:
                                    base_amount = float(sold_product[4]) * quantity
                                    total_amount = base_amount - (base_amount * discount / 100)
                                    db.add_business_money(total_amount)
                                st.success(f"✅ Sale recorded! {quantity} units sold")
                                st.balloons()
                                st.rerun()
                            else:
                                st.error("❌ Sale recording failed")
                else:
                    st.info("Add products to inventory first")
            except Exception as e:
                st.error(f"Error: {e}")

        with tab2:
            st.markdown('<div class="section-title">Sales History (Last 30 Days)</div>', unsafe_allow_html=True)
            try:
                sales = SalesManager.get_sales_data(days=30)
                if not sales.empty:
                    products = InventoryManager.get_all_products()
                    sales = sales.merge(products[['product_id', 'product_name']], on='product_id', how='left')
                    st.dataframe(
                        sales[['sale_id', 'product_name', 'quantity_sold', 'sale_price', 'discount_applied', 'total_amount', 'sale_date']],
                        use_container_width=True
                    )

                    st.markdown('<div class="section-title">📈 Daily Revenue</div>', unsafe_allow_html=True)
                    daily = sales.copy()
                    daily['sale_date'] = pd.to_datetime(daily['sale_date']).dt.date
                    daily_summary = daily.groupby('sale_date')['total_amount'].sum().reset_index()
                    fig = px.bar(
                        daily_summary, x='sale_date', y='total_amount',
                        color='total_amount', color_continuous_scale='Bluyl'
                    )
                    fig.update_layout(
                        template="plotly_dark",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        height=320, margin=dict(l=10, r=10, t=20, b=10),
                        xaxis_title="Date", yaxis_title="Revenue (₹)"
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    st.markdown('<div class="section-title">🏆 Units Sold by Product</div>', unsafe_allow_html=True)
                    product_summary = sales.groupby('product_name')['quantity_sold'].sum().reset_index().sort_values('quantity_sold', ascending=False)
                    fig2 = px.bar(
                        product_summary, x='product_name', y='quantity_sold',
                        color='quantity_sold', color_continuous_scale='Tealgrn'
                    )
                    fig2.update_layout(
                        template="plotly_dark",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        height=320, margin=dict(l=10, r=10, t=20, b=10),
                        xaxis_title="", yaxis_title="Units Sold"
                    )
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.info("No sales recorded yet")
            except Exception as e:
                st.error(f"Error: {e}")

elif page == "🧾 Billing":
    with st.container(key="billing_dashboard"):
        st.markdown(
            '<div class="dash-header"><div class="dash-header-icon">🧾</div>'
            f'<div class="dash-header-title">{t("billing_header")}</div></div>',
            unsafe_allow_html=True
        )

        recent_bills_kpi = BillingManager.get_recent_bills(limit=100)
        recent_returns_kpi = BillingManager.get_recent_returns(limit=100)
        bills_count = len(recent_bills_kpi)
        billing_revenue = sum(b['total_amount'] for b in recent_bills_kpi) if recent_bills_kpi else 0
        returns_count = len(recent_returns_kpi)
        total_refunded = sum(r['refund_amount'] for r in recent_returns_kpi) if recent_returns_kpi else 0

        billing_kpi_cards = [
            ("🧾", "#5b7bf7", "Total Bills", f"{bills_count}", "All time"),
            ("💰", "#2ecc91", "Billing Revenue", f"₹{billing_revenue:,.0f}", "All time"),
            ("↩️", "#f6a623", "Returns Processed", f"{returns_count}", "All time"),
            ("💸", "#ff5c6a", "Total Refunded", f"₹{total_refunded:,.0f}", "All time"),
        ]
        billing_cards_html = '<div class="kpi-row">'
        for icon, color, label, value, sub in billing_kpi_cards:
            billing_cards_html += (
                '<div class="kpi-card">'
                f'<div class="kpi-icon" style="background:{color}22; color:{color};">{icon}</div>'
                f'<div class="kpi-label">{label}</div>'
                f'<div class="kpi-value" style="color:{color};">{value}</div>'
                f'<div class="kpi-sub">{sub}</div>'
                '</div>'
            )
        billing_cards_html += '</div>'
        st.markdown(billing_cards_html, unsafe_allow_html=True)

        bill_tab1, bill_tab2, bill_tab3 = st.tabs(["🧾 New Bill", "↩️ Returns & Refunds", "📜 Bill History"])

        # ============================= NEW BILL (Fast Billing) =============================
        with bill_tab1:
            if 'billing_cart' not in st.session_state:
                st.session_state.billing_cart = []

            st.markdown('<div class="section-title">📷 Barcode / QR Scanner (experimental)</div>', unsafe_allow_html=True)
            st.caption("Scans a product's QR code (shows its Product ID) using your camera. Camera access may be blocked by some browsers/embeds — if so, just use the dropdown below instead.")
            with st.expander("Open Camera Scanner"):
                scanner_html = """
                <div id="reader" style="width: 280px;"></div>
                <div id="scan-result" style="margin-top:8px; font-weight:bold; font-family:sans-serif;"></div>
                <script src="https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js"></script>
                <script>
                function onScanSuccess(decodedText) {
                    document.getElementById('scan-result').innerText = "Scanned Product ID: " + decodedText + " (copy this into the box below)";
                }
                try {
                    var html5QrcodeScanner = new Html5QrcodeScanner("reader", { fps: 10, qrbox: 200 });
                    html5QrcodeScanner.render(onScanSuccess);
                } catch (e) {
                    document.getElementById('scan-result').innerText = "Camera not available in this browser/embed.";
                }
                </script>
                """
                components.html(scanner_html, height=340)

            st.markdown('<div class="section-title">🛒 Add Products to Cart</div>', unsafe_allow_html=True)
            try:
                products = InventoryManager.get_all_products()
            except Exception:
                products = pd.DataFrame()

            if not products.empty:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    scan_product_id = st.selectbox(
                        "Select Product (or scanned Product ID)",
                        options=products['product_id'],
                        format_func=lambda x: f"#{x} — {products[products['product_id']==x]['product_name'].values[0]}",
                        key="billing_product_select"
                    )
                with col2:
                    add_qty = st.number_input("Qty", min_value=1, value=1, step=1, key="billing_add_qty")
                with col3:
                    st.write("")
                    st.write("")
                    if st.button("➕ Add to Cart", use_container_width=True):
                        product = InventoryManager.get_product_by_id(scan_product_id)
                        if product:
                            st.session_state.billing_cart.append({
                                "product_id": scan_product_id,
                                "product_name": product[1],
                                "quantity": int(add_qty),
                                "unit_price": float(product[4])
                            })
                            st.rerun()

                if st.session_state.billing_cart:
                    cart_df = pd.DataFrame(st.session_state.billing_cart)
                    cart_df['line_total'] = cart_df['quantity'] * cart_df['unit_price']
                    st.dataframe(cart_df, use_container_width=True)

                    subtotal = float(cart_df['line_total'].sum())

                    col1, col2 = st.columns(2)
                    with col1:
                        gst_percent = st.selectbox("GST %", [0, 5, 12, 18, 28], index=1, key="billing_gst")
                    with col2:
                        payment_method = st.radio("Payment Method", ["Cash", "UPI", "Card", "Wallet"], horizontal=True, key="billing_payment")

                    customer_name = st.text_input("Customer Name (optional)", key="billing_customer_name")

                    gst_amount = subtotal * gst_percent / 100
                    total_amount = subtotal + gst_amount

                    m1, m2, m3 = st.columns(3)
                    m1.metric("Subtotal", f"₹{subtotal:,.2f}")
                    m2.metric(f"GST ({gst_percent}%)", f"₹{gst_amount:,.2f}")
                    m3.metric("Total", f"₹{total_amount:,.2f}")

                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button("💳 Checkout", use_container_width=True):
                            success, msg, bill_id = BillingManager.checkout(
                                st.session_state.billing_cart, payment_method, gst_percent, customer_name
                            )
                            if success:
                                st.session_state.last_bill_id = bill_id
                                st.session_state.billing_cart = []
                                st.success(f"✅ {msg}")
                                st.rerun()
                            else:
                                st.error(f"❌ {msg}")
                    with b2:
                        if st.button("🗑️ Clear Cart", use_container_width=True):
                            st.session_state.billing_cart = []
                            st.rerun()
                else:
                    st.info("Cart is empty — add products above to start a new bill.")
            else:
                st.info("Add products to inventory first.")

            # ---- Receipt / Invoice for the last completed bill ----
            if st.session_state.get('last_bill_id'):
                bill, items = BillingManager.get_bill(st.session_state.last_bill_id)
                if bill:
                    st.markdown("---")
                    st.markdown(f'<div class="section-title">🧾 GST Invoice — Bill #{bill["bill_id"]}</div>', unsafe_allow_html=True)

                    inv_df = pd.DataFrame(items)[['product_name', 'quantity', 'unit_price', 'line_total']]
                    st.dataframe(inv_df, use_container_width=True)

                    ic1, ic2, ic3, ic4 = st.columns(4)
                    ic1.metric("Subtotal", f"₹{bill['subtotal']:,.2f}")
                    ic2.metric(f"GST ({bill['gst_percent']}%)", f"₹{bill['gst_amount']:,.2f}")
                    ic3.metric("Total", f"₹{bill['total_amount']:,.2f}")
                    ic4.metric("Payment", bill['payment_method'])

                    receipt_text = BillingManager.generate_thermal_receipt_text(bill, items)

                    rc1, rc2 = st.columns(2)
                    with rc1:
                        st.markdown('<div class="section-title">🧾 Thermal Receipt</div>', unsafe_allow_html=True)
                        escaped_receipt = html_lib.escape(receipt_text)
                        receipt_print_html = (
                            f'<pre style="font-family: monospace; font-size:13px; '
                            f'background:#fff; color:#000; padding:10px; border-radius:6px;">{escaped_receipt}</pre>'
                            f'<button onclick="window.print()" style="padding:8px 16px; border-radius:6px; '
                            f'border:none; background:#d63447; color:white; cursor:pointer;">🖨️ Print Receipt</button>'
                        )
                        components.html(receipt_print_html, height=480, scrolling=True)

                        st.download_button(
                            "⬇️ Download Receipt (.txt)",
                            data=receipt_text,
                            file_name=f"receipt_bill_{bill['bill_id']}.txt",
                            use_container_width=True
                        )

                        mailto_body = urllib.parse.quote(receipt_text)
                        mailto_link = f"mailto:?subject=MVA%20Mart%20Receipt%20-%20Bill%20{bill['bill_id']}&body={mailto_body}"
                        st.markdown(f"📧 [Email this Receipt]({mailto_link})")

                    with rc2:
                        st.markdown('<div class="section-title">📱 QR Code</div>', unsafe_allow_html=True)
                        if bill['payment_method'] == 'UPI':
                            qr_data = BillingManager.build_upi_qr_string(
                                "merchant@upi", "MVA Mart", bill['total_amount'], bill['bill_id']
                            )
                            qr_caption = "Scan with any UPI app to pay"
                        else:
                            qr_data = f"MVA Mart Bill #{bill['bill_id']} - Total Rs{bill['total_amount']:.2f}"
                            qr_caption = "Bill reference QR code"

                        qr_bytes = BillingManager.generate_qr_code_bytes(qr_data)
                        if qr_bytes:
                            st.image(qr_bytes, caption=qr_caption, width=200)
                        else:
                            st.info("Install the `qrcode` package (see requirements.txt) to enable QR codes.")

                    if st.button("✖️ Close Invoice"):
                        st.session_state.last_bill_id = None
                        st.rerun()

        # ============================= RETURNS & REFUNDS =============================
        with bill_tab2:
            st.markdown('<div class="section-title">↩️ Returns & Refunds</div>', unsafe_allow_html=True)
            bills_for_return = BillingManager.get_recent_bills(limit=50)

            if bills_for_return:
                bill_options = {
                    b['bill_id']: f"Bill #{b['bill_id']} — ₹{b['total_amount']:.2f} ({b['created_at']})"
                    for b in bills_for_return
                }
                selected_bill_id = st.selectbox(
                    "Select Bill", options=list(bill_options.keys()),
                    format_func=lambda x: bill_options[x], key="return_bill_select"
                )
                _, return_items = BillingManager.get_bill(selected_bill_id)

                returnable_items = [i for i in return_items if i['quantity'] - i['returned_quantity'] > 0]

                if returnable_items:
                    for item in returnable_items:
                        remaining = item['quantity'] - item['returned_quantity']
                        with st.container(border=True):
                            st.write(f"**{item['product_name']}** — sold: {item['quantity']}, "
                                     f"already returned: {item['returned_quantity']}, returnable: {remaining}")
                            rc1, rc2, rc3 = st.columns([1, 2, 1])
                            with rc1:
                                return_qty = st.number_input(
                                    "Qty to return", min_value=1, max_value=int(remaining), value=1,
                                    key=f"return_qty_{item['bill_item_id']}"
                                )
                            with rc2:
                                return_reason = st.text_input(
                                    "Reason (optional)", key=f"return_reason_{item['bill_item_id']}"
                                )
                            with rc3:
                                st.write("")
                                st.write("")
                                if st.button("↩️ Process Return", key=f"return_btn_{item['bill_item_id']}", use_container_width=True):
                                    success, msg = BillingManager.process_return(item['bill_item_id'], return_qty, return_reason)
                                    if success:
                                        st.success(f"✅ {msg}")
                                    else:
                                        st.error(f"❌ {msg}")
                                    st.rerun()
                else:
                    st.info("No returnable items on this bill (everything already returned or bill is empty).")
            else:
                st.info("No bills yet — create one in the 'New Bill' tab first.")

        # ============================= BILL HISTORY =============================
        with bill_tab3:
            st.markdown('<div class="section-title">📜 Bill History</div>', unsafe_allow_html=True)
            all_bills = BillingManager.get_recent_bills(limit=100)
            if all_bills:
                bills_df = pd.DataFrame([dict(b) for b in all_bills])
                st.dataframe(bills_df, use_container_width=True)
            else:
                st.info("No bills yet.")

elif page == "👥 Employees":
    with st.container(key="employees_dashboard"):
        st.markdown(
            '<div class="dash-header"><div class="dash-header-icon">👥</div>'
            f'<div class="dash-header-title">{t("employees_header")}</div></div>',
            unsafe_allow_html=True
        )

        all_employees = EmployeeManager.get_all_employees()
        today_str = datetime.now().strftime('%Y-%m-%d')
        today_attendance = EmployeeManager.get_attendance(attendance_date=today_str)
        present_today = len([a for a in today_attendance if a['status'] == 'Present'])
        pending_salaries = EmployeeManager.get_pending_salaries()
        monthly_salary_cost = sum(e['monthly_salary'] for e in all_employees) if all_employees else 0

        emp_kpi_cards = [
            ("👥", "#5b7bf7", "Total Employees", f"{len(all_employees)}", "Active staff"),
            ("✅", "#2ecc91", "Present Today", f"{present_today}", today_str),
            ("💸", "#f6a623", "Pending Salaries", f"{len(pending_salaries)}", "Awaiting payment"),
            ("💼", "#ff5c6a", "Monthly Salary Cost", f"₹{monthly_salary_cost:,.0f}", "Across all employees"),
        ]
        emp_cards_html = '<div class="kpi-row">'
        for icon, color, label, value, sub in emp_kpi_cards:
            emp_cards_html += (
                '<div class="kpi-card">'
                f'<div class="kpi-icon" style="background:{color}22; color:{color};">{icon}</div>'
                f'<div class="kpi-label">{label}</div>'
                f'<div class="kpi-value" style="color:{color};">{value}</div>'
                f'<div class="kpi-sub">{sub}</div>'
                '</div>'
            )
        emp_cards_html += '</div>'
        st.markdown(emp_cards_html, unsafe_allow_html=True)

        emp_tab1, emp_tab2, emp_tab3, emp_tab4 = st.tabs(["👥 Directory", "🕒 Attendance", "💰 Salary", "📅 Shifts"])

        # ============================= DIRECTORY =============================
        with emp_tab1:
            st.markdown('<div class="section-title">➕ Add Employee</div>', unsafe_allow_html=True)
            with st.form("add_employee_form"):
                c1, c2 = st.columns(2)
                with c1:
                    emp_name = st.text_input("Full Name")
                    emp_role = st.selectbox("Role", ROLES)
                    emp_phone = st.text_input("Phone")
                with c2:
                    emp_email = st.text_input("Email")
                    emp_salary = st.number_input("Monthly Salary (₹)", min_value=0.0, step=500.0)
                    emp_join_date = st.date_input("Join Date", value=datetime.now())
                emp_username = st.text_input("Linked Login Username (optional)")

                if st.form_submit_button("✅ Add Employee"):
                    if emp_name and emp_role:
                        success, msg = EmployeeManager.add_employee(
                            emp_name, emp_role, emp_phone, emp_email,
                            emp_salary, emp_join_date.strftime('%Y-%m-%d'), emp_username
                        )
                        if success:
                            st.success(f"✅ {msg}")
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")
                    else:
                        st.error("❌ Name and Role are required.")

            st.markdown('<div class="section-title">👥 Employee Directory</div>', unsafe_allow_html=True)
            if all_employees:
                emp_df = pd.DataFrame([dict(e) for e in all_employees])
                st.dataframe(emp_df, use_container_width=True)
            else:
                st.info("No employees added yet.")

        # ============================= ATTENDANCE =============================
        with emp_tab2:
            st.markdown('<div class="section-title">🕒 Mark Attendance</div>', unsafe_allow_html=True)
            if all_employees:
                emp_options = {e['employee_id']: f"{e['full_name']} ({e['role']})" for e in all_employees}

                with st.form("attendance_form"):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        att_employee_id = st.selectbox("Employee", options=list(emp_options.keys()), format_func=lambda x: emp_options[x])
                        att_date = st.date_input("Date", value=datetime.now())
                    with c2:
                        att_status = st.selectbox("Status", ATTENDANCE_STATUSES)
                        att_check_in = st.text_input("Check-in Time (e.g. 09:00)")
                    with c3:
                        att_check_out = st.text_input("Check-out Time (e.g. 18:00)")

                    if st.form_submit_button("✅ Mark Attendance"):
                        success, msg = EmployeeManager.mark_attendance(
                            att_employee_id, att_date.strftime('%Y-%m-%d'), att_status, att_check_in, att_check_out
                        )
                        if success:
                            st.success(f"✅ {msg}")
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")

                st.markdown(f'<div class="section-title">📋 Attendance for {today_str}</div>', unsafe_allow_html=True)
                if today_attendance:
                    att_df = pd.DataFrame([dict(a) for a in today_attendance])
                    st.dataframe(att_df, use_container_width=True)
                else:
                    st.info("No attendance marked for today yet.")

                st.markdown('<div class="section-title">📊 Attendance Summary (last 30 days)</div>', unsafe_allow_html=True)
                summary_employee_id = st.selectbox("Select employee for summary", options=list(emp_options.keys()), format_func=lambda x: emp_options[x], key="att_summary_emp")
                summary = EmployeeManager.get_attendance_summary(summary_employee_id, days=30)
                sc1, sc2, sc3, sc4 = st.columns(4)
                sc1.metric("Present", summary.get("Present", 0))
                sc2.metric("Absent", summary.get("Absent", 0))
                sc3.metric("Half Day", summary.get("Half Day", 0))
                sc4.metric("Leave", summary.get("Leave", 0))
            else:
                st.info("Add employees first in the Directory tab.")

        # ============================= SALARY =============================
        with emp_tab3:
            st.markdown('<div class="section-title">💰 Record Salary Payment</div>', unsafe_allow_html=True)
            if all_employees:
                emp_options_salary = {e['employee_id']: f"{e['full_name']} ({e['role']}) — ₹{e['monthly_salary']:,.0f}/mo" for e in all_employees}

                with st.form("salary_form"):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        sal_employee_id = st.selectbox("Employee", options=list(emp_options_salary.keys()), format_func=lambda x: emp_options_salary[x])
                        default_amount = next((e['monthly_salary'] for e in all_employees if e['employee_id'] == sal_employee_id), 0.0)
                    with c2:
                        sal_amount = st.number_input("Amount (₹)", min_value=0.0, value=float(default_amount), step=500.0)
                        sal_month = st.selectbox("Month", list(range(1, 13)), index=datetime.now().month - 1)
                    with c3:
                        sal_year = st.number_input("Year", min_value=2020, max_value=2100, value=datetime.now().year, step=1)
                        sal_status = st.selectbox("Status", ["Pending", "Paid"])

                    if st.form_submit_button("✅ Record Salary"):
                        success, msg = EmployeeManager.record_salary_payment(sal_employee_id, sal_amount, sal_month, sal_year, sal_status)
                        if success:
                            st.success(f"✅ {msg}")
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")

                st.markdown('<div class="section-title">⏳ Pending Salary Payments</div>', unsafe_allow_html=True)
                if pending_salaries:
                    for p in pending_salaries:
                        emp = EmployeeManager.get_employee_by_id(p['employee_id'])
                        emp_name = emp['full_name'] if emp else f"Employee #{p['employee_id']}"
                        with st.container(border=True):
                            c1, c2 = st.columns([3, 1])
                            with c1:
                                st.write(f"**{emp_name}** — ₹{p['amount']:,.2f} for {p['pay_month']}/{p['pay_year']}")
                            with c2:
                                if st.button("💳 Mark Paid", key=f"pay_{p['payment_id']}", use_container_width=True):
                                    success, msg = EmployeeManager.mark_salary_paid(p['payment_id'])
                                    if success:
                                        st.success(msg)
                                        st.rerun()
                else:
                    st.info("No pending salary payments.")

                st.markdown('<div class="section-title">📜 Salary History</div>', unsafe_allow_html=True)
                salary_history = EmployeeManager.get_salary_history(limit=50)
                if salary_history:
                    hist_df = pd.DataFrame([dict(s) for s in salary_history])
                    st.dataframe(hist_df, use_container_width=True)
                else:
                    st.info("No salary records yet.")
            else:
                st.info("Add employees first in the Directory tab.")

        # ============================= SHIFTS =============================
        with emp_tab4:
            st.markdown('<div class="section-title">📅 Assign Shift</div>', unsafe_allow_html=True)
            if all_employees:
                emp_options_shift = {e['employee_id']: f"{e['full_name']} ({e['role']})" for e in all_employees}

                with st.form("shift_form"):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        shift_employee_id = st.selectbox("Employee", options=list(emp_options_shift.keys()), format_func=lambda x: emp_options_shift[x])
                        shift_date = st.date_input("Shift Date", value=datetime.now())
                    with c2:
                        shift_name = st.selectbox("Shift", SHIFT_NAMES)
                        shift_start = st.text_input("Start Time (e.g. 09:00)")
                    with c3:
                        shift_end = st.text_input("End Time (e.g. 17:00)")

                    if st.form_submit_button("✅ Assign Shift"):
                        success, msg = EmployeeManager.assign_shift(
                            shift_employee_id, shift_date.strftime('%Y-%m-%d'), shift_name, shift_start, shift_end
                        )
                        if success:
                            st.success(f"✅ {msg}")
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")

                st.markdown('<div class="section-title">📋 Upcoming Shifts</div>', unsafe_allow_html=True)
                upcoming_shifts = EmployeeManager.get_shifts()
                if upcoming_shifts:
                    shifts_df = pd.DataFrame([dict(s) for s in upcoming_shifts])
                    st.dataframe(shifts_df, use_container_width=True)
                else:
                    st.info("No shifts scheduled yet.")
            else:
                st.info("Add employees first in the Directory tab.")

elif page == "🤖 AI Customers":
    with st.container(key="ai_customers_dashboard"):
        st.markdown(
            '<div class="dash-header"><div class="dash-header-icon">🤖</div>'
            f'<div class="dash-header-title">{t("ai_customers_header")}</div></div>',
            unsafe_allow_html=True
        )
        st.caption("💡 Simulated customer messages for demo purposes — new messages accumulate automatically over time. Click 'Check for New Messages' or navigate the app to see the latest.")

        if st.button("🔄 Check for New Messages", use_container_width=False):
            st.rerun()

        stats = AICustomerManager.get_order_stats()

        ai_cust_kpi_cards = [
            ("📨", "#f6a623", t("kpi_pending_messages"), f"{stats['pending']}", t("sub_awaiting_response")),
            ("✅", "#2ecc91", t("kpi_fulfilled"), f"{stats['fulfilled']}", t("sub_orders_completed")),
            ("❌", "#ff5c6a", t("kpi_rejected"), f"{stats['rejected']}", t("sub_orders_declined")),
            ("🧾", "#5b7bf7", t("kpi_total_messages"), f"{stats['pending'] + stats['fulfilled'] + stats['rejected']}", t("sub_all_time")),
        ]
        ai_cust_cards_html = '<div class="kpi-row">'
        for icon, color, label, value, sub in ai_cust_kpi_cards:
            ai_cust_cards_html += (
                '<div class="kpi-card">'
                f'<div class="kpi-icon" style="background:{color}22; color:{color};">{icon}</div>'
                f'<div class="kpi-label">{label}</div>'
                f'<div class="kpi-value" style="color:{color};">{value}</div>'
                f'<div class="kpi-sub">{sub}</div>'
                '</div>'
            )
        ai_cust_cards_html += '</div>'
        st.markdown(ai_cust_cards_html, unsafe_allow_html=True)

        tab1, tab2 = st.tabs([t("tab_pending_messages"), t("tab_order_history")])

        with tab1:
            st.markdown('<div class="section-title">Pending Customer Messages</div>', unsafe_allow_html=True)
            pending_orders = AICustomerManager.get_orders(status="pending")

            if pending_orders:
                for order in pending_orders:
                    with st.container(border=True):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**👤 {order['customer_name']}**")
                            st.write(f"💬 {order['message']}")
                            st.caption(f"Wants: {order['quantity']} × {order['product_name']}  |  {order['created_at']}")
                        with col2:
                            fulfill_clicked = st.button(t("btn_fulfill"), key=f"fulfill_{order['order_id']}", use_container_width=True)
                            reject_clicked = st.button(t("btn_reject"), key=f"reject_{order['order_id']}", use_container_width=True)

                        if fulfill_clicked:
                            success, msg = AICustomerManager.fulfill_order(order['order_id'])
                            if success:
                                st.success(msg)
                            else:
                                st.error(msg)
                            st.rerun()

                        if reject_clicked:
                            success, msg = AICustomerManager.reject_order(order['order_id'])
                            st.info(msg)
                            st.rerun()
            else:
                st.info("No pending messages. Click 'Simulate New Customer Message' above to generate one.")

        with tab2:
            st.markdown('<div class="section-title">Order History</div>', unsafe_allow_html=True)
            all_orders = AICustomerManager.get_orders()
            if all_orders:
                df = pd.DataFrame([dict(o) for o in all_orders])
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No customer messages yet.")

elif page == "📈 Analytics":
    with st.container(key="analytics_dashboard"):
        st.markdown(
            '<div class="dash-header"><div class="dash-header-icon">📈</div>'
            f'<div class="dash-header-title">{t("analytics_header")}</div></div>',
            unsafe_allow_html=True
        )

        revenue = SalesManager.calculate_total_revenue(30)
        profit = SalesManager.calculate_profit(30)
        margin = SalesManager.calculate_profit_margin(30)
        inv_value = InventoryManager.calculate_inventory_value()

        analytics_kpi_cards = [
            ("💰", "#2ecc91", t("kpi_30d_revenue"), f"₹{revenue:,.0f}", t("sub_last_30_days")),
            ("📈", "#22c1c3", t("kpi_30d_profit"), f"₹{profit:,.0f}", t("sub_last_30_days")),
            ("📊", "#f6a623", t("kpi_profit_margin"), f"{margin:.1f}%", t("sub_revenue_based")),
            ("💼", "#5b7bf7", t("kpi_inventory_value"), f"₹{inv_value:,.0f}", t("sub_stock_cost_price")),
        ]
        analytics_cards_html = '<div class="kpi-row">'
        for icon, color, label, value, sub in analytics_kpi_cards:
            analytics_cards_html += (
                '<div class="kpi-card">'
                f'<div class="kpi-icon" style="background:{color}22; color:{color};">{icon}</div>'
                f'<div class="kpi-label">{label}</div>'
                f'<div class="kpi-value" style="color:{color};">{value}</div>'
                f'<div class="kpi-sub">{sub}</div>'
                '</div>'
            )
        analytics_cards_html += '</div>'
        st.markdown(analytics_cards_html, unsafe_allow_html=True)

        tab1, tab2, tab3 = st.tabs([t("tab_overview"), t("tab_category_analysis"), t("tab_top_products")])

        with tab1:
            st.markdown('<div class="section-title">Revenue vs Profit (Last 30 Days)</div>', unsafe_allow_html=True)
            try:
                cost = max(revenue - profit, 0)
                overview_df = pd.DataFrame({
                    "Metric": ["Revenue", "Profit", "Cost"],
                    "Amount": [revenue, profit, cost]
                })
                fig = px.bar(
                    overview_df, x='Metric', y='Amount', color='Metric',
                    color_discrete_map={"Revenue": "#5b7bf7", "Profit": "#2ecc91", "Cost": "#ff5c6a"}
                )
                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    height=340, margin=dict(l=10, r=10, t=20, b=10),
                    xaxis_title="", yaxis_title="₹", showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error loading chart: {e}")

        with tab2:
            st.markdown('<div class="section-title">Category Performance</div>', unsafe_allow_html=True)
            try:
                category_data = Analytics.get_category_performance()
                if category_data:
                    df = pd.DataFrame(category_data)

                    col1, col2 = st.columns(2)

                    with col1:
                        fig = px.bar(
                            df, x='category', y='revenue',
                            color='revenue', color_continuous_scale='Bluyl'
                        )
                        fig.update_layout(
                            template="plotly_dark",
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            height=320, margin=dict(l=10, r=10, t=20, b=10),
                            xaxis_title="", yaxis_title="Revenue (₹)"
                        )
                        st.plotly_chart(fig, use_container_width=True)

                    with col2:
                        fig = px.bar(
                            df, x='category', y='profit',
                            color='profit', color_continuous_scale='Tealgrn'
                        )
                        fig.update_layout(
                            template="plotly_dark",
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            height=320, margin=dict(l=10, r=10, t=20, b=10),
                            xaxis_title="", yaxis_title="Profit (₹)"
                        )
                        st.plotly_chart(fig, use_container_width=True)

                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No category data yet.")
            except Exception as e:
                st.error(f"Error: {e}")

        with tab3:
            st.markdown('<div class="section-title">Top Performing Products</div>', unsafe_allow_html=True)
            metric = st.radio(t("field_rank_by"), ["Profit", "Revenue", "Sales Volume"], horizontal=True)

            try:
                top_products = Analytics.get_top_products(
                    metric={'Profit': 'profit', 'Revenue': 'revenue', 'Sales Volume': 'sales_volume'}[metric],
                    limit=10
                )
                if top_products:
                    df = pd.DataFrame(top_products)
                    fig = px.bar(
                        df, x='product_name', y='value',
                        color='value', color_continuous_scale='Purpor'
                    )
                    fig.update_layout(
                        template="plotly_dark",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        height=340, margin=dict(l=10, r=10, t=20, b=10),
                        xaxis_title="", yaxis_title=f"{metric}"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No sales yet.")
            except Exception as e:
                st.error(f"Error: {e}")

elif page == "🔮 Forecasting":
    with st.container(key="forecasting_dashboard"):
        st.markdown(
            '<div class="dash-header"><div class="dash-header-icon">🔮</div>'
            f'<div class="dash-header-title">{t("forecasting_header")}</div></div>',
            unsafe_allow_html=True
        )

        try:
            fc_recommendations = DemandForecaster.get_all_recommendations()
        except Exception:
            fc_recommendations = []

        fc_rec_count = len(fc_recommendations)
        fc_total_units = sum(r.get('recommended_quantity', 0) for r in fc_recommendations)
        try:
            fc_product_count = len(InventoryManager.get_all_products())
        except Exception:
            fc_product_count = 0

        fc_kpi_cards = [
            ("🏷️", "#5b7bf7", t("kpi_products_tracked"), f"{fc_product_count}", t("sub_unique_skus")),
            ("📦", "#f6a623", t("kpi_reorder_alerts"), f"{fc_rec_count}", t("sub_predicted_by_ai")),
            ("📈", "#2ecc91", t("kpi_units_to_reorder"), f"{fc_total_units:,}", t("sub_across_alerts")),
        ]
        fc_cards_html = '<div class="kpi-row">'
        for icon, color, label, value, sub in fc_kpi_cards:
            fc_cards_html += (
                '<div class="kpi-card">'
                f'<div class="kpi-icon" style="background:{color}22; color:{color};">{icon}</div>'
                f'<div class="kpi-label">{label}</div>'
                f'<div class="kpi-value" style="color:{color};">{value}</div>'
                f'<div class="kpi-sub">{sub}</div>'
                '</div>'
            )
        fc_cards_html += '</div>'
        st.markdown(fc_cards_html, unsafe_allow_html=True)

        tab1, tab2 = st.tabs([t("tab_forecast"), t("tab_recommendations")])

        with tab1:
            st.markdown('<div class="section-title">30-Day Demand Forecast</div>', unsafe_allow_html=True)
            try:
                products = InventoryManager.get_all_products()
                if not products.empty:
                    product_id = st.selectbox(t("field_select_product"),
                        options=products['product_id'],
                        format_func=lambda x: products[products['product_id']==x]['product_name'].values[0])

                    forecast = DemandForecaster.forecast_demand(product_id, days=30)
                    if forecast:
                        df = pd.DataFrame(forecast)
                        df['date'] = pd.to_datetime(df['date'])

                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=df['date'], y=df['forecasted_quantity'],
                            fill='tozeroy', name='Forecast',
                            line=dict(color='#5b7bf7', width=3),
                            fillcolor='rgba(91,123,247,0.25)'
                        ))
                        fig.add_trace(go.Scatter(
                            x=df['date'], y=df['upper_bound'],
                            fill=None, name='Upper Bound', line=dict(width=0),
                            showlegend=False
                        ))
                        fig.add_trace(go.Scatter(
                            x=df['date'], y=df['lower_bound'],
                            fill='tonexty', name='Lower Bound', line=dict(width=0),
                            fillcolor='rgba(91,123,247,0.1)',
                            showlegend=False
                        ))

                        fig.update_layout(
                            template="plotly_dark",
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            xaxis_title="Date",
                            yaxis_title="Quantity",
                            hovermode='x unified',
                            height=380,
                            margin=dict(l=10, r=10, t=20, b=10)
                        )
                        st.plotly_chart(fig, use_container_width=True)

                        st.dataframe(df, use_container_width=True)
                else:
                    st.info("Add products to inventory first.")
            except Exception as e:
                st.error(f"Error: {e}")

        with tab2:
            st.markdown('<div class="section-title">Purchase Recommendations</div>', unsafe_allow_html=True)
            try:
                if fc_recommendations:
                    df = pd.DataFrame(fc_recommendations)

                    for _, row in df.iterrows():
                        with st.container(border=True):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.write(f"**Product ID:** {row['product_id']}")
                            with col2:
                                st.write(f"**Current Stock:** {row['current_stock']}")
                            with col3:
                                st.write(f"**30-Day Demand:** {row['forecasted_30day_demand']:.0f}")

                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Recommended Qty", f"{int(row['recommended_quantity'])} units")
                            with col2:
                                st.info(row['status'])
                else:
                    st.info("No reorder recommendations at this time")
            except Exception as e:
                st.error(f"Error: {e}")

elif page == "⚠️ Alerts":
    try:
        alerts = Analytics.get_alerts()

        with st.container(key="alerts_dashboard"):
            st.markdown(
                '<div class="dash-header"><div class="dash-header-icon">⚠️</div>'
                f'<div class="dash-header-title">{t("alerts_header")}</div></div>',
                unsafe_allow_html=True
            )

            critical_count = len([a for a in alerts if a['severity'] == 'critical']) if alerts else 0
            warning_count = len([a for a in alerts if a['severity'] == 'warning']) if alerts else 0
            info_count = len([a for a in alerts if a['severity'] == 'info']) if alerts else 0

            try:
                alerts_ai_count = len(DemandForecaster.get_all_recommendations())
            except Exception:
                alerts_ai_count = 0

            alert_kpi_cards = [
                ("🔴", "#ff5c6a", t("kpi_critical"), f"{critical_count}", t("sub_immediate_action")),
                ("🟠", "#f6a623", t("kpi_warning"), f"{warning_count}", t("sub_keep_eye")),
                ("🔵", "#5b7bf7", t("kpi_info"), f"{info_count}", t("sub_for_awareness")),
                ("📋", "#2ecc91", t("kpi_total_alerts"), f"{len(alerts) if alerts else 0}", t("sub_all_active_alerts")),
                ("🤖", "#4cc9f0", t("kpi_ai_predicted"), f"{alerts_ai_count}", t("sub_forecasted_issues")),
            ]
            alert_cards_html = '<div class="kpi-row">'
            for icon, color, label, value, sub in alert_kpi_cards:
                alert_cards_html += (
                    '<div class="kpi-card">'
                    f'<div class="kpi-icon" style="background:{color}22; color:{color};">{icon}</div>'
                    f'<div class="kpi-label">{label}</div>'
                    f'<div class="kpi-value" style="color:{color};">{value}</div>'
                    f'<div class="kpi-sub">{sub}</div>'
                    '</div>'
                )
            alert_cards_html += '</div>'
            st.markdown(alert_cards_html, unsafe_allow_html=True)

            if alerts:
                st.markdown('<div class="section-title">Filter Alerts</div>', unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                with col1:
                    alert_type = st.multiselect("Alert Type",
                        options=list(set([a['type'] for a in alerts])),
                        default=list(set([a['type'] for a in alerts])))
                with col2:
                    severity = st.multiselect("Severity",
                        options=['critical', 'warning', 'info'],
                        default=['critical', 'warning'])

                filtered_alerts = [a for a in alerts if a['type'] in alert_type and a['severity'] in severity]

                st.markdown('<div class="section-title">Active Alerts</div>', unsafe_allow_html=True)
                for alert in filtered_alerts:
                    if alert['severity'] == 'critical':
                        st.markdown(f"<div class='alert-critical'>{alert['message']}</div>", unsafe_allow_html=True)
                    elif alert['severity'] == 'warning':
                        st.markdown(f"<div class='alert-warning'>{alert['message']}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='alert-info'>{alert['message']}</div>", unsafe_allow_html=True)
            else:
                st.success("✅ No active alerts! System is healthy.")

            # ---- AI Predictive Alerts (based on demand forecasting) ----
            st.markdown('<div class="section-title">🤖 AI Predictive Alerts</div>', unsafe_allow_html=True)
            try:
                ai_predictions = DemandForecaster.get_all_recommendations()
                if ai_predictions:
                    ai_products = InventoryManager.get_all_products()
                    for pred in ai_predictions:
                        match = ai_products[ai_products['product_id'] == pred['product_id']]
                        pname = match['product_name'].values[0] if not match.empty else f"Product #{pred['product_id']}"
                        shortfall_ratio = pred['recommended_quantity'] / max(pred['current_stock'], 1)
                        message = (f"🤖 <b>{pname}</b>: predicted demand exceeds stock — "
                                   f"AI recommends reordering {int(pred['recommended_quantity'])} units "
                                   f"(current stock: {pred['current_stock']}).")
                        if shortfall_ratio >= 1:
                            st.markdown(f"<div class='alert-critical'>{message}</div>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div class='alert-warning'>{message}</div>", unsafe_allow_html=True)
                else:
                    st.success("🤖 AI predicts no stockouts in the next 30 days.")
            except Exception as e:
                st.error(f"Error loading AI predictions: {e}")
    except Exception as e:
        st.error(f"Error: {e}")
elif page == "📥 Restock":
    with st.container(key="restock_dashboard"):
        st.markdown(
            '<div class="dash-header"><div class="dash-header-icon">📥</div>'
            f'<div class="dash-header-title">{t("restock_header")}</div></div>',
            unsafe_allow_html=True
        )

        try:
            purchase_stats = db.fetch_one(
                """SELECT COUNT(*) as cnt, COALESCE(SUM(quantity_purchased),0) as units,
                          COALESCE(SUM(total_cost),0) as cost
                   FROM purchases
                   WHERE purchase_date >= datetime('now', '-30 days')"""
            )
            restock_count = purchase_stats['cnt'] if purchase_stats else 0
            restock_units = purchase_stats['units'] if purchase_stats else 0
            restock_cost = purchase_stats['cost'] if purchase_stats else 0
        except Exception:
            restock_count = restock_units = restock_cost = 0

        try:
            low_stock_products = InventoryManager.get_all_products()
            low_stock_now = int((low_stock_products['stock'] <= low_stock_products['reorder_level']).sum()) if not low_stock_products.empty else 0
        except Exception:
            low_stock_now = 0

        restock_kpi_cards = [
            ("📥", "#5b7bf7", t("kpi_restocks_30d"), f"{restock_count}", t("sub_purchase_entries")),
            ("📦", "#2ecc91", t("kpi_units_added_30d"), f"{restock_units:,}", t("sub_total_quantity")),
            ("💸", "#f6a623", t("kpi_restock_cost_30d"), f"₹{restock_cost:,.0f}", t("sub_total_spend")),
            ("⚠️", "#ff5c6a", t("kpi_low_stock_now"), f"{low_stock_now}", t("sub_need_restocking")),
        ]
        restock_cards_html = '<div class="kpi-row">'
        for icon, color, label, value, sub in restock_kpi_cards:
            restock_cards_html += (
                '<div class="kpi-card">'
                f'<div class="kpi-icon" style="background:{color}22; color:{color};">{icon}</div>'
                f'<div class="kpi-label">{label}</div>'
                f'<div class="kpi-value" style="color:{color};">{value}</div>'
                f'<div class="kpi-sub">{sub}</div>'
                '</div>'
            )
        restock_cards_html += '</div>'
        st.markdown(restock_cards_html, unsafe_allow_html=True)

        st.markdown('<div class="section-title">Add Stock</div>', unsafe_allow_html=True)
        try:
            products = InventoryManager.get_all_products()
            if not products.empty:
                with st.form("restock_form"):
                    product_id = st.selectbox(t("field_select_product"),
                        options=products['product_id'],
                        format_func=lambda x: products[products['product_id']==x]['product_name'].values[0])

                    quantity = st.number_input("Quantity to Add", min_value=1, step=10)
                    cost_per_unit = st.number_input("Cost per Unit (₹)", min_value=0.0, step=10.0)

                    if st.form_submit_button(t("btn_restock")):
                        total_cost = quantity * cost_per_unit
                        available_funds = db.get_business_money()

                        if total_cost > available_funds:
                            st.error(t("not_enough_money").format(
                                available=f"{available_funds:,.2f}",
                                required=f"{total_cost:,.2f}"
                            ))
                        else:
                            InventoryManager.update_stock(product_id, quantity, 'restock')

                            # Record purchase
                            query = """
                                INSERT INTO purchases (product_id, quantity_purchased, cost_per_unit, total_cost)
                                VALUES (?, ?, ?, ?)
                            """
                            db.execute_query(query, (product_id, quantity, cost_per_unit, total_cost))

                            # Deduct the cost from available funds
                            db.deduct_business_money(total_cost)

                            st.success(f"✅ Restocked {quantity} units!")
                            st.rerun()
            else:
                st.info("Add products to inventory first")
        except Exception as e:
            st.error(f"Error: {e}")

elif page == "💰 Discounts":
    with st.container(key="discounts_dashboard"):
        st.markdown(
            '<div class="dash-header"><div class="dash-header-icon">💰</div>'
            f'<div class="dash-header-title">{t("discounts_header")}</div></div>',
            unsafe_allow_html=True
        )

        try:
            discount_recommendations = DiscountEngine.get_all_recommendations()
        except Exception:
            discount_recommendations = []

        disc_count = len(discount_recommendations)
        disc_avg = (sum(r.get('discount', 0) for r in discount_recommendations) / disc_count) if disc_count else 0
        disc_profit_recovery = sum(r.get('estimated_profit_recovery', 0) for r in discount_recommendations)
        disc_critical = len([r for r in discount_recommendations if r.get('urgency') == 'CRITICAL'])

        discount_kpi_cards = [
            ("💰", "#5b7bf7", t("kpi_recommendations"), f"{disc_count}", t("sub_ai_suggested")),
            ("📊", "#f6a623", t("kpi_avg_discount"), f"{disc_avg:.0f}%", t("sub_across_recs")),
            ("📈", "#2ecc91", t("kpi_est_profit_recovery"), f"₹{disc_profit_recovery:,.0f}", t("sub_if_all_applied")),
            ("🔴", "#ff5c6a", t("kpi_critical_urgency"), f"{disc_critical}", t("sub_act_soon")),
        ]
        discount_cards_html = '<div class="kpi-row">'
        for icon, color, label, value, sub in discount_kpi_cards:
            discount_cards_html += (
                '<div class="kpi-card">'
                f'<div class="kpi-icon" style="background:{color}22; color:{color};">{icon}</div>'
                f'<div class="kpi-label">{label}</div>'
                f'<div class="kpi-value" style="color:{color};">{value}</div>'
                f'<div class="kpi-sub">{sub}</div>'
                '</div>'
            )
        discount_cards_html += '</div>'
        st.markdown(discount_cards_html, unsafe_allow_html=True)

        tab1, tab2 = st.tabs([t("tab_discount_recs"), t("tab_apply_discount")])

        with tab1:
            st.markdown('<div class="section-title">AI Discount Recommendations</div>', unsafe_allow_html=True)
            try:
                if discount_recommendations:
                    for rec in discount_recommendations:
                        with st.container(border=True):
                            col1, col2, col3 = st.columns([2, 1, 1])

                            with col1:
                                st.write(f"**Product ID {rec['product_id']}**")
                                st.write(rec['recommendation'])

                            with col2:
                                urgency_color = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}
                                st.write(f"**{urgency_color.get(rec['urgency'], '')} {rec['urgency']}**")
                                st.write(f"**Discount:** {rec['discount']}%")

                            with col3:
                                st.metric("Price", f"₹{rec['discounted_price']:.2f}")
                                st.metric("Est. Profit", f"₹{rec['estimated_profit_recovery']:.0f}")

                    if st.button(t("btn_apply_all_recs")):
                        applied_count = 0
                        for rec in discount_recommendations:
                            try:
                                DiscountEngine.apply_discount_recommendation(
                                    rec['product_id'], rec['discount'], "AI recommended discount"
                                )
                                product = InventoryManager.get_product_by_id(rec['product_id'])
                                if product:
                                    DiscountLogManager.log_discount(
                                        product_id=rec['product_id'],
                                        product_name=product[1],
                                        discount_percent=rec['discount'],
                                        original_price=float(product[4]),
                                        discounted_price=rec['discounted_price'],
                                        reason="AI recommended discount"
                                    )
                                applied_count += 1
                            except Exception:
                                continue
                        st.success(f"✅ Applied {applied_count} recommended discount(s)! Check the Dashboard to see them.")
                        st.rerun()
                else:
                    st.info("No discount recommendations at this time")
            except Exception as e:
                st.error(f"Error: {e}")

        with tab2:
            st.markdown('<div class="section-title">Apply Custom Discount</div>', unsafe_allow_html=True)
            try:
                products = InventoryManager.get_all_products()
                if not products.empty:
                    with st.form("discount_form"):
                        product_id = st.selectbox(t("field_select_product"),
                            options=products['product_id'],
                            format_func=lambda x: products[products['product_id']==x]['product_name'].values[0])

                        discount = st.slider(t("field_discount_percent"), 0, 50, 10)
                        reason = st.text_input(t("field_reason"))

                        if st.form_submit_button(t("btn_apply_discount")):
                            DiscountEngine.apply_discount_recommendation(product_id, discount, reason)

                            product = InventoryManager.get_product_by_id(product_id)
                            if product:
                                original_price = float(product[4])
                                discounted_price = round(original_price * (1 - discount / 100), 2)
                                DiscountLogManager.log_discount(
                                    product_id=product_id,
                                    product_name=product[1],
                                    discount_percent=discount,
                                    original_price=original_price,
                                    discounted_price=discounted_price,
                                    reason=reason
                                )

                            st.success(f"✅ {discount}% discount applied! It will now show up on the Dashboard.")
                            st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

elif page == "📋 Reports":
    with st.container(key="reports_dashboard"):
        st.markdown(
            '<div class="dash-header"><div class="dash-header-icon">📋</div>'
            f'<div class="dash-header-title">{t("reports_header")}</div></div>',
            unsafe_allow_html=True
        )

        try:
            report_products = InventoryManager.get_all_products()
            report_product_count = len(report_products) if not report_products.empty else 0
        except Exception:
            report_product_count = 0

        try:
            report_sales = SalesManager.get_sales_data(days=30)
            report_sales_count = len(report_sales) if not report_sales.empty else 0
        except Exception:
            report_sales_count = 0

        report_kpi_cards = [
            ("🏷️", "#5b7bf7", t("kpi_total_products"), f"{report_product_count}", t("sub_across_products")),
            ("🧾", "#2ecc91", t("kpi_total_sales"), f"{report_sales_count}", t("sub_across_products")),
            ("📋", "#f6a623", "Report Types", "4", "Inventory, Sales, Financial, Complete"),
        ]
        report_cards_html = '<div class="kpi-row">'
        for icon, color, label, value, sub in report_kpi_cards:
            report_cards_html += (
                '<div class="kpi-card">'
                f'<div class="kpi-icon" style="background:{color}22; color:{color};">{icon}</div>'
                f'<div class="kpi-label">{label}</div>'
                f'<div class="kpi-value" style="color:{color};">{value}</div>'
                f'<div class="kpi-sub">{sub}</div>'
                '</div>'
            )
        report_cards_html += '</div>'
        st.markdown(report_cards_html, unsafe_allow_html=True)

        tab1, tab2 = st.tabs([t("tab_generate"), t("tab_view_reports")])

        with tab1:
            st.markdown('<div class="section-title">Generate Reports</div>', unsafe_allow_html=True)

            report_type = st.radio(t("field_report_type"),
                ["Inventory Report", "Sales Report", "Financial Report", "Complete Report"])

            days = st.slider(t("field_include_days"), 1, 365, 30)

            if st.button(t("btn_generate_report")):
                try:
                    if report_type == "Inventory Report":
                        products = InventoryManager.get_all_products()
                        csv = products.to_csv(index=False)
                        st.download_button(
                            label=t("btn_download_csv"),
                            data=csv,
                            file_name=f"inventory_report_{datetime.now().strftime('%Y%m%d')}.csv"
                        )

                    elif report_type == "Sales Report":
                        sales = SalesManager.get_sales_data(days)
                        csv = sales.to_csv(index=False)
                        st.download_button(
                            label=t("btn_download_csv"),
                            data=csv,
                            file_name=f"sales_report_{datetime.now().strftime('%Y%m%d')}.csv"
                        )

                    elif report_type == "Financial Report":
                        kpis = Analytics.get_kpis(days)
                        df = pd.DataFrame([kpis])
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label=t("btn_download_csv"),
                            data=csv,
                            file_name=f"financial_report_{datetime.now().strftime('%Y%m%d')}.csv"
                        )

                    st.success("✅ Report generated!")
                except Exception as e:
                    st.error(f"Error: {e}")

        with tab2:
            st.markdown('<div class="section-title">View Reports</div>', unsafe_allow_html=True)
            st.info("📌 Reports are generated on demand from the Generate tab")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: gray; font-size: 12px;'>
    🏪 AI-Driven Retail Intelligence Dashboard | HCL Jigsaw Innovation Challenge<br>
    Built with ❤️ using Streamlit & Python
    </div>
""", unsafe_allow_html=True)
