#!/usr/bin/env python3
"""
Shadow Testing System - Paper trading on live data.

Run models in real-time with live data, but no real money.
Track predictions vs actual outcomes to validate performance.
"""

import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
import json
import pickle
from collections import deque


class ShadowTester:
    """
    Run models in shadow mode (paper trading) on live data.

    Monitors:
    - Prediction accuracy
    - Real-time PnL
    - Performance degradation
    - Regime-specific performance
    """

    def __init__(
        self,
        model_path: str,
        initial_capital: float = 10000,
        position_size: float = 0.05,
        min_trading_hours: int = 24,  # Minimum hours before evaluation
        max_degradation_pct: float = 0.20,  # Max allowed performance drop
    ):
        self.model_path = model_path
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.position_size = position_size
        self.min_trading_hours = min_trading_hours
        self.max_degradation = max_degradation_pct

        # Load model
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)

        # State tracking
        self.predictions: List[Dict] = []
        self.trades: List[Dict] = []
        self.equity_curve: deque = deque([initial_capital], maxlen=1000)
        self.start_time = None
        self.baseline_sharpe: Optional[float] = None

        # Performance monitoring
        self.rolling_returns: deque = deque(maxlen=100)
        self.hourly_returns: List[float] = []

    def start(self):
        """Start shadow testing."""
        self.start_time = datetime.now()
        print(f"\n[Shadow Test] Starting shadow testing")
        print(f"  Model: {self.model_path}")
        print(f"  Capital: ${self.capital:.2f}")
        print(f"  Position size: {self.position_size:.1%}")
        print(f"  Minimum trading hours: {self.min_trading_hours}")
        print(f"\n{'='*60}\n")

    async def process_tick(
        self,
        features: Dict,
        market_data: Dict,
    ) -> Optional[Dict]:
        """
        Process a new data tick.

        Args:
            features: Feature dict for prediction
            market_data: Current market state

        Returns:
            Trade decision if made, None otherwise
        """
        if self.start_time is None:
            self.start()

        # Prepare features for model
        feature_vector = self._prepare_features(features)

        # Make prediction
        prediction = self.model.predict([feature_vector])[0]

        # Record prediction
        prediction_record = {
            'timestamp': datetime.now(),
            'features': features,
            'prediction': prediction,
            'market_state': market_data,
        }

        # Check if we should trade
        trade_decision = self._evaluate_trade(prediction, market_data)

        if trade_decision:
            # Record trade
            trade_record = {
                'timestamp': datetime.now(),
                'prediction': prediction,
                'decision': trade_decision,
                'capital': self.capital,
            }
            self.trades.append(trade_record)
            prediction_record['trade'] = trade_record

            print(f"[Shadow Test] Trade: {trade_decision['side']} | "
                  f"Pred: {prediction:.4f} | Capital: ${self.capital:.2f}")

        self.predictions.append(prediction_record)
        return trade_decision

    def _prepare_features(self, features: Dict) -> List[float]:
        """Convert features dict to vector for model."""
        # This depends on your feature schema
        # Adjust based on your model's expected input
        feature_keys = [
            'return_1h', 'return_6h', 'return_24h', 'return_168h',
            'volatility_24h', 'volatility_168h',
            'momentum_24h', 'momentum_168h',
            'volume_change_24h',
            'sentiment_mean_24h', 'sentiment_std_24h',
            'regime_encoded',
        ]

        vector = [features.get(k, 0) for k in feature_keys]
        return vector

    def _evaluate_trade(self, prediction: float, market_data: Dict) -> Optional[Dict]:
        """
        Evaluate whether to make a trade based on prediction.

        Simple threshold-based strategy for shadow testing.
        """
        threshold = 0.001  # 0.1% threshold

        if abs(prediction) > threshold:
            # Trade size based on confidence
            confidence = min(abs(prediction) / threshold, 2.0)
            trade_capital = self.capital * self.position_size * confidence

            side = 'long' if prediction > 0 else 'short'

            return {
                'side': side,
                'size': trade_capital,
                'confidence': confidence,
                'threshold': threshold,
                'prediction': prediction,
            }

        return None

    def update_outcome(self, trade_index: int, actual_return: float):
        """
        Update trade with actual outcome.

        Called after trade resolves (e.g., after 1 hour).
        """
        if trade_index >= len(self.trades):
            return

        trade = self.trades[trade_index]
        side = trade['decision']['side']

        # Calculate PnL
        if side == 'long':
            pnl = trade['decision']['size'] * actual_return
        else:
            pnl = trade['decision']['size'] * -actual_return

        trade['actual_return'] = actual_return
        trade['pnl'] = pnl
        trade['resolved'] = True
        trade['resolution_time'] = datetime.now()

        # Update capital
        self.capital += pnl
        self.equity_curve.append(self.capital)

        # Track returns
        self.rolling_returns.append(pnl / self.initial_capital)

        print(f"[Shadow Test] Trade resolved: {side} | "
              f"PnL: ${pnl:.2f} | Capital: ${self.capital:.2f}")

    def get_performance(self) -> Dict:
        """Calculate current performance metrics."""
        if not self.trades:
            return {
                'trading_hours': 0,
                'total_trades': 0,
                'sharpe_ratio': 0,
                'win_rate': 0,
                'pnl': 0,
            }

        # Calculate trading hours
        if self.start_time:
            trading_hours = (datetime.now() - self.start_time).total_seconds() / 3600
        else:
            trading_hours = 0

        # Resolve trades
        resolved_trades = [t for t in self.trades if t.get('resolved', False)]

        if not resolved_trades:
            return {
                'trading_hours': trading_hours,
                'total_trades': len(self.trades),
                'resolved_trades': 0,
                'sharpe_ratio': 0,
                'win_rate': 0,
                'pnl': 0,
                'capital': self.capital,
            }

        # Calculate metrics
        total_pnl = sum(t['pnl'] for t in resolved_trades)
        winning_trades = len([t for t in resolved_trades if t['pnl'] > 0])
        win_rate = winning_trades / len(resolved_trades)

        # Sharpe ratio
        returns = [t['pnl'] / self.initial_capital for t in resolved_trades]
        if returns and np.std(returns) > 0:
            sharpe = np.mean(returns) / np.std(returns) * np.sqrt(24 * 30)  # Hourly -> monthly
        else:
            sharpe = 0

        # Max drawdown
        peak_capital = max(self.equity_curve) if self.equity_curve else self.initial_capital
        min_capital = min(self.equity_curve) if self.equity_curve else self.initial_capital
        max_drawdown = (peak_capital - min_capital) / peak_capital if peak_capital > 0 else 0

        return {
            'trading_hours': trading_hours,
            'total_trades': len(self.trades),
            'resolved_trades': len(resolved_trades),
            'pending_trades': len(self.trades) - len(resolved_trades),
            'sharpe_ratio': sharpe,
            'win_rate': win_rate,
            'pnl': total_pnl,
            'capital': self.capital,
            'return_pct': (self.capital - self.initial_capital) / self.initial_capital,
            'max_drawdown': max_drawdown,
        }

    def check_degradation(self) -> Tuple[bool, Optional[float]]:
        """
        Check if performance has degraded from baseline.

        Returns:
            (degraded, current_sharpe): Whether degraded and current Sharpe
        """
        performance = self.get_performance()

        if self.baseline_sharpe is None:
            # Set baseline on first check
            self.baseline_sharpe = performance['sharpe_ratio']
            return False, performance['sharpe_ratio']

        current_sharpe = performance['sharpe_ratio']

        # Check for degradation
        if self.baseline_sharpe > 0:
            degradation_pct = (self.baseline_sharpe - current_sharpe) / abs(self.baseline_sharpe)
            degraded = degradation_pct > self.max_degradation

            if degraded:
                print(f"\n[Shadow Test] ⚠️  PERFORMANCE DEGRADED")
                print(f"  Baseline Sharpe: {self.baseline_sharpe:.2f}")
                print(f"  Current Sharpe:   {current_sharpe:.2f}")
                print(f"  Degradation:      {degradation_pct:.1%}\n")

            return degraded, current_sharpe

        return False, current_sharpe

    def is_ready_for_evaluation(self) -> Tuple[bool, str]:
        """
        Check if model has enough data for evaluation.

        Returns:
            (ready, reason): Whether ready and why/why not
        """
        if self.start_time is None:
            return False, "Shadow testing not started"

        trading_hours = (datetime.now() - self.start_time).total_seconds() / 3600

        if trading_hours < self.min_trading_hours:
            return False, f"Insufficient trading time ({trading_hours:.1f}h < {self.min_trading_hours}h)"

        resolved_trades = [t for t in self.trades if t.get('resolved', False)]

        if len(resolved_trades) < 30:
            return False, f"Insufficient resolved trades ({len(resolved_trades)} < 30)"

        return True, "Ready for evaluation"

    def print_status(self):
        """Print current status."""
        performance = self.get_performance()
        ready, reason = self.is_ready_for_evaluation()

        print(f"\n{'='*60}")
        print("SHADOW TESTING STATUS")
        print(f"{'='*60}")

        print(f"\nTrading Stats:")
        print(f"  Trading Hours:    {performance['trading_hours']:.1f} / {self.min_trading_hours} required")
        print(f"  Total Trades:     {performance['total_trades']}")
        print(f"  Resolved:         {performance['resolved_trades']}")
        print(f"  Pending:          {performance['pending_trades']}")

        print(f"\nPerformance:")
        print(f"  PnL:              ${performance['pnl']:.2f}")
        print(f"  Return:           {performance['return_pct']:.2%}")
        print(f"  Capital:          ${performance['capital']:.2f}")
        print(f"  Sharpe Ratio:     {performance['sharpe_ratio']:.2f}")
        print(f"  Win Rate:         {performance['win_rate']:.2%}")
        print(f"  Max Drawdown:     {performance['max_drawdown']:.2%}")

        print(f"\nEvaluation Status:")
        print(f"  Ready:            {'YES' if ready else 'NO'}")
        print(f"  Reason:           {reason}")

        if self.baseline_sharpe is not None:
            degraded, current_sharpe = self.check_degradation()
            print(f"\nDegradation Check:")
            print(f"  Baseline Sharpe:  {self.baseline_sharpe:.2f}")
            print(f"  Current Sharpe:   {current_sharpe:.2f}")
            print(f"  Degraded:        {'YES ⚠️' if degraded else 'NO'}")

        print(f"\n{'='*60}\n")

    def save_results(self, path: Optional[str] = None):
        """Save shadow test results."""
        if path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = f"shadow_test_results_{timestamp}.json"

        results = {
            'model_path': self.model_path,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'initial_capital': self.initial_capital,
            'final_capital': self.capital,
            'performance': self.get_performance(),
            'baseline_sharpe': self.baseline_sharpe,
            'num_predictions': len(self.predictions),
            'num_trades': len(self.trades),
        }

        with open(path, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"Shadow test results saved to: {path}")


