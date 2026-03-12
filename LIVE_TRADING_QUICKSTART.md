# Live Trading System - Quick Start

## What Changed?

**NO MORE 90-DAY BACKTESTS.**

We now trade on **live prediction markets that resolve in hours/days**, not months.

## How It Works

```
Discover Markets → Make Predictions → Execute Trades → Track Resolutions → Validate
     (100s)              (ML model)        (real-time)     (hours/days)     (30+ trades)
```

### Key Difference

| Old System | New System |
|------------|-----------|
| 90-day backtest | Live market trading |
| Historical data | Real-time data |
| One market type | Multiple sectors |
| Slow validation | Fast validation (days) |

## Quick Start (5 Minutes)

### 1. Install Dependencies

```bash
cd ~/autoresearch_quant
pip install -r requirements.txt
```

### 2. Run Demo

```bash
# Market discovery demo
python3 market_discovery.py

# Live trading demo
python3 live_trading_engine.py

# Single agent demo
python3 live_trading_agent.py

# Swarm demo (multiple agents)
python3 live_trading_swarm.py
```

### 3. Run Production

```bash
# Single agent
python3 live_trading_agent.py

# Swarm (7 agents, 7 sectors)
python3 live_trading_swarm.py
```

## Validation Criteria (Live Data)

**30 resolved trades minimum.**

| Metric | Threshold |
|--------|-----------|
| Resolved Trades | 30+ |
| Win Rate | 55%+ |
| Sharpe Ratio | 0.5+ |
| Return | Positive |

**No waiting 90 days!** Most markets resolve in 1-7 days.

## Sector-Based Agents

Each agent specializes in a sector:

| Agent ID | Sector | Markets/Week | Resolution Time |
|----------|--------|---------------|-----------------|
| sports_agent_001 | Sports | 100+ | Hours to days |
| sports_agent_002 | Sports | 100+ | Hours to days |
| politics_agent | Politics | 20+ | Days to weeks |
| crypto_agent_001 | Crypto | 50+ | Hours to weeks |
| crypto_agent_002 | Crypto | 50+ | Hours to weeks |
| entertainment_agent | Entertainment | 30+ | Days to weeks |
| weather_agent | Weather | 10+ | Hours to days |

## Why This Works

### Speed
- **Old**: 90 days to validate
- **New**: 7-14 days to validate (30 trades across sectors)

### Diversity
- **Old**: Single market type
- **New**: 7 sectors, hundreds of markets

### Reality
- **Old**: Historical data (may not reflect current conditions)
- **New**: Live markets (current conditions)

### Volume
- **Old**: Limited to available historical data
- **New**: Hundreds of live markets daily

## Risk Management

### Per-Market Limits
- Maximum position: $500
- Minimum deviation: 5%
- Only trade liquid markets ($1,000+ volume)

### Sector Limits
- Max exposure per sector: $5,000
- Multiple agents per sector for diversification

### Portfolio Limits
- Max total exposure: $20,000
- Minimum 3 sectors for diversification

## File Structure

```
autoresearch_quant/
├── market_discovery.py        # Find live prediction markets
├── live_trading_engine.py     # Core trading logic
├── live_trading_agent.py     # Single sector-based agent
├── live_trading_swarm.py     # Multiple agents (swarm)
├── live_trading_system.md    # Design documentation
└── LIVE_TRADING_QUICKSTART.md # This file
```

## Monitoring

### Check Agent Status

```bash
# View trading state
cat demo_trader_trading_state.json

# View swarm state
cat swarm_state.json
```

### Key Metrics

- **Total PnL**: Overall profit/loss
- **Win Rate**: Percentage of winning trades
- **Sharpe**: Risk-adjusted returns
- **Resolved Trades**: Number of completed trades
- **Sector Performance**: PnL per sector

## Demo Output

```
MARKET DISCOVERY
Found 50 markets
Filtered to 42 liquid markets

SPORTS: 18 markets
  Chiefs vs 49ers: will win
    Volume: $3,450
    Liquidity: 0.34
    Odds: YES 52% / NO 48%
    Resolution: 24 hours

LIVE TRADING
Trade Executed:
  Market: Chiefs vs 49ers: will win
  Side: YES
  Size: $450.00
  Odds: 52% / 48%
  Internal: 58%
  Deviation: 6%

Position Resolved:
  Market: Chiefs vs 49ers: will win
  Side: YES
  Outcome: YES
  PnL: $86.54
  Return: 19.23%
  Capital: $10,086.54
```

## Next Steps

1. **Run demo**: `python3 live_trading_swarm.py`
2. **Review metrics**: Check win rate, PnL, Sharpe
3. **Validate**: Wait for 30 resolved trades
4. **Scale up**: Increase position sizes on validated agents
5. **Add sectors**: More sectors = more diversification

## Real Market APIs

To connect to real prediction markets, update `market_discovery.py`:

```python
async def discover_markets(self, sectors, limit):
    # Connect to Polymarket API
    async with aiohttp.ClientSession() as session:
        response = await session.get("https://api.polymarket.com/markets")
        markets_data = await response.json()
        # Parse and filter
        markets = self._parse_polymarket_data(markets_data)
        return markets
```

## Production Deployment

For real money trading:

1. **Connect APIs**: Polymarket, Kalshi, etc.
2. **Fund accounts**: Minimum $1,000 per agent
3. **Set up monitoring**: Real-time alerts
4. **Start small**: Begin with $10-50 per trade
5. **Scale up gradually**: Increase on validation
6. **Track everything**: Every trade, resolution, PnL

## Advantages Over Old System

✓ **Faster validation**: Days vs months
✓ **Real data**: Live markets vs historical
✓ **More opportunities**: Hundreds of markets
✓ **Sector diversification**: 7 sectors
✓ **Adaptive**: Real-time learning
✓ **Scalable**: Add more agents/sectors

## Key Files

- `market_discovery.py` - Find live markets
- `live_trading_engine.py` - Core trading logic
- `live_trading_agent.py` - Single agent
- `live_trading_swarm.py` - Multi-agent swarm
- `live_trading_system.md` - Full documentation

## Run Commands

```bash
# Single agent
python3 live_trading_agent.py

# Swarm (7 agents)
python3 live_trading_swarm.py

# Continuous mode (run forever)
# Add to agent code: await agent.run_continuous(check_interval_hours=1.0)
```

## Validation Timeline

```
Day 1-2:   Make 100 trades across 7 sectors
Day 3-7:   Markets start resolving
Day 7-10:   30+ trades resolved
Day 10+:    Agent validated, scale up
```

**Total: 10 days to validate (vs 90 days before)**

## Summary

**No more waiting 90 days.** Trade on live markets that resolve in hours/days, validate in 1-2 weeks, scale up profitable strategies.

**This is how real quant funds trade prediction markets.**
