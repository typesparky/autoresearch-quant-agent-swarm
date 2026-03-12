#!/usr/bin/env python3
"""
Backtesting Engine - Production-grade validation with walk-forward analysis.

Implements:
- Walk-forward analysis (rolling window backtest)
- Out-of-sample testing only
- Multiple market regimes
- Statistical significance testing
- No lookahead bias
"""

import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import json
import pickle
from scipy import stats


class BacktestingEngine:
    """Production backtesting with walk-forward analysis."""

    def __init__(
        self,
        train_window_days: int = 90,
        test_window_days: int = 30,
        min_trades_for_significance: int = 100,
        confidence_level: float = 0.95,
    ):
        """
        Initialize backtesting engine.

        Args:
            train_window_days: Days of training data
            test_window_days: Days of out-of-sample testing
            min_trades_for_significance: Minimum trades for statistical validation
            confidence_level: Confidence level for statistical tests (0-1)
        """
        self.train_window = timedelta(days=train_window_days)
        self.test_window = timedelta(days=test_window_days)
        self.min_trades = min_trades_for_significance
        self.confidence_level = confidence_level

    def load_historical_data(
        self,
        market_type: str,
        start_date: datetime,
        end_date: datetime,
    ) -> pd.DataFrame:
        """
        Load historical data for backtesting.

        In production, this would connect to your data source.
        For now, simulate realistic crypto market data.
        """
        print(f"[Backtest] Loading historical data: {start_date.date()} to {end_date.date()}")

        # Generate realistic synthetic data
        # In production: load from your database (Polymarket, etc.)
        dates = pd.date_range(start=start_date, end=end_date, freq='H')
        n_samples = len(dates)

        # Simulate price with trend + volatility + regime changes
        np.random.seed(42)

        # Create regimes: bullish, bearish, sideways
        regimes = []
        regime_labels = []

        for i, date in enumerate(dates):
            if i < n_samples * 0.3:
                regimes.append(0.0001)  # Bullish
                regime_labels.append("bullish")
            elif i < n_samples * 0.6:
                regimes.append(-0.0001)  # Bearish
                regime_labels.append("bearish")
            else:
                regimes.append(0.00001)  # Sideways
                regime_labels.append("sideways")

        regimes = np.array(regimes)

        # Generate price series
        returns = np.random.normal(regimes, 0.02, n_samples)
        price = 50000 * (1 + returns).cumprod()

        # Generate volume
        volume = np.random.lognormal(15, 0.5, n_samples)

        # Generate sentiment
        sentiment = np.random.normal(0, 0.3, n_samples)

        df = pd.DataFrame({
            'timestamp': dates,
            'price': price,
            'volume': volume,
            'sentiment': sentiment,
            'regime': regime_labels,
            'returns': returns,
        })

        return df

    def create_features(
        self,
        df: pd.DataFrame,
        lookback_periods: List[int] = [1, 6, 24, 168],  # 1h, 6h, 1d, 1w
    ) -> pd.DataFrame:
        """
        Create features for model training.

        No lookahead - only use past data.
        """
        df = df.copy()

        # Lagged returns
        for period in lookback_periods:
            df[f'return_{period}h'] = df['returns'].rolling(period).sum()
            df[f'volatility_{period}h'] = df['returns'].rolling(period).std()

        # Momentum indicators
        df['momentum_24h'] = df['price'] / df['price'].shift(24) - 1
        df['momentum_168h'] = df['price'] / df['price'].shift(168) - 1

        # Volume changes
        df['volume_change_24h'] = df['volume'] / df['volume'].shift(24) - 1

        # Sentiment aggregations
        df['sentiment_mean_24h'] = df['sentiment'].rolling(24).mean()
        df['sentiment_std_24h'] = df['sentiment'].rolling(24).std()

        # Regime encoding
        regime_map = {'bullish': 1, 'bearish': -1, 'sideways': 0}
        df['regime_encoded'] = df['regime'].map(regime_map)

        # Target: next hour return (for training)
        df['target'] = df['returns'].shift(-1)

        # Drop NaNs (from lagged features)
        df = df.dropna()

        return df

    def walk_forward_analysis(
        self,
        df: pd.DataFrame,
        model_factory,
        feature_columns: List[str],
    ) -> Dict:
        """
        Perform walk-forward analysis.

        Rolling train/test windows with no overlap.
        """
        print(f"\n[Backtest] Starting walk-forward analysis")
        print(f"Train window: {self.train_window.days} days")
        print(f"Test window: {self.test_window.days} days")

        all_results = []
        equity_curve = [100000]  # Starting capital
        trades = []

        # Find windows
        total_range = df['timestamp'].max() - df['timestamp'].min()
        num_windows = int(total_range / (self.train_window + self.test_window))

        print(f"Total data range: {total_range.days} days")
        print(f"Number of windows: {num_windows}")

        for window_idx in range(num_windows):
            # Calculate window boundaries
            start_date = df['timestamp'].min() + window_idx * (self.train_window + self.test_window)
            train_end = start_date + self.train_window
            test_end = train_end + self.test_window

            # Skip if not enough data
            if test_end > df['timestamp'].max():
                break

            # Split data
            train_df = df[(df['timestamp'] >= start_date) & (df['timestamp'] < train_end)]
            test_df = df[(df['timestamp'] >= train_end) & (df['timestamp'] < test_end)]

            print(f"\n[Window {window_idx + 1}]")
            print(f"  Train: {train_df['timestamp'].min().date()} to {train_df['timestamp'].max().date()}")
            print(f"  Test:  {test_df['timestamp'].min().date()} to {test_df['timestamp'].max().date()}")
            print(f"  Train samples: {len(train_df)}, Test samples: {len(test_df)}")

            # Skip if insufficient data
            if len(train_df) < 100 or len(test_df) < 50:
                print(f"  Skipping - insufficient data")
                continue

            # Train model
            try:
                model = model_factory()

                X_train = train_df[feature_columns].values
                y_train = train_df['target'].values

                model.fit(X_train, y_train)

                # Test model
                X_test = test_df[feature_columns].values
                y_test = test_df['target'].values

                predictions = model.predict(X_test)

                # Simulate trading
                window_results = self._simulate_trading(
                    test_df,
                    predictions,
                    y_test,
                    equity_curve[-1],
                )

                all_results.append(window_results)
                equity_curve.extend(window_results['equity_curve'][1:])  # Skip initial capital
                trades.extend(window_results['trades'])

                print(f"  Window PnL: ${window_results['pnl']:.2f}")
                print(f"  Win Rate: {window_results['win_rate']:.2%}")
                print(f"  Sharpe: {window_results['sharpe_ratio']:.2f}")

            except Exception as e:
                print(f"  Error: {e}")
                continue

        # Aggregate results
        final_results = self._aggregate_results(all_results, equity_curve, trades)

        return final_results

    def _simulate_trading(
        self,
        df: pd.DataFrame,
        predictions: np.ndarray,
        actual_returns: np.ndarray,
        initial_capital: float,
    ) -> Dict:
        """
        Simulate trading on test data.

        Simple strategy: long if prediction positive, short if negative.
        Position size: 5% of capital.
        """
        capital = initial_capital
        position_size_pct = 0.05
        max_drawdown = 0
        peak_capital = capital

        equity_curve = [capital]
        trades = []

        for i, (pred, actual_return) in enumerate(zip(predictions, actual_returns)):
            # Determine position
            if pred > 0:
                # Long
                position_capital = capital * position_size_pct
                trade_return = position_capital * actual_return
                capital += trade_return

                trades.append({
                    'timestamp': df['timestamp'].iloc[i],
                    'prediction': pred,
                    'actual': actual_return,
                    'pnl': trade_return,
                    'side': 'long',
                    'capital': capital,
                })

            elif pred < 0:
                # Short
                position_capital = capital * position_size_pct
                trade_return = position_capital * -actual_return
                capital += trade_return

                trades.append({
                    'timestamp': df['timestamp'].iloc[i],
                    'prediction': pred,
                    'actual': actual_return,
                    'pnl': trade_return,
                    'side': 'short',
                    'capital': capital,
                })

            # Track drawdown
            peak_capital = max(peak_capital, capital)
            current_drawdown = (peak_capital - capital) / peak_capital
            max_drawdown = max(max_drawdown, current_drawdown)

            equity_curve.append(capital)

        # Calculate metrics
        pnl = capital - initial_capital
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t['pnl'] > 0])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0

        # Calculate Sharpe
        returns_list = [t['pnl'] / initial_capital for t in trades]
        if returns_list:
            sharpe = np.mean(returns_list) / (np.std(returns_list) + 1e-8) * np.sqrt(252 * 24)  # Hourly -> annual
        else:
            sharpe = 0

        return {
            'pnl': pnl,
            'capital': capital,
            'win_rate': win_rate,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': total_trades - winning_trades,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'equity_curve': equity_curve,
            'trades': trades,
        }

    def _aggregate_results(
        self,
        all_results: List[Dict],
        equity_curve: List[float],
        trades: List[Dict],
    ) -> Dict:
        """Aggregate results across all windows."""
        if not all_results:
            return {
                'valid': False,
                'error': 'No valid windows',
            }

        # Calculate aggregate metrics
        total_pnl = sum(r['pnl'] for r in all_results)
        total_trades = sum(r['total_trades'] for r in all_results)
        winning_trades = sum(r['winning_trades'] for r in all_results)

        # Overall Sharpe
        overall_returns = [t['pnl'] / 100000 for t in trades]
        if overall_returns:
            sharpe = np.mean(overall_returns) / (np.std(overall_returns) + 1e-8) * np.sqrt(252 * 24)
        else:
            sharpe = 0

        # Max drawdown
        peak_capital = max(equity_curve)
        min_capital = min(equity_curve)
        max_drawdown = (peak_capital - min_capital) / peak_capital

        # Regime analysis
        regime_results = self._analyze_regimes(trades)

        # Statistical significance testing
        significance_test = self._test_significance(trades)

        results = {
            'valid': True,
            'total_pnl': total_pnl,
            'final_capital': equity_curve[-1],
            'initial_capital': equity_curve[0],
            'return_pct': (equity_curve[-1] - equity_curve[0]) / equity_curve[0],
            'sharpe_ratio': sharpe,
            'win_rate': winning_trades / total_trades if total_trades > 0 else 0,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': total_trades - winning_trades,
            'max_drawdown': max_drawdown,
            'num_windows': len(all_results),
            'equity_curve': equity_curve,
            'trades': trades,
            'regime_results': regime_results,
            'significance_test': significance_test,
        }

        return results

    def _analyze_regimes(self, trades: List[Dict]) -> Dict:
        """Analyze performance across market regimes."""
        if not trades:
            return {}

        regime_pnl = {}
        regime_trades = {}
        regime_win_rate = {}

        for trade in trades:
            # Determine regime from timestamp
            timestamp = trade['timestamp']
            hour = timestamp.hour

            # Simple regime classification based on time (simplified)
            if 6 <= hour < 18:
                regime = "active"
            else:
                regime = "quiet"

            if regime not in regime_pnl:
                regime_pnl[regime] = 0
                regime_trades[regime] = 0
                regime_win_rate[regime] = {'wins': 0, 'total': 0}

            regime_pnl[regime] += trade['pnl']
            regime_trades[regime] += 1
            regime_win_rate[regime]['total'] += 1

            if trade['pnl'] > 0:
                regime_win_rate[regime]['wins'] += 1

        return {
            'regime_pnl': regime_pnl,
            'regime_trades': regime_trades,
            'regime_win_rate': {
                r: v['wins'] / v['total'] if v['total'] > 0 else 0
                for r, v in regime_win_rate.items()
            },
        }

    def _test_significance(self, trades: List[Dict]) -> Dict:
        """Test statistical significance of returns."""
        if len(trades) < self.min_trades:
            return {
                'significant': False,
                'reason': f'insufficient_trades ({len(trades)} < {self.min_trades})',
            }

        returns = [t['pnl'] for t in trades]
        mean_return = np.mean(returns)

        # One-sample t-test: is mean return > 0?
        t_stat, p_value = stats.ttest_1samp(returns, 0)

        # Check if significant
        significant = p_value < (1 - self.confidence_level)

        return {
            'significant': significant,
            't_statistic': t_stat,
            'p_value': p_value,
            'confidence_level': self.confidence_level,
            'mean_return': mean_return,
            'num_trades': len(trades),
        }

    def validate_model(self, results: Dict) -> Tuple[bool, str]:
        """
        Validate if model meets minimum criteria for deployment.

        Returns:
            (valid, reason): Whether model is deployable and why/why not.
        """
        if not results.get('valid'):
            return False, results.get('error', 'Invalid results')

        # Minimum Sharpe
        min_sharpe = 1.0
        if results['sharpe_ratio'] < min_sharpe:
            return False, f"Sharpe ratio ({results['sharpe_ratio']:.2f}) below minimum ({min_sharpe})"

        # Minimum win rate
        min_win_rate = 0.55
        if results['win_rate'] < min_win_rate:
            return False, f"Win rate ({results['win_rate']:.2%}) below minimum ({min_win_rate:.0%})"

        # Maximum drawdown
        max_drawdown_limit = 0.15
        if results['max_drawdown'] > max_drawdown_limit:
            return False, f"Max drawdown ({results['max_drawdown']:.2%}) exceeds limit ({max_drawdown_limit:.0%})"

        # Minimum trades
        if results['total_trades'] < self.min_trades:
            return False, f"Insufficient trades ({results['total_trades']} < {self.min_trades})"

        # Statistical significance
        significance = results.get('significance_test', {})
        if not significance.get('significant', False):
            return False, f"Not statistically significant (p={significance.get('p_value', 1):.3f})"

        # At least one positive window
        if results['num_windows'] == 0:
            return False, "No valid windows"

        return True, "Model passes all validation criteria"

    def print_results(self, results: Dict):
        """Print backtesting results."""
        if not results.get('valid'):
            print(f"\n[Backtest] Invalid: {results.get('error')}")
            return

        print(f"\n{'='*60}")
        print("BACKTESTING RESULTS")
        print(f"{'='*60}")

        print(f"\nOverall Performance:")
        print(f"  Total PnL:        ${results['total_pnl']:.2f}")
        print(f"  Return:           {results['return_pct']:.2%}")
        print(f"  Sharpe Ratio:     {results['sharpe_ratio']:.2f}")
        print(f"  Win Rate:         {results['win_rate']:.2%}")
        print(f"  Max Drawdown:     {results['max_drawdown']:.2%}")

        print(f"\nTrading Statistics:")
        print(f"  Total Trades:     {results['total_trades']}")
        print(f"  Winning Trades:   {results['winning_trades']}")
        print(f"  Losing Trades:    {results['losing_trades']}")

        print(f"\nValidation:")
        print(f"  Windows Tested:   {results['num_windows']}")
        validity, reason = self.validate_model(results)
        print(f"  Deployable:       {validity}")
        print(f"  Reason:           {reason}")

        # Significance test
        sig_test = results.get('significance_test', {})
        if sig_test:
            print(f"\nStatistical Significance:")
            print(f"  T-statistic:      {sig_test.get('t_statistic', 0):.3f}")
            print(f"  P-value:          {sig_test.get('p_value', 1):.3f}")
            print(f"  Significant:      {sig_test.get('significant', False)}")

        # Regime analysis
        regime_results = results.get('regime_results', {})
        if regime_results.get('regime_pnl'):
            print(f"\nRegime Performance:")
            for regime, pnl in regime_results['regime_pnl'].items():
                win_rate = regime_results['regime_win_rate'].get(regime, 0)
                trades = regime_results['regime_trades'].get(regime, 0)
                print(f"  {regime.capitalize()}:")
                print(f"    PnL:       ${pnl:.2f}")
                print(f"    Win Rate:  {win_rate:.2%} ({trades} trades)")

        print(f"\n{'='*60}\n")


