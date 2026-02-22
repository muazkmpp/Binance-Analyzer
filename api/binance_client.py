import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode

from config.settings import BINANCE_API_KEY, BINANCE_SECRET_KEY, BASE_URL

# Default start date for historical data
DEFAULT_START_DATE = "2024-01-01"


class BinanceClient:
    def __init__(self):
        self.api_key = BINANCE_API_KEY
        self.secret_key = BINANCE_SECRET_KEY
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            "X-MBX-APIKEY": self.api_key
        })

    # ==================================================
    # Internal helpers
    # ==================================================
    def _sign(self, params: dict) -> dict:
        query_string = urlencode(params)
        signature = hmac.new(
            self.secret_key.encode(),
            query_string.encode(),
            hashlib.sha256
        ).hexdigest()
        params["signature"] = signature
        return params

    def _get(self, path, params=None):
        if params is None:
            params = {}
        params["timestamp"] = int(time.time() * 1000)
        signed_params = self._sign(params)
        url = self.base_url + path
        try:
            response = self.session.get(url, params=signed_params, timeout=20)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Binance request failed for {path}: {e}") from e

    # ==================================================
    # Public API
    # ==================================================
    def get_my_trades(self, symbol=None, limit=1000):
        trades = []
        if symbol:
            params = {"symbol": symbol, "limit": limit}
            return self._get("/api/v3/myTrades", params)

        account_info = self._get("/api/v3/account")
        for asset in account_info.get("balances", []):
            asset_symbol = asset["asset"] + "USDT"
            try:
                params = {"symbol": asset_symbol, "limit": limit}
                data = self._get("/api/v3/myTrades", params)
                trades.extend(data)
            except Exception:
                continue
        return trades

    def get_binance_pay(self):
        # مثال، لاحظ يجب تعديل endpoint حسب Binance Pay API
        return self._get("/sapi/v1/pay/transactions")

    def get_deposits(self):
        return self._get("/sapi/v1/capital/deposit/hisrec")

    def get_withdrawals(self):
        return self._get("/sapi/v1/capital/withdraw/history")

    def get_simple_earn_distribution(self):
        # إذا لم يكن لديك endpoint رسمي، نعيد مصفوفة فارغة أو بيانات تجريبية
        try:
            # مثال endpoint تخيلي
            data = self._get("/sapi/v1/earn/simple-distribution")
            return data.get("distribution", [])
        except Exception:
            # لتجنب الخطأ أثناء التطوير
            print("⚠️ Simple Earn distribution not available, returning empty list")
            return []

    def get_stock_positions(self):
        # مثال لإرجاع بيانات الأسهم
        try:
            data = self._get("/sapi/v1/stock/positions")
            return data.get("positions", [])
        except Exception:
            print("⚠️ Stock positions not available, returning empty list")
            return []

    def get_asset_dividends(self, limit=500, startTime=None, endTime=None, asset=None):
        """Get asset dividend history"""
        params = {"limit": limit}
        if startTime:
            params["startTime"] = startTime
        if endTime:
            params["endTime"] = endTime
        if asset:
            params["asset"] = asset

        data = self._get("/sapi/v1/asset/assetDividend", params)
        if isinstance(data, dict):
            return data.get("rows", [])
        if isinstance(data, list):
            return data
        return []

    # ==================================================
    # User History Endpoints
    # ==================================================
    def get_all_orders(self, symbol=None, limit=1000, startTime=None, endTime=None):
        """Get all orders history"""
        params = {"limit": limit}
        if symbol:
            params["symbol"] = symbol
        if startTime:
            params["startTime"] = startTime
        if endTime:
            params["endTime"] = endTime
        return self._get("/api/v3/allOrders", params)

    def get_all_oco_orders(self, limit=1000, startTime=None, endTime=None):
        """Get all OCO orders"""
        params = {"limit": limit}
        if startTime:
            params["startTime"] = startTime
        if endTime:
            params["endTime"] = endTime
        return self._get("/api/v3/allOrderList", params)

    def get_oco_order(self, order_list_id):
        """Get single OCO order by orderListId"""
        params = {"orderListId": order_list_id}
        return self._get("/api/v3/orderList", params)

    def get_account_info(self):
        """Get account information"""
        return self._get("/api/v3/account")

    def get_internal_transfers(self, limit=1000, startTime=None, endTime=None):
        """Get internal transfers history"""
        params = {"limit": limit}
        if startTime:
            params["startTime"] = startTime
        if endTime:
            params["endTime"] = endTime
        return self._get("/sapi/v1/account/transfer", params)

    def get_deposit_addresses(self):
        """Get all deposit addresses"""
        return self._get("/sapi/v1/capital/deposit/address")

    def get_travel_rule_deposit_history(self, limit=1000, startTime=None, endTime=None):
        """Get travel rule deposit history"""
        params = {"limit": limit}
        if startTime:
            params["startTime"] = startTime
        if endTime:
            params["endTime"] = endTime
        return self._get("/sapi/v1/capital/deposit/travelrule", params)

    def get_travel_rule_withdraw_history(self, limit=1000, startTime=None, endTime=None):
        """Get travel rule withdraw history"""
        params = {"limit": limit}
        if startTime:
            params["startTime"] = startTime
        if endTime:
            params["endTime"] = endTime
        return self._get("/sapi/v1/capital/withdraw/travelrule", params)

    def get_flexible_subscription_record(self, limit=1000, startTime=None, endTime=None):
        """Get flexible subscription record"""
        params = {"limit": limit}
        if startTime:
            params["startTime"] = startTime
        if endTime:
            params["endTime"] = endTime
        return self._get("/sapi/v1/earn/flexible/subscribe/history", params)

    def get_locked_subscription_record(self, limit=1000, startTime=None, endTime=None):
        """Get locked subscription record"""
        params = {"limit": limit}
        if startTime:
            params["startTime"] = startTime
        if endTime:
            params["endTime"] = endTime
        return self._get("/sapi/v1/earn/locked/subscribe/history", params)

    def get_flexible_redemption_record(self, limit=1000, startTime=None, endTime=None):
        """Get flexible redemption record"""
        params = {"limit": limit}
        if startTime:
            params["startTime"] = startTime
        if endTime:
            params["endTime"] = endTime
        return self._get("/sapi/v1/earn/flexible/redeem/history", params)

    def get_locked_redemption_record(self, limit=1000, startTime=None, endTime=None):
        """Get locked redemption record"""
        params = {"limit": limit}
        if startTime:
            params["startTime"] = startTime
        if endTime:
            params["endTime"] = endTime
        return self._get("/sapi/v1/earn/locked/redeem/history", params)

    def get_flexible_rewards_history(self, limit=1000, startTime=None, endTime=None):
        """Get flexible rewards history"""
        params = {"limit": limit}
        if startTime:
            params["startTime"] = startTime
        if endTime:
            params["endTime"] = endTime
        return self._get("/sapi/v1/earn/flexible/history", params)

    def get_locked_rewards_history(self, limit=1000, startTime=None, endTime=None):
        """Get locked rewards history"""
        params = {"limit": limit}
        if startTime:
            params["startTime"] = startTime
        if endTime:
            params["endTime"] = endTime
        return self._get("/sapi/v1/earn/locked/history", params)

    def get_collateral_history(self, limit=1000, startTime=None, endTime=None):
        """Get collateral history"""
        params = {"limit": limit}
        if startTime:
            params["startTime"] = startTime
        if endTime:
            params["endTime"] = endTime
        return self._get("/sapi/v1/collateral/history", params)

    def get_rate_history(self, vip_level=None, limit=1000):
        """Get rate history"""
        params = {"limit": limit}
        if vip_level:
            params["vipLevel"] = vip_level
        return self._get("/sapi/v1/interest/rate/history", params)

    # RWUSD endpoints
    def get_rwusd_account(self):
        """Get RWUSD account info"""
        return self._get("/sapi/v1/rd/wusd/account")

    def get_rwusd_quota_details(self):
        """Get RWUSD quota details"""
        return self._get("/sapi/v1/rd/wusd/quota")

    def get_rwusd_subscription_history(self, limit=1000, startTime=None, endTime=None):
        """Get RWUSD subscription history"""
        params = {"limit": limit}
        if startTime:
            params["startTime"] = startTime
        if endTime:
            params["endTime"] = endTime
        return self._get("/sapi/v1/rd/wusd/subscription/history", params)

    def get_rwusd_redemption_history(self, limit=1000, startTime=None, endTime=None):
        """Get RWUSD redemption history"""
        params = {"limit": limit}
        if startTime:
            params["startTime"] = startTime
        if endTime:
            params["endTime"] = endTime
        return self._get("/sapi/v1/rd/wusd/redemption/history", params)

    def get_rwusd_rewards_history(self, limit=1000, startTime=None, endTime=None):
        """Get RWUSD rewards history"""
        params = {"limit": limit}
        if startTime:
            params["startTime"] = startTime
        if endTime:
            params["endTime"] = endTime
        return self._get("/sapi/v1/rd/wusd/reward/history", params)

    def get_rwusd_rate_history(self, limit=1000, startTime=None, endTime=None):
        """Get RWUSD rate history"""
        params = {"limit": limit}
        if startTime:
            params["startTime"] = startTime
        if endTime:
            params["endTime"] = endTime
        return self._get("/sapi/v1/rd/wusd/rate/history", params)

    # BFUSD endpoints
    def get_bfusd_subscription_history(self, limit=1000, startTime=None, endTime=None):
        """Get BFUSD subscription history"""
        params = {"limit": limit}
        if startTime:
            params["startTime"] = startTime
        if endTime:
            params["endTime"] = endTime
        return self._get("/sapi/v1/bsusd/subscription/history", params)

    # SOL Staking endpoints
    def get_sol_staking_history(self, limit=1000, startTime=None, endTime=None):
        """Get SOL staking history"""
        params = {"limit": limit}
        if startTime:
            params["startTime"] = startTime
        if endTime:
            params["endTime"] = endTime
        return self._get("/sapi/v1/staking/sol/history", params)

    def get_bnsol_rewards_history(self, limit=1000, startTime=None, endTime=None):
        """Get BNSOL rewards history"""
        params = {"limit": limit}
        if startTime:
            params["startTime"] = startTime
        if endTime:
            params["endTime"] = endTime
        return self._get("/sapi/v1/staking/sol/reward/history", params)

    def get_bnsol_rate_history(self, limit=1000, startTime=None, endTime=None):
        """Get BNSOL rate history"""
        params = {"limit": limit}
        if startTime:
            params["startTime"] = startTime
        if endTime:
            params["endTime"] = endTime
        return self._get("/sapi/v1/staking/sol/rate/history", params)

    def get_boost_rewards_history(self, limit=1000, startTime=None, endTime=None):
        """Get boost rewards history"""
        params = {"limit": limit}
        if startTime:
            params["startTime"] = startTime
        if endTime:
            params["endTime"] = endTime
        return self._get("/sapi/v1/boost/history", params)
