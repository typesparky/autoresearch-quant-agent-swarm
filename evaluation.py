#!/usr/bin/env python3
"""
Performance Evaluator

Evaluates model performance and decides if it's an improvement.
"""

from typing import Dict, Optional


class PerformanceEvaluator:
    """Evaluate model performance and improvement."""

    def __init__(
        self,
        min_sharpe: float = 0.5,
        min_win_rate: float = 0.5,
        max_drawdown: float = 0.2,
        improvement_threshold: float = 0.1,  # 10% improvement required
    ):
        self.min_sharpe = min_sharpe
        self.min_win_rate = min_win_rate
        self.max_drawdown = max_drawdown
        self.improvement_threshold = improvement_threshold

    def is_improvement(
        self,
        new_metrics: Dict,
        best_metrics: Dict,
    ) -> tuple[bool, str]:
        """
        Determine if new model is an improvement.

        Returns:
        - is_improvement: Whether to save
        - reason: Human-readable explanation
        """
        # Validate required metrics
        required_metrics = ["total_pnl", "sharpe_ratio", "win_rate", "max_drawdown"]
        for metric in required_metrics:
            if metric not in new_metrics:
                return False, f"missing_metric:{metric}"

        # Check minimum thresholds
        if new_metrics["sharpe_ratio"] < self.min_sharpe:
            return False, f"sharpe_below_threshold:{new_metrics['sharpe_ratio']:.2f}"

        if new_metrics["win_rate"] < self.min_win_rate:
            return False, f"win_rate_below_threshold:{new_metrics['win_rate']:.2%}"

        if new_metrics["max_drawdown"] > self.max_drawdown:
            return False, f"drawdown_exceeded:{new_metrics['max_drawdown']:.2%}"

        # If no best metrics yet, this is an improvement
        if not best_metrics:
            return True, "first_valid_model"

        # Compare to best
        new_sharpe = new_metrics["sharpe_ratio"]
        best_sharpe = best_metrics.get("sharpe_ratio", 0)

        new_pnl = new_metrics["total_pnl"]
        best_pnl = best_metrics.get("total_pnl", 0)

        # Check for significant improvement
        sharpe_improvement = (new_sharpe - best_sharpe) / (abs(best_sharpe) + 1e-8)

        # Prefer higher Sharpe with positive PnL
        if new_pnl > best_pnl and new_sharpe > best_sharpe:
            return True, f"improved_pnl_and_sharpe:{new_pnl:.2f},{new_sharpe:.2f}"

        # Accept if Sharpe improvement is significant
        if sharpe_improvement > self.improvement_threshold:
            return True, f"sharpe_improvement:{sharpe_improvement:.1%}"

        # Accept if Sharpe is similar but PnL is much higher
        if abs(new_sharpe - best_sharpe) < 0.1 and new_pnl > best_pnl * 1.2:
            return True, f"higher_pnl_similar_sharpe:{new_pnl:.2f}"

        return False, f"no_significant_improvement:sharpe={new_sharpe:.2f},pnl={new_pnl:.2f}"

    def calculate_ranking_score(self, metrics: Dict) -> float:
        """
        Calculate single ranking score from metrics.

        Higher is better. Balances Sharpe, PnL, and risk.
        """
        sharpe = metrics.get("sharpe_ratio", 0)
        pnl = metrics.get("total_pnl", 0)
        drawdown = metrics.get("max_drawdown", 1.0)
        win_rate = metrics.get("win_rate", 0.5)

        # Normalize components
        sharpe_score = max(0, sharpe)  # Higher is better
        pnl_score = max(0, pnl) / 1000  # Normalize by $1000
        drawdown_score = max(0, 1 - drawdown)  # Lower is better
        win_rate_score = win_rate  # Higher is better

        # Weighted combination
        total_score = (
            sharpe_score * 0.4 +
            pnl_score * 0.2 +
            drawdown_score * 0.2 +
            win_rate_score * 0.2
        )

        return total_score

    def print_metrics_report(self, metrics: Dict, label: str = "Model"):
        """Print formatted metrics report."""
        print(f"\n{'='*60}")
        print(f"{label} Performance Report")
        print(f"{'='*60}")
        print(f"Total PnL:        ${metrics.get('total_pnl', 0):.2f}")
        print(f"Sharpe Ratio:     {metrics.get('sharpe_ratio', 0):.2f}")
        print(f"Win Rate:         {metrics.get('win_rate', 0):.2%}")
        print(f"Max Drawdown:     {metrics.get('max_drawdown', 0):.2%}")
        print(f"Num Trades:       {metrics.get('num_trades', 0)}")
        print(f"Test Accuracy:    {metrics.get('test_accuracy', 0):.4f}")
        print(f"{'='*60}\n")
