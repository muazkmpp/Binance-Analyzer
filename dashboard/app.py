import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from config.settings import REPORT_FILE, DB_FILE

# ==================================================
# Ensure REPORT_FILE is a Path object
# ==================================================
REPORT_FILE = Path(REPORT_FILE)

# ==================================================
# Helper to load Excel data safely with caching
# ==================================================

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data():
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

    if not any(not df.empty for df in [summary_db, fifo_db, trades_db, binance_pay_db, deposits_db, withdrawals_db, simple_earn_db]) and not REPORT_FILE.exists():
        st.warning("No report or SQLite data found. Generate data first.")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    if any(not df.empty for df in [summary_db, fifo_db, trades_db, binance_pay_db, deposits_db, withdrawals_db, simple_earn_db]):
        return summary_db, fifo_db, trades_db, binance_pay_db, deposits_db, withdrawals_db, simple_earn_db

    xls = pd.ExcelFile(REPORT_FILE)
    st.write("Available sheets:", xls.sheet_names)

    # Case-insensitive search for sheets
    summary_sheets = [s for s in xls.sheet_names if "summary" in s.lower()]
    fifo_sheets = [s for s in xls.sheet_names if "fifo" in s.lower()]
    trades_sheets = [s for s in xls.sheet_names if "trade" in s.lower()]
    binance_pay_sheets = [s for s in xls.sheet_names if "binance pay" in s.lower()]
    deposits_sheets = [s for s in xls.sheet_names if "deposit" in s.lower()]
    withdrawals_sheets = [s for s in xls.sheet_names if "withdrawal" in s.lower()]
    simple_earn_sheets = [s for s in xls.sheet_names if "simple earn" in s.lower()]

    # Load all available data
    summary_df = pd.read_excel(REPORT_FILE, sheet_name=summary_sheets[0]) if summary_sheets else pd.DataFrame()
    fifo_df = pd.read_excel(REPORT_FILE, sheet_name=fifo_sheets[0]) if fifo_sheets else pd.DataFrame()
    trades_df = pd.read_excel(REPORT_FILE, sheet_name=trades_sheets[0]) if trades_sheets else pd.DataFrame()
    binance_pay_df = pd.read_excel(REPORT_FILE, sheet_name=binance_pay_sheets[0]) if binance_pay_sheets else pd.DataFrame()
    deposits_df = pd.read_excel(REPORT_FILE, sheet_name=deposits_sheets[0]) if deposits_sheets else pd.DataFrame()
    withdrawals_df = pd.read_excel(REPORT_FILE, sheet_name=withdrawals_sheets[0]) if withdrawals_sheets else pd.DataFrame()
    simple_earn_df = pd.read_excel(REPORT_FILE, sheet_name=simple_earn_sheets[0]) if simple_earn_sheets else pd.DataFrame()

    return summary_df, fifo_df, trades_df, binance_pay_df, deposits_df, withdrawals_df, simple_earn_df

# ==================================================
# Load Data
# ==================================================
summary_df, fifo_df, trades_df, binance_pay_df, deposits_df, withdrawals_df, simple_earn_df = load_data()

st.set_page_config(page_title="Crypto Dashboard", layout="wide", initial_sidebar_state="expanded")
st.title("📊 Crypto Investment Dashboard")

# ==================================================
# Interactive Filters Sidebar
# ==================================================
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

# PnL filter for FIFO data
pnl_filter = st.sidebar.selectbox(
    "فلتر الربح/الخسارة",
    options=["الكل", "صفقات رابحة فقط", "صفقات خاسرة فقط"],
    index=0
)

# Refresh button
if st.sidebar.button("🔄 تحديث البيانات"):
    st.cache_data.clear()
    st.rerun()

# ==================================================
# Filter Data Functions
# ==================================================
def filter_data_by_date(df, date_range, date_col='time'):
    if df.empty or date_col not in df.columns:
        return df
    
    df_copy = df.copy()
    df_copy[date_col] = pd.to_datetime(df_copy[date_col], errors='coerce')
    start_date = pd.to_datetime(date_range[0])
    end_date = pd.to_datetime(date_range[1]) + timedelta(days=1)  # Include end date
    
    return df_copy[(df_copy[date_col] >= start_date) & (df_copy[date_col] < end_date)]

