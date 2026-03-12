#!/usr/bin/env python3
"""
Tiered Optimization System - Time-horizon-aware execution.

Matches iteration time to market's characteristics.
Immediate markets: 30-second iterations
Fast markets: 1-minute iterations
Normal markets: 5-minute iterations
Slow markets: 30-minute iterations
"""

import asyncio
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass, field
import json

from market_discovery import Market, Sector


@dataclass
class Strategy:
    """Simple strategy dataclass."""
    strategy_id: str
    name: str
    description: str
    theory: str
    code: str
    features: str
    model_type: str
    risk_management: Dict
    iteration_created: int


@dataclass
class TierConfig:
    """Configuration for a market tier."""
    tier: str
    time_to_resolution: timedelta  # Maximum time to resolution
    iteration_time: float  # Iteration time in seconds
    evaluation_time: float  # Evaluation time (if any)
    allow_evaluation: bool
    parallel_execution: bool  # Execute in parallel with others
    description: str


# Tier configurations
TIERS = {
    "IMMEDIATE": TierConfig(
        tier="IMMEDIATE",
        time_to_resolution=timedelta(minutes=15),
        iteration_time=30,  # 30 seconds
        evaluation_time=0,
        allow_evaluation=False,  # No evaluation, just execute
        parallel_execution=True,
        description="Markets resolving in minutes (live scores, in-play)"
    ),
    "FAST": TierConfig(
        tier="FAST",
        time_to_resolution=timedelta(hours=4),
        iteration_time=60,  # 1 minute
        evaluation_time=30,  # 30 seconds quick eval
        allow_evaluation=True,
        parallel_execution=True,
        description="Markets resolving in hours (hourly props, game results)"
    ),
    "NORMAL": TierConfig(
        tier="NORMAL",
        time_to_resolution=timedelta(hours=24),
        iteration_time=300,  # 5 minutes
        evaluation_time=60,  # 1 minute evaluation
        allow_evaluation=True,
        parallel_execution=True,
        description="Markets resolving in days (daily props, outcomes)",
    ),
    "SLOW": TierConfig(
        tier="SLOW",
        time_to_resolution=timedelta(weeks=2),
        iteration_time=1800,  # 30 minutes
        evaluation_time=600,  # 10 minutes thorough eval
        allow_evaluation=True,
        parallel_execution=False,  # Sequential to not overload
        description="Markets resolving in weeks (playoffs, championships)",
    ),
    "VERY_SLOW": TierConfig(
        tier="VERY_SLOW",
        time_to_resolution=timedelta(weeks=8),
        iteration_time=7200,  # 2 hours
        evaluation_time=3600,  # 1 hour deep analysis
        allow_evaluation=False,
        parallel_execution=False,  # Sequential, deep analysis
        description="Markets resolving in months (elections, seasonal events)",
    ),
}


class MarketTierClassifier:
    """
    Classify markets into tiers based on time horizon.

    Automatic detection based on market description and resolution time.
    """

    @staticmethod
    def classify_market(market: Market) -> str:
        """Classify market into tier based on characteristics."""
        # Keywords that indicate tier
        immediate_keywords = [
            "live", "in-play", "score", "minute", "minute-", "next",
            "current", "now", "real-time", "in-game", "half-time",
        ]

        fast_keywords = [
            "hourly", "h1", "end of hour", "60 min",
            "first half", "second half", "period",
        ]

        normal_keywords = [
            "daily", "end of day", "close", "outcome", "result",
            "winner", "24h", "today", "this week",
        ]

        slow_keywords = [
            "playoff", "championship", "series", "best of",
            "quarter", "monthly", "this month",
        ]

        very_slow_keywords = [
            "election", "president", "congress", "parliament",
            "season", "full season", "year", "2024",
        ]

        # Check keywords in title and description
        title_lower = market.title.lower()
        time_str = f"{market.resolution_time.hour}h"

        for keyword in very_slow_keywords:
            if keyword in title_lower:
                return "VERY_SLOW"

        for keyword in slow_keywords:
            if keyword in title_lower:
                return "SLOW"

        for keyword in normal_keywords:
            if keyword in title_lower:
                return "NORMAL"

        for keyword in fast_keywords:
            if keyword in title_lower:
                return "FAST"

        for keyword in immediate_keywords:
            if keyword in title_lower:
                return "IMMEDIATE"

        # Check time to resolution
        time_to_resolution = market.resolution_time - datetime.now()
        hours_to_resolution = time_to_resolution.total_seconds() / 3600

        if hours_to_resolution <= 0.25:  # 15 minutes
            return "IMMEDIATE"
        elif hours_to_resolution <= 4:  # 4 hours
            return "FAST"
        elif hours_to_resolution <= 24:  # 1 day
            return "NORMAL"
        elif hours_to_resolution <= 720:  # 1 month
            return "SLOW"
        else:
            return "VERY_SLOW"


