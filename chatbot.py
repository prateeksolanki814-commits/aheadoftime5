"""AI Assistant Chatbot Module - powered by Google Gemini.

This gives you a REAL, open-ended AI chat (like ChatGPT/Gemini) that can
answer literally anything about MVA Mart -- not just a fixed list of
topics -- by calling Google's Gemini API with a detailed description of
the whole project as context.

SETUP REQUIRED (one-time):
1. Get a free API key from https://aistudio.google.com/apikey
2. Add it as a Streamlit secret named GEMINI_API_KEY:
   - Locally: create a file .streamlit/secrets.toml with:
       GEMINI_API_KEY = "your-key-here"
   - On Streamlit Cloud: go to your app -> Settings -> Secrets, and add:
       GEMINI_API_KEY = "your-key-here"

If the key isn't set, or if the Gemini API is ever briefly unreachable,
this module automatically falls back to a built-in keyword-based
knowledge base, so the chatbot never fully breaks or crashes the app.
"""

import logging
import requests
import streamlit as st

logger = logging.getLogger(__name__)

# Primary model, with an automatic fallback if it's ever deprecated/renamed.
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_FALLBACK_MODEL = "gemini-flash-latest"  # auto-updating alias
GEMINI_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

# Context given to Gemini so it deeply understands this specific project.
PROJECT_CONTEXT = """You are the AI Assistant embedded inside "MVA Mart", an AI-driven \
supermarket management Streamlit app. Answer questions about how to use THIS specific \
app, in a friendly, concise, ChatGPT-like way. Use the details below. If asked something \
outside the app, you can still answer briefly and helpfully like a normal AI assistant.

=== MVA MART FEATURES ===
- Login/Register: Sign In / Sign Up tabs on the login screen. Roles are staff or admin \
(currently informational only, no access restrictions enforced). No password recovery yet.
- Top bar (every page): Language switcher (English/Hindi, translates the whole UI), a \
Funds widget (view/edit total available money anytime), and this AI Assistant chat.
- 📊 Dashboard: KPI cards for Inventory Value, Revenue, Profit, Profit Margin, Low Stock, \
Near Expiry, AI Reorder Needed, Discounts Applied. Charts: Sales Trend, Stock Levels, \
Revenue by Category, Profit by Product, Top Products by Revenue, and a live feed of \
Recently Applied Discounts.
- 📦 Inventory: View tab (product table, Stock by Category chart, AI Restock \
Recommendations table), Add Product tab (name, category, cost price, selling price, \
initial stock, reorder level, expiry date -- costs money from Funds), Update tab (edit \
stock/prices/expiry), Search tab (by name or category).
- 🛒 Sales: Record Sale tab (pick product + quantity + optional discount %, adds revenue \
to Funds), Sales History tab (past sales, Daily Revenue chart, Units Sold by Product \
chart), plus an AI Insight callout about trending-low products.
- 🤖 AI Customers: simulated customer messages requesting to buy products, arriving \
automatically roughly every 30 seconds as the app is used. Staff can Fulfill (records a \
real sale, adds revenue) or Reject each message. This is a demo simulator, not real \
customers.
- 💰 Discounts: AI Recommendations tab (suggested discounts with urgency levels \
Critical/High/Medium/Low, plus an Apply All button), Apply Discount tab (custom % on any \
product). Every discount applied is logged and shown on the Dashboard.
- 🔮 Forecasting: uses a scikit-learn Linear Regression model with weekly seasonality, \
trained on real sales history, to predict 30-day demand per product with a confidence \
band, plus purchase/reorder recommendations.
- ⚠️ Alerts: Critical/Warning/Info alerts for low stock and expiring items (with filters), \
plus a separate AI Predictive Alerts section from the forecasting model.
- 📥 Restock: buy more stock for a product (checks Funds first, blocks if insufficient). \
KPIs: Restocks (30d), Units Added (30d), Restock Cost (30d), Low Stock Now.
- 📈 Analytics: Overview (Revenue vs Profit vs Cost), Category Analysis (revenue/profit by \
category), Top Products (rank by Profit/Revenue/Sales Volume).
- 📋 Reports: generate and download CSV reports -- Inventory, Sales, or Financial.
- Funds: buying stock (Add Product/Restock) deducts from Funds and is blocked if \
insufficient; selling (Sales/AI Customers) adds revenue back automatically.
- Data storage: SQLite database. On Streamlit Cloud's free tier this can reset if the app \
fully restarts/sleeps for a long time -- so data isn't guaranteed permanent.
"""

