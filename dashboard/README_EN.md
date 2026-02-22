# Crypto Dashboard - Enhanced Version

## 📊 Overview

An advanced dashboard for cryptocurrency investment analysis with comprehensive interactive features and advanced analytics.

## 🚀 New Features

### 📈 **Multiple Pages**
- **📊 Executive Summary**: Comprehensive performance overview with advanced indicators
- **🔄 Transactions**: Interactive transaction display with search and sorting
- **🧮 FIFO Analysis**: Detailed FIFO method analysis
- **📈 Advanced Charts**: Interactive charts using Plotly
- **📤 Export & Share**: Data export and report sharing
- **⚠️ Risk Analysis**: Comprehensive risk analysis and performance indicators

### 🔍 **Advanced Interactive Filters**
- Dynamic date range
- Multi-select coins
- Transaction size filter
- Profit/loss filter
- Automatic data refresh

### 📊 **Advanced Performance Indicators**
- Win/Loss Rate
- Profit Factor
- Sharpe Ratio
- Max Drawdown
- Calmar Ratio
- Sortino Ratio
- Value at Risk (VaR)
- Conditional VaR (CVaR)

### 📈 **Advanced Charts**
- Interactive line chart
- Performance-colored bar chart
- Cumulative profit chart
- Scatter plot
- Volume analysis
- Risk charts

### 🔔 **Alert System**
- Price alerts
- Performance alerts
- Risk alerts
- Instant notifications
- Ready templates

### 📤 **Export & Share**
- CSV export
- Excel export
- JSON export
- Share links
- Custom export settings

## 🛠️ Installation & Running

### 1. **Install Libraries**
```bash
pip install -r requirements.txt
```

### 2. **Run Dashboard**
```bash
# Run from main folder
streamlit run dashboard/enhanced_app.py

# Or run from dashboard folder
cd dashboard
streamlit run enhanced_app.py
```

### 3. **Run Full System**
```bash
# Run desktop application
python app_desktop.py

# Run all operations
python main.py
```

## 📁 File Structure

```
dashboard/
├── enhanced_app.py      # Main enhanced application
├── app.py              # Original application
├── components.py       # User interface components
├── utils.py           # Advanced analysis tools
├── alerts.py          # Alert system
└── README.md          # This file
```

## 🎯 How to Use

### 1. **Home Page**
- Instant executive summary display
- Main performance indicators
- Current portfolio status

### 2. **Interactive Filters**
- Use sidebar to filter data
- Select desired date range
- Specify required coins
- Adjust transaction size

### 3. **Advanced Analysis**
- Go to "Advanced Charts" page
- Choose chart type
- Interact with charts

### 4. **Export**
- Go to "Export & Share" page
- Select export format
- Download data

### 5. **Alerts**
- Alert settings in sidebar
- Add new alerts
- Monitor notifications

## 🔧 Customization

### **Adding New Indicators**
```python
# In utils.py
def custom_metric(data):
    # Calculate custom indicator
    return result

# In enhanced_app.py
metrics['custom_metric'] = custom_metric(data)
```

### **Adding New Charts**
```python
# In enhanced_app.py
def custom_chart(data):
    fig = px.custom_chart(...)
    st.plotly_chart(fig, use_container_width=True)
```

### **Customize Alerts**
```python
# In alerts.py
def custom_alert_condition(data, threshold):
    # Custom alert condition
    return condition_met
```

## 📊 Supported Data Types

### **Spot Transactions**
- Date and time
- Trading pair
- Quantity and price
- Total and fees

### **FIFO Data**
- Sale date
- Coin
- Realized profit
- Fees

### **Other Data**
- Binance Pay
- Deposits
- Withdrawals
- Simple Earn

## 🎨 Design & Interface

### **Themes**
- Modern design with gradient colors
- Interactive user interface
- Smooth animations
- Responsive design

### **Language**
- Full Arabic support
- Bilingual interface
- Professional Arabic labels

## 🚀 Performance

### **Optimizations**
- Data caching (5 minutes)
- Lazy loading
- Efficient large data processing
- Smart automatic updates

### **Memory**
- Efficient memory management
- Old data cleaning
- Data compression

## 🔒 Security

### **Data Protection**
- Input validation
- Error handling
- Sensitive data protection

### **Privacy**
- No personal data storage
- Sensitive data encryption
- Privacy policy

## 🐛 Troubleshooting

### **Common Issues**
1. **No data displayed**: Make sure to run `python main.py --report` first
2. **Error messages**: Check for `data/investment_report.xlsx` file
3. **Slow performance**: Use filters to reduce data size

### **Error Logs**
```bash
# View Streamlit logs
streamlit logs

# Run in debug mode
streamlit run enhanced_app.py --logger.level debug
```

## 🔄 Updates

### **Current Version**: v2.0.0
- ✅ Multiple pages
- ✅ Interactive filters
- ✅ Advanced charts
- ✅ Alert system
- ✅ Risk analysis

### **Coming in v2.1.0**
- 🔄 Additional exchange support
- 🤖 AI features
- 👥 Social features
- 📱 Mobile app

## 📞 Support

### **Contact**
- Email: support@crypto-dashboard.com
- Documentation: https://docs.crypto-dashboard.com
- Community: https://community.crypto-dashboard.com

### **Contribution**
- GitHub: https://github.com/crypto-dashboard
- Suggestions: https://feedback.crypto-dashboard.com

## 📄 License

This project is licensed under MIT License - See LICENSE file for details.

---

**Note**: Make sure `data/investment_report.xlsx` exists before running the dashboard. Run `python main.py` to generate the initial report.