class TieredOptimizer:
    """
    Tiered optimization system with time-horizon-aware execution.

    Different tiers execute with different iteration times and strategies.
    """

    def __init__(
        self,
        agent_id: str,
        sector: Sector,
        initial_capital: float = 10000,
        max_position_size: float = 500,
    ):
        self.agent_id = agent_id
        self.sector = sector
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.max_position_size = max_position_size

        # Tier tracking
        self.markets_by_tier: Dict[str, List[Market]] = defaultdict(list)
        self.strategies_by_tier: Dict[str, List[Strategy]] = defaultdict(list)
        self.allocation_by_tier: Dict[str, float] = defaultdict(float)
        self.total_allocation: float = initial_capital

        # Performance tracking per tier
        self.tier_performance: Dict[str, Dict] = defaultdict(dict)

    async def discover_and_classify_markets(self, discovery) -> Dict[str, List[Market]]:
        """
        Discover markets and classify into tiers.
        """
        print(f"\n[Tiered Optimizer] Discovering and classifying markets...")

        # Discover all markets
        all_markets = await discovery.discover_markets(
            sectors=[self.sector],
            limit=500,
        )

        # Classify into tiers
        for market in all_markets:
            tier = MarketTierClassifier.classify_market(market)
            self.markets_by_tier[tier].append(market)

        # Print classification
        print(f"\n[Tiered Optimizer] Market Classification:")
        for tier, markets in sorted(self.markets_by_tier.items()):
            print(f"  {tier}: {len(markets)} markets")
            if markets:
                # Show first example
                example = markets[0]
                print(f"    Example: {example.title}")
                print(f"    Resolution: {(example.resolution_time - datetime.now()).total_seconds()/3600:.1f} hours")

        return self.markets_by_tier

    async def initialize_tier_strategies(self):
        """
        Initialize diverse strategies for each tier.

        Different tiers use different iteration times and strategies.
        """
        print(f"\n[Tiered Optimizer] Initializing tier-specific strategies...")

        # Strategy types by tier
        tier_strategy_types = {
            "IMMEDIATE": [
                "momentum_instant",
                "volatility_scalping",
                "order_book_depth",
            ],
            "FAST": [
                "price_momentum_short",
                "sentiment_reactive",
                "microstructure_mean_reversion",
            ],
            "NORMAL": [
                "xgboost_price_features",
                "neural_sentiment_fusion",
                "ensemble_weighted",
            ],
            "SLOW": [
                "lstm_time_series_deep",
                "random_forest_comprehensive",
                "gradient_boosting_extensive",
            ],
            "VERY_SLOW": [
                "transformer_attention",
                "hybrid_ml_fundamental",
                "multi_modal_sentiment",
            ],
        }

        # Generate strategies for each tier
        for tier, strategy_types in tier_strategy_types.items():
            for i, strategy_type in enumerate(strategy_types):
                strategy_id = f"{tier.lower()}_strat_{i:03d}_{strategy_type}"

                # Different iteration times for different tiers
                config = TIERS[tier]
                iteration_time_minutes = config.iteration_time / 60

                # Generate strategy
                strategy = self._generate_strategy(
                    strategy_id=strategy_id,
                    tier=tier,
                    strategy_type=strategy_type,
                    iteration_time_minutes=iteration_time_minutes,
                )

                self.strategies_by_tier[tier].append(strategy)

                print(f"  {tier}: {strategy_id} ({strategy_type})")

        print(f"[Tiered Optimizer] Initialized {len(self.strategies_by_tier['IMMEDIATE'])} immediate, "
              f"{len(self.strategies_by_tier['FAST'])} fast, "
              f"{len(self.strategies_by_tier['NORMAL'])} normal, "
              f"{len(self.strategies_by_tier['SLOW'])} slow, "
              f"{len(self.strategies_by_tier['VERY_SLOW'])} very slow strategies")

    def _generate_strategy(
        self,
        strategy_id: str,
        tier: str,
        strategy_type: str,
        iteration_time_minutes: float,
    ) -> Strategy:
        """Generate a strategy with tier-specific parameters."""
        config = TIERS[tier]

        # Tier-specific code
        code = f"""
# Tier: {tier}
# Iteration Time: {iteration_time_minutes:.0f} minutes
# Strategy Type: {strategy_type}
# Description: {config.description}

import numpy as np
import pandas as pd
from {self._get_model_import(tier)} import {self._get_model_class(tier)}

class {tier.replace('_', '').title()}Strategy:
    def __init__(self):
        self.strategy_type = "{strategy_type}"
        self.tier = "{tier}"
        self.iteration_time = {iteration_time_minutes} minutes

        # Tier-specific model
        self.model = {self._get_model_class(tier)}()

        # Tier-specific features
        self.features = {self._get_feature_list(tier, strategy_type)}

        # Tier-specific risk management
        if tier == "IMMEDIATE":
            # Ultra-fast execution, minimal evaluation
            self.risk_management = {{
                'position_size_pct': 0.02,  # 2% per trade (small, fast)
                'max_position_size': 200,
                'min_edge_pct': 0.02,  # Lower threshold for fast markets
                'stop_loss_pct': 0.01,  # 1% stop (fast markets move fast)
                'take_profit_pct': 0.02,  # 2% take (fast)
                'max_positions': 20,  # More positions (faster markets)
            }}
        elif tier == "FAST":
            # Fast execution, quick evaluation
            self.risk_management = {{
                'position_size_pct': 0.03,  # 3% per trade
                'max_position_size': 300,
                'min_edge_pct': 0.03,
                'stop_loss_pct': 0.015,
                'take_profit_pct': 0.03,
                'max_positions': 15,
            }}
        elif tier == "NORMAL":
            # Standard execution, full evaluation
            self.risk_management = {{
                'position_size_pct': 0.05,  # 5% per trade
                'max_position_size': 500,
                'min_edge_pct': 0.05,
                'stop_loss_pct': 0.02,
                'take_profit_pct': 0.05,
                'max_positions': 10,
            }}
        elif tier == "SLOW":
            # Conservative execution, thorough evaluation
            self.risk_management = {{
                'position_size_pct': 0.03,  # 3% (smaller, less risk)
                'max_position_size': 500,
                'min_edge_pct': 0.07,  # Higher threshold (more selective)
                'stop_loss_pct': 0.025,
                'take_profit_pct': 0.07,
                'max_positions': 5,  # Fewer positions
            }}
        elif tier == "VERY_SLOW":
            # Very conservative, deep evaluation
            self.risk_management = {{
                'position_size_pct': 0.02,  # 2% (very selective)
                'max_position_size': 500,
                'min_edge_pct': 0.10,  # High threshold (very selective)
                'stop_loss_pct': 0.03,
                'take_profit_pct': 0.10,
                'max_positions': 3,  # Very few positions
            }}

    def predict(self, X):
        # Tier-specific prediction logic
        if self.tier == "IMMEDIATE":
            # Very simple model for speed
            base_prob = 0.5 + (X[:, 0] if len(X[0]) > 0 else 0) * 0.3
            return base_prob
        else:
            # Full model for accuracy
            return self.model.predict(X)

    def get_edge(self, prediction, market_odds):
        edge = prediction - market_odds
        return edge

# Training function
def train_strategy(X_train, y_train):
    model = {self._get_model_class(tier)}()
    model.fit(X_train, y_train)
    return model

# Evaluation function
def evaluate_strategy(model, X_test, y_test):
    predictions = model.predict(X_test)
    metrics = {{
        'accuracy': (predictions > 0.5) == (y_test > 0.5),
        'mse': ((predictions - y_test) ** 2).mean(),
        'mae': (predictions - y_test).abs().mean(),
    }}
    return metrics
"""
        return code

        # Create strategy object
        strategy = Strategy(
            strategy_id=strategy_id,
            name=f"{tier}_{strategy_type}",
            description=f"{tier} tier: {strategy_type} strategy",
            theory=f"Optimized for {config.description}. Iteration time: {iteration_time_minutes:.0f} min. Strategy: {strategy_type}.",
            code=code,
            features=self._get_feature_list(tier, strategy_type),
            model_type=self._get_model_class(tier),
            risk_management=config.risk_management,
            iteration_created=0,
        )

        return strategy

    def _get_model_import(self, tier: str) -> str:
        """Get model import for tier."""
        if tier in ["IMMEDIATE", "FAST", "NORMAL"]:
            return "sklearn.ensemble"
        elif tier == "SLOW":
            return "xgboost"
        elif tier == "VERY_SLOW":
            return "tensorflow.keras"
        else:
            return "sklearn.ensemble"

    def _get_model_class(self, tier: str) -> str:
        """Get model class for tier."""
        if tier in ["IMMEDIATE", "FAST", "NORMAL"]:
            return "RandomForestRegressor"
        elif tier == "SLOW":
            return "XGBRegressor"
        elif tier == "VERY_SLOW":
            return "Sequential"
        else:
            return "RandomForestRegressor"

    def _get_feature_list(self, tier: str, strategy_type: str) -> str:
        """Get feature list based on tier and strategy type."""
        # Base features
        base_features = [
            'price_momentum_1h', 'price_momentum_24h',
            'volume_change_24h', 'volatility_24h',
            'liquidity_score',
        ]

        # Tier-specific features
        if tier in ["FAST", "NORMAL"]:
            # Add sentiment, time features
            tier_features = [
                'sentiment_mean_24h', 'sentiment_std_24h',
                'time_of_day', 'day_of_week',
            ]
        elif tier in ["SLOW", "VERY_SLOW"]:
            # Add advanced features
            tier_features = [
                'momentum_1d', 'momentum_7d',
                'mean_reversion_7d', 'volatility_7d',
                'trend_strength', 'regime_indicator',
            ]
        else:
            tier_features = []

        # Strategy-specific features
        if "momentum" in strategy_type:
            strategy_features = [
                'price_momentum_5m', 'price_momentum_15m',
                'volume_momentum_5m',
            ]
        elif "sentiment" in strategy_type:
            strategy_features = [
                'news_sentiment', 'social_sentiment',
                'analyst_rating',
            ]
        elif "mean_reversion" in strategy_type:
            strategy_features = [
                'price_vs_ma7d', 'rsi_14d',
                'bollinger_position',
            ]
        else:
            strategy_features = []

        return f"[{', '.join(base_features + tier_features + strategy_features)}]"

    async def allocate_capital_by_tier(self):
        """
        Allocate capital across tiers based on their characteristics.

        Immediate markets: More capital (fast turnover)
        Slow markets: Less capital (slow turnover)
        """
        print(f"\n[Tiered Optimizer] Allocating capital across tiers...")

        # Calculate total allocation weights
        tier_weights = {
            "IMMEDIATE": 0.15,  # 15% - fast turnover
            "FAST": 0.25,       # 25% - frequent opportunities
            "NORMAL": 0.35,      # 35% - balance
            "SLOW": 0.15,        # 15% - selective opportunities
            "VERY_SLOW": 0.10,  # 10% - high-quality opportunities
        }

        # Allocate
        total_weighted = sum(tier_weights.values())
        for tier, weight in tier_weights.items():
            allocation = (weight / total_weighted) * self.total_allocation
            self.allocation_by_tier[tier] = allocation

        print(f"[Tiered Optimizer] Capital allocation:")
        for tier, allocation in sorted(self.allocation_by_tier.items()):
            config = TIERS[tier]
            print(f"  {tier}: ${allocation:.0f} ({allocation/self.total_allocation*100:.1f}%) - "
                  f"{config.description}")

    async def run_tiered_iteration(
        self,
        tier: str,
        markets: List[Market],
        iteration_num: int,
    ) -> Dict:
        """
        Run iteration for a specific tier.

        Each tier has its own iteration time and strategy.
        """
        config = TIERS[tier]

        print(f"\n{'='*80}")
        print(f"TIERED ITERATION - {tier}")
        print(f"Iteration: {iteration_num}")
        print(f"Iteration Time: {config.iteration_time:.0f} seconds")
        print(f"Description: {config.description}")
        print(f"{'='*80}\n")

        iteration_start = datetime.now()

        # Phase 1: Analyze (tier-specific)
        analyze_time = config.iteration_time * 0.2  # 20% of iteration time
        # Simulate analysis
        await asyncio.sleep(analyze_time)  # Simulated analysis time

        # Phase 2: Develop (tier-specific)
        develop_time = config.iteration_time * 0.4  # 40% of iteration time
        # Simulate development
        await asyncio.sleep(develop_time)

        # Phase 3: Test (tier-specific)
        test_time = config.iteration_time * 0.3  # 30% of iteration time
        # Simulate testing
        await asyncio.sleep(test_time)

        # Phase 4: Evaluate (tier-specific)
        eval_time = config.iteration_time * 0.1  # 10% of iteration time
        # Simulate evaluation
        await asyncio.sleep(eval_time)

        # Total iteration time
        total_time = (datetime.now() - iteration_start).total_seconds()

        # Package result
        result = {
            'tier': tier,
            'iteration': iteration_num,
            'iteration_time': total_time,
            'num_markets': len(markets),
            'config': {
                'time_to_resolution': str(config.time_to_resolution),
                'iteration_time': config.iteration_time,
                'description': config.description,
            },
            'timestamp': datetime.now().isoformat(),
        }

        print(f"\n[Tiered Optimizer] {tier} iteration {iteration_num} complete: {total_time:.1f}s")

        return result

    async def run_parallel_tiered_iterations(
        self,
        all_markets: Dict[str, List[Market]],
        iteration_num: int,
    ) -> Dict[str, Dict]:
        """
        Run iterations for ALL tiers in parallel.

        Immediate: 30-second iterations
        Fast: 1-minute iterations
        Normal: 5-minute iterations
        Slow: 30-minute iterations
        Very Slow: 2-hour iterations

        Each tier runs independently, optimizing for its market type.
        """
        print(f"\n{'='*80}")
        print(f"PARALLEL TIERED ITERATION - All Tiers")
        print(f"Iteration: {iteration_num}")
        print(f"{'='*80}\n")

        # Create tasks for each tier
        tier_tasks = []

        for tier, markets in all_markets.items():
            if not markets:
                continue

            task = self.run_tiered_iteration(tier, markets, iteration_num)
            tier_tasks.append(task)

        # Execute all tiers in parallel
        start_time = datetime.now()

        results = await asyncio.gather(*tier_tasks, return_exceptions=True)

        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()

        # Package results
        tier_results = {}

        for tier, result in zip(all_markets.keys(), results):
            if isinstance(result, Exception):
                tier_results[tier] = {
                    'error': str(result),
                    'success': False,
                }
            else:
                tier_results[tier] = {
                    'success': True,
                    'result': result,
                }

        print(f"\n[Tiered Optimizer] All {len(tier_results)} tiers completed in {total_time:.1f}s")

        # Print summary
        print(f"\n[Tiered Optimizer] Iteration {iteration_num} Summary:")
        for tier, result_data in sorted(tier_results.items()):
            if result_data['success']:
                result = result_data['result']
                print(f"  {tier}: {result['iteration_time']:.1f}s - {result['num_markets']} markets")
            else:
                print(f"  {tier}: ERROR - {result_data['error']}")

        return tier_results

    async def optimize_portfolio(self):
        """
        Optimize portfolio allocation across tiers.

        Rebalance based on performance.
        """
        print(f"\n[Tiered Optimizer] Optimizing portfolio...")

        # Calculate tier performance (simulated)
        tier_performance = {
            tier: {
                'recent_return': np.random.normal(0.02, 0.01),
                'win_rate': 0.55 + np.random.normal(0, 0.05),
                'sharpe': np.random.normal(1.0, 0.3),
            }
            for tier in TIERS.keys()
        }

        # Update allocation based on performance
        new_allocation = {}

        for tier, perf in tier_performance.items():
            current_alloc = self.allocation_by_tier[tier]

            # More allocation to better tiers
            if perf['sharpe'] > 1.0:
                adjustment = 1.2  # Increase by 20%
            elif perf['sharpe'] < 0.5:
                adjustment = 0.8  # Decrease by 20%
            else:
                adjustment = 1.0  # No change

            new_allocation[tier] = current_alloc * adjustment

        # Normalize to total capital
        total_new_alloc = sum(new_allocation.values())
        for tier in new_allocation:
            new_allocation[tier] = (new_allocation[tier] / total_new_alloc) * self.total_allocation

        self.allocation_by_tier = new_allocation

        print(f"\n[Tiered Optimizer] New allocation:")
        for tier, alloc in sorted(self.allocation_by_tier.items()):
            config = TIERS[tier]
            print(f"  {tier}: ${alloc:.0f} ({alloc/self.total_allocation*100:.1f}%) - "
                  f"{config.description}")

    def print_system_summary(self):
        """Print system summary."""
        print(f"\n{'='*80}")
        print(f"TIERED OPTIMIZATION SYSTEM SUMMARY")
        print(f"{'='*80}")

        print(f"\nAgent: {self.agent_id}")
        print(f"Sector: {self.sector.value}")
        print(f"Initial Capital: ${self.initial_capital:.2f}")
        print(f"Current Capital: ${self.capital:.2f}")

        print(f"\nTier Classification:")
        print(f"  IMMEDIATE: {TIERS['IMMEDIATE'].description}")
        print(f"  FAST:       {TIERS['FAST'].description}")
        print(f"  NORMAL:     {TIERS['NORMAL'].description}")
        print(f"  SLOW:       {TIERS['SLOW'].description}")
        print(f"  VERY_SLOW:  {TIERS['VERY_SLOW'].description}")

        print(f"\nTier Configurations:")
        for tier, config in TIERS.items():
            print(f"  {tier}:")
            print(f"    Iteration Time: {config.iteration_time:.0f}s")
            print(f"    Max Resolution: {config.time_to_resolution}")
            print(f"    Allow Evaluation: {config.allow_evaluation}")
            print(f"    Parallel: {config.parallel_execution}")

        print(f"\nCurrent Allocation:")
        for tier, alloc in sorted(self.allocation_by_tier.items()):
            num_markets = len(self.markets_by_tier[tier])
            strategies = len(self.strategies_by_tier[tier])
            print(f"  {tier}: ${alloc:.0f} ({alloc/self.total_allocation*100:.1f}%) - "
                  f"{num_markets} markets, {strategies} strategies")

        print(f"{'='*80}\n")