# ---------------------------------------------------------------------------
# Fallback knowledge base (used only if Gemini is unavailable / not configured)
# ---------------------------------------------------------------------------
KNOWLEDGE_BASE = [
    (["what is this project", "what is mva mart", "about this project", "what does this app do"],
     "🏪 MVA Mart is an AI-driven supermarket management system. It handles inventory, sales, "
     "discounts, demand forecasting, alerts, restocking, funds, and reports — all in one "
     "dashboard, with AI predictions and a simulated AI customer feed built in."),
    (["hi", "hello", "hey", "namaste"],
     "👋 Hi there! Ask me about anything in MVA Mart — products, sales, discounts, forecasting, "
     "alerts, AI customers, funds, reports, or your account."),
    (["who are you", "what are you", "are you real ai"],
     "🤖 I'm the MVA Mart Assistant, powered by Google Gemini, with full knowledge of this project."),
    (["thank you", "thanks"],
     "😊 You're welcome! Ask me anything else about MVA Mart anytime."),
    (["dashboard", "executive dashboard", "kpi", "overview", "home page", "main page"],
     "📊 The 📊 Dashboard is your home screen — KPI cards for Inventory Value, Revenue, Profit, "
     "Profit Margin, Low Stock, Near Expiry, AI Reorder Needed, and Discounts Applied, plus "
     "charts and a live feed of Recently Applied Discounts."),
    (["profit margin"],
     "📊 Profit Margin = (Profit ÷ Revenue) × 100, over the last 30 days."),
    (["inventory value"],
     "💼 Inventory Value = Stock × Cost Price, summed across all products."),
    (["ai reorder needed", "ai reorder"],
     "🤖 Counts how many products AI Forecasting currently recommends reordering."),
    (["add product", "add a product", "new product", "create product", "add item"],
     "➕ Go to 📦 Inventory → Add Product tab. Fill in name, category, cost price, selling "
     "price, initial stock, reorder level, expiry date. Needs enough Funds to cover the cost."),
    (["update product", "edit product", "change price", "change stock"],
     "✏️ Go to 📦 Inventory → Update tab, select the product, change stock/prices/expiry."),
    (["search product", "find product", "search inventory"],
     "🔍 Go to 📦 Inventory → Search tab. Search by name or filter by category."),
    (["view inventory", "current inventory", "stock levels"],
     "📋 Go to 📦 Inventory → View tab: product table, Stock by Category chart, AI Restock "
     "Recommendations."),
    (["reorder level"],
     "📦 Reorder Level is the stock threshold that flags a product as low stock."),
    (["expiry date", "expiring", "near expiry"],
     "⏰ Set per product; items close to expiring show up in Near Expiry and Alerts."),
    (["category", "categories"],
     "🗂️ Categories organize products (e.g. Dairy, Bakery, Snacks)."),
    (["record sale", "make a sale", "sell product", "sell item", "how to sell"],
     "🛒 Go to 🛒 Sales → Record Sale tab. Revenue is automatically added to your Funds."),
    (["sales history", "past sales", "daily revenue"],
     "📜 Go to 🛒 Sales → Sales History tab for past sales and charts."),
    (["ai insight", "trending low"],
     "🤖 On the Sales page, an AI Insight callout shows products trending low."),
    (["ai customer", "customer message", "fulfill order", "reject order"],
     "🤖 The 🤖 AI Customers page simulates customers messaging in, arriving automatically "
     "roughly every 30 seconds. Fulfill (records a sale) or Reject each one."),
    (["discount", "apply discount", "custom discount"],
     "💰 Go to 💰 Discounts: AI Recommendations (with urgency levels) or a custom % discount. "
     "Every discount applied shows up on the Dashboard."),
    (["forecast", "prediction", "predict", "demand forecasting", "ai prediction", "algorithm"],
     "🔮 Go to 🔮 Forecasting: scikit-learn Linear Regression with weekly seasonality, trained "
     "on your real sales history, predicts 30-day demand with reorder recommendations."),
    (["alert", "low stock", "expiry warning"],
     "⚠️ Go to ⚠️ Alerts: Critical/Warning/Info alerts plus AI Predictive Alerts."),
    (["restock", "add stock", "buy stock"],
     "📥 Go to 📥 Restock: checks your Funds first, blocks if insufficient."),
    (["analytics", "financial analytics", "top products"],
     "📈 Go to 📈 Analytics: Revenue vs Profit, Category Analysis, Top Products ranking."),
    (["report", "export", "download", "csv"],
     "📋 Go to 📋 Reports → Generate tab to download Inventory/Sales/Financial CSVs."),
    (["fund", "money", "capital", "not enough money", "budget"],
     "💰 Click Funds in the top-right corner to view/edit available money. Buying deducts, "
     "selling adds, automatically."),
    (["language", "hindi", "translate"],
     "🌐 Click Language in the top-right corner for English/हिंदी."),
    (["login", "sign in"],
     "🔐 Use the Sign In tab on the login screen."),
    (["register", "sign up", "create account"],
     "📝 Use the Sign Up tab — name, username, password, role."),
    (["logout", "log out"],
     "🚪 Click Logout at the top of the sidebar."),
    (["role", "admin", "staff"],
     "👤 Role (staff/admin) is currently informational only, no access restrictions yet."),
    (["password", "forgot password"],
     "🔑 No password recovery yet — register a new account if needed."),
    (["data", "database", "sqlite", "does data persist"],
     "💾 Data is stored in SQLite. On Streamlit Cloud's free tier it can reset after a full "
     "restart, so it's not guaranteed permanent."),
]

