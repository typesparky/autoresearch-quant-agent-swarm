#!/usr/bin/env python3
"""
Zero-Leakage Data Pipeline

Ensures all data is day-zero (post-training-cutoff) with contamination detection.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import aiohttp
import hashlib
import json


class ZeroLeakagePipeline:
    """Real-time data pipeline with zero-leakage guarantees."""

    def __init__(
        self,
        training_cutoff_date: str = "2024-01-01",  # Adjust based on LLM cutoff
        max_data_age_days: int = 30,
    ):
        self.training_cutoff = datetime.fromisoformat(training_cutoff_date)
        self.max_data_age = timedelta(days=max_data_age_days)

        # Data sources (real-time APIs)
        self.sources = {
            "crypto": [
                "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart",
                "https://api.binance.com/api/v3/ticker/24hr",
            ],
            "news": [
                "https://newsapi.org/v2/top-headlines",
                "https://cryptonews-api.com/api/v1/news",
            ],
            "sentiment": [
                "https://api.stocktwits.com/streams/symbol/BTC.X",
                "https://api.twitter.com/2/tweets/search/recent",
            ],
        }

    async def fetch_live_data(
        self,
        market_type: str,
        window_days: int = 7,
    ) -> Dict:
        """
        Fetch day-zero live data from multiple sources.

        Returns data with contamination metadata.
        """
        print(f"[Data Pipeline] Fetching {market_type} data...")

        # Fetch from all relevant sources
        sources = self._get_sources_for_market(market_type)

        all_data = []
        contamination_flags = []

        for source_url in sources:
            try:
                data = await self._fetch_source(source_url, window_days)
                all_data.extend(data)
            except Exception as e:
                print(f"[Warning] Failed to fetch {source_url}: {e}")
                contamination_flags.append(f"source_failure:{source_url}")

        # Validate zero-leakage
        is_day_zero, contamination_reason = self._validate_zero_leakage(all_data)

        if not is_day_zero:
            contamination_flags.append(contamination_reason)

        # Process into features
        features = self._extract_features(all_data, market_type)

        # Calculate metadata
        date_range = self._get_date_range(all_data)

        result = {
            "features": features,
            "is_day_zero": is_day_zero,
            "contamination_flags": contamination_flags,
            "date_range": date_range,
            "source_count": len(sources),
            "data_point_count": len(all_data),
            "fetched_at": datetime.now().isoformat(),
        }

        print(f"[Data Pipeline] Fetched {len(all_data)} data points")
        print(f"[Data Pipeline] Zero-leakage: {is_day_zero}")
        print(f"[Data Pipeline] Date range: {date_range}")

        return result

    def _get_sources_for_market(self, market_type: str) -> List[str]:
        """Get data sources for a given market type."""
        if market_type == "crypto":
            return self.sources["crypto"] + self.sources["news"] + self.sources["sentiment"]
        elif market_type == "stocks":
            return self.sources["news"] + self.sources["sentiment"]
        elif market_type == "sports":
            return ["https://api.the-odds-api.com/v4/sports/"]  # Placeholder
        else:
            return []

    async def _fetch_source(
        self,
        url: str,
        window_days: int,
    ) -> List[Dict]:
        """Fetch data from a single source."""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")

                data = await response.json()
                return self._normalize_source_data(data, url, window_days)

    def _normalize_source_data(
        self,
        raw_data: Dict,
        source_url: str,
        window_days: int,
    ) -> List[Dict]:
        """Normalize data from different sources to common format."""
        normalized = []

        # Coingecko format
        if "coingecko" in source_url:
            if "prices" in raw_data:
                for timestamp, price in raw_data["prices"]:
                    normalized.append({
                        "source": "coingecko",
                        "type": "price",
                        "timestamp": timestamp,
                        "value": price,
                        "symbol": "BTC",
                    })

        # Binance format
        elif "binance" in source_url:
            if isinstance(raw_data, list):
                for ticker in raw_data:
                    normalized.append({
                        "source": "binance",
                        "type": "ticker",
                        "timestamp": int(datetime.now().timestamp() * 1000),
                        "symbol": ticker.get("symbol"),
                        "price": float(ticker.get("lastPrice", 0)),
                        "volume": float(ticker.get("volume", 0)),
                    })

        # News API format
        elif "newsapi" in source_url:
            if "articles" in raw_data:
                for article in raw_data["articles"][:50]:  # Limit to 50 articles
                    normalized.append({
                        "source": "newsapi",
                        "type": "news",
                        "timestamp": self._parse_date(article.get("publishedAt")),
                        "title": article.get("title"),
                        "description": article.get("description"),
                        "url": article.get("url"),
                    })

        return normalized

    def _parse_date(self, date_str: Optional[str]) -> Optional[int]:
        """Parse date string to timestamp."""
        if not date_str:
            return None
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return int(dt.timestamp() * 1000)
        except:
            return None

    def _validate_zero_leakage(self, data: List[Dict]) -> tuple[bool, str]:
        """
        Validate that all data is day-zero (post-training-cutoff).

        Returns (is_valid, contamination_reason).
        """
        if not data:
            return False, "no_data"

        # Check timestamps
        min_timestamp = min(
            d.get("timestamp") for d in data if d.get("timestamp")
        )

        # Find earliest data point
        earliest_date = datetime.fromtimestamp(min_timestamp / 1000)

        # Check against training cutoff
        if earliest_date < self.training_cutoff:
            return False, f"pre_cutoff_data:{earliest_date.date()}"

        # Check data age
        now = datetime.now()
        if now - earliest_date > self.max_data_age:
            return False, f"stale_data:{(now - earliest_date).days} days"

        return True, "ok"

    def _extract_features(
        self,
        data: List[Dict],
        market_type: str,
    ) -> List[Dict]:
        """Extract ML-ready features from raw data."""
        features = []

        for item in data:
            feature = {
                "source": item.get("source"),
                "type": item.get("type"),
                "timestamp": item.get("timestamp"),
            }

            # Extract type-specific features
            if item.get("type") == "price":
                feature["price"] = item.get("value")
                feature["symbol"] = item.get("symbol")

            elif item.get("type") == "ticker":
                feature["price"] = item.get("price")
                feature["volume"] = item.get("volume")
                feature["symbol"] = item.get("symbol")

            elif item.get("type") == "news":
                # Text features
                title = item.get("title", "")
                description = item.get("description", "")

                feature["title"] = title
                feature["description"] = description
                feature["title_length"] = len(title)
                feature["description_length"] = len(description)

                # Simple sentiment (placeholder - use real sentiment analysis)
                feature["sentiment_score"] = self._simple_sentiment(title + description)

            features.append(feature)

        return features

    def _simple_sentiment(self, text: str) -> float:
        """Simple sentiment scoring (placeholder)."""
        positive_words = ["up", "good", "positive", "gain", "bull", "rise"]
        negative_words = ["down", "bad", "negative", "loss", "bear", "fall"]

        text_lower = text.lower()

        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        if positive_count + negative_count == 0:
            return 0.0

        return (positive_count - negative_count) / (positive_count + negative_count)

    def _get_date_range(self, data: List[Dict]) -> str:
        """Get date range of data."""
        timestamps = [d.get("timestamp") for d in data if d.get("timestamp")]

        if not timestamps:
            return "no_data"

        min_ts = min(timestamps)
        max_ts = max(timestamps)

        min_date = datetime.fromtimestamp(min_ts / 1000).date()
        max_date = datetime.fromtimestamp(max_ts / 1000).date()

        return f"{min_date} to {max_date}"
