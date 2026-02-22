import io
import os
import sqlite3
import sys
from datetime import datetime

import pandas as pd
import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import DB_FILE  # noqa: E402


st.set_page_config(page_title="Dashboard Tables", layout="wide", page_icon="🗂️")
st.title("🗂️ Dashboard Tables")
st.caption("عرض جداول SQLite + تقارير محاسبية وتحليلية + تصدير Excel حسب الاختيار")


def get_table_names():
    try:
        with sqlite3.connect(DB_FILE) as conn:
            query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            return pd.read_sql_query(query, conn)["name"].tolist()
    except Exception:
        return []


def load_table(table_name):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            return pd.read_sql_query(f'SELECT * FROM "{table_name}"', conn)
    except Exception:
        return pd.DataFrame()


def build_reports(loaded_tables):
    reports = {}

    # 1) ملخص عام للجداول
    overview_rows = []
    for name, df in loaded_tables.items():
        overview_rows.append(
            {
                "table_name": name,
                "rows": len(df),
                "columns": len(df.columns),
            }
        )
    reports["report_tables_overview"] = pd.DataFrame(overview_rows).sort_values("table_name")

    # 2) تقرير FIFO محاسبي
    fifo_df = loaded_tables.get("fifo_results", pd.DataFrame())
    if not fifo_df.empty and "realized_pnl" in fifo_df.columns:
        fifo_work = fifo_df.copy()
        for col in ["realized_pnl", "fee", "quantity", "buy_price", "sell_price"]:
            if col in fifo_work.columns:
                fifo_work[col] = pd.to_numeric(fifo_work[col], errors="coerce")
        reports["report_fifo_by_symbol"] = (
            fifo_work.groupby("symbol", dropna=False)
            .agg(
                trades=("symbol", "count"),
                realized_pnl=("realized_pnl", "sum"),
                fee=("fee", "sum"),
                quantity=("quantity", "sum"),
            )
            .reset_index()
            .sort_values("realized_pnl", ascending=False)
        )

        time_col = "sell_time" if "sell_time" in fifo_work.columns else None
        if time_col:
            fifo_work[time_col] = pd.to_datetime(fifo_work[time_col], errors="coerce")
            monthly = fifo_work.dropna(subset=[time_col]).copy()
            if not monthly.empty:
                monthly["month"] = monthly[time_col].dt.to_period("M").astype(str)
                reports["report_fifo_monthly"] = (
                    monthly.groupby("month", dropna=False)
                    .agg(
                        trades=("symbol", "count"),
                        realized_pnl=("realized_pnl", "sum"),
                        fee=("fee", "sum"),
                    )
                    .reset_index()
                    .sort_values("month")
                )

    # 3) تقرير التداولات
    trades_df = loaded_tables.get("spot_trades", pd.DataFrame())
    if not trades_df.empty and "symbol" in trades_df.columns:
        t = trades_df.copy()
        for col in ["qty", "quantity", "price", "quoteQty"]:
            if col in t.columns:
                t[col] = pd.to_numeric(t[col], errors="coerce")
        if "quantity" not in t.columns and "qty" in t.columns:
            t["quantity"] = t["qty"]
        if "quoteQty" not in t.columns and {"quantity", "price"}.issubset(t.columns):
            t["quoteQty"] = t["quantity"] * t["price"]

        reports["report_trades_by_symbol"] = (
            t.groupby("symbol", dropna=False)
            .agg(
                trades=("symbol", "count"),
                total_qty=("quantity", "sum"),
                total_quote=("quoteQty", "sum"),
            )
            .reset_index()
            .sort_values("total_quote", ascending=False)
        )

    # 4) تقرير المحفظة
    portfolio_df = loaded_tables.get("portfolio", pd.DataFrame())
    if not portfolio_df.empty:
        p = portfolio_df.copy()
        for col in ["allocation_value", "unrealized_pnl", "total_quantity"]:
            if col in p.columns:
                p[col] = pd.to_numeric(p[col], errors="coerce")
        reports["report_portfolio_totals"] = pd.DataFrame(
            [
                {
                    "assets_count": len(p),
                    "total_allocation_value": p.get("allocation_value", pd.Series([0])).sum(),
                    "total_unrealized_pnl": p.get("unrealized_pnl", pd.Series([0])).sum(),
                    "total_quantity": p.get("total_quantity", pd.Series([0])).sum(),
                }
            ]
        )

    return reports


def to_excel_bytes(selected_dataframes):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for sheet_name, df in selected_dataframes.items():
            safe_name = sheet_name[:31]
            if df is None or df.empty:
                pd.DataFrame({"info": [f"No data in {sheet_name}"]}).to_excel(
                    writer, sheet_name=safe_name, index=False
                )
            else:
                df.to_excel(writer, sheet_name=safe_name, index=False)
    buffer.seek(0)
    return buffer.getvalue()


if not os.path.exists(DB_FILE):
    st.error(f"قاعدة البيانات غير موجودة: {DB_FILE}")
    st.info("شغّل خطوة Fetch أولًا لإنشاء البيانات داخل SQLite.")
    st.stop()


table_names = get_table_names()
if not table_names:
    st.warning("لا توجد جداول داخل SQLite حتى الآن.")
    st.stop()

st.sidebar.header("خيارات العرض")
selected_tables = st.sidebar.multiselect("اختر الجداول", table_names, default=table_names[:5])
max_rows = st.sidebar.number_input("عدد الصفوف المعروضة لكل جدول", min_value=10, max_value=1000, value=200, step=10)

loaded_tables = {name: load_table(name) for name in selected_tables}
reports = build_reports(loaded_tables)

col1, col2, col3 = st.columns(3)
col1.metric("عدد الجداول المختارة", len(selected_tables))
col2.metric("إجمالي الصفوف (المختارة)", sum(len(df) for df in loaded_tables.values()))
col3.metric("عدد التقارير المحسوبة", len(reports))

st.markdown("---")
st.subheader("📋 الجداول")
for table_name, df in loaded_tables.items():
    with st.expander(f"Table: {table_name} ({len(df)} rows)", expanded=False):
        st.dataframe(df.head(int(max_rows)), use_container_width=True, hide_index=True)

st.markdown("---")
st.subheader("📊 التقارير المحاسبية والتحليلية")
for report_name, report_df in reports.items():
    with st.expander(f"Report: {report_name} ({len(report_df)} rows)", expanded=False):
        st.dataframe(report_df, use_container_width=True, hide_index=True)

st.markdown("---")
st.subheader("📤 تصدير Excel حسب الاختيار")

export_pool = {}
for name, df in loaded_tables.items():
    export_pool[f"table_{name}"] = df
for name, df in reports.items():
    export_pool[name] = df

default_export = [k for k in export_pool.keys() if k.startswith("report_")]
selected_exports = st.multiselect("اختر الجداول/التقارير للتصدير", list(export_pool.keys()), default=default_export)

if selected_exports:
    selected_dataframes = {name: export_pool[name] for name in selected_exports}
    excel_bytes = to_excel_bytes(selected_dataframes)
    filename = f"dashboard_tables_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    st.download_button(
        label="⬇️ تحميل ملف Excel",
        data=excel_bytes,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
else:
    st.info("اختر عنصرًا واحدًا على الأقل للتصدير.")

