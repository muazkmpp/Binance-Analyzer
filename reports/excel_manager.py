import pandas as pd

class ExcelManager:

    def __init__(self, file_path):
        self.writer = pd.ExcelWriter(
            file_path,
            engine="xlsxwriter"
        )
        self.workbook = self.writer.book

    def write_df(self, df, sheet_name):
        df.to_excel(
            self.writer,
            sheet_name=sheet_name,
            index=False
        )

    def create_dashboard(self, pnl_df, trades_df):
        ws = self.workbook.add_worksheet("Dashboard")

        total_pnl = pnl_df["pnl"].sum()
        total_trades = len(trades_df)
        win_rate = (pnl_df["pnl"] > 0).mean() * 100

        title = self.workbook.add_format({
            "bold": True, "font_size": 16
        })

        metric = self.workbook.add_format({
            "bold": True, "font_size": 16
        })

        ws.write("A1", "📊 Crypto Investment Dashboard", title)

        ws.write_row("A3", ["Total PnL (USDT)", total_pnl], metric)
        ws.write_row("A4", ["Total Trades", total_trades], metric)
        ws.write_row("A5", ["Winning Rate %", round(win_rate, 2)], metric)

        ws.write_url(
            "A7",
            "http://localhost:8501",
            string="🚀 Open Interactive Dashboard"
        )

    def close(self):
        self.writer.close()