async def main():
    """Run example shadow test."""
    print("\n" + "="*60)
    print("Shadow Testing System - Paper Trading")
    print("="*60 + "\n")

    # For demo, create a mock model
    from xgboost import XGBRegressor
    import numpy as np

    # Train simple model
    X_train = np.random.randn(100, 12)
    y_train = np.random.randn(100)
    model = XGBRegressor(n_estimators=10, max_depth=3)
    model.fit(X_train, y_train)

    # Save model
    model_path = "demo_model.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)

    # Initialize shadow tester
    tester = ShadowTester(
        model_path=model_path,
        initial_capital=10000,
        position_size=0.05,
        min_trading_hours=1,  # Demo: 1 hour minimum
    )

    tester.start()

    # Simulate some ticks
    print("Simulating 10 ticks...\n")

    for i in range(10):
        # Generate random features
        features = {
            'return_1h': np.random.randn() * 0.01,
            'return_6h': np.random.randn() * 0.02,
            'return_24h': np.random.randn() * 0.05,
            'return_168h': np.random.randn() * 0.1,
            'volatility_24h': abs(np.random.randn() * 0.02),
            'volatility_168h': abs(np.random.randn() * 0.03),
            'momentum_24h': np.random.randn() * 0.03,
            'momentum_168h': np.random.randn() * 0.1,
            'volume_change_24h': np.random.randn() * 0.1,
            'sentiment_mean_24h': np.random.randn() * 0.3,
            'sentiment_std_24h': abs(np.random.randn() * 0.2),
            'regime_encoded': np.random.choice([-1, 0, 1]),
        }

            market_data = {
                'price': 50000 * (1 + np.random.randn() * 0.01),
                'volume': np.random.lognormal(15, 0.5),
            }

        # Process tick
        trade = await tester.process_tick(features, market_data)

        # Resolve some trades randomly
        if i > 0 and i % 3 == 0:
            tester.update_outcome(
                trade_index=i-3,
                actual_return=np.random.randn() * 0.01,
            )

        await asyncio.sleep(0.5)

    # Print status
    tester.print_status()

    # Save results
    tester.save_results()

    # Cleanup
    Path(model_path).unlink(missing_ok=True)


if __name__ == "__main__":
    asyncio.run(main())