async def main():
    """Demo tiered optimization."""
    from market_discovery import MarketDiscovery

    print("\n" + "="*80)
    print("TIERED OPTIMIZATION SYSTEM - Time-Horizon-Aware Execution")
    print("="*80 + "\n")

    # Create optimizer
    optimizer = TieredOptimizer(
        agent_id="tiered_opt_001",
        sector=Sector.SPORTS,
        initial_capital=10000,
    )

    # Create market discovery
    discovery = MarketDiscovery(
        min_volume=1000.0,
        max_resolution_days=30,
        min_liquidity_score=0.3,
    )

    # Discover and classify markets
    all_markets_by_tier = await optimizer.discover_and_classify_markets(discovery)

    # Initialize tier strategies
    await optimizer.initialize_tier_strategies()

    # Allocate capital
    await optimizer.allocate_capital_by_tier()

    # Print summary
    optimizer.print_system_summary()

    # Run parallel tiered iterations
    for iteration in range(1, 4):
        results = await optimizer.run_parallel_tiered_iterations(
            all_markets=all_markets_by_tier,
            iteration_num=iteration,
        )

        # Optimize portfolio
        await optimizer.optimize_portfolio()

        # Brief pause
        await asyncio.sleep(1)

    # Print final summary
    optimizer.print_system_summary()


if __name__ == "__main__":
    asyncio.run(main())
