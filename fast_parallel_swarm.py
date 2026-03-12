#!/usr/bin/env python3
"""
Fast Parallel Swarm - Multiple sector agents running in parallel.

All agents run fast iteration cycles simultaneously.
Total iteration time: 2-3 seconds for ALL sectors (not 2-3 seconds per sector).
"""

import asyncio
import numpy as np
from datetime import datetime
from typing import List, Dict
import time

from fast_inference_engine import FastSectorAgent
from market_discovery import Sector


class FastParallelSwarm:
    """
    Parallel swarm of fast sector agents.

    All agents run simultaneously, maximizing throughput.
    """

    def __init__(
        self,
        iteration_interval_minutes: int = 5,
        data_fetch_interval_minutes: int = 1,
    ):
        self.iteration_interval = iteration_interval_minutes
        self.data_fetch_interval = data_fetch_interval_minutes

        # Create sector agents
        self.agents = self._create_agents()

        # Performance tracking
        self.total_iterations = 0
        self.swarm_performance = []

    def _create_agents(self) -> List[FastSectorAgent]:
        """Create sector-based agents."""
        agent_configs = [
            {
                'agent_id': 'sports_fast_001',
                'sector': Sector.SPORTS,
                'model_path': None,
            },
            {
                'agent_id': 'politics_fast',
                'sector': Sector.POLITICS,
                'model_path': None,
            },
            {
                'agent_id': 'crypto_fast_001',
                'sector': Sector.CRYPTO,
                'model_path': None,
            },
            {
                'agent_id': 'tech_fast',
                'sector': Sector.TECHNOLOGY,
                'model_path': None,
            },
            {
                'agent_id': 'economy_fast',
                'sector': Sector.ECONOMICS,
                'model_path': None,
            },
            {
                'agent_id': 'entertainment_fast',
                'sector': Sector.ENTERTAINMENT,
                'model_path': None,
            },
            {
                'agent_id': 'esports_fast',
                'sector': Sector.SPORTS,  # Use sports sector for esports
                'model_path': None,
            },
        ]

        agents = []
        for config in agent_configs:
            agent = FastSectorAgent(
                agent_id=config['agent_id'],
                sector=config['sector'],
                model_path=config['model_path'],
                iteration_interval_minutes=self.iteration_interval,
                data_fetch_interval_minutes=self.data_fetch_interval,
            )
            agents.append(agent)

        return agents

    async def run_parallel_iteration(
        self,
        market_discovery,
    ) -> Dict:
        """
        Run parallel iteration across all agents.

        All agents run simultaneously in parallel.
        """
        iteration_start = time.time()

        print(f"\n{'='*70}")
        print(f"PARALLEL ITERATION - Fast Swarm")
        print(f"{'='*70}")
        print(f"Agents: {len(self.agents)}")
        print(f"Iteration: {self.total_iterations + 1}")
        print(f"{'='*70}\n")

        # Step 1: All agents fetch data (parallel)
        print("[Step 1] All agents fetching data (parallel)...")
        data_fetch_start = time.time()

        fetch_tasks = [
            market_discovery.discover_markets(
                sectors=[agent.sector],
                limit=200,
            )
            for agent in self.agents
        ]

        all_markets = await asyncio.gather(*fetch_tasks)
        data_fetch_time = time.time() - data_fetch_start

        print(f"[Step 1] Data fetch complete: {data_fetch_time:.2f}s")

        # Step 2: All agents update caches (parallel)
        print("\n[Step 2] All agents updating caches (parallel)...")
        cache_update_start = time.time()

        cache_tasks = [
            agent.inference_engine.update_data_cache(markets)
            for agent, markets in zip(self.agents, all_markets)
        ]

        await asyncio.gather(*cache_tasks)
        cache_update_time = time.time() - cache_update_start

        print(f"[Step 2] Cache update complete: {cache_update_time:.2f}s")

        # Step 3: All agents batch predict (parallel)
        print("\n[Step 3] All agents batch predicting (parallel)...")
        predict_start = time.time()

        predict_tasks = [
            agent.inference_engine.batch_predict(markets)
            for agent, markets in zip(self.agents, all_markets)
        ]

        all_predictions = await asyncio.gather(*predict_tasks)
        predict_time = time.time() - predict_start

        print(f"[Step 3] Batch prediction complete: {predict_time:.2f}s")

        # Step 4: All agents identify edges (parallel)
        print("\n[Step 4] All agents identifying edges (parallel)...")
        edge_start = time.time()

        edge_tasks = [
            agent.inference_engine.identify_edges(predictions)
            for agent, predictions in zip(self.agents, all_predictions)
        ]

        all_edges = await asyncio.gather(*edge_tasks)
        edge_time = time.time() - edge_start

        print(f"[Step 4] Edge identification complete: {edge_time:.2f}s")

        # Step 5: All agents execute trades (parallel)
        print("\n[Step 5] All agents executing trades (parallel)...")
        trade_start = time.time()

        trade_tasks = [
            agent.inference_engine._execute_top_trades(edges[:10])
            for agent, edges in zip(self.agents, all_edges)
        ]

        all_trades = await asyncio.gather(*trade_tasks)
        trade_time = time.time() - trade_start

        print(f"[Step 5] Trade execution complete: {trade_time:.2f}s")

        # Calculate totals
        total_iteration_time = time.time() - iteration_start

        total_markets = sum(len(m) for m in all_markets)
        total_edges = sum(len(e) for e in all_edges)
        total_trades = sum(len(t) for t in all_trades)

        # Aggregate results
        results = {
            'iteration': self.total_iterations + 1,
            'agents': len(self.agents),
            'total_markets': total_markets,
            'total_edges': total_edges,
            'total_trades': total_trades,
            'data_fetch_time': data_fetch_time,
            'cache_update_time': cache_update_time,
            'predict_time': predict_time,
            'edge_time': edge_time,
            'trade_time': trade_time,
            'total_time': total_iteration_time,
            'agent_results': [
                {
                    'agent_id': agent.agent_id,
                    'sector': agent.sector.value,
                    'markets': len(markets),
                    'edges': len(edges),
                    'trades': len(trades),
                }
                for agent, markets, edges, trades in zip(self.agents, all_markets, all_edges, all_trades)
            ],
            'timestamp': datetime.now().isoformat(),
        }

        # Print summary
        self._print_iteration_summary(results)

        self.total_iterations += 1
        self.swarm_performance.append(results)

        return results

    def _print_iteration_summary(self, results: Dict):
        """Print iteration summary."""
        print(f"\n{'='*70}")
        print(f"PARALLEL ITERATION SUMMARY")
        print(f"{'='*70}")
        print(f"Iteration: {results['iteration']}")
        print(f"Total markets processed: {results['total_markets']}")
        print(f"Total edges found: {results['total_edges']}")
        print(f"Total trades executed: {results['total_trades']}")

        print(f"\nTiming Breakdown:")
        print(f"  Data fetch:         {results['data_fetch_time']:.2f}s")
        print(f"  Cache update:       {results['cache_update_time']:.2f}s")
        print(f"  Batch prediction:    {results['predict_time']:.2f}s")
        print(f"  Edge identification:  {results['edge_time']:.2f}s")
        print(f"  Trade execution:     {results['trade_time']:.2f}s")
        print(f"  TOTAL:              {results['total_time']:.2f}s")

        print(f"\nAgent Results:")
        for agent_result in results['agent_results']:
            print(f"  {agent_result['agent_id']:20s}: {agent_result['markets']:3d} markets, {agent_result['edges']:2d} edges, {agent_result['trades']:2d} trades")

        print(f"\nThroughput: {results['total_markets']/results['total_time']:.0f} markets/second")
        print(f"Edge rate: {results['total_edges']/results['total_markets']*100:.1f}%")
        print(f"Trade rate: {results['total_trades']/results['total_edges']*100:.1f}% of edges")
        print(f"{'='*70}\n")

    async def run_continuous(
        self,
        market_discovery,
        max_iterations: int = None,
    ):
        """
        Run continuous parallel iterations.

        Every 5 minutes: Run parallel iteration across all agents.
        """
        print(f"\n{'='*70}")
        print(f"FAST PARALLEL SWARM - Continuous Operation")
        print(f"{'='*70}")
        print(f"Agents: {len(self.agents)}")
        print(f"Iteration interval: {self.iteration_interval} minutes")
        print(f"{'='*70}\n")

        while True:
            # Run parallel iteration
            await self.run_parallel_iteration(market_discovery)

            # Check if we should stop
            if max_iterations and self.total_iterations >= max_iterations:
                print(f"\nReached {max_iterations} iterations. Stopping.")
                break

            # Print swarm performance every 5 iterations
            if self.total_iterations % 5 == 0:
                self._print_swarm_performance()

            # Wait for next iteration
            print(f"Waiting {self.iteration_interval} minutes until next iteration...\n")
            await asyncio.sleep(self.iteration_interval * 60)

    def _print_swarm_performance(self):
        """Print aggregate swarm performance."""
        if not self.swarm_performance:
            return

        print(f"\n{'='*70}")
        print(f"SWARM PERFORMANCE - {self.total_iterations} iterations")
        print(f"{'='*70}")

        # Calculate averages
        avg_time = np.mean([r['total_time'] for r in self.swarm_performance])
        avg_markets = np.mean([r['total_markets'] for r in self.swarm_performance])
        avg_edges = np.mean([r['total_edges'] for r in self.swarm_performance])
        avg_trades = np.mean([r['total_trades'] for r in self.swarm_performance])

        print(f"Averages per iteration:")
        print(f"  Total time:    {avg_time:.2f}s")
        print(f"  Markets:       {avg_markets:.0f}")
        print(f"  Edges:         {avg_edges:.0f}")
        print(f"  Trades:        {avg_trades:.0f}")

        # Calculate totals
        total_markets = sum([r['total_markets'] for r in self.swarm_performance])
        total_edges = sum([r['total_edges'] for r in self.swarm_performance])
        total_trades = sum([r['total_trades'] for r in self.swarm_performance])

        print(f"\nTotals ({self.total_iterations} iterations):")
        print(f"  Markets processed: {total_markets}")
        print(f"  Edges found:      {total_edges}")
        print(f"  Trades executed:  {total_trades}")

        # Per-hour metrics
        hours_elapsed = self.total_iterations * self.iteration_interval / 60.0
        markets_per_hour = total_markets / hours_elapsed if hours_elapsed > 0 else 0
        edges_per_hour = total_edges / hours_elapsed if hours_elapsed > 0 else 0
        trades_per_hour = total_trades / hours_elapsed if hours_elapsed > 0 else 0

        print(f"\nPer Hour:")
        print(f"  Markets: {markets_per_hour:.0f}")
        print(f"  Edges:   {edges_per_hour:.0f}")
        print(f"  Trades:  {trades_per_hour:.0f}")

        print(f"{'='*70}\n")


async def main():
    """Demo fast parallel swarm."""
    from market_discovery import MarketDiscovery

    print("\n" + "="*70)
    print("FAST PARALLEL SWARM - Multi-Agent Fast Iterations")
    print("="*70 + "\n")

    # Create swarm
    swarm = FastParallelSwarm(
        iteration_interval_minutes=5,
        data_fetch_interval_minutes=1,
    )

    # Create market discovery
    discovery = MarketDiscovery(
        min_volume=1000.0,
        max_resolution_days=30,
        min_liquidity_score=0.3,
    )

    # Run for 3 iterations
    await swarm.run_continuous(
        market_discovery=discovery,
        max_iterations=3,
    )

    # Print performance
    swarm._print_swarm_performance()


if __name__ == "__main__":
    asyncio.run(main())
