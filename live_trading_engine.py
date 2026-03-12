#!/usr/bin/env python3
"""
Live Trading Engine - Trade on live prediction markets.

Make predictions, track resolutions, validate on actual outcomes.
No 90-day backtesting - validate on live markets that resolve in days.
"""

import asyncio
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import pickle
from collections import defaultdict

from market_discovery import Market, MarketDiscovery, Sector


class Side(Enum):
    """Trade side."""
    YES = "yes"
    NO = "no"


@dataclass
class Trade:
    """A trade on a prediction market."""
    trade_id: str
    market_id: str
    market_title: str
    sector: Sector
    side: Side
    yes_odds: float
    no_odds: float
    position_size: float
    entry_time: datetime
    resolution_time: datetime
    internal_probability: float
    market_probability: float
    deviation: float
    confidence: float
    status: str = "open"  # open, resolved, failed
    outcome: Optional[bool] = None  # True = YES won, False = NO won
    pnl: Optional[float] = None
    realized_return: Optional[float] = None


@dataclass
class TradingMetrics:
    """Performance metrics for live trading."""
    total_trades: int = 0
    resolved_trades: int = 0
    pending_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    total_invested: float = 0.0
    win_rate: float = 0.0
    average_return: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0

    # Sector-specific
    sector_pnl: Dict[str, float] = field(default_factory=dict)
    sector_win_rate: Dict[str, float] = field(default_factory=dict)
    sector_trades: Dict[str, int] = field(default_factory=dict)


