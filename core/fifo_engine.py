import pandas as pd
import os
from collections import defaultdict

from config.settings import DATA_DIR
from core.database import DatabaseManager


class FIFOEngine:
    def __init__(self):
        self.trades_file = os.path.join(DATA_DIR, "spot_trades.csv")
        self.output_file = os.path.join(DATA_DIR, "fifo_results.csv")
        self.db = DatabaseManager()

    # ==================================================
    # Public API
    # ==================================================
    def run(self):
        trades_df = self._load_trades()
        fifo_df = self._calculate_fifo(trades_df)
        fifo_df.to_csv(self.output_file, index=False)
        self.db.save_dataframe("fifo_results", fifo_df)
        print(f"✅ FIFO results saved to {self.output_file}")

    # ==================================================
    # Load & Normalize Trades
    # ==================================================
    def _load_trades(self) -> pd.DataFrame:
        def to_bool(value):
            if isinstance(value, bool):
                return value
            if isinstance(value, (int, float)):
                return value != 0
            text = str(value).strip().lower()
            return text in ("true", "1", "yes", "y", "buy")

        db_df = self.db.load_dataframe("spot_trades")
        if not db_df.empty:
            df = db_df.copy()
        else:
            if not os.path.exists(self.trades_file):
                raise FileNotFoundError("spot_trades.csv not found. Run fetch step first.")
            df = pd.read_csv(self.trades_file)

        # توحيد الأعمدة
        df = df.rename(columns={
            "time": "timestamp",
            "qty": "quantity",
            "isBuyer": "is_buy",
        })

        # 🔑 تحويل timestamp بذكاء
        if pd.api.types.is_numeric_dtype(df["timestamp"]):
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", errors="coerce")
        else:
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

        if "side" in df.columns:
            df["side"] = df["side"].astype(str).str.upper()
        else:
            df["side"] = df["is_buy"].apply(lambda x: "BUY" if to_bool(x) else "SELL")
        df["quantity"] = df["quantity"].astype(float)
        df["price"] = df["price"].astype(float)

        # fee
        if "commission" in df.columns:
            df["fee"] = df["commission"].astype(float)
        else:
            df["fee"] = 0.0

        df = df.sort_values("timestamp").reset_index(drop=True)
        return df

    # ==================================================
    # FIFO Logic
    # ==================================================
    def _calculate_fifo(self, df: pd.DataFrame) -> pd.DataFrame:
        positions = defaultdict(list)
        results = []

        for _, row in df.iterrows():
            symbol = row["symbol"]
            qty = row["quantity"]
            price = row["price"]
            side = row["side"]
            time = row["timestamp"]
            fee = row["fee"]

            if side == "BUY":
                positions[symbol].append({
                    "qty": qty,
                    "price": price,
                    "time": time,
                    "fee": fee
                })

            else:  # SELL
                remaining = qty
                sell_fee_allocated = fee

                while remaining > 0 and positions[symbol]:
                    buy = positions[symbol][0]
                    used_qty = min(buy["qty"], remaining)

                    pnl = (price - buy["price"]) * used_qty
                    total_fee = buy["fee"] * (used_qty / buy["qty"]) + sell_fee_allocated

                    results.append({
                        "symbol": symbol,
                        "buy_time": buy["time"],
                        "sell_time": time,
                        "quantity": used_qty,
                        "buy_price": buy["price"],
                        "sell_price": price,
                        "fee": round(total_fee, 6),
                        "realized_pnl": round(pnl - total_fee, 6)
                    })

                    buy["qty"] -= used_qty
                    remaining -= used_qty

                    if buy["qty"] == 0:
                        positions[symbol].pop(0)

        return pd.DataFrame(results)
