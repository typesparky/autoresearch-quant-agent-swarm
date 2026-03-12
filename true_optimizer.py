#!/usr/bin/env python3
"""
True Optimization - Parallel strategies, real-time tracking, profit maximization.

Solves the 5-minute evaluation problem:
- All strategies execute simultaneously (no delays)
- Real-time performance tracking
- Thompson Sampling for profit optimization
- Meta-learning for zero-second strategy selection
"""

import asyncio
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass, field
import json
import pickle

from market_discovery import Market, Sector
from balanced_iteration_agent import Strategy


@dataclass
class StrategyState:
    """State of a strategy for Thompson Sampling."""
    strategy_id: str
    alpha: int = 1  # Wins
    beta: int = 1   # Losses
    total_trades: int = 0
    total_pnl: float = 0.0
    win_rate: float = 0.0
    sharpe: float = 0.0


@dataclass
class MarketConditions:
    """Current market conditions."""
    timestamp: datetime
    volatility: float
    trend: str  # "up", "down", "sideways"
    liquidity: float
    sentiment: float
    time_of_day: str  # "morning", "afternoon", "evening", "night"


@dataclass
class ExecutionResult:
    """Result of strategy execution."""
    strategy_id: str
    market_id: str
    side: str
    position_size: float
    entry_price: float
    entry_time: datetime
    status: str = "open"  # open, resolved, failed
    outcome: Optional[bool] = None
    pnl: Optional[float] = None
    resolution_time: Optional[datetime] = None