class LiveTradingEngine:
    """
    Live trading engine for prediction markets.

    Validates on live markets that resolve in hours/days, not months.
    """

    def __init__(
        self,
        agent_id: str,
        initial_capital: float = 10000,
        max_position_size: float = 500,  # $500 per market max
        min_deviation: float = 0.05,  # 5% deviation to trade
        max_exposure_per_sector: float = 5000,  # $5,000 per sector
        max_total_exposure: float = 20000,  # $20,000 total
    ):
        self.agent_id = agent_id
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.max_position_size = max_position_size
        self.min_deviation = min_deviation
        self.max_exposure_per_sector = max_exposure_per_sector
        self.max_total_exposure = max_total_exposure

        # Trade tracking
        self.trades: List[Trade] = []
        self.open_positions: Dict[str, Trade] = {}  # market_id -> Trade

        # Performance tracking
        self.equity_curve: List[Tuple[datetime, float]] = [(datetime.now(), initial_capital)]
        self.peak_capital: float = initial_capital
        self.max_drawdown: float = 0.0

        # Sector exposure
        self.sector_exposure: Dict[Sector, float] = defaultdict(float)

    async def discover_and_trade(self, discovery: MarketDiscovery, limit: int = 100):
        """
        Discover markets and make trades on liquid opportunities.
        """
        print(f"\n[Trading] Discovering markets and identifying opportunities...")

        # Discover markets
        markets = await discovery.discover_markets(limit=limit)

        # Evaluate each market for trading opportunity
        for market in markets:
            try:
                await self.evaluate_market(market)
            except Exception as e:
                print(f"[Trading] Error evaluating {market.market_id}: {e}")
                continue

        print(f"\n[Trading] Evaluated {len(markets)} markets")
        print(f"[Trading] Open positions: {len(self.open_positions)}")

    async def evaluate_market(self, market: Market):
        """
        Evaluate a market for trading opportunity.

        Make prediction, check for mispricing, execute if opportunity exists.
        """
        # Check if already have position
        if market.market_id in self.open_positions:
            return

        # Check sector exposure
        sector_exposure = self.sector_exposure.get(market.sector, 0)
        if sector_exposure >= self.max_exposure_per_sector:
            return

        # Check total exposure
        total_exposure = sum(self.sector_exposure.values())
        if total_exposure >= self.max_total_exposure:
            return

        # Make prediction (simplified - in production use actual model)
        internal_prob = self._predict(market)

        # Check for mispricing
        trade_decision = self._check_opportunity(market, internal_prob)

        if trade_decision:
            await self.execute_trade(market, internal_prob, trade_decision)

    def _predict(self, market: Market) -> float:
        """
        Generate prediction for a market.

        In production: Use trained ML model.
        For demo: Use simple heuristic + randomness.
        """
        # Simple heuristic based on market features
        base_prob = 0.5

        # Adjust based on odds (sentiment indicator)
        if market.yes_odds > 0.6:
            base_prob -= 0.1  # Market may be overconfident
        elif market.yes_odds < 0.4:
            base_prob += 0.1  # Market may be underconfident

        # Add randomness (simulating model uncertainty)
        noise = np.random.normal(0, 0.1)
        final_prob = base_prob + noise

        # Clip to valid range
        final_prob = max(0.1, min(0.9, final_prob))

        return final_prob

    def _check_opportunity(
        self,
        market: Market,
        internal_prob: float,
    ) -> Optional[Dict]:
        """
        Check if there's a profitable trading opportunity.

        Returns trade decision if deviation exceeds threshold.
        """
        # Calculate deviation
        yes_deviation = abs(internal_prob - market.yes_odds)
        no_deviation = abs((1 - internal_prob) - market.no_odds)

        # Determine which side to trade
        if yes_deviation >= self.min_deviation and internal_prob > market.yes_odds:
            # Market undervalues YES
            return {
                'side': Side.YES,
                'market_prob': market.yes_odds,
                'deviation': yes_deviation,
                'expected_edge': internal_prob - market.yes_odds,
            }

        elif no_deviation >= self.min_deviation and (1 - internal_prob) > market.no_odds:
            # Market undervalues NO
            return {
                'side': Side.NO,
                'market_prob': market.no_odds,
                'deviation': no_deviation,
                'expected_edge': (1 - internal_prob) - market.no_odds,
            }

        return None

    async def execute_trade(
        self,
        market: Market,
        internal_prob: float,
        trade_decision: Dict,
    ):
        """Execute a trade on a market."""
        # Calculate position size based on confidence
        confidence = min(trade_decision['deviation'] / self.min_deviation, 2.0)
        position_size = min(
            self.max_position_size,
            self.capital * 0.05 * confidence,  # Max 5% of capital
        )

        # Create trade record
        trade = Trade(
            trade_id=f"{market.market_id}_{int(datetime.now().timestamp())}",
            market_id=market.market_id,
            market_title=market.title,
            sector=market.sector,
            side=trade_decision['side'],
            yes_odds=market.yes_odds,
            no_odds=market.no_odds,
            position_size=position_size,
            entry_time=datetime.now(),
            resolution_time=market.resolution_time,
            internal_probability=internal_prob,
            market_probability=trade_decision['market_prob'],
            deviation=trade_decision['deviation'],
            confidence=confidence,
        )

        # Record trade
        self.trades.append(trade)
        self.open_positions[market.market_id] = trade

        # Update sector exposure
        self.sector_exposure[market.sector] += position_size

        print(f"\n[Trade Executed]")
        print(f"  Market: {market.title}")
        print(f"  Side: {trade.side.value}")
        print(f"  Size: ${position_size:.2f}")
        print(f"  Odds: {trade.yes_odds:.2%} / {trade.no_odds:.2%}")
        print(f"  Internal: {internal_prob:.2%}")
        print(f"  Deviation: {trade.deviation:.2%}")
        print(f"  Expected Edge: {trade_decision['expected_edge']:.2%}")

    async def check_resolutions(self):
        """
        Check if any open positions have resolved.

        Simulate resolutions (in production, check actual market status).
        """
        print(f"\n[Resolutions] Checking {len(self.open_positions)} open positions...")

        # For demo: Simulate some resolutions
        # In production: Query market API for actual resolutions

        markets_to_close = []

        for market_id, trade in list(self.open_positions.items()):
            # Simulate resolution based on time
            time_until_resolution = (trade.resolution_time - datetime.now()).total_seconds() / 3600

            if time_until_resolution <= 0:
                # Simulate outcome (in production: get actual outcome)
                outcome = self._simulate_outcome(trade)
                markets_to_close.append((market_id, outcome))

        # Close resolved markets
        for market_id, outcome in markets_to_close:
            self.resolve_position(market_id, outcome)

        print(f"[Resolutions] Resolved {len(markets_to_close)} markets")
        print(f"[Resolutions] Still open: {len(self.open_positions)}")

    def _simulate_outcome(self, trade: Trade) -> bool:
        """
        Simulate market outcome (for demo).

        In production: Get actual outcome from market API.
        """
        # Simulate outcome based on market probability + noise
        # (More likely outcomes happen more often)
        if trade.side == Side.YES:
            outcome_prob = trade.market_probability
        else:
            outcome_prob = trade.no_odds

        # Add noise (markets aren't perfectly efficient)
        outcome_prob = outcome_prob + np.random.normal(0, 0.1)
        outcome_prob = max(0.01, min(0.99, outcome_prob))

        # Generate outcome
        return np.random.random() < outcome_prob

    def resolve_position(self, market_id: str, outcome: bool):
        """
        Resolve a position and calculate PnL.

        Args:
            market_id: Market identifier
            outcome: True if YES won, False if NO won
        """
        if market_id not in self.open_positions:
            return

        trade = self.open_positions[market_id]

        # Determine if trade won
        won = (trade.side == Side.YES and outcome) or (trade.side == Side.NO and not outcome)

        # Calculate PnL
        if won:
            # Calculate winnings based on odds
            if trade.side == Side.YES:
                odds = trade.yes_odds
            else:
                odds = trade.no_odds

            # Return = position_size * (1/odds)
            # PnL = return - position_size
            return_amount = trade.position_size * (1.0 / odds)
            pnl = return_amount - trade.position_size
        else:
            pnl = -trade.position_size  # Lost the position size

        realized_return = pnl / trade.position_size

        # Update trade
        trade.outcome = outcome
        trade.pnl = pnl
        trade.realized_return = realized_return
        trade.status = "resolved"

        # Update capital
        self.capital += pnl

        # Update equity curve
        self.equity_curve.append((datetime.now(), self.capital))

        # Update drawdown
        self.peak_capital = max(self.peak_capital, self.capital)
        self.max_drawdown = max(self.max_drawdown, (self.peak_capital - self.capital) / self.peak_capital)

        # Remove from open positions
        del self.open_positions[market_id]
        self.sector_exposure[trade.sector] -= trade.position_size

        print(f"\n[Position Resolved]")
        print(f"  Market: {trade.market_title}")
        print(f"  Side: {trade.side.value}")
        print(f"  Outcome: {'YES' if outcome else 'NO'}")
        print(f"  PnL: ${pnl:.2f}")
        print(f"  Return: {realized_return:.2%}")
        print(f"  Capital: ${self.capital:.2f}")

    def calculate_metrics(self) -> TradingMetrics:
        """Calculate current trading metrics."""
        resolved_trades = [t for t in self.trades if t.status == "resolved"]

        if not resolved_trades:
            return TradingMetrics()

        # Basic metrics
        total_pnl = sum(t.pnl for t in resolved_trades)
        winning_trades = len([t for t in resolved_trades if t.pnl > 0])
        losing_trades = len(resolved_trades) - winning_trades
        win_rate = winning_trades / len(resolved_trades)

        total_invested = sum(t.position_size for t in resolved_trades)
        average_return = total_pnl / total_invested if total_invested > 0 else 0

        # Sharpe ratio
        returns = [t.realized_return for t in resolved_trades]
        if returns and np.std(returns) > 0:
            sharpe = np.mean(returns) / np.std(returns)
        else:
            sharpe = 0.0

        # Sector-specific
        sector_pnl = defaultdict(float)
        sector_win_rate = defaultdict(list)
        sector_trades = defaultdict(int)

        for trade in resolved_trades:
            sector = trade.sector.value
            sector_pnl[sector] += trade.pnl
            sector_trades[sector] += 1
            sector_win_rate[sector].append(1 if trade.pnl > 0 else 0)

        sector_win_rate_final = {
            sector: sum(wins) / len(wins)
            for sector, wins in sector_win_rate.items()
        }

        return TradingMetrics(
            total_trades=len(self.trades),
            resolved_trades=len(resolved_trades),
            pending_trades=len(self.open_positions),
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            total_pnl=total_pnl,
            total_invested=total_invested,
            win_rate=win_rate,
            average_return=average_return,
            max_drawdown=self.max_drawdown,
            sharpe_ratio=sharpe,
            sector_pnl=dict(sector_pnl),
            sector_win_rate=sector_win_rate_final,
            sector_trades=dict(sector_trades),
        )

    def print_status(self):
        """Print current trading status."""
        metrics = self.calculate_metrics()

        print(f"\n{'='*80}")
        print(f"LIVE TRADING STATUS - {self.agent_id}")
        print(f"{'='*80}")

        print(f"\nPortfolio:")
        print(f"  Capital:           ${self.capital:.2f}")
        print(f"  Initial Capital:   ${self.initial_capital:.2f}")
        print(f"  Total PnL:        ${metrics.total_pnl:.2f}")
        print(f"  Return:           {metrics.total_pnl / self.initial_capital:.2%}")
        print(f"  Max Drawdown:      {metrics.max_drawdown:.2%}")

        print(f"\nTrading Statistics:")
        print(f"  Total Trades:      {metrics.total_trades}")
        print(f"  Resolved Trades:   {metrics.resolved_trades}")
        print(f"  Pending Trades:    {metrics.pending_trades}")
        print(f"  Winning Trades:   {metrics.winning_trades}")
        print(f"  Losing Trades:    {metrics.losing_trades}")
        print(f"  Win Rate:         {metrics.win_rate:.2%}")
        print(f"  Avg Return:        {metrics.average_return:.2%}")
        print(f"  Sharpe Ratio:     {metrics.sharpe_ratio:.2f}")

        if metrics.sector_pnl:
            print(f"\nSector Performance:")
            for sector, pnl in sorted(metrics.sector_pnl.items(), key=lambda x: x[1], reverse=True):
                win_rate = metrics.sector_win_rate.get(sector, 0)
                trades = metrics.sector_trades.get(sector, 0)
                print(f"  {sector.capitalize():15s}: PnL ${pnl:7.2f}  |  WR {win_rate:.2%}  |  {trades} trades")

        # Check if we have enough data for validation
        if metrics.resolved_trades >= 30:
            print(f"\n✓ Sufficient data for statistical validation ({metrics.resolved_trades} trades)")
        else:
            print(f"\n⚠ Need {30 - metrics.resolved_trades} more resolved trades for validation")

        print(f"\n{'='*80}\n")

    async def run_continuous(
        self,
        discovery: MarketDiscovery,
        check_interval_hours: float = 1.0,
    ):
        """
        Run continuous trading loop.

        Discover markets, trade, check resolutions.
        """
        print(f"\n{'='*80}")
        print(f"CONTINUOUS LIVE TRADING")
        print(f"{'='*80}")

        iteration = 0
        while True:
            print(f"\n{'='*80}")
            print(f"Iteration {iteration + 1}")
            print(f"{'='*80}")

            # Discover and trade
            await self.discover_and_trade(discovery, limit=50)

            # Check resolutions
            await self.check_resolutions()

            # Print status
            self.print_status()

            # Save state
            self._save_state()

            # Wait for next iteration
            print(f"Waiting {check_interval_hours} hours until next check...")
            await asyncio.sleep(check_interval_hours * 3600)

            iteration += 1

    def _save_state(self):
        """Save trading state to disk."""
        state = {
            'agent_id': self.agent_id,
            'capital': self.capital,
            'trades': [
                {
                    'trade_id': t.trade_id,
                    'market_id': t.market_id,
                    'market_title': t.market_title,
                    'sector': t.sector.value,
                    'side': t.side.value,
                    'position_size': t.position_size,
                    'entry_time': t.entry_time.isoformat(),
                    'resolution_time': t.resolution_time.isoformat(),
                    'internal_probability': t.internal_probability,
                    'market_probability': t.market_probability,
                    'deviation': t.deviation,
                    'status': t.status,
                    'outcome': t.outcome,
                    'pnl': t.pnl,
                    'realized_return': t.realized_return,
                }
                for t in self.trades
            ],
            'equity_curve': [(ts.isoformat(), cap) for ts, cap in self.equity_curve],
            'max_drawdown': self.max_drawdown,
            'sector_exposure': {k.value: v for k, v in self.sector_exposure.items()},
        }

        filename = f"{self.agent_id}_trading_state.json"
        with open(filename, 'w') as f:
            json.dump(state, f, indent=2, default=str)

        print(f"[Saved] Trading state to {filename}")


async def main():
    """Demo live trading."""
    print("\n" + "="*80)
    print("LIVE TRADING ENGINE - Trade on Prediction Markets")
    print("="*80 + "\n")

    # Initialize market discovery
    discovery = MarketDiscovery(
        min_volume=1000.0,
        max_resolution_days=30,
        min_liquidity_score=0.3,
    )

    # Initialize trading engine
    trader = LiveTradingEngine(
        agent_id="demo_trader",
        initial_capital=10000,
        max_position_size=500,
        min_deviation=0.05,
    )

    # Run trading cycle
    print("Running single trading cycle...\n")

    # Discover and trade
    await trader.discover_and_trade(discovery, limit=50)

    # Check resolutions (simulate some)
    await trader.check_resolutions()

    # Print status
    trader.print_status()

    # Simulate time passing and more resolutions
    print("\nSimulating time passing (24 hours)...\n")
    await asyncio.sleep(1)

    # Check more resolutions
    await trader.check_resolutions()

    # Print final status
    trader.print_status()


if __name__ == "__main__":
    asyncio.run(main())
