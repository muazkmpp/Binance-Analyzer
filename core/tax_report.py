"""
Tax Report Generator Module
===========================
Generates tax reports for cryptocurrency transactions in multiple formats.
Supports various tax systems and calculates capital gains/losses.
"""

import os
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from config.settings import DATA_DIR


class TaxReportGenerator:
    """Generates tax reports for cryptocurrency transactions"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).resolve().parent
        self.data_dir = self.base_dir / "data"
        self.reports_dir = self.base_dir / "data"  # Save tax reports to data folder
        
        # Create data directory if not exists
        if not self.reports_dir.exists():
            self.reports_dir.mkdir(parents=True)
        
        # Tax system configurations
        self.tax_systems = {
            "US": {
                "name": "United States (IRS)",
                "short_term_days": 365,
                "short_term_rates": {
                    "ordinary": 0.37,  # Highest bracket
                    "capital_gains": 0.20
                },
                "currency": "USD"
            },
            "UK": {
                "name": "United Kingdom (HMRC)",
                "short_term_days": 0,
                "allowance": 12300,  # Annual CGT allowance 2024
                "rates": {
                    "basic": 0.10,
                    "higher": 0.20
                },
                "currency": "GBP"
            },
            "DE": {
                "name": "Germany",
                "short_term_days": 365,
                "capital_gains_rate": 0.25,
                "solidarity_surcharge": 0.055,
                "church_tax": 0.08,  # Optional
                "currency": "EUR"
            },
            "EG": {
                "name": "Egypt (Tax Authority)",
                "short_term_days": 0,
                "capital_gains_rate": 0.10,
                "currency": "EGP"
            },
            "SA": {
                "name": "Saudi Arabia (ZATCA)",
                "short_term_days": 0,
                "capital_gains_rate": 0.0,  # No capital gains tax
                "currency": "SAR"
            },
            "AE": {
                "name": "UAE (FTA)",
                "short_term_days": 0,
                "capital_gains_rate": 0.0,  # No capital gains tax
                "currency": "AED"
            },
            "GENERIC": {
                "name": "Generic / Custom",
                "short_term_days": 365,
                "capital_gains_rate": 0.15,
                "currency": "USD"
            }
        }
    
    def load_trade_data(self) -> pd.DataFrame:
        """Load trade data from CSV files"""
        trades_file = self.data_dir / "spot_trades.csv"
        
        if not trades_file.exists():
            # Try fifo_results as fallback
            fifo_file = self.data_dir / "fifo_results.csv"
            if fifo_file.exists():
                df = pd.read_csv(fifo_file)
                return df
            return pd.DataFrame()
        
        df = pd.read_csv(trades_file)
        
        # Convert date columns
        date_columns = ['date', 'time', 'datetime', 'trade_date']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        return df
    
    def calculate_gains_losses(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate capital gains and losses from trades"""
        if df.empty:
            return pd.DataFrame()
        
        # Identify sell transactions and calculate gains/losses
        results = []
        
        # Group by symbol
        for symbol in df['symbol'].unique() if 'symbol' in df.columns else []:
            symbol_df = df[df['symbol'] == symbol].copy()
            
            # Sort by date
            if 'date' in symbol_df.columns:
                symbol_df = symbol_df.sort_values('date')
            
            # Calculate gains for each sell
            for _, row in symbol_df.iterrows():
                if 'side' in row and row['side'] == 'SELL':
                    gain = row.get('profit_loss', row.get('pnl', row.get('gain', 0)))
                    cost = row.get('cost', row.get('cost_basis', 0))
                    proceeds = row.get('proceeds', row.get('quoteQty', row.get('total', 0)))
                    
                    results.append({
                        'symbol': symbol,
                        'date': row.get('date'),
                        'type': 'SELL',
                        'proceeds': float(proceeds) if proceeds else 0,
                        'cost_basis': float(cost) if cost else 0,
                        'gain_loss': float(gain) if gain else 0,
                        'holding_period': row.get('holding_days', row.get('holding_period', 0))
                    })
        
        return pd.DataFrame(results)
    
    def classify_holding_period(self, days: int, tax_system: str = "US") -> str:
        """Classify as short-term or long-term based on tax system"""
        threshold = self.tax_systems.get(tax_system, {}).get("short_term_days", 365)
        
        if days > threshold:
            return "LONG_TERM"
        return "SHORT_TERM"
    
    def calculate_tax_liability(self, gains_df: pd.DataFrame, tax_system: str = "US") -> Dict:
        """Calculate tax liability based on the selected tax system"""
        if gains_df is None or gains_df.empty:
            tax_config = self.tax_systems.get(tax_system, self.tax_systems["GENERIC"])
            return {
                "tax_system": tax_system,
                "system_name": tax_config["name"],
                "currency": tax_config["currency"],
                "total_proceeds": 0,
                "total_cost_basis": 0,
                "total_gain_loss": 0,
                "short_term_gain": 0,
                "long_term_gain": 0,
                "short_term_count": 0,
                "long_term_count": 0,
                "estimated_tax": 0,
                "transactions": []
            }
        
        tax_config = self.tax_systems.get(tax_system, self.tax_systems["GENERIC"])
        
        # Classify each transaction
        gains_df['holding_type'] = gains_df['holding_period'].apply(
            lambda x: self.classify_holding_period(int(x) if pd.notna(x) else 0, tax_system)
        )
        
        # Calculate totals
        short_term = gains_df[gains_df['holding_type'] == 'SHORT_TERM']
        long_term = gains_df[gains_df['holding_type'] == 'LONG_TERM']
        
        total_proceeds = gains_df['proceeds'].sum()
        total_cost_basis = gains_df['cost_basis'].sum()
        total_gain_loss = gains_df['gain_loss'].sum()
        
        short_term_gain = short_term['gain_loss'].sum() if not short_term.empty else 0
        long_term_gain = long_term['gain_loss'].sum() if not long_term.empty else 0
        
        # Calculate estimated tax
        if tax_system == "US":
            # US: Short-term at ordinary income rate, Long-term at capital gains rate
            short_term_tax = max(0, short_term_gain * tax_config["short_term_rates"]["ordinary"])
            long_term_tax = max(0, long_term_gain * tax_config["short_term_rates"]["capital_gains"])
            estimated_tax = short_term_tax + long_term_tax
            
        elif tax_system == "UK":
            # UK: Use CGT allowance
            allowance = tax_config.get("allowance", 12300)
            taxable_gain = max(0, total_gain_loss - allowance)
            # Assuming higher rate for simplicity
            estimated_tax = taxable_gain * tax_config["rates"]["higher"]
            
        elif tax_system == "DE":
            # Germany: 25% + solidarity surcharge + optional church tax
            rate = tax_config["capital_gains_rate"] + tax_config["solidarity_surcharge"]
            estimated_tax = max(0, total_gain_loss * rate)
            
        elif tax_system in ["EG", "SA", "AE"]:
            # No or low capital gains tax
            estimated_tax = max(0, total_gain_loss * tax_config["capital_gains_rate"])
            
        else:
            # Generic calculation
            estimated_tax = max(0, total_gain_loss * tax_config["capital_gains_rate"])
        
        return {
            "tax_system": tax_system,
            "system_name": tax_config["name"],
            "currency": tax_config["currency"],
            "total_proceeds": total_proceeds,
            "total_cost_basis": total_cost_basis,
            "total_gain_loss": total_gain_loss,
            "short_term_gain": short_term_gain,
            "long_term_gain": long_term_gain,
            "short_term_count": len(short_term),
            "long_term_count": len(long_term),
            "estimated_tax": estimated_tax,
            "transactions": gains_df.to_dict('records')
        }
    
    def generate_tax_report(self, tax_system: str = "US", year: int = None) -> str:
        """Generate comprehensive tax report"""
        if year is None:
            year = datetime.now().year
        
        # Load and process data
        trades_df = self.load_trade_data()
        
        # Filter by year if possible
        if 'date' in trades_df.columns and year:
            trades_df = trades_df[trades_df['date'].dt.year == year]
        
        # Calculate gains/losses
        gains_df = self.calculate_gains_losses(trades_df)
        
        # Calculate tax liability
        tax_summary = self.calculate_tax_liability(gains_df, tax_system)
        
        # Generate report filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tax_report_{tax_system}_{year}_{timestamp}.xlsx"
        output_path = self.reports_dir / filename
        
        # Create Excel report with multiple sheets
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Summary sheet - always create this first
            summary_data = {
                'Description': [
                    'Tax System',
                    'Tax Year',
                    'Total Proceeds',
                    'Total Cost Basis',
                    'Total Gain/Loss',
                    'Short-Term Gain',
                    'Long-Term Gain',
                    'Number of Short-Term Transactions',
                    'Number of Long-Term Transactions',
                    'Estimated Tax Liability',
                    'Report Date'
                ],
                'Value': [
                    tax_summary['system_name'],
                    str(year),
                    f"{tax_summary['total_proceeds']:.2f}",
                    f"{tax_summary['total_cost_basis']:.2f}",
                    f"{tax_summary['total_gain_loss']:.2f}",
                    f"{tax_summary['short_term_gain']:.2f}",
                    f"{tax_summary['long_term_gain']:.2f}",
                    str(tax_summary['short_term_count']),
                    str(tax_summary['long_term_count']),
                    f"{tax_summary['estimated_tax']:.2f} {tax_summary['currency']}",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Transactions sheet - only if we have data
            if gains_df is not None and not gains_df.empty:
                # Add a visible sheet first before empty ones
                gains_df.to_excel(writer, sheet_name='Transactions', index=False)
            else:
                # Create a placeholder sheet with message
                placeholder_data = {
                    'Message': ['No transaction data available for this period'],
                    'Note': ['Please run FIFO calculation first to generate transaction data']
                }
                pd.DataFrame(placeholder_data).to_excel(writer, sheet_name='Transactions', index=False)
            
            # Tax System Info sheet - always create
            tax_info = []
            for code, config in self.tax_systems.items():
                tax_info.append({
                    'Code': code,
                    'Name': config['name'],
                    'Currency': config['currency'],
                    'Short Term Days': config.get('short_term_days', 'N/A')
                })
            pd.DataFrame(tax_info).to_excel(writer, sheet_name='Tax Systems', index=False)
        
        # Also generate CSV for each format
        csv_filename = f"tax_report_{tax_system}_{year}_{timestamp}.csv"
        csv_path = self.reports_dir / csv_filename
        
        if gains_df is not None and not gains_df.empty:
            gains_df.to_csv(csv_path, index=False)
        else:
            # Create empty CSV with headers
            pd.DataFrame(columns=['symbol', 'date', 'type', 'proceeds', 'cost_basis', 'gain_loss', 'holding_period']).to_csv(csv_path, index=False)
        
        return str(output_path)
    
    def get_available_systems(self) -> List[Dict]:
        """Get list of available tax systems"""
        return [
            {"code": code, "name": config["name"], "currency": config["currency"]}
            for code, config in self.tax_systems.items()
        ]
    
    def generate_all_systems_report(self, year: int = None) -> Dict[str, str]:
        """Generate tax reports for all supported systems"""
        reports = {}
        
        for system_code in self.tax_systems.keys():
            try:
                report_path = self.generate_tax_report(system_code, year)
                reports[system_code] = report_path
            except Exception as e:
                print(f"Error generating report for {system_code}: {e}")
        
        return reports


def generate_tax_report_cli(tax_system: str = "US", year: int = None):
    """CLI entry point for tax report generation"""
    generator = TaxReportGenerator()
    output_path = generator.generate_tax_report(tax_system, year)
    print(f"✅ Tax report generated: {output_path}")
    return output_path


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate Crypto Tax Reports")
    parser.add_argument("--system", "-s", default="US", 
                        help="Tax system code (US, UK, DE, EG, SA, AE, GENERIC)")
    parser.add_argument("--year", "-y", type=int, default=None,
                        help="Tax year")
    parser.add_argument("--all", "-a", action="store_true",
                        help="Generate reports for all tax systems")
    
    args = parser.parse_args()
    
    generator = TaxReportGenerator()
    
    if args.all:
        reports = generator.generate_all_systems_report(args.year)
        print("Generated reports:")
        for system, path in reports.items():
            print(f"  {system}: {path}")
    else:
        output = generator.generate_tax_report(args.system, args.year)
        print(f"✅ Tax report saved to: {output}")
