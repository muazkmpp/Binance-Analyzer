"""
AI Analysis Module
==================
Provides AI-powered analysis for cryptocurrency investments.
Includes market trend analysis, price predictions, and portfolio recommendations.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from config.settings import DATA_DIR


class AIAnalyzer:
    """AI-powered cryptocurrency analysis engine"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).resolve().parent
        self.data_dir = self.base_dir / "data"
        self.reports_dir = self.base_dir / "reports"
        
        if not self.reports_dir.exists():
            self.reports_dir.mkdir(parents=True)
    
    # ================================================
    # Data Loading
    # ================================================
    def load_trade_data(self) -> pd.DataFrame:
        """Load trade history"""
        trades_file = self.data_dir / "spot_trades.csv"
        if trades_file.exists():
            df = pd.read_csv(trades_file)
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
            return df
        return pd.DataFrame()
    
    def load_portfolio(self) -> pd.DataFrame:
        """Load current portfolio"""
        portfolio_file = self.data_dir / "portfolio.csv"
        if portfolio_file.exists():
            return pd.read_csv(portfolio_file)
        return pd.DataFrame()
    
    def load_fifo_results(self) -> pd.DataFrame:
        """Load FIFO results"""
        fifo_file = self.data_dir / "fifo_results.csv"
        if fifo_file.exists():
            df = pd.read_csv(fifo_file)
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
            return df
        return pd.DataFrame()
    
    # ================================================
    # Market Trend Analysis
    # ================================================
    def analyze_market_trends(self, symbol: str = None) -> Dict:
        """Analyze market trends using technical indicators"""
        trades_df = self.load_trade_data()
        
        if trades_df.empty:
            return {"error": "No trading data available"}
        
        if symbol:
            trades_df = trades_df[trades_df['symbol'] == symbol]
        
        results = {
            "total_trades": len(trades_df),
            "symbols_analyzed": trades_df['symbol'].unique().tolist() if 'symbol' in trades_df.columns else [],
            "trends": {}
        }
        
        # Calculate simple moving averages (if we have price data)
        if 'price' in trades_df.columns or 'quoteQty' in trades_df.columns:
            prices = trades_df.get('price', trades_df.get('quoteQty', pd.Series([1])))
            
            # Simple Moving Averages
            for window in [7, 14, 30]:
                if len(prices) >= window:
                    sma = prices.rolling(window=window).mean()
                    results["trends"][f"sma_{window}"] = float(sma.iloc[-1]) if not pd.isna(sma.iloc[-1]) else 0
            
            # Volatility (Standard Deviation)
            results["trends"]["volatility"] = float(prices.std())
            
            # Price change percentage
            if len(prices) > 1:
                results["trends"]["price_change_percent"] = float(
                    ((prices.iloc[-1] - prices.iloc[0]) / prices.iloc[0]) * 100
                )
        
        # Analyze by symbol
        if 'symbol' in trades_df.columns:
            for sym in trades_df['symbol'].unique():
                sym_df = trades_df[trades_df['symbol'] == sym]
                results["trends"][sym] = {
                    "trade_count": len(sym_df),
                    "volume": float(sym_df.get('quoteQty', sym_df.get('total', pd.Series([0]))).sum())
                }
        
        return results
    
    # ================================================
    # Price Prediction (Simplified Model)
    # ================================================
    def predict_price(self, symbol: str, days_ahead: int = 7) -> Dict:
        """
        Simple price prediction using linear regression
        Note: This is a simplified model for demonstration
        Real trading decisions should not rely solely on this
        """
        trades_df = self.load_trade_data()
        
        if trades_df.empty:
            return {"error": "No data available for prediction"}
        
        # Filter by symbol
        if symbol:
            symbol_df = trades_df[trades_df['symbol'] == symbol].copy()
        else:
            # Use all data
            symbol_df = trades_df.copy()
        
        if symbol_df.empty:
            return {"error": f"No data for symbol {symbol}"}
        
        # Get price data
        if 'price' not in symbol_df.columns:
            # Try to calculate price from other columns
            if 'quoteQty' in symbol_df.columns and 'qty' in symbol_df.columns:
                symbol_df['price'] = symbol_df['quoteQty'] / symbol_df['qty']
            else:
                return {"error": "Price data not available"}
        
        prices = symbol_df['price'].dropna().values
        
        if len(prices) < 5:
            return {"error": "Insufficient data for prediction"}
        
        # Simple linear regression for trend
        x = np.arange(len(prices))
        coeffs = np.polyfit(x, prices, 1)
        slope = coeffs[0]
        
        # Predict future prices
        future_x = np.arange(len(prices), len(prices) + days_ahead)
        predicted_prices = np.polyval(coeffs, future_x)
        
        # Calculate confidence (simplified)
        # In real ML, we'd use cross-validation and more sophisticated metrics
        residuals = prices - np.polyval(coeffs, x)
        mse = np.mean(residuals ** 2)
        rmse = np.sqrt(mse)
        
        return {
            "symbol": symbol,
            "current_price": float(prices[-1]),
            "predicted_prices": [float(p) for p in predicted_prices],
            "trend": "BULLISH" if slope > 0 else "BEARISH",
            "trend_strength": abs(slope) / np.mean(prices) * 100,  # percentage
            "predicted_change_percent": float(
                ((predicted_prices[-1] - prices[-1]) / prices[-1]) * 100
            ),
            "confidence_rmse": float(rmse),
            "days_ahead": days_ahead
        }
    
    # ================================================
    # Portfolio Recommendations
    # ================================================
    def get_portfolio_recommendations(self) -> Dict:
        """Generate AI-powered portfolio recommendations"""
        trades_df = self.load_trade_data()
        portfolio_df = self.load_portfolio()
        
        if trades_df.empty:
            return {"error": "No trading data available"}
        
        recommendations = {
            "timestamp": datetime.now().isoformat(),
            "risk_assessment": {},
            "allocation_recommendations": [],
            "trading_signals": []
        }
        
        # Analyze performance by symbol
        if 'symbol' in trades_df.columns:
            symbol_stats = {}
            
            for sym in trades_df['symbol'].unique():
                sym_df = trades_df[trades_df['symbol'] == sym]
                
                # Calculate win rate
                if 'profit' in sym_df.columns or 'pnl' in sym_df.columns:
                    profit_col = 'profit' if 'profit' in sym_df.columns else 'pnl'
                    wins = len(sym_df[sym_df[profit_col] > 0])
                    total = len(sym_df)
                    win_rate = wins / total if total > 0 else 0
                    
                    symbol_stats[sym] = {
                        "trade_count": total,
                        "win_rate": win_rate,
                        "avg_profit": float(sym_df[profit_col].mean()),
                        "total_volume": float(sym_df.get('quoteQty', sym_df.get('total', pd.Series([0]))).sum())
                    }
            
            # Generate recommendations based on performance
            for sym, stats in symbol_stats.items():
                rec = {
                    "symbol": sym,
                    "action": "HOLD",
                    "reason": "",
                    "confidence": 0
                }
                
                if stats["win_rate"] >= 0.6 and stats["avg_profit"] > 0:
                    rec["action"] = "CONSIDER_BUY"
                    rec["reason"] = f"High win rate ({stats['win_rate']*100:.1f}%) with positive average profit"
                    rec["confidence"] = stats["win_rate"]
                elif stats["win_rate"] < 0.4 or stats["avg_profit"] < 0:
                    rec["action"] = "CONSIDER_SELL"
                    rec["reason"] = f"Low win rate ({stats['win_rate']*100:.1f}%) or negative average profit"
                    rec["confidence"] = 1 - stats["win_rate"]
                
                recommendations["trading_signals"].append(rec)
            
            # Risk assessment
            total_trades = sum(s["trade_count"] for s in symbol_stats.values())
            if total_trades > 0:
                # Calculate portfolio diversification
                recommendations["risk_assessment"]["diversification_score"] = len(symbol_stats) / 10  # 10 = max diversification
                recommendations["risk_assessment"]["total_symbols"] = len(symbol_stats)
                recommendations["risk_assessment"]["total_trades"] = total_trades
        
        # Allocation recommendations (simplified)
        if not portfolio_df.empty:
            if 'asset' in portfolio_df.columns and 'quantity' in portfolio_df.columns:
                total_value = portfolio_df['quantity'].sum()
                if total_value > 0:
                    for _, row in portfolio_df.iterrows():
                        allocation = (row['quantity'] / total_value) * 100
                        recommendations["allocation_recommendations"].append({
                            "asset": row['asset'],
                            "current_allocation": float(allocation),
                            "recommendation": "INCREASE" if allocation < 20 else "HOLD"
                        })
        
        return recommendations
    
    # ================================================
    # Comprehensive AI Report
    # ================================================
    def generate_ai_report(self, symbol: str = None) -> str:
        """Generate comprehensive AI analysis report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Get all analyses
        trends = self.analyze_market_trends(symbol)
        recommendations = self.get_portfolio_recommendations()
        
        # Get predictions if symbol specified
        predictions = None
        if symbol:
            predictions = self.predict_price(symbol)
        
        # Create Excel report
        filename = f"ai_analysis_{timestamp}.xlsx"
        output_path = self.reports_dir / filename
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Summary sheet
            summary_data = {
                'Metric': ['Report Date', 'Symbols Analyzed', 'Total Trades'],
                'Value': [
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    len(trends.get('symbols_analyzed', [])),
                    trends.get('total_trades', 0)
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
            
            # Market Trends
            if trends.get('trends'):
                trends_df = pd.DataFrame([trends['trends']])
                trends_df.to_excel(writer, sheet_name='Market Trends', index=False)
            
            # Trading Signals
            if recommendations.get('trading_signals'):
                signals_df = pd.DataFrame(recommendations['trading_signals'])
                signals_df.to_excel(writer, sheet_name='Trading Signals', index=False)
            
            # Predictions
            if predictions and 'error' not in predictions:
                pred_df = pd.DataFrame({
                    'Day': range(1, predictions['days_ahead'] + 1),
                    'Predicted Price': predictions['predicted_prices']
                })
                pred_df.to_excel(writer, sheet_name='Price Predictions', index=False)
                
                # Add prediction summary
                pred_summary = pd.DataFrame({
                    'Metric': ['Current Price', 'Trend', 'Predicted Change %', 'Confidence (RMSE)'],
                    'Value': [
                        predictions['current_price'],
                        predictions['trend'],
                        predictions['predicted_change_percent'],
                        predictions['confidence_rmse']
                    ]
                })
                pred_summary.to_excel(writer, sheet_name='Prediction Summary', index=False)
        
        # Also generate JSON
        json_filename = f"ai_analysis_{timestamp}.json"
        json_path = self.reports_dir / json_filename
        
        import json
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                "trends": trends,
                "predictions": predictions,
                "recommendations": recommendations
            }, f, indent=2, default=str)
        
        return str(output_path)


def run_ai_analysis(symbol: str = None):
    """CLI entry point for AI analysis"""
    analyzer = AIAnalyzer()
    output_path = analyzer.generate_ai_report(symbol)
    print(f"✅ AI Analysis report generated: {output_path}")
    return output_path


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Crypto Analysis")
    parser.add_argument("--symbol", "-s", default=None, help="Symbol to analyze (e.g., BTCUSDT)")
    
    args = parser.parse_args()
    run_ai_analysis(args.symbol)