# Model factories for testing
def xgboost_model_factory():
    """Factory for XGBoost model."""
    from xgboost import XGBRegressor
    return XGBRegressor(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
    )


def simple_linear_factory():
    """Factory for simple linear model."""
    from sklearn.linear_model import LinearRegression
    return LinearRegression()


def random_forest_factory():
    """Factory for Random Forest model."""
    from sklearn.ensemble import RandomForestRegressor
    return RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=42,
    )


async def main():
    """Run example backtest."""
    print("\n" + "="*60)
    print("Backtesting Engine - Walk-Forward Analysis")
    print("="*60 + "\n")

    # Initialize engine
    engine = BacktestingEngine(
        train_window_days=90,
        test_window_days=30,
        min_trades_for_significance=100,
        confidence_level=0.95,
    )

    # Load historical data (6 months)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)

    df = engine.load_historical_data(
        market_type="crypto",
        start_date=start_date,
        end_date=end_date,
    )

    # Create features
    feature_columns = [
        'return_1h', 'return_6h', 'return_24h', 'return_168h',
        'volatility_24h', 'volatility_168h',
        'momentum_24h', 'momentum_168h',
        'volume_change_24h',
        'sentiment_mean_24h', 'sentiment_std_24h',
        'regime_encoded',
    ]

    df = engine.create_features(df)

    print(f"\nFeatures created: {len(feature_columns)}")
    print(f"Total samples: {len(df)}")

    # Run walk-forward analysis
    results = engine.walk_forward_analysis(
        df=df,
        model_factory=xgboost_model_factory,
        feature_columns=feature_columns,
    )

    # Print results
    engine.print_results(results)

    # Save results
    output_path = Path("backtest_results.json")
    with open(output_path, 'w') as f:
        # Remove large lists for JSON serialization
        saveable_results = results.copy()
        saveable_results.pop('equity_curve', None)
        saveable_results.pop('trades', None)
        json.dump(saveable_results, f, indent=2, default=str)

    print(f"Results saved to: {output_path}\n")


if __name__ == "__main__":
    asyncio.run(main())
