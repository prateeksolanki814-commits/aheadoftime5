"""AI Assistant Chatbot Module.

A self-contained help assistant that answers unlimited questions about
how to use MVA Mart. It works by matching keywords in the user's
question against a knowledge base covering every feature of the app,
and returns the most relevant answer.

Note: this does NOT call any external AI API (like OpenAI or Claude).
It's a rule-based FAQ assistant, which means it works instantly, for
free, with zero extra dependencies, and never fails to load on
Streamlit Cloud. It can answer any number of questions about the
project's features; it does not have general knowledge outside of
MVA Mart itself.
"""

# Each entry: (list of keywords/phrases, answer text)
# Keep keywords lowercase. More specific/longer phrases should come
# first so they get priority over generic single-word matches.
KNOWLEDGE_BASE = [
    (["what is this project", "what is mva mart", "about this project", "what does this app do"],
     "🏪 MVA Mart is an AI-driven supermarket management system. It handles inventory, sales, "
     "discounts, demand forecasting, alerts, restocking, and reports — all in one dashboard, "
     "with AI predictions built in."),

    (["add product", "add a product", "new product", "create product", "add item"],
     "➕ To add a product: go to **📦 Inventory → Add Product** tab. Fill in the name, category, "
     "cost price, selling price, initial stock, reorder level, and expiry date, then click "
     "**Add Product**. Note: you need enough funds to cover the cost of the initial stock."),

    (["update product", "edit product", "change price", "change stock"],
     "✏️ To update a product: go to **📦 Inventory → Update** tab, select the product, and change "
     "its stock, cost price, selling price, or expiry date."),

    (["search product", "find product", "search inventory"],
     "🔍 Go to **📦 Inventory → Search** tab. You can search by name or filter by category."),

    (["record sale", "make a sale", "sell product", "sell item", "how to sell"],
     "🛒 Go to **🛒 Sales → Record Sale** tab, choose the product and quantity, optionally add a "
     "discount %, then click **Record Sale**. The revenue is automatically added to your funds."),

    (["sales history", "past sales", "previous sales"],
     "📜 Go to **🛒 Sales → Sales History** tab to see all past sales, daily revenue, and units "
     "sold by product."),

    (["discount", "apply discount", "how do discounts work"],
     "💰 Go to the **💰 Discounts** page. The AI Recommendations tab suggests discounts for slow-"
     "moving or expiring stock. The Apply Discount tab lets you set a custom discount on any "
     "product. Every discount you apply shows up on the Executive Dashboard too."),

    (["restock", "add stock", "buy stock", "purchase stock"],
     "📥 Go to the **📥 Restock** page, pick a product, enter quantity and cost per unit, then "
     "click Restock. This checks your available funds first — if there isn't enough money, "
     "it will tell you and won't go through."),

    (["forecast", "prediction", "predict", "demand forecasting", "ai prediction"],
     "🔮 Go to the **🔮 Forecasting** page. It uses AI (scikit-learn) to predict demand for the "
     "next 30 days per product, and gives purchase/reorder recommendations based on your real "
     "sales history."),

    (["alert", "low stock", "expiry warning", "warnings"],
     "⚠️ Go to the **⚠️ Alerts** page. It shows critical/warning/info alerts for low stock and "
     "expiring items, plus AI Predictive Alerts based on demand forecasting."),

    (["ai customer", "customer message", "simulated customer", "fulfill order"],
     "🤖 The **🤖 AI Customers** page simulates customers messaging in wanting to buy products. "
     "New messages appear automatically over time. You can Fulfill an order (records a real "
     "sale and adds revenue) or Reject it."),

    (["report", "export", "download", "csv"],
     "📋 Go to the **📋 Reports** page → Generate tab. Choose a report type (Inventory, Sales, "
     "or Financial) and click Generate Report to download a CSV."),

    (["dashboard", "executive dashboard", "kpi", "overview"],
     "📊 The **📊 Dashboard** page is your home screen — it shows Inventory Value, Revenue, "
     "Profit, Profit Margin, Low Stock, Near Expiry, AI Reorder Needed, and Discounts Applied, "
     "plus charts and your recently applied discounts."),

    (["fund", "money", "capital", "not enough money", "budget"],
     "💰 Click the **Funds** button in the top-right corner to see your available money and set "
     "a new total anytime. Buying stock (Add Product / Restock) deducts from your funds and "
     "will be blocked if you don't have enough. Selling products adds revenue back to your funds."),

    (["language", "hindi", "translate", "change language"],
     "🌐 Click the **Language** dropdown in the top-right corner and choose English or हिंदी. "
     "The whole app updates immediately."),

    (["login", "sign in", "log in"],
     "🔐 Use the **Sign In** tab on the login screen with your username and password."),

    (["register", "sign up", "create account", "new account"],
     "📝 Use the **Sign Up** tab on the login screen — enter your name, choose a username and "
     "password, pick a role (staff/admin), and click Create Account."),

    (["logout", "log out", "sign out"],
     "🚪 Click the **Logout** button at the top of the sidebar."),

    (["category", "categories"],
     "🗂️ Categories organize your products (e.g. Dairy, Bakery, Snacks). You pick one when "
     "adding a product, and can filter/analyze by category in Inventory and Analytics."),

    (["analytics", "financial analytics", "profit margin"],
     "📈 Go to the **📈 Analytics** page for Revenue vs Profit charts, category performance, and "
     "top products ranked by profit, revenue, or sales volume."),

    (["help", "how does this work", "what can you do"],
     "🤖 I can help you with: adding/updating products, recording sales, discounts, restocking, "
     "AI forecasting, alerts, AI customers, reports, funds, language, and account questions. "
     "Just ask me about any of these!"),
]

FALLBACK_RESPONSE = (
    "🤔 I'm not sure about that one. I can help with: products, sales, discounts, restocking, "
    "forecasting, alerts, AI customers, reports, funds, dashboard, or your account (login/"
    "register). Try asking about one of those!"
)


def get_bot_response(question: str, history=None) -> str:
    """
    Returns the best matching answer.
    'history' is accepted for compatibility with app.py.
    """

    if history is None:
        history = []

    if not question or not question.strip():
        return (
            "Ask me anything about MVA Mart — products, sales, discounts, "
            "forecasting, alerts, billing, reports, and more!"
        )

    q = question.lower()
    best_score = 0
    best_answer = None

    for keywords, answer in KNOWLEDGE_BASE:
        score = sum(1 for phrase in keywords if phrase in q)
        if score > best_score:
            best_score = score
            best_answer = answer

    return best_answer if best_answer else FALLBACK_RESPONSE
