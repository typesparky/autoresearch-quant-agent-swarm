#!/usr/bin/env python3
"""
AgentHub DAG

Manages swarm coordination via Directed Acyclic Graph of commits.
Agents share successful strategies and learn from each other.
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
from collections import defaultdict


class AgentHubDAG:
    """
    GitHub for agents - manages commits and relationships.

    Each commit is a node in the DAG, connected by parent-child relationships.
    Agents can:
    - Commit their successful models
    - Query the DAG for best strategies
    - Copy and improve upon other agents' work
    """

    def __init__(self, storage_path: str = "agenthub_dag.json"):
        self.storage_path = Path(storage_path)
        self.dag = self._load_dag()

        # Indexes for fast queries
        self._by_agent: Dict[str, List[str]] = defaultdict(list)
        self._by_timestamp: Dict[str, int] = {}
        self._rebuild_indexes()

    def _load_dag(self) -> Dict:
        """Load DAG from storage."""
        if self.storage_path.exists():
            with open(self.storage_path) as f:
                return json.load(f)
        return {
            "commits": {},
            "latest_commits": {},  # agent_id -> commit_id
        }

    def _save_dag(self):
        """Save DAG to storage."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, "w") as f:
            json.dump(self.dag, f, indent=2)

    def _rebuild_indexes(self):
        """Rebuild indexes for fast queries."""
        self._by_agent = defaultdict(list)
        self._by_timestamp = {}

        for commit_id, commit_data in self.dag["commits"].items():
            agent_id = commit_data["agent_id"]
            self._by_agent[agent_id].append(commit_id)
            self._by_timestamp[commit_id] = self._get_timestamp(commit_data)

        # Sort each agent's commits by timestamp
        for agent_id in self._by_agent:
            self._by_agent[agent_id].sort(
                key=lambda c: self._by_timestamp[c],
                reverse=True,
            )

    def _get_timestamp(self, commit_data: Dict) -> int:
        """Get timestamp from commit data."""
        ts_str = commit_data.get("timestamp", "")
        return int(datetime.fromisoformat(ts_str).timestamp())

    def commit(
        self,
        agent_id: str,
        commit_hash: str,
        data: Dict,
        parent_commit_id: Optional[str] = None,
    ) -> str:
        """
        Create a new commit in the DAG.

        Returns:
        - commit_id: Unique identifier for the commit
        """
        commit_id = f"{agent_id}_{commit_hash}"

        # Create commit node
        commit_node = {
            "commit_id": commit_id,
            "commit_hash": commit_hash,
            "agent_id": agent_id,
            "parent_id": parent_commit_id,
            "timestamp": datetime.now().isoformat(),
            "data": data,
        }

        # Add to DAG
        self.dag["commits"][commit_id] = commit_node
        self.dag["latest_commits"][agent_id] = commit_id

        # Update indexes
        self._by_agent[agent_id].append(commit_id)
        self._by_timestamp[commit_id] = self._get_timestamp(commit_node)

        # Save to storage
        self._save_dag()

        print(f"[AgentHub] Committed {commit_id} from {agent_id}")

        return commit_id

    def get_commit(self, commit_id: str) -> Optional[Dict]:
        """Get commit by ID."""
        return self.dag["commits"].get(commit_id)

    def get_agent_commits(
        self,
        agent_id: str,
        limit: int = 10,
    ) -> List[Dict]:
        """Get latest commits for an agent."""
        commit_ids = self._by_agent.get(agent_id, [])[:limit]
        return [self.dag["commits"][cid] for cid in commit_ids]

    def get_best_commits(
        self,
        metric: str = "sharpe_ratio",
        limit: int = 10,
        min_trades: int = 50,
    ) -> List[Dict]:
        """
        Get best commits across all agents by metric.

        Useful for agents to discover and learn from top performers.
        """
        all_commits = list(self.dag["commits"].values())

        # Filter by minimum trades
        valid_commits = [
            c for c in all_commits
            if c["data"].get("metrics", {}).get("num_trades", 0) >= min_trades
        ]

        # Sort by metric
        valid_commits.sort(
            key=lambda c: c["data"]["metrics"].get(metric, 0),
            reverse=True,
        )

        return valid_commits[:limit]

    def get_consensus(self, limit: int = 20) -> Dict:
        """
        Get consensus view across the swarm.

        Returns:
        - consensus_metrics: Average metrics across latest commits
        - strategy_distribution: Distribution of strategies being used
        """
        # Get latest commit from each agent
        latest_commits = []
        for agent_id, commit_id in self.dag["latest_commits"].items():
            if commit_id in self.dag["commits"]:
                latest_commits.append(self.dag["commits"][commit_id])

        if not latest_commits:
            return {"consensus_metrics": {}, "strategy_distribution": {}}

        # Calculate consensus metrics
        metric_keys = ["total_pnl", "sharpe_ratio", "win_rate", "max_drawdown"]
        consensus_metrics = {}

        for key in metric_keys:
            values = [
                c["data"]["metrics"].get(key, 0)
                for c in latest_commits
                if "metrics" in c["data"] and key in c["data"]["metrics"]
            ]
            if values:
                consensus_metrics[key] = {
                    "mean": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values),
                }

        # Analyze strategy distribution
        strategies = defaultdict(int)
        for commit in latest_commits:
            strategy = commit["data"].get("reason", "unknown")
            strategies[strategy] += 1

        strategy_distribution = {
            k: {"count": v, "percentage": v / len(latest_commits) * 100}
            for k, v in strategies.items()
        }

        return {
            "consensus_metrics": consensus_metrics,
            "strategy_distribution": strategy_distribution,
            "num_agents": len(latest_commits),
        }

    def get_divergence(self) -> Dict:
        """
        Measure divergence in swarm predictions.

        High divergence indicates:
        - Agents disagree on market direction
        - High polarity in the market
        - Multiple valid strategies being tested
        """
        latest_commits = [
            self.dag["commits"][cid]
            for cid in self.dag["latest_commits"].values()
            if cid in self.dag["commits"]
        ]

        if len(latest_commits) < 2:
            return {"divergence_score": 0.0, "polarity": "none"}

        # Get Sharpe ratios
        sharpes = [
            c["data"]["metrics"].get("sharpe_ratio", 0)
            for c in latest_commits
            if "metrics" in c["data"]
        ]

        if not sharpes:
            return {"divergence_score": 0.0, "polarity": "none"}

        # Calculate divergence (standard deviation of Sharpe)
        mean_sharpe = sum(sharpes) / len(sharpes)
        variance = sum((s - mean_sharpe) ** 2 for s in sharpes) / len(sharpes)
        divergence_score = variance ** 0.5

        # Classify polarity
        if divergence_score < 0.3:
            polarity = "low"
        elif divergence_score < 0.7:
            polarity = "medium"
        else:
            polarity = "high"

        return {
            "divergence_score": divergence_score,
            "polarity": polarity,
            "mean_sharpe": mean_sharpe,
            "sharpe_range": [min(sharpes), max(sharpes)],
            "num_agents": len(sharpes),
        }

    def print_status(self):
        """Print AgentHub status."""
        print(f"\n{'='*60}")
        print("AgentHub Status")
        print(f"{'='*60}")

        num_commits = len(self.dag["commits"])
        num_agents = len(self.dag["latest_commits"])

        print(f"Total commits:    {num_commits}")
        print(f"Active agents:    {num_agents}")

        # Get consensus
        consensus = self.get_consensus()
        if consensus["consensus_metrics"]:
            metrics = consensus["consensus_metrics"]
            print(f"\nConsensus Metrics:")
            if "sharpe_ratio" in metrics:
                print(f"  Mean Sharpe:    {metrics['sharpe_ratio']['mean']:.2f}")
            if "total_pnl" in metrics:
                print(f"  Mean PnL:       ${metrics['total_pnl']['mean']:.2f}")
            if "win_rate" in metrics:
                print(f"  Mean Win Rate:  {metrics['win_rate']['mean']:.2%}")

        # Get divergence
        divergence = self.get_divergence()
        print(f"\nSwarm Divergence:")
        print(f"  Score:          {divergence['divergence_score']:.2f}")
        print(f"  Polarity:       {divergence['polarity']}")

        print(f"{'='*60}\n")
