#!/usr/bin/env python3
"""
Auto-startup script for Retail Intelligence Dashboard
Runs everything automatically
"""

import subprocess
import sys
import time
import os
import webbrowser
from pathlib import Path

def check_python_version():
    """Check if Python 3.7+ is installed"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ required")
        sys.exit(1)
    print(f"✅ Python {sys.version.split()[0]} detected")

def install_requirements():
    """Install all required packages"""
    print("\n📦 Installing dependencies...")
    req_file = Path("requirements.txt")
    if req_file.exists():
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"], check=False)
        print("✅ Dependencies installed")
    else:
        print("⚠️ requirements.txt not found")

def create_data_directory():
    """Create data directory if it doesn't exist"""
    Path("data").mkdir(exist_ok=True)
    print("✅ Data directory ready")

def initialize_database():
    """Initialize the database"""
    print("\n🗄️ Initializing database...")
    try:
        from database import db
        print("✅ Database initialized")
    except Exception as e:
        print(f"⚠️ Database init note: {e}")

def open_browser():
    """Open browser to dashboard"""
    time.sleep(3)
    print("\n🌐 Opening browser...")
    webbrowser.open("http://localhost:8501")

def main():
    """Main startup function"""
    print("\n")
    print("=" * 60)
    print("🏪 RETAIL INTELLIGENCE DASHBOARD")
    print("=" * 60)
    print("\n")
    
    check_python_version()
    create_data_directory()
    install_requirements()
    initialize_database()
    
    print("\n" + "=" * 60)
    print("🚀 STARTING STREAMLIT APPLICATION")
    print("=" * 60)
    print("\n📍 Dashboard: http://localhost:8501")
    print("🛑 Press Ctrl+C to stop\n")
    print("=" * 60)
    print("\n")
    
    # Open browser in background
    import threading
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Run Streamlit
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py", "--logger.level=error"], check=False)
    except KeyboardInterrupt:
        print("\n\n👋 Dashboard stopped")
        sys.exit(0)

if __name__ == "__main__":
    main()
