import os
from dotenv import load_dotenv
from config.user_config import user_config

# Load from config directory
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

# Try to load from user_config first, fallback to .env
def get_api_keys():
    """Get API keys from user config or environment"""
    # Check user config first
    if user_config.is_configured():
        return user_config.get_api_key(), user_config.get_api_secret()
    
    # Fallback to environment variables
    api_key = os.getenv("BINANCE_API_KEY")
    secret_key = os.getenv("BINANCE_SECRET_KEY")
    return api_key, secret_key

# Get API keys
BINANCE_API_KEY, BINANCE_SECRET_KEY = get_api_keys()

# 🌐 Binance Base URL
BASE_URL = "https://api.binance.com"

# 📁 Paths
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
REPORT_FILE = os.path.join(DATA_DIR, "investment_report.xlsx")
DB_FILE = os.path.join(DATA_DIR, "crypto_fund_manager.db")

# Configuration file path
CONFIG_FILE = os.path.join(BASE_DIR, "config", "user_config.json")
