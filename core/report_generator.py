import pandas as pd
from pathlib import Path
from datetime import datetime
from core.database import DatabaseManager


class ExcelReportGenerator:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.data_dir = self.base_dir / "data"
        self.db = DatabaseManager()

        # ملفات البيانات
        self.files = {
            "spot_trades": self.data_dir / "spot_trades.csv",
            "fifo": self.data_dir / "fifo_results.csv",
            "binance_pay": self.data_dir / "binance_pay.csv",
            "deposits": self.data_dir / "deposits.csv",
            "withdrawals": self.data_dir / "withdrawals.csv",
            "simple_earn": self.data_dir / "simple_earn.csv",
            "asset_dividends": self.data_dir / "asset_dividends.csv",
            "stock": self.data_dir / "stock.csv",
            "rwusd": self.data_dir / "rwusd.csv",
            "bfusd": self.data_dir / "bfusd.csv",
            "bnsol": self.data_dir / "bnsol.csv",
            "lusdt": self.data_dir / "lusdt.csv",
            "flexible_stock": self.data_dir / "flexible_stock.csv",
            "small_assets": self.data_dir / "small_assets.csv",
            "spot_wallet": self.data_dir / "spot_wallet.csv",
            "fund_wallet": self.data_dir / "fund_wallet.csv",
            "earn_wallet": self.data_dir / "earn_wallet.csv",
        }

        self.output_file = self.data_dir / "investment_report.xlsx"

    # =========================
    # Public API
    # =========================
    def generate(self):
        # تحميل البيانات
        dataframes = {name: self._load_data(name, file) for name, file in self.files.items()}

        # بناء الملخص
        summary_df = self._build_summary(dataframes)
        self.db.save_dataframe("report_summary", summary_df)

        # كتابة التقرير Excel
        self._write_excel(dataframes, summary_df)

        return self.output_file

    # =========================
    # Load CSV
    # =========================
    def _load_data(self, table_name: str, path: Path):
        db_df = self.db.load_dataframe(table_name)
        if not db_df.empty:
            return db_df

        if not path.exists():
            return pd.DataFrame()
        df = pd.read_csv(path)
        if "time" in df.columns:
            df["time"] = pd.to_datetime(df["time"], errors="coerce")
        return df

    # =========================
    # Build Summary
    # =========================
    def _build_summary(self, dfs: dict):
        rows = []
        rows.append(("Report Generated At", datetime.now()))

        # عدد كل نوع من البيانات
        for name, df in dfs.items():
            rows.append((f"Total {name.replace('_', ' ').title()}", len(df)))

        # Realized PnL و Total Fees من FIFO
        fifo_df = dfs.get("fifo", pd.DataFrame())
        if not fifo_df.empty:
            rows.append(("Realized PnL", fifo_df.get("realized_pnl", 0).sum()))
            rows.append(("Total Fees", fifo_df.get("fee", 0).sum()))
        else:
            rows.append(("Realized PnL", 0))
            rows.append(("Total Fees", 0))

        return pd.DataFrame(rows, columns=["Metric", "Value"])

    # =========================
    # Write Excel
    # =========================
    def _write_excel(self, dfs: dict, summary_df: pd.DataFrame):
        self.data_dir.mkdir(exist_ok=True)

        with pd.ExcelWriter(self.output_file, engine="openpyxl") as writer:
            # الملخص
            summary_df.to_excel(writer, sheet_name="Summary", index=False)

            # كل البيانات
            for name, df in dfs.items():
                if not df.empty:
                    sheet_name = name.replace("_", " ").title()
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
