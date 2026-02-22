from api.binance_client import BinanceClient, DEFAULT_START_DATE
import pandas as pd
import os
import re
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from config.settings import DATA_DIR
from core.database import DatabaseManager
import warnings
warnings.filterwarnings('ignore')


def detect_and_flatten_nested_columns(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, List[str]]]:
    """
    اكتشف الأعمدة المتداخلة وقم بتسطيحها.
    
    Args:
        df: DataFrame يحتوي على بيانات قد تكون متداخلة
        
    Returns:
        - DataFrame مسطح مع أعمدة جديدة
        - dict يحتوي على mapping من العمود الأصلي للأعمدة الجديدة
    """
    nested_columns = {}
    df_flat = df.copy()
    
    for col in df.columns:
        # فحص إذا كان العمود يحتوي على dict أو list
        sample = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
        
        if sample is None:
            continue
            
        if isinstance(sample, dict):
            # تسطيح الـ dict - اجمع كل المفاتيح من جميع الصفوف
            all_keys = set()
            for item in df[col].dropna():
                if isinstance(item, dict):
                    all_keys.update(item.keys())
            
            if all_keys:
                nested_columns[col] = []
                for key in all_keys:
                    new_col_name = f"{col}_{key}"
                    df_flat[new_col_name] = df[col].apply(
                        lambda x: x.get(key) if isinstance(x, dict) else None
                    )
                    nested_columns[col].append(new_col_name)
                
        elif isinstance(sample, list) and len(sample) > 0:
            # معالجة الـ list - إذا كان يحتوي على dicts
            first_item = sample[0] if isinstance(sample[0], (dict, list)) else None
            
            if isinstance(first_item, dict):
                # اجمع كل المفاتيح من جميع العناصر
                all_keys = set()
                for item in df[col].dropna():
                    if isinstance(item, list):
                        for sub_item in item:
                            if isinstance(sub_item, dict):
                                all_keys.update(sub_item.keys())
                
                if all_keys:
                    nested_columns[col] = []
                    for key in all_keys:
                        new_col_name = f"{col}_{key}"
                        df_flat[new_col_name] = df[col].apply(
                            lambda x: x[0].get(key) if isinstance(x, list) and len(x) > 0 and isinstance(x[0], dict) else None
                        )
                        nested_columns[col].append(new_col_name)
            else:
                # تحويل الـ list إلى string
                df_flat[col] = df[col].apply(lambda x: ','.join(map(str, x)) if isinstance(x, list) else x)
    
    return df_flat, nested_columns


