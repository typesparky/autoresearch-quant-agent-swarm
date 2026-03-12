#!/usr/bin/env python3
"""
Agent Specialization & Tracking System

Simulates real prediction market traders who specialize in niches.
- Each agent specializes in a specific market type/niche
- Track performance by niche
- Leaderboards per niche
- Reputation system
- Expertise development
"""

import asyncio
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
import json

from market_discovery import Market, Sector
from tiered_optimization import TieredOptimizer, MarketTierClassifier


class Niche(Enum):
    """Market niches for agent specialization."""

    # Sports niches
    NBA_GAME = "NBA Game"
    NBA_PLAYER_PROPS = "NBA Player Props"
    NFL_GAME = "NFL Game"
    NFL_PLAYER_PROPS = "NFL Player Props"
    MLB_GAME = "MLB Game"
    MLB_PLAYER_PROPS = "MLB Player Props"
    SOCCER = "Soccer"
    TENNIS = "Tennis"
    COMBAT_SPORTS = "Combat Sports"

    # Crypto niches
    CRYPTO_HOURLY = "Crypto Hourly"
    CRYPTO_DAILY = "Crypto Daily"
    CRYPTO_OPTIONS = "Crypto Options"
    DEFI_PROTOCOLS = "DeFi Protocols"

    # Politics niches
    PRESIDENTIAL_ELECTIONS = "Presidential Elections"
    CONGRESSIONAL_ELECTIONS = "Congressional Elections"
    STATE_ELECTIONS = "State Elections"
    POLLING_TRENDS = "Polling Trends"

    # Economics niches
    INTEREST_RATES = "Interest Rates"
    INFLATION_DATA = "Inflation Data"
    GDP_FORECASTS = "GDP Forecasts"
    ECONOMIC_INDICATORS = "Economic Indicators"

    # Entertainment niches
    AWARDS_SHOWS = "Awards Shows"
    REALITY_TV = "Reality TV"
    GAMING_TOURNAMENTS = "Gaming Tournaments"

    # Weather niches
    HURRICANES = "Hurricanes"
    SEVERE_WEATHER = "Severe Weather"
    TEMPERATURE_RECORDS = "Temperature Records"


@dataclass
class AgentIdentity:
    """Agent identity and reputation."""

    agent_id: str
    name: str
    specialized_niche: Niche
    secondary_niches: List[Niche] = field(default_factory=list)

    # Reputation metrics
    overall_reputation: float = 50.0  # 0-100 scale
    niche_reputation: float = 50.0  # Reputation within niche
    trades_count: int = 0
    successful_trades: int = 0
    win_rate: float = 0.0

    # Expertise development
    expertise_score: float = 0.0  # How expert they are in niche
    knowledge_depth: float = 0.0  # Depth of knowledge
    adaptability: float = 0.0  # How fast they adapt to changes
    consistency: float = 0.0  # Consistency of performance

    # Tracking
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    specialization_start: datetime = field(default_factory=datetime.now)

    def calculate_reputation(self):
        """Calculate reputation based on performance."""
        if self.trades_count > 0:
            self.win_rate = self.successful_trades / self.trades_count

        # Reputation = base + win_rate_bonus + consistency_bonus + expertise_bonus
        base = 30.0
        win_rate_bonus = self.win_rate * 40.0
        consistency_bonus = self.consistency * 15.0
        expertise_bonus = self.expertise_score * 15.0

        self.overall_reputation = base + win_rate_bonus + consistency_bonus + expertise_bonus
        self.overall_reputation = min(100.0, max(0.0, self.overall_reputation))

        # Niche reputation is higher (specialization bonus)
        self.niche_reputation = min(100.0, self.overall_reputation + 5.0)


@dataclass
class Trade:
    """Individual trade executed by an agent."""

    trade_id: str
    agent_id: str
    market_id: str
    niche: Niche

    # Market details
    market_title: str
    prediction: float  # 0-1 probability
    market_odds: float
    position_size: float
    direction: str  # "YES" or "NO"

    # Outcome
    outcome: Optional[str] = None  # "YES", "NO", or "PENDING"
    profit_loss: Optional[float] = None
    execution_time: Optional[float] = None  # Time to execute in seconds

    # Timing
    placed_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None

    # Edge analysis
    expected_edge: Optional[float] = None  # Expected edge (prediction - odds)
    realized_edge: Optional[float] = None  # Actual edge


