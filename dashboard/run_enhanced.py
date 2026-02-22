#!/usr/bin/env python3
"""
Enhanced Dashboard Launcher
Quick launcher for the enhanced crypto dashboard
"""

import subprocess
import sys
import os
from pathlib import Path

def check_requirements():
    """Check if required packages are installed"""
    required_packages = [
        'streamlit', 'plotly', 'pandas', 'numpy', 'openpyxl'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("📦 Installing missing packages...")
        
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install"
            ] + missing_packages)
            print("✅ Packages installed successfully!")
        except subprocess.CalledProcessError:
            print("❌ Failed to install packages. Please run:")
            print("pip install -r requirements.txt")
            return False
    
    return True

def check_data_file():
    """Check if data file exists"""
    data_file = Path("data/investment_report.xlsx")
    db_file = Path("data/crypto_fund_manager.db")
    
    if not data_file.exists() and not db_file.exists():
        print("⚠️ No data file found. Generating sample data...")
        
        try:
            # Try to generate data
            subprocess.check_call([sys.executable, "main.py"])
            print("✅ Data generated successfully!")
        except subprocess.CalledProcessError:
            print("❌ Failed to generate data. Please run:")
            print("python main.py")
            return False
    
    return True

def launch_dashboard():
    """Launch the enhanced dashboard"""
    print("🚀 Launching Enhanced Crypto Dashboard...")
    
    # Change to dashboard directory
    dashboard_dir = Path(__file__).parent
    os.chdir(dashboard_dir)
    
    # Launch streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "enhanced_app.py", "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Error launching dashboard: {e}")

def main():
    """Main launcher function"""
    print("=" * 50)
    print("📊 Enhanced Crypto Dashboard Launcher")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        return
    
    # Check data file
    if not check_data_file():
        print("⚠️ Continuing without data file...")
    
    # Launch dashboard
    launch_dashboard()

if __name__ == "__main__":
    main()
