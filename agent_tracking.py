#!/usr/bin/env python3
"""
Agent Tracking & Analytics System

Comprehensive tracking for specialized agent performance.
- Per-agent metrics
- Per-niche comparison
- Time-series performance
- Expertise development tracking
- Leaderboards and rankings
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from enum import Enum
import numpy as np

from agent_specialization import (
    SpecializedAgent, AgentSwarm, Niche, AgentIdentity, Trade, NichePerformance
)


class TimeGranularity(Enum):
    """Time granularity for tracking."""
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


@dataclass
class AgentSnapshot:
    """Snapshot of agent state at a point in time."""
    agent_id: str
    timestamp: datetime

    # Financial snapshot
    current_capital: float
    total_return: float
    daily_return: float

    # Performance snapshot
    total_trades: int
    win_rate: float
    sharpe_ratio: float

    # Reputation snapshot
    overall_reputation: float
    niche_reputation: float

    # Expertise snapshot
    expertise_score: float
    knowledge_depth: float
    adaptability: float
    consistency: float

    # Niche-specific snapshot
    niche: str
    niche_trades: int
    niche_win_rate: float
    niche_pnl: float


@dataclass
class NicheSnapshot:
    """Snapshot of niche performance at a point in time."""
    niche: str
    timestamp: datetime

    # Aggregate metrics
    total_agents: int
    total_trades: int
    total_pnl: float
    avg_win_rate: float

    # Top performers
    top_agent_id: str
    top_agent_pnl: float
    top_agent_win_rate: float

    # Best strategy
    best_strategy: str
    best_strategy_return: float


@dataclass
class SwarmSnapshot:
    """Snapshot of entire swarm at a point in time."""
    timestamp: datetime

    # Aggregate metrics
    total_agents: int
    total_capital: float
    total_return: float

    # Performance metrics
    total_trades: int
    avg_win_rate: float
    total_pnl: float

    # Niche distribution
    niches_covered: int
    agents_per_niche: Dict[str, int]

    # Top performers
    top_niche: str
    top_niche_pnl: float
    top_agent_id: str
    top_agent_pnl: float


class AgentTracker:
    """
    Track and analyze agent performance over time.

    Creates time-series data for:
    - Individual agents
    - Niche performance
    - Swarm-wide metrics
    """

    def __init__(self, swarm: AgentSwarm):
        self.swarm = swarm

        # Time-series data
        self.agent_snapshots: Dict[str, List[AgentSnapshot]] = defaultdict(list)
        self.niche_snapshots: Dict[Niche, List[NicheSnapshot]] = defaultdict(list)
        self.swarm_snapshots: List[SwarmSnapshot] = []

        # Metrics aggregation
        self.hourly_metrics: Dict[datetime, Dict] = {}
        self.daily_metrics: Dict[datetime, Dict] = {}
        self.weekly_metrics: Dict[datetime, Dict] = {}

    async def take_snapshot(self) -> SwarmSnapshot:
        """Take a snapshot of the entire swarm state."""
        timestamp = datetime.now()

        # Agent snapshots
        for agent_id, agent in self.swarm.agents.items():
            perf = agent.niche_performance.get(agent.specialized_niche)

            snapshot = AgentSnapshot(
                agent_id=agent_id,
                timestamp=timestamp,
                current_capital=agent.current_capital,
                total_return=(agent.current_capital / agent.initial_capital - 1),
                daily_return=self._calculate_daily_return(agent),
                total_trades=agent.identity.trades_count,
                win_rate=agent.identity.win_rate,
                sharpe_ratio=perf.sharpe_ratio if perf else 0.0,
                overall_reputation=agent.identity.overall_reputation,
                niche_reputation=agent.identity.niche_reputation,
                expertise_score=agent.identity.expertise_score,
                knowledge_depth=agent.identity.knowledge_depth,
                adaptability=agent.identity.adaptability,
                consistency=agent.identity.consistency,
                niche=agent.specialized_niche.value,
                niche_trades=perf.total_trades if perf else 0,
                niche_win_rate=perf.win_rate if perf else 0.0,
                niche_pnl=perf.total_profit_loss if perf else 0.0,
            )

            self.agent_snapshots[agent_id].append(snapshot)

        # Niche snapshots
        for niche, perf in self.swarm.swarm_performance.items():
            # Find top agent in this niche
            top_agent_id = None
            top_agent_pnl = -float('inf')

            for agent_id in self.swarm.niche_agents.get(niche, []):
                agent = self.swarm.agents[agent_id]
                agent_perf = agent.niche_performance.get(niche)
                if agent_perf and agent_perf.total_profit_loss > top_agent_pnl:
                    top_agent_pnl = agent_perf.total_profit_loss
                    top_agent_id = agent_id

            snapshot = NicheSnapshot(
                niche=niche.value,
                timestamp=timestamp,
                total_agents=len(self.swarm.niche_agents.get(niche, [])),
                total_trades=perf.total_trades,
                total_pnl=perf.total_profit_loss,
                avg_win_rate=perf.win_rate,
                top_agent_id=top_agent_id,
                top_agent_pnl=top_agent_pnl,
                top_agent_win_rate=self.swarm.agents[top_agent_id].identity.win_rate if top_agent_id else 0.0,
                best_strategy="N/A",  # Would be calculated from strategies
                best_strategy_return=0.0,
            )

            self.niche_snapshots[niche].append(snapshot)

        # Swarm snapshot
        # Find top niche
        top_niche = None
        top_niche_pnl = -float('inf')
        for niche, perf in self.swarm.swarm_performance.items():
            if perf.total_profit_loss > top_niche_pnl:
                top_niche_pnl = perf.total_profit_loss
                top_niche = niche

        # Find top agent
        top_agent_id = None
        top_agent_pnl = -float('inf')
        for agent_id, agent in self.swarm.agents.items():
            perf = agent.niche_performance.get(agent.specialized_niche)
            if perf and perf.total_profit_loss > top_agent_pnl:
                top_agent_pnl = perf.total_profit_loss
                top_agent_id = agent_id

        swarm_snapshot = SwarmSnapshot(
            timestamp=timestamp,
            total_agents=len(self.swarm.agents),
            total_capital=self.swarm.current_capital,
            total_return=(self.swarm.current_capital / self.swarm.initial_capital - 1),
            total_trades=self.swarm.total_trades,
            avg_win_rate=sum(perf.win_rate for perf in self.swarm.swarm_performance.values()) / len(self.swarm.swarm_performance) if self.swarm.swarm_performance else 0.0,
            total_pnl=self.swarm.total_profit_loss,
            niches_covered=len(self.swarm.niche_agents),
            agents_per_niche={niche.value: len(agents) for niche, agents in self.swarm.niche_agents.items()},
            top_niche=top_niche.value if top_niche else "N/A",
            top_niche_pnl=top_niche_pnl,
            top_agent_id=top_agent_id,
            top_agent_pnl=top_agent_pnl,
        )

        self.swarm_snapshots.append(swarm_snapshot)

        return swarm_snapshot

    def _calculate_daily_return(self, agent: SpecializedAgent) -> float:
        """Calculate daily return for an agent."""
        # Get yesterday's snapshot
        yesterday = datetime.now() - timedelta(days=1)

        yesterday_capital = None
        for snapshot in reversed(self.agent_snapshots[agent.agent_id]):
            if snapshot.timestamp.date() == yesterday.date():
                yesterday_capital = snapshot.current_capital
                break

        if yesterday_capital:
            return (agent.current_capital / yesterday_capital - 1)
        else:
            return 0.0

    async def generate_agent_report(self, agent_id: str) -> Dict:
        """Generate comprehensive report for an agent."""
        if agent_id not in self.swarm.agents:
            return {"error": "Agent not found"}

        agent = self.swarm.agents[agent_id]
        snapshots = self.agent_snapshots.get(agent_id, [])

        if not snapshots:
            return {"error": "No snapshots available"}

        # Current state
        current = snapshots[-1]

        # Performance trends
        if len(snapshots) > 1:
            # Calculate trends
            capital_trend = snapshots[-1].current_capital - snapshots[0].current_capital
            win_rate_trend = snapshots[-1].win_rate - snapshots[0].win_rate
            reputation_trend = snapshots[-1].overall_reputation - snapshots[0].overall_reputation
            expertise_trend = snapshots[-1].expertise_score - snapshots[0].expertise_score
        else:
            capital_trend = 0.0
            win_rate_trend = 0.0
            reputation_trend = 0.0
            expertise_trend = 0.0

        # Calculate metrics
        total_trades = len(agent.trades)
        profitable_trades = sum(1 for t in agent.trades if t.outcome == "WIN")
        total_pnl = sum(t.profit_loss for t in agent.trades if t.profit_loss)

        # Win rate by niche
        niche_performance = {}
        for niche, perf in agent.niche_performance.items():
            niche_performance[niche.value] = {
                'trades': perf.total_trades,
                'win_rate': perf.win_rate,
                'pnl': perf.total_profit_loss,
                'sharpe': perf.sharpe_ratio,
            }

        # Recent performance
        recent_trades = agent.trades[-10:]
        recent_wins = sum(1 for t in recent_trades if t.outcome == "WIN")
        recent_pnl = sum(t.profit_loss for t in recent_trades if t.profit_loss)

        return {
            'agent_id': agent_id,
            'name': agent.name,
            'specialization': agent.specialized_niche.value,

            # Current metrics
            'current_metrics': {
                'capital': current.current_capital,
                'return': current.total_return,
                'daily_return': current.daily_return,
                'win_rate': current.win_rate,
                'sharpe_ratio': current.sharpe_ratio,
            },

            # Trends
            'trends': {
                'capital_change': capital_trend,
                'win_rate_change': win_rate_trend,
                'reputation_change': reputation_trend,
                'expertise_growth': expertise_trend,
            },

            # Trade stats
            'trade_stats': {
                'total_trades': total_trades,
                'profitable_trades': profitable_trades,
                'total_pnl': total_pnl,
            },

            # Reputation
            'reputation': {
                'overall': agent.identity.overall_reputation,
                'niche': agent.identity.niche_reputation,
                'rank_in_niche': self._get_agent_rank_in_niche(agent_id),
            },

            # Expertise
            'expertise': {
                'score': agent.identity.expertise_score,
                'knowledge_depth': agent.identity.knowledge_depth,
                'adaptability': agent.identity.adaptability,
                'consistency': agent.identity.consistency,
            },

            # Niche performance
            'niche_performance': niche_performance,

            # Recent performance
            'recent_performance': {
                'trades': len(recent_trades),
                'wins': recent_wins,
                'win_rate': recent_wins / len(recent_trades) if recent_trades else 0.0,
                'pnl': recent_pnl,
            },

            # Risk metrics
            'risk_metrics': {
                'max_drawdown': self._calculate_max_drawdown(agent_id),
                'avg_position_size': agent.niche_performance.get(agent.specialized_niche, NichePerformance(niche=agent.specialized_niche)).avg_position_size,
                'max_position_size': agent.niche_performance.get(agent.specialized_niche, NichePerformance(niche=agent.specialized_niche)).max_position_size,
            },
        }

    def _get_agent_rank_in_niche(self, agent_id: str) -> int:
        """Get agent's rank within their niche."""
        agent = self.swarm.agents[agent_id]
        niche = agent.specialized_niche

        if niche not in self.swarm.leaderboards:
            return 0

        leaderboard = self.swarm.leaderboards[niche]

        for rank, (lb_agent_id, score) in enumerate(leaderboard, 1):
            if lb_agent_id == agent_id:
                return rank

        return 0

    def _calculate_max_drawdown(self, agent_id: str) -> float:
        """Calculate maximum drawdown for an agent."""
        snapshots = self.agent_snapshots.get(agent_id, [])

        if len(snapshots) < 2:
            return 0.0

        peak = snapshots[0].current_capital
        max_drawdown = 0.0

        for snapshot in snapshots[1:]:
            if snapshot.current_capital > peak:
                peak = snapshot.current_capital

            drawdown = (peak - snapshot.current_capital) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        return max_drawdown

    async def generate_niche_report(self, niche: Niche) -> Dict:
        """Generate comprehensive report for a niche."""
        snapshots = self.niche_snapshots.get(niche, [])

        if not snapshots:
            return {"error": "No snapshots available"}

        # Current state
        current = snapshots[-1]

        # Agent ranking
        agents_in_niche = self.swarm.niche_agents.get(niche, [])
        agent_rankings = []

        for agent_id in agents_in_niche:
            agent = self.swarm.agents[agent_id]
            perf = agent.niche_performance.get(niche)

            agent_rankings.append({
                'agent_id': agent_id,
                'name': agent.name,
                'pnl': perf.total_profit_loss if perf else 0.0,
                'win_rate': perf.win_rate if perf else 0.0,
                'trades': perf.total_trades if perf else 0,
                'sharpe': perf.sharpe_ratio if perf else 0.0,
                'reputation': agent.identity.niche_reputation,
            })

        # Sort by PnL
        agent_rankings.sort(key=lambda x: x['pnl'], reverse=True)

        # Niche trends
        if len(snapshots) > 1:
            pnl_trend = snapshots[-1].total_pnl - snapshots[0].total_pnl
            win_rate_trend = snapshots[-1].avg_win_rate - snapshots[0].avg_win_rate
        else:
            pnl_trend = 0.0
            win_rate_trend = 0.0

        return {
            'niche': niche.value,

            # Current metrics
            'current_metrics': {
                'total_agents': current.total_agents,
                'total_trades': current.total_trades,
                'total_pnl': current.total_pnl,
                'avg_win_rate': current.avg_win_rate,
            },

            # Trends
            'trends': {
                'pnl_change': pnl_trend,
                'win_rate_change': win_rate_trend,
            },

            # Agent rankings
            'agent_rankings': agent_rankings,

            # Top performer
            'top_performer': {
                'agent_id': current.top_agent_id,
                'pnl': current.top_agent_pnl,
                'win_rate': current.top_agent_win_rate,
            },

            # Market opportunity
            'market_opportunity': {
                'liquidity': self._estimate_niche_liquidity(niche),
                'competition': self._estimate_niche_competition(niche),
                'edge_potential': self._estimate_niche_edge_potential(niche),
            },
        }

    def _estimate_niche_liquidity(self, niche: Niche) -> float:
        """Estimate liquidity of a niche (simulated)."""
        # In production, would fetch real market data
        niche_liquidity_map = {
            Niche.CRYPTO_HOURLY: 0.95,
            Niche.CRYPTO_DAILY: 0.90,
            Niche.CRYPTO_OPTIONS: 0.85,
            Niche.NBA_PLAYER_PROPS: 0.80,
            Niche.NFL_PLAYER_PROPS: 0.78,
            Niche.MLB_PLAYER_PROPS: 0.72,
            Niche.PRESIDENTIAL_ELECTIONS: 0.70,
            Niche.INTEREST_RATES: 0.65,
            Niche.INFLATION_DATA: 0.60,
        }

        return niche_liquidity_map.get(niche, 0.5)

    def _estimate_niche_competition(self, niche: Niche) -> float:
        """Estimate competition in a niche (simulated)."""
        # Higher value = more competition
        niche_competition_map = {
            Niche.CRYPTO_HOURLY: 0.85,
            Niche.CRYPTO_DAILY: 0.80,
            Niche.CRYPTO_OPTIONS: 0.75,
            Niche.NBA_PLAYER_PROPS: 0.70,
            Niche.NFL_PLAYER_PROPS: 0.68,
            Niche.MLB_PLAYER_PROPS: 0.62,
            Niche.PRESIDENTIAL_ELECTIONS: 0.55,
            Niche.INTEREST_RATES: 0.50,
            Niche.INFLATION_DATA: 0.45,
        }

        return niche_competition_map.get(niche, 0.3)

    def _estimate_niche_edge_potential(self, niche: Niche) -> float:
        """Estimate edge potential in a niche (simulated)."""
        # Higher value = more potential for edge (less efficient markets)
        niche_edge_map = {
            Niche.PRESIDENTIAL_ELECTIONS: 0.90,
            Niche.INTEREST_RATES: 0.85,
            Niche.INFLATION_DATA: 0.80,
            Niche.MLB_PLAYER_PROPS: 0.75,
            Niche.NFL_PLAYER_PROPS: 0.70,
            Niche.NBA_PLAYER_PROPS: 0.68,
            Niche.CRYPTO_OPTIONS: 0.60,
            Niche.CRYPTO_HOURLY: 0.40,
            Niche.CRYPTO_DAILY: 0.35,
        }

        return niche_edge_map.get(niche, 0.5)

    async def generate_swarm_report(self) -> Dict:
        """Generate comprehensive report for the entire swarm."""
        if not self.swarm_snapshots:
            return {"error": "No snapshots available"}

        # Current state
        current = self.swarm_snapshots[-1]

        # Trends
        if len(self.swarm_snapshots) > 1:
            first = self.swarm_snapshots[0]
            capital_trend = current.total_capital - first.total_capital
            return_trend = current.total_return - first.total_return
            trades_trend = current.total_trades - first.total_trades
        else:
            capital_trend = 0.0
            return_trend = 0.0
            trades_trend = 0

        # Niche performance ranking
        niche_rankings = []
        for niche, perf in self.swarm.swarm_performance.items():
            niche_rankings.append({
                'niche': niche.value,
                'pnl': perf.total_profit_loss,
                'win_rate': perf.win_rate,
                'trades': perf.total_trades,
                'agents': len(self.swarm.niche_agents.get(niche, [])),
            })

        niche_rankings.sort(key=lambda x: x['pnl'], reverse=True)

        # Top agents across all niches
        all_agents = []
        for agent_id, agent in self.swarm.agents.items():
            perf = agent.niche_performance.get(agent.specialized_niche)
            all_agents.append({
                'agent_id': agent_id,
                'name': agent.name,
                'niche': agent.specialized_niche.value,
                'pnl': perf.total_profit_loss if perf else 0.0,
                'win_rate': perf.win_rate if perf else 0.0,
                'reputation': agent.identity.overall_reputation,
            })

        all_agents.sort(key=lambda x: x['pnl'], reverse=True)

        return {
            # Current metrics
            'current_metrics': {
                'total_agents': current.total_agents,
                'total_capital': current.total_capital,
                'total_return': current.total_return,
                'total_trades': current.total_trades,
                'avg_win_rate': current.avg_win_rate,
                'total_pnl': current.total_pnl,
                'niches_covered': current.niches_covered,
            },

            # Trends
            'trends': {
                'capital_change': capital_trend,
                'return_change': return_trend,
                'trades_change': trades_trend,
            },

            # Niche rankings
            'niche_rankings': niche_rankings,

            # Top agents
            'top_agents': all_agents[:10],

            # Top niche
            'top_niche': {
                'niche': current.top_niche,
                'pnl': current.top_niche_pnl,
            },

            # Top agent
            'top_agent': {
                'agent_id': current.top_agent_id,
                'pnl': current.top_agent_pnl,
            },

            # Agent distribution
            'agent_distribution': current.agents_per_niche,
        }

    def print_agent_report(self, agent_id: str):
        """Print formatted agent report."""
        import asyncio

        report = asyncio.run(self.generate_agent_report(agent_id))

        if 'error' in report:
            print(f"Error: {report['error']}")
            return

        print(f"\n{'='*80}")
        print(f"AGENT REPORT: {report['name']} ({report['agent_id']})")
        print(f"{'='*80}")

        print(f"\nSpecialization: {report['specialization']}")

        print(f"\nCurrent Metrics:")
        print(f"  Capital: ${report['current_metrics']['capital']:.2f}")
        print(f"  Total Return: {report['current_metrics']['return']*100:.2f}%")
        print(f"  Daily Return: {report['current_metrics']['daily_return']*100:.2f}%")
        print(f"  Win Rate: {report['current_metrics']['win_rate']*100:.1f}%")
        print(f"  Sharpe Ratio: {report['current_metrics']['sharpe_ratio']:.2f}")

        print(f"\nTrends:")
        print(f"  Capital Change: ${report['trends']['capital_change']:.2f}")
        print(f"  Win Rate Change: {report['trends']['win_rate_change']*100:.2f}%")
        print(f"  Reputation Change: {report['trends']['reputation_change']:.1f}")
        print(f"  Expertise Growth: {report['trends']['expertise_growth']*100:.1f}%")

        print(f"\nTrade Stats:")
        print(f"  Total Trades: {report['trade_stats']['total_trades']}")
        print(f"  Profitable Trades: {report['trade_stats']['profitable_trades']}")
        print(f"  Total PnL: ${report['trade_stats']['total_pnl']:.2f}")

        print(f"\nReputation:")
        print(f"  Overall: {report['reputation']['overall']:.1f}/100")
        print(f"  Niche: {report['reputation']['niche']:.1f}/100")
        print(f"  Rank in Niche: #{report['reputation']['rank_in_niche']}")

        print(f"\nExpertise:")
        print(f"  Score: {report['expertise']['score']*100:.1f}%")
        print(f"  Knowledge Depth: {report['expertise']['knowledge_depth']*100:.1f}%")
        print(f"  Adaptability: {report['expertise']['adaptability']*100:.1f}%")
        print(f"  Consistency: {report['expertise']['consistency']*100:.1f}%")

        print(f"\nRisk Metrics:")
        print(f"  Max Drawdown: {report['risk_metrics']['max_drawdown']*100:.2f}%")
        print(f"  Avg Position Size: ${report['risk_metrics']['avg_position_size']:.2f}")
        print(f"  Max Position Size: ${report['risk_metrics']['max_position_size']:.2f}")

        print(f"\nRecent Performance (last 10 trades):")
        print(f"  Trades: {report['recent_performance']['trades']}")
        print(f"  Wins: {report['recent_performance']['wins']}")
        print(f"  Win Rate: {report['recent_performance']['win_rate']*100:.1f}%")
        print(f"  PnL: ${report['recent_performance']['pnl']:.2f}")

        print(f"\nNiche Performance:")
        for niche, perf in report['niche_performance'].items():
            print(f"  {niche}:")
            print(f"    Trades: {perf['trades']}")
            print(f"    Win Rate: {perf['win_rate']*100:.1f}%")
            print(f"    PnL: ${perf['pnl']:.2f}")
            print(f"    Sharpe: {perf['sharpe']:.2f}")

        print(f"{'='*80}\n")

    def print_niche_report(self, niche: Niche):
        """Print formatted niche report."""
        import asyncio

        report = asyncio.run(self.generate_niche_report(niche))

        if 'error' in report:
            print(f"Error: {report['error']}")
            return

        print(f"\n{'='*80}")
        print(f"NICHE REPORT: {report['niche']}")
        print(f"{'='*80}")

        print(f"\nCurrent Metrics:")
        print(f"  Total Agents: {report['current_metrics']['total_agents']}")
        print(f"  Total Trades: {report['current_metrics']['total_trades']}")
        print(f"  Total PnL: ${report['current_metrics']['total_pnl']:.2f}")
        print(f"  Avg Win Rate: {report['current_metrics']['avg_win_rate']*100:.1f}%")

        print(f"\nTrends:")
        print(f"  PnL Change: ${report['trends']['pnl_change']:.2f}")
        print(f"  Win Rate Change: {report['trends']['win_rate_change']*100:.2f}%")

        print(f"\nTop Performer:")
        print(f"  Agent: {report['top_performer']['agent_id']}")
        print(f"  PnL: ${report['top_performer']['pnl']:.2f}")
        print(f"  Win Rate: {report['top_performer']['win_rate']*100:.1f}%")

        print(f"\nMarket Opportunity:")
        print(f"  Liquidity: {report['market_opportunity']['liquidity']*100:.0f}%")
        print(f"  Competition: {report['market_opportunity']['competition']*100:.0f}%")
        print(f"  Edge Potential: {report['market_opportunity']['edge_potential']*100:.0f}%")

        print(f"\nAgent Rankings:")
        print(f"{'Rank':<6} {'Agent':<30} {'PnL':<12} {'Win Rate':<10} {'Trades':<8}")
        print(f"{'-'*80}")

        for rank, agent_data in enumerate(report['agent_rankings'][:5], 1):
            print(f"{rank:<6} {agent_data['name']:<30} ${agent_data['pnl']:>9.2f} {agent_data['win_rate']*100:>8.1f}% {agent_data['trades']:<8}")

        print(f"{'='*80}\n")

    def print_swarm_report(self):
        """Print formatted swarm report."""
        import asyncio

        report = asyncio.run(self.generate_swarm_report())

        if 'error' in report:
            print(f"Error: {report['error']}")
            return

        print(f"\n{'='*80}")
        print(f"SWARM REPORT")
        print(f"{'='*80}")

        print(f"\nCurrent Metrics:")
        print(f"  Total Agents: {report['current_metrics']['total_agents']}")
        print(f"  Total Capital: ${report['current_metrics']['total_capital']:.2f}")
        print(f"  Total Return: {report['current_metrics']['total_return']*100:.2f}%")
        print(f"  Total Trades: {report['current_metrics']['total_trades']}")
        print(f"  Avg Win Rate: {report['current_metrics']['avg_win_rate']*100:.1f}%")
        print(f"  Total PnL: ${report['current_metrics']['total_pnl']:.2f}")
        print(f"  Niches Covered: {report['current_metrics']['niches_covered']}")

        print(f"\nTrends:")
        print(f"  Capital Change: ${report['trends']['capital_change']:.2f}")
        print(f"  Return Change: {report['trends']['return_change']*100:.2f}%")
        print(f"  Trades Change: {report['trends']['trades_change']}")

        print(f"\nTop Niche:")
        print(f"  Niche: {report['top_niche']['niche']}")
        print(f"  PnL: ${report['top_niche']['pnl']:.2f}")

        print(f"\nTop Agent:")
        print(f"  Agent: {report['top_agent']['agent_id']}")
        print(f"  PnL: ${report['top_agent']['pnl']:.2f}")

        print(f"\nNiche Rankings:")
        print(f"{'Rank':<6} {'Niche':<30} {'PnL':<12} {'Win Rate':<10} {'Trades':<8}")
        print(f"{'-'*80}")

        for rank, niche_data in enumerate(report['niche_rankings'][:5], 1):
            print(f"{rank:<6} {niche_data['niche']:<30} ${niche_data['pnl']:>9.2f} {niche_data['win_rate']*100:>8.1f}% {niche_data['trades']:<8}")

        print(f"\nTop Agents (All Niches):")
        print(f"{'Rank':<6} {'Agent':<30} {'Niche':<20} {'PnL':<12} {'Win Rate':<10}")
        print(f"{'-'*80}")

        for rank, agent_data in enumerate(report['top_agents'][:5], 1):
            print(f"{rank:<6} {agent_data['name']:<30} {agent_data['niche']:<20} ${agent_data['pnl']:>9.2f} {agent_data['win_rate']*100:>8.1f}%")

        print(f"\nAgent Distribution:")
        for niche, count in sorted(report['agent_distribution'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {niche}: {count} agents")

        print(f"{'='*80}\n")


async def main():
    """Demo agent tracking system."""
    from market_discovery import MarketDiscovery
    from agent_specialization import AgentSwarm, Niche

    print("\n" + "="*80)
    print("AGENT TRACKING SYSTEM")
    print("="*80 + "\n")

    # Create swarm
    swarm = AgentSwarm(initial_capital=100000)

    # Create specialized agents
    print("[Creating specialized agents...]\n")

    await swarm.create_specialized_agent("Crypto Charlie", Niche.CRYPTO_HOURLY, capital_allocation=15000)
    await swarm.create_specialized_agent("Nate the Great", Niche.NBA_PLAYER_PROPS, capital_allocation=10000)
    await swarm.create_specialized_agent("Political Patty", Niche.PRESIDENTIAL_ELECTIONS, capital_allocation=8000)
    await swarm.create_specialized_agent("Economist Ed", Niche.INTEREST_RATES, capital_allocation=8000)
    await swarm.create_specialized_agent("Stats Sam", Niche.NFL_PLAYER_PROPS, capital_allocation=10000)
    await swarm.create_specialized_agent("Baseball Bob", Niche.MLB_PLAYER_PROPS, capital_allocation=10000)

    # Create tracker
    tracker = AgentTracker(swarm)

    # Discover markets
    discovery = MarketDiscovery(
        min_volume=1000.0,
        max_resolution_days=30,
        min_liquidity_score=0.3,
    )

    print("[Discovering markets...]\n")

    all_markets = []
    for sector in [Sector.SPORTS, Sector.CRYPTO, Sector.POLITICS]:
        markets = await discovery.discover_markets(
            sectors=[sector],
            limit=30,
        )
        all_markets.extend(markets)

    print(f"Discovered {len(all_markets)} total markets\n")

    # Run trading cycles
    for cycle in range(1, 4):
        print(f"{'='*80}")
        print(f"TRADING CYCLE {cycle}")
        print(f"{'='*80}\n")

        # Distribute and trade
        agent_markets = await swarm.distribute_markets_to_agents(all_markets)
        trades = await swarm.execute_agent_trades(agent_markets)

        print(f"Executed {len(trades)} trades\n")

        # Update leaderboards
        await swarm.update_leaderboards()

        # Take snapshot
        await tracker.take_snapshot()

        # Print swarm summary
        swarm.print_swarm_summary()

        # Print niche leaderboards
        for niche in [Niche.CRYPTO_HOURLY, Niche.NBA_PLAYER_PROPS]:
            if niche in swarm.leaderboards:
                swarm.print_leaderboard(niche, top_n=3)

        await asyncio.sleep(0.5)

    # Print final reports
    print(f"\n{'='*80}")
    print(f"FINAL REPORTS")
    print(f"{'='*80}\n")

    # Swarm report
    tracker.print_swarm_report()

    # Top agent report
    top_agent = max(swarm.agents.values(), key=lambda a: a.current_capital)
    tracker.print_agent_report(top_agent.agent_id)

    # Top niche report
    top_niche = max(swarm.swarm_performance.items(), key=lambda x: x[1].total_profit_loss)[0]
    tracker.print_niche_report(top_niche)


if __name__ == "__main__":
    asyncio.run(main())
