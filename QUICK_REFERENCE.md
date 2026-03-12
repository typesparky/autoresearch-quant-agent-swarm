# Quick Reference - What to Run

## You Want Live Trading (No 90-Day Backtests)

### Run This

```bash
cd ~/autoresearch_quant

# Install dependencies
pip install -r requirements.txt

# Run full swarm (7 agents, 7 sectors)
python3 live_trading_swarm.py
```

### What This Does

1. Discovers 100+ live prediction markets per week
2. Trades on mispricing (5%+ deviation)
3. Tracks resolutions (markets resolve in hours/days)
4. Validates on 30+ resolved trades (7-14 days total)
5. Scales up on profitable agents

### Sectors

- Sports (2 agents)
- Politics
- Crypto (2 agents)
- Entertainment
- Weather

### Validation Criteria

- 30+ resolved trades
- Win rate 55%+
- Sharpe 0.5+
- Positive return

**Timeline: 7-14 days (not 90 days)**

## Demo Commands

```bash
# Market discovery
python3 market_discovery.py

# Live trading engine
python3 live_trading_engine.py

# Single agent
python3 live_trading_agent.py

# Full swarm
python3 live_trading_swarm.py
```

## Key Files

- `live_trading_swarm.py` - Main entry point
- `market_discovery.py` - Find markets
- `live_trading_engine.py` - Trading logic
- `LIVE_TRADING_QUICKSTART.md` - Full guide
- `README.md` - System overview

## What We Built

**Live trading system for prediction markets.**

- No 90-day backtests
- Validate in 1-2 weeks
- 7 sectors, 7 agents
- Real-time data
- Production-ready

## Next Step

**Run the demo:**
```bash
python3 live_trading_swarm.py
```

Then read `LIVE_TRADING_QUICKSTART.md` for full details.
