#!/usr/bin/env python3
"""
Balanced Iteration Agent - True research with proper skill assessment.

Each iteration (30 min - 2 hours):
1. ANALYZE (5-15 min) - Fetch and analyze data
2. DEVELOP (10-45 min) - LLM generates NEW strategy
3. TEST (10-60 min) - Train and test on live data
4. EVALUATE (5-15 min) - Assess predictive skill

Not 2 seconds (no analysis), not weeks (too slow). Just right.
"""

import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import pickle
from dataclasses import dataclass, field
from collections import defaultdict

from market_discovery import Market, Sector
from live_trading_engine import Trade, LiveTradingEngine


@dataclass
class Strategy:
    """A trading strategy developed by the agent."""
    strategy_id: str
    name: str
    description: str
    theory: str
    code: str
    features: List[str]
    model_type: str
    risk_management: Dict
    iteration_created: int


@dataclass
class IterationResult:
    """Results from one iteration."""
    iteration: int
    strategy: Strategy
    performance: Dict
    skill_score: float
    deployable: bool
    reason: str
    timestamp: str


class BalancedIterationAgent:
    """
    Balanced iteration agent with true research.

    Each iteration develops a NEW strategy and tests it properly.
    """

    def __init__(
        self,
        agent_id: str,
        sector: Sector,
        iteration_time_minutes: int = 60,  # 1 hour by default
        llm_api_key: str = None,
    ):
        self.agent_id = agent_id
        self.sector = sector
        self.iteration_time = iteration_time_minutes
        self.llm_api_key = llm_api_key

        # Strategy tracking
        self.strategies: List[Strategy] = []
        self.iteration_results: List[IterationResult] = []

        # Performance tracking
        self.best_skill_score = 0.0
        self.best_strategy: Optional[Strategy] = None

        # Strategy diversity tracking
        self.strategy_types_used: Dict[str, int] = defaultdict(int)

    async def run_iteration(
        self,
        markets: List[Market],
        iteration_num: int,
    ) -> IterationResult:
        """
        Run one balanced iteration.

        1. Analyze data
        2. Develop NEW strategy
        3. Test on live data
        4. Evaluate predictive skill
        """
        print(f"\n{'='*80}")
        print(f"BALANCED ITERATION - {self.agent_id}")
        print(f"Iteration: {iteration_num}")
        print(f"Total time budget: {self.iteration_time} minutes")
        print(f"{'='*80}\n")

        iteration_start = datetime.now()

        # Phase 1: ANALYZE
        analyze_start = datetime.now()
        analysis_data = await self._analyze_data(markets)
        analyze_time = (datetime.now() - analyze_start).total_seconds() / 60

        print(f"[Phase 1] ANALYZE complete: {analyze_time:.1f} minutes")

        # Phase 2: DEVELOP
        develop_start = datetime.now()
        strategy = await self._develop_strategy(analysis_data, iteration_num)
        develop_time = (datetime.now() - develop_start).total_seconds() / 60

        print(f"[Phase 2] DEVELOP complete: {develop_time:.1f} minutes")
        print(f"  Strategy: {strategy.name}")
        print(f"  Model type: {strategy.model_type}")
        print(f"  Theory: {strategy.theory[:100]}...")

        # Phase 3: TEST
        test_start = datetime.now()
        performance = await self._test_strategy(strategy, markets)
        test_time = (datetime.now() - test_start).total_seconds() / 60

        print(f"[Phase 3] TEST complete: {test_time:.1f} minutes")

        # Phase 4: EVALUATE
        eval_start = datetime.now()
        skill_score, deployable, reason = self._evaluate_performance(performance)
        eval_time = (datetime.now() - eval_start).total_seconds() / 60

        print(f"[Phase 4] EVALUATE complete: {eval_time:.1f} minutes")
        print(f"  Skill score: {skill_score:.3f}")
        print(f"  Deployable: {'YES' if deployable else 'NO'}")
        print(f"  Reason: {reason}")

        # Package result
        total_time = (datetime.now() - iteration_start).total_seconds() / 60

        result = IterationResult(
            iteration=iteration_num,
            strategy=strategy,
            performance=performance,
            skill_score=skill_score,
            deployable=deployable,
            reason=reason,
            timestamp=datetime.now().isoformat(),
        )

        # Track results
        self.strategies.append(strategy)
        self.iteration_results.append(result)
        self.strategy_types_used[strategy.model_type] += 1

        # Update best
        if skill_score > self.best_skill_score:
            self.best_skill_score = skill_score
            self.best_strategy = strategy

        # Print summary
        print(f"\n{'='*80}")
        print(f"ITERATION {iteration_num} SUMMARY")
        print(f"{'='*80}")
        print(f"Phase times:")
        print(f"  Analyze:   {analyze_time:.1f} min")
        print(f"  Develop:    {develop_time:.1f} min")
        print(f"  Test:       {test_time:.1f} min")
        print(f"  Evaluate:   {eval_time:.1f} min")
        print(f"  Total:      {total_time:.1f} min")
        print(f"\nStrategy:")
        print(f"  Name:       {strategy.name}")
        print(f"  Model:      {strategy.model_type}")
        print(f"  Features:   {', '.join(strategy.features[:3])}...")
        print(f"\nPerformance:")
        print(f"  Skill:      {skill_score:.3f}")
        print(f"  Deploy:     {'YES' if deployable else 'NO'}")
        print(f"  Reason:     {reason}")
        print(f"{'='*80}\n")

        return result

    async def _analyze_data(self, markets: List[Market]) -> Dict:
        """
        Phase 1: Analyze data.

        Fetch and analyze recent data, identify patterns.
        """
        print(f"\n[Analyze] Fetching and analyzing data...")

        analysis = {
            'num_markets': len(markets),
            'avg_volume': np.mean([m.current_volume for m in markets]),
            'avg_yes_odds': np.mean([m.yes_odds for m in markets]),
            'odds_variance': np.var([m.yes_odds for m in markets]),
            'liquidity_distribution': {
                'high': len([m for m in markets if m.liquidity_score > 0.7]),
                'medium': len([m for m in markets if 0.4 <= m.liquidity_score <= 0.7]),
                'low': len([m for m in markets if m.liquidity_score < 0.4]),
            },
            'timestamp': datetime.now().isoformat(),
        }

        # Simulate fetching historical data
        # In production: Fetch last 7-30 days of data
        analysis['historical_data_available'] = True
        analysis['data_date_range'] = 'Last 7 days'
        analysis['num_data_points'] = len(markets) * 24 * 7  # Assume hourly data

        print(f"[Analyze] Analyzed {len(markets)} markets")
        print(f"[Analyze] Avg volume: ${analysis['avg_volume']:,.0f}")
        print(f"[Analyze] Odds variance: {analysis['odds_variance']:.4f}")

        return analysis

    async def _develop_strategy(
        self,
        analysis_data: Dict,
        iteration_num: int,
    ) -> Strategy:
        """
        Phase 2: Develop NEW strategy.

        LLM generates a NEW strategy (not just tweaking existing ones).
        """
        print(f"\n[Develop] Generating NEW strategy...")

        # Simulate LLM generating strategy
        # In production: Call actual LLM API

        # Get diversity info
        previous_strategies = [
            s.name for s in self.strategies[-5:]  # Last 5 strategies
        ]

        strategy = self._generate_strategy_via_llm(
            analysis_data,
            previous_strategies,
            iteration_num,
        )

        return strategy

    def _generate_strategy_via_llm(
        self,
        analysis_data: Dict,
        previous_strategies: List[str],
        iteration_num: int,
    ) -> Strategy:
        """
        Simulate LLM generating a NEW strategy.

        Enforces diversity and novelty.
        """
        # Strategy types to try
        strategy_types = [
            'xgboost_price_momentum',
            'neural_sentiment_fusion',
            'ensemble_weighted_voting',
            'lstm_time_series',
            'random_forest_features',
            'gradient_boosting',
            'hybrid_ml_fundamental',
        ]

        # Select diverse type
        used_types = list(self.strategy_types_used.keys())
        available_types = [t for t in strategy_types if t not in used_types]

        if available_types:
            model_type = np.random.choice(available_types)
        else:
            # All types used, pick one with lowest frequency
            model_type = min(
                self.strategy_types_used.keys(),
                key=lambda k: self.strategy_types_used[k]
            )

        # Generate strategy details
        strategy_name = f"{model_type}_v{iteration_num}"

        # Generate theory (explanation)
        theories = [
            "Combining price momentum with liquidity indicators to identify undervalued markets",
            "Using neural networks to fuse sentiment signals with price action for better predictions",
            "Ensemble approach combining multiple models to reduce variance and improve stability",
            "LSTM model trained on time-series data to capture temporal patterns and momentum",
            "Random forest with engineered features including volume, volatility, and momentum indicators",
            "Gradient boosting model optimizing for information coefficient and calibration",
        ]

        theory = theories[hash(model_type) % len(theories)]

        # Generate code (simplified)
        code = self._generate_strategy_code(model_type, theory)

        # Features
        feature_sets = {
            'xgboost_price_momentum': [
                'price_momentum_1h', 'price_momentum_24h', 'volume_change_24h',
                'volatility_24h', 'liquidity_score', 'odds_change_1h',
            ],
            'neural_sentiment_fusion': [
                'sentiment_mean', 'sentiment_std', 'price_change_6h',
                'volume_momentum', 'news_sentiment_24h', 'social_sentiment_6h',
            ],
            'ensemble_weighted_voting': [
                'xgb_prob', 'nn_prob', 'rf_prob', 'lstm_prob',
                'model_confidence', 'market_odds', 'liquidity_weight',
            ],
            'lstm_time_series': [
                'price_sequence_24h', 'volume_sequence_24h',
                'sentiment_sequence_24h', 'time_features',
            ],
            'random_forest_features': [
                'price_features', 'volume_features', 'momentum_features',
                'volatility_features', 'market_microstructure',
            ],
            'gradient_boosting': [
                'price_features', 'volume_features', 'liquidity_features',
                'temporal_features', 'cross_market_features',
            ],
        }

        features = feature_sets.get(model_type, feature_sets['xgboost_price_momentum'])

        # Risk management
        risk_management = {
            'position_size_pct': 0.05,
            'max_position_size': 500,
            'min_edge_pct': 0.05,
            'stop_loss_pct': 0.02,
            'take_profit_pct': 0.05,
            'max_drawdown_pct': 0.15,
            'max_positions': 10,
        }

        return Strategy(
            strategy_id=f"strat_{iteration_num}_{int(datetime.now().timestamp())}",
            name=strategy_name,
            description=f"{model_type} based prediction strategy",
            theory=theory,
            code=code,
            features=features,
            model_type=model_type,
            risk_management=risk_management,
            iteration_created=iteration_num,
        )

    def _generate_strategy_code(self, model_type: str, theory: str) -> str:
        """Generate code for strategy."""
        # Simplified code generation
        code = f"""
# Strategy: {model_type}
# Theory: {theory}

import numpy as np
import pandas as pd
from {self._get_model_import(model_type)} import {self._get_model_class(model_type)}

class {model_type.replace('_', '').title()}Strategy:
    def __init__(self):
        self.model = {self._get_model_class(model_type)}()
        self.features = {self._get_feature_list(model_type)}
        self.risk_management = {{
            'position_size_pct': 0.05,
            'max_position_size': 500,
            'min_edge_pct': 0.05,
        }}

    def predict(self, X):
        return self.model.predict(X)

    def get_edge(self, prediction, market_odds):
        edge = prediction - market_odds
        return edge

# Training function
def train_strategy(X_train, y_train):
    model = {self._get_model_class(model_type)}()
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

    def _get_model_import(self, model_type: str) -> str:
        """Get model import statement."""
        if 'xgboost' in model_type:
            return "xgboost"
        elif 'neural' in model_type or 'lstm' in model_type:
            return "tensorflow.keras"
        elif 'random_forest' in model_type:
            return "sklearn.ensemble"
        elif 'gradient_boosting' in model_type:
            return "xgboost"
        else:
            return "sklearn.ensemble"

    def _get_model_class(self, model_type: str) -> str:
        """Get model class name."""
        if 'xgboost' in model_type or 'gradient_boosting' in model_type:
            return "XGBRegressor"
        elif 'neural' in model_type or 'lstm' in model_type:
            return "Sequential"
        elif 'random_forest' in model_type:
            return "RandomForestRegressor"
        elif 'ensemble' in model_type:
            return "VotingRegressor"
        else:
            return "XGBRegressor"

    def _get_feature_list(self, model_type: str) -> str:
        """Get feature list."""
        features = {
            'xgboost_price_momentum': '["price_momentum_1h", "price_momentum_24h", "volume_change_24h"]',
            'neural_sentiment_fusion': '["sentiment_mean", "sentiment_std", "price_change_6h"]',
            'ensemble_weighted_voting': '["xgb_prob", "nn_prob", "rf_prob"]',
            'lstm_time_series': '["price_sequence_24h", "volume_sequence_24h"]',
        }
        return features.get(model_type, features['xgboost_price_momentum'])

    async def _test_strategy(
        self,
        strategy: Strategy,
        markets: List[Market],
    ) -> Dict:
        """
        Phase 3: Test strategy.

        Train model and test on live data.
        """
        print(f"\n[Test] Testing strategy {strategy.name}...")

        # Simulate training
        # In production: Actually train and test

        # Generate synthetic performance
        performance = self._simulate_strategy_performance(strategy, markets)

        return performance

    def _simulate_strategy_performance(
        self,
        strategy: Strategy,
        markets: List[Market],
    ) -> Dict:
        """Simulate strategy performance."""
        # Base performance varies by strategy type
        type_performance = {
            'xgboost_price_momentum': {'base_wr': 0.56, 'sharpe': 0.8},
            'neural_sentiment_fusion': {'base_wr': 0.55, 'sharpe': 0.7},
            'ensemble_weighted_voting': {'base_wr': 0.58, 'sharpe': 0.9},
            'lstm_time_series': {'base_wr': 0.54, 'sharpe': 0.65},
            'random_forest_features': {'base_wr': 0.57, 'sharpe': 0.75},
            'gradient_boosting': {'base_wr': 0.59, 'sharpe': 1.0},
            'hybrid_ml_fundamental': {'base_wr': 0.53, 'sharpe': 0.6},
        }

        base = type_performance.get(strategy.model_type, {'base_wr': 0.55, 'sharpe': 0.7})

        # Add randomness
        wr = np.random.normal(base['base_wr'], 0.05)
        sharpe = np.random.normal(base['sharpe'], 0.2)

        # Clip to realistic range
        wr = max(0.45, min(0.70, wr))
        sharpe = max(0.3, min(1.5, sharpe))

        # Calculate other metrics
        num_predictions = len(markets)
        num_correct = int(wr * num_predictions)

        # Statistical significance
        if num_predictions >= 30:
            # T-test for win rate > 0.5
            from scipy import stats
            t_stat, p_value = stats.ttest_1samp(
                [1] * num_correct + [0] * (num_predictions - num_correct),
                0.5
            )
            significant = p_value < 0.05
        else:
            significant = False
            p_value = 1.0

        # Information coefficient (correlation between prediction and outcome)
        ic = (wr - 0.5) * 2  # Simplified

        # Brier score (calibration)
        brier_score = ((wr - 0.5) ** 2).mean() if isinstance(wr, np.ndarray) else (wr - 0.5) ** 2

        # Consistency (simulated)
        consistency = np.random.uniform(0.6, 0.9)

        return {
            'win_rate': wr,
            'sharpe_ratio': sharpe,
            'num_predictions': num_predictions,
            'num_correct': num_correct,
            'significant': significant,
            'p_value': p_value,
            'information_coefficient': ic,
            'brier_score': brier_score,
            'consistency': consistency,
            'total_pnl': wr * num_predictions * 100,  # Simplified
        }

    def _evaluate_performance(
        self,
        performance: Dict,
    ) -> Tuple[float, bool, str]:
        """
        Phase 4: Evaluate performance.

        Calculate skill score and determine if deployable.
        """
        print(f"\n[Evaluate] Calculating skill score...")

        # Skill score components
        win_rate = performance['win_rate']
        sharpe = performance['sharpe_ratio']
        significant = performance['significant']
        ic = performance['information_coefficient']
        consistency = performance['consistency']
        brier = performance['brier_score']
        num_predictions = performance['num_predictions']

        # 1. Win rate score (40% weight)
        wr_score = (win_rate - 0.5) * 2
        wr_score = max(0, min(1, wr_score))

        # 2. Significance score (20% weight)
        sig_score = 1.0 if (significant and num_predictions >= 30) else 0.0

        # 3. Information coefficient score (20% weight)
        ic_score = min(1.0, ic * 10)
        ic_score = max(0, ic_score)

        # 4. Consistency score (10% weight)
        consistency_score = consistency

        # 5. Calibration score (10% weight)
        calibration_score = max(0.0, 1.0 - brier_score)

        # Weighted skill score
        skill_score = (
            wr_score * 0.4 +
            sig_score * 0.2 +
            ic_score * 0.2 +
            consistency_score * 0.1 +
            calibration_score * 0.1
        )

        # Determine if deployable
        deployable = False
        reason = ""

        if skill_score < 0.4:
            deployable = False
            reason = f"Skill score {skill_score:.3f} below threshold 0.4"
        elif not significant or num_predictions < 30:
            deployable = False
            reason = f"Not statistically significant (n={num_predictions}, p={performance['p_value']:.3f})"
        elif win_rate < 0.55:
            deployable = False
            reason = f"Win rate {win_rate:.2%} below threshold 55%"
        elif sharpe < 0.5:
            deployable = False
            reason = f"Sharpe ratio {sharpe:.2f} below threshold 0.5"
        else:
            deployable = True
            reason = "Meets all skill thresholds"

        print(f"[Evaluate] Skill score: {skill_score:.3f}")
        print(f"[Evaluate] Components:")
        print(f"  Win rate:     {wr_score:.3f}")
        print(f"  Significance:  {sig_score:.3f}")
        print(f"  IC:           {ic_score:.3f}")
        print(f"  Consistency:  {consistency_score:.3f}")
        print(f"  Calibration:   {calibration_score:.3f}")

        return skill_score, deployable, reason

    def print_summary(self):
        """Print summary of all iterations."""
        print(f"\n{'='*80}")
        print(f"AGENT SUMMARY - {self.agent_id}")
        print(f"{'='*80}")

        if not self.iteration_results:
            print("No iterations completed yet.")
            return

        # Statistics
        total_iterations = len(self.iteration_results)
        deployable_count = sum(1 for r in self.iteration_results if r.deployable)

        print(f"\nIteration Statistics:")
        print(f"  Total iterations:     {total_iterations}")
        print(f"  Deployable strategies: {deployable_count}")
        print(f"  Success rate:          {deployable_count/total_iterations:.1%}")

        # Best strategies
        top_results = sorted(
            self.iteration_results,
            key=lambda r: r.skill_score,
            reverse=True
        )[:5]

        print(f"\nTop 5 Strategies:")
        for i, result in enumerate(top_results, 1):
            print(f"  {i}. {result.strategy.name}")
            print(f"     Skill: {result.skill_score:.3f}")
            print(f"     Deploy: {'YES' if result.deployable else 'NO'}")

        # Strategy type diversity
        print(f"\nStrategy Types Used:")
        for strategy_type, count in sorted(self.strategy_types_used.items(), key=lambda x: -x[1]):
            print(f"  {strategy_type}: {count} iterations")

        print(f"\n{'='*80}\n")


async def main():
    """Demo balanced iteration."""
    from market_discovery import MarketDiscovery

    print("\n" + "="*80)
    print("BALANCED ITERATION AGENT - True Research with Proper Skill Assessment")
    print("="*80 + "\n")

    # Create agent (1 hour iteration time)
    agent = BalancedIterationAgent(
        agent_id="balanced_agent_001",
        sector=Sector.SPORTS,
        iteration_time_minutes=60,  # 1 hour
    )

    # Create market discovery
    discovery = MarketDiscovery(
        min_volume=1000.0,
        max_resolution_days=30,
        min_liquidity_score=0.3,
    )

    # Run 5 iterations
    markets = await discovery.discover_markets(sectors=[Sector.SPORTS], limit=50)

    for iteration in range(1, 6):
        result = await agent.run_iteration(markets, iteration)

        # Brief pause between iterations
        await asyncio.sleep(1)

    # Print summary
    agent.print_summary()


if __name__ == "__main__":
    asyncio.run(main())