@dataclass
class NichePerformance:
    """Performance metrics for a specific niche."""

    niche: Niche

    # Aggregate metrics
    total_trades: int = 0
    successful_trades: int = 0
    win_rate: float = 0.0
    total_profit_loss: float = 0.0
    sharpe_ratio: float = 0.0

    # Edge metrics
    avg_expected_edge: float = 0.0
    avg_realized_edge: float = 0.0
    edge_accuracy: float = 0.0  # How often expected edge > realized edge

    # Timing metrics
    avg_execution_time: float = 0.0

    # Risk metrics
    max_drawdown: float = 0.0
    max_position_size: float = 0.0
    avg_position_size: float = 0.0

    # Recent performance (last 10 trades)
    recent_win_rate: float = 0.0
    recent_profit_loss: float = 0.0


class NicheClassifier:
    """Classify markets into niches for agent specialization."""

    @staticmethod
    def classify_market(market: Market) -> Niche:
        """Classify a market into its niche."""
        title_lower = market.title.lower()
        description_lower = (market.description or "").lower()
        text = f"{title_lower} {description_lower}"

        # Sports niches
        if "nba" in text:
            if "player" in text or "prop" in text:
                return Niche.NBA_PLAYER_PROPS
            else:
                return Niche.NBA_GAME
        elif "nfl" in text or "football" in text:
            if "player" in text or "prop" in text or "touchdown" in text:
                return Niche.NFL_PLAYER_PROPS
            else:
                return Niche.NFL_GAME
        elif "mlb" in text or "baseball" in text:
            if "player" in text or "prop" in text or "hit" in text:
                return Niche.MLB_PLAYER_PROPS
            else:
                return Niche.MLB_GAME
        elif "soccer" in text or "football" in text and "nfl" not in text:
            return Niche.SOCCER
        elif "tennis" in text:
            return Niche.TENNIS
        elif "ufc" in text or "mma" in text or "fight" in text or "boxing" in text:
            return Niche.COMBAT_SPORTS

        # Crypto niches
        elif "crypto" in text or "bitcoin" in text or "btc" in text or "ethereum" in text or "eth" in text:
            if "hour" in text or "hourly" in text or "1h" in text:
                return Niche.CRYPTO_HOURLY
            elif "daily" in text or "end of day" in text:
                return Niche.CRYPTO_DAILY
            elif "option" in text:
                return Niche.CRYPTO_OPTIONS
            elif "defi" in text or "protocol" in text or "yield" in text:
                return Niche.DEFI_PROTOCOLS
            else:
                return Niche.CRYPTO_DAILY  # Default

        # Politics niches
        elif "president" in text or "presidential" in text or "white house" in text:
            return Niche.PRESIDENTIAL_ELECTIONS
        elif "congress" in text or "senate" in text or "house" in text:
            return Niche.CONGRESSIONAL_ELECTIONS
        elif "governor" in text or "state" in text and "election" in text:
            return Niche.STATE_ELECTIONS
        elif "poll" in text or "polling" in text:
            return Niche.POLLING_TRENDS

        # Economics niches
        elif "interest rate" in text or "fed rate" in text or "fomc" in text:
            return Niche.INTEREST_RATES
        elif "inflation" in text or "cpi" in text or "pce" in text:
            return Niche.INFLATION_DATA
        elif "gdp" in text or "gross domestic" in text:
            return Niche.GDP_FORECASTS
        elif "employment" in text or "jobs" in text or "unemployment" in text:
            return Niche.ECONOMIC_INDICATORS

        # Entertainment niches
        elif "oscar" in text or "grammy" in text or "emmy" in text:
            return Niche.AWARDS_SHOWS
        elif "reality" in text or "survivor" in text or "bachelor" in text:
            return Niche.REALITY_TV
        elif "esport" in text or "league" in text or "championship" in text and "nfl" not in text:
            return Niche.GAMING_TOURNAMENTS

        # Weather niches
        elif "hurricane" in text or "cyclone" in text or "typhoon" in text:
            return Niche.HURRICANES
        elif "severe weather" in text or "tornado" in text or "storm" in text:
            return Niche.SEVERE_WEATHER
        elif "temperature" in text or "heat" in text or "cold" in text or "record" in text:
            return Niche.TEMPERATURE_RECORDS

        # Default: try to categorize by sector
        elif market.sector == Sector.SPORTS:
            return Niche.NBA_GAME  # Default sports
        elif market.sector == Sector.CRYPTO:
            return Niche.CRYPTO_DAILY
        elif market.sector == Sector.POLITICS:
            return Niche.PRESIDENTIAL_ELECTIONS
        else:
            # Try to detect crypto vs other
            if "price" in text and ("btc" in text or "eth" in text or "crypto" in text):
                return Niche.CRYPTO_DAILY
            else:
                return Niche.NBA_GAME  # Default


