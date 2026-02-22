import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import sys
import os
import base64
import io
import sqlite3

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config.settings import REPORT_FILE, DB_FILE
except ImportError:
    # Fallback if config module not available
    REPORT_FILE = Path(__file__).parent.parent / "data" / "investment_report.xlsx"
    DB_FILE = Path(__file__).parent.parent / "data" / "crypto_fund_manager.db"

# ==================================================
# Configuration
# ==================================================
st.set_page_config(
    page_title="Crypto Investment Dashboard", 
    layout="wide", 
    initial_sidebar_state="expanded",
    page_icon="📊"
)

# ==================================================
# Ensure REPORT_FILE is a Path object
# ==================================================
REPORT_FILE = Path(REPORT_FILE)
DB_FILE = Path(DB_FILE)

# ==================================================
# Custom CSS for better styling
# ==================================================
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
    }
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chart-container {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ==================================================
# Helper functions with caching and loading states
# ==================================================

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data():
    """Load all data with progress indication"""
    def load_from_db(table_name):
        try:
            with sqlite3.connect(DB_FILE) as conn:
                return pd.read_sql_query(f'SELECT * FROM "{table_name}"', conn)
        except Exception:
            return pd.DataFrame()

    summary_db = load_from_db("report_summary")
    fifo_db = load_from_db("fifo")
    if fifo_db.empty:
        fifo_db = load_from_db("fifo_results")
    trades_db = load_from_db("spot_trades")
    binance_pay_db = load_from_db("binance_pay")
    deposits_db = load_from_db("deposits")
    withdrawals_db = load_from_db("withdrawals")
    simple_earn_db = load_from_db("simple_earn")
    rwusd_db = load_from_db("rwusd")
    bfusd_db = load_from_db("bfusd")
    bnsol_db = load_from_db("bnsol")
    lusdt_db = load_from_db("lusdt")
    flexible_stock_db = load_from_db("flexible_stock")
    small_assets_db = load_from_db("small_assets")
    spot_wallet_db = load_from_db("spot_wallet")
    fund_wallet_db = load_from_db("fund_wallet")
    earn_wallet_db = load_from_db("earn_wallet")

    db_frames = [
        summary_db, fifo_db, trades_db, binance_pay_db, deposits_db, withdrawals_db, simple_earn_db,
        rwusd_db, bfusd_db, bnsol_db, lusdt_db, flexible_stock_db, small_assets_db, spot_wallet_db,
        fund_wallet_db, earn_wallet_db
    ]

    if any(not df.empty for df in db_frames):
        return (
            summary_db, fifo_db, trades_db, binance_pay_db, deposits_db, withdrawals_db, simple_earn_db,
            rwusd_db, bfusd_db, bnsol_db, lusdt_db, flexible_stock_db, small_assets_db,
            spot_wallet_db, fund_wallet_db, earn_wallet_db
        )

    if not REPORT_FILE.exists():
        st.warning("No report or SQLite data found. Generate data first.")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    try:
        xls = pd.ExcelFile(REPORT_FILE)
        
        # Case-insensitive search for sheets
        summary_sheets = [s for s in xls.sheet_names if "summary" in s.lower()]
        fifo_sheets = [s for s in xls.sheet_names if "fifo" in s.lower()]
        trades_sheets = [s for s in xls.sheet_names if "trade" in s.lower()]
        binance_pay_sheets = [s for s in xls.sheet_names if "binance pay" in s.lower()]
        deposits_sheets = [s for s in xls.sheet_names if "deposit" in s.lower()]
        withdrawals_sheets = [s for s in xls.sheet_names if "withdrawal" in s.lower()]
        simple_earn_sheets = [s for s in xls.sheet_names if "simple earn" in s.lower()]
        rwusd_sheets = [s for s in xls.sheet_names if "rwusd" in s.lower()]
        bfusd_sheets = [s for s in xls.sheet_names if "bfusd" in s.lower()]
        bnsol_sheets = [s for s in xls.sheet_names if "bnsol" in s.lower()]
        lusdt_sheets = [s for s in xls.sheet_names if "lusdt" in s.lower()]
        flexible_stock_sheets = [s for s in xls.sheet_names if "flexible stock" in s.lower()]
        small_assets_sheets = [s for s in xls.sheet_names if "small assets" in s.lower()]
        spot_wallet_sheets = [s for s in xls.sheet_names if "spot wallet" in s.lower()]
        fund_wallet_sheets = [s for s in xls.sheet_names if "fund wallet" in s.lower()]
        earn_wallet_sheets = [s for s in xls.sheet_names if "earn wallet" in s.lower()]

        # Load all available data
        summary_df = pd.read_excel(REPORT_FILE, sheet_name=summary_sheets[0]) if summary_sheets else pd.DataFrame()
        fifo_df = pd.read_excel(REPORT_FILE, sheet_name=fifo_sheets[0]) if fifo_sheets else pd.DataFrame()
        trades_df = pd.read_excel(REPORT_FILE, sheet_name=trades_sheets[0]) if trades_sheets else pd.DataFrame()
        binance_pay_df = pd.read_excel(REPORT_FILE, sheet_name=binance_pay_sheets[0]) if binance_pay_sheets else pd.DataFrame()
        deposits_df = pd.read_excel(REPORT_FILE, sheet_name=deposits_sheets[0]) if deposits_sheets else pd.DataFrame()
        withdrawals_df = pd.read_excel(REPORT_FILE, sheet_name=withdrawals_sheets[0]) if withdrawals_sheets else pd.DataFrame()
        simple_earn_df = pd.read_excel(REPORT_FILE, sheet_name=simple_earn_sheets[0]) if simple_earn_sheets else pd.DataFrame()
        rwusd_df = pd.read_excel(REPORT_FILE, sheet_name=rwusd_sheets[0]) if rwusd_sheets else pd.DataFrame()
        bfusd_df = pd.read_excel(REPORT_FILE, sheet_name=bfusd_sheets[0]) if bfusd_sheets else pd.DataFrame()
        bnsol_df = pd.read_excel(REPORT_FILE, sheet_name=bnsol_sheets[0]) if bnsol_sheets else pd.DataFrame()
        lusdt_df = pd.read_excel(REPORT_FILE, sheet_name=lusdt_sheets[0]) if lusdt_sheets else pd.DataFrame()
        flexible_stock_df = pd.read_excel(REPORT_FILE, sheet_name=flexible_stock_sheets[0]) if flexible_stock_sheets else pd.DataFrame()
        small_assets_df = pd.read_excel(REPORT_FILE, sheet_name=small_assets_sheets[0]) if small_assets_sheets else pd.DataFrame()
        spot_wallet_df = pd.read_excel(REPORT_FILE, sheet_name=spot_wallet_sheets[0]) if spot_wallet_sheets else pd.DataFrame()
        fund_wallet_df = pd.read_excel(REPORT_FILE, sheet_name=fund_wallet_sheets[0]) if fund_wallet_sheets else pd.DataFrame()
        earn_wallet_df = pd.read_excel(REPORT_FILE, sheet_name=earn_wallet_sheets[0]) if earn_wallet_sheets else pd.DataFrame()

        return (
            summary_df, fifo_df, trades_df, binance_pay_df, deposits_df, withdrawals_df, simple_earn_df,
            rwusd_df, bfusd_df, bnsol_df, lusdt_df, flexible_stock_df, small_assets_df,
            spot_wallet_df, fund_wallet_df, earn_wallet_df
        )
    
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return (
            pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(),
            pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(),
            pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        )

@st.cache_data(ttl=300)
def calculate_advanced_metrics(trades_df, fifo_df):
    """Calculate advanced performance metrics"""
    metrics = {}
    
    if not trades_df.empty:
        metrics['total_trades'] = len(trades_df)
        
        # Win rate calculation
        if not fifo_df.empty and 'realized_pnl' in fifo_df.columns:
            winning_trades = len(fifo_df[fifo_df['realized_pnl'] > 0])
            total_completed_trades = len(fifo_df)
            metrics['win_rate'] = (winning_trades / total_completed_trades * 100) if total_completed_trades > 0 else 0
            
            # Average trade metrics
            metrics['avg_win'] = fifo_df[fifo_df['realized_pnl'] > 0]['realized_pnl'].mean() if winning_trades > 0 else 0
            metrics['avg_loss'] = fifo_df[fifo_df['realized_pnl'] < 0]['realized_pnl'].mean() if len(fifo_df[fifo_df['realized_pnl'] < 0]) > 0 else 0
            
            # Best and worst trades
            metrics['best_trade'] = fifo_df['realized_pnl'].max()
            metrics['worst_trade'] = fifo_df['realized_pnl'].min()
            
            # Profit factor
            gross_profit = fifo_df[fifo_df['realized_pnl'] > 0]['realized_pnl'].sum()
            gross_loss = abs(fifo_df[fifo_df['realized_pnl'] < 0]['realized_pnl'].sum())
            metrics['profit_factor'] = gross_profit / gross_loss if gross_loss > 0 else float('inf')
            
            # Total metrics
            metrics['realized_pnl'] = fifo_df['realized_pnl'].sum()
            metrics['total_fees'] = fifo_df.get('fee', pd.Series([0])).sum()
            metrics['net_profit'] = metrics['realized_pnl'] - metrics['total_fees']
            
            # Max drawdown calculation
            cumulative_pnl = fifo_df.sort_values('sell_time' if 'sell_time' in fifo_df.columns else 'sellTime')['realized_pnl'].cumsum()
            running_max = cumulative_pnl.expanding().max()
            drawdown = (cumulative_pnl - running_max) / running_max
            metrics['max_drawdown'] = drawdown.min() * 100  # as percentage
            
            # Sharpe ratio (simplified)
            if len(fifo_df) > 1:
                returns = fifo_df['realized_pnl'].pct_change().dropna()
                if returns.std() > 0:
                    metrics['sharpe_ratio'] = (returns.mean() / returns.std()) * np.sqrt(252)  # annualized
                else:
                    metrics['sharpe_ratio'] = 0
            else:
                metrics['sharpe_ratio'] = 0
    
    return metrics

def filter_data_by_date(df, date_range, date_col='time'):
    """Filter data by date range"""
    if df.empty or date_col not in df.columns:
        return df
    
    df_copy = df.copy()
    df_copy[date_col] = pd.to_datetime(df_copy[date_col], errors='coerce')
    start_date = pd.to_datetime(date_range[0])
    end_date = pd.to_datetime(date_range[1]) + timedelta(days=1)
    
    return df_copy[(df_copy[date_col] >= start_date) & (df_copy[date_col] < end_date)]

def filter_data_by_coins(df, selected_coins, symbol_col='symbol'):
    """Filter data by selected coins"""
    if df.empty or not selected_coins or symbol_col not in df.columns:
        return df
    
    df_copy = df.copy()
    if symbol_col == 'symbol':
        df_copy['coin'] = df_copy[symbol_col].str.replace('USDT', '')
        return df_copy[df_copy['coin'].isin(selected_coins)]
    else:
        return df_copy[df_copy[symbol_col].isin(selected_coins)]

def filter_data_by_amount(df, min_amount, amount_col='quantity'):
    """Filter data by minimum amount"""
    if df.empty or amount_col not in df.columns:
        return df
    
    return df[df[amount_col] >= min_amount]

def filter_data_by_pnl(df, pnl_filter):
    """Filter FIFO data by PnL"""
    if df.empty or 'realized_pnl' not in df.columns:
        return df
    
    if pnl_filter == "صفقات رابحة فقط":
        return df[df['realized_pnl'] > 0]
    elif pnl_filter == "صفقات خاسرة فقط":
        return df[df['realized_pnl'] < 0]
    return df

def create_download_link(df, filename, link_text):
    """Create a download link for dataframe"""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{link_text}</a>'
    return href

# ==================================================
# Page Navigation
# ==================================================
def main():
    # Load data with loading state
    with st.spinner("🔄 جاري تحميل البيانات..."):
        (
            summary_df, fifo_df, trades_df, binance_pay_df, deposits_df, withdrawals_df, simple_earn_df,
            rwusd_df, bfusd_df, bnsol_df, lusdt_df, flexible_stock_df, small_assets_df,
            spot_wallet_df, fund_wallet_df, earn_wallet_df
        ) = load_data()
    
    # Main header
    st.markdown("""
    <div class="main-header">
        <h1>📊 Crypto Investment Dashboard</h1>
        <p>نظام متقدم لتحليل الاستثمار في العملات المشفرة</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar navigation
    st.sidebar.header("🧭 التنقل")
    page = st.sidebar.selectbox("اختر الصفحة", [
        "📊 ملخص تنفيذي", 
        "🔄 المعاملات", 
        "🧮 تحليل FIFO",
        "📈 الرسوم البيانية المتقدمة",
        "📤 التصدير والمشاركة",
        "⚠️ تحليل المخاطر",
        "💰 منتجات الاستثمار"
    ])
    
    # Common filters in sidebar
    st.sidebar.header("🔍 الفلاتر التفاعلية")
    
    # Date range filter
    if not trades_df.empty and 'time' in trades_df.columns:
        min_date = pd.to_datetime(trades_df['time']).min().date()
        max_date = pd.to_datetime(trades_df['time']).max().date()
        date_range = st.sidebar.date_input(
            "نطاق التاريخ",
            value=[min_date, max_date],
            min_value=min_date,
            max_value=max_date
        )
    else:
        date_range = [datetime.now().date() - timedelta(days=30), datetime.now().date()]
    
    # Coin filter
    available_coins = []
    if not trades_df.empty:
        if 'symbol' in trades_df.columns:
            available_coins = sorted(trades_df['symbol'].str.replace('USDT', '').unique())
        elif 'asset' in trades_df.columns:
            available_coins = sorted(trades_df['asset'].unique())
    
    selected_coins = st.sidebar.multiselect(
        "العملات",
        options=available_coins,
        default=available_coins[:5] if len(available_coins) > 5 else available_coins
    )
    
    # Amount filter
    min_amount = st.sidebar.number_input(
        "الحد الأدنى للمبلغ",
        value=0.0,
        min_value=0.0,
        step=10.0
    )
    
    # PnL filter
    pnl_filter = st.sidebar.selectbox(
        "فلتر الربح/الخسارة",
        options=["الكل", "صفقات رابحة فقط", "صفقات خاسرة فقط"],
        index=0
    )
    
    # Refresh button
    if st.sidebar.button("🔄 تحديث البيانات"):
        st.cache_data.clear()
        st.rerun()
    
    # Apply filters
    filtered_trades = trades_df.copy()
    filtered_fifo = fifo_df.copy()
    
    filtered_trades = filter_data_by_date(filtered_trades, date_range)
    filtered_fifo = filter_data_by_date(filtered_fifo, date_range, 'sell_time' if 'sell_time' in filtered_fifo.columns else 'sellTime')
    filtered_trades = filter_data_by_coins(filtered_trades, selected_coins)
    filtered_fifo = filter_data_by_coins(filtered_fifo, selected_coins, 'symbol' if 'symbol' in filtered_fifo.columns else 'asset')
    filtered_trades = filter_data_by_amount(filtered_trades, min_amount, 'quantity' if 'quantity' in filtered_trades.columns else 'amount')
    filtered_fifo = filter_data_by_pnl(filtered_fifo, pnl_filter)
    
    # Calculate advanced metrics
    with st.spinner("🧮 جاري حساب المؤشرات المتقدمة..."):
        metrics = calculate_advanced_metrics(filtered_trades, filtered_fifo)
    
    # Page routing
    if page == "📊 ملخص تنفيذي":
        show_summary_page(metrics, filtered_trades, filtered_fifo, trades_df, date_range)
    elif page == "🔄 المعاملات":
        show_trades_page(filtered_trades)
    elif page == "🧮 تحليل FIFO":
        show_fifo_page(filtered_fifo)
    elif page == "📈 الرسوم البيانية المتقدمة":
        show_charts_page(filtered_trades, filtered_fifo)
    elif page == "📤 التصدير والمشاركة":
        show_export_page(filtered_trades, filtered_fifo, metrics)
    elif page == "⚠️ تحليل المخاطر":
        show_risk_analysis_page(filtered_trades, filtered_fifo, metrics)
    elif page == "💰 منتجات الاستثمار":
        show_investment_products_page(rwusd_df, bfusd_df, bnsol_df, lusdt_df, flexible_stock_df, small_assets_df)

def show_summary_page(metrics, filtered_trades, filtered_fifo, original_trades_df, date_range):
    """Show executive summary page"""
    st.header("📊 الملخص التنفيذي")
    
    # Filter summary
    st.info(f"🔍 عرض {len(filtered_trades)} صفقة من {len(original_trades_df)} إجماليًا | نطاق التاريخ: {date_range[0]} إلى {date_range[1]}")
    
    # Enhanced metrics cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "إجمالي الصفقات", 
            metrics.get('total_trades', 0),
            delta=f"+{metrics.get('total_trades', 0)}" if metrics.get('total_trades', 0) > 0 else "0"
        )
    
    with col2:
        pnl = metrics.get('realized_pnl', 0)
        st.metric(
            "الربح المحقق", 
            f"{pnl:.2f}",
            delta=f"+{pnl:.2f}" if pnl > 0 else f"{pnl:.2f}",
            delta_color="normal" if pnl >= 0 else "inverse"
        )
    
    with col3:
        fees = metrics.get('total_fees', 0)
        st.metric(
            "إجمالي الرسوم", 
            f"{fees:.2f}",
            delta=f"-{fees:.2f}" if fees > 0 else "0",
            delta_color="inverse"
        )
    
    with col4:
        net = metrics.get('net_profit', 0)
        st.metric(
            "صافي الربح", 
            f"{net:.2f}",
            delta=f"+{net:.2f}" if net >= 0 else f"{net:.2f}",
            delta_color="normal" if net >= 0 else "inverse"
        )
    
    st.markdown("---")
    
    # Advanced metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "نسبة الربح %",
            f"{metrics.get('win_rate', 0):.1f}%",
            delta="Win Rate"
        )
    
    with col2:
        st.metric(
            "معامل الربح",
            f"{metrics.get('profit_factor', 0):.2f}",
            delta="Profit Factor"
        )
    
    with col3:
        st.metric(
            "أقصى انخفاض %",
            f"{metrics.get('max_drawdown', 0):.2f}%",
            delta="Max Drawdown",
            delta_color="inverse"
        )
    
    with col4:
        st.metric(
            "مؤشر شارب",
            f"{metrics.get('sharpe_ratio', 0):.2f}",
            delta="Sharpe Ratio"
        )
    
    st.markdown("---")
    
    # Performance summary
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 إحصائيات الأداء")
        performance_data = {
            "المؤشر": ["أفضل صفقة", "متوسط الربح", "متوسط الخسارة", "أسوأ صفقة"],
            "القيمة": [
                f"{metrics.get('best_trade', 0):.2f}",
                f"{metrics.get('avg_win', 0):.2f}",
                f"{metrics.get('avg_loss', 0):.2f}",
                f"{metrics.get('worst_trade', 0):.2f}"
            ]
        }
        perf_df = pd.DataFrame(performance_data)
        st.dataframe(perf_df, use_container_width=True, hide_index=True)
    
    with col2:
        st.subheader("🎯 ملخص الحالة")
        if metrics.get('net_profit', 0) > 0:
            st.success("🎉 المحفظة في حالة ربح!")
        elif metrics.get('net_profit', 0) < 0:
            st.error("⚠️ المحفظة في حالة خسارة")
        else:
            st.info("📊 المحفظة محايدة")
        
        # Progress bar for win rate
        win_rate = metrics.get('win_rate', 0)
        st.progress(win_rate / 100, text=f"نسبة الربح: {win_rate:.1f}%")

def show_trades_page(filtered_trades):
    """Show trades page with advanced filtering"""
    st.header("🔄 المعاملات")
    
    if not filtered_trades.empty:
        # Search and filter
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_term = st.text_input("🔍 بحث في المعاملات...", placeholder="ابحث عن عملة، معرف، أو مبلغ...")
        
        with col2:
            sort_by = st.selectbox("ترتيب حسب", ["الوقت", "الكمية", "السعر", "الإجمالي"])
        
        # Apply search
        if search_term:
            search_mask = filtered_trades.astype(str).apply(
                lambda x: x.str.contains(search_term, case=False, na=False)
            ).any(axis=1)
            display_trades = filtered_trades[search_mask]
        else:
            display_trades = filtered_trades
        
        # Apply sorting
        if sort_by == "الوقت" and 'time' in display_trades.columns:
            display_trades = display_trades.sort_values('time', ascending=False)
        elif sort_by == "الكمية" and 'quantity' in display_trades.columns:
            display_trades = display_trades.sort_values('quantity', ascending=False)
        elif sort_by == "السعر" and 'price' in display_trades.columns:
            display_trades = display_trades.sort_values('price', ascending=False)
        elif sort_by == "الإجمالي" and 'quoteQty' in display_trades.columns:
            display_trades = display_trades.sort_values('quoteQty', ascending=False)
        
        # Format display
        trades_df_display = display_trades.copy()
        if 'time' in trades_df_display.columns:
            trades_df_display['time'] = pd.to_datetime(trades_df_display['time'], errors='coerce')
            trades_df_display['time'] = trades_df_display['time'].dt.strftime('%Y-%m-%d %H:%M')
        
        # Interactive table
        st.dataframe(
            trades_df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "time": st.column_config.DatetimeColumn("التاريخ", format="YYYY-MM-DD HH:mm"),
                "symbol": st.column_config.TextColumn("الزوج"),
                "quantity": st.column_config.NumberColumn("الكمية", format="%.4f"),
                "price": st.column_config.NumberColumn("السعر", format="%.4f"),
                "quoteQty": st.column_config.NumberColumn("الإجمالي", format="%.2f"),
            }
        )
        
        st.write(f"عرض {len(display_trades)} من {len(filtered_trades)} معاملة")
        
        # Download button
        csv = display_trades.to_csv(index=False)
        st.download_button(
            label="📥 تحميل المعاملات كـ CSV",
            data=csv,
            file_name=f"trades_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    else:
        st.info("لا توجد بيانات معاملات متاحة")

def show_fifo_page(filtered_fifo):
    """Show FIFO analysis page"""
    st.header("🧮 تحليل FIFO")
    
    if not filtered_fifo.empty:
        fifo_df_display = filtered_fifo.copy()
        
        # Detect time column
        time_col = None
        for col in ['sell_time', 'sellTime', 'timestamp']:
            if col in fifo_df_display.columns:
                time_col = col
                break
        
        if time_col:
            fifo_df_display[time_col] = pd.to_datetime(fifo_df_display[time_col], errors='coerce')
        
        # Interactive table
        st.dataframe(
            fifo_df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                time_col: st.column_config.DatetimeColumn("تاريخ البيع", format="YYYY-MM-DD HH:mm"),
                "symbol": st.column_config.TextColumn("العملة"),
                "realized_pnl": st.column_config.NumberColumn("الربح المحقق", format="%.2f"),
                "fee": st.column_config.NumberColumn("الرسوم", format="%.4f"),
            }
        )
        
        # Quick stats
        col1, col2, col3 = st.columns(3)
        
        with col1:
            winning_trades = len(fifo_df_display[fifo_df_display['realized_pnl'] > 0])
            st.metric("صفقات رابحة", winning_trades)
        
        with col2:
            losing_trades = len(fifo_df_display[fifo_df_display['realized_pnl'] < 0])
            st.metric("صفقات خاسرة", losing_trades)
        
        with col3:
            avg_pnl = fifo_df_display['realized_pnl'].mean()
            st.metric("متوسط الربح/الخسارة", f"{avg_pnl:.2f}")
    
    else:
        st.info("لا توجد بيانات FIFO متاحة")

def show_charts_page(filtered_trades, filtered_fifo):
    """Show advanced charts page"""
    st.header("📈 الرسوم البيانية المتقدمة")
    
    if not filtered_fifo.empty:
        # Detect time column
        time_col = None
        for col in ['sell_time', 'sellTime', 'timestamp']:
            if col in filtered_fifo.columns:
                time_col = col
                break
        
        if time_col:
            filtered_fifo[time_col] = pd.to_datetime(filtered_fifo[time_col], errors='coerce')
        
        # Chart selection
        chart_type = st.selectbox("اختر نوع الرسم البياني", [
            "الربح/الخسارة اليومية",
            "توزيع الأرباح حسب العملة",
            "الربح التراكمي",
            "تحليل حجم الصفقات",
            "مخطط التشتت (Scatter Plot)"
        ])
        
        if chart_type == "الربح/الخسارة اليومية":
            pnl_by_date = filtered_fifo.groupby(filtered_fifo[time_col].dt.date)['realized_pnl'].sum().reset_index()
            fig = px.line(
                pnl_by_date, 
                x=time_col, 
                y='realized_pnl',
                title="الربح/الخسارة اليومية",
                labels={'realized_pnl': 'الربح/الخسارة', time_col: 'التاريخ'},
                markers=True
            )
            fig.update_layout(hovermode='x unified')
            fig.add_hline(y=0, line_dash="dash", line_color="gray")
            st.plotly_chart(fig, use_container_width=True)
        
        elif chart_type == "توزيع الأرباح حسب العملة":
            pnl_by_coin = filtered_fifo.groupby('symbol')['realized_pnl'].sum().reset_index()
            pnl_by_coin = pnl_by_coin[pnl_by_coin['realized_pnl'] != 0]
            
            if not pnl_by_coin.empty:
                fig = px.bar(
                    pnl_by_coin,
                    x='symbol',
                    y='realized_pnl',
                    title="الربح/الخسارة حسب العملة",
                    labels={'realized_pnl': 'الربح/الخسارة', 'symbol': 'العملة'},
                    color='realized_pnl',
                    color_continuous_scale=['red', 'yellow', 'green']
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
        
        elif chart_type == "الربح التراكمي":
            fifo_sorted = filtered_fifo.sort_values(time_col)
            fifo_sorted['cumulative_pnl'] = fifo_sorted['realized_pnl'].cumsum()
            
            fig = px.line(
                fifo_sorted,
                x=time_col,
                y='cumulative_pnl',
                title="الربح التراكمي مع الوقت",
                labels={'cumulative_pnl': 'الربح التراكمي', time_col: 'التاريخ'}
            )
            fig.add_hline(y=0, line_dash="dash", line_color="gray")
            fig.update_layout(hovermode='x unified')
            st.plotly_chart(fig, use_container_width=True)
        
        elif chart_type == "تحليل حجم الصفقات":
            if not filtered_trades.empty:
                volume_by_date = filtered_trades.groupby(filtered_trades['time'].dt.date)['quoteQty'].sum().reset_index()
                fig = px.bar(
                    volume_by_date,
                    x='time',
                    y='quoteQty',
                    title="حجم التداول اليومي",
                    labels={'quoteQty': 'حجم التداول', 'time': 'التاريخ'}
                )
                st.plotly_chart(fig, use_container_width=True)
        
        elif chart_type == "مخطط التشتت (Scatter Plot)":
            if not filtered_trades.empty and 'price' in filtered_trades.columns and 'quantity' in filtered_trades.columns:
                fig = px.scatter(
                    filtered_trades,
                    x='price',
                    y='quantity',
                    color='symbol',
                    size='quoteQty',
                    title="مخطط التشتت للسعر مقابل الكمية",
                    labels={'price': 'السعر', 'quantity': 'الكمية', 'quoteQty': 'الإجمالي'},
                    hover_data=['time']
                )
                st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.info("لا توجد بيانات كافية للرسوم البيانية")

def show_export_page(filtered_trades, filtered_fifo, metrics):
    """Show export and sharing page"""
    st.header("📤 التصدير والمشاركة")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📥 تصدير البيانات")
        
        # Export trades
        if not filtered_trades.empty:
            csv_trades = filtered_trades.to_csv(index=False)
            st.download_button(
                label="📊 تحميل المعاملات",
                data=csv_trades,
                file_name=f"trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        # Export FIFO
        if not filtered_fifo.empty:
            csv_fifo = filtered_fifo.to_csv(index=False)
            st.download_button(
                label="🧮 تحليل FIFO",
                data=csv_fifo,
                file_name=f"fifo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        # Export summary
        summary_data = {
            "المؤشر": ["إجمالي الصفقات", "الربح المحقق", "إجمالي الرسوم", "صافي الربح", "نسبة الربح", "معامل الربح"],
            "القيمة": [
                metrics.get('total_trades', 0),
                f"{metrics.get('realized_pnl', 0):.2f}",
                f"{metrics.get('total_fees', 0):.2f}",
                f"{metrics.get('net_profit', 0):.2f}",
                f"{metrics.get('win_rate', 0):.1f}%",
                f"{metrics.get('profit_factor', 0):.2f}"
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        csv_summary = summary_df.to_csv(index=False)
        st.download_button(
            label="📋 الملخص التنفيذي",
            data=csv_summary,
            file_name=f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col2:
        st.subheader("🔗 مشاركة التقارير")
        
        # Generate report link (placeholder)
        st.info("🔗 رابط المشاركة:")
        st.code(f"https://crypto-dashboard.app/share/{datetime.now().strftime('%Y%m%d')}")
        
        st.button("📧 إرسال بالبريد الإلكتروني")
        st.button("📱 مشاركة عبر WhatsApp")
        
        # Export settings
        st.subheader("⚙️ إعدادات التصدير")
        include_charts = st.checkbox("تضمين الرسوم البيانية", value=True)
        include_summary = st.checkbox("تضمين الملخص", value=True)
        date_format = st.selectbox("تنسيق التاريخ", ["YYYY-MM-DD", "DD/MM/YYYY", "MM/DD/YYYY"])
        
        if st.button("📦 إنشاء حزمة تقارير"):
            st.success("✅ جاري إنشاء حزمة التقارير...")

def show_risk_analysis_page(filtered_trades, filtered_fifo, metrics):
    """Show risk analysis page"""
    st.header("⚠️ تحليل المخاطر")
    
    if not filtered_fifo.empty:
        # Risk metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "أقصى انخفاض %",
                f"{metrics.get('max_drawdown', 0):.2f}%",
                delta="Max Drawdown",
                delta_color="inverse"
            )
        
        with col2:
            st.metric(
                "مؤشر شارب",
                f"{metrics.get('sharpe_ratio', 0):.2f}",
                delta="Sharpe Ratio"
            )
        
        with col3:
            volatility = filtered_fifo['realized_pnl'].std() if not filtered_fifo.empty else 0
            st.metric(
                "التقلب",
                f"{volatility:.2f}",
                delta="Volatility"
            )
        
        with col4:
            st.metric(
                "معامل الربح",
                f"{metrics.get('profit_factor', 0):.2f}",
                delta="Profit Factor"
            )
        
        st.markdown("---")
        
        # Risk charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📉 تحليل الانخفاض")
            if 'sell_time' in filtered_fifo.columns or 'sellTime' in filtered_fifo.columns:
                time_col = 'sell_time' if 'sell_time' in filtered_fifo.columns else 'sellTime'
                fifo_sorted = filtered_fifo.sort_values(time_col)
                fifo_sorted['cumulative_pnl'] = fifo_sorted['realized_pnl'].cumsum()
                running_max = fifo_sorted['cumulative_pnl'].expanding().max()
                drawdown = (fifo_sorted['cumulative_pnl'] - running_max) / running_max * 100
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=fifo_sorted[time_col],
                    y=drawdown,
                    fill='tozeroy',
                    mode='lines',
                    name='Drawdown',
                    line=dict(color='red')
                ))
                fig.update_layout(
                    title="تحليل الانخفاض (Drawdown)",
                    xaxis_title="التاريخ",
                    yaxis_title="الانخفاض (%)",
                    hovermode='x unified'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("📊 توزيع الأرباح/الخسائر")
            pnl_data = filtered_fifo['realized_pnl']
            
            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=pnl_data,
                nbinsx=20,
                name='PnL Distribution',
                marker_color='lightblue'
            ))
            fig.add_vline(x=pnl_data.mean(), line_dash="dash", line_color="red", annotation_text="المتوسط")
            fig.update_layout(
                title="توزيع الأرباح والخسائر",
                xaxis_title="الربح/الخسارة",
                yaxis_title="التكرار"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Risk recommendations
        st.subheader("🎯 توصيات إدارة المخاطر")
        
        risk_score = 0
        if metrics.get('max_drawdown', 0) < -10:
            risk_score += 2
            st.warning("⚠️ الانخفاض مرتفع - يوصى بمراجعة استراتيجية إدارة المخاطر")
        
        if metrics.get('sharpe_ratio', 0) < 1:
            risk_score += 1
            st.info("📊 مؤشر شارب منخفض - يمكن تحسين العائد مقابل المخاطرة")
        
        if metrics.get('profit_factor', 0) < 1.5:
            risk_score += 1
            st.warning("⚠️ معامل الربح منخفض - يجب تحسين نسبة الأرباح للخسائر")
        
        if risk_score == 0:
            st.success("✅ مستوى المخاطرة معقول ومقبول")
        elif risk_score <= 2:
            st.info("📊 مستوى المخاطرة متوسط - يوصى بمراقبة الأداء")
        else:
            st.error("🚨 مستوى المخاطرة مرتفع - يوصى بتعديل الاستراتيجية")
    
    else:
        st.info("لا توجد بيانات كافية لتحليل المخاطر")

def show_investment_products_page(rwusd_df, bfusd_df, bnsol_df, lusdt_df, flexible_stock_df, small_assets_df):
    """Show investment products page"""
    st.header("💰 منتجات الاستثمار")
    
    # Product summary cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        rwusd_total = rwusd_df[rwusd_df['type'] == 'account']['total_amount'].sum() if not rwusd_df.empty else 0
        st.metric("RWUSD", f"${rwusd_total:,.2f}", help="Reward Wrapped USD")
    
    with col2:
        bfusd_total = bfusd_df[bfusd_df['type'] == 'account']['total_amount'].sum() if not bfusd_df.empty else 0
        st.metric("BFUSD", f"${bfusd_total:,.2f}", help="Binance Flexible USD")
    
    with col3:
        bnsol_total = bnsol_df[bnsol_df['type'] == 'account']['total_amount'].sum() if not bnsol_df.empty else 0
        st.metric("BNSOL", f"{bnsol_total:.4f} SOL", help="Binance Staked SOL")
    
    st.markdown("---")
    
    # Detailed product tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📄 RWUSD", "💵 BFUSD", "🌟 BNSOL", "🔶 LUSDT", "📈 Flexible Stock", "🔄 Small Assets"
    ])
    
    with tab1:
        st.subheader("📄 RWUSD - Reward Wrapped USD")
        if not rwusd_df.empty:
            # Filter for account data
            account_data = rwusd_df[rwusd_df['type'] == 'account']
            if not account_data.empty:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("الإجمالي", f"${account_data['total_amount'].iloc[0]:,.2f}")
                    st.metric("المتاح", f"${account_data['available_amount'].iloc[0]:,.2f}")
                with col2:
                    st.metric("العائد", f"${account_data['interest_amount'].iloc[0]:,.2f}")
                    st.metric("الحالة", account_data['status'].iloc[0])
            
            # Rewards history
            rewards_data = rwusd_df[rwusd_df['type'] == 'reward']
            if not rewards_data.empty:
                st.subheader("سجل المكافآت")
                rewards_data['time'] = pd.to_datetime(rewards_data['time'], errors='coerce')
                st.dataframe(rewards_data.sort_values('time', ascending=False), use_container_width=True)
        else:
            st.info("لا توجد بيانات RWUSD متاحة")
    
    with tab2:
        st.subheader("💵 BFUSD - Binance Flexible USD")
        if not bfusd_df.empty:
            # Account summary
            account_data = bfusd_df[bfusd_df['type'] == 'account']
            if not account_data.empty:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("الإجمالي", f"${account_data['total_amount'].iloc[0]:,.2f}")
                    st.metric("المتاح", f"${account_data['available_amount'].iloc[0]:,.2f}")
                with col2:
                    st.metric("العائد", f"${account_data['interest_amount'].iloc[0]:,.2f}")
                    st.metric("نسبة العائد السنوي", f"{account_data['annual_percentage_rate'].iloc[0]:.2f}%")
            
            # Activity chart
            activity_data = bfusd_df.groupby('type').size()
            if not activity_data.empty:
                st.subheader("نشاط المنتج")
                fig = px.pie(
                    values=activity_data.values,
                    names=activity_data.index,
                    title="توزيع الأنشطة"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Recent transactions
            recent_data = bfusd_df[bfusd_df['type'].isin(['subscription', 'redemption', 'reward'])]
            if not recent_data.empty:
                st.subheader("المعاملات الأخيرة")
                recent_data['time'] = pd.to_datetime(recent_data['time'], errors='coerce')
                st.dataframe(recent_data.sort_values('time', ascending=False).head(10), use_container_width=True)
        else:
            st.info("لا توجد بيانات BFUSD متاحة")
    
    with tab3:
        st.subheader("🌟 BNSOL - Binance Staked SOL")
        if not bnsol_df.empty:
            # Account summary
            account_data = bnsol_df[bnsol_df['type'] == 'account']
            if not account_data.empty:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("الإجمالي", f"{account_data['total_amount'].iloc[0]:.4f} SOL")
                    st.metric("المتاح", f"{account_data['available_amount'].iloc[0]:.4f} SOL")
                with col2:
                    st.metric("العائد", f"{account_data['interest_amount'].iloc[0]:.4f} SOL")
                    st.metric("نسبة العائد السنوي", f"{account_data['apy'].iloc[0]:.2f}%")
            
            # Rewards chart
            rewards_data = bnsol_df[bnsol_df['type'] == 'reward']
            if not rewards_data.empty:
                st.subheader("مكافآت الستاكينغ")
                rewards_data['time'] = pd.to_datetime(rewards_data['time'], errors='coerce')
                rewards_data['date'] = rewards_data['time'].dt.date
                daily_rewards = rewards_data.groupby('date')['amount'].sum()
                
                fig = px.line(
                    x=daily_rewards.index,
                    y=daily_rewards.values,
                    title="مكافآت SOL اليومية",
                    labels={'x': 'التاريخ', 'y': 'مقدار SOL'}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Recent activity
            recent_data = bnsol_df[bnsol_df['type'].isin(['subscription', 'redemption', 'reward'])]
            if not recent_data.empty:
                st.subheader("النشاط الأخير")
                recent_data['time'] = pd.to_datetime(recent_data['time'], errors='coerce')
                st.dataframe(recent_data.sort_values('time', ascending=False).head(10), use_container_width=True)
        else:
            st.info("لا توجد بيانات BNSOL متاحة")
    
    with tab4:
        st.subheader("🔶 LUSDT - Locked USDT")
        if not lusdt_df.empty:
            st.dataframe(lusdt_df, use_container_width=True)
        else:
            st.info("لا توجد بيانات LUSDT متاحة")
    
    with tab5:
        st.subheader("📈 Flexible Stock")
        if not flexible_stock_df.empty:
            st.dataframe(flexible_stock_df, use_container_width=True)
        else:
            st.info("لا توجد بيانات Flexible Stock متاحة")
    
    with tab6:
        st.subheader("🔄 Small Assets Conversion")
        if not small_assets_df.empty:
            st.dataframe(small_assets_df, use_container_width=True)
        else:
            st.info("لا توجد بيانات Small Assets متاحة")
    
    # Export section
    st.markdown("---")
    st.subheader("📤 تصدير بيانات المنتجات")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if not rwusd_df.empty:
            csv = rwusd_df.to_csv(index=False)
            st.download_button("📥 RWUSD", data=csv, file_name="rwusd_data.csv", mime="text/csv")
    
    with col2:
        if not bfusd_df.empty:
            csv = bfusd_df.to_csv(index=False)
            st.download_button("📥 BFUSD", data=csv, file_name="bfusd_data.csv", mime="text/csv")
    
    with col3:
        if not bnsol_df.empty:
            csv = bnsol_df.to_csv(index=False)
            st.download_button("📥 BNSOL", data=csv, file_name="bnsol_data.csv", mime="text/csv")

# ==================================================
# Entry Point
# ==================================================
if __name__ == "__main__":
    main()
