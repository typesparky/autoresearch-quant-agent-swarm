# Robust AutoResearch Quant System - Production-Ready Trading Agent Swarm

## Overview

A production-grade autonomous quant research system that **only deploys models that pass rigorous validation**. Every model must prove itself through:

1. **Research Phase** - Generate and test strategies
2. **Backtesting Phase** - Walk-forward analysis with statistical validation
3. **Shadow Testing Phase** - Paper trading on live data (24h+)
4. **Selection Phase** - Multi-objective optimization
5. **Deployment Phase** - Gradual rollout with monitoring

**NO BLIND ITERATIONS** - Every model is validated before any commitment.

## Key Principles

### Zero-Leakage Guarantee
- All training data is day-zero (post-training-cutoff)
- Strict temporal splits (no lookahead bias)
- Contamination detection and rejection

### Statistical Validation
- Walk-forward analysis (rolling window backtest)
- Minimum 100 trades for significance
- 95% confidence level t-tests
- Multi-regime testing

### Multi-Objective Optimization
Optimize across conflicting objectives:
- **Maximize Profit** - Total PnL and returns
- **Minimize Volatility** - Lower drawdown, smoother equity curve
- **Maximize Sharpe Ratio** - Risk-adjusted returns
- **Minimize Tail Risk** - CVaR and downside protection
- **Maximize Robustness** - Performance across market regimes

### Gradual Deployment
- Start with 1% allocation
- Scale up only if performance holds
- Auto-disable on degradation
- Continuous monitoring

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    ROBUST AUTORESEARCH LOOP                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Phase 1: Research                                              │
│  - LLM generates research plan                                  │
│  - Writes model training code                                   │
│  - Explores new strategies                                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓ (if code generated)
┌─────────────────────────────────────────────────────────────────┐
│  Phase 2: Backtesting (Walk-Forward Analysis)                  │
│  - Train on historical data (90 days)                           │
│  - Test on rolling windows (30 days each)                      │
│  - Statistical significance testing                             │
│  - Multi-regime validation                                      │
│  - Minimum criteria: Sharpe > 1.0, Win Rate > 55%, DD < 15%   │
└─────────────────────────────────────────────────────────────────┘
                              ↓ (if statistically significant)
┌─────────────────────────────────────────────────────────────────┐
│  Phase 3: Shadow Testing (Paper Trading)                       │
│  - Run on live data (no real money)                             │
│  - Minimum 24 hours of trading                                 │
│  - Monitor for performance degradation                          │
│  - Real-time PnL tracking                                       │
│  - Validate: Sharpe, Win Rate, Degradation < 20%               │
└─────────────────────────────────────────────────────────────────┘
                              ↓ (if performance holds)
┌─────────────────────────────────────────────────────────────────┐
│  Phase 4: Selection (Multi-Objective Optimization)              │
│  - Calculate objective scores (profit, risk, robustness)       │
│  - Weighted composite score                                     │
│  - Pareto frontier analysis                                     │
│  - Compare against swarm consensus                              │
│  - Minimum weighted score: 0.4                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓ (if score meets threshold)
┌─────────────────────────────────────────────────────────────────┐
│  Phase 5: Deployment (Gradual Rollout)                          │
│  - Deploy with 1% initial allocation                            │
│  - Monitor performance in real-time                              │
│  - Scale up 2x if 5% gain sustained                             │
│  - Max allocation: 10%                                          │
│  - Auto-disable on degradation                                  │
│  - Commit to AgentHub DAG                                       │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Install Dependencies

```bash
cd ~/autoresearch_quant
pip install -r requirements.txt
```

### 2. Run Demo (No API Key Required)

The demo shows all components without requiring actual API keys:

```bash
# Backtesting demo
python3 backtesting_engine.py

# Shadow testing demo
python3 shadow_testing.py

# Multi-objective optimization demo
python3 multi_objective_optimizer.py

# Full robust research loop demo
python3 robust_research_loop.py
```

### 3. Run Production System

Set your LLM API key and run the robust research loop:

```bash
# Single agent
LLM_API_KEY=sk-your-key-here AGENT_ID=quant_001 MARKET_TYPE=crypto \
    python3 robust_research_loop.py

# Run with 3 agents (background processes)
LLM_API_KEY=sk-your-key-here ./run_robust_swarm.sh
```

