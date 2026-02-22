# 📊 Crypto Fund Manager

## 🎯 Overview

**Crypto Fund Manager** is an integrated system for managing and analyzing cryptocurrency investments with full Binance platform support. The system provides advanced tools for calculating profits and losses using the FIFO method, portfolio analysis, and generating detailed reports.

## ✨ Key Features

### 🔄 **Data Fetching**
- Secure connection with Binance API
- Historical transaction fetching
- Deposit and withdrawal data
- Binance Pay and Simple Earn data

### 🧮 **FIFO Calculation**
- Accurate profit and loss calculation
- Cost basis tracking
- Complex transaction processing
- Detailed tax reports

### 📈 **Portfolio Analysis**
- Current asset allocation
- Real-time portfolio value
- Historical performance analysis
- Advanced performance indicators

### 📊 **Dashboards**
- **Original Dashboard**: Simple and fast interface
- **Enhanced Dashboard**: Advanced 6-page interface
- Multi-dimensional interactive filters
- Professional charts

### 📤 **Reports & Export**
- Detailed Excel reports
- Multi-format export (CSV/Excel/JSON)
- Exportable charts
- Report sharing links

### 🔔 **Alert System**
- Price alerts
- Performance alerts
- Risk alerts
- Instant notifications

## 🚀 Quick Start

### 1. **Install Requirements**
```bash
# Install required libraries
pip install -r requirements.txt
```

### 2. **Setup API Keys**
```bash
# Create .env file in config folder
cp config/.env.example config/.env
# Add your Binance API keys
```

### 3. **Run the System**

#### **Option 1: Desktop Application (Recommended)**
```bash
python app_desktop.py
```

#### **Option 2: Command Line**
```bash
# Run all operations
python main.py

# Or run specific operations
python main.py --fetch      # Fetch data
python main.py --fifo       # Calculate FIFO
python main.py --portfolio  # Calculate Portfolio
python main.py --report     # Generate Reports
```

#### **Option 3: Dashboard**
```bash
# Original Dashboard
streamlit run dashboard/app.py

# Enhanced Dashboard
streamlit run dashboard/enhanced_app.py

# Or using auto-runner
python dashboard/run_enhanced.py
```

## 📁 Project Structure

```
crypto_fund_manager/
├── 📁 api/                    # Binance API connection
│   └── binance_client.py      # Binance client
├── 📁 config/                 # System settings
│   ├── settings.py           # General settings
│   └── .env                  # API keys (secret)
├── 📁 core/                   # Main engine
│   ├── data_fetcher.py       # Data fetching
│   ├── fifo_engine.py        # FIFO engine
│   ├── portfolio.py          # Portfolio analysis
│   └── report_generator.py   # Report generation
├── 📁 dashboard/              # Dashboards
│   ├── app.py               # Original dashboard
│   ├── enhanced_app.py      # Enhanced dashboard
│   ├── simple_app.py        # Simplified version
│   ├── components.py        # UI components
│   ├── utils.py            # Analysis tools
│   ├── alerts.py           # Alert system
│   └── run_enhanced.py     # Auto-runner
├── 📁 data/                  # Data storage
│   ├── *.csv               # Raw data
│   └── investment_report.xlsx # Main report
├── 📁 logs/                  # System logs
├── 📁 reports/               # Exported reports
├── 📄 app_desktop.py         # Desktop application
├── 📄 main.py               # Main entry point
├── 📄 requirements.txt      # Required libraries
└── 📄 README.md             # This file
```

## 🔐 Binance API Setup

