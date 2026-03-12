#!/usr/bin/env python3
"""
Market Executor

Executes trades when market odds deviate from agent's internal probability.
Implements dynamic pricing and position sizing.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional
import pickle


class MarketExecutor:
    """
    Execute trades on prediction markets.

    Each agent:
    1. Generates internal probability using their model
    2. Fetches current market odds
    3. Trades when deviation exceeds threshold
    4. Manages position sizing and risk
    """

    def __init__(
        self,
        agent_id: str,
        initial_capital: float = 10000,
        max_position_size: float = 0.05,  # 5% of portfolio
        min_deviation: float = 0.05,  # 5% deviation required to trade
        stop_loss: float = 0.02,  # 2% stop loss
        take_profit: float = 0.05,  # 5% take profit
    ):
        self.agent_id = agent_id
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.max_position_size = max_position_size
        self.min_deviation = min_deviation
        self.stop_loss = stop_loss
        self.take_profit = take_profit

        # Position tracking
        self.positions: Dict[str, Dict] = {}  # symbol -> position
        self.trade_history: List[Dict] = []

    def calculate_internal_probability(
        self,
        model_path: str,
        features: Dict,
    ) -> float:
        """
        Calculate internal probability using trained model.

        Args:
            model_path: Path to saved model
            features: Feature dict for current market state

        Returns:
            probability: Internal probability (0-1)
        """
        # Load model
        with open(model_path, "rb") as f:
            model = pickle.load(f)

        # Prepare features (simplified)
        import numpy as np
        feature_array = np.array([[
            features.get("price", 0),
            features.get("volume", 0),
            features.get("sentiment_score", 0),
            features.get("price_change_1h", 0),
            features.get("price_change_24h", 0),
        ]])

        # Get prediction
        probability = model.predict(feature_array)[0]

        # Clip to valid probability range
        probability = max(0.01, min(0.99, probability))

        return probability

    async def fetch_market_odds(self, symbol: str) -> Dict:
        """
        Fetch current market odds for a symbol.

        Returns:
            odds: {yes_odds: float, no_odds: float, liquidity: float}
        """
        # Placeholder: Implement actual market API call
        # This would connect to Polymarket, Hyperliquid, or other prediction markets

        # Simulated market odds
        return {
            "yes_odds": 0.52,
            "no_odds": 0.48,
            "liquidity": 100000,
            "timestamp": datetime.now().isoformat(),
        }

    def calculate_position_size(
        self,
        confidence: float,
        current_capital: float,
    ) -> float:
        """
        Calculate position size based on confidence.

        More confident trades get larger positions (up to max_position_size).
        """
        # Base position size
        base_size = current_capital * self.max_position_size

        # Scale by confidence (0.5 to 1.5x)
        confidence_factor = 0.5 + confidence  # 0.5 to 1.5
        position_size = base_size * confidence_factor

        return position_size

    def check_trade_opportunity(
        self,
        internal_prob: float,
        market_odds: Dict,
    ) -> Optional[Dict]:
        """
        Check if there's a profitable trading opportunity.

        Returns trade details if deviation exceeds threshold, None otherwise.
        """
        market_yes = market_odds["yes_odds"]
        market_no = market_odds["no_odds"]

        # Calculate deviations
        yes_deviation = abs(internal_prob - market_yes)
        no_deviation = abs((1 - internal_prob) - market_no)

        # Determine best side to trade
        if yes_deviation >= self.min_deviation and internal_prob > market_yes:
            # Bet on YES (market undervalues)
            return {
                "side": "YES",
                "internal_prob": internal_prob,
                "market_prob": market_yes,
                "deviation": yes_deviation,
                "expected_edge": internal_prob - market_yes,
                "action": "buy",
            }

        elif no_deviation >= self.min_deviation and (1 - internal_prob) > market_no:
            # Bet on NO (market undervalues)
            return {
                "side": "NO",
                "internal_prob": 1 - internal_prob,
                "market_prob": market_no,
                "deviation": no_deviation,
                "expected_edge": (1 - internal_prob) - market_no,
                "action": "buy",
            }

        return None

    async def execute_trade(
        self,
        symbol: str,
        trade_details: Dict,
    ) -> Dict:
        """
        Execute a trade.

        Returns trade result.
        """
        # Calculate position size
        position_size = self.calculate_position_size(
            confidence=trade_details["expected_edge"] / trade_details["deviation"],
            current_capital=self.capital,
        )

        # Create position
        position = {
            "symbol": symbol,
            "side": trade_details["side"],
            "size": position_size,
            "entry_price": trade_details["market_prob"],
            "internal_prob": trade_details["internal_prob"],
            "expected_edge": trade_details["expected_edge"],
            "entry_time": datetime.now().isoformat(),
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
        }

        self.positions[symbol] = position

        # Record trade
        trade = {
            **position,
            "type": "open",
            "agent_id": self.agent_id,
        }
        self.trade_history.append(trade)

        print(f"\n[Trade Executed]")
        print(f"  Symbol:     {symbol}")
        print(f"  Side:       {trade_details['side']}")
        print(f"  Size:       ${position_size:.2f}")
        print(f"  Entry:      {trade_details['market_prob']:.2%}")
        print(f"  Internal:   {trade_details['internal_prob']:.2%}")
        print(f"  Edge:       {trade_details['expected_edge']:.2%}")

        return trade

    def close_position(
        self,
        symbol: str,
        exit_price: float,
        reason: str,
    ) -> Dict:
        """
        Close an existing position.

        Returns trade result with PnL.
        """
        if symbol not in self.positions:
            raise ValueError(f"No position in {symbol}")

        position = self.positions[symbol]

        # Calculate PnL
        if position["side"] == "YES":
            pnl = position["size"] * (exit_price - position["entry_price"])
        else:
            pnl = position["size"] * (position["entry_price"] - exit_price)

        # Update capital
        self.capital += pnl

        # Record trade
        trade = {
            "symbol": symbol,
            "side": position["side"],
            "size": position["size"],
            "entry_price": position["entry_price"],
            "exit_price": exit_price,
            "pnl": pnl,
            "exit_time": datetime.now().isoformat(),
            "exit_reason": reason,
            "type": "close",
            "agent_id": self.agent_id,
        }
        self.trade_history.append(trade)

        # Remove position
        del self.positions[symbol]

        print(f"\n[Position Closed]")
        print(f"  Symbol:     {symbol}")
        print(f"  Exit:       {exit_price:.2%}")
        print(f"  PnL:        ${pnl:.2f}")
        print(f"  Reason:     {reason}")

        return trade

    async def manage_positions(self):
        """
        Check open positions for stop-loss or take-profit.

        Close positions that hit risk management thresholds.
        """
        for symbol, position in list(self.positions.items()):
            # Fetch current price
            market_odds = await self.fetch_market_odds(symbol)
            current_price = market_odds["yes_odds"] if position["side"] == "YES" else market_odds["no_odds"]

            # Calculate PnL percentage
            if position["side"] == "YES":
                pnl_pct = (current_price - position["entry_price"]) / position["entry_price"]
            else:
                pnl_pct = (position["entry_price"] - current_price) / position["entry_price"]

            # Check stop-loss
            if pnl_pct <= -position["stop_loss"]:
                self.close_position(symbol, current_price, "stop_loss")

            # Check take-profit
            elif pnl_pct >= position["take_profit"]:
                self.close_position(symbol, current_price, "take_profit")

    async def run_trading_loop(
        self,
        model_path: str,
        symbols: List[str],
        interval_seconds: int = 60,
    ):
        """
        Run continuous trading loop.

        Args:
            model_path: Path to trained model
            symbols: List of symbols to trade
            interval_seconds: Time between checks
        """
        print(f"\n{'='*60}")
        print(f"Starting Trading Loop for {self.agent_id}")
        print(f"Symbols: {symbols}")
        print(f"Initial Capital: ${self.capital:.2f}")
        print(f"{'='*60}\n")

        while True:
            # Manage existing positions
            await self.manage_positions()

            # Check for new opportunities
            for symbol in symbols:
                # Fetch market odds
                market_odds = await self.fetch_market_odds(symbol)

                # Skip if already have position
                if symbol in self.positions:
                    continue

                # Get features (placeholder)
                features = {
                    "price": 50000,
                    "volume": 1000000,
                    "sentiment_score": 0.3,
                    "price_change_1h": 0.01,
                    "price_change_24h": 0.02,
                }

                # Calculate internal probability
                internal_prob = self.calculate_internal_probability(
                    model_path,
                    features,
                )

                # Check for trade opportunity
                trade_details = self.check_trade_opportunity(
                    internal_prob,
                    market_odds,
                )

                if trade_details:
                    await self.execute_trade(symbol, trade_details)

            # Wait before next iteration
            await asyncio.sleep(interval_seconds)

    def get_performance_summary(self) -> Dict:
        """Get performance summary."""
        if not self.trade_history:
            return {
                "total_trades": 0,
                "total_pnl": 0,
                "capital": self.capital,
                "return_pct": 0,
            }

        # Calculate metrics
        closed_trades = [t for t in self.trade_history if t["type"] == "close"]
        total_pnl = sum(t["pnl"] for t in closed_trades)

        winning_trades = [t for t in closed_trades if t["pnl"] > 0]
        win_rate = len(winning_trades) / len(closed_trades) if closed_trades else 0

        return {
            "total_trades": len(closed_trades),
            "winning_trades": len(winning_trades),
            "losing_trades": len(closed_trades) - len(winning_trades),
            "win_rate": win_rate,
            "total_pnl": total_pnl,
            "capital": self.capital,
            "return_pct": (self.capital - self.initial_capital) / self.initial_capital,
            "open_positions": len(self.positions),
        }
