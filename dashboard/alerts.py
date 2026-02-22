"""
Alerts and Notifications Module
Real-time alerts and notification system for the dashboard
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
import json
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False

class AlertManager:
    """Manage alerts and notifications"""
    
    def __init__(self, storage_path: str = "data/alerts.json"):
        self.storage_path = Path(storage_path)
        self.alerts = self._load_alerts()
    
    def _load_alerts(self) -> Dict:
        """Load alerts from storage"""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return {
            'price_alerts': [],
            'performance_alerts': [],
            'risk_alerts': [],
            'system_alerts': []
        }
    
    def _save_alerts(self):
        """Save alerts to storage"""
        try:
            self.storage_path.parent.mkdir(exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump(self.alerts, f, indent=2, default=str)
        except Exception as e:
            st.error(f"Error saving alerts: {e}")
    
    def add_price_alert(self, symbol: str, target_price: float, condition: str = "above", message: str = ""):
        """Add price alert"""
        alert = {
            'id': f"price_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'symbol': symbol,
            'target_price': target_price,
            'condition': condition,  # 'above' or 'below'
            'message': message,
            'created_at': datetime.now(),
            'triggered': False,
            'triggered_at': None
        }
        self.alerts['price_alerts'].append(alert)
        self._save_alerts()
    
    def add_performance_alert(self, metric: str, threshold: float, condition: str = "below", message: str = ""):
        """Add performance alert"""
        alert = {
            'id': f"perf_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'metric': metric,
            'threshold': threshold,
            'condition': condition,
            'message': message,
            'created_at': datetime.now(),
            'triggered': False,
            'triggered_at': None
        }
        self.alerts['performance_alerts'].append(alert)
        self._save_alerts()
    
    def add_risk_alert(self, risk_type: str, threshold: float, condition: str = "above", message: str = ""):
        """Add risk alert"""
        alert = {
            'id': f"risk_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'risk_type': risk_type,
            'threshold': threshold,
            'condition': condition,
            'message': message,
            'created_at': datetime.now(),
            'triggered': False,
            'triggered_at': None
        }
        self.alerts['risk_alerts'].append(alert)
        self._save_alerts()
    
    def check_price_alerts(self, current_prices: Dict[str, float]):
        """Check and trigger price alerts"""
        for alert in self.alerts['price_alerts']:
            if alert['triggered']:
                continue
            
            symbol = alert['symbol']
            if symbol not in current_prices:
                continue
            
            current_price = current_prices[symbol]
            target_price = alert['target_price']
            condition = alert['condition']
            
            triggered = False
            if condition == "above" and current_price >= target_price:
                triggered = True
            elif condition == "below" and current_price <= target_price:
                triggered = True
            
            if triggered:
                alert['triggered'] = True
                alert['triggered_at'] = datetime.now()
                self._save_alerts()
                self._trigger_notification(alert, current_price)
    
    def check_performance_alerts(self, metrics: Dict[str, float]):
        """Check and trigger performance alerts"""
        for alert in self.alerts['performance_alerts']:
            if alert['triggered']:
                continue
            
            metric_name = alert['metric']
            if metric_name not in metrics:
                continue
            
            current_value = metrics[metric_name]
            threshold = alert['threshold']
            condition = alert['condition']
            
            triggered = False
            if condition == "below" and current_value <= threshold:
                triggered = True
            elif condition == "above" and current_value >= threshold:
                triggered = True
            
            if triggered:
                alert['triggered'] = True
                alert['triggered_at'] = datetime.now()
                self._save_alerts()
                self._trigger_notification(alert, current_value)
    
    def check_risk_alerts(self, risk_metrics: Dict[str, float]):
        """Check and trigger risk alerts"""
        for alert in self.alerts['risk_alerts']:
            if alert['triggered']:
                continue
            
            risk_type = alert['risk_type']
            if risk_type not in risk_metrics:
                continue
            
            current_value = risk_metrics[risk_type]
            threshold = alert['threshold']
            condition = alert['condition']
            
            triggered = False
            if condition == "above" and current_value >= threshold:
                triggered = True
            elif condition == "below" and current_value <= threshold:
                triggered = True
            
            if triggered:
                alert['triggered'] = True
                alert['triggered_at'] = datetime.now()
                self._save_alerts()
                self._trigger_notification(alert, current_value)
    
    def _trigger_notification(self, alert: Dict, current_value: float):
        """Trigger notification for alert"""
        alert_type = alert['id'].split('_')[0]
        
        if alert_type == "price":
            message = f"🔔 Price Alert: {alert['symbol']} is {alert['condition']} ${alert['target_price']} (Current: ${current_value})"
        elif alert_type == "perf":
            message = f"📊 Performance Alert: {alert['metric']} is {alert['condition']} {alert['threshold']} (Current: {current_value})"
        elif alert_type == "risk":
            message = f"⚠️ Risk Alert: {alert['risk_type']} is {alert['condition']} {alert['threshold']} (Current: {current_value})"
        else:
            message = f"🔔 Alert: {alert.get('message', 'Alert triggered')}"
        
        # Add to system alerts
        system_alert = {
            'id': f"system_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'type': 'alert_triggered',
            'message': message,
            'timestamp': datetime.now(),
            'read': False
        }
        self.alerts['system_alerts'].append(system_alert)
        self._save_alerts()
        
        # Show in dashboard
        st.warning(message)
    
    def get_active_alerts(self) -> List[Dict]:
        """Get all active (non-triggered) alerts"""
        active_alerts = []
        
        for alert_type in ['price_alerts', 'performance_alerts', 'risk_alerts']:
            for alert in self.alerts[alert_type]:
                if not alert['triggered']:
                    active_alerts.append(alert)
        
        return active_alerts
    
    def get_recent_notifications(self, limit: int = 10) -> List[Dict]:
        """Get recent notifications"""
        system_alerts = self.alerts['system_alerts']
        # Sort by timestamp and get recent ones
        system_alerts.sort(key=lambda x: x['timestamp'], reverse=True)
        return system_alerts[:limit]
    
    def mark_notification_read(self, alert_id: str):
        """Mark notification as read"""
        for alert in self.alerts['system_alerts']:
            if alert['id'] == alert_id:
                alert['read'] = True
                self._save_alerts()
                break
    
    def clear_old_alerts(self, days: int = 30):
        """Clear old triggered alerts"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for alert_type in ['price_alerts', 'performance_alerts', 'risk_alerts']:
            self.alerts[alert_type] = [
                alert for alert in self.alerts[alert_type]
                if not alert['triggered'] or 
                (alert['triggered_at'] and pd.to_datetime(alert['triggered_at']) > cutoff_date)
            ]
        
        # Clear old system alerts
        self.alerts['system_alerts'] = [
            alert for alert in self.alerts['system_alerts']
            if pd.to_datetime(alert['timestamp']) > cutoff_date
        ]
        
        self._save_alerts()

