"""
Dashboard Utilities Module
Helper functions for data processing and analysis
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class DataProcessor:
    """Advanced data processing utilities"""
    
    @staticmethod
    def clean_price_data(df: pd.DataFrame, price_col: str = 'price') -> pd.DataFrame:
        """Clean and validate price data"""
        df_clean = df.copy()
        
        # Remove invalid prices
        df_clean = df_clean[df_clean[price_col] > 0]
        
        # Remove outliers using IQR method
        Q1 = df_clean[price_col].quantile(0.25)
        Q3 = df_clean[price_col].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        df_clean = df_clean[
            (df_clean[price_col] >= lower_bound) & 
            (df_clean[price_col] <= upper_bound)
        ]
        
        return df_clean
    
    @staticmethod
    def resample_time_series(df: pd.DataFrame, time_col: str, freq: str = '1D') -> pd.DataFrame:
        """Resample time series data"""
        if time_col not in df.columns:
            return df
        
        df_resampled = df.copy()
        df_resampled[time_col] = pd.to_datetime(df_resampled[time_col])
        df_resampled = df_resampled.set_index(time_col)
        
        # Resample based on frequency
        if freq == '1D':
            df_resampled = df_resampled.resample('D').sum()
        elif freq == '1W':
            df_resampled = df_resampled.resample('W').sum()
        elif freq == '1M':
            df_resampled = df_resampled.resample('M').sum()
        
        return df_resampled.reset_index()
    
    @staticmethod
    def detect_anomalies(df: pd.DataFrame, column: str, method: str = 'zscore') -> pd.DataFrame:
        """Detect anomalies in data"""
        if column not in df.columns:
            return df
        
        df_anomaly = df.copy()
        
        if method == 'zscore':
            z_scores = np.abs((df_anomaly[column] - df_anomaly[column].mean()) / df_anomaly[column].std())
            df_anomaly['is_anomaly'] = z_scores > 3
        elif method == 'iqr':
            Q1 = df_anomaly[column].quantile(0.25)
            Q3 = df_anomaly[column].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            df_anomaly['is_anomaly'] = (df_anomaly[column] < lower_bound) | (df_anomaly[column] > upper_bound)
        
        return df_anomaly

class PerformanceAnalyzer:
    """Advanced performance analysis utilities"""
    
    @staticmethod
    def calculate_returns(prices: pd.Series) -> pd.Series:
        """Calculate returns from price series"""
        return prices.pct_change().dropna()
    
    @staticmethod
    def calculate_volatility(returns: pd.Series, window: int = 30) -> pd.Series:
        """Calculate rolling volatility"""
        return returns.rolling(window=window).std() * np.sqrt(252)  # Annualized
    
    @staticmethod
    def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio"""
        excess_returns = returns - risk_free_rate / 252
        if len(excess_returns) == 0 or excess_returns.std() == 0:
            return 0
        return excess_returns.mean() / excess_returns.std() * np.sqrt(252)
    
    @staticmethod
    def calculate_max_drawdown(equity_curve: pd.Series) -> Tuple[float, pd.Timestamp, pd.Timestamp]:
        """Calculate maximum drawdown and its dates"""
        peak = equity_curve.expanding().max()
        drawdown = (equity_curve - peak) / peak
        
        max_dd = drawdown.min()
        max_dd_date = drawdown.idxmin()
        
        # Find the peak date before max drawdown
        peak_date = peak.loc[:max_dd_date].idxmax()
        
        return max_dd, peak_date, max_dd_date
    
    @staticmethod
    def calculate_calmar_ratio(equity_curve: pd.Series) -> float:
        """Calculate Calmar ratio (annual return / max drawdown)"""
        total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1
        years = len(equity_curve) / 252  # Assuming daily data
        
        annual_return = (1 + total_return) ** (1/years) - 1
        max_dd, _, _ = PerformanceAnalyzer.calculate_max_drawdown(equity_curve)
        
        if max_dd == 0:
            return float('inf')
        
        return annual_return / abs(max_dd)
    
    @staticmethod
    def calculate_sortino_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate Sortino ratio (downside risk only)"""
        excess_returns = returns - risk_free_rate / 252
        downside_returns = excess_returns[excess_returns < 0]
        
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0
        
        return excess_returns.mean() / downside_returns.std() * np.sqrt(252)
    
    @staticmethod
    def calculate_var(returns: pd.Series, confidence_level: float = 0.05) -> float:
        """Calculate Value at Risk (VaR)"""
        return returns.quantile(confidence_level)
    
    @staticmethod
    def calculate_cvar(returns: pd.Series, confidence_level: float = 0.05) -> float:
        """Calculate Conditional Value at Risk (CVaR)"""
        var = PerformanceAnalyzer.calculate_var(returns, confidence_level)
        return returns[returns <= var].mean()

class RiskMetrics:
    """Risk calculation utilities"""
    
    @staticmethod
    def calculate_beta(returns: pd.Series, market_returns: pd.Series) -> float:
        """Calculate beta coefficient"""
        if len(returns) != len(market_returns):
            return 0
        
        covariance = np.cov(returns, market_returns)[0][1]
        market_variance = np.var(market_returns)
        
        if market_variance == 0:
            return 0
        
        return covariance / market_variance
    
    @staticmethod
    def calculate_alpha(returns: pd.Series, market_returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate alpha"""
        beta = RiskMetrics.calculate_beta(returns, market_returns)
        
        returns_mean = returns.mean() * 252  # Annualized
        market_mean = market_returns.mean() * 252  # Annualized
        
        alpha = returns_mean - (risk_free_rate + beta * (market_mean - risk_free_rate))
        return alpha
    
    @staticmethod
    def calculate_information_ratio(returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """Calculate Information Ratio"""
        excess_returns = returns - benchmark_returns
        
        if len(excess_returns) == 0 or excess_returns.std() == 0:
            return 0
        
        return excess_returns.mean() / excess_returns.std() * np.sqrt(252)
    
    @staticmethod
    def calculate_tracking_error(returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """Calculate tracking error"""
        excess_returns = returns - benchmark_returns
        return excess_returns.std() * np.sqrt(252)

class TechnicalIndicators:
    """Technical analysis indicators"""
    
    @staticmethod
    def sma(data: pd.Series, window: int) -> pd.Series:
        """Simple Moving Average"""
        return data.rolling(window=window).mean()
    
    @staticmethod
    def ema(data: pd.Series, window: int) -> pd.Series:
        """Exponential Moving Average"""
        return data.ewm(span=window).mean()
    
    @staticmethod
    def rsi(data: pd.Series, window: int = 14) -> pd.Series:
        """Relative Strength Index"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """MACD indicator"""
        ema_fast = TechnicalIndicators.ema(data, fast)
        ema_slow = TechnicalIndicators.ema(data, slow)
        
        macd_line = ema_fast - ema_slow
        signal_line = TechnicalIndicators.ema(macd_line, signal)
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    @staticmethod
    def bollinger_bands(data: pd.Series, window: int = 20, num_std: int = 2) -> Dict[str, pd.Series]:
        """Bollinger Bands"""
        sma = TechnicalIndicators.sma(data, window)
        std = data.rolling(window=window).std()
        
        upper_band = sma + (std * num_std)
        lower_band = sma - (std * num_std)
        
        return {
            'upper': upper_band,
            'middle': sma,
            'lower': lower_band
        }
    
    @staticmethod
    def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_window: int = 14, d_window: int = 3) -> Dict[str, pd.Series]:
        """Stochastic Oscillator"""
        lowest_low = low.rolling(window=k_window).min()
        highest_high = high.rolling(window=k_window).max()
        
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_window).mean()
        
        return {
            'k': k_percent,
            'd': d_percent
        }

class PortfolioAnalyzer:
    """Portfolio analysis utilities"""
    
    @staticmethod
    def calculate_portfolio_returns(weights: np.ndarray, returns: pd.DataFrame) -> pd.Series:
        """Calculate portfolio returns from weights and individual returns"""
        return (returns * weights).sum(axis=1)
    
    @staticmethod
    def calculate_portfolio_volatility(weights: np.ndarray, cov_matrix: pd.DataFrame) -> float:
        """Calculate portfolio volatility"""
        return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    
    @staticmethod
    def efficient_frontier(returns: pd.DataFrame, num_portfolios: int = 100) -> pd.DataFrame:
        """Generate efficient frontier points"""
        mean_returns = returns.mean()
        cov_matrix = returns.cov()
        
        results = []
        
        for _ in range(num_portfolios):
            weights = np.random.random(len(mean_returns))
            weights /= np.sum(weights)
            
            portfolio_return = np.sum(mean_returns * weights) * 252
            portfolio_volatility = PortfolioAnalyzer.calculate_portfolio_volatility(weights, cov_matrix) * np.sqrt(252)
            
            results.append({
                'return': portfolio_return,
                'volatility': portfolio_volatility,
                'sharpe': portfolio_return / portfolio_volatility
            })
        
        return pd.DataFrame(results)
    
    @staticmethod
    def calculate_correlation_matrix(returns: pd.DataFrame) -> pd.DataFrame:
        """Calculate correlation matrix"""
        return returns.corr()
    
    @staticmethod
    def diversification_ratio(weights: np.ndarray, volatilities: pd.Series, corr_matrix: pd.DataFrame) -> float:
        """Calculate diversification ratio"""
        weighted_vol = np.sum(weights * volatilities)
        portfolio_vol = PortfolioAnalyzer.calculate_portfolio_volatility(weights, corr_matrix)
        
        return weighted_vol / portfolio_vol

class DataValidator:
    """Data validation utilities"""
    
    @staticmethod
    def validate_price_data(df: pd.DataFrame, price_col: str = 'price') -> Dict[str, any]:
        """Validate price data"""
        issues = []
        
        # Check for missing values
        missing_count = df[price_col].isnull().sum()
        if missing_count > 0:
            issues.append(f"Missing values: {missing_count}")
        
        # Check for negative prices
        negative_count = (df[price_col] < 0).sum()
        if negative_count > 0:
            issues.append(f"Negative prices: {negative_count}")
        
        # Check for zero prices
        zero_count = (df[price_col] == 0).sum()
        if zero_count > 0:
            issues.append(f"Zero prices: {zero_count}")
        
        # Check for outliers
        Q1 = df[price_col].quantile(0.25)
        Q3 = df[price_col].quantile(0.75)
        IQR = Q3 - Q1
        outliers = ((df[price_col] < (Q1 - 1.5 * IQR)) | (df[price_col] > (Q3 + 1.5 * IQR))).sum()
        
        if outliers > 0:
            issues.append(f"Outliers: {outliers}")
        
        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'total_records': len(df),
            'valid_records': len(df) - sum([int(issue.split(': ')[1]) for issue in issues if 'Missing' not in issue])
        }
    
    @staticmethod
    def validate_trade_data(df: pd.DataFrame) -> Dict[str, any]:
        """Validate trade data"""
        issues = []
        required_columns = ['time', 'symbol', 'quantity', 'price']
        
        # Check required columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            issues.append(f"Missing columns: {missing_columns}")
        
        # Check for empty trades
        if 'quantity' in df.columns:
            empty_trades = (df['quantity'] <= 0).sum()
            if empty_trades > 0:
                issues.append(f"Empty trades: {empty_trades}")
        
        # Check for invalid timestamps
        if 'time' in df.columns:
            invalid_dates = pd.to_datetime(df['time'], errors='coerce').isnull().sum()
            if invalid_dates > 0:
                issues.append(f"Invalid dates: {invalid_dates}")
        
        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'total_records': len(df)
        }

class ReportGenerator:
    """Advanced report generation utilities"""
    
    @staticmethod
    def generate_performance_report(returns: pd.Series, benchmark_returns: Optional[pd.Series] = None) -> Dict[str, float]:
        """Generate comprehensive performance report"""
        report = {}
        
        # Basic metrics
        report['total_return'] = (returns.iloc[-1] / returns.iloc[0]) - 1
        report['annual_return'] = report['total_return'] * (252 / len(returns))
        report['volatility'] = returns.std() * np.sqrt(252)
        report['sharpe_ratio'] = PerformanceAnalyzer.calculate_sharpe_ratio(returns)
        report['max_drawdown'] = PerformanceAnalyzer.calculate_max_drawdown(returns.cumsum())[0]
        report['calmar_ratio'] = PerformanceAnalyzer.calculate_calmar_ratio(returns.cumsum())
        report['sortino_ratio'] = PerformanceAnalyzer.calculate_sortino_ratio(returns)
        report['var_95'] = PerformanceAnalyzer.calculate_var(returns, 0.05)
        report['cvar_95'] = PerformanceAnalyzer.calculate_cvar(returns, 0.05)
        
        # Benchmark comparison if available
        if benchmark_returns is not None:
            report['alpha'] = RiskMetrics.calculate_alpha(returns, benchmark_returns)
            report['beta'] = RiskMetrics.calculate_beta(returns, benchmark_returns)
            report['information_ratio'] = RiskMetrics.calculate_information_ratio(returns, benchmark_returns)
            report['tracking_error'] = RiskMetrics.calculate_tracking_error(returns, benchmark_returns)
        
        return report
    
    @staticmethod
    def generate_risk_report(returns: pd.Series) -> Dict[str, float]:
        """Generate risk analysis report"""
        report = {}
        
        # Risk metrics
        report['volatility'] = returns.std() * np.sqrt(252)
        report['downside_volatility'] = returns[returns < 0].std() * np.sqrt(252)
        report['skewness'] = returns.skew()
        report['kurtosis'] = returns.kurtosis()
        report['var_95'] = PerformanceAnalyzer.calculate_var(returns, 0.05)
        report['var_99'] = PerformanceAnalyzer.calculate_var(returns, 0.01)
        report['cvar_95'] = PerformanceAnalyzer.calculate_cvar(returns, 0.05)
        report['cvar_99'] = PerformanceAnalyzer.calculate_cvar(returns, 0.01)
        
        # Drawdown analysis
        drawdown, peak_date, trough_date = PerformanceAnalyzer.calculate_max_drawdown(returns.cumsum())
        report['max_drawdown'] = drawdown
        report['drawdown_duration'] = (trough_date - peak_date).days if pd.notna(trough_date) and pd.notna(peak_date) else 0
        
        return report

# Utility functions
def safe_divide(numerator: float, denominator: float, default: float = 0) -> float:
    """Safe division with default value"""
    if denominator == 0:
        return default
    return numerator / denominator

def normalize_data(data: pd.Series) -> pd.Series:
    """Normalize data to 0-1 range"""
    return (data - data.min()) / (data.max() - data.min())

def winsorize_data(data: pd.Series, lower_percentile: float = 0.01, upper_percentile: float = 0.99) -> pd.Series:
    """Winsorize data to remove outliers"""
    lower_bound = data.quantile(lower_percentile)
    upper_bound = data.quantile(upper_percentile)
    
    return data.clip(lower_bound, upper_bound)
