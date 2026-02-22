import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
import sqlite3

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Simple fallback configuration
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
# Custom CSS
# ==================================================
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
    }
</style>
""", unsafe_allow_html=True)

# ==================================================
# Helper functions
# ==================================================

@st.cache_data(ttl=300)
def load_data():
    """Load data with error handling"""
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

    if not summary_db.empty or not fifo_db.empty or not trades_db.empty:
        return summary_db, fifo_db, trades_db

    if not REPORT_FILE.exists():
        st.warning("No report or SQLite data found. Please run 'python main.py' first to generate data.")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    try:
        xls = pd.ExcelFile(REPORT_FILE)
        
        # Find sheets
        summary_sheets = [s for s in xls.sheet_names if "summary" in s.lower()]
        fifo_sheets = [s for s in xls.sheet_names if "fifo" in s.lower()]
        trades_sheets = [s for s in xls.sheet_names if "trade" in s.lower()]
        
        # Load data
        summary_df = pd.read_excel(REPORT_FILE, sheet_name=summary_sheets[0]) if summary_sheets else pd.DataFrame()
        fifo_df = pd.read_excel(REPORT_FILE, sheet_name=fifo_sheets[0]) if fifo_sheets else pd.DataFrame()
        trades_df = pd.read_excel(REPORT_FILE, sheet_name=trades_sheets[0]) if trades_sheets else pd.DataFrame()
        
        return summary_df, fifo_df, trades_df
    
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def calculate_metrics(trades_df, fifo_df):
    """Calculate basic metrics"""
    metrics = {}
    
    if not trades_df.empty:
        metrics['total_trades'] = len(trades_df)
    
    if not fifo_df.empty and 'realized_pnl' in fifo_df.columns:
        metrics['realized_pnl'] = fifo_df['realized_pnl'].sum()
        metrics['total_fees'] = fifo_df.get('fee', pd.Series([0])).sum()
        metrics['net_profit'] = metrics['realized_pnl'] - metrics['total_fees']
        
        # Win rate
        winning_trades = len(fifo_df[fifo_df['realized_pnl'] > 0])
        metrics['win_rate'] = (winning_trades / len(fifo_df) * 100) if len(fifo_df) > 0 else 0
    
    return metrics

def filter_data(df, date_range=None, coins=None, min_amount=0):
    """Filter data"""
    if df.empty:
        return df
    
    filtered_df = df.copy()
    
    # Date filter
    if date_range and 'time' in filtered_df.columns:
        filtered_df['time'] = pd.to_datetime(filtered_df['time'], errors='coerce')
        start_date = pd.to_datetime(date_range[0])
        end_date = pd.to_datetime(date_range[1]) + timedelta(days=1)
        filtered_df = filtered_df[(filtered_df['time'] >= start_date) & (filtered_df['time'] < end_date)]
    
    # Coin filter
    if coins and 'symbol' in filtered_df.columns:
        filtered_df['coin'] = filtered_df['symbol'].str.replace('USDT', '')
        filtered_df = filtered_df[filtered_df['coin'].isin(coins)]
    
    # Amount filter
    if min_amount > 0 and 'quantity' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['quantity'] >= min_amount]
    
    return filtered_df

# ==================================================
# Main App
# ==================================================
def main():
    # Load data
    with st.spinner("🔄 جاري تحميل البيانات..."):
        summary_df, fifo_df, trades_df = load_data()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📊 Crypto Investment Dashboard</h1>
        <p>نظام متقدم لتحليل الاستثمار في العملات المشفرة</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.header("🔍 الفلاتر")
    
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
    if not trades_df.empty and 'symbol' in trades_df.columns:
        available_coins = sorted(trades_df['symbol'].str.replace('USDT', '').unique())
    
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
    
    # Refresh button
    if st.sidebar.button("🔄 تحديث البيانات"):
        st.cache_data.clear()
        st.rerun()
    
    # Apply filters
    filtered_trades = filter_data(trades_df, date_range, selected_coins, min_amount)
    filtered_fifo = filter_data(fifo_df, date_range, selected_coins, min_amount)
    
    # Calculate metrics
    metrics = calculate_metrics(filtered_trades, filtered_fifo)
    
    # Main content
    if not filtered_trades.empty or not filtered_fifo.empty:
        # Summary cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "إجمالي الصفقات", 
                metrics.get('total_trades', 0)
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
                f"{fees:.2f}"
            )
        
        with col4:
            net = metrics.get('net_profit', 0)
            st.metric(
                "صافي الربح", 
                f"{net:.2f}",
                delta=f"+{net:.2f}" if net >= 0 else f"{net:.2f}",
                delta_color="normal" if net >= 0 else "inverse"
            )
        
        # Additional metrics
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                "نسبة الربح %",
                f"{metrics.get('win_rate', 0):.1f}%"
            )
        
        with col2:
            profit_factor = 0
            if not filtered_fifo.empty and 'realized_pnl' in filtered_fifo.columns:
                gross_profit = filtered_fifo[filtered_fifo['realized_pnl'] > 0]['realized_pnl'].sum()
                gross_loss = abs(filtered_fifo[filtered_fifo['realized_pnl'] < 0]['realized_pnl'].sum())
                profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
            
            st.metric(
                "معامل الربح",
                f"{profit_factor:.2f}"
            )
        
        st.markdown("---")
        
        # Tabs
        tab1, tab2, tab3 = st.tabs(["🔄 المعاملات", "🧮 تحليل FIFO", "📈 الرسوم البيانية"])
        
        with tab1:
            st.subheader("المعاملات")
            
            if not filtered_trades.empty:
                # Search
                search_term = st.text_input("🔍 بحث...", placeholder="ابحث عن عملة، معرف، أو مبلغ...")
                
                if search_term:
                    search_mask = filtered_trades.astype(str).apply(
                        lambda x: x.str.contains(search_term, case=False, na=False)
                    ).any(axis=1)
                    display_trades = filtered_trades[search_mask]
                else:
                    display_trades = filtered_trades
                
                # Format display
                trades_display = display_trades.copy()
                if 'time' in trades_display.columns:
                    trades_display['time'] = pd.to_datetime(trades_display['time'], errors='coerce')
                    trades_display['time'] = trades_display['time'].dt.strftime('%Y-%m-%d %H:%M')
                
                st.dataframe(trades_display, use_container_width=True, hide_index=True)
                
                # Download
                csv = display_trades.to_csv(index=False)
                st.download_button(
                    label="📥 تحميل المعاملات",
                    data=csv,
                    file_name=f"trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("لا توجد بيانات معاملات متاحة")
        
        with tab2:
            st.subheader("تحليل FIFO")
            
            if not filtered_fifo.empty:
                fifo_display = filtered_fifo.copy()
                
                # Format time
                time_col = None
                for col in ['sell_time', 'sellTime', 'timestamp']:
                    if col in fifo_display.columns:
                        time_col = col
                        fifo_display[col] = pd.to_datetime(fifo_display[col], errors='coerce')
                        break
                
                st.dataframe(fifo_display, use_container_width=True, hide_index=True)
                
                # Quick stats
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    winning = len(fifo_display[fifo_display['realized_pnl'] > 0])
                    st.metric("صفقات رابحة", winning)
                
                with col2:
                    losing = len(fifo_display[fifo_display['realized_pnl'] < 0])
                    st.metric("صفقات خاسرة", losing)
                
                with col3:
                    avg_pnl = fifo_display['realized_pnl'].mean()
                    st.metric("متوسط الربح/الخسارة", f"{avg_pnl:.2f}")
            else:
                st.info("لا توجد بيانات FIFO متاحة")
        
        with tab3:
            st.subheader("الرسوم البيانية")
            
            if not filtered_fifo.empty:
                # PnL chart
                time_col = None
                for col in ['sell_time', 'sellTime', 'timestamp']:
                    if col in filtered_fifo.columns:
                        time_col = col
                        break
                
                if time_col:
                    filtered_fifo[time_col] = pd.to_datetime(filtered_fifo[time_col], errors='coerce')
                    
                    # Daily PnL
                    pnl_by_date = filtered_fifo.groupby(filtered_fifo[time_col].dt.date)['realized_pnl'].sum().reset_index()
                    
                    fig = px.line(
                        pnl_by_date, 
                        x=time_col, 
                        y='realized_pnl',
                        title="الربح/الخسارة اليومية",
                        markers=True
                    )
                    fig.add_hline(y=0, line_dash="dash", line_color="gray")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # PnL by coin
                    if 'symbol' in filtered_fifo.columns:
                        pnl_by_coin = filtered_fifo.groupby('symbol')['realized_pnl'].sum().reset_index()
                        pnl_by_coin = pnl_by_coin[pnl_by_coin['realized_pnl'] != 0]
                        
                        if not pnl_by_coin.empty:
                            fig2 = px.bar(
                                pnl_by_coin,
                                x='symbol',
                                y='realized_pnl',
                                title="الربح/الخسارة حسب العملة",
                                color='realized_pnl',
                                color_continuous_scale=['red', 'yellow', 'green']
                            )
                            st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("لا توجد بيانات كافية للرسوم البيانية")
        
        # Filter summary
        st.info(f"🔍 عرض {len(filtered_trades)} صفقة من {len(trades_df)} إجماليًا | نطاق التاريخ: {date_range[0]} إلى {date_range[1]}")
    
    else:
        st.warning("⚠️ لا توجد بيانات متاحة. يرجى تشغيل 'python main.py' أولاً لإنشاء التقرير.")
        
        # Instructions
        st.markdown("""
        ### 📋 كيفية إنشاء البيانات:
        
        1. **تشغيل جميع العمليات:**
           ```bash
           python main.py
           ```
        
        2. **أو تشغيل العمليات بشكل منفصل:**
           ```bash
           python main.py --fetch    # جلب البيانات
           python main.py --fifo     # حساب FIFO
           python main.py --portfolio # حساب المحفظة
           python main.py --report   # إنشاء التقارير
           ```
        
        3. **أو استخدام تطبيق سطح المكتب:**
           ```bash
           python app_desktop.py
           ```
        
        بعد تشغيل إحدى هذه الأوامر، أعد تحديث لوحة التحكم لعرض البيانات.
        """)

if __name__ == "__main__":
    main()
