#!/usr/bin/env python3
"""
Fast Inference Engine - Batch predictions for all markets.

Separates training (once/day) from inference (every 5 minutes).
Predictions take seconds, not minutes.
"""

import asyncio
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import time
from collections import defaultdict
import pickle

from market_discovery import Market, Sector


class FastInferenceEngine:
    """
    Fast batch inference for prediction markets.

    Key optimization: Predict ALL markets at once, not one-by-one.
    """

    def __init__(
        self,
        agent_id: str,
        sector: Sector,
        model_path: str = None,
        min_edge_pct: float = 0.05,  # 5% minimum edge
    ):
        self.agent_id = agent_id
        self.sector = sector
        self.model_path = model_path
        self.min_edge_pct = min_edge_pct

        # Load model (once at startup)
        self.model = None
        if model_path:
            self._load_model()

        # Data cache
        self.odds_cache: Dict[str, Dict] = {}  # market_id -> odds data
        self.features_cache: Dict[str, np.ndarray] = {}  # market_id -> features
        self.predictions_cache: Dict[str, float] = {}  # market_id -> probability

        # Performance tracking
        self.inference_times = []
        self.batch_sizes = []

    def _load_model(self):
        """Load trained model from disk."""
        try:
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            print(f"[{self.agent_id}] Model loaded: {self.model_path}")
        except Exception as e:
            print(f"[{self.agent_id}] Failed to load model: {e}")
            self.model = None

    async def update_data_cache(self, markets: List[Market]):
        """
        Update data cache with market data.

        In production: Stream via WebSocket (real-time)
        For demo: Simulate fast update
        """
        start = time.time()

        for market in markets:
            self.odds_cache[market.market_id] = {
                'yes_odds': market.yes_odds,
                'no_odds': market.no_odds,
                'volume': market.current_volume,
                'liquidity': market.liquidity_score,
                'timestamp': datetime.now(),
            }

            # Extract features (cached for inference)
            self.features_cache[market.market_id] = self._extract_features(market)

        update_time = time.time() - start
        print(f"[{self.agent_id}] Data cache updated: {len(markets)} markets in {update_time:.3f}s")

    def _extract_features(self, market: Market) -> np.ndarray:
        """Extract features for prediction."""
        # Simple features for demo
        features = [
            market.yes_odds,
            market.no_odds,
            market.current_volume / 10000.0,  # Normalized volume
            market.liquidity_score,
            abs(market.yes_odds - 0.5),  # Distance from 50%
            (market.resolution_time - datetime.now()).total_seconds() / 3600.0,  # Hours to resolution
        ]

        # Add more features in production:
        # - Historical odds movement
        # - Volume trends
        # - Sentiment
        # - Team stats (for sports)
        # - Polling data (for politics)

        return np.array(features)

    async def batch_predict(self, markets: List[Market]) -> List[Dict]:
        """
        Batch predict for ALL markets at once.

        Key optimization: Batch processing, not one-by-one.
        """
        start = time.time()

        if self.model is None:
            # Use simple heuristic if no model
            predictions = self._heuristic_predict(markets)
        else:
            # Use model for batch prediction
            predictions = self._model_predict_batch(markets)

        predict_time = time.time() - start

        # Track performance
        self.inference_times.append(predict_time)
        self.batch_sizes.append(len(markets))

        print(f"[{self.agent_id}] Batch prediction: {len(markets)} markets in {predict_time:.3f}s")
        print(f"[{self.agent_id}] Avg prediction time: {predict_time/len(markets)*1000:.2f}ms per market")

        return predictions

    def _model_predict_batch(self, markets: List[Market]) -> List[Dict]:
        """
        Batch prediction using trained model.

        Key: Single model.predict() call for ALL markets.
        """
        # Prepare all features at once
        all_features = np.array([
            self._extract_features(market)
            for market in markets
        ])

        # Batch prediction (one call!)
        start = time.time()
        all_predictions = self.model.predict(all_features)
        predict_time = time.time() - start

        # Package results
        results = []
        for market, pred_prob in zip(markets, all_predictions):
            result = {
                'market_id': market.market_id,
                'market_title': market.title,
                'internal_probability': pred_prob,
                'market_probability': market.yes_odds,
                'edge_pct': pred_prob - market.yes_odds,
                'expected_value': (pred_prob - market.yes_odds) / market.yes_odds,
            }
            results.append(result)

        print(f"[{self.agent_id}] Model.predict() time: {predict_time*1000:.2f}ms for {len(markets)} markets")

        return results

    def _heuristic_predict(self, markets: List[Market]) -> List[Dict]:
        """
        Heuristic prediction (simple model).

        Used when no trained model available.
        """
        results = []

        for market in markets:
            # Simple heuristic: odds around 50% are more likely to be mispriced
            base_prob = 0.5

            # Adjust based on odds
            if market.yes_odds > 0.6:
                base_prob -= 0.1
            elif market.yes_odds < 0.4:
                base_prob += 0.1

            # Add randomness (simulating model uncertainty)
            noise = np.random.normal(0, 0.08)
            pred_prob = base_prob + noise
            pred_prob = max(0.1, min(0.9, pred_prob))

            result = {
                'market_id': market.market_id,
                'market_title': market.title,
                'internal_probability': pred_prob,
                'market_probability': market.yes_odds,
                'edge_pct': pred_prob - market.yes_odds,
                'expected_value': (pred_prob - market.yes_odds) / market.yes_odds,
            }
            results.append(result)

        return results

    async def identify_edges(self, predictions: List[Dict]) -> List[Dict]:
        """
        Identify markets with quantifiable edge.

        Edge = internal_probability - market_probability
        Only consider markets with edge > threshold (5%).
        """
        start = time.time()

        # Filter by edge threshold
        edges = [
            pred for pred in predictions
            if abs(pred['edge_pct']) >= self.min_edge_pct
        ]

        # Sort by edge (descending)
        edges.sort(key=lambda x: abs(x['edge_pct']), reverse=True)

        # Add side (YES or NO)
        for edge in edges:
            if edge['edge_pct'] > 0:
                edge['side'] = 'YES'
                edge['market_odds'] = edge['market_probability']
                edge['take_odds'] = 1.0 / edge['market_probability']
            else:
                edge['side'] = 'NO'
                edge['market_odds'] = edge['market_probability'] - 1.0 + 1.0
                # For NO, edge is on opposite side
                edge['take_odds'] = 1.0 / (1.0 - edge['market_probability'])

        filter_time = time.time() - start

        print(f"[{self.agent_id}] Identified {len(edges)} edges in {filter_time:.3f}s")
        print(f"[{self.agent_id}] Threshold: {self.min_edge_pct:.1%}")

        return edges

    async def fast_iteration(
        self,
        markets: List[Market],
        execute_trades: bool = True,
    ) -> Dict:
        """
        Run fast iteration cycle.

        Takes 2-3 seconds total (not minutes).
        """
        iteration_start = time.time()

        print(f"\n{'='*70}")
        print(f"FAST ITERATION - {self.agent_id}")
        print(f"{'='*70}")

        # Step 1: Update data cache (<1 sec)
        print(f"\n[Step 1] Updating data cache...")
        await self.update_data_cache(markets)

        # Step 2: Batch predict (<1 sec)
        print(f"\n[Step 2] Batch predicting...")
        predictions = await self.batch_predict(markets)

        # Step 3: Identify edges (<0.1 sec)
        print(f"\n[Step 3] Identifying edges...")
        edges = await self.identify_edges(predictions)

        # Step 4: Execute trades (<1 sec)
        trades_executed = []
        if execute_trades and edges:
            print(f"\n[Step 4] Executing top trades...")
            trades_executed = await self._execute_top_trades(edges[:10])  # Top 10 edges

        iteration_time = time.time() - iteration_start

        result = {
            'agent_id': self.agent_id,
            'sector': self.sector.value,
            'markets_processed': len(markets),
            'edges_found': len(edges),
            'trades_executed': len(trades_executed),
            'predictions': predictions,
            'edges': edges,
            'trades': trades_executed,
            'iteration_time': iteration_time,
            'timestamp': datetime.now().isoformat(),
        }

        # Print summary
        print(f"\n{'='*70}")
        print(f"ITERATION SUMMARY")
        print(f"{'='*70}")
        print(f"Markets processed: {len(markets)}")
        print(f"Edges found: {len(edges)}")
        print(f"Trades executed: {len(trades_executed)}")
        print(f"Iteration time: {iteration_time:.3f}s")
        print(f"{'='*70}\n")

        return result

    async def _execute_top_trades(self, edges: List[Dict]) -> List[Dict]:
        """Execute top edge trades."""
        trades = []

        for edge in edges:
            # Calculate position size (5% of edge confidence)
            edge_confidence = min(abs(edge['edge_pct']) / self.min_edge_pct, 2.0)
            position_size = 500 * edge_confidence  # $500 max

            trade = {
                'market_id': edge['market_id'],
                'market_title': edge['market_title'],
                'side': edge['side'],
                'position_size': position_size,
                'entry_odds': edge['market_odds'],
                'take_odds': edge['take_odds'],
                'edge_pct': edge['edge_pct'],
                'expected_value': edge['expected_value'],
                'timestamp': datetime.now().isoformat(),
            }

            trades.append(trade)

            print(f"  Trade: {edge['market_title']}")
            print(f"    Side: {edge['side']}")
            print(f"    Size: ${position_size:.2f}")
            print(f"    Edge: {edge['edge_pct']:.2%}")
            print(f"    EV: {edge['expected_value']:.4f}")

        return trades

    def print_performance_stats(self):
        """Print inference performance statistics."""
        if not self.inference_times:
            return

        avg_time = np.mean(self.inference_times)
        avg_batch_size = np.mean(self.batch_sizes)

        print(f"\n{'='*70}")
        print(f"PERFORMANCE STATS - {self.agent_id}")
        print(f"{'='*70}")
        print(f"Total iterations: {len(self.inference_times)}")
        print(f"Avg iteration time: {avg_time:.3f}s")
        print(f"Avg batch size: {avg_batch_size:.0f} markets")
        print(f"Avg time per market: {avg_time/avg_batch_size*1000:.2f}ms")
        print(f"Throughput: {avg_batch_size/avg_time:.0f} markets/second")
        print(f"{'='*70}\n")


