import os
import pandas as pd
from collections import defaultdict
from config.settings import DATA_DIR
from api.binance_client import BinanceClient
from core.database import DatabaseManager


class Portfolio:
    def __init__(self):
        self.data_dir = DATA_DIR
        self.trades_file = os.path.join(self.data_dir, "spot_trades.csv")
        self.fifo_file = os.path.join(self.data_dir, "fifo_results.csv")
        self.portfolio_file = os.path.join(self.data_dir, "portfolio.csv")
        self.client = BinanceClient()
        self.db = DatabaseManager()

    # ==============================
    # Public API
    # ==============================
    def calculate(self):
        trades_df = self._load_trades()
        fifo_df = self._load_fifo()

        allocation = self._compute_allocation(trades_df, fifo_df)
        portfolio_df = pd.DataFrame(allocation)

        # حفظ الملف
        portfolio_df.to_csv(self.portfolio_file, index=False)
        self.db.save_dataframe("portfolio", portfolio_df)
        print(f"✅ Portfolio saved to {self.portfolio_file}")
        return portfolio_df

    # ==============================
    # Load Data
    # ==============================
    def _load_trades(self):
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
                raise FileNotFoundError("spot_trades.csv not found. Fetch trades first.")
            df = pd.read_csv(self.trades_file)
        df["quantity"] = df["qty"].astype(float) if "qty" in df.columns else df["quantity"].astype(float)
        df["price"] = df["price"].astype(float)
        df["symbol"] = df["symbol"].astype(str)
        if "side" in df.columns:
            df["side"] = df["side"].astype(str).str.upper()
        elif "isBuyer" in df.columns:
            df["side"] = df["isBuyer"].apply(lambda x: "BUY" if to_bool(x) else "SELL")
        elif "is_buy" in df.columns:
            df["side"] = df["is_buy"].apply(lambda x: "BUY" if to_bool(x) else "SELL")
        else:
            raise ValueError("Trades data missing side/isBuyer/is_buy columns.")
        return df

    def _load_fifo(self):
        db_df = self.db.load_dataframe("fifo_results")
        if not db_df.empty:
            return db_df
        if not os.path.exists(self.fifo_file):
            return pd.DataFrame()
        return pd.read_csv(self.fifo_file)

    # ==============================
    # Compute Allocation & Unrealized PnL
    # ==============================
    def _compute_allocation(self, trades_df, fifo_df):
        """
        Returns a list of dicts:
        - symbol
        - total_quantity
        - avg_buy_price
        - current_price
        - unrealized_pnl
        - allocation_value
        """
        positions = defaultdict(lambda: {"quantity": 0.0, "total_cost": 0.0})

        # حساب كمية كل عملة وتكلفتها من Spot Trades
        for _, row in trades_df.iterrows():
            symbol = row["symbol"]
            qty = row["quantity"]
            price = row["price"]
            side = row["side"]

            if side == "BUY":
                positions[symbol]["quantity"] += qty
                positions[symbol]["total_cost"] += qty * price
            else:  # SELL
                positions[symbol]["quantity"] -= qty
                positions[symbol]["total_cost"] -= qty * price  # تقريبي، يمكن تعديل بناءً على FIFO إذا تريد دقة عالية

        # جلب آخر الأسعار لكل عملة
        portfolio_list = []
        for symbol, pos in positions.items():
            if pos["quantity"] <= 0:
                continue

            avg_buy_price = pos["total_cost"] / pos["quantity"] if pos["quantity"] != 0 else 0.0
            try:
                ticker = self.client._get("/api/v3/ticker/price", {"symbol": symbol})
                current_price = float(ticker.get("price", 0))
            except Exception:
                current_price = 0.0

            unrealized_pnl = (current_price - avg_buy_price) * pos["quantity"]
            allocation_value = current_price * pos["quantity"]

            portfolio_list.append({
                "symbol": symbol,
                "total_quantity": pos["quantity"],
                "avg_buy_price": round(avg_buy_price, 4),
                "current_price": round(current_price, 4),
                "unrealized_pnl": round(unrealized_pnl, 4),
                "allocation_value": round(allocation_value, 4)
            })

        return portfolio_list
