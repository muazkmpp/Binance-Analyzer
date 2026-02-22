import tkinter as tk
from tkinter import messagebox
import subprocess
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Import user config
sys.path.insert(0, BASE_DIR)
from config.user_config import user_config

# ==================================================
# API Configuration Check and Setup
# ==================================================
def check_api_configured():
    """Check if API keys are configured"""
    return user_config.is_configured()


def show_api_setup_dialog(parent=None):
    """Show API configuration dialog"""
    dialog = tk.Toplevel(parent if parent else root)
    dialog.title("🔐 API Configuration / إعداد مفاتيح API")
    dialog.geometry("500x630")
    dialog.transient(parent if parent else root)
    dialog.grab_set()
    dialog.resizable(False, False)
    
    # Center the dialog
    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
    y = (dialog.winfo_screenheight() // 2) - (630 // 2)
    dialog.geometry(f"500x630+{x}+{y}")
    
    # Title
    title_label = tk.Label(
        dialog,
        text="📋 User & API Configuration",
        font=("Segoe UI", 16, "bold")
    )
    title_label.pack(pady=15)
    
    # Form frame
    form_frame = tk.Frame(dialog, padx=20)
    form_frame.pack(fill="both", expand=True)
    
    # User Name
    tk.Label(form_frame, text="👤 User Name:", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(10, 3))
    user_name_entry = tk.Entry(form_frame, font=("Segoe UI", 12), width=45)
    user_name_entry.pack(fill="x", pady=3)
    user_name_entry.insert(0, user_config.config.get("user_name", ""))
    
    # Enable right-click menu for all entries
    def create_context_menu(entry):
        menu = tk.Menu(entry, tearoff=0)
        menu.add_command(label="Cut", command=lambda: entry.event_generate("<<Cut>>"))
        menu.add_command(label="Copy", command=lambda: entry.event_generate("<<Copy>>"))
        menu.add_command(label="Paste", command=lambda: entry.event_generate("<<Paste>>"))
        menu.add_separator()
        menu.add_command(label="Select All", command=lambda: entry.select_range(0, "end"))
        
        def show_menu(event):
            menu.tk_popup(event.x_root, event.y_root)
        
        entry.bind("<Button-3>", show_menu)  # Right-click
    
    create_context_menu(user_name_entry)
    
    # Account Name
    tk.Label(form_frame, text="📁 Account Name:", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(10, 3))
    account_name_entry = tk.Entry(form_frame, font=("Segoe UI", 12), width=45)
    account_name_entry.pack(fill="x", pady=3)
    account_name_entry.insert(0, user_config.config.get("account_name", ""))
    create_context_menu(account_name_entry)
    
    # Platform Name
    tk.Label(form_frame, text="🌐 Platform:", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(10, 3))
    platform_name_entry = tk.Entry(form_frame, font=("Segoe UI", 12), width=45)
    platform_name_entry.pack(fill="x", pady=3)
    platform_name_entry.insert(0, user_config.config.get("platform_name", "Binance"))
    create_context_menu(platform_name_entry)
    
    # API Key
    tk.Label(form_frame, text="🔑 API Key:", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(10, 3))
    api_key_entry = tk.Entry(form_frame, font=("Segoe UI", 12), width=45, show="*")
    api_key_entry.pack(fill="x", pady=3)
    api_key_entry.insert(0, user_config.config.get("api_key", ""))
    create_context_menu(api_key_entry)
    
    # API Secret
    tk.Label(form_frame, text="🔐 API Secret:", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(10, 3))
    api_secret_entry = tk.Entry(form_frame, font=("Segoe UI", 12), width=45, show="*")
    api_secret_entry.pack(fill="x", pady=3)
    api_secret_entry.insert(0, user_config.config.get("api_secret", ""))
    create_context_menu(api_secret_entry)
    
    # Show/Hide keys toggle
    show_keys = tk.BooleanVar(value=False)
    
    def toggle_show_keys():
        if show_keys.get():
            api_key_entry.config(show="")
            api_secret_entry.config(show="")
        else:
            api_key_entry.config(show="*")
            api_secret_entry.config(show="*")
    
    tk.Checkbutton(
        form_frame,
        text="Show API keys",
        variable=show_keys,
        command=toggle_show_keys,
        font=("Segoe UI", 10)
    ).pack(anchor="w", pady=5)
    
    # Help text for copy/paste
    tk.Label(
        form_frame,
        text="💡 Tip: Right-click to Copy/Paste",
        font=("Segoe UI", 9),
        fg="gray"
    ).pack(anchor="w", pady=3)
    
    # Info label
    info_label = tk.Label(
        dialog,
        text="📁 Data saved to: config/user_config.json",
        font=("Segoe UI", 9),
        fg="blue"
    )
    info_label.pack(pady=8)
    
    # Result label
    result_label = tk.Label(dialog, text="", font=("Segoe UI", 10))
    result_label.pack(pady=3)
    
    def save_config():
        user_name = user_name_entry.get().strip()
        account_name = account_name_entry.get().strip()
        platform_name = platform_name_entry.get().strip()
        api_key = api_key_entry.get().strip()
        api_secret = api_secret_entry.get().strip()
        
        if not user_name:
            result_label.config(text="⚠️ Please enter user name", fg="orange")
            return
        
        if not account_name:
            result_label.config(text="⚠️ Please enter account name", fg="orange")
            return
        
        if not api_key or not api_secret:
            result_label.config(text="⚠️ Please enter both API key and secret", fg="orange")
            return
        
        # Save configuration to user_config.json
        user_config.set_config(user_name, account_name, platform_name, api_key, api_secret)
        
        # Also save to .env file
        env_path = os.path.join(BASE_DIR, "config", ".env")
        try:
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write(f"BINANCE_API_KEY={api_key}\n")
                f.write(f"BINANCE_SECRET_KEY={api_secret}\n")
        except Exception as e:
            print(f"Error saving .env file: {e}")
        
        result_label.config(text="✅ Configuration saved successfully!", fg="green")
        
        # Refresh main window status
        if not parent:
            update_status_display()
        
        # Show success message and close
        dialog.after(1000, lambda: [
            dialog.destroy(),
            messagebox.showinfo("Success", "✅ تم حفظ الإعدادات بنجاح!\n\nYour API keys have been saved.")
        ])
    
    def clear_config():
        """Clear all saved data"""
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to delete all saved data?\nهل أنت متأكد من حذف جميع البيانات؟"):
            # Clear user_config.json
            user_config.set_config("", "", "", "", "")
            
            # Clear .env file
            env_path = os.path.join(BASE_DIR, "config", ".env")
            try:
                with open(env_path, 'w', encoding='utf-8') as f:
                    f.write("BINANCE_API_KEY=\n")
                    f.write("BINANCE_SECRET_KEY=\n")
            except Exception as e:
                print(f"Error clearing .env file: {e}")
            
            # Clear entry fields
            user_name_entry.delete(0, "end")
            account_name_entry.delete(0, "end")
            platform_name_entry.delete(0, "end")
            api_key_entry.delete(0, "end")
            api_secret_entry.delete(0, "end")
            
            # Refresh main window status
            if not parent:
                update_status_display()
            
            result_label.config(text="🗑️ All data cleared!", fg="red")
    
    # Buttons frame - Standard buttons
    button_frame = tk.Frame(dialog, relief="groove", bd=2)
    button_frame.pack(fill="x", padx=20, pady=15)
    
    # Left side - Save button
    save_frame = tk.Frame(button_frame)
    save_frame.pack(side="left", padx=5, pady=10)
    
    save_btn = tk.Button(
        save_frame,
        text="💾 Save Account Data",
        command=save_config,
        font=("Segoe UI", 12, "bold"),
        bg="#4CAF50",
        fg="white",
        width=20,
        height=2,
        cursor="hand2",
        relief="raised",
        bd=3
    )
    save_btn.pack()
    
    # Right side - Cancel and Clear buttons
    right_frame = tk.Frame(button_frame)
    right_frame.pack(side="right", padx=5, pady=10)
    
    # Clear button
    clear_btn = tk.Button(
        right_frame,
        text="🗑️ Clear Data",
        command=clear_config,
        font=("Segoe UI", 11),
        bg="#f44336",
        fg="white",
        width=15,
        height=1,
        cursor="hand2",
        relief="raised",
        bd=3
    )
    clear_btn.pack(pady=2)
    
    # Cancel button
    cancel_btn = tk.Button(
        right_frame,
        text="❌ Cancel",
        command=dialog.destroy,
        font=("Segoe UI", 11),
        width=15,
        height=1,
        cursor="hand2",
        relief="raised",
        bd=3
    )
    cancel_btn.pack(pady=2)
    
    return dialog


def show_api_missing_dialog():
    """Show dialog when API keys are missing"""
    dialog = tk.Toplevel(root)
    dialog.title("⚠️ API Keys Required")
    dialog.geometry("450x300")
    dialog.transient(root)
    dialog.grab_set()
    
    # Center
    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() // 2) - (450 // 2)
    y = (dialog.winfo_screenheight() // 2) - (300 // 2)
    dialog.geometry(f"450x300+{x}+{y}")
    
    # Warning icon and title
    tk.Label(
        dialog,
        text="⚠️",
        font=("Segoe UI", 48)
    ).pack(pady=10)
    
    tk.Label(
        dialog,
        text="API Keys Not Configured",
        font=("Segoe UI", 16, "bold")
    ).pack(pady=5)
    
    tk.Label(
        dialog,
        text="Please configure your API keys before running this function.\nالرجاء إعداد مفاتيح API قبل التشغيل.",
        font=("Segoe UI", 11),
        justify="center"
    ).pack(pady=10)
    
    # Buttons
    btn_frame = tk.Frame(dialog)
    btn_frame.pack(pady=20)
    
    tk.Button(
        btn_frame,
        text="🔐 Configure Now",
        command=lambda: [dialog.destroy(), show_api_setup_dialog()],
        font=("Segoe UI", 12, "bold"),
        bg="#4CAF50",
        fg="white",
        width=18
    ).pack(pady=5)
    
    tk.Button(
        btn_frame,
        text="❌ Cancel",
        command=dialog.destroy,
        font=("Segoe UI", 12),
        width=18
    ).pack(pady=5)
    
    return dialog


# ==================================================
# Helpers
# ==================================================
def run_command(command, title):
    # Check API configuration before running commands that need API
    if not check_api_configured():
        show_api_missing_dialog()
        return
    
    try:
        status_label.config(text=f"⏳ {title}...")
        subprocess.run(command, check=True)
        status_label.config(text=f"✅ {title} completed")
    except subprocess.CalledProcessError as e:
        status_label.config(text="❌ Error")
        messagebox.showerror("Error", str(e))


# ==================================================
# Actions
# ==================================================
def fetch_data():
    run_command([sys.executable, "main.py", "--fetch"], "Fetching Binance Data")


def fetch_user_history():
    """Fetch all user history endpoints and save to Excel"""
    if not check_api_configured():
        show_api_missing_dialog()
        return
        
    status_label.config(text="⏳ Fetching User History Data...")
    try:
        from core.data_fetcher import DataFetcher
        fetcher = DataFetcher()
        output_file = fetcher.fetch_all_user_history(start_date="2024-01-01")
        if output_file:
            status_label.config(text="✅ User History Data Fetched Successfully")
            messagebox.showinfo("Success", f"Data saved to:\n{output_file}")
        else:
            status_label.config(text="⚠️ No data fetched")
            messagebox.showwarning("Warning", "No data was fetched from the API")
    except Exception as e:
        status_label.config(text="❌ Error")
        messagebox.showerror("Error", str(e))


def calculate_fifo():
    run_command([sys.executable, "main.py", "--fifo"], "Calculating FIFO PnL")


def calculate_portfolio():
    run_command([sys.executable, "main.py", "--portfolio"], "Calculating Portfolio")


def generate_reports():
    run_command([sys.executable, "main.py", "--report"], "Generating Excel Report")


def generate_tax_report():
    """Generate tax report with system selection dialog"""
    if not check_api_configured():
        show_api_missing_dialog()
        return
    
    # Simple tax system selection
    tax_system = "US"  # Default
    
    # Ask user for tax system
    system_names = {
        "1": ("US", "United States"),
        "2": ("UK", "United Kingdom"),
        "3": ("DE", "Germany"),
        "4": ("EG", "Egypt"),
        "5": ("SA", "Saudi Arabia"),
        "6": ("AE", "UAE"),
        "7": ("GENERIC", "Generic"),
        "8": ("ALL", "All Systems")
    }
    
    # Show selection dialog
    selection = tk.StringVar(value="1")
    
    def run_tax_report():
        selected = selection.get()
        code, name = system_names.get(selected, ("US", "US"))
        status_label.config(text=f"⏳ Generating {name} Tax Report...")
        
        try:
            if code == "ALL":
                # Generate for all systems
                subprocess.run([sys.executable, "main.py", "--tax", "--all"], check=True)
            else:
                # Generate for specific system
                subprocess.run([sys.executable, "main.py", "--tax", "--tax-system", code], check=True)
            
            status_label.config(text=f"✅ {name} Tax Report completed")
            messagebox.showinfo("Success", f"Tax report generated successfully!\nCheck the reports folder.")
        except subprocess.CalledProcessError as e:
            status_label.config(text="❌ Error")
            messagebox.showerror("Error", str(e))
        
        dialog.destroy()
    
    # Create dialog
    dialog = tk.Toplevel(root)
    dialog.title("Select Tax System")
    dialog.geometry("350x600")
    dialog.transient(root)
    dialog.grab_set()
    
    tk.Label(dialog, text="🧾 Select Tax System", font=("Segoe UI", 14, "bold")).pack(pady=15)
    
    for key, (code, name) in system_names.items():
        tk.Radiobutton(
            dialog, 
            text=f"{key}. {name}", 
            variable=selection, 
            value=key,
            font=("Segoe UI", 12)
        ).pack(anchor="w", padx=70, pady=2)
    
    tk.Button(
        dialog, 
        text="Generate Report", 
        command=run_tax_report,
        font=("Segoe UI", 12),
        bg="#4CAF50",
        fg="white",
        width=20
    ).pack(pady=20)
    
    tk.Button(
        dialog, 
        text="Cancel", 
        command=dialog.destroy,
        font=("Segoe UI", 12),
        width=20
    ).pack(pady=5)


def run_ai_analysis():
    """Run AI analysis with symbol selection"""
    if not check_api_configured():
        show_api_missing_dialog()
        return
    
    def run_ai():
        symbol = symbol_entry.get().strip().upper()
        status_label.config(text="🤖 Running AI Analysis...")
        
        try:
            if symbol:
                subprocess.run([sys.executable, "main.py", "--ai", "--symbol", symbol], check=True)
            else:
                subprocess.run([sys.executable, "main.py", "--ai"], check=True)
            
            status_label.config(text="✅ AI Analysis completed")
            messagebox.showinfo("Success", f"AI Analysis completed!\nCheck the reports folder.")
        except subprocess.CalledProcessError as e:
            status_label.config(text="❌ Error")
            messagebox.showerror("Error", str(e))
        
        dialog.destroy()
    
    # Create dialog
    dialog = tk.Toplevel(root)
    dialog.title("AI Analysis")
    dialog.geometry("400x300")
    dialog.transient(root)
    dialog.grab_set()
    
    tk.Label(
        dialog, 
        text="🤖 AI Market Analysis", 
        font=("Segoe UI", 14, "bold")
    ).pack(pady=15)
    
    tk.Label(
        dialog, 
        text="Enter cryptocurrency symbol (e.g., BTCUSDT)", 
        font=("Segoe UI", 11)
    ).pack(pady=5)
    
    symbol_entry = tk.Entry(dialog, font=("Segoe UI", 14), width=20)
    symbol_entry.pack(pady=10)
    symbol_entry.insert(0, "BTCUSDT")  # Default
    
    tk.Label(
        dialog, 
        text="Leave empty for full portfolio analysis", 
        font=("Segoe UI", 10),
        fg="gray"
    ).pack(pady=5)
    
    tk.Button(
        dialog, 
        text="Run AI Analysis", 
        command=run_ai,
        font=("Segoe UI", 12),
        bg="#9C27B0",
        fg="white",
        width=20
    ).pack(pady=20)
    
    tk.Button(
        dialog, 
        text="Cancel", 
        command=dialog.destroy,
        font=("Segoe UI", 12),
        width=20
    ).pack(pady=5)


def launch_enhanced_dashboard():
    status_label.config(text="🚀 Launching Enhanced Dashboard...")
    try:
        subprocess.Popen(
            [
                sys.executable,
                os.path.join("dashboard", "run_enhanced.py")
            ],
            cwd=BASE_DIR
        )
    except Exception as e:
        messagebox.showerror("Enhanced Dashboard Error", str(e))


def open_reports():
    reports_path = os.path.join(BASE_DIR, "data", "reports")  # مجلد التقارير
    if not os.path.exists(reports_path):
        reports_path = os.path.join(BASE_DIR, "data")  # fallback to data folder
    os.startfile(reports_path)


def run_ledger_engine():
    """Launch Ledger Engine dialog"""
    if not check_api_configured():
        show_api_missing_dialog()
        return
    
    status_label.config(text="🚀 Launching Ledger Engine...")
    try:
        # Try to show dialog first
        from core.ledger_engine import show_ledger_dialog
        show_ledger_dialog(root)
        status_label.config(text="Ready ✅")
    except Exception as e:
        # Fallback to CLI
        try:
            subprocess.run([sys.executable, "main.py", "--ledger"], check=True)
            status_label.config(text="✅ Ledger Engine completed")
        except subprocess.CalledProcessError as e:
            status_label.config(text="❌ Error")
            messagebox.showerror("Ledger Engine Error", str(e))


def open_settings():
    """Open API settings dialog"""
    show_api_setup_dialog(root)


def exit_app():
    if messagebox.askyesno("Exit", "Do you really want to exit?"):
        root.destroy()


# ==================================================
# UI
# ==================================================
root = tk.Tk()
root.title("Crypto Investment Manager")
root.geometry("420x1250")
root.resizable(False, False)


title = tk.Label(
    root,
    text="📊 Crypto Investment Manager",
    font=("Segoe UI", 16, "bold")
)
title.pack(pady=15)

# User info display
user_info_frame = tk.Frame(root, bg="#f0f0f0", relief="sunken", bd=1)
user_info_frame.pack(fill="x", padx=10, pady=5)

user_info_label = tk.Label(
    user_info_frame,
    text="",
    font=("Segoe UI", 10),
    bg="#f0f0f0",
    fg="#333333"
)
user_info_label.pack(pady=5)

api_status_label = tk.Label(
    user_info_frame,
    text="",
    font=("Segoe UI", 10, "bold"),
    bg="#f0f0f0"
)
api_status_label.pack(pady=(0, 5))


def update_status_display():
    """Update user info and API status display"""
    if user_config.is_configured():
        user_info = user_config.get_user_info()
        user_info_label.config(text=f"👤 {user_info}")
        api_status_label.config(text="✅ API Configured", fg="green")
    else:
        user_info_label.config(text="⚠️ Not configured yet")
        api_status_label.config(text="❌ API Keys Missing", fg="red")


update_status_display()

# Note: API setup dialog will only show when user clicks the Settings button
# or when trying to run an operation that requires API keys

btn_style = {
    "width": 30,
    "height": 1,
    "font": ("Segoe UI", 14)
}

# Settings button at top
tk.Button(root, text="⚙️ API Settings", command=open_settings, width=30, height=1, font=("Segoe UI", 14, "bold"), bg="#2196F3", fg="white").pack(pady=3)

tk.Button(root, text="1 Fetch Binance Data", command=fetch_data, **btn_style).pack(pady=3)
tk.Button(root, text="2 Fetch User History (Excel)", command=fetch_user_history, **btn_style).pack(pady=3)
tk.Button(root, text="3 Calculate FIFO PnL", command=calculate_fifo, **btn_style).pack(pady=3)
tk.Button(root, text="4 Calculate Portfolio", command=calculate_portfolio, **btn_style).pack(pady=3)
tk.Button(root, text="5 Generate Excel Reports", command=generate_reports, **btn_style).pack(pady=3)
tk.Button(root, text="6 Generate Tax Reports", command=generate_tax_report, **btn_style).pack(pady=3)
tk.Button(root, text="7 Enhanced Dashboard", command=launch_enhanced_dashboard, **btn_style).pack(pady=3)
tk.Button(root, text="8 AI Analysis & Predictions", command=run_ai_analysis, **btn_style).pack(pady=3)
tk.Button(root, text="9 Ledger Engine (API)", command=run_ledger_engine, **btn_style).pack(pady=3)
tk.Button(root, text="📂 Open Reports Folder", command=open_reports, **btn_style).pack(pady=3)
tk.Button(root, text="❌ Exit", command=exit_app, **btn_style).pack(pady=10)

status_label = tk.Label(
    root,
    text="Ready ✅",
    font=("Segoe UI", 14),
    fg="green"
)
status_label.pack(pady=14)

footer = tk.Label(
    root,
    text="FIFO • Binance • Excel • AI • Tax Reports",
    font=("Segoe UI", 12),
    fg="gray"
)
footer.pack(side="bottom", pady=10)

root.mainloop()
