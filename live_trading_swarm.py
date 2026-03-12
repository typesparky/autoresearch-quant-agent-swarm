#!/usr/bin/env python3
"""
Live Trading Swarm - Multiple sector-based agents trading in parallel.

Each agent specializes in a sector, trading on live markets.
Coordinate via shared metrics and consensus.
"""

import asyncio
from datetime import datetime
from typing import List, Dict
import json
import os

from market_discovery import Sector
from live_trading_agent import LiveTradingAgent


class LiveTradingSwarm:
    """
    Swarm of sector-based trading agents.

    Each agent specializes in a sector and validates on live markets.
    Swarm coordinates via shared metrics.
    """

    def __init__(
        self,
        initial_capital_per_agent: float = 10000,
        max_position_size: float = 500,
        min_deviation: float = 0.05,
    ):
        self.initial_capital_per_agent = initial_capital_per_agent
        self.max_position_size = max_position_size
        self.min_deviation = min_deviation

        # Create agents for each sector
        self.agents: List[LiveTradingAgent] = []

        # Define sector assignments
        sector_assignments = [
            {
                'agent_id': 'sports_agent_001',
                'sectors': [Sector.SPORTS],
            },
            {
                'agent_id': 'sports_agent_002',
                'sectors': [Sector.SPORTS],
            },
            {
                'agent_id': 'politics_agent',
                'sectors': [Sector.POLITICS],
            },
            {
                'agent_id': 'crypto_agent_001',
                'sectors': [Sector.CRYPTO],
            },
            {
                'agent_id': 'crypto_agent_002',
                'sectors': [Sector.CRYPTO],
            },
            {
                'agent_id': 'entertainment_agent',
                'sectors': [Sector.ENTERTAINMENT],
            },
            {
                'agent_id': 'weather_agent',
                'sectors': [Sector.WEATHER],
            },
        ]

        # Initialize agents
        for assignment in sector_assignments:
            agent = LiveTradingAgent(
                agent_id=assignment['agent_id'],
                sectors=assignment['sectors'],
                initial_capital=initial_capital_per_agent,
                max_position_size=max_position_size,
                min_deviation=min_deviation,
            )
            self.agents.append(agent)

        print(f"Initialized {len(self.agents)} agents")

    async def run_cycle(self):
        """
        Run one cycle for all agents.

        All agents discover markets, trade, and check resolutions in parallel.
        """
        print(f"\n{'='*80}")
        print(f"SWARM CYCLE")
        print(f"{'='*80}\n")

        # Run all agents in parallel
        tasks = [agent.run_cycle() for agent in self.agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check results
        for i, (agent, result) in enumerate(zip(self.agents, results)):
            if isinstance(result, Exception):
                print(f"[Error] {agent.agent_id} failed: {result}")
            else:
                print(f"[Success] {agent.agent_id} completed")

        # Print swarm summary
        self.print_swarm_summary()

        return results

    def print_swarm_summary(self):
        """Print summary of all agents."""
        print(f"\n{'='*80}")
        print(f"SWARM SUMMARY")
        print(f"{'='*80}\n")

        # Aggregate metrics
        total_capital = 0
        total_pnl = 0
        total_resolved = 0
        total_pending = 0
        sector_metrics = {}

        for agent in self.agents:
            metrics = agent.trader.calculate_metrics()

            total_capital += agent.initial_capital
            total_pnl += metrics.total_pnl
            total_resolved += metrics.resolved_trades
            total_pending += metrics.pending_trades

            # Aggregate by sector
            for sector in agent.sectors:
                sector_name = sector.value
                if sector_name not in sector_metrics:
                    sector_metrics[sector_name] = {
                        'pnl': 0,
                        'trades': 0,
                        'win_rate': [],
                    }

                if sector_name in metrics.sector_pnl:
                    sector_metrics[sector_name]['pnl'] += metrics.sector_pnl[sector_name]
                    sector_metrics[sector_name]['trades'] += metrics.sector_trades.get(sector_name, 0)
                    if sector_name in metrics.sector_win_rate:
                        sector_metrics[sector_name]['win_rate'].append(
                            metrics.sector_win_rate[sector_name]
                        )

        # Calculate aggregate metrics
        overall_return = total_pnl / total_capital if total_capital > 0 else 0

        # Calculate win rates
        sector_win_rates = {
            sector: sum(wins) / len(wins) if wins else 0
            for sector, wins in {
                k: v['win_rate'] for k, v in sector_metrics.items()
            }.items()
        }

        print(f"Overall Performance:")
        print(f"  Total Capital: ${total_capital:.2f}")
        print(f"  Total PnL: ${total_pnl:.2f}")
        print(f"  Return: {overall_return:.2%}")
        print(f"  Total Resolved: {total_resolved}")
        print(f"  Total Pending: {total_pending}")

        print(f"\nAgent Performance:")
        for agent in sorted(self.agents, key=lambda a: a.trader.calculate_metrics().total_pnl, reverse=True):
            metrics = agent.trader.calculate_metrics()
            sector_str = ', '.join(s.value for s in agent.sectors)

            print(f"\n  {agent.agent_id}:")
            print(f"    Sectors: {sector_str}")
            print(f"    PnL: ${metrics.total_pnl:7.2f}")
            print(f"    Return: {metrics.total_pnl / agent.initial_capital:.2%}")
            print(f"    Win Rate: {metrics.win_rate:.2%}")
            print(f"    Resolved: {metrics.resolved_trades}")

        print(f"\nSector Performance:")
        for sector, metrics_data in sorted(sector_metrics.items(), key=lambda x: x[1]['pnl'], reverse=True):
            win_rate = sector_win_rates.get(sector, 0)
            print(f"  {sector.capitalize():15s}: ${metrics_data['pnl']:7.2f}  |  WR {win_rate:.2%}  |  {metrics_data['trades']} trades")

        print(f"\n{'='*80}\n")

    def get_validated_agents(self) -> List[LiveTradingAgent]:
        """Get agents that have met validation criteria."""
        validated = []

        for agent in self.agents:
            metrics = agent.trader.calculate_metrics()

            if (
                metrics.resolved_trades >= 30 and
                metrics.win_rate >= 0.55 and
                metrics.sharpe_ratio >= 0.5
            ):
                validated.append(agent)

        return validated

    async def run_continuous(self, check_interval_hours: float = 1.0):
        """
        Run swarm continuously.

        All agents run in parallel, with periodic summaries.
        """
        print(f"\n{'='*80}")
        print(f"CONTINUOUS SWARM TRADING")
        print(f"Agents: {len(self.agents)}")
        print(f"Check interval: {check_interval_hours} hours")
        print(f"{'='*80}\n")

        iteration = 0

        while True:
            iteration += 1

            print(f"\n{'='*80}")
            print(f"SWARM ITERATION {iteration}")
            print(f"{'='*80}\n")

            # Run cycle
            await self.run_cycle()

            # Check validated agents
            validated = self.get_validated_agents()

            if validated:
                print(f"\n✓ VALIDATED AGENTS ({len(validated)}):")
                for agent in validated:
                    metrics = agent.trader.calculate_metrics()
                    print(f"  - {agent.agent_id}: {metrics.total_pnl / agent.initial_capital:.2%} return, {metrics.win_rate:.2%} WR")
            else:
                print(f"\n⚠ No agents validated yet")

            # Save swarm state
            self._save_swarm_state()

            # Wait for next cycle
            print(f"\nWaiting {check_interval_hours} hours until next cycle...\n")
            await asyncio.sleep(check_interval_hours * 3600)

    def _save_swarm_state(self):
        """Save swarm state to disk."""
        state = {
            'timestamp': datetime.now().isoformat(),
            'num_agents': len(self.agents),
            'agents': [
                {
                    'agent_id': agent.agent_id,
                    'sectors': [s.value for s in agent.sectors],
                    'capital': agent.initial_capital,
                    'metrics': {
                        'total_pnl': agent.trader.calculate_metrics().total_pnl,
                        'win_rate': agent.trader.calculate_metrics().win_rate,
                        'resolved_trades': agent.trader.calculate_metrics().resolved_trades,
                        'sharpe_ratio': agent.trader.calculate_metrics().sharpe_ratio,
                    },
                }
                for agent in self.agents
            ],
        }

        filename = "swarm_state.json"
        with open(filename, 'w') as f:
            json.dump(state, f, indent=2, default=str)

        print(f"[Saved] Swarm state to {filename}")


async def main():
    """Demo live trading swarm."""
    print("\n" + "="*80)
    print("LIVE TRADING SWARM - Multiple Sector-Based Agents")
    print("="*80 + "\n")

    # Initialize swarm
    swarm = LiveTradingSwarm(
        initial_capital_per_agent=10000,
        max_position_size=500,
        min_deviation=0.05,
    )

    # Run 3 cycles
    for i in range(3):
        print(f"\n{'='*80}")
        print(f"SWARM CYCLE {i+1}")
        print(f"{'='*80}\n")

        await swarm.run_cycle()

        # Simulate time passing between cycles
        if i < 2:
            print(f"\nSimulating 6 hours passing...\n")
            await asyncio.sleep(0.5)

    # Print final summary
    swarm.print_swarm_summary()


if __name__ == "__main__":
    asyncio.run(main())
