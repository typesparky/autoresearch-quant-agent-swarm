# Robust AutoResearch Quant - Quick Start Guide

## 5-Minute Setup

### 1. Install Dependencies

```bash
cd ~/autoresearch_quant
pip install -r requirements.txt
```

### 2. Run Demo (No API Key)

```bash
python3 robust_demo.py
```

This shows:
- Walk-forward backtesting
- Paper trading (shadow testing)
- Multi-objective optimization
- Full 5-stage validation pipeline

### 3. Run Production System

```bash
# Set your LLM API key
export LLM_API_KEY="sk-your-key-here"

# Run single agent
python3 robust_research_loop.py

# Or run multiple agents
./run_robust_swarm.sh
```

## What Makes This Different?

### Original System (What We Had Before)
- Blind iterations: generate → train → save (no validation)
- Basic backtesting (in-sample only)
- No shadow testing
- No statistical validation
- Immediate deployment (risky!)

### Robust System (What We Have Now)
- 5-stage validation pipeline
- Walk-forward analysis (out-of-sample only)
- 24h+ shadow testing (paper trading)
- Statistical significance testing
- Multi-objective optimization
- Gradual deployment (1% → 10%)

## Validation Pipeline (What Every Model Must Pass)

```
┌─────────────────────────────────────────────────────────────────┐
│  1. RESEARCH                                                      │
│     LLM generates strategy and writes code                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  2. BACKTESTING (Walk-Forward)                                   │
│     ✓ Sharpe > 1.0                                                │
│     ✓ Win Rate > 55%                                             │
│     ✓ Drawdown < 15%                                             │
│     ✓ 100+ trades, p < 0.05                                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  3. SHADOW TESTING (Paper Trading)                               │
│     ✓ 24h+ live data                                             │
│     ✓ 30+ resolved trades                                        │
│     ✓ Degradation < 20%                                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  4. SELECTION (Multi-Objective)                                 │
│     ✓ Weighted score > 0.4                                       │
│     ✓ Optimize: profit, risk, robustness                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  5. DEPLOYMENT (Gradual Rollout)                                 │
│     ✓ Start at 1% allocation                                    │
│     ✓ Scale up if performance holds                              │
│     ✓ Auto-disable on degradation                               │
└─────────────────────────────────────────────────────────────────┘
```

## Key Metrics

### What We Optimize For

**Profit:**
- Total PnL ($)
- Return %
- Average return per trade

**Risk:**
- Sharpe ratio (risk-adjusted returns)
- Max drawdown (peak-to-trough loss)
- Volatility (standard deviation)
- Tail risk (CVaR)

**Robustness:**
- Performance across market regimes
- Stability over time
- Win rate consistency

### Success Criteria

A model is deployable if it passes:

1. **Backtest:** Sharpe > 1.0, WR > 55%, DD < 15%, p < 0.05
2. **Shadow Test:** 24h+ trading, <20% degradation
3. **Selection:** Weighted score > 0.4

## Running Multiple Agents

### Simple (Background Processes)

```bash
export LLM_API_KEY="sk-your-key-here"
./run_robust_swarm.sh
```

This launches 3 agents by default. To customize:

```bash
NUM_AGENTS=5 MARKET_TYPE=crypto ./run_robust_swarm.sh
```

### Production (Systemd)

```bash
# Create service (see ROBUST_README.md)
sudo systemctl enable robust-autoresearch@quant_001
sudo systemctl start robust-autoresearch@quant_001
```

## Monitoring

### Check AgentHub Status

```bash
python3 -c "from agenthub_dag import AgentHubDAG; dag = AgentHubDAG(); dag.print_status()"
```

This shows:
- Total commits
- Active agents
- Consensus metrics
- Swarm divergence (polarity)

### View Agent Logs

```bash
tail -f logs/robust/robust_quant_001.log
```

### Check Validation Summaries

```bash
grep 'VALIDATION SUMMARY' logs/robust/robust_quant_*.log -A 20
```

## Common Issues

### Models Failing Backtesting?

**Check:**
- Using day-zero data (no historical leakage)
- Minimum 100 trades
- Statistical significance (p < 0.05)
- Meet minimum Sharpe, win rate, drawdown

**Fix:**
- Adjust criteria in `robust_research_loop.py`
- Increase training window
- Improve feature engineering

### Shadow Testing Degradation?

**Check:**
- Overfitting (in-sample vs out-of-sample gap)
- Market regime changes
- Data quality

**Fix:**
- Increase `min_trading_hours`
- Use more robust features
- Consider regularization

### No Models Passing Selection?

**Check:**
- Weighted score threshold too high?
- Objective weights appropriate?

**Fix:**
- Lower `min_weighted_score`
- Adjust `WEIGHT_PROFILES`
- Choose different risk profile

## Next Steps

1. **Run the demo** to see the system in action
2. **Customize config** in `robust_research_loop.py`
3. **Launch swarm** with your LLM API key
4. **Monitor performance** via AgentHub and logs
5. **Iterate** on strategies and validation criteria

## Documentation

- `ROBUST_README.md` - Full documentation
- `robust_system.md` - Design principles
- `ARCHITECTURE.md` - Technical architecture
- `USAGE.md` - Original usage guide

## Production Checklist

Before going live with real money:

- [ ] Run shadow testing for 30+ days
- [ ] Validate across multiple market regimes
- [ ] Set up monitoring and alerts
- [ ] Configure risk limits
- [ ] Test gradual rollout
- [ ] Set up database (PostgreSQL)
- [ ] Secure API keys
- [ ] Configure systemd services
- [ ] Set up backups
- [ ] Review regulatory requirements

## Support

The system is production-ready but complex. Start with the demo to understand each component, then deploy gradually with monitoring.

**Remember: No model trades real money until it passes ALL 5 validation stages.**