class DataFetcher:
    """
    فئة DataFetcher تنظم جلب بيانات التداول والحساب من واجهة Binance API
    وتصدّر كل نوع بيانات إلى ملف CSV منفصل في مجلد data/.
    
    تعمل هذه الفئة كمرحلة أولى في خط أنابيب البيانات: جلب البيانات الخام من Binance
    وتطبيعها بصيغة CSV للمعالجة لاحقاً (FIFO، المحفظة، التقارير).
    """
    
    @staticmethod
    def _clean_binance_pay_data(df):
        """
        تنظيف بيانات معاملات Binance Pay، خاصة عمود data.
        
        تقوم هذه الدالة بـ:
        1. استخراج بيانات JSON من عمود data
        2. إزالة الأقواس والأحرف الخاصة غير الضرورية
        3. تحويل البيانات إلى صيغة نظيفة وسهلة القراءة
        4. حفظ البيانات المهمة في أعمدة منفصلة
        
        Args:
            df (pd.DataFrame): DataFrame يحتوي على معاملات Binance Pay
            
        Returns:
            pd.DataFrame: DataFrame منظف مع عمود data النظيف
        """
        if df.empty or "data" not in df.columns:
            return df
        
        # تنظيف عمود data
        def clean_data_field(data_val):
            if pd.isna(data_val) or data_val == "":
                return ""
            
            data_str = str(data_val)
            
            # محاولة تحليل JSON إذا كان البيانات بصيغة JSON
            try:
                data_json = json.loads(data_str)
                # تحويل JSON إلى نص منسق بدون أقواس كبيرة
                if isinstance(data_json, dict):
                    items = ", ".join([f"{k}: {v}" for k, v in data_json.items()])
                    return items
                else:
                    return str(data_json)
            except (json.JSONDecodeError, ValueError):
                pass
            
            # إزالة الأقواس الكبيرة والصغيرة وعلامات الترقيم الزائدة
            # الاحتفاظ بالمعلومات المهمة فقط
            cleaned = data_str.strip("{}[]()\"'")
            
            # إزالة علامات الترقيم المتكررة
            cleaned = re.sub(r'[,\s]+', ', ', cleaned)
            cleaned = re.sub(r': +', ': ', cleaned)
            cleaned = re.sub(r',\s*$', '', cleaned)
            
            return cleaned
        
        df["data"] = df["data"].apply(clean_data_field)
        
        return df

    def __init__(self):
        """
        تهيئة DataFetcher مع عميل Binance API ومجلد الإخراج.
        
        الخصائص:
            client (BinanceClient): عميل Binance API المصرح للقيام بالطلبات
            output_dir (str): مسار المجلد حيث سيتم حفظ ملفات CSV (من config.settings.DATA_DIR)
        """
        self.client = BinanceClient()
        self.output_dir = DATA_DIR
        self.db = DatabaseManager()

    def _sync_all_csv_to_sqlite(self):
        """
        مزامنة جميع ملفات CSV الموجودة في data/ إلى جداول SQLite محلية.
        اسم الجدول يساوي اسم الملف بدون الامتداد.
        """
        try:
            csv_files = [f for f in os.listdir(self.output_dir) if f.lower().endswith(".csv")]
            for csv_file in csv_files:
                csv_path = os.path.join(self.output_dir, csv_file)
                table_name = os.path.splitext(csv_file)[0]
                try:
                    df = pd.read_csv(csv_path)
                    self.db.save_dataframe(table_name, df)
                except Exception as e:
                    print(f"⚠️ فشل مزامنة {csv_file} إلى SQLite: {e}")
            print("✅ تمت مزامنة ملفات CSV إلى SQLite")
        except Exception as e:
            print(f"⚠️ خطأ عام أثناء مزامنة SQLite: {e}")

    def fetch_all(self):
        """
        تنظيم خط أنابيب جلب البيانات الكاملة من Binance.
        
        هذه الطريقة:
        1. إنشاء مجلد الإخراج (data/) إذا لم يكن موجوداً
        2. استدعاء طرق الجلب الفردية لكل نوع بيانات بالتتابع
        3. كل طريقة تكتب نتائجها إلى ملف CSV منفصل
        
        ملفات الإخراج المُنشأة:
        - spot_trades.csv: جميع معاملات الشراء/البيع (لحساب FIFO)
        - binance_pay.csv: معاملات Binance Pay
        - deposits.csv & withdrawals.csv: سجل الودائع والسحوبات على السلسلة
        - simple_earn.csv: توزيعات المكافآت من الرهن/الإقراض
        - asset_dividends.csv: توزيعات الأرباح من الأصول (/sapi/v1/asset/assetDividend)
        - stock.csv: مراكز التداول الفوري (إن وجدت)
        - rwusd.csv: منتجات RWUSD
        - bfusd.csv: منتجات BFUSD
        - bnsol.csv: منتجات BNSOL
        - lusdt.csv: منتجات LUSDT
        - flexible_stock.csv: منتجات Flexible Stock
        - small_assets.csv: سجل تحويل العملات الصغيرة
        - spot_wallet.csv: بيانات محفظة Spot اليومية
        - fund_wallet.csv: بيانات محفظة Fund اليومية
        - earn_wallet.csv: بيانات محفظة Earn اليومية
        """
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        self._fetch_spot_trades()
        self._fetch_binance_pay()
        self._fetch_deposits_withdrawals()
        self._fetch_simple_earn()
        self._fetch_asset_dividends()
        self._fetch_stock()
        self._fetch_rwusd()
        self._fetch_bfusd()
        self._fetch_bnsol()
        self._fetch_lusdt()
        self._fetch_flexible_stock()
        self._fetch_small_assets_conversion()
        self._fetch_spot_wallet_history()
        self._fetch_fund_wallet_history()
        self._fetch_earn_wallet_history()
        self._sync_all_csv_to_sqlite()

    def _fetch_spot_wallet_history(self):
        """
        جلب بيانات محفظة Spot اليومية للفترة التاريخية وحفظها في spot_wallet.csv
        """
        print("📥 جاري جلب بيانات محفظة Spot التاريخية...")
        try:
            # جلب الرصيد اليومي لكل عملة من /api/v3/account
            # لا يوجد endpoint رسمي للتاريخ الكامل، سنستخدم الرصيد الحالي ونضيف تاريخ اليوم
            account = self.client._get("/api/v3/account")
            balances = account.get("balances", [])
            today = pd.Timestamp.today()
            for b in balances:
                b["date"] = today.strftime("%Y-%m-%d")
            pd.DataFrame(balances).to_csv(os.path.join(self.output_dir, "spot_wallet.csv"), index=False)
            print(f"✅ تم حفظ spot_wallet.csv إلى {self.output_dir}")
        except Exception as e:
            print(f"⚠️ خطأ في جلب محفظة Spot: {e}")

    def _fetch_fund_wallet_history(self):
        """
        جلب بيانات محفظة Fund اليومية للفترة التاريخية وحفظها في fund_wallet.csv
        """
        print("📥 جاري جلب بيانات محفظة Fund التاريخية...")
        try:
            # جلب الرصيد اليومي من /sapi/v1/asset/assetDetail
            fund = self.client._get("/sapi/v1/asset/assetDetail")
            today = pd.Timestamp.today()
            rows = []
            for asset, details in fund.items():
                row = {"asset": asset, **details, "date": today.strftime("%Y-%m-%d")}
                rows.append(row)
            pd.DataFrame(rows).to_csv(os.path.join(self.output_dir, "fund_wallet.csv"), index=False)
            print(f"✅ تم حفظ fund_wallet.csv إلى {self.output_dir}")
        except Exception as e:
            print(f"⚠️ خطأ في جلب محفظة Fund: {e}")

    def _fetch_earn_wallet_history(self):
        """
        جلب بيانات محفظة Earn اليومية للفترة التاريخية وحفظها في earn_wallet.csv
        """
        print("📥 جاري جلب بيانات محفظة Earn التاريخية...")
        try:
            # جلب بيانات Earn من /sapi/v1/earn/flexible/history
            earn = self.client._get("/sapi/v1/earn/flexible/history")
            today = pd.Timestamp.today()
            for e in earn:
                e["date"] = today.strftime("%Y-%m-%d")
            pd.DataFrame(earn).to_csv(os.path.join(self.output_dir, "earn_wallet.csv"), index=False)
            print(f"✅ تم حفظ earn_wallet.csv إلى {self.output_dir}")
        except Exception as e:
            print(f"⚠️ خطأ في جلب محفظة Earn: {e}")

    def _fetch_small_assets_conversion(self):
        """
        جلب سجل تحويل العملات الصغيرة (Small Assets Conversion) والرسوم وحفظها في small_assets.csv
        """
        print("📥 جاري جلب سجل تحويل العملات الصغيرة...")
        try:
            # endpoint الرسمي لتحويل العملات الصغيرة
            data = self.client._get("/sapi/v1/asset/dribblet")
            if data and "userAssetDribblets" in data:
                dribblets = data["userAssetDribblets"]
                # كل عملية تحويل قد تحتوي على تفاصيل فرعية
                rows = []
                for d in dribblets:
                    for detail in d.get("userAssetDribbletDetails", []):
                        row = {**d, **detail}
                        rows.append(row)
                if rows:
                    pd.DataFrame(rows).to_csv(os.path.join(self.output_dir, "small_assets.csv"), index=False)
                    print(f"✅ تم حفظ small_assets.csv إلى {self.output_dir}")
                else:
                    print("⚠️ لا توجد تفاصيل لتحويل العملات الصغيرة")
            else:
                print("⚠️ لم يتم إرجاع بيانات تحويل العملات الصغيرة")
        except Exception as e:
            print(f"⚠️ خطأ في جلب تحويل العملات الصغيرة: {e}")

    def _fetch_rwusd(self):
        """
        جلب بيانات منتجات RWUSD (Reward Wrapped USD) وحفظها في rwusd.csv
        
        RWUSD هو منتج استثماري من Binance يوفر عوائد على الدولار الأمريكي.
        تشمل البيانات:
        - الرصيد الحالي
        - تاريخ الاكتتاب
        - العائد المستحق
        - حالة الاشتراك
        
        الإخراج: rwusd.csv
        """
        print("📥 جاري جلب منتجات RWUSD...")
        try:
            # جلب بيانات حساب RWUSD
            rwusd_account = self.client._get("/sapi/v1/rd/wusd/account")
            
            # جلب سجل الاشتراكات
            rwusd_history = self.client._get("/sapi/v1/rd/wusd/subscription/history")
            
            # جلب سجل المكافآت
            rwusd_rewards = self.client._get("/sapi/v1/rd/wusd/reward/history")
            
            all_data = []
            
            # إضافة بيانات الحساب الحالي
            if rwusd_account:
                account_data = {
                    'type': 'account',
                    'total_amount': rwusd_account.get('totalAmount', 0),
                    'available_amount': rwusd_account.get('availableAmount', 0),
                    'interest_amount': rwusd_account.get('interestAmount', 0),
                    'latest_interest_time': rwusd_account.get('latestInterestTime', ''),
                    'subscription_time': rwusd_account.get('subscriptionTime', ''),
                    'redemption_time': rwusd_account.get('redemptionTime', ''),
                    'status': rwusd_account.get('status', 'unknown')
                }
                all_data.append(account_data)
            
            # إضافة سجل الاشتراكات
            if rwusd_history:
                for record in rwusd_history:
                    history_data = {
                        'type': 'subscription',
                        'amount': record.get('amount', 0),
                        'time': record.get('time', ''),
                        'status': record.get('status', ''),
                        'subscription_id': record.get('subscriptionId', ''),
                        'principal_amount': record.get('principalAmount', 0),
                        'interest_amount': record.get('interestAmount', 0)
                    }
                    all_data.append(history_data)
            
            # إضافة سجل المكافآت
            if rwusd_rewards:
                for reward in rwusd_rewards:
                    reward_data = {
                        'type': 'reward',
                        'amount': reward.get('amount', 0),
                        'time': reward.get('time', ''),
                        'asset': reward.get('asset', 'RWUSD'),
                        'reward_id': reward.get('id', ''),
                        'subscription_id': reward.get('subscriptionId', '')
                    }
                    all_data.append(reward_data)
            
            if all_data:
                df = pd.DataFrame(all_data)
                df.to_csv(os.path.join(self.output_dir, "rwusd.csv"), index=False)
                print(f"✅ تم حفظ rwusd.csv إلى {self.output_dir} ({len(all_data)} سجل)")
            else:
                print("⚠️ لم يتم إرجاع بيانات RWUSD")
                
        except Exception as e:
            print(f"⚠️ خطأ في جلب RWUSD: {e}")

    def _fetch_bfusd(self):
        """
        جلب بيانات منتجات BFUSD (Binance Flexible USD) وحفظها في bfusd.csv
        
        BFUSD هو منتج استثماري مرن من Binance يوفر عوائد على الدولار الأمريكي.
        تشمل البيانات:
        - الاشتراكات النشطة
        - سجل المكافآت اليومية
        - تاريخ الشراء والاسترداد
        - العائد السنوي
        
        الإخراج: bfusd.csv
        """
        print("📥 جاري جلب منتجات BFUSD...")
        try:
            # جلب بيانات حساب BFUSD
            bfusd_account = self.client._get("/sapi/v1/bsusd/account")
            
            # جلب سجل الاشتراكات
            bfusd_history = self.client._get("/sapi/v1/bsusd/subscription/history")
            
            # جلب سجل المكافآت
            bfusd_rewards = self.client._get("/sapi/v1/bsusd/reward/history")
            
            # جلب سجل الاستردادات
            bfusd_redemptions = self.client._get("/sapi/v1/bsusd/redemption/history")
            
            all_data = []
            
            # إضافة بيانات الحساب الحالي
            if bfusd_account:
                account_data = {
                    'type': 'account',
                    'total_amount': bfusd_account.get('totalAmount', 0),
                    'available_amount': bfusd_account.get('availableAmount', 0),
                    'interest_amount': bfusd_account.get('interestAmount', 0),
                    'latest_interest_time': bfusd_account.get('latestInterestTime', ''),
                    'annual_percentage_rate': bfusd_account.get('annualPercentageRate', 0),
                    'status': bfusd_account.get('status', 'unknown')
                }
                all_data.append(account_data)
            
            # إضافة سجل الاشتراكات
            if bfusd_history:
                for record in bfusd_history:
                    history_data = {
                        'type': 'subscription',
                        'amount': record.get('amount', 0),
                        'time': record.get('time', ''),
                        'status': record.get('status', ''),
                        'subscription_id': record.get('subscriptionId', ''),
                        'principal_amount': record.get('principalAmount', 0),
                        'interest_amount': record.get('interestAmount', 0),
                        'annual_percentage_rate': record.get('annualPercentageRate', 0)
                    }
                    all_data.append(history_data)
            
            # إضافة سجل المكافآت
            if bfusd_rewards:
                for reward in bfusd_rewards:
                    reward_data = {
                        'type': 'reward',
                        'amount': reward.get('amount', 0),
                        'time': reward.get('time', ''),
                        'asset': reward.get('asset', 'BFUSD'),
                        'reward_id': reward.get('id', ''),
                        'subscription_id': reward.get('subscriptionId', ''),
                        'reward_type': reward.get('rewardType', 'interest')
                    }
                    all_data.append(reward_data)
            
            # إضافة سجل الاستردادات
            if bfusd_redemptions:
                for redemption in bfusd_redemptions:
                    redemption_data = {
                        'type': 'redemption',
                        'amount': redemption.get('amount', 0),
                        'time': redemption.get('time', ''),
                        'status': redemption.get('status', ''),
                        'redemption_id': redemption.get('redemptionId', ''),
                        'principal_amount': redemption.get('principalAmount', 0),
                        'interest_amount': redemption.get('interestAmount', 0)
                    }
                    all_data.append(redemption_data)
            
            if all_data:
                df = pd.DataFrame(all_data)
                df.to_csv(os.path.join(self.output_dir, "bfusd.csv"), index=False)
                print(f"✅ تم حفظ bfusd.csv إلى {self.output_dir} ({len(all_data)} سجل)")
            else:
                print("⚠️ لم يتم إرجاع بيانات BFUSD")
                
        except Exception as e:
            print(f"⚠️ خطأ في جلب BFUSD: {e}")

    def _fetch_bnsol(self):
        """
        جلب بيانات منتجات BNSOL (Binance Staked SOL) وحفظها في bnsol.csv
        
        BNSOL هو منتج رهن SOL (Solana) على Binance يوفر مكافآت الستاكينغ.
        تشمل البيانات:
        - رصيد SOL المرهون
        - سجل المكافآت اليومية
        - تاريخ الاشتراك والاسترداد
        - APY الحالي
        
        الإخراج: bnsol.csv
        """
        print("📥 جاري جلب منتجات BNSOL...")
        try:
            # جلب بيانات حساب BNSOL
            bnsol_account = self.client._get("/sapi/v1/staking/sol/account")
            
            # جلب سجل المكافآت
            bnsol_rewards = self.client._get("/sapi/v1/staking/sol/reward/history")
            
            # جلب سجل الاشتراكات
            bnsol_history = self.client._get("/sapi/v1/staking/sol/history")
            
            # جلب سجل الاستردادات
            bnsol_redemptions = self.client._get("/sapi/v1/staking/sol/redemption/history")
            
            all_data = []
            
            # إضافة بيانات الحساب الحالي
            if bnsol_account:
                account_data = {
                    'type': 'account',
                    'total_amount': bnsol_account.get('totalAmount', 0),
                    'available_amount': bnsol_account.get('availableAmount', 0),
                    'interest_amount': bnsol_account.get('interestAmount', 0),
                    'latest_interest_time': bnsol_account.get('latestInterestTime', ''),
                    'apy': bnsol_account.get('apy', 0),
                    'status': bnsol_account.get('status', 'unknown')
                }
                all_data.append(account_data)
            
            # إضافة سجل المكافآت
            if bnsol_rewards:
                for reward in bnsol_rewards:
                    reward_data = {
                        'type': 'reward',
                        'amount': reward.get('amount', 0),
                        'time': reward.get('time', ''),
                        'asset': reward.get('asset', 'SOL'),
                        'reward_id': reward.get('id', ''),
                        'reward_type': reward.get('rewardType', 'staking')
                    }
                    all_data.append(reward_data)
            
            # إضافة سجل الاشتراكات
            if bnsol_history:
                for record in bnsol_history:
                    history_data = {
                        'type': 'subscription',
                        'amount': record.get('amount', 0),
                        'time': record.get('time', ''),
                        'status': record.get('status', ''),
                        'subscription_id': record.get('subscriptionId', ''),
                        'apy_at_subscription': record.get('apy', 0)
                    }
                    all_data.append(history_data)
            
            # إضافة سجل الاستردادات
            if bnsol_redemptions:
                for redemption in bnsol_redemptions:
                    redemption_data = {
                        'type': 'redemption',
                        'amount': redemption.get('amount', 0),
                        'time': redemption.get('time', ''),
                        'status': redemption.get('status', ''),
                        'redemption_id': redemption.get('redemptionId', ''),
                        'principal_amount': redemption.get('principalAmount', 0),
                        'interest_amount': redemption.get('interestAmount', 0)
                    }
                    all_data.append(redemption_data)
            
            if all_data:
                df = pd.DataFrame(all_data)
                df.to_csv(os.path.join(self.output_dir, "bnsol.csv"), index=False)
                print(f"✅ تم حفظ bnsol.csv إلى {self.output_dir} ({len(all_data)} سجل)")
            else:
                print("⚠️ لم يتم إرجاع بيانات BNSOL")
                
        except Exception as e:
            print(f"⚠️ خطأ في جلب BNSOL: {e}")

    def _fetch_lusdt(self):
        """
        جلب بيانات منتجات LUSDT وحفظها في lusdt.csv
        """
        print("📥 جاري جلب منتجات LUSDT...")
        try:
            lusdt = self.client._get("/sapi/v1/rd/lusdt/account")
            if lusdt:
                pd.DataFrame([lusdt]).to_csv(os.path.join(self.output_dir, "lusdt.csv"), index=False)
                print(f"✅ تم حفظ lusdt.csv إلى {self.output_dir}")
            else:
                print("⚠️ لم يتم إرجاع بيانات LUSDT")
        except Exception as e:
            print(f"⚠️ خطأ في جلب LUSDT: {e}")

    def _fetch_flexible_stock(self):
        """
        جلب بيانات منتجات Flexible Stock وحفظها في flexible_stock.csv
        """
        print("📥 جاري جلب منتجات Flexible Stock...")
        try:
            flex_stock = self.client._get("/sapi/v1/staking/flexible/product/list")
            if flex_stock:
                pd.DataFrame(flex_stock).to_csv(os.path.join(self.output_dir, "flexible_stock.csv"), index=False)
                print(f"✅ تم حفظ flexible_stock.csv إلى {self.output_dir}")
            else:
                print("⚠️ لم يتم إرجاع بيانات Flexible Stock")
        except Exception as e:
            print(f"⚠️ خطأ في جلب Flexible Stock: {e}")

    def _fetch_spot_trades(self):
        """
        جلب جميع معاملات التداول الفوري (أزواج الشراء/البيع) من حساب Binance.
        
        هذا هو مصدر البيانات الأساسي لحساب FIFO PnL. يتضمن كل سجل تداول
        الرمز، الكمية، السعر، العمولة، الطابع الزمني، وجانب الشراء/البيع.
        
        العملية:
        1. استدعاء واجهة Binance API للحصول على جميع التداولات لجميع الرموز
        2. تحويل طابع Unix الزمني (بالميلي ثانية) إلى datetime في pandas
        3. الحفظ كـ spot_trades.csv للمعالجة اللاحقة بواسطة FIFO
        """
        print("📥 جاري جلب معاملات التداول الفوري والعمولات...")
        try:
            trades = self.client.get_my_trades()
            df = pd.DataFrame(trades)

            # تحويل طابع Unix الزمني (بالميلي ثانية) إلى datetime للتحليل الأسهل
            if "time" in df.columns:
                df["time"] = pd.to_datetime(df["time"], unit="ms")

            df.to_csv(os.path.join(self.output_dir, "spot_trades.csv"), index=False)
            print(f"✅ تم حفظ spot_trades.csv إلى {self.output_dir}")
        except Exception as e:
            print(f"⚠️ خطأ في جلب معاملات التداول الفوري: {e}")

    def _fetch_binance_pay(self):
        """
        جلب سجل معاملات Binance Pay وتنظيف البيانات.
        
        تتضمن سجلات Binance Pay عمليات الدفع والتحويلات والعمليات المعاكسة.
        قد تكون ذات صلة بأغراض ضريبية/محاسبية.
        
        العملية:
        1. جلب معاملات Binance Pay من API
        2. اكتشاف الأعمدة المتداخلة وتسطيحها
        3. حفظ البيانات المسطحة لملف CSV
        
        الإخراج: binance_pay.csv (بيانات مسطحة جاهزة لـ Excel وقاعدة البيانات)
        """
        print("📥 جاري جلب معاملات Binance Pay...")
        try:
            pay = self.client.get_binance_pay()
            
            # استخراج قائمة البيانات من الاستجابة
            if isinstance(pay, dict) and 'data' in pay:
                data_list = pay['data']
            else:
                data_list = pay if isinstance(pay, list) else []
            
            if not data_list:
                print("⚠️ لا توجد بيانات Binance Pay")
                return
            
            df = pd.DataFrame(data_list)
            
            # اكتشاف وتسطيح الأعمدة المتداخلة
            print("   🔍 جاري اكتشاف الأعمدة المتداخلة...")
            df_flattened, nested_info = detect_and_flatten_nested_columns(df)
            
            if nested_info:
                print(f"   ✅ تم اكتشاف وتسطيح {len(nested_info)} عمود متداخل:")
                for col, new_cols in nested_info.items():
                    print(f"      - {col} -> {new_cols}")
            
            # حفظ البيانات المسطحة
            df_flattened.to_csv(os.path.join(self.output_dir, "binance_pay.csv"), index=False)
            print(f"✅ تم حفظ binance_pay.csv ({len(df_flattened)} صف, {len(df_flattened.columns)} عمود) إلى {self.output_dir}")
            
        except Exception as e:
            print(f"⚠️ خطأ في جلب Binance Pay: {e}")

    def _fetch_deposits_withdrawals(self):
        """
        جلب سجلات الودائع والسحوبات على السلسلة.
        
        تتبع هذه السجلات حركات العملات المشفرة من/إلى محافظ خارجية.
        مفيد ل:
        - تتبع أساس التكلفة للعملات المشفرة المهداة/المستلمة
        - سجل تدقيق حركات المحفظة
        - التقارير الضريبية (الأحداث الخاضعة للضريبة المحققة)
        
        المخرجات:
        - deposits.csv: تحويلات العملات المشفرة الواردة
        - withdrawals.csv: تحويلات العملات المشفرة الصادرة
        
        ملاحظة: إرجاع ملفات CSV فارغة إذا لم يتم العثور على ودائع/سحوبات (تدهور متدرج).
        """
        print("📥 جاري جلب السحوبات والودائع...")
        try:
            deposits = self.client.get_deposits()
            withdrawals = self.client.get_withdrawals()

            if deposits:
                pd.DataFrame(deposits).to_csv(os.path.join(self.output_dir, "deposits.csv"), index=False)
            else:
                print("⚠️ لم يتم إرجاع ودائع")

            if withdrawals:
                pd.DataFrame(withdrawals).to_csv(os.path.join(self.output_dir, "withdrawals.csv"), index=False)
            else:
                print("⚠️ لم يتم إرجاع سحوبات")
        except Exception as e:
            print(f"⚠️ خطأ في جلب السحوبات/الودائع: {e}")

    def _fetch_simple_earn(self):
        """
        جلب سجل توزيع Binance Simple Earn (مكافآت الرهن).
        
        Binance Simple Earn هي خدمة رهن مرنة/مقفلة تولد دخلاً سلبياً.
        تُظهر سجلات التوزيع:
        - متى تم دفع المكافآت
        - المبلغ المكتسب
        - نوع الأصل
        
        تُعتبر هذه عادةً دخلاً خاضعاً للضريبة في معظم الولايات القضائية.
        الإخراج: simple_earn.csv (فارغ إذا لم يكن لدى المستخدم نشاط رهن)
        """
        print("📥 جاري جلب توزيع Simple Earn...")
        try:
            earn = self.client.get_simple_earn_distribution()
            if earn:
                pd.DataFrame(earn).to_csv(os.path.join(self.output_dir, "simple_earn.csv"), index=False)
                print(f"✅ تم حفظ simple_earn.csv إلى {self.output_dir}")
            else:
                print("⚠️ لم يتم إرجاع توزيع Simple Earn")
        except Exception as e:
            print(f"⚠️ خطأ في جلب Simple Earn: {e}")

    def _fetch_asset_dividends(self):
        """
        جلب سجل توزيعات الأرباح للأصول من Binance.

        endpoint:
        - /sapi/v1/asset/assetDividend

        الإخراج:
        - asset_dividends.csv
        
        ملاحظة: يتم تحويل طوابع الزمن إلى تاريخ ووقت قياسيين
        - حقل Date: التاريخ بصيغة YYYY-MM-DD
        - حقل Time: الوقت بصيغة HH:MM:SS
        """
        print("📥 جاري جلب Asset Dividend History...")
        try:
            dividends = self.client.get_asset_dividends(limit=500)
            if dividends:
                df = pd.DataFrame(dividends)
                
                # تحويل divTime (طابع زمني بالمللي ثانية) إلى تاريخ ووقت قياسيين
                if 'divTime' in df.columns:
                    # تحويل الطابع الزمني إلى datetime
                    df['divTime'] = pd.to_numeric(df['divTime'], errors='coerce')
                    df['datetime'] = pd.to_datetime(df['divTime'], unit='ms', utc=True)
                    
                    # استخراج التاريخ القياسي في حقل Date
                    df['Date'] = df['datetime'].dt.strftime('%Y-%m-%d')
                    
                    # استخراج الوقت القياسي في حقل Time (تحويل التوقيت إلى Cairo UTC+2)
                    df['Time'] = df['datetime'].dt.tz_convert('Africa/Cairo').dt.strftime('%H:%M:%S')
                    
                    # حذف الأعمدة المؤقتة
                    df = df.drop(columns=['datetime'])
                
                # حفظ إلى ملف CSV
                csv_path = os.path.join(self.output_dir, "asset_dividends.csv")
                df.to_csv(csv_path, index=False)
                print(f"✅ تم حفظ asset_dividends.csv إلى {self.output_dir}")
                
                # حفظ إلى قاعدة البيانات
                try:
                    self.db.save_dataframe("asset_dividends", df)
                    print("✅ تم حفظ asset_dividends إلى قاعدة البيانات")
                except Exception as db_error:
                    print(f"⚠️ خطأ في حفظ asset_dividends إلى قاعدة البيانات: {db_error}")
                    
            else:
                print("⚠️ لم يتم إرجاع بيانات Asset Dividend")
        except Exception as e:
            print(f"⚠️ خطأ في جلب Asset Dividend: {e}")

    def _fetch_stock(self):
        """
        جلب مراكز أسهم Binance (سندات Bearer والأصول الشبيهة بالأسهم).
        
        يوفر Binance تداول أسهم/صناديق استثمارية مقسمة عبر Simple Stocks.
        تسترجع هذه الطريقة أصول الملكية الحالية وتفاصيلها.
        
        الإخراج: stock.csv (فارغ إذا لم يكن لدى المستخدم مراكز أسهم)
        """
        print("📥 جاري جلب مراكز الأسهم...")
        try:
            stock = self.client.get_stock_positions()
            if stock:
                pd.DataFrame(stock).to_csv(os.path.join(self.output_dir, "stock.csv"), index=False)
                print(f"✅ تم حفظ stock.csv إلى {self.output_dir}")
            else:
                print("⚠️ لم يتم إرجاع مراكز أسهم")
        except Exception as e:
            print(f"⚠️ خطأ في جلب مراكز الأسهم: {e}")

    def _convert_date_to_millis(self, date_str):
        """Convert date string to milliseconds timestamp"""
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return int(dt.timestamp() * 1000)
        except Exception:
            return None

    def fetch_all_user_history(self, start_date=DEFAULT_START_DATE):
        """
        Fetch all user history endpoints and save to Excel file.
        
        This method fetches data from all the user history endpoints:
        - My Trades History
        - All Orders History
        - All OCO Order List
        - Single OCO Order List
        - Account Info
        - Deposit History
        - Withdraw History
        - Internal Transfers
        - Deposit Addresses
        - Travel Rule Deposit History
        - Travel Rule Withdraw History
        - Flexible Subscription Record
        - Locked Subscription Record
        - Flexible Redemption Record
        - Locked Redemption Record
        - Flexible Rewards History
        - Locked Rewards History
        - Collateral History
        - Rate History
        - RWUSD Account
        - RWUSD Quota Details
        - RWUSD Subscription History
        - RWUSD Redemption History
        - RWUSD Rewards History
        - RWUSD Rate History
        - BFUSD Subscription History
        - SOL Staking History
        - BNSOL Rewards History
        - BNSOL Rate History
        - Boost Rewards History
        - Asset Dividend History
        
        Output: Binance_User_History_Endpoints.xlsx (Excel file with multiple sheets)
        """
        print("📥 جاري جلب جميع بيانات سجلات المستخدم...")
        
        start_time = self._convert_date_to_millis(start_date)
        end_time = int(datetime.now().timestamp() * 1000)
        
        # Dictionary to store all dataframes
        all_data = {}
        
        # Helper function to add data to dictionary
        def add_data(sheet_name, data):
            if data:
                try:
                    df = pd.DataFrame(data)
                    if not df.empty:
                        # Convert timestamp columns to datetime if they exist
                        for col in df.columns:
                            if 'time' in col.lower() or 'date' in col.lower():
                                try:
                                    df[col] = pd.to_datetime(df[col], unit='ms', errors='ignore')
                                except:
                                    pass
                        all_data[sheet_name] = df
                        table_name = sheet_name.lower().replace(" ", "_").replace("-", "_")
                        self.db.save_dataframe(f"user_history_{table_name}", df)
                        print(f"   ✅ {sheet_name}: {len(df)} records")
                except Exception as e:
                    print(f"   ⚠️ {sheet_name}: Error processing data - {e}")
            else:
                print(f"   ⚠️ {sheet_name}: No data returned")
        
        try:
            # 1. My Trades History
            print("   📊 جاري جلب My Trades History...")
            try:
                trades = self.client.get_my_trades(limit=1000)
                add_data("My Trades History", trades)
            except Exception as e:
                print(f"   ⚠️ My Trades History: Error - {e}")
            
            # 2. All Orders History
            print("   📊 جاري جلب All Orders History...")
            try:
                orders = self.client.get_all_orders(limit=1000, startTime=start_time, endTime=end_time)
                add_data("All Orders History", orders)
            except Exception as e:
                print(f"   ⚠️ All Orders History: Error - {e}")
            
            # 3. All OCO Order List
            print("   📊 جاري جلب All OCO Order List...")
            try:
                oco_orders = self.client.get_all_oco_orders(limit=1000, startTime=start_time, endTime=end_time)
                add_data("All OCO Order List", oco_orders)
            except Exception as e:
                print(f"   ⚠️ All OCO Order List: Error - {e}")
            
            # 4. Account Info
            print("   📊 جاري جلب Account Info...")
            try:
                account = self.client.get_account_info()
                if account:
                    # Convert balances to dataframe
                    if "balances" in account:
                        balances_df = pd.DataFrame(account["balances"])
                        balances_df["account_type"] = "spot"
                        add_data("Account Info - Balances", [account])
                        add_data("Account Info - All Balances", balances_df.to_dict('records'))
            except Exception as e:
                print(f"   ⚠️ Account Info: Error - {e}")
            
            # 5. Deposit History
            print("   📊 جاري جلب Deposit History...")
            try:
                deposits = self.client.get_deposits()
                add_data("Deposit History", deposits)
            except Exception as e:
                print(f"   ⚠️ Deposit History: Error - {e}")
            
            # 6. Withdraw History
            print("   📊 جلي جلب Withdraw History...")
            try:
                withdrawals = self.client.get_withdrawals()
                add_data("Withdraw History", withdrawals)
            except Exception as e:
                print(f"   ⚠️ Withdraw History: Error - {e}")
            
            # 7. Internal Transfers
            print("   📊 جاري جلب Internal Transfers...")
            try:
                transfers = self.client.get_internal_transfers(limit=1000, startTime=start_time, endTime=end_time)
                add_data("Internal Transfers", transfers)
            except Exception as e:
                print(f"   ⚠️ Internal Transfers: Error - {e}")
            
            # 8. Deposit Addresses
            print("   📊 جاري جلب Deposit Addresses...")
            try:
                addresses = self.client.get_deposit_addresses()
                add_data("Deposit Addresses", addresses)
            except Exception as e:
                print(f"   ⚠️ Deposit Addresses: Error - {e}")
            
            # 9. Travel Rule Deposit History
            print("   📊 جاري جلب Travel Rule Deposit History...")
            try:
                travel_deposits = self.client.get_travel_rule_deposit_history(limit=1000, startTime=start_time, endTime=end_time)
                add_data("Travel Rule Deposit History", travel_deposits)
            except Exception as e:
                print(f"   ⚠️ Travel Rule Deposit History: Error - {e}")
            
            # 10. Travel Rule Withdraw History
            print("   📊 جاري جلب Travel Rule Withdraw History...")
            try:
                travel_withdraws = self.client.get_travel_rule_withdraw_history(limit=1000, startTime=start_time, endTime=end_time)
                add_data("Travel Rule Withdraw History", travel_withdraws)
            except Exception as e:
                print(f"   ⚠️ Travel Rule Withdraw History: Error - {e}")
            
            # 11. Flexible Subscription Record
            print("   📊 جاري جلب Flexible Subscription Record...")
            try:
                flex_subs = self.client.get_flexible_subscription_record(limit=1000, startTime=start_time, endTime=end_time)
                add_data("Flexible Subscription Record", flex_subs)
            except Exception as e:
                print(f"   ⚠️ Flexible Subscription Record: Error - {e}")
            
            # 12. Locked Subscription Record
            print("   📊 جاري جلب Locked Subscription Record...")
            try:
                locked_subs = self.client.get_locked_subscription_record(limit=1000, startTime=start_time, endTime=end_time)
                add_data("Locked Subscription Record", locked_subs)
            except Exception as e:
                print(f"   ⚠️ Locked Subscription Record: Error - {e}")
            
            # 13. Flexible Redemption Record
            print("   📊 جاري جلب Flexible Redemption Record...")
            try:
                flex_redemptions = self.client.get_flexible_redemption_record(limit=1000, startTime=start_time, endTime=end_time)
                add_data("Flexible Redemption Record", flex_redemptions)
            except Exception as e:
                print(f"   ⚠️ Flexible Redemption Record: Error - {e}")
            
            # 14. Locked Redemption Record
            print("   📊 جاري جلب Locked Redemption Record...")
            try:
                locked_redemptions = self.client.get_locked_redemption_record(limit=1000, startTime=start_time, endTime=end_time)
                add_data("Locked Redemption Record", locked_redemptions)
            except Exception as e:
                print(f"   ⚠️ Locked Redemption Record: Error - {e}")
            
            # 15. Flexible Rewards History
            print("   📊 جاري جلب Flexible Rewards History...")
            try:
                flex_rewards = self.client.get_flexible_rewards_history(limit=1000, startTime=start_time, endTime=end_time)
                add_data("Flexible Rewards History", flex_rewards)
            except Exception as e:
                print(f"   ⚠️ Flexible Rewards History: Error - {e}")
            
            # 16. Locked Rewards History
            print("   📊 جاري جلب Locked Rewards History...")
            try:
                locked_rewards = self.client.get_locked_rewards_history(limit=1000, startTime=start_time, endTime=end_time)
                add_data("Locked Rewards History", locked_rewards)
            except Exception as e:
                print(f"   ⚠️ Locked Rewards History: Error - {e}")
            
            # 17. Collateral History
            print("   📊 جاري جلب Collateral History...")
            try:
                collateral = self.client.get_collateral_history(limit=1000, startTime=start_time, endTime=end_time)
                add_data("Collateral History", collateral)
            except Exception as e:
                print(f"   ⚠️ Collateral History: Error - {e}")
            
            # 18. Rate History
            print("   📊 جاري جلب Rate History...")
            try:
                rates = self.client.get_rate_history(limit=1000)
                add_data("Rate History", rates)
            except Exception as e:
                print(f"   ⚠️ Rate History: Error - {e}")
            
            # 19. RWUSD Account
            print("   📊 جاري جلب RWUSD Account...")
            try:
                rwusd_account = self.client.get_rwusd_account()
                add_data("RWUSD Account", [rwusd_account] if rwusd_account else [])
            except Exception as e:
                print(f"   ⚠️ RWUSD Account: Error - {e}")
            
            # 20. RWUSD Quota Details
            print("   📊 جاري جلب RWUSD Quota Details...")
            try:
                rwusd_quota = self.client.get_rwusd_quota_details()
                add_data("RWUSD Quota Details", [rwusd_quota] if rwusd_quota else [])
            except Exception as e:
                print(f"   ⚠️ RWUSD Quota Details: Error - {e}")
            
            # 21. RWUSD Subscription History
            print("   📊 جاري جلب RWUSD Subscription History...")
            try:
                rwusd_subs = self.client.get_rwusd_subscription_history(limit=1000, startTime=start_time, endTime=end_time)
                add_data("RWUSD Subscription History", rwusd_subs)
            except Exception as e:
                print(f"   ⚠️ RWUSD Subscription History: Error - {e}")
            
            # 22. RWUSD Redemption History
            print("   📊 جاري جلب RWUSD Redemption History...")
            try:
                rwusd_redemptions = self.client.get_rwusd_redemption_history(limit=1000, startTime=start_time, endTime=end_time)
                add_data("RWUSD Redemption History", rwusd_redemptions)
            except Exception as e:
                print(f"   ⚠️ RWUSD Redemption History: Error - {e}")
            
            # 23. RWUSD Rewards History
            print("   📊 جاري جلب RWUSD Rewards History...")
            try:
                rwusd_rewards = self.client.get_rwusd_rewards_history(limit=1000, startTime=start_time, endTime=end_time)
                add_data("RWUSD Rewards History", rwusd_rewards)
            except Exception as e:
                print(f"   ⚠️ RWUSD Rewards History: Error - {e}")
            
            # 24. RWUSD Rate History
            print("   📊 جاري جلب RWUSD Rate History...")
            try:
                rwusd_rates = self.client.get_rwusd_rate_history(limit=1000, startTime=start_time, endTime=end_time)
                add_data("RWUSD Rate History", rwusd_rates)
            except Exception as e:
                print(f"   ⚠️ RWUSD Rate History: Error - {e}")
            
            # 25. BFUSD Subscription History
            print("   📊 جاري جلب BFUSD Subscription History...")
            try:
                bfusd_subs = self.client.get_bfusd_subscription_history(limit=1000, startTime=start_time, endTime=end_time)
                add_data("BFUSD Subscription History", bfusd_subs)
            except Exception as e:
                print(f"   ⚠️ BFUSD Subscription History: Error - {e}")
            
            # 26. SOL Staking History
            print("   📊 جاري جلب SOL Staking History...")
            try:
                sol_staking = self.client.get_sol_staking_history(limit=1000, startTime=start_time, endTime=end_time)
                add_data("SOL Staking History", sol_staking)
            except Exception as e:
                print(f"   ⚠️ SOL Staking History: Error - {e}")
            
            # 27. BNSOL Rewards History
            print("   📊 جاري جلب BNSOL Rewards History...")
            try:
                bnsol_rewards = self.client.get_bnsol_rewards_history(limit=1000, startTime=start_time, endTime=end_time)
                add_data("BNSOL Rewards History", bnsol_rewards)
            except Exception as e:
                print(f"   ⚠️ BNSOL Rewards History: Error - {e}")
            
            # 28. BNSOL Rate History
            print("   📊 جاري جلب BNSOL Rate History...")
            try:
                bnsol_rates = self.client.get_bnsol_rate_history(limit=1000, startTime=start_time, endTime=end_time)
                add_data("BNSOL Rate History", bnsol_rates)
            except Exception as e:
                print(f"   ⚠️ BNSOL Rate History: Error - {e}")
            
            # 29. Boost Rewards History
            print("   📊 جاري جلب Boost Rewards History...")
            try:
                boost_rewards = self.client.get_boost_rewards_history(limit=1000, startTime=start_time, endTime=end_time)
                add_data("Boost Rewards History", boost_rewards)
            except Exception as e:
                print(f"   ⚠️ Boost Rewards History: Error - {e}")

            # 30. Asset Dividend History
            print("   📊 جاري جلب Asset Dividend History...")
            try:
                asset_dividends = self.client.get_asset_dividends(limit=500, startTime=start_time, endTime=end_time)
                add_data("Asset Dividend History", asset_dividends)
            except Exception as e:
                print(f"   ⚠️ Asset Dividend History: Error - {e}")
            
            # Save all data to Excel
            if all_data:
                output_file = os.path.join(self.output_dir, "Binance_User_History_Endpoints.xlsx")
                
                with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                    for sheet_name, df in all_data.items():
                        # Excel sheet name must be <= 31 chars
                        sheet_name = sheet_name[:31]
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                print(f"\n✅ تم حفظ جميع البيانات إلى {output_file}")
                print(f"   📊 إجمالي الأوراق: {len(all_data)}")
                return output_file
            else:
                print("⚠️ لم يتم جلب أي بيانات")
                return None
                
        except Exception as e:
            print(f"⚠️ خطأ عام في جلب البيانات: {e}")
            return None
