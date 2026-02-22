"""
Ledger Engine - Fetch and display complete ledger data from Binance API
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import pandas as pd
from datetime import datetime
import json

from api.binance_client import BinanceClient


class LedgerEngine:
    def __init__(self):
        self.client = None
        self.ledger_data = {}
        
    def connect(self):
        """Connect to Binance API"""
        try:
            self.client = BinanceClient()
            # Test connection with account info
            account_info = self.client.get_account_info()
            return True, "Connected to Binance API successfully"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    def fetch_all_ledger_data(self, start_date="2024-01-01"):
        """Fetch all ledger data from various endpoints"""
        if not self.client:
            success, msg = self.connect()
            if not success:
                return False, msg
        
        self.ledger_data = {}
        errors = []
        
        try:
            # 1. Get Account Info
            self.ledger_data['account_info'] = self.client.get_account_info()
        except Exception as e:
            errors.append(f"Account Info: {str(e)}")
        
        try:
            # 2. Get Deposits
            self.ledger_data['deposits'] = self.client.get_deposits()
        except Exception as e:
            errors.append(f"Deposits: {str(e)}")
            self.ledger_data['deposits'] = []
        
        try:
            # 3. Get Withdrawals
            self.ledger_data['withdrawals'] = self.client.get_withdrawals()
        except Exception as e:
            errors.append(f"Withdrawals: {str(e)}")
            self.ledger_data['withdrawals'] = []
        
        try:
            # 4. Get My Trades
            self.ledger_data['trades'] = self.client.get_my_trades(limit=1000)
        except Exception as e:
            errors.append(f"Trades: {str(e)}")
            self.ledger_data['trades'] = []
        
        try:
            # 5. Get Internal Transfers
            self.ledger_data['transfers'] = self.client.get_internal_transfers(limit=1000)
        except Exception as e:
            errors.append(f"Transfers: {str(e)}")
            self.ledger_data['transfers'] = []
        
        try:
            # 6. Get Asset Dividends
            self.ledger_data['dividends'] = self.client.get_asset_dividends(limit=500)
        except Exception as e:
            errors.append(f"Dividends: {str(e)}")
            self.ledger_data['dividends'] = []
        
        try:
            # 7. Get Deposit Addresses
            self.ledger_data['deposit_addresses'] = self.client.get_deposit_addresses()
        except Exception as e:
            errors.append(f"Deposit Addresses: {str(e)}")
            self.ledger_data['deposit_addresses'] = []
        
        try:
            # 8. Get Flexible Rewards History (Earn)
            self.ledger_data['flexible_rewards'] = self.client.get_flexible_rewards_history(limit=500)
        except Exception as e:
            errors.append(f"Flexible Rewards: {str(e)}")
            self.ledger_data['flexible_rewards'] = []
        
        try:
            # 9. Get Locked Rewards History (Earn)
            self.ledger_data['locked_rewards'] = self.client.get_locked_rewards_history(limit=500)
        except Exception as e:
            errors.append(f"Locked Rewards: {str(e)}")
            self.ledger_data['locked_rewards'] = []
        
        try:
            # 10. Get All Orders
            self.ledger_data['all_orders'] = self.client.get_all_orders(limit=500)
        except Exception as e:
            errors.append(f"All Orders: {str(e)}")
            self.ledger_data['all_orders'] = []
        
        if errors:
            return True, f"Data fetched with {len(errors)} errors"
        return True, "All ledger data fetched successfully"
    
    def save_to_excel(self, output_path=None):
        """Save ledger data to Excel file"""
        if not self.ledger_data:
            return False, "No data to save"
        
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join("data", f"ledger_data_{timestamp}.xlsx")
        
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Account Info
                if 'account_info' in self.ledger_data:
                    acc = self.ledger_data['account_info']
                    if 'balances' in acc:
                        df = pd.DataFrame(acc['balances'])
                        df.to_excel(writer, sheet_name='Account_Balances', index=False)
                
                # Deposits
                if self.ledger_data.get('deposits'):
                    df = pd.DataFrame(self.ledger_data['deposits'])
                    df.to_excel(writer, sheet_name='Deposits', index=False)
                
                # Withdrawals
                if self.ledger_data.get('withdrawals'):
                    df = pd.DataFrame(self.ledger_data['withdrawals'])
                    df.to_excel(writer, sheet_name='Withdrawals', index=False)
                
                # Trades
                if self.ledger_data.get('trades'):
                    df = pd.DataFrame(self.ledger_data['trades'])
                    df.to_excel(writer, sheet_name='Trades', index=False)
                
                # Transfers
                if self.ledger_data.get('transfers'):
                    df = pd.DataFrame(self.ledger_data['transfers'])
                    df.to_excel(writer, sheet_name='Transfers', index=False)
                
                # Dividends
                if self.ledger_data.get('dividends'):
                    df = pd.DataFrame(self.ledger_data['dividends'])
                    df.to_excel(writer, sheet_name='Dividends', index=False)
                
                # Deposit Addresses
                if self.ledger_data.get('deposit_addresses'):
                    df = pd.DataFrame(self.ledger_data['deposit_addresses'])
                    df.to_excel(writer, sheet_name='Deposit_Addresses', index=False)
                
                # Flexible Rewards
                if self.ledger_data.get('flexible_rewards'):
                    df = pd.DataFrame(self.ledger_data['flexible_rewards'])
                    df.to_excel(writer, sheet_name='Flexible_Rewards', index=False)
                
                # Locked Rewards
                if self.ledger_data.get('locked_rewards'):
                    df = pd.DataFrame(self.ledger_data['locked_rewards'])
                    df.to_excel(writer, sheet_name='Locked_Rewards', index=False)
                
                # All Orders
                if self.ledger_data.get('all_orders'):
                    df = pd.DataFrame(self.ledger_data['all_orders'])
                    df.to_excel(writer, sheet_name='All_Orders', index=False)
            
            return True, output_path
        except Exception as e:
            return False, f"Failed to save Excel: {str(e)}"
    
    def save_to_json(self, output_path=None):
        """Save ledger data to JSON file"""
        if not self.ledger_data:
            return False, "No data to save"
        
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join("data", f"ledger_data_{timestamp}.json")
        
        try:
            # Convert non-serializable objects to dict
            serializable_data = {}
            for key, value in self.ledger_data.items():
                if isinstance(value, dict):
                    serializable_data[key] = value
                elif isinstance(value, list):
                    serializable_data[key] = value
                else:
                    serializable_data[key] = str(value)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_data, f, indent=2, ensure_ascii=False)
            
            return True, output_path
        except Exception as e:
            return False, f"Failed to save JSON: {str(e)}"
    
    def get_summary(self):
        """Get a summary of ledger data"""
        summary = []
        summary.append("=" * 50)
        summary.append("LEDGER SUMMARY")
        summary.append("=" * 50)
        
        if 'account_info' in self.ledger_data:
            acc = self.ledger_data['account_info']
            summary.append(f"Account Type: {acc.get('accountType', 'N/A')}")
            summary.append(f"Commission Rate: {acc.get('commissionRate', 'N/A')}")
        
        summary.append("-" * 50)
        summary.append("DATA COUNTS:")
        summary.append(f"  Deposits: {len(self.ledger_data.get('deposits', []))}")
        summary.append(f"  Withdrawals: {len(self.ledger_data.get('withdrawals', []))}")
        summary.append(f"  Trades: {len(self.ledger_data.get('trades', []))}")
        summary.append(f"  Transfers: {len(self.ledger_data.get('transfers', []))}")
        summary.append(f"  Dividends: {len(self.ledger_data.get('dividends', []))}")
        summary.append(f"  Deposit Addresses: {len(self.ledger_data.get('deposit_addresses', []))}")
        summary.append(f"  Flexible Rewards: {len(self.ledger_data.get('flexible_rewards', []))}")
        summary.append(f"  Locked Rewards: {len(self.ledger_data.get('locked_rewards', []))}")
        summary.append(f"  All Orders: {len(self.ledger_data.get('all_orders', []))}")
        summary.append("=" * 50)
        
        return "\n".join(summary)


def show_ledger_dialog(parent):
    """Show the Ledger Engine dialog"""
    dialog = tk.Toplevel(parent)
    dialog.title("📒 Ledger Engine - Binance API")
    dialog.geometry("700x600")
    dialog.transient(parent)
    
    # Status
    status_label = tk.Label(dialog, text="Initializing...", font=("Segoe UI", 12))
    status_label.pack(pady=10)
    
    # Progress
    progress = ttk.Progressbar(dialog, mode='indeterminate')
    progress.pack(fill='x', padx=20, pady=5)
    
    # Text area for results
    result_text = scrolledtext.ScrolledText(
        dialog, 
        width=80, 
        height=25, 
        font=("Consolas", 10)
    )
    result_text.pack(padx=20, pady=10, fill='both', expand=True)
    
    # Buttons frame
    btn_frame = tk.Frame(dialog)
    btn_frame.pack(pady=10)
    
    ledger_engine = LedgerEngine()
    
    def run_ledger():
        """Fetch and display ledger data"""
        progress.start()
        status_label.config(text="Connecting to Binance API...")
        
        # Connect
        success, msg = ledger_engine.connect()
        if not success:
            progress.stop()
            status_label.config(text=f"❌ {msg}")
            messagebox.showerror("Connection Error", msg)
            return
        
        status_label.config(text="Fetching ledger data...")
        result_text.insert('end', "📡 Connecting to Binance API...\n")
        result_text.see('end')
        
        # Fetch all data
        success, msg = ledger_engine.fetch_all_ledger_data()
        
        # Display summary
        result_text.insert('end', f"\n{msg}\n\n")
        result_text.insert('end', ledger_engine.get_summary())
        result_text.see('end')
        
        progress.stop()
        
        if success:
            status_label.config(text="✅ Ledger data fetched successfully")
            # Enable save buttons
            save_excel_btn.config(state='normal')
            save_json_btn.config(state='normal')
        else:
            status_label.config(text=f"❌ {msg}")
    
    def save_excel():
        success, path = ledger_engine.save_to_excel()
        if success:
            messagebox.showinfo("Success", f"Data saved to:\n{path}")
        else:
            messagebox.showerror("Error", path)
    
    def save_json():
        success, path = ledger_engine.save_to_json()
        if success:
            messagebox.showinfo("Success", f"Data saved to:\n{path}")
        else:
            messagebox.showerror("Error", path)
    
    # Buttons
    tk.Button(
        btn_frame, 
        text="🚀 Fetch Ledger Data", 
        command=run_ledger,
        font=("Segoe UI", 12),
        bg="#2196F3",
        fg="white",
        width=20
    ).pack(side='left', padx=5)
    
    save_excel_btn = tk.Button(
        btn_frame, 
        text="💾 Save to Excel", 
        command=save_excel,
        font=("Segoe UI", 12),
        bg="#4CAF50",
        fg="white",
        width=18,
        state='disabled'
    )
    save_excel_btn.pack(side='left', padx=5)
    
    save_json_btn = tk.Button(
        btn_frame, 
        text="📄 Save to JSON", 
        command=save_json,
        font=("Segoe UI", 12),
        bg="#FF9800",
        fg="white",
        width=18,
        state='disabled'
    )
    save_json_btn.pack(side='left', padx=5)
    
    tk.Button(
        dialog, 
        text="Close", 
        command=dialog.destroy,
        font=("Segoe UI", 12),
        width=15
    ).pack(pady=10)


# Standalone function for CLI usage
def run_ledger_cli():
    """Run ledger engine from CLI"""
    print("=" * 50)
    print("Binance Ledger Engine")
    print("=" * 50)
    
    engine = LedgerEngine()
    
    # Connect
    print("\n📡 Connecting to Binance API...")
    success, msg = engine.connect()
    if not success:
        print(f"❌ {msg}")
        return
    
    print("✅ Connected successfully")
    
    # Fetch data
    print("\n📥 Fetching ledger data...")
    success, msg = engine.fetch_all_ledger_data()
    print(msg)
    
    # Show summary
    print("\n" + engine.get_summary())
    
    # Save to Excel
    print("\n💾 Saving to Excel...")
    success, path = engine.save_to_excel()
    if success:
        print(f"✅ Saved to: {path}")
    else:
        print(f"❌ {path}")
    
    # Save to JSON
    print("\n📄 Saving to JSON...")
    success, path = engine.save_to_json()
    if success:
        print(f"✅ Saved to: {path}")
    else:
        print(f"❌ {path}")


if __name__ == "__main__":
    run_ledger_cli()
