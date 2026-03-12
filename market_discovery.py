#!/usr/bin/env python3
"""
Market Discovery - Find live prediction markets.

Connects to prediction market APIs to discover markets, filter by liquidity,
and categorize by sector.
"""

import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
import json


class Sector(Enum):
    """Market sectors."""
    SPORTS = "sports"
    POLITICS = "politics"
    CRYPTO = "crypto"
    ENTERTAINMENT = "entertainment"
    WEATHER = "weather"
    ECONOMICS = "economics"
    TECHNOLOGY = "technology"
    OTHER = "other"


@dataclass
class Market:
    """Prediction market."""
    market_id: str
    title: str
    description: str
    sector: Sector
    resolution_time: datetime
    minimum_volume: float  # Minimum trading volume
    current_volume: float  # Current volume
    liquidity_score: float  # 0-1 based on volume + depth
    yes_odds: float
    no_odds: float
    url: str
    created_at: datetime

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        d = asdict(self)
        d['sector'] = d['sector'].value
        d['resolution_time'] = d['resolution_time'].isoformat()
        d['created_at'] = d['created_at'].isoformat()
        return d


class MarketDiscovery:
    """
    Discover and filter prediction markets.

    In production, connect to real APIs (Polymarket, etc.).
    For demo, generate realistic synthetic markets.
    """

    def __init__(
        self,
        min_volume: float = 1000.0,
        max_resolution_days: int = 30,
        min_liquidity_score: float = 0.3,
    ):
        self.min_volume = min_volume
        self.max_resolution_days = max_resolution_days
        self.min_liquidity_score = min_liquidity_score

        # API configuration (placeholder)
        self.apis = {
            "polymarket": "https://api.polymarket.com/markets",
            # Add other prediction market APIs as needed
        }

    async def discover_markets(
        self,
        sectors: Optional[List[Sector]] = None,
        limit: int = 100,
    ) -> List[Market]:
        """
        Discover live prediction markets.

        Returns markets filtered by liquidity and resolution time.
        """
        if sectors is None:
            sectors = list(Sector)

        print(f"\n[Discovery] Finding live markets...")
        print(f"  Sectors: {', '.join(s.value for s in sectors)}")
        print(f"  Min volume: ${self.min_volume}")
        print(f"  Max resolution: {self.max_resolution_days} days")
        print(f"  Min liquidity score: {self.min_liquidity_score}")

        # In production: Fetch from real APIs
        # For demo: Generate synthetic markets
        markets = await self._generate_synthetic_markets(sectors, limit)

        # Filter by criteria
        filtered_markets = self._filter_markets(markets)

        print(f"\n[Discovery] Found {len(markets)} total markets")
        print(f"[Discovery] Filtered to {len(filtered_markets)} liquid markets")

        return filtered_markets

    async def _generate_synthetic_markets(
        self,
        sectors: List[Sector],
        limit: int,
    ) -> List[Market]:
        """Generate realistic synthetic markets for demo."""
        import random

        markets = []

        # Synthetic market generators by sector
        generators = {
            Sector.SPORTS: self._generate_sports_markets,
            Sector.POLITICS: self._generate_politics_markets,
            Sector.CRYPTO: self._generate_crypto_markets,
            Sector.ENTERTAINMENT: self._generate_entertainment_markets,
            Sector.WEATHER: self._generate_weather_markets,
        }

        for sector in sectors:
            if sector in generators:
                sector_markets = generators[sector](limit // len(sectors))
                markets.extend(sector_markets)

        return markets[:limit]

    def _generate_sports_markets(self, count: int) -> List[Market]:
        """Generate synthetic sports markets."""
        import random

        teams = [
            ("Chiefs", "49ers"), ("Eagles", "Cowboys"), ("Bills", "Dolphins"),
            ("Lakers", "Celtics"), ("Warriors", "Bucks"), ("Suns", "Mavericks"),
            ("Yankees", "Red Sox"), ("Dodgers", "Giants"), ("Braves", "Phillies"),
        ]

        event_types = ["will win", "will cover spread", "will go over total"]

        markets = []
        for i in range(count):
            team1, team2 = random.choice(teams)
            event = random.choice(event_types)

            resolution_hours = random.choice([1, 3, 6, 12, 24, 48, 72, 168])  # 1h to 7d
            resolution_time = datetime.now() + timedelta(hours=resolution_hours)

            volume = random.lognormvariate(8, 1.5)  # Mean $3,000
            yes_odds = random.uniform(0.3, 0.7)
            no_odds = 1.0 - yes_odds

            liquidity_score = min(1.0, volume / 10000.0)

            markets.append(Market(
                market_id=f"sports_{i}",
                title=f"{team1} vs {team2}: {event}",
                description=f"{team1} {event} against {team2}",
                sector=Sector.SPORTS,
                resolution_time=resolution_time,
                minimum_volume=self.min_volume,
                current_volume=volume,
                liquidity_score=liquidity_score,
                yes_odds=yes_odds,
                no_odds=no_odds,
                url=f"https://example.com/sports/{i}",
                created_at=datetime.now(),
            ))

        return markets

    def _generate_politics_markets(self, count: int) -> List[Market]:
        """Generate synthetic politics markets."""
        import random

        events = [
            "Candidate X will win primary",
            "Bill will pass congress",
            "Election turnout will exceed 60%",
            "Candidate Y will resign",
            "Poll will show >50% support",
        ]

        markets = []
        for i in range(count):
            event = random.choice(events)

            resolution_hours = random.choice([24, 72, 168, 336, 672])  # 1d to 28d
            resolution_time = datetime.now() + timedelta(hours=resolution_hours)

            volume = random.lognormvariate(7, 1.2)  # Mean $1,100
            yes_odds = random.uniform(0.25, 0.75)
            no_odds = 1.0 - yes_odds

            liquidity_score = min(1.0, volume / 5000.0)

            markets.append(Market(
                market_id=f"politics_{i}",
                title=f"Politics: {event}",
                description=event,
                sector=Sector.POLITICS,
                resolution_time=resolution_time,
                minimum_volume=self.min_volume,
                current_volume=volume,
                liquidity_score=liquidity_score,
                yes_odds=yes_odds,
                no_odds=no_odds,
                url=f"https://example.com/politics/{i}",
                created_at=datetime.now(),
            ))

        return markets

    def _generate_crypto_markets(self, count: int) -> List[Market]:
        """Generate synthetic crypto markets."""
        import random

        events = [
            "BTC > $60,000 by end of day",
            "ETH > $4,000 by Friday",
            "SOL > $200 in 7 days",
            "Crypto bill will pass Senate",
            "Bitcoin ETF approval by SEC",
            "Regulation announcement this week",
        ]

        markets = []
        for i in range(count):
            event = random.choice(events)

            resolution_hours = random.choice([6, 12, 24, 48, 168, 336])  # 6h to 14d
            resolution_time = datetime.now() + timedelta(hours=resolution_hours)

            volume = random.lognormvariate(8, 1.3)  # Mean $3,000
            yes_odds = random.uniform(0.35, 0.65)
            no_odds = 1.0 - yes_odds

            liquidity_score = min(1.0, volume / 8000.0)

            markets.append(Market(
                market_id=f"crypto_{i}",
                title=f"Crypto: {event}",
                description=event,
                sector=Sector.CRYPTO,
                resolution_time=resolution_time,
                minimum_volume=self.min_volume,
                current_volume=volume,
                liquidity_score=liquidity_score,
                yes_odds=yes_odds,
                no_odds=no_odds,
                url=f"https://example.com/crypto/{i}",
                created_at=datetime.now(),
            ))

        return markets

    def _generate_entertainment_markets(self, count: int) -> List[Market]:
        """Generate synthetic entertainment markets."""
        import random

        events = [
            "Movie X will open > $100M",
            "TV show Y will have >10M viewers",
            "Artist Z will win award",
            "Album will debut at #1",
            "Streaming show will be renewed",
        ]

        markets = []
        for i in range(count):
            event = random.choice(events)

            resolution_hours = random.choice([24, 72, 168, 336])  # 1d to 14d
            resolution_time = datetime.now() + timedelta(hours=resolution_hours)

            volume = random.lognormvariate(7.5, 1.2)  # Mean $1,800
            yes_odds = random.uniform(0.3, 0.7)
            no_odds = 1.0 - yes_odds

            liquidity_score = min(1.0, volume / 6000.0)

            markets.append(Market(
                market_id=f"entertainment_{i}",
                title=f"Entertainment: {event}",
                description=event,
                sector=Sector.ENTERTAINMENT,
                resolution_time=resolution_time,
                minimum_volume=self.min_volume,
                current_volume=volume,
                liquidity_score=liquidity_score,
                yes_odds=yes_odds,
                no_odds=no_odds,
                url=f"https://example.com/entertainment/{i}",
                created_at=datetime.now(),
            ))

        return markets

    def _generate_weather_markets(self, count: int) -> List[Market]:
        """Generate synthetic weather markets."""
        import random

        cities = ["New York", "Los Angeles", "Chicago", "Miami", "Seattle"]
        events = [
            "Temperature > 80°F",
            "Rainfall > 0.5 inches",
            "Snowfall > 2 inches",
            "Wind speed > 30 mph",
        ]

        markets = []
        for i in range(count):
            city = random.choice(cities)
            event = random.choice(events)

            resolution_hours = random.choice([6, 12, 24, 48, 72])  # 6h to 3d
            resolution_time = datetime.now() + timedelta(hours=resolution_hours)

            volume = random.lognormvariate(6.5, 1.0)  # Mean $665
            yes_odds = random.uniform(0.2, 0.8)
            no_odds = 1.0 - yes_odds

            liquidity_score = min(1.0, volume / 3000.0)

            markets.append(Market(
                market_id=f"weather_{i}",
                title=f"{city} Weather: {event}",
                description=f"{city} will experience {event}",
                sector=Sector.WEATHER,
                resolution_time=resolution_time,
                minimum_volume=self.min_volume,
                current_volume=volume,
                liquidity_score=liquidity_score,
                yes_odds=yes_odds,
                no_odds=no_odds,
                url=f"https://example.com/weather/{i}",
                created_at=datetime.now(),
            ))

        return markets

    def _filter_markets(self, markets: List[Market]) -> List[Market]:
        """Filter markets by criteria."""
        filtered = []

        now = datetime.now()
        max_resolution_time = now + timedelta(days=self.max_resolution_days)

        for market in markets:
            # Filter by volume
            if market.current_volume < self.min_volume:
                continue

            # Filter by resolution time
            if market.resolution_time > max_resolution_time:
                continue

            # Filter by liquidity
            if market.liquidity_score < self.min_liquidity_score:
                continue

            filtered.append(market)

        # Sort by liquidity (highest first)
        filtered.sort(key=lambda m: m.liquidity_score, reverse=True)

        return filtered

    def print_markets(self, markets: List[Market], limit: int = 20):
        """Print discovered markets."""
        print(f"\n{'='*80}")
        print(f"LIVE PREDICTION MARKETS ({len(markets)} total)")
        print(f"{'='*80}")

        # Group by sector
        by_sector = {}
        for market in markets:
            sector = market.sector
            if sector not in by_sector:
                by_sector[sector] = []
            by_sector[sector].append(market)

        for sector, sector_markets in sorted(by_sector.items(), key=lambda x: x[0].value):
            print(f"\n{sector.value.upper()}: {len(sector_markets)} markets")
            print(f"{'-'*80}")

            for market in sector_markets[:limit]:
                resolution_hours = (market.resolution_time - datetime.now()).total_seconds() / 3600
                print(f"\n  {market.title}")
                print(f"    Volume:     ${market.current_volume:,.0f}")
                print(f"    Liquidity:  {market.liquidity_score:.2f}")
                print(f"    Odds:       YES {market.yes_odds:.2%} / NO {market.no_odds:.2%}")
                print(f"    Resolution: {resolution_hours:.1f} hours")

        print(f"\n{'='*80}\n")


async def main():
    """Demo market discovery."""
    print("\n" + "="*80)
    print("MARKET DISCOVERY - Find Live Prediction Markets")
    print("="*80 + "\n")

    discovery = MarketDiscovery(
        min_volume=1000.0,
        max_resolution_days=30,
        min_liquidity_score=0.3,
    )

    # Discover markets
    markets = await discovery.discover_markets(limit=50)

    # Print results
    discovery.print_markets(markets)

    print(f"\nTop 10 Markets by Liquidity:")
    print(f"{'-'*80}")

    for i, market in enumerate(markets[:10]):
        print(f"\n{i+1}. {market.title}")
        print(f"   Sector:     {market.sector.value}")
        print(f"   Volume:     ${market.current_volume:,.0f}")
        print(f"   Liquidity:  {market.liquidity_score:.2f}")
        print(f"   Odds:       YES {market.yes_odds:.2%} / NO {market.no_odds:.2%}")

    # Save to JSON
    output_file = "discovered_markets.json"
    with open(output_file, 'w') as f:
        json.dump([m.to_dict() for m in markets], f, indent=2, default=str)

    print(f"\nSaved {len(markets)} markets to {output_file}\n")


if __name__ == "__main__":
    asyncio.run(main())
