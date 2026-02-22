import sys
import os
from datetime import datetime
from pathlib import Path

from core.data_fetcher import DataFetcher
from core.fifo_engine import FIFOEngine
from core.report_generator import ExcelReportGenerator
from core.portfolio import Portfolio
from core.tax_report import TaxReportGenerator
from core.ai_analyzer import AIAnalyzer
from core.ledger_engine import LedgerEngine
from config.settings import DATA_DIR


# ==================================================
# Helpers
# ==================================================
def ensure_dirs():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


# ==================================================
# Core Steps
# ==================================================
def fetch_binance_data():
    print("📡 Fetching Binance historical data...")
    fetcher = DataFetcher()
    fetcher.fetch_all()
    print("✅ Binance data fetched successfully")


def calculate_fifo_pnl():
    print("🧮 Calculating FIFO PnL...")
    fifo = FIFOEngine()
    fifo.run()
    print("✅ FIFO PnL calculation completed")


def calculate_portfolio():
    print("📊 Calculating Portfolio...")
    portfolio = Portfolio()
    portfolio.calculate()
    print("✅ Portfolio calculation completed")


def generate_excel_report():
    print("📊 Generating Excel report...")
    generator = ExcelReportGenerator(Path(__file__).resolve().parent)
    generator.generate()
    print("✅ Excel report generated successfully")


def generate_tax_report(tax_system: str = "US", year: int = None):
    print("📊 Generating Tax Report...")
    generator = TaxReportGenerator(Path(__file__).resolve().parent)
    output_path = generator.generate_tax_report(tax_system, year)
    print(f"✅ Tax report generated: {output_path}")


def run_ai_analysis(symbol: str = None):
    print("🤖 Running AI Analysis...")
    analyzer = AIAnalyzer(Path(__file__).resolve().parent)
    output_path = analyzer.generate_ai_report(symbol)
    print(f"✅ AI Analysis report generated: {output_path}")


def run_ledger():
    """Run Ledger Engine from CLI"""
    print("📒 Running Ledger Engine...")
    engine = LedgerEngine()
    
    # Connect
    success, msg = engine.connect()
    if not success:
        print(f"❌ {msg}")
        return
    print("✅ Connected to Binance API")
    
    # Fetch data
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


# ==================================================
# Main Runner
# ==================================================
def main():
    ensure_dirs()
    args = sys.argv

    # تشغيل انتقائي من Desktop App
    if "--fetch" in args:
        fetch_binance_data()
        return

    if "--fifo" in args:
        calculate_fifo_pnl()
        return

    if "--portfolio" in args:
        calculate_portfolio()
        return

    if "--report" in args:
        generate_excel_report()
        return

    if "--tax" in args:
        # Get tax system from args (default: US)
        tax_system = "US"
        year = None
        generate_all = False
        
        for i, arg in enumerate(args):
            if arg == "--tax-system" and i + 1 < len(args):
                tax_system = args[i + 1]
            if arg == "--tax-year" and i + 1 < len(args):
                year = int(args[i + 1])
            if arg == "--all":
                generate_all = True
        
        if generate_all:
            print("📊 Generating Tax Reports for ALL Systems...")
            generator = TaxReportGenerator(Path(__file__).resolve().parent)
            reports = generator.generate_all_systems_report(year)
            print("Generated reports:")
            for system, path in reports.items():
                print(f"  {system}: {path}")
        else:
            generate_tax_report(tax_system, year)
        return

    if "--ai" in args:
        # Get symbol from args
        symbol = None
        for i, arg in enumerate(args):
            if arg == "--symbol" and i + 1 < len(args):
                symbol = args[i + 1]
        run_ai_analysis(symbol)
        return
    
    if "--ledger" in args:
        run_ledger()
        return

    # تشغيل كامل افتراضي
    fetch_binance_data()
    calculate_fifo_pnl()
    calculate_portfolio()
    generate_excel_report()
    print("\nAll operations completed!")


# ==================================================
# Entry Point
# ==================================================
if __name__ == "__main__":
    # Set UTF-8 encoding for Windows console
    import io
    import sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    start = datetime.now()
    print(f"🚀 Crypto Fund Manager Started @ {start.strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        main()
    except Exception as e:
        print("❌ Fatal Error:", str(e))
        raise

    end = datetime.now()
    duration = end - start
    print(f"🏁 Finished in {duration}")