## Validation Criteria

### Backtesting (Phase 2)

| Metric | Minimum | Description |
|--------|---------|-------------|
| Sharpe Ratio | 1.0 | Risk-adjusted returns |
| Win Rate | 55% | Winning trade percentage |
| Max Drawdown | 15% | Maximum peak-to-trough loss |
| Trades | 100 | Minimum for significance |
| P-Value | < 0.05 | Statistical significance |

### Shadow Testing (Phase 3)

| Metric | Minimum | Description |
|--------|---------|-------------|
| Trading Hours | 24 | Minimum live trading time |
| Resolved Trades | 30 | Minimum completed trades |
| Sharpe Ratio | 0.8* | 80% of backtest Sharpe (allow degradation) |
| Win Rate | 49.5%* | 90% of backtest win rate |
| Degradation | < 20% | Maximum performance drop |

*Adjusted from backtest baseline

### Selection (Phase 4)

| Objective | Weight | Description |
|-----------|--------|-------------|
| Profit | 30% | Total PnL and returns |
| Volatility | 20% | Lower is better |
| Sharpe | 25% | Risk-adjusted returns |
| Drawdown | 10% | Lower is better |
| Win Rate | 5% | Higher is better |
| Tail Risk | 5% | Lower is better |
| Robustness | 5% | Regime stability |

**Minimum weighted score: 0.4**

## Configuration

### Customizing Validation Thresholds

Edit `robust_research_loop.py` to adjust criteria:

```python
config = {
    'backtest': {
        'train_window_days': 90,
        'test_window_days': 30,
        'min_trades': 100,
        'confidence_level': 0.95,
        'min_sharpe': 1.0,
        'min_win_rate': 0.55,
        'max_drawdown': 0.15,
    },
    'shadow_test': {
        'min_trading_hours': 24,
        'max_degradation_pct': 0.20,
        'min_trades': 30,
    },
    'optimization': {
        'weights': WEIGHT_PROFILES['balanced'],  # or 'aggressive', 'conservative'
        'min_weighted_score': 0.4,
    },
    'deployment': {
        'initial_allocation_pct': 0.01,
        'scale_up_threshold': 0.05,
        'scale_up_factor': 2.0,
        'max_allocation_pct': 0.10,
    },
}
```

### Risk Profiles

Choose weight profiles based on your risk tolerance:

```python
from multi_objective_optimizer import WEIGHT_PROFILES

# Aggressive: Maximize profit, accept higher risk
weights = WEIGHT_PROFILES['aggressive']

# Balanced: Trade-off between profit and risk (default)
weights = WEIGHT_PROFILES['balanced']

# Conservative: Minimize risk, accept lower returns
weights = WEIGHT_PROFILES['conservative']
```

## Monitoring

### Check AgentHub Status

```python
from agenthub_dag import AgentHubDAG

dag = AgentHubDAG()
dag.print_status()
```

### View Detailed Results

```python
from robust_research_loop import RobustResearchLoop

# Load agent configuration
agent_path = "agents/quant_001/config.yaml"
with open(agent_path) as f:
    config = yaml.safe_load(f)

# Print validation summary
# (This would be stored in experiment directories)
```

### Real-time Performance

Shadow testing provides real-time feedback:

```python
from shadow_testing import ShadowTester

tester = ShadowTester(model_path="model.pkl")
tester.start()
# ... run ...
tester.print_status()
```

## Running Multiple Agents

### Background Processes (Simplest)

```bash
LLM_API_KEY=sk-your-key-here NUM_AGENTS=3 ./run_robust_swarm.sh
```

### Systemd Services (Production)

Create `/etc/systemd/system/robust-autoresearch@.service`:

```ini
[Unit]
Description=Robust AutoResearch Agent %i
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/home/your-user/autoresearch_quant
Environment=AGENT_ID=%i
Environment=MARKET_TYPE=crypto
Environment=LLM_API_KEY=your-api-key
ExecStart=/usr/bin/python3 robust_research_loop.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable robust-autoresearch@quant_001
sudo systemctl start robust-autoresearch@quant_001
sudo systemctl start robust-autoresearch@quant_002
sudo systemctl start robust-autoresearch@quant_003
```

## Architecture Comparison

### Original vs Robust System