def filter_data_by_coins(df, selected_coins, symbol_col='symbol'):
    if df.empty or not selected_coins or symbol_col not in df.columns:
        return df
    
    # Handle different symbol formats
    df_copy = df.copy()
    if symbol_col == 'symbol':
        # Convert USDT pairs to coin names
        df_copy['coin'] = df_copy[symbol_col].str.replace('USDT', '')
        return df_copy[df_copy['coin'].isin(selected_coins)]
    else:
        return df_copy[df_copy[symbol_col].isin(selected_coins)]

def filter_data_by_amount(df, min_amount, amount_col='quantity'):
    if df.empty or amount_col not in df.columns:
        return df
    
    return df[df[amount_col] >= min_amount]

def filter_data_by_pnl(df, pnl_filter):
    if df.empty or 'realized_pnl' not in df.columns:
        return df
    
    if pnl_filter == "صفقات رابحة فقط":
        return df[df['realized_pnl'] > 0]
    elif pnl_filter == "صفقات خاسرة فقط":
        return df[df['realized_pnl'] < 0]
    return df

# Apply filters to all data
filtered_trades = trades_df.copy()
filtered_fifo = fifo_df.copy()

# Apply date filter
filtered_trades = filter_data_by_date(filtered_trades, date_range)
filtered_fifo = filter_data_by_date(filtered_fifo, date_range, 'sell_time' if 'sell_time' in filtered_fifo.columns else 'sellTime')

# Apply coin filter
filtered_trades = filter_data_by_coins(filtered_trades, selected_coins)
filtered_fifo = filter_data_by_coins(filtered_fifo, selected_coins, 'symbol' if 'symbol' in filtered_fifo.columns else 'asset')

# Apply amount filter
filtered_trades = filter_data_by_amount(filtered_trades, min_amount, 'quantity' if 'quantity' in filtered_trades.columns else 'amount')

# Apply PnL filter
filtered_fifo = filter_data_by_pnl(filtered_fifo, pnl_filter)

# ==================================================
# Calculate filtered metrics
# ==================================================
def calculate_filtered_metrics(trades_df, fifo_df):
    total_trades = len(trades_df)
    realized_pnl = fifo_df['realized_pnl'].sum() if not fifo_df.empty and 'realized_pnl' in fifo_df.columns else 0
    total_fees = fifo_df['fee'].sum() if not fifo_df.empty and 'fee' in fifo_df.columns else 0
    
    # Calculate deltas (compare with previous period)
    delta_trades = f"+{total_trades}" if total_trades > 0 else "0"
    delta_pnl = f"+{realized_pnl:.2f}" if realized_pnl > 0 else f"{realized_pnl:.2f}"
    
    return total_trades, realized_pnl, total_fees, delta_trades, delta_pnl

total_trades, realized_pnl, total_fees, delta_trades, delta_pnl = calculate_filtered_metrics(filtered_trades, filtered_fifo)

# ==================================================
# Enhanced Summary Cards
# ==================================================
col1, col2, col3, col4 = st.columns(4)
col1.metric(
    "إجمالي الصفقات", 
    total_trades, 
    delta=delta_trades,
    delta_color="normal" if total_trades >= 0 else "inverse"
)
col2.metric(
    "الربح المحقق", 
    f"{realized_pnl:.2f}", 
    delta=delta_pnl,
    delta_color="normal" if realized_pnl >= 0 else "inverse"
)
col3.metric(
    "إجمالي الرسوم", 
    f"{total_fees:.2f}",
    delta=f"-{total_fees:.2f}" if total_fees > 0 else "0",
    delta_color="inverse"
)
col4.metric(
    "صافي الربح", 
    f"{realized_pnl - total_fees:.2f}",
    delta=f"+{realized_pnl - total_fees:.2f}" if realized_pnl - total_fees >= 0 else f"{realized_pnl - total_fees:.2f}",
    delta_color="normal" if realized_pnl - total_fees >= 0 else "inverse"
)