class FastSectorAgent:
    """
    Fast sector-based agent.

    Runs fast iteration cycles continuously.
    """

    def __init__(
        self,
        agent_id: str,
        sector: Sector,
        model_path: str = None,
        iteration_interval_minutes: int = 5,
        data_fetch_interval_minutes: int = 1,
    ):
        self.agent_id = agent_id
        self.sector = sector
        self.inference_engine = FastInferenceEngine(
            agent_id=agent_id,
            sector=sector,
            model_path=model_path,
            min_edge_pct=0.05,
        )

        self.iteration_interval = iteration_interval_minutes * 60  # Convert to seconds
        self.data_fetch_interval = data_fetch_interval_minutes * 60

        self.iteration_count = 0
        self.results_history = []

    async def run_continuous(
        self,
        market_discovery,
        max_iterations: int = None,
    ):
        """
        Run continuous fast iterations.

        Every 5 minutes: Predict for ALL markets, find edges, execute trades.
        Every 1 minute: Update data cache.
        """
        print(f"\n{'='*70}")
        print(f"FAST CONTINUOUS AGENT - {self.agent_id}")
        print(f"{'='*70}")
        print(f"Sector: {self.sector.value}")
        print(f"Iteration interval: {self.iteration_interval/60:.0f} minutes")
        print(f"Data fetch interval: {self.data_fetch_interval/60:.0f} minutes")
        print(f"{'='*70}\n")

        iteration_start_time = time.time()
        last_data_fetch = iteration_start_time - self.data_fetch_interval

        while True:
            current_time = time.time()

            # Check if we need to fetch data
            if current_time - last_data_fetch >= self.data_fetch_interval:
                print(f"\n[Data] Fetching fresh data...")
                markets = await market_discovery.discover_markets(
                    sectors=[self.sector],
                    limit=200,
                )
                print(f"[Data] Found {len(markets)} markets")

                # Update data cache
                await self.inference_engine.update_data_cache(markets)

                last_data_fetch = current_time

            # Check if we need to run inference iteration
            if current_time - last_data_fetch >= self.iteration_interval:
                # Run fast iteration
                result = await self.inference_engine.fast_iteration(
                    markets,
                    execute_trades=True,
                )

                self.results_history.append(result)
                self.iteration_count += 1

                # Print stats every 10 iterations
                if self.iteration_count % 10 == 0:
                    self.inference_engine.print_performance_stats()

                    # Print edge statistics
                    self._print_edge_stats()

            # Check if we should stop
            if max_iterations and self.iteration_count >= max_iterations:
                print(f"\nReached {max_iterations} iterations. Stopping.")
                break

            # Sleep for short interval (check every 30 seconds)
            await asyncio.sleep(30)

    def _print_edge_stats(self):
        """Print statistics on edges found."""
        total_edges = sum(r['edges_found'] for r in self.results_history)
        total_trades = sum(r['trades_executed'] for r in self.results_history)
        avg_edges_per_iter = total_edges / len(self.results_history) if self.results_history else 0

        print(f"\n{'='*70}")
        print(f"EDGE STATISTICS - {self.agent_id}")
        print(f"{'='*70}")
        print(f"Total iterations: {len(self.results_history)}")
        print(f"Total edges found: {total_edges}")
        print(f"Total trades executed: {total_trades}")
        print(f"Avg edges per iteration: {avg_edges_per_iter:.1f}")
        print(f"{'='*70}\n")


async def main():
    """Demo fast inference."""
    from market_discovery import MarketDiscovery

    print("\n" + "="*70)
    print("FAST INFERENCE ENGINE - Batch Predictions")
    print("="*70 + "\n")

    # Create agent
    agent = FastSectorAgent(
        agent_id="sports_fast_agent",
        sector=Sector.SPORTS,
        model_path=None,  # No model, use heuristic
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
    await agent.run_continuous(
        market_discovery=discovery,
        max_iterations=3,
    )

    # Print performance stats
    agent.inference_engine.print_performance_stats()
    agent._print_edge_stats()


if __name__ == "__main__":
    asyncio.run(main())