| Aspect | Original | Robust System |
|--------|----------|---------------|
| Validation | None | 5-stage pipeline |
| Backtesting | Basic in-sample | Walk-forward analysis |
| Statistical Tests | No | Yes (t-tests, significance) |
| Shadow Testing | No | Yes (24h+ paper trading) |
| Objective Optimization | Single (Sharpe) | Multi-objective (7 metrics) |
| Deployment | Immediate | Gradual (1% → 10%) |
| Risk Management | Basic | Advanced (CVaR, regimes) |
| Monitoring | Basic | Real-time degradation alerts |
| Production Ready | No | Yes |

## File Structure

```
autoresearch_quant/
├── README.md                    # This file
├── robust_system.md             # Design principles
├── robust_research_loop.py      # Main system (5-stage pipeline)
├── backtesting_engine.py        # Walk-forward analysis
├── shadow_testing.py            # Paper trading
├── multi_objective_optimizer.py # Multi-objective optimization
├── agent_model_generator.py     # LLM code generation
├── agenthub_dag.py              # Swarm coordination
├── evaluation.py               # Performance metrics
├── data_pipeline.py             # Zero-leakage data
├── market_executor.py           # Trading execution
├── demo.py                      # Original demo
├── requirements.txt             # Dependencies
├── run_robust_swarm.sh          # Launch multiple agents
├── stop_robust_swarm.sh         # Stop all agents
└── agents/                      # Agent workspaces
    └── {agent_id}/
        ├── config.yaml
        ├── experiments/
        │   └── robust_exp_*/
        │       ├── model.py
        │       ├── model.pkl
        │       ├── metadata.yaml
        │       └── results.json
        └── models/
            └── best_model.pkl
```

## Performance Metrics Explained

### Primary Metrics

- **Total PnL**: Total profit/loss in dollars
- **Return %**: Percentage return on initial capital
- **Sharpe Ratio**: Risk-adjusted returns (annualized)
- **Win Rate**: Percentage of winning trades
- **Max Drawdown**: Maximum peak-to-trough loss
- **Sortino Ratio**: Downside-adjusted returns
- **Calmar Ratio**: Return / max drawdown

### Secondary Metrics

- **Average Return/Trade**: Mean PnL per trade
- **Profit Factor**: Gross profit / gross loss
- **Avg Win / Avg Loss**: Average winner / average loser
- **Monthly Hit Rate**: Win rate per month

### Risk Metrics

- **VaR (Value at Risk)**: Maximum expected loss at confidence level
- **CVaR (Conditional VaR)**: Expected loss beyond VaR
- **Beta**: Correlation with market
- **Tail Risk**: Extreme event exposure

## Troubleshooting

### Issue: Models failing backtesting

**Solution**:
- Check if using day-zero data
- Verify train/test split is temporal
- Ensure sufficient trades (>100)
- Review statistical significance p-value

### Issue: Shadow testing degradation

**Solution**:
- Increase `min_trading_hours` for more data
- Check for overfitting (in-sample vs out-of-sample gap)
- Review market regime changes
- Consider more robust features

### Issue: No models passing selection

**Solution**:
- Lower `min_weighted_score` threshold
- Adjust objective weights for your risk profile
- Review backtest criteria (too strict?)
- Check data quality

### Issue: Deployment degradation

**Solution**:
- Start with smaller allocation (<1%)
- Monitor for regime shifts
- Consider rolling restarts
- Review risk limits

## Production Deployment

For production trading, ensure:

1. **Real Data Sources**: Connect to live market APIs (Polymarket, etc.)
2. **Risk Limits**: Set maximum exposure per strategy
3. **Alerting**: Set up notifications for degradation
4. **Backup**: Maintain fallback models
5. **Compliance**: Follow regulatory requirements
6. **Monitoring**: Real-time dashboards
7. **Security**: Secure API keys and credentials
8. **Database**: Store results in PostgreSQL (not JSON)

## License

Experimental/Research use only. Not financial advice.

## Support

This is a complex system. Key components:
- Backtesting: Walk-forward analysis with statistical validation
- Shadow Testing: Paper trading on live data
- Multi-Objective: Optimize profit, risk, and robustness
- AgentHub: Swarm coordination via DAG

Each model must pass ALL 5 validation stages before deployment.