class AlertUI:
    """UI components for alerts"""
    
    @staticmethod
    def show_alert_sidebar(alert_manager: AlertManager):
        """Show alert sidebar"""
        st.sidebar.header("🔔 التنبيهات")
        
        # Recent notifications
        recent_notifications = alert_manager.get_recent_notifications(5)
        unread_count = sum(1 for n in recent_notifications if not n['read'])
        
        if unread_count > 0:
            st.sidebar.warning(f"🔔 {unread_count} تنبيهات غير مقروءة")
        
        for notification in recent_notifications:
            if notification['read']:
                st.sidebar.info(f"✅ {notification['message']}")
            else:
                st.sidebar.warning(f"🔔 {notification['message']}")
                if st.sidebar.button(f"علامة كمقروء", key=f"read_{notification['id']}"):
                    alert_manager.mark_notification_read(notification['id'])
                    st.rerun()
        
        # Active alerts
        active_alerts = alert_manager.get_active_alerts()
        if active_alerts:
            st.sidebar.subheader("🎯 التنبيهات النشطة")
            for alert in active_alerts[:3]:  # Show only first 3
                alert_type = alert['id'].split('_')[0]
                if alert_type == "price":
                    st.sidebar.write(f"💰 {alert['symbol']} {alert['condition']} ${alert['target_price']}")
                elif alert_type == "perf":
                    st.sidebar.write(f"📊 {alert['metric']} {alert['condition']} {alert['threshold']}")
                elif alert_type == "risk":
                    st.sidebar.write(f"⚠️ {alert['risk_type']} {alert['condition']} {alert['threshold']}")
    
    @staticmethod
    def show_alert_config(alert_manager: AlertManager):
        """Show alert configuration page"""
        st.header("⚙️ إعدادات التنبيهات")
        
        tab1, tab2, tab3, tab4 = st.tabs(["🔔 تنبيهات الأسعار", "📊 تنبيهات الأداء", "⚠️ تنبيهات المخاطر", "🔧 الإعدادات"])
        
        with tab1:
            st.subheader("تنبيهات الأسعار")
            
            col1, col2 = st.columns(2)
            
            with col1:
                symbol = st.text_input("رمز العملة", placeholder="BTCUSDT")
                target_price = st.number_input("السعر المستهدف", value=0.0, step=0.01)
            
            with col2:
                condition = st.selectbox("الشرط", ["فوق", "تحت"])
                message = st.text_input("رسالة مخصصة (اختياري)")
            
            if st.button("➕ إضافة تنبيه سعر"):
                if symbol and target_price > 0:
                    alert_manager.add_price_alert(
                        symbol, target_price, 
                        "above" if condition == "فوق" else "below", 
                        message
                    )
                    st.success("✅ تم إضافة تنبيه السعر")
                else:
                    st.error("❌ يرجى ملء جميع الحقول المطلوبة")
        
        with tab2:
            st.subheader("تنبيهات الأداء")
            
            col1, col2 = st.columns(2)
            
            with col1:
                metric = st.selectbox("المؤشر", [
                    "win_rate", "sharpe_ratio", "max_drawdown", "profit_factor"
                ])
                threshold = st.number_input("الحد", value=0.0, step=0.01)
            
            with col2:
                condition = st.selectbox("الشرط", ["أقل من", "أعلى من"])
                message = st.text_input("رسالة مخصصة (اختياري)")
            
            if st.button("➕ إضافة تنبيه أداء"):
                if threshold > 0:
                    alert_manager.add_performance_alert(
                        metric, threshold,
                        "below" if condition == "أقل من" else "above",
                        message
                    )
                    st.success("✅ تم إضافة تنبيه الأداء")
                else:
                    st.error("❌ يرجى تحديد حد صحيح")
        
        with tab3:
            st.subheader("تنبيهات المخاطر")
            
            col1, col2 = st.columns(2)
            
            with col1:
                risk_type = st.selectbox("نوع المخاطرة", [
                    "max_drawdown", "volatility", "var_95", "concentration_risk"
                ])
                threshold = st.number_input("الحد (%)", value=0.0, step=0.01)
            
            with col2:
                condition = st.selectbox("الشرط", ["أعلى من", "أقل من"])
                message = st.text_input("رسالة مخصصة (اختياري)")
            
            if st.button("➕ إضافة تنبيه مخاطر"):
                if threshold > 0:
                    alert_manager.add_risk_alert(
                        risk_type, threshold,
                        "above" if condition == "أعلى من" else "below",
                        message
                    )
                    st.success("✅ تم إضافة تنبيه المخاطر")
                else:
                    st.error("❌ يرجى تحديد حد صحيح")
        
        with tab4:
            st.subheader("الإعدادات العامة")
            
            # Clear old alerts
            days_to_keep = st.number_input("عدد الأيام للاحتفاظ بالتنبيهات", value=30, min_value=1)
            
            if st.button("🧹 تنظيف التنبيهات القديمة"):
                alert_manager.clear_old_alerts(days_to_keep)
                st.success(f"✅ تم تنظيف التنبيهات الأقدم من {days_to_keep} يوم")
            
            # Alert settings
            st.subheader("إعدادات الإشعارات")
            
            email_notifications = st.checkbox("الإشعارات عبر البريد الإلكتروني")
            if email_notifications:
                email = st.text_input("البريد الإلكتروني")
                st.info("🔧 ميزة البريد الإلكتروني قيد التطوير")
            
            sound_alerts = st.checkbox("تنبيهات صوتية")
            if sound_alerts:
                st.info("🔧 ميزة التنبيهات الصوتية قيد التطوير")