FALLBACK_RESPONSE = (
    "🤔 I'm having trouble reaching the AI service right now, and I don't have a specific "
    "answer for that in my backup list. Try asking about: products, sales, discounts, "
    "restocking, forecasting, alerts, AI customers, reports, or funds."
)


def _get_keyword_response(question: str) -> str:
    """Backup rule-based matcher, used only if Gemini can't be reached."""
    q = question.lower()
    best_score, best_answer = 0, None
    for keywords, answer in KNOWLEDGE_BASE:
        score = sum(1 for phrase in keywords if phrase in q)
        if score > best_score:
            best_score, best_answer = score, answer
    return best_answer if best_answer else FALLBACK_RESPONSE


def _call_gemini(model: str, api_key: str, contents: list) -> str:
    """Make one request to the Gemini API. Raises on failure."""
    url = GEMINI_URL_TEMPLATE.format(model=model)
    response = requests.post(
        url,
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        json={"contents": contents},
        timeout=25
    )
    response.raise_for_status()
    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


def get_bot_response(question: str, history: list = None) -> str:
    """Returns an AI-generated answer using Google Gemini, with the whole
    project's features as context, so it can answer virtually anything
    about MVA Mart in an open-ended, ChatGPT-like way.

    `history` is an optional list of (role, message) tuples from the
    current conversation, used for multi-turn context.

    Falls back to a simple keyword-based answer if Gemini isn't
    configured or isn't reachable, so the chatbot never crashes.
    """
    if not question or not question.strip():
        return "Ask me anything about MVA Mart!"

    try:
        api_key = st.secrets.get("GEMINI_API_KEY", None)
    except Exception:
        api_key = None

    if not api_key:
        return (
            "⚠️ The full AI Assistant isn't set up yet (missing GEMINI_API_KEY in "
            "Streamlit secrets), so I'm using my backup answers for now:\n\n"
            + _get_keyword_response(question)
        )

    # Build the conversation: project context, then recent history, then the new question
    contents = [
        {"role": "user", "parts": [{"text": PROJECT_CONTEXT}]},
        {"role": "model", "parts": [{"text": "Understood -- I'm ready to help with MVA Mart!"}]},
    ]
    if history:
        for role, msg in history[-10:]:
            gem_role = "user" if role == "user" else "model"
            contents.append({"role": gem_role, "parts": [{"text": msg}]})
    contents.append({"role": "user", "parts": [{"text": question}]})

    for model in (GEMINI_MODEL, GEMINI_FALLBACK_MODEL):
        try:
            return _call_gemini(model, api_key, contents)
        except Exception as e:
            logger.warning(f"Gemini call failed with model {model}: {e}")
            continue

    # Both attempts failed -- use the offline backup so the user still gets an answer
    return (
        "⚠️ Couldn't reach the AI service just now, so here's a backup answer:\n\n"
        + _get_keyword_response(question)
    )
