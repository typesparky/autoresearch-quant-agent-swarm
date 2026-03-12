#!/usr/bin/env python3
"""
Multi-Objective Optimization for Quant Strategies.

Optimize across multiple conflicting objectives:
- Maximize profit
- Minimize volatility (lower drawdown)
- Maximize Sharpe ratio
- Minimize tail risk
- Maximize robustness (regime stability)
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class Objective(Enum):
    """Optimization objectives."""
    MAXIMIZE_PROFIT = "max_profit"
    MINIMIZE_VOLATILITY = "min_volatility"
    MAXIMIZE_SHARPE = "max_sharpe"
    MINIMIZE_DRAWDOWN = "min_drawdown"
    MAXIMIZE_WIN_RATE = "max_win_rate"
    MINIMIZE_TAIL_RISK = "min_tail_risk"
    MAXIMIZE_ROBUSTNESS = "max_robustness"


@dataclass
class ObjectiveWeights:
    """Weights for multi-objective optimization."""
    profit: float = 0.3
    volatility: float = 0.2
    sharpe: float = 0.25
    drawdown: float = 0.1
    win_rate: float = 0.05
    tail_risk: float = 0.05
    robustness: float = 0.05

    def normalize(self):
        """Ensure weights sum to 1."""
        total = sum([self.profit, self.volatility, self.sharpe,
                    self.drawdown, self.win_rate, self.tail_risk, self.robustness])
        if total > 0:
            self.profit /= total
            self.volatility /= total
            self.sharpe /= total
            self.drawdown /= total
            self.win_rate /= total
            self.tail_risk /= total
            self.robustness /= total


class MultiObjectiveOptimizer:
    """Multi-objective optimization for strategy selection."""

    def __init__(self, weights: Optional[ObjectiveWeights] = None):
        self.weights = weights or ObjectiveWeights()
        self.weights.normalize()

    def calculate_objective_scores(
        self,
        results: Dict,
    ) -> Dict[str, float]:
        """
        Calculate normalized scores for each objective.

        Returns:
            Dict mapping objective names to scores (0-1 range)
        """
        # Profit score (normalize by capital)
        initial_capital = results.get('initial_capital', 100000)
        total_pnl = results.get('total_pnl', 0)
        profit_score = min(1.0, max(0.0, (total_pnl / initial_capital) / 0.5))  # 50% return = 1.0

        # Volatility score (lower is better)
        volatility = results.get('volatility', 0)
        volatility_score = max(0.0, 1.0 - volatility / 0.5)  # 50% vol = 0 score

        # Sharpe score (normalize)
        sharpe = results.get('sharpe_ratio', 0)
        sharpe_score = min(1.0, max(0.0, sharpe / 3.0))  # Sharpe 3.0 = 1.0

        # Drawdown score (lower is better)
        drawdown = results.get('max_drawdown', 0)
        drawdown_score = max(0.0, 1.0 - drawdown / 0.5)  # 50% drawdown = 0 score

        # Win rate score
        win_rate = results.get('win_rate', 0.5)
        win_rate_score = min(1.0, max(0.0, (win_rate - 0.5) / 0.4))  # 90% win rate = 1.0

        # Tail risk score (CVaR)
        # Calculate 5th percentile of returns
        returns = [t.get('pnl', 0) for t in results.get('trades', [])]
        if returns:
            var_95 = np.percentile(returns, 5)
            cvar = np.mean([r for r in returns if r <= var_95])
            tail_risk_score = max(0.0, 1.0 + cvar / (initial_capital * 0.1))  # -10% CVaR = 0 score
        else:
            tail_risk_score = 0.5

        # Robustness score (regime stability)
        regime_results = results.get('regime_results', {})
        if regime_results.get('regime_pnl'):
            # Check if positive in all regimes
            all_positive = all(pnl > 0 for pnl in regime_results['regime_pnl'].values())
            if all_positive:
                robustness_score = 1.0
            else:
                # Score based on proportion of positive regimes
                positive_regimes = sum(1 for pnl in regime_results['regime_pnl'].values() if pnl > 0)
                robustness_score = positive_regimes / len(regime_results['regime_pnl'])
        else:
            robustness_score = 0.5

        return {
            'profit': profit_score,
            'volatility': volatility_score,
            'sharpe': sharpe_score,
            'drawdown': drawdown_score,
            'win_rate': win_rate_score,
            'tail_risk': tail_risk_score,
            'robustness': robustness_score,
        }

    def calculate_weighted_score(
        self,
        objective_scores: Dict[str, float],
    ) -> float:
        """
        Calculate weighted composite score.

        Higher is better.
        """
        weighted_sum = (
            objective_scores['profit'] * self.weights.profit +
            objective_scores['volatility'] * self.weights.volatility +
            objective_scores['sharpe'] * self.weights.sharpe +
            objective_scores['drawdown'] * self.weights.drawdown +
            objective_scores['win_rate'] * self.weights.win_rate +
            objective_scores['tail_risk'] * self.weights.tail_risk +
            objective_scores['robustness'] * self.weights.robustness
        )

        return weighted_sum

    def rank_strategies(
        self,
        strategies: List[Dict],
    ) -> List[Dict]:
        """
        Rank strategies by multi-objective score.

        Args:
            strategies: List of strategy result dicts

        Returns:
            Sorted list with ranking info added
        """
        ranked = []

        for i, strategy_results in enumerate(strategies):
            # Calculate objective scores
            objective_scores = self.calculate_objective_scores(strategy_results)

            # Calculate weighted score
            weighted_score = self.calculate_weighted_score(objective_scores)

            # Add ranking info
            ranked_strategy = strategy_results.copy()
            ranked_strategy['ranking'] = {
                'rank': None,  # Will be assigned after sorting
                'weighted_score': weighted_score,
                'objective_scores': objective_scores,
                'strategy_id': i,
            }

            ranked.append(ranked_strategy)

        # Sort by weighted score
        ranked.sort(key=lambda x: x['ranking']['weighted_score'], reverse=True)

        # Assign ranks
        for i, strategy in enumerate(ranked):
            strategy['ranking']['rank'] = i + 1

        return ranked

    def find_pareto_frontier(
        self,
        strategies: List[Dict],
    ) -> List[Dict]:
        """
        Find Pareto-optimal strategies (non-dominated).

        A strategy is Pareto-optimal if no other strategy is better
        in at least one objective without being worse in another.
        """
        if not strategies:
            return []

        # Calculate objective scores for all strategies
        scored_strategies = []
        for i, strategy in enumerate(strategies):
            objective_scores = self.calculate_objective_scores(strategy)
            scored_strategies.append({
                'id': i,
                'scores': objective_scores,
                'results': strategy,
            })

        pareto_frontier = []

        for candidate in scored_strategies:
            dominated = False

            for competitor in scored_strategies:
                if candidate['id'] == competitor['id']:
                    continue

                # Check if competitor dominates candidate
                # (better in at least one objective, not worse in any)
                better_in_any = False
                not_worse_in_all = True

                for obj, score in candidate['scores'].items():
                    if competitor['scores'][obj] > score:
                        better_in_any = True
                    elif competitor['scores'][obj] < score:
                        not_worse_in_all = False
                        break

                if better_in_any and not_worse_in_all:
                    dominated = True
                    break

            if not dominated:
                pareto_frontier.append(candidate['results'])

        return pareto_frontier

    def print_strategy_ranking(self, ranked_strategies: List[Dict]):
        """Print ranked strategies."""
        print(f"\n{'='*60}")
        print("STRATEGY RANKING")
        print(f"{'='*60}")

        weights_str = (
            f"Profit: {self.weights.profit:.2f}, "
            f"Vol: {self.weights.volatility:.2f}, "
            f"Sharpe: {self.weights.sharpe:.2f}, "
            f"DD: {self.weights.drawdown:.2f}, "
            f"WR: {self.weights.win_rate:.2f}, "
            f"Tail: {self.weights.tail_risk:.2f}, "
            f"Robust: {self.weights.robustness:.2f}"
        )
        print(f"\nObjective Weights: {weights_str}\n")

        for strategy in ranked_strategies[:10]:  # Top 10
            rank = strategy['ranking']['rank']
            score = strategy['ranking']['weighted_score']
            obj_scores = strategy['ranking']['objective_scores']

            print(f"\nRank {rank}: Score {score:.3f}")
            print(f"  PnL:            ${strategy.get('total_pnl', 0):.2f}")
            print(f"  Sharpe:         {strategy.get('sharpe_ratio', 0):.2f}")
            print(f"  Win Rate:       {strategy.get('win_rate', 0):.2%}")
            print(f"  Max Drawdown:   {strategy.get('max_drawdown', 0):.2%}")
            print(f"  Objective Scores:")
            print(f"    Profit:      {obj_scores['profit']:.3f}")
            print(f"    Volatility:  {obj_scores['volatility']:.3f}")
            print(f"    Sharpe:      {obj_scores['sharpe']:.3f}")
            print(f"    Drawdown:    {obj_scores['drawdown']:.3f}")
            print(f"    Win Rate:    {obj_scores['win_rate']:.3f}")
            print(f"    Tail Risk:   {obj_scores['tail_risk']:.3f}")
            print(f"    Robustness:  {obj_scores['robustness']:.3f}")

        print(f"\n{'='*60}\n")

    def print_pareto_frontier(self, pareto_strategies: List[Dict]):
        """Print Pareto-optimal strategies."""
        print(f"\n{'='*60}")
        print(f"PARETO FRONTIER ({len(pareto_strategies)} strategies)")
        print(f"{'='*60}\n")

        for i, strategy in enumerate(pareto_strategies):
            obj_scores = self.calculate_objective_scores(strategy)

            print(f"\nStrategy {i+1}:")
            print(f"  PnL:          ${strategy.get('total_pnl', 0):.2f}")
            print(f"  Sharpe:       {strategy.get('sharpe_ratio', 0):.2f}")
            print(f"  Win Rate:     {strategy.get('win_rate', 0):.2%}")
            print(f"  Max Drawdown: {strategy.get('max_drawdown', 0):.2%}")
            print(f"  Objectives:")
            print(f"    Profit:     {obj_scores['profit']:.3f}")
            print(f"    Volatility: {obj_scores['volatility']:.3f}")
            print(f"    Sharpe:     {obj_scores['sharpe']:.3f}")
            print(f"    Drawdown:   {obj_scores['drawdown']:.3f}")
            print(f"    Robustness: {obj_scores['robustness']:.3f}")

        print(f"\n{'='*60}\n")


# Weight profiles for different risk preferences
WEIGHT_PROFILES = {
    'aggressive': ObjectiveWeights(
        profit=0.5,
        volatility=0.1,
        sharpe=0.2,
        drawdown=0.05,
        win_rate=0.05,
        tail_risk=0.05,
        robustness=0.05,
    ),
    'balanced': ObjectiveWeights(
        profit=0.3,
        volatility=0.2,
        sharpe=0.25,
        drawdown=0.1,
        win_rate=0.05,
        tail_risk=0.05,
        robustness=0.05,
    ),
    'conservative': ObjectiveWeights(
        profit=0.15,
        volatility=0.3,
        sharpe=0.3,
        drawdown=0.2,
        win_rate=0.03,
        tail_risk=0.01,
        robustness=0.01,
    ),
}


def main():
    """Example multi-objective optimization."""
    print("\n" + "="*60)
    print("Multi-Objective Optimization")
    print("="*60 + "\n")

    # Generate sample strategies
    strategies = []
    np.random.seed(42)

    for i in range(20):
        # Generate random but realistic performance metrics
        sharpe = np.random.normal(1.5, 0.5)
        sharpe = max(0.5, min(3.0, sharpe))

        win_rate = np.random.normal(0.55, 0.05)
        win_rate = max(0.5, min(0.7, win_rate))

        max_drawdown = np.random.normal(0.15, 0.05)
        max_drawdown = max(0.05, min(0.3, max_drawdown))

        total_pnl = np.random.normal(20000, 10000)

        strategies.append({
            'total_pnl': total_pnl,
            'sharpe_ratio': sharpe,
            'win_rate': win_rate,
            'max_drawdown': max_drawdown,
            'total_trades': np.random.randint(50, 200),
            'initial_capital': 100000,
            'regime_results': {
                'regime_pnl': {
                    'bullish': np.random.uniform(5000, 15000),
                    'bearish': np.random.uniform(-2000, 10000),
                    'sideways': np.random.uniform(0, 8000),
                },
            },
        })

    # Create optimizer
    optimizer = MultiObjectiveOptimizer(weights=WEIGHT_PROFILES['balanced'])

    # Rank strategies
    ranked = optimizer.rank_strategies(strategies)
    optimizer.print_strategy_ranking(ranked)

    # Find Pareto frontier
    pareto = optimizer.find_pareto_frontier(strategies)
    optimizer.print_pareto_frontier(pareto)

    print(f"Top strategy:")
    print(f"  Weighted Score: {ranked[0]['ranking']['weighted_score']:.3f}")
    print(f"  PnL: ${ranked[0]['total_pnl']:.2f}")
    print(f"  Sharpe: {ranked[0]['sharpe_ratio']:.2f}")


if __name__ == "__main__":
    main()