class TrueOptimizer:
    """
    True optimizer with parallel execution, real-time tracking, profit maximization.

    Solves stale data problem:
    - All strategies execute simultaneously
    - No evaluation delays
    - Real-time performance tracking
    - Thompson Sampling for profit optimization
    """

    def __init__(
        self,
        agent_id: str,
        sector: Sector,
        num_strategies: int = 10,
        max_position_size: float = 500,
        portfolio_value: float = 10000,
    ):
        self.agent_id = agent_id
        self.sector = sector
        self.num_strategies = num_strategies
        self.max_position_size = max_position_size
        self.portfolio_value = portfolio_value

        # Strategy states (Thompson Sampling)
        self.strategy_states: Dict[str, StrategyState] = {}
        self.allocation: Dict[str, float] = {}  # Strategy -> % of portfolio

        # Market conditions
        self.current_conditions: Optional[MarketConditions] = None

        # Execution tracking
        self.executions: List[ExecutionResult] = []
        self.resolved_trades: List[ExecutionResult] = []

        # Performance tracking
        self.performance_metrics = {
            'total_pnl': 0.0,
            'win_rate': 0.0,
            'sharpe': 0.0,
            'max_drawdown': 0.0,
            'num_trades': 0,
            'num_wins': 0,
        }

        # Meta-learning model (predicts best strategy given conditions)
        self.meta_model: Optional[Dict] = None

        # Real-time tracking
        self.update_interval_seconds = 1  # Update every second
        self.last_update_time: Optional[datetime] = None

    async def initialize_strategies(self):
        """Initialize multiple strategies."""
        print(f"\n[Optimizer] Initializing {self.num_strategies} strategies...")

        # Generate diverse strategies
        strategy_types = [
            'xgboost_price_momentum',
            'neural_sentiment_fusion',
            'ensemble_weighted_voting',
            'lstm_time_series',
            'random_forest_features',
            'gradient_boosting',
            'hybrid_ml_fundamental',
            'mean_reversion',
            'trend_following',
        ]

        for i in range(self.num_strategies):
            strategy_type = strategy_types[i % len(strategy_types)]
            strategy_id = f"strategy_{i:03d}_{strategy_type}"

            # Initialize state (Beta(1, 1) = uniform)
            state = StrategyState(
                strategy_id=strategy_id,
                strategy_type=strategy_type,
                alpha=1,
                beta=1,
            )

            self.strategy_states[strategy_id] = state
            self.allocation[strategy_id] = 1.0 / self.num_strategies  # Equal start

            print(f"[Optimizer]  {strategy_id}: {strategy_type}")

        print(f"[Optimizer] Initialized {len(self.strategy_states)} strategies")

    def _thompson_sample(self) -> str:
        """
        Thompson Sampling: Select strategy based on Beta distributions.

        Returns strategy ID with highest sample.
        """
        samples = {}

        for strategy_id, state in self.strategy_states.items():
            # Sample from Beta distribution
            sample = np.random.beta(state.alpha, state.beta)
            samples[strategy_id] = sample

        # Select strategy with highest sample
        selected_strategy = max(samples, key=samples.get)

        return selected_strategy

    def _update_thompson_parameters(self, strategy_id: str, won: bool):
        """
        Update Thompson Sampling parameters after trade resolution.

        Beta(α, β) where:
        - α = wins + 1
        - β = losses + 1
        """
        state = self.strategy_states[strategy_id]

        state.total_trades += 1

        if won:
            state.alpha += 1
            state.num_wins += 1
        else:
            state.beta += 1

        # Update win rate
        state.win_rate = state.num_wins / state.total_trades

        print(f"[Thompson] {strategy_id}: {'WIN' if won else 'LOSS'} -> "
              f"Alpha={state.alpha}, Beta={state.beta}, WR={state.win_rate:.2%}")

    def _allocate_capital(self):
        """
        Allocate capital based on Thompson Sampling probabilities.

        Strategies with higher alpha/(alpha+beta) get more capital.
        """
        total_expected_value = 0

        # Calculate expected value for each strategy
        for strategy_id, state in self.strategy_states.items():
            if state.total_trades > 0:
                expected_value = state.alpha / (state.alpha + state.beta)
            else:
                # No data yet, equal allocation
                expected_value = 1.0

            total_expected_value += expected_value

        # Allocate based on expected value
        for strategy_id in self.strategy_states:
            if state.total_trades > 0:
                expected_value = state.alpha / (state.alpha + state.beta)
                allocation = (expected_value / total_expected_value) * self.portfolio_value
            else:
                allocation = self.portfolio_value / self.num_strategies

            self.allocation[strategy_id] = allocation

        print(f"\n[Allocation] Capital allocation based on Thompson Sampling:")
        for strategy_id, allocation in sorted(self.allocation.items(), key=lambda x: x[1], reverse=True):
            state = self.strategy_states[strategy_id]
            if state.total_trades > 0:
                wr_pct = state.win_rate * 100
            else:
                wr_pct = 0.0
            print(f"  {strategy_id}: ${allocation:.2f} ({allocation/self.portfolio_value*100:.1f}%) - "
                  f"WR: {wr_pct:.1f}% (α={state.alpha}, β={state.beta})")

    async def get_market_conditions(self, markets: List[Market]) -> MarketConditions:
        """
        Analyze current market conditions.

        Returns market conditions for meta-learning.
        """
        print(f"\n[Conditions] Analyzing market conditions...")

        # Calculate volatility
        yes_odds = [m.yes_odds for m in markets]
        volatility = np.std(yes_odds) if yes_odds else 0.0

        # Calculate trend
        avg_odds = np.mean(yes_odds)
        if len(markets) > 0:
            recent_odds = yes_odds[-10:]  # Last 10 markets
            recent_avg = np.mean(recent_odds)

            if recent_avg > avg_odds * 1.02:
                trend = "up"
            elif recent_avg < avg_odds * 0.98:
                trend = "down"
            else:
                trend = "sideways"
        else:
            trend = "sideways"

        # Calculate liquidity
        volumes = [m.current_volume for m in markets]
        liquidity = np.mean(volumes) if volumes else 0.0

        # Calculate sentiment (from odds)
        if volatility > 0:
            # High volatility = bearish sentiment (simplified)
            sentiment = -min(1.0, volatility * 5)
        else:
            sentiment = 0.0

        # Time of day
        hour = datetime.now().hour
        if 6 <= hour < 12:
            time_of_day = "morning"
        elif 12 <= hour < 18:
            time_of_day = "afternoon"
        elif 18 <= hour < 24:
            time_of_day = "evening"
        else:
            time_of_day = "night"

        conditions = MarketConditions(
            timestamp=datetime.now(),
            volatility=volatility,
            trend=trend,
            liquidity=liquidity,
            sentiment=sentiment,
            time_of_day=time_of_day,
        )

        print(f"[Conditions] Volatility: {volatility:.4f}")
        print(f"[Conditions] Trend: {trend}")
        print(f"[Conditions] Liquidity: ${liquidity:,.0f}")
        print(f"[Conditions] Sentiment: {sentiment:.2f}")
        print(f"[Conditions] Time: {time_of_day}")

        return conditions

    def _meta_predict_best_strategy(self, conditions: MarketConditions) -> Optional[str]:
        """
        Meta-learning: Predict best strategy given conditions.

        In production: Use trained ML model.
        For demo: Use heuristic.
        """
        if self.meta_model is None:
            # Build simple meta-model from historical performance
            self._build_meta_model()

        # Predict best strategy type
        if conditions.trend == "up":
            # Trending strategies
            best_type = "trend_following"
        elif conditions.volatility > 0.05:
            # High volatility = mean reversion
            best_type = "mean_reversion"
        elif conditions.sentiment < -0.3:
            # Bearish sentiment = trend_following (short)
            best_type = "trend_following"
        else:
            # Default
            best_type = "xgboost_price_momentum"

        # Find strategy of this type
        candidates = [
            s_id for s_id, s in self.strategy_states.items()
            if s.strategy_type == best_type
        ]

        if candidates:
            # Return strategy with best historical performance
            best_candidate = min(
                candidates,
                key=lambda s: self.strategy_states[s].sharpe if self.strategy_states[s].sharpe > 0 else 0,
                reverse=True
            )
            return best_candidate

        return None

    def _build_meta_model(self):
        """
        Build simple meta-model from historical performance.

        In production: Use ML model.
        For demo: Use heuristic lookup.
        """
        print(f"\n[Meta-Learning] Building meta-model...")

        # Simple heuristic mapping: conditions -> best strategy type
        self.meta_model = {
            'up_trend': 'trend_following',
            'down_trend': 'trend_following',
            'sideways': 'mean_reversion',
            'high_volatility': 'mean_reversion',
            'low_volatility': 'xgboost_price_momentum',
            'bearish_sentiment': 'trend_following',
            'bullish_sentiment': 'xgboost_price_momentum',
        }

        print(f"[Meta-Learning] Meta-model built with {len(self.meta_model)} rules")

    async def parallel_execute_strategies(
        self,
        markets: List[Market],
    ) -> List[ExecutionResult]:
        """
        Execute ALL strategies in parallel.

        All start at T=0, no delays, no stale data.
        """
        print(f"\n[Parallel] Executing {len(self.strategy_states)} strategies in parallel...")

        # Create execution tasks for all strategies
        execution_tasks = []

        for strategy_id, state in self.strategy_states.items():
            task = self._execute_strategy(strategy_id, markets, state)
            execution_tasks.append(task)

        # Execute all in parallel
        results = await asyncio.gather(*execution_tasks)

        # Track all executions
        self.executions.extend(results)

        print(f"[Parallel] Executed {len(results)} strategies")

        return results

    async def _execute_strategy(
        self,
        strategy_id: str,
        markets: List[Market],
        state: StrategyState,
    ) -> ExecutionResult:
        """
        Execute a single strategy on ALL markets.

        Batch prediction, edge detection, trade execution.
        """
        # Get position size from allocation
        position_size = min(self.allocation[strategy_id], self.max_position_size)
        position_size_per_market = position_size / len(markets) if markets else 0

        results = []

        for market in markets:
            # Simulate strategy execution
            # In production: Actual model prediction
            # For demo: Heuristic based on strategy type

            edge = self._calculate_strategy_edge(state, market)

            if edge > 0.05:  # 5% minimum edge
                # Execute trade
                result = ExecutionResult(
                    strategy_id=strategy_id,
                    market_id=market.market_id,
                    side='YES' if edge > 0 else 'NO',
                    position_size=position_size_per_market,
                    entry_price=market.yes_odds,
                    entry_time=datetime.now(),
                    status='open',
                )
                results.append(result)
            else:
                # No edge, skip
                pass

        return results[0] if results else None

    def _calculate_strategy_edge(
        self,
        state: StrategyState,
        market: Market,
    ) -> float:
        """
        Calculate edge for a strategy on a market.

        In production: Use actual model prediction.
        For demo: Heuristic based on strategy type.
        """
        # Strategy type specific edge calculation
        strategy_type = state.strategy_type

        if strategy_type == "xgboost_price_momentum":
            # Momentum: predict higher odds will increase
            edge = (market.yes_odds - 0.5) * 0.3  # Predict upward trend
        elif strategy_type == "mean_reversion":
            # Mean reversion: predict odds will revert to mean
            edge = (0.5 - market.yes_odds) * 0.3  # Predict downward reversion
        elif strategy_type == "trend_following":
            # Trend following: go with current trend
            edge = market.yes_odds - 0.5
        elif strategy_type == "neural_sentiment_fusion":
            # Sentiment: use sentiment signal
            edge = market.sentiment * 0.2
        else:
            # Default: random edge
            edge = np.random.normal(0, 0.05)

        return edge

    async def update_performance_realtime(self):
        """
        Update performance metrics in real-time.

        Track PnL, Sharpe, drawdown as trades resolve.
        """
        # Calculate current metrics
        resolved = [r for r in self.resolved_trades if r.outcome is not None]

        if resolved:
            total_pnl = sum(r.pnl for r in resolved if r.pnl is not None)
            num_trades = len(resolved)
            num_wins = sum(1 for r in resolved if r.outcome and r.pnl is not None and r.pnl > 0)

            # Calculate returns
            returns = [r.pnl / self.portfolio_value for r in resolved if r.pnl is not None]

            if returns and len(returns) > 1:
                win_rate = num_wins / num_trades
                sharpe = np.mean(returns) / (np.std(returns) + 1e-8) * np.sqrt(252 * 24)

                # Calculate max drawdown
                cumulative = np.cumsum([r.pnl / self.portfolio_value for r in resolved if r.pnl is not None])
                running_max = np.maximum.accumulate(cumulative)
                drawdown = (running_max - cumulative) / (running_max + 1e-8)
                max_drawdown = np.max(drawdown) if len(drawdown) > 0 else 0
            else:
                win_rate = 0.0
                sharpe = 0.0
                max_drawdown = 0.0

            # Update performance metrics
            self.performance_metrics = {
                'total_pnl': total_pnl,
                'win_rate': win_rate,
                'sharpe': sharpe,
                'max_drawdown': max_drawdown,
                'num_trades': num_trades,
                'num_wins': num_wins,
            }

    async def run_parallel_iteration(
        self,
        markets: List[Market],
        iteration_num: int,
    ) -> Dict:
        """
        Run one parallel iteration.

        1. Get market conditions
        2. Meta-learn best strategy
        3. Thompson Sample (or use meta prediction)
        4. Allocate capital
        5. Execute ALL strategies in parallel (no delays)
        6. Track performance in real-time
        """
        iteration_start = datetime.now()

        print(f"\n{'='*80}")
        print(f"TRUE OPTIMIZATION ITERATION - {self.agent_id}")
        print(f"Iteration: {iteration_num}")
        print(f"{'='*80}\n")

        # Phase 1: Get market conditions
        self.current_conditions = await self.get_market_conditions(markets)

        # Phase 2: Meta-learn best strategy
        best_strategy = self._meta_predict_best_strategy(self.current_conditions)

        if best_strategy:
            print(f"\n[Meta-Learning] Predicted best strategy: {best_strategy}")
        else:
            print(f"\n[Meta-Learning] Using Thompson Sampling")

        # Phase 3: Thompson Sample (or use meta prediction)
        if best_strategy:
            selected_strategy = best_strategy
        else:
            selected_strategy = self._thompson_sample()

        print(f"\n[Selection] Selected strategy: {selected_strategy}")

        # Phase 4: Allocate capital
        self._allocate_capital()

        # Phase 5: Execute ALL strategies in parallel
        execution_results = await self.parallel_execute_strategies(markets)

        # Phase 6: Track performance
        await self.update_performance_realtime()

        # Calculate iteration time
        iteration_time = (datetime.now() - iteration_start).total_seconds()

        result = {
            'iteration': iteration_num,
            'conditions': {
                'volatility': self.current_conditions.volatility,
                'trend': self.current_conditions.trend,
                'liquidity': self.current_conditions.liquidity,
            },
            'selected_strategy': selected_strategy,
            'num_strategies': len(self.strategy_states),
            'num_trades': len(execution_results),
            'performance': self.performance_metrics,
            'allocation': self.allocation.copy(),
            'thompson_samples': {
                s_id: self.strategy_states[s_id].alpha / (self.strategy_states[s_id].alpha + self.strategy_states[s_id].beta)
                for s_id in self.strategy_states
            },
            'iteration_time': iteration_time,
            'timestamp': datetime.now().isoformat(),
        }

        # Print summary
        self._print_iteration_summary(result)

        return result

    def _print_iteration_summary(self, result: Dict):
        """Print iteration summary."""
        perf = result['performance']

        print(f"\n{'='*80}")
        print(f"ITERATION SUMMARY")
        print(f"{'='*80}")
        print(f"Iteration time: {result['iteration_time']:.2f}s")

        print(f"\nMarket Conditions:")
        print(f"  Volatility: {result['conditions']['volatility']:.4f}")
        print(f"  Trend: {result['conditions']['trend']}")
        print(f"  Liquidity: ${result['conditions']['liquidity']:,.0f}")

        print(f"\nSelected Strategy:")
        print(f"  {result['selected_strategy']}")

        print(f"\nPerformance:")
        print(f"  Total PnL: ${perf['total_pnl']:.2f}")
        print(f"  Win Rate: {perf['win_rate']:.2%}")
        print(f"  Sharpe: {perf['sharpe']:.2f}")
        print(f"  Max Drawdown: {perf['max_drawdown']:.2%}")
        print(f"  Total Trades: {perf['num_trades']}")
        print(f"  Winning Trades: {perf['num_wins']}")

        print(f"\nTop 5 Strategies (by Thompson probability):")
        sorted_strategies = sorted(
            result['thompson_samples'].items(),
            key=lambda x: x[1],
            reverse=True,
        )[:5]

        for strategy_id, probability in sorted_strategies:
            state = self.strategy_states[strategy_id]
            if state.total_trades > 0:
                wr_pct = state.win_rate * 100
            else:
                wr_pct = 0.0
            print(f"  {strategy_id}: {probability:.3f} (WR: {wr_pct:.1f}%, "
                  f"{state.total_trades} trades, α={state.alpha}, β={state.beta})")

        print(f"{'='*80}\n")

    async def resolve_random_trades(self):
        """
        Simulate random resolutions (for demo).

        In production: Actual resolutions from markets.
        """
        # Simulate 10% of open trades resolving
        open_trades = [e for e in self.executions if e.status == 'open']

        if not open_trades:
            return

        num_to_resolve = max(1, len(open_trades) // 10)

        # Randomly select trades to resolve
        indices = np.random.choice(len(open_trades), num_to_resolve, replace=False)

        for i, idx in enumerate(indices):
            trade = open_trades[idx]

            # Simulate outcome (in production: get actual from market)
            if np.random.random() < 0.5:
                outcome = True  # YES won
            else:
                outcome = False  # NO won

            # Calculate PnL
            if outcome:
                # YES won
                if trade.side == 'YES':
                    # Bet on YES, won
                    return_amount = trade.position_size * (1.0 / trade.entry_price)
                    pnl = return_amount - trade.position_size
                else:
                    # Bet on NO, won (NO won, so YES lost)
                    return_amount = trade.position_size * (1.0 / (1.0 - trade.entry_price))
                    pnl = return_amount - trade.position_size
            else:
                # NO won
                if trade.side == 'YES':
                    # Bet on YES, lost
                    pnl = -trade.position_size
                else:
                    # Bet on NO, won
                    return_amount = trade.position_size * (1.0 / (1.0 - trade.entry_price))
                    pnl = return_amount - trade.position_size

            # Update trade
            trade.outcome = outcome
            trade.pnl = pnl
            trade.resolution_time = datetime.now()
            trade.status = 'resolved'

            # Update Thompson parameters
            self._update_thompson_parameters(trade.strategy_id, outcome)

            # Add to resolved
            self.resolved_trades.append(trade)

            print(f"\n[Resolved] {trade.market_id}: {trade.side} - "
                  f"{'WIN' if outcome else 'LOSS'} - PnL: ${pnl:.2f}")

        print(f"\n[Resolved] {num_to_resolve} trades resolved")


async def main():
    """Demo true optimization."""
    from market_discovery import MarketDiscovery

    print("\n" + "="*80)
    print("TRUE OPTIMIZATION - Parallel Strategies, Real-Time Tracking, Profit Maximization")
    print("="*80 + "\n")

    # Create optimizer
    optimizer = TrueOptimizer(
        agent_id="true_optimizer_001",
        sector=Sector.SPORTS,
        num_strategies=10,
        portfolio_value=10000,
    )

    # Initialize strategies
    await optimizer.initialize_strategies()

    # Create market discovery
    discovery = MarketDiscovery(
        min_volume=1000.0,
        max_resolution_days=30,
        min_liquidity_score=0.3,
    )

    # Run iterations
    markets = await discovery.discover_markets(sectors=[Sector.SPORTS], limit=50)

    print(f"\nRunning iterations...\n")

    for iteration in range(1, 4):
        # Run parallel iteration
        result = await optimizer.run_parallel_iteration(markets, iteration)

        # Resolve some trades
        await optimizer.resolve_random_trades()

        # Brief pause
        await asyncio.sleep(1)

    # Print final summary
    print(f"\n{'='*80}")
    print(f"FINAL SUMMARY")
    print(f"{'='*80}")

    perf = optimizer.performance_metrics
    print(f"\nPortfolio Performance:")
    print(f"  Initial Value: ${optimizer.portfolio_value:.2f}")
    print(f"  Final Value: ${optimizer.portfolio_value + perf['total_pnl']:.2f}")
    print(f"  Total PnL: ${perf['total_pnl']:.2f}")
    print(f"  Return: {perf['total_pnl']/optimizer.portfolio_value:.2%}")

    print(f"\nRisk Metrics:")
    print(f"  Win Rate: {perf['win_rate']:.2%}")
    print(f"  Sharpe Ratio: {perf['sharpe']:.2f}")
    print(f"  Max Drawdown: {perf['max_drawdown']:.2%}")

    print(f"\nTrading:")
    print(f"  Total Trades: {perf['num_trades']}")
    print(f"  Winning Trades: {perf['num_wins']}")

    print(f"\nTop Strategies (by Thompson probability):")
    sorted_strategies = sorted(
        optimizer.strategy_states.items(),
        key=lambda x: optimizer.strategy_states[x[1]].total_trades,
        reverse=True,
    )[:5]

    for strategy_id, state in sorted_strategies:
        probability = state.alpha / (state.alpha + state.beta)
        print(f"  {strategy_id}: {probability:.3f} - "
              f"{state.win_rate:.2%} WR, {state.total_trades} trades")

    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    asyncio.run(main())