class NotificationService:
    """Notification service for sending alerts"""
    
    def __init__(self):
        self.email_config = None
    
    def configure_email(self, smtp_server: str, port: int, username: str, password: str):
        """Configure email settings"""
        self.email_config = {
            'smtp_server': smtp_server,
            'port': port,
            'username': username,
            'password': password
        }
    
    def send_email_alert(self, to_email: str, subject: str, message: str):
        """Send email alert"""
        if not EMAIL_AVAILABLE:
            st.error("❌ Email functionality not available")
            return False
            
        if not self.email_config:
            st.error("❌ Email not configured")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config['username']
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(message, 'plain'))
            
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['port'])
            server.starttls()
            server.login(self.email_config['username'], self.email_config['password'])
            
            text = msg.as_string()
            server.sendmail(self.email_config['username'], to_email, text)
            server.quit()
            
            return True
        
        except Exception as e:
            st.error(f"❌ Error sending email: {e}")
            return False
    
    def send_webhook_notification(self, webhook_url: str, data: Dict):
        """Send webhook notification"""
        try:
            import requests
        except ImportError:
            st.error("❌ Requests library not available for webhook notifications")
            return False
            
        try:
            payload = {
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            return response.status_code == 200
        
        except Exception as e:
            st.error(f"❌ Error sending webhook: {e}")
            return False

# Alert templates
class AlertTemplates:
    """Predefined alert templates"""
    
    PRICE_TEMPLATES = {
        "BTC Above $50k": {
            'symbol': 'BTCUSDT',
            'target_price': 50000,
            'condition': 'above',
            'message': 'Bitcoin has reached $50,000!'
        },
        "ETH Below $2k": {
            'symbol': 'ETHUSDT',
            'target_price': 2000,
            'condition': 'below',
            'message': 'Ethereum has dropped below $2,000'
        }
    }
    
    PERFORMANCE_TEMPLATES = {
        "Low Win Rate": {
            'metric': 'win_rate',
            'threshold': 40,
            'condition': 'below',
            'message': 'Win rate has dropped below 40%'
        },
        "High Drawdown": {
            'metric': 'max_drawdown',
            'threshold': 15,
            'condition': 'above',
            'message': 'Maximum drawdown has exceeded 15%'
        }
    }
    
    RISK_TEMPLATES = {
        "High Volatility": {
            'risk_type': 'volatility',
            'threshold': 30,
            'condition': 'above',
            'message': 'Portfolio volatility has exceeded 30%'
        },
        "High VaR": {
            'risk_type': 'var_95',
            'threshold': 5,
            'condition': 'above',
            'message': 'Value at Risk (95%) has exceeded 5%'
        }
    }
    
    @staticmethod
    def apply_template(alert_manager: AlertManager, template_type: str, template_name: str):
        """Apply a predefined template"""
        templates = {
            'price': AlertTemplates.PRICE_TEMPLATES,
            'performance': AlertTemplates.PERFORMANCE_TEMPLATES,
            'risk': AlertTemplates.RISK_TEMPLATES
        }
        
        if template_type not in templates:
            st.error(f"❌ Unknown template type: {template_type}")
            return
        
        template = templates[template_type].get(template_name)
        if not template:
            st.error(f"❌ Template not found: {template_name}")
            return
        
        if template_type == 'price':
            alert_manager.add_price_alert(**template)
        elif template_type == 'performance':
            alert_manager.add_performance_alert(**template)
        elif template_type == 'risk':
            alert_manager.add_risk_alert(**template)
        
        st.success(f"✅ Applied template: {template_name}")

# Integration with main dashboard
def initialize_alert_system():
    """Initialize alert system in dashboard"""
    if 'alert_manager' not in st.session_state:
        st.session_state.alert_manager = AlertManager()
    
    if 'notification_service' not in st.session_state:
        st.session_state.notification_service = NotificationService()
    
    return st.session_state.alert_manager

def check_and_trigger_alerts(alert_manager: AlertManager, trades_df: pd.DataFrame, fifo_df: pd.DataFrame):
    """Check all alerts and trigger if conditions are met"""
    try:
        # Get current prices (mock data for now)
        current_prices = {}
        if not trades_df.empty and 'symbol' in trades_df.columns and 'price' in trades_df.columns:
            latest_prices = trades_df.groupby('symbol')['price'].last()
            current_prices = latest_prices.to_dict()
        
        # Get performance metrics
        metrics = {}
        if not fifo_df.empty and 'realized_pnl' in fifo_df.columns:
            metrics['win_rate'] = len(fifo_df[fifo_df['realized_pnl'] > 0]) / len(fifo_df) * 100
            metrics['total_pnl'] = fifo_df['realized_pnl'].sum()
            metrics['avg_pnl'] = fifo_df['realized_pnl'].mean()
        
        # Get risk metrics
        risk_metrics = {}
        if not fifo_df.empty and 'realized_pnl' in fifo_df.columns:
            returns = fifo_df['realized_pnl']
            risk_metrics['volatility'] = returns.std()
            risk_metrics['var_95'] = returns.quantile(0.05)
        
        # Check alerts
        alert_manager.check_price_alerts(current_prices)
        alert_manager.check_performance_alerts(metrics)
        alert_manager.check_risk_alerts(risk_metrics)
        
    except Exception as e:
        st.error(f"❌ Error checking alerts: {e}")
