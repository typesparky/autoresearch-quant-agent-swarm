#!/usr/bin/env python3
"""
Live Trading Agent - Sector-based autonomous trader.

Each agent specializes in a sector and trades on live prediction markets.
Validates on live market resolutions (not 90-day backtests).
"""

import asyncio
import os
from datetime import datetime
from typing import List, Dict, Optional
import json

from market_discovery import Market, MarketDiscovery, Sector
from live_trading_engine import LiveTradingEngine


class LiveTradingAgent:
    """
    Sector-based autonomous trading agent.

    Specializes in one or more sectors and validates on live markets.
    """

    def __init__(
        self,
        agent_id: str,
        sectors: List[Sector],
        initial_capital: float = 10000,
        max_position_size: float = 500,
        min_deviation: float = 0.05,
    ):
        self.agent_id = agent_id
        self.sectors = sectors
        self.initial_capital = initial_capital

        # Initialize market discovery
        self.discovery = MarketDiscovery(
            min_volume=1000.0,
            max_resolution_days=30,
            min_liquidity_score=0.3,
        )

        # Initialize trading engine
        self.trader = LiveTradingEngine(
            agent_id=agent_id,
            initial_capital=initial_capital,
            max_position_size=max_position_size,
            min_deviation=min_deviation,
        )

        # Validation criteria
        self.min_resolved_trades = 30
        self.min_win_rate = 0.55
        self.min_sharpe = 0.5

    async def run_cycle(self):
        """
        Run one trading cycle.

        1. Discover markets in assigned sectors
        2. Make predictions and execute trades
        3. Check for resolutions
        4. Validate performance if enough data
        """
        print(f"\n{'='*80}")
        print(f"AGENT CYCLE - {self.agent_id}")
        print(f"Sectors: {', '.join(s.value for s in self.sectors)}")
        print(f"{'='*80}\n")

        # Step 1: Discover markets in assigned sectors
        print("[Step 1] Discovering markets in assigned sectors...")
        markets = await self.discovery.discover_markets(
            sectors=self.sectors,
            limit=100,
        )

        # Step 2: Evaluate and trade
        print(f"\n[Step 2] Evaluating {len(markets)} markets for opportunities...")

        for market in markets:
            await self.trader.evaluate_market(market)

        print(f"[Step 2] Open positions: {len(self.trader.open_positions)}")

        # Step 3: Check resolutions
        print(f"\n[Step 3] Checking for market resolutions...")
        await self.trader.check_resolutions()

        # Step 4: Validate if enough data
        print(f"\n[Step 4] Validating performance...")
        metrics = self.trader.calculate_metrics()

        if metrics.resolved_trades >= self.min_resolved_trades:
            is_valid = self._validate(metrics)
            print(f"{'='*80}")
            print(f"VALIDATION RESULT: {'✓ VALID' if is_valid else '✗ INVALID'}")
            print(f"{'='*80}\n")

            return is_valid
        else:
            print(f"⚠ Need {self.min_resolved_trades - metrics.resolved_trades} more resolved trades")
            return None

    def _validate(self, metrics) -> bool:
        """Validate performance against criteria."""
        print(f"\nValidation Criteria:")
        print(f"  Minimum resolved trades: {self.min_resolved_trades} (actual: {metrics.resolved_trades})")
        print(f"  Minimum win rate: {self.min_win_rate:.0%} (actual: {metrics.win_rate:.2%})")
        print(f"  Minimum Sharpe: {self.min_sharpe} (actual: {metrics.sharpe_ratio:.2f})")

        # Check criteria
        passed = (
            metrics.resolved_trades >= self.min_resolved_trades and
            metrics.win_rate >= self.min_win_rate and
            metrics.sharpe_ratio >= self.min_sharpe
        )

        return passed

    def print_summary(self):
        """Print agent summary."""
        metrics = self.trader.calculate_metrics()

        print(f"\n{'='*80}")
        print(f"AGENT SUMMARY - {self.agent_id}")
        print(f"{'='*80}")

        print(f"\nAgent Configuration:")
        print(f"  Sectors: {', '.join(s.value for s in self.sectors)}")
        print(f"  Initial Capital: ${self.initial_capital:.2f}")
        print(f"  Current Capital: ${metrics.total_pnl + self.initial_capital:.2f}")

        print(f"\nPerformance:")
        print(f"  Total PnL: ${metrics.total_pnl:.2f}")
        print(f"  Return: {metrics.total_pnl / self.initial_capital:.2%}")
        print(f"  Win Rate: {metrics.win_rate:.2%}")
        print(f"  Sharpe: {metrics.sharpe_ratio:.2f}")
        print(f"  Resolved Trades: {metrics.resolved_trades}")

        if metrics.sector_pnl:
            print(f"\nSector Performance:")
            for sector, pnl in sorted(metrics.sector_pnl.items(), key=lambda x: x[1], reverse=True):
                win_rate = metrics.sector_win_rate.get(sector, 0)
                trades = metrics.sector_trades.get(sector, 0)
                print(f"  {sector.capitalize():15s}: ${pnl:7.2f}  |  WR {win_rate:.2%}  |  {trades} trades")

        print(f"\n{'='*80}\n")

    async def run_continuous(self, check_interval_hours: float = 1.0):
        """
        Run agent continuously.

        Check markets, trade, validate in cycles.
        """
        print(f"\n{'='*80}")
        print(f"CONTINUOUS AGENT - {self.agent_id}")
        print(f"Sectors: {', '.join(s.value for s in self.sectors)}")
        print(f"Check interval: {check_interval_hours} hours")
        print(f"{'='*80}\n")

        iteration = 0
        consecutive_valid = 0
        consecutive_invalid = 0

        while True:
            iteration += 1

            try:
                # Run cycle
                validation_result = await self.run_cycle()

                if validation_result is True:
                    consecutive_valid += 1
                    consecutive_invalid = 0

                    if consecutive_valid >= 3:
                        print(f"\n✓✓✓ AGENT {self.agent_id} VALIDATED ({consecutive_valid} consecutive cycles)")
                        print("Ready to scale up deployment!\n")

                elif validation_result is False:
                    consecutive_invalid += 1
                    consecutive_valid = 0

                    if consecutive_invalid >= 3:
                        print(f"\n✗✗✗ AGENT {self.agent_id} INVALID ({consecutive_invalid} consecutive cycles)")
                        print("Need to adjust strategy!\n")

                # Print summary every 5 iterations
                if iteration % 5 == 0:
                    self.print_summary()

                # Save state
                self.trader._save_state()

                # Wait for next cycle
                print(f"Waiting {check_interval_hours} hours until next cycle...\n")
                await asyncio.sleep(check_interval_hours * 3600)

            except Exception as e:
                print(f"\n[ERROR] Cycle {iteration} failed: {e}")
                import traceback
                traceback.print_exc()

                # Wait and retry
                await asyncio.sleep(300)  # 5 minutes


async def main():
    """Demo live trading agent."""
    print("\n" + "="*80)
    print("LIVE TRADING AGENT - Sector-Based Autonomous Trader")
    print("="*80 + "\n")

    # Create sports agent
    sports_agent = LiveTradingAgent(
        agent_id="sports_agent_001",
        sectors=[Sector.SPORTS],
        initial_capital=10000,
        max_position_size=500,
        min_deviation=0.05,
    )

    # Run 3 cycles
    for i in range(3):
        print(f"\n{'='*80}")
        print(f"CYCLE {i+1}")
        print(f"{'='*80}\n")

        await sports_agent.run_cycle()

        # Simulate time passing between cycles
        if i < 2:
            print(f"\nSimulating 6 hours passing...\n")
            await asyncio.sleep(0.5)

    # Print final summary
    sports_agent.print_summary()


if __name__ == "__main__":
    asyncio.run(main())