# Show filter summary
st.info(f"🔍 عرض {len(filtered_trades)} صفقة من {len(trades_df)} إجماليًا | نطاق التاريخ: {date_range[0]} إلى {date_range[1]}")

st.markdown("---")

# ==================================================
# Enhanced Spot Trades Table with Search
# ==================================================
st.subheader("🔄 Spot Trades")
if not filtered_trades.empty:
    # Search box
    search_term = st.text_input("🔍 بحث في المعاملات...", placeholder="ابحث عن عملة، معرف، أو مبلغ...")
    
    # Apply search
    if search_term:
        search_mask = filtered_trades.astype(str).apply(
            lambda x: x.str.contains(search_term, case=False, na=False)
        ).any(axis=1)
        display_trades = filtered_trades[search_mask]
    else:
        display_trades = filtered_trades
    
    # Format display
    trades_df_display = display_trades.copy()
    if 'time' in trades_df_display.columns:
        trades_df_display['time'] = pd.to_datetime(trades_df_display['time'], errors='coerce')
        trades_df_display['time'] = trades_df_display['time'].dt.strftime('%Y-%m-%d %H:%M')
    
    # Interactive table with sorting
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
else:
    st.info("No Spot Trades data available.")

st.markdown("---")

# ==================================================
# Enhanced FIFO Details with Advanced Charts
# ==================================================
st.subheader("🧮 FIFO Details")
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

    # Advanced Charts Section
    st.markdown("### 📈 الرسوم البيانية المتقدمة")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**الربح/الخسارة حسب التاريخ**")
        if 'realized_pnl' in fifo_df_display.columns and time_col:
            pnl_by_date = fifo_df_display.groupby(fifo_df_display[time_col].dt.date)['realized_pnl'].sum().reset_index()
            fig_pnl = px.line(
                pnl_by_date, 
                x=time_col, 
                y='realized_pnl',
                title="الربح/الخسارة اليومية",
                labels={'realized_pnl': 'الربح/الخسارة', time_col: 'التاريخ'},
                markers=True
            )
            fig_pnl.update_layout(hovermode='x unified')
            fig_pnl.add_hline(y=0, line_dash="dash", line_color="gray")
            st.plotly_chart(fig_pnl, use_container_width=True)
    
    with col2:
        st.markdown("**توزيع الأرباح حسب العملة**")
        if 'symbol' in fifo_df_display.columns and 'realized_pnl' in fifo_df_display.columns:
            pnl_by_coin = fifo_df_display.groupby('symbol')['realized_pnl'].sum().reset_index()
            pnl_by_coin = pnl_by_coin[pnl_by_coin['realized_pnl'] != 0]  # Exclude zero PnL
            
            if not pnl_by_coin.empty:
                fig_coin = px.bar(
                    pnl_by_coin,
                    x='symbol',
                    y='realized_pnl',
                    title="الربح/الخسارة حسب العملة",
                    labels={'realized_pnl': 'الربح/الخسارة', 'symbol': 'العملة'},
                    color='realized_pnl',
                    color_continuous_scale=['red', 'yellow', 'green']
                )
                fig_coin.update_layout(showlegend=False)
                st.plotly_chart(fig_coin, use_container_width=True)
    
    # Additional chart: Cumulative PnL
    st.markdown("**الربح التراكمي**")
    if 'realized_pnl' in fifo_df_display.columns and time_col:
        fifo_sorted = fifo_df_display.sort_values(time_col)
        fifo_sorted['cumulative_pnl'] = fifo_sorted['realized_pnl'].cumsum()
        
        fig_cumulative = px.line(
            fifo_sorted,
            x=time_col,
            y='cumulative_pnl',
            title="الربح التراكمي مع الوقت",
            labels={'cumulative_pnl': 'الربح التراكمي', time_col: 'التاريخ'}
        )
        fig_cumulative.add_hline(y=0, line_dash="dash", line_color="gray")
        fig_cumulative.update_layout(hovermode='x unified')
        st.plotly_chart(fig_cumulative, use_container_width=True)
        
else:
    st.info("No FIFO data available yet. Run FIFO calculation first.")