class SpecializedAgent:
    """
    A specialized agent that focuses on a specific market niche.

    Simulates real prediction market traders who specialize in a specific area
    to develop deeper knowledge and better models than generalists.
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        specialized_niche: Niche,
        secondary_niches: Optional[List[Niche]] = None,
        initial_capital: float = 10000,
        max_position_size: float = 500,
    ):
        self.agent_id = agent_id
        self.name = name
        self.specialized_niche = specialized_niche
        self.secondary_niches = secondary_niches or []

        # Financial metrics
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.max_position_size = max_position_size

        # Identity & reputation
        self.identity = AgentIdentity(
            agent_id=agent_id,
            name=name,
            specialized_niche=specialized_niche,
            secondary_niches=secondary_niches,
        )

        # Trading history
        self.trades: List[Trade] = []
        self.niche_performance: Dict[Niche, NichePerformance] = {}

        # Initialize performance for specialized niche
        self.niche_performance[specialized_niche] = NichePerformance(niche=specialized_niche)

        for niche in self.secondary_niches:
            self.niche_performance[niche] = NichePerformance(niche=niche)

        # Strategy parameters (niche-specific)
        self.risk_parameters = self._get_niche_risk_parameters()

        # Knowledge base (simulates agent's expertise)
        self.knowledge_base = self._initialize_knowledge_base()

        # Learning rate (how fast the agent learns)
        self.learning_rate = 0.05

    def _get_niche_risk_parameters(self) -> Dict:
        """Get risk parameters based on niche specialization."""
        niche = self.specialized_niche

        # Base parameters
        base_params = {
            'position_size_pct': 0.05,  # 5% per trade
            'min_edge_pct': 0.05,  # 5% minimum edge
            'max_positions': 10,
        }

        # Niche-specific adjustments
        if niche in [Niche.CRYPTO_HOURLY, Niche.CRYPTO_DAILY]:
            # Crypto: higher risk tolerance
            base_params.update({
                'position_size_pct': 0.07,  # 7%
                'min_edge_pct': 0.04,  # Lower threshold (more opportunities)
                'max_positions': 15,
            })
        elif niche in [Niche.NBA_PLAYER_PROPS, Niche.NFL_PLAYER_PROPS, Niche.MLB_PLAYER_PROPS]:
            # Player props: moderate risk
            base_params.update({
                'position_size_pct': 0.05,
                'min_edge_pct': 0.05,
                'max_positions': 12,
            })
        elif niche in [Niche.PRESIDENTIAL_ELECTIONS, Niche.CONGRESSIONAL_ELECTIONS]:
            # Elections: lower risk, high selectivity
            base_params.update({
                'position_size_pct': 0.03,
                'min_edge_pct': 0.08,  # High threshold (very selective)
                'max_positions': 5,
            })
        elif niche in [Niche.INTEREST_RATES, Niche.INFLATION_DATA]:
            # Economics: very selective
            base_params.update({
                'position_size_pct': 0.04,
                'min_edge_pct': 0.07,
                'max_positions': 6,
            })

        return base_params

    def _initialize_knowledge_base(self) -> Dict:
        """Initialize knowledge base based on niche."""
        niche = self.specialized_niche

        # Base knowledge structure
        knowledge = {
            'learned_patterns': [],
            'successful_features': [],
            'failed_strategies': [],
            'market_regimes': {},
            'edge_sources': [],
        }

        # Niche-specific initial knowledge
        if niche == Niche.CRYPTO_HOURLY:
            knowledge.update({
                'learned_patterns': [
                    'volatility clustering',
                    'momentum persistence',
                    'mean reversion in overbought conditions',
                ],
                'successful_features': [
                    'rsi_14',
                    'volume_surge',
                    'order_book_imbalance',
                ],
            })
        elif niche == Niche.NBA_PLAYER_PROPS:
            knowledge.update({
                'learned_patterns': [
                    'rest days impact',
                    'home/away split differences',
                    'injury recovery effects',
                ],
                'successful_features': [
                    'usage_rate',
                    'pace_of_play',
                    'defensive_rating',
                ],
            })

        return knowledge

    def is_market_in_specialization(self, market: Market) -> Tuple[bool, float]:
        """
        Check if market is within agent's specialization.

        Returns:
            (is_specialized, confidence_score)
        """
        niche = NicheClassifier.classify_market(market)

        if niche == self.specialized_niche:
            return True, 1.0  # 100% match
        elif niche in self.secondary_niches:
            return True, 0.7  # 70% match (secondary)
        else:
            return False, 0.0

    async def analyze_market(self, market: Market) -> Optional[Dict]:
        """
        Analyze a market within specialization.

        Returns:
            prediction, edge, confidence, or None if not in specialization
        """
        is_specialized, confidence = self.is_market_in_specialization(market)

        if not is_specialized:
            return None

        # Simulate analysis based on niche expertise
        niche = self.specialized_niche

        # Simulate prediction (would use actual ML models in production)
        base_prediction = np.random.normal(0.5, 0.2)
        prediction = max(0.0, min(1.0, base_prediction))

        # Calculate edge
        market_odds = market.yes_price if hasattr(market, 'yes_price') else np.random.uniform(0.3, 0.7)
        expected_edge = prediction - market_odds

        # Adjust based on expertise
        expertise_multiplier = 0.5 + (self.identity.expertise_score * 0.5)  # 0.5 - 1.0

        # Adjust confidence based on niche knowledge
        niche_confidence = confidence * expertise_multiplier

        # Only trade if edge exceeds threshold
        min_edge = self.risk_parameters['min_edge_pct']
        if abs(expected_edge) < min_edge:
            return None

        return {
            'prediction': prediction,
            'market_odds': market_odds,
            'expected_edge': expected_edge,
            'confidence': niche_confidence,
            'niche': self.specialized_niche,
            'position_size': self._calculate_position_size(expected_edge, niche_confidence),
        }

    def _calculate_position_size(self, edge: float, confidence: float) -> float:
        """Calculate position size based on edge and confidence."""
        # Base position size
        base_size = self.current_capital * self.risk_parameters['position_size_pct']

        # Adjust based on edge (higher edge = larger position)
        edge_multiplier = 1.0 + (abs(edge) * 5.0)  # 1.0 - 1.25

        # Adjust based on confidence
        confidence_multiplier = 0.5 + (confidence * 0.5)  # 0.5 - 1.0

        # Calculate final size
        position_size = base_size * edge_multiplier * confidence_multiplier

        # Cap at max position size
        position_size = min(position_size, self.max_position_size)

        return round(position_size, 2)

    async def execute_trade(
        self,
        market: Market,
        prediction: float,
        position_size: float,
        execution_time: float,
    ) -> Trade:
        """Execute a trade in the market."""
        # Determine direction
        if prediction > 0.5:
            direction = "YES"
        else:
            direction = "NO"

        # Create trade
        trade = Trade(
            trade_id=f"{self.agent_id}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            agent_id=self.agent_id,
            market_id=market.market_id,
            niche=self.specialized_niche,
            market_title=market.title,
            prediction=prediction,
            market_odds=market.yes_price if hasattr(market, 'yes_price') else 0.5,
            position_size=position_size,
            direction=direction,
            execution_time=execution_time,
        )

        # Simulate outcome (random for demo)
        outcome = np.random.choice(["YES", "NO"], p=[prediction, 1-prediction])

        # Calculate PnL
        if direction == outcome:
            # Win
            if direction == "YES":
                profit_loss = position_size * (1.0 / trade.market_odds - 1.0)
            else:
                profit_loss = position_size * (1.0 / (1.0 - trade.market_odds) - 1.0)
            trade.outcome = "WIN"
        else:
            # Loss
            profit_loss = -position_size
            trade.outcome = "LOSS"

        trade.profit_loss = profit_loss

        # Update capital
        self.current_capital += profit_loss

        # Track trade
        self.trades.append(trade)

        # Update performance
        self._update_performance(trade)

        # Update identity
        self.identity.trades_count += 1
        if trade.outcome == "WIN":
            self.identity.successful_trades += 1
        self.identity.calculate_reputation()

        # Update last active
        self.identity.last_active = datetime.now()

        return trade

    def _update_performance(self, trade: Trade):
        """Update niche performance after a trade."""
        niche = trade.niche

        if niche not in self.niche_performance:
            self.niche_performance[niche] = NichePerformance(niche=niche)

        perf = self.niche_performance[niche]

        # Update aggregate metrics
        perf.total_trades += 1
        if trade.outcome == "WIN":
            perf.successful_trades += 1
        perf.win_rate = perf.successful_trades / perf.total_trades

        # Update PnL
        if trade.profit_loss:
            perf.total_profit_loss += trade.profit_loss

        # Update edge metrics
        if trade.expected_edge:
            perf.avg_expected_edge = (perf.avg_expected_edge * (perf.total_trades - 1) + trade.expected_edge) / perf.total_trades

        # Update execution time
        if trade.execution_time:
            perf.avg_execution_time = (perf.avg_execution_time * (perf.total_trades - 1) + trade.execution_time) / perf.total_trades

        # Update position size
        perf.max_position_size = max(perf.max_position_size, trade.position_size)
        perf.avg_position_size = (perf.avg_position_size * (perf.total_trades - 1) + trade.position_size) / perf.total_trades

        # Calculate Sharpe ratio (simplified)
        if perf.total_trades > 10:
            returns = [t.profit_loss for t in self.trades[-10:] if t.niche == niche and t.profit_loss]
            if returns:
                avg_return = np.mean(returns)
                std_return = np.std(returns)
                if std_return > 0:
                    perf.sharpe_ratio = avg_return / std_return

        # Update recent performance
        recent_trades = [t for t in self.trades if t.niche == niche][-10:]
        if recent_trades:
            recent_wins = sum(1 for t in recent_trades if t.outcome == "WIN")
            perf.recent_win_rate = recent_wins / len(recent_trades)
            perf.recent_profit_loss = sum(t.profit_loss for t in recent_trades if t.profit_loss)

    def learn_from_trade(self, trade: Trade):
        """Learn from the trade outcome to improve expertise."""
        if trade.outcome == "WIN":
            # Reinforce successful pattern
            self.identity.expertise_score = min(1.0, self.identity.expertise_score + self.learning_rate * 0.1)
        else:
            # Deduct from expertise (but slower than gains)
            self.identity.expertise_score = max(0.0, self.identity.expertise_score - self.learning_rate * 0.05)

        # Update consistency based on recent performance
        recent_trades = self.trades[-10:]
        if len(recent_trades) >= 5:
            recent_win_rate = sum(1 for t in recent_trades if t.outcome == "WIN") / len(recent_trades)
            self.identity.consistency = recent_win_rate

        # Update adaptability (how quickly agent adapts to new market conditions)
        # Higher if recent performance is improving
        if len(recent_trades) >= 5:
            recent_win_rate = sum(1 for t in recent_trades if t.outcome == "WIN") / len(recent_trades)
            older_trades = self.trades[-20:-10] if len(self.trades) > 20 else []
            if older_trades:
                older_win_rate = sum(1 for t in older_trades if t.outcome == "WIN") / len(older_trades)
                self.identity.adaptability = max(0.0, min(1.0, recent_win_rate - older_win_rate + 0.5))
            else:
                self.identity.adaptability = 0.5


class AgentSwarm:
    """
    Swarm of specialized agents, each focusing on a specific niche.

    Simulates a group of prediction market traders, each with their own
    specialization and expertise.
    """

    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital

        # Agent registry
        self.agents: Dict[str, SpecializedAgent] = {}

        # Leaderboards
        self.leaderboards: Dict[Niche, List[Tuple[str, float]]] = {}

        # Niche allocation
        self.niche_agents: Dict[Niche, List[str]] = defaultdict(list)

        # Performance tracking
        self.swarm_performance: Dict[Niche, NichePerformance] = {}
        self.total_trades: int = 0
        self.total_profit_loss: float = 0.0

    async def create_specialized_agent(
        self,
        name: str,
        specialized_niche: Niche,
        secondary_niches: Optional[List[Niche]] = None,
        capital_allocation: float = 10000,
    ) -> SpecializedAgent:
        """Create a new specialized agent."""
        agent_id = f"{specialized_niche.value.lower().replace(' ', '_')}_{len(self.agents)+1:03d}"

        agent = SpecializedAgent(
            agent_id=agent_id,
            name=name,
            specialized_niche=specialized_niche,
            secondary_niches=secondary_niches,
            initial_capital=capital_allocation,
        )

        self.agents[agent_id] = agent
        self.niche_agents[specialized_niche].append(agent_id)

        # Update capital
        self.current_capital -= capital_allocation

        # Initialize leaderboard
        if specialized_niche not in self.leaderboards:
            self.leaderboards[specialized_niche] = []

        # Initialize swarm performance
        if specialized_niche not in self.swarm_performance:
            self.swarm_performance[specialized_niche] = NichePerformance(niche=specialized_niche)

        return agent

    async def distribute_markets_to_agents(self, markets: List[Market]) -> Dict[str, List[Dict]]:
        """
        Distribute markets to specialized agents based on their specialization.

        Returns:
            Dict mapping agent_id to list of market analyses
        """
        agent_markets: Dict[str, List[Dict]] = defaultdict(list)

        for market in markets:
            # Classify market into niche
            niche = NicheClassifier.classify_market(market)

            # Find agents specializing in this niche
            if niche in self.niche_agents:
                for agent_id in self.niche_agents[niche]:
                    agent = self.agents[agent_id]

                    # Analyze market
                    analysis = await agent.analyze_market(market)

                    if analysis:
                        agent_markets[agent_id].append({
                            'market': market,
                            'analysis': analysis,
                        })

        return agent_markets

    async def execute_agent_trades(
        self,
        agent_markets: Dict[str, List[Dict]],
        max_execution_time: float = 10.0,
    ) -> List[Trade]:
        """Execute trades for all agents."""
        trades = []

        for agent_id, market_list in agent_markets.items():
            agent = self.agents[agent_id]

            for market_data in market_list:
                market = market_data['market']
                analysis = market_data['analysis']

                # Simulate execution time (based on agent expertise)
                execution_time = max(0.1, 2.0 - agent.identity.expertise_score)  # Better agents execute faster

                # Check execution time constraint
                if execution_time > max_execution_time:
                    continue

                # Execute trade
                trade = await agent.execute_trade(
                    market=market,
                    prediction=analysis['prediction'],
                    position_size=analysis['position_size'],
                    execution_time=execution_time,
                )

                trades.append(trade)

                # Agent learns from trade
                agent.learn_from_trade(trade)

                # Update swarm totals
                self.total_trades += 1
                if trade.profit_loss:
                    self.total_profit_loss += trade.profit_loss
                    self.current_capital += trade.profit_loss

                # Update swarm performance
                niche = trade.niche
                if niche not in self.swarm_performance:
                    self.swarm_performance[niche] = NichePerformance(niche=niche)

                perf = self.swarm_performance[niche]
                perf.total_trades += 1
                if trade.outcome == "WIN":
                    perf.successful_trades += 1
                perf.win_rate = perf.successful_trades / perf.total_trades
                if trade.profit_loss:
                    perf.total_profit_loss += trade.profit_loss

        return trades

    async def update_leaderboards(self):
        """Update leaderboards for each niche."""
        for niche in self.niche_agents.keys():
            agent_ids = self.niche_agents[niche]

            # Calculate scores
            scores = []
            for agent_id in agent_ids:
                agent = self.agents[agent_id]
                score = agent.identity.niche_reputation
                scores.append((agent_id, score))

            # Sort by score
            scores.sort(key=lambda x: x[1], reverse=True)

            # Update leaderboard
            self.leaderboards[niche] = scores

    def print_leaderboard(self, niche: Niche, top_n: int = 5):
        """Print leaderboard for a niche."""
        print(f"\n{'='*80}")
        print(f"LEADERBOARD: {niche.value}")
        print(f"{'='*80}")

        if niche not in self.leaderboards or not self.leaderboards[niche]:
            print(f"No agents in this niche yet.")
            return

        print(f"{'Rank':<6} {'Agent':<30} {'Reputation':<12} {'Trades':<8} {'Win Rate':<10}")
        print(f"{'-'*80}")

        for rank, (agent_id, score) in enumerate(self.leaderboards[niche][:top_n], 1):
            agent = self.agents[agent_id]
            perf = agent.niche_performance.get(niche)

            print(f"{rank:<6} {agent.name:<30} {score:>10.1f}/100 {agent.identity.trades_count:<8} {agent.identity.win_rate*100:>8.1f}%")

        print(f"{'='*80}\n")

    def print_swarm_summary(self):
        """Print swarm summary."""
        print(f"\n{'='*80}")
        print(f"AGENT SWARM SUMMARY")
        print(f"{'='*80}")

        print(f"\nTotal Agents: {len(self.agents)}")
        print(f"Total Niches: {len(self.niche_agents)}")
        print(f"Total Trades: {self.total_trades}")
        print(f"Total PnL: ${self.total_profit_loss:.2f}")
        print(f"Initial Capital: ${self.initial_capital:.2f}")
        print(f"Current Capital: ${self.current_capital:.2f}")
        print(f"Return: {(self.current_capital/self.initial_capital - 1)*100:.2f}%")

        print(f"\nNiche Performance:")
        print(f"{'Niche':<30} {'Trades':<8} {'Win Rate':<10} {'PnL':<12} {'Sharpe':<8}")
        print(f"{'-'*80}")

        for niche, perf in sorted(self.swarm_performance.items(), key=lambda x: x[1].total_profit_loss, reverse=True):
            print(f"{niche.value:<30} {perf.total_trades:<8} {perf.win_rate*100:>8.1f}% ${perf.total_profit_loss:>9.2f} {perf.sharpe_ratio:>7.2f}")

        print(f"\n{'='*80}\n")

    def print_agent_details(self, agent_id: str):
        """Print detailed information about an agent."""
        if agent_id not in self.agents:
            print(f"Agent {agent_id} not found.")
            return

        agent = self.agents[agent_id]

        print(f"\n{'='*80}")
        print(f"AGENT DETAILS: {agent.name} ({agent_id})")
        print(f"{'='*80}")

        print(f"\nSpecialization: {agent.specialized_niche.value}")
        print(f"Secondary Niches: {[n.value for n in agent.secondary_niches]}")

        print(f"\nFinancials:")
        print(f"  Initial Capital: ${agent.initial_capital:.2f}")
        print(f"  Current Capital: ${agent.current_capital:.2f}")
        print(f"  Return: {(agent.current_capital/agent.initial_capital - 1)*100:.2f}%")

        print(f"\nReputation:")
        print(f"  Overall: {agent.identity.overall_reputation:.1f}/100")
        print(f"  Niche: {agent.identity.niche_reputation:.1f}/100")
        print(f"  Trades: {agent.identity.trades_count}")
        print(f"  Win Rate: {agent.identity.win_rate*100:.1f}%")

        print(f"\nExpertise:")
        print(f"  Expertise Score: {agent.identity.expertise_score*100:.1f}%")
        print(f"  Knowledge Depth: {agent.identity.knowledge_depth*100:.1f}%")
        print(f"  Adaptability: {agent.identity.adaptability*100:.1f}%")
        print(f"  Consistency: {agent.identity.consistency*100:.1f}%")

        print(f"\nNiche Performance:")
        perf = agent.niche_performance.get(agent.specialized_niche)
        if perf:
            print(f"  Total Trades: {perf.total_trades}")
            print(f"  Win Rate: {perf.win_rate*100:.1f}%")
            print(f"  Total PnL: ${perf.total_profit_loss:.2f}")
            print(f"  Sharpe: {perf.sharpe_ratio:.2f}")
            print(f"  Avg Edge: {perf.avg_expected_edge*100:.2f}%")

        print(f"\nRecent Trades:")
        recent_trades = agent.trades[-5:]
        for trade in recent_trades:
            print(f"  {trade.outcome} | {trade.market_title[:50]} | PnL: ${trade.profit_loss:.2f}")

        print(f"\n{'='*80}\n")


async def main():
    """Demo agent specialization system."""
    from market_discovery import MarketDiscovery

    print("\n" + "="*80)
    print("AGENT SPECIALIZATION SYSTEM")
    print("="*80 + "\n")

    # Create swarm
    swarm = AgentSwarm(initial_capital=100000)

    # Create specialized agents for different niches
    print("\n[Creating specialized agents...]\n")

    # Sports agents
    await swarm.create_specialized_agent(
        name="Crypto Charlie",
        specialized_niche=Niche.CRYPTO_HOURLY,
        capital_allocation=15000,
    )

    await swarm.create_specialized_agent(
        name="Nate the Great",
        specialized_niche=Niche.NBA_PLAYER_PROPS,
        capital_allocation=10000,
    )

    await swarm.create_specialized_agent(
        name="Political Patty",
        specialized_niche=Niche.PRESIDENTIAL_ELECTIONS,
        capital_allocation=8000,
    )

    await swarm.create_specialized_agent(
        name="Economist Ed",
        specialized_niche=Niche.INTEREST_RATES,
        capital_allocation=8000,
    )

    await swarm.create_specialized_agent(
        name="Stats Sam",
        specialized_niche=Niche.NFL_PLAYER_PROPS,
        capital_allocation=10000,
    )

    await swarm.create_specialized_agent(
        name="Baseball Bob",
        specialized_niche=Niche.MLB_PLAYER_PROPS,
        capital_allocation=10000,
    )

    await swarm.create_specialized_agent(
        name="DeFi Diana",
        specialized_niche=Niche.DEFI_PROTOCOLS,
        capital_allocation=12000,
    )

    await swarm.create_specialized_agent(
        name="Inflation Irene",
        specialized_niche=Niche.INFLATION_DATA,
        capital_allocation=8000,
    )

    # Discover markets
    discovery = MarketDiscovery(
        min_volume=1000.0,
        max_resolution_days=30,
        min_liquidity_score=0.3,
    )

    print("\n[Discovering markets...]\n")

    all_markets = []
    for sector in [Sector.SPORTS, Sector.CRYPTO, Sector.POLITICS]:
        markets = await discovery.discover_markets(
            sectors=[sector],
            limit=50,
        )
        all_markets.extend(markets)

    print(f"Discovered {len(all_markets)} total markets")

    # Run trading cycle
    print("\n[Running trading cycle 1...]\n")

    # Distribute markets to agents
    agent_markets = await swarm.distribute_markets_to_agents(all_markets)

    print(f"Distributed markets to {len(agent_markets)} agents")

    # Execute trades
    trades = await swarm.execute_agent_trades(agent_markets)

    print(f"Executed {len(trades)} trades")

    # Update leaderboards
    await swarm.update_leaderboards()

    # Print summary
    swarm.print_swarm_summary()

    # Print leaderboards
    for niche in [Niche.CRYPTO_HOURLY, Niche.NBA_PLAYER_PROPS, Niche.PRESIDENTIAL_ELECTIONS]:
        if niche in swarm.leaderboards:
            swarm.print_leaderboard(niche, top_n=3)

    # Print agent details for top performer
    top_agent_id = None
    top_pnl = -float('inf')

    for agent_id, agent in swarm.agents.items():
        perf = agent.niche_performance.get(agent.specialized_niche)
        if perf and perf.total_profit_loss > top_pnl:
            top_pnl = perf.total_profit_loss
            top_agent_id = agent_id

    if top_agent_id:
        swarm.print_agent_details(top_agent_id)

    # Run additional cycles
    for cycle in range(2, 4):
        print(f"\n[Running trading cycle {cycle}...]\n")

        # Re-distribute markets
        agent_markets = await swarm.distribute_markets_to_agents(all_markets)

        # Execute trades
        trades = await swarm.execute_agent_trades(agent_markets)

        print(f"Executed {len(trades)} trades")

        # Update leaderboards
        await swarm.update_leaderboards()

        # Brief pause
        await asyncio.sleep(0.5)

    # Final summary
    swarm.print_swarm_summary()


if __name__ == "__main__":
    asyncio.run(main())