### 1. **Create API Keys**
1. Log in to [Binance](https://www.binance.com)
2. Go to `API Management`
3. Create new keys
4. Enable required permissions:
   - ✅ Enable Reading
   - ✅ Enable Spot & Margin Trading
   - ✅ Enable Futures (Optional)

### 2. **Configure Keys**
```bash
# In config/.env file
BINANCE_API_KEY=your_api_key_here
BINANCE_SECRET_KEY=your_secret_key_here
```

### 3. **Test Connection**
```python
from api.binance_client import BinanceClient
client = BinanceClient()
account = client._get("/api/v3/account")
print("✅ Connection successful!")
```

## 📊 Dashboards

### 🖥️ **Desktop Application**
Tkinter interface with 8 buttons for complete control:
1. 🔄 Fetch Binance Data
2. 🧮 Calculate FIFO PnL  
3. 📊 Calculate Portfolio
4. 📋 Generate Excel Reports
5. 📈 Launch Dashboard
6. 🚀 Enhanced Dashboard
7. 📂 Open Reports Folder
8. ❌ Exit

### 🌐 **Original Dashboard**
- Single simple page
- Basic filters
- Live charts
- Suitable for quick operations

### 🎨 **Enhanced Dashboard**
Professional 6-page dashboard:

#### 📊 **Executive Summary**
- 15+ performance indicators
- Interactive cards
- Real-time portfolio status
- Performance recommendations

#### 🔄 **Transactions**
- Interactive search and sorting
- Multiple filters
- Instant export
- Transaction statistics

#### 🧮 **FIFO Analysis**
- Detailed FIFO analysis
- Profit/loss statistics
- Advanced charts
- Tax reports

#### 📈 **Advanced Charts**
- 5+ chart types
- Interactive charts
- Time analysis
- Export as images

#### 📤 **Export & Share**
- Export in all formats
- Share links
- Report bundles
- Custom settings

#### ⚠️ **Risk Analysis**
- Drawdown analysis
- Value at Risk (VaR)
- Risk indicators
- Risk management recommendations

## 📈 Performance Indicators

### 📊 **Basic Indicators**
- Total trades
- Realized profit
- Total fees
- Net profit
- Win rate

### 🎯 **Advanced Indicators**
- Profit Factor
- Sharpe Ratio
- Max Drawdown
- Calmar Ratio
- Sortino Ratio
- Value at Risk (VaR)
- Conditional VaR (CVaR)
- Beta coefficient
- Alpha coefficient

## 🔧 Interactive Filters

### 📅 **Date Filter**
- Dynamic date range selection
- Daily/weekly/monthly granularity
- Period comparison

### 🪙 **Coin Filter**
- Multi-select coins
- Quick coin search
- Filter by volume

### 💰 **Amount Filter**
- Minimum transaction size
- Filter by total value
- Flexible ranges

### 📊 **Performance Filter**
- Winning trades only
- Losing trades only
- Filter by profit size

## 📤 Export & Share

### 📋 **Export Formats**
- **CSV**: For analysis in Excel
- **Excel**: Formatted reports
- **JSON**: For system integration
- **PNG**: For charts

### 🔗 **Sharing**
- Direct report links
- Share via email
- Share via WhatsApp
- Embed in websites

### 📦 **Report Bundles**
- Multi-page bundles
- Custom reports
- Time series
- Comparative analysis

## 🔔 Alert System

### 💰 **Price Alerts**
- When price reaches certain level
- Above/below target
- For multiple coins

### 📊 **Performance Alerts**
- Win rate drops
- Loss threshold exceeded
- Large portfolio changes

### ⚠️ **Risk Alerts**
- Risk limit exceeded
- Sharp value decline
- High volatility

### 🎯 **Ready Templates**
- Pre-defined templates
- Quick customization
- One-click activation

## 🛠️ Customization & Development

### 🔧 **Adding New Indicators**
```python
# In utils.py
def custom_metric(data):
    # Calculate custom indicator
    return result

# In enhanced_app.py
metrics['custom_metric'] = custom_metric(data)
```

### 📊 **Adding New Charts**
```python
# In components.py
def custom_chart(data):
    fig = px.custom_chart(...)
    return fig
```

### 🔔 **Adding New Alerts**
```python
# In alerts.py
def custom_alert_condition(data, threshold):
    return condition_met
```

## 📋 Technical Requirements

### 🐍 **Python**
- Python 3.8 or higher
- Required libraries in `requirements.txt`

### 📦 **Main Libraries**
```
streamlit>=1.28.0    # Dashboards
plotly>=5.0.0        # Charts
pandas>=1.5.0        # Data analysis
numpy>=1.21.0        # Calculations
requests>=2.32.5     # API connection
openpyxl>=3.0.0      # Excel files
python-dotenv>=0.19.0 # Environment variables
```

### 🌐 **External Requirements**
- Stable internet connection
- Binance account with API Keys
- Modern web browser

## 🔒 Security & Privacy

### 🛡️ **Data Protection**
- All communications encrypted (HTTPS)
- Digital signing of all requests (HMAC-SHA256)
- No sensitive data storage
- Secure key handling

### 🔐 **Best Practices**
- Never share API keys
- Use test environment for testing
- Update keys periodically
- Review permissions regularly

### 📊 **Privacy**
- All data is local
- No data sent to external servers
- Full data control
- Data deletion capability

## 🐛 Troubleshooting

### 🔧 **Common Issues**

#### **❌ No data displayed**
```bash
# Solution: Run data first
python main.py --report
```

#### **❌ Binance connection error**
```bash
# Solution: Check API keys
# 1. Verify keys are correct in config/.env
# 2. Verify permissions are enabled on Binance
# 3. Check internet connection
```

#### **❌ Library errors**
```bash
# Solution: Reinstall libraries
pip install -r requirements.txt --upgrade
```

#### **❌ Dashboard not working**
```bash
# Solution: Use simplified version
streamlit run dashboard/simple_app.py
```

### 📋 **Error Logs**
```bash
# View Streamlit logs
streamlit logs

# Run in debug mode
streamlit run dashboard/enhanced_app.py --logger.level debug
```

## 🚀 Performance & Optimization

### ⚡ **Performance Optimizations**
- Data caching (5 minutes)
- Lazy loading for large data
- Efficient memory processing
- Smart updates

### 📊 **Data Processing**
- Automatic data cleaning
- Outlier removal
- Data validation
- Data compression

### 🔄 **Updates**
- Automatic data updates
- Manual refresh button
- New data notifications
- Smart sync

## 📚 Documentation & Support

### 📖 **User Guides**
- [Quick Start Guide](#-quick-start)
- [API Setup Guide](#-binance-api-setup)
- [Dashboard Guide](#-dashboards)
- [Customization Guide](#-customization--development)

### 🆘 **Getting Help**
- **Email**: support@crypto-fund-manager.com
- **Documentation**: https://docs.crypto-fund-manager.com
- **Community**: https://community.crypto-fund-manager.com
- **GitHub**: https://github.com/crypto-fund-manager/issues

### 📺 **Video Tutorials**
- [Quick Start Video](https://youtu.be/quickstart)
- [API Setup Video](https://youtu.be/api-setup)
- [Dashboard Tour Video](https://youtu.be/dashboard-tour)
- [Advanced Analysis Video](https://youtu.be/advanced-analysis)

## 🗺️ Roadmap

### 📅 **Current Version: v2.0.0**
- ✅ Enhanced 6-page dashboard
- ✅ 15+ advanced performance indicators
- ✅ Complete alert system
- ✅ Comprehensive risk analysis
- ✅ Multi-format export

### 🚀 **Coming in v2.1.0**
- 🔄 Additional exchange support (Coinbase, Kraken)
- 🤱 AI features
- 📱 Mobile app
- 👥 Social features and comparison
- 🔔 Push notifications via app

### 🎯 **Long-term (v3.0.0)**
- 🌐 Full web interface
- 🤖 Advanced trading bot
- 📊 Professional technical analysis
- 🔗 Platform integrations
- 💰 Multi-portfolio management

## 🤝 Contributing

### 📋 **How to Contribute**
1. Fork the project
2. Create new branch (`git checkout -b feature/amazing-feature`)
3. Make changes
4. Commit (`git commit -m 'Add amazing feature'`)
5. Push (`git push origin feature/amazing-feature`)
6. Create Pull Request

### 🎯 **Needed Contributions**
- 🐛 Bug fixes
- ✨ New features
- 📚 Documentation improvement
- 🌐 Translation to other languages
- 🧪 Writing tests

### 📝 **Code Standards**
- Follow PEP 8
- Write clear comments
- Test code before submitting
- Document changes

## 📄 License

This project is licensed under **MIT License** - See [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

### 🌟 **Contributors**
- All developers who contributed to the project
- Valuable user community
- Beta testers

### 🏢 **Partners**
- **Binance** for providing the reliable API
- **Streamlit** for the dashboard framework
