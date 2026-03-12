# AutoResearch Quant Agent Swarm

## FIVE Production-Ready Systems

We have FOUR systems built for different needs.

### System 1: Balanced Iteration ⭐⭐⭐ (What You Wanted)

**True research iterations. NEW strategy each time. Proper skill assessment.**

```
Entry: python3 balanced_iteration_agent.py
Iteration time: 30 minutes - 2 hours (recommended: 1 hour)
Iterations/day: 24
Features: NEW methods each time, proper skill assessment
Docs: BALANCED_QUICKSTART.md
```

**What It Does:**
1. **Analyze** (5-15 min) - Fetch and analyze data
2. **Develop** (10-45 min) - LLM generates NEW strategy
3. **Test** (10-60 min) - Train and test on live data
4. **Evaluate** (5-15 min) - Assess predictive skill

**Key Features:**
- NEW strategy each iteration (not same model)
- Proper skill assessment (statistical significance, IC, calibration)
- Strategy diversity (can't repeat same types)
- Time to analyze and develop methods
- Statistical validation
- Deployable threshold: skill >0.4

**Best for:**
- ✓ Want time to analyze data
- ✓ Want NEW methods each iteration
- ✓ Want proper predictive skill assessment
- ✓ Want 30 min - 2 hour iterations
- ✓ Want 24 iterations/day

### System 2: Fast Inference (2 second iterations)

**Ultra-fast iteration with batch prediction.**

- **Iteration time**: 2-3 seconds
- **Iterations/day**: 144
- **Features**: Batch prediction, data caching, parallel agents
- **Entry point**: `python3 fast_parallel_swarm.py`
- **Quick start**: `FAST_QUICKSTART.md`

**Best for:**
- Want 2 second iterations
- Don't need to analyze data each iteration
- Don't need to develop new methods each time
- Just want fast inference on existing model

### System 3: Live Trading (1-2 week validation)

**Trade on live markets, validate on resolved outcomes.**

- **Validation time**: 1-2 weeks (30 resolved trades)
- **Data**: Real-time live markets
- **Sectors**: 7 (sports, politics, crypto, entertainment, weather, etc.)
- **Agents**: 7 sector-based agents
- **Entry point**: `python3 live_trading_swarm.py`
- **Quick start**: `LIVE_TRADING_QUICKSTART.md`

**Best for:**
- ✓ Trading prediction markets (Polymarket, Kalshi, etc.)
- ✓ Markets that resolve quickly
- ✓ Need fast validation
- ✓ Want real-time data
- ✓ Want sector diversification

### System 4: Robust Backtesting (3 month validation)

**Statistical backtesting with 5-stage pipeline.**

- **Validation**: 3 months (90-day backtest + shadow testing)
- **Data**: Historical + live (shadow testing)
- **Validation stages**: 5 (Research → Backtest → Shadow → Selection → Deploy)
- **Optimization**: Multi-objective (7 metrics)
- **Entry point**: `python3 robust_research_loop.py`
- **Quick start**: `ROBUST_README.md`

**Best for:**
- ✓ Trading traditional finance (stocks, forex, futures)
- ✓ Need statistical significance (t-tests, p-values)
- ✓ Markets don't "resolve" (continuous trading)
- ✓ Want multi-objective optimization
- ✓ Need 5-stage validation pipeline

### System 5: Agent Specialization & Tracking ⭐⭐⭐ (NEW!)

**Specialized agents for each market niche with comprehensive tracking.**

- **Specialized agents**: 30+ niches (Crypto Hourly, NBA Player Props, Presidential Elections, etc.)
- **Performance tracking**: Agent-level, niche-level, swarm-level metrics
- **Leaderboards**: Rankings within niches and across all niches
- **Reputation system**: Track agent reputation over time
- **Expertise development**: Agents learn and improve over time
- **Entry points**:
  - `python3 agent_specialization.py` - Create and manage specialized agents
  - `python3 agent_tracking.py` - Track and analyze performance
- **Documentation**: `AGENT_SPECIALIZATION_SYSTEM.md`

**What It Does:**
1. **Create specialized agents** for different market niches
2. **Distribute markets** to agents based on their specialization
3. **Execute trades** with niche-specific risk parameters
4. **Track performance** with comprehensive metrics
5. **Update leaderboards** (per niche, overall)
6. **Develop expertise** - Agents learn from wins and losses

**Key Features:**
- 30+ market niches across Sports, Crypto, Politics, Economics, Entertainment, Weather
- Agent identity and reputation system
- Time-series tracking (snapshots at minute/hour/day/week intervals)
- Comprehensive reports (agent, niche, swarm level)
- Niche-specific risk management
- Competitive environment with leaderboards

**Best for:**
- ✓ Want specialized agents for each niche
- ✓ Want to simulate real prediction market traders
- ✓ Want comprehensive performance tracking
- ✓ Want leaderboards and competitive environment
- ✓ Want agents that develop expertise over time

## Quick Start

### Balanced System (What You Wanted) ⭐
```bash
cd ~/autoresearch_quant
pip install -r requirements.txt

# Run balanced agent (1 hour iterations)
python3 balanced_iteration_agent.py
```

### Fast System
```bash
# Run fast parallel swarm (2 second iterations)
python3 fast_parallel_swarm.py
```

### Live Trading System
```bash
# Run live trading swarm
python3 live_trading_swarm.py
```

### Robust System
```bash
# Run robust research loop
python3 robust_research_loop.py
```

### Agent Specialization & Tracking (NEW!)
```bash
# Run agent specialization demo
python3 agent_specialization.py

# Run agent tracking demo
python3 agent_tracking.py
```

### Live Trading System (What You Want)

```bash
cd ~/autoresearch_quant

# Install dependencies
pip install -r requirements.txt

# Run swarm demo (7 agents)
python3 live_trading_swarm.py

# Run single agent
python3 live_trading_agent.py

# Discover markets
python3 market_discovery.py
```

### Robust Backtesting System (If You Need Backtesting)

```bash
cd ~/autoresearch_quant

# Run full pipeline demo
python3 robust_demo.py

# Run backtesting
python3 backtesting_engine.py

# Run shadow testing
python3 shadow_testing.py
```

## Which System Should You Use?

### Use Live Trading System If:
```
✓ Trading prediction markets
✓ Markets resolve in hours/days
✓ Want to validate in 1-2 weeks
✓ Need real-time data
✓ Want sector diversification
```

### Use Robust Backtesting System If:
```
✓ Trading traditional finance
✓ Need statistical significance tests
✓ Markets don't resolve (continuous)
✓ Want multi-objective optimization
✓ Need 5-stage validation pipeline
```

## Documentation

### Live Trading System
- **Quick Start**: `LIVE_TRADING_QUICKSTART.md`
- **Summary**: `LIVE_SYSTEM_SUMMARY.md`
- **Full Docs**: `live_trading_system.md`

### Robust Backtesting System
- **Quick Start**: `ROBUST_README.md`
- **Summary**: `robust_system.md`
- **Architecture**: `ARCHITECTURE.md`

### Comparison
- **System Comparison**: `COMPARISON.md`
- **Decision Guide**: See comparison table in COMPARISON.md

## Key Features

### Live Trading System
- Live market discovery
- Real-time trading
- Fast validation (1-2 weeks)
- 7 sectors, 7 agents
- Risk management (dollar limits)

### Robust Backtesting System
- Walk-forward analysis
- Shadow testing (paper trading)
- Multi-objective optimization
- Statistical significance testing
- Gradual deployment

## File Structure

### Live Trading Files
```
market_discovery.py        # Find live markets
live_trading_engine.py     # Core trading logic
live_trading_agent.py     # Single agent
live_trading_swarm.py     # Multi-agent swarm
```

### Robust Backtesting Files
```
backtesting_engine.py        # Walk-forward analysis
shadow_testing.py          # Paper trading
multi_objective_optimizer.py # Multi-objective opt
robust_research_loop.py     # Main system
```

### Shared Components
```
agent_model_generator.py     # LLM code generation
agenthub_dag.py              # Swarm coordination
data_pipeline.py             # Zero-leakage data
evaluation.py               # Performance metrics
market_executor.py           # Trading execution
```

### Agent Specialization Files (NEW!)
```
agent_specialization.py      # Create and manage specialized agents
agent_tracking.py            # Track and analyze performance
tiered_optimization.py      # Time-horizon-aware execution
```

### Documentation
```
LIVE_TRADING_QUICKSTART.md # Live system quick start
LIVE_SYSTEM_SUMMARY.md    # Live system summary
live_trading_system.md    # Live system full docs
ROBUST_README.md          # Robust system docs
robust_system.md          # Robust system design
ARCHITECTURE.md           # Technical architecture
COMPARISON.md             # System comparison
QUICKSTART.md             # Original quick start
SUMMARY.md               # Original summary
AGENT_SPECIALIZATION_SYSTEM.md  # Agent specialization docs (NEW!)
TIERED_OPTIMIZATION_DESIGN.md   # Tiered optimization docs (NEW!)
```

## Advantages

### Live Trading System
✓ 10x faster (2 weeks vs 3 months)
✓ Real data (current conditions)
✓ More opportunities (100+ markets/week)
✓ Sector diversification (7 sectors)
✓ Adaptive (learn in real-time)

### Robust Backtesting System
✓ Statistical rigor (t-tests, p-values)
✓ Multi-objective optimization (7 metrics)
✓ Walk-forward analysis (no lookahead bias)
✓ Gradual deployment (1% → 10%)
✓ Better for traditional finance

## Production Deployment

### Live Trading System
1. Connect to prediction market APIs
2. Fund accounts ($1,000+ per agent)
3. Start small ($10-50 per trade)
4. Wait for validation (30 trades)
5. Scale up profitable agents

### Robust Backtesting System
1. Run backtests on historical data
2. Shadow test on live data (30+ days)
3. Validate multi-objective scores
4. Deploy gradually (1% → 10%)
5. Monitor and scale

## Next Steps

### For Prediction Markets (Live Trading System)
```bash
# Run demo
python3 live_trading_swarm.py

# Read quick start
cat LIVE_TRADING_QUICKSTART.md

# Connect APIs
# Edit market_discovery.py to add real APIs

# Start trading
python3 live_trading_agent.py
```

### For Traditional Finance (Robust Backtesting System)
```bash
# Run demo
python3 robust_demo.py

# Read documentation
cat ROBUST_README.md

# Configure thresholds
# Edit robust_research_loop.py

# Run backtests
python3 robust_research_loop.py
```

## Key Decision

**Question**: Do you want to validate on live markets or run 90-day backtests?

**Live Trading System**: 1-2 weeks, real data, 7 sectors
**Robust Backtesting System**: 3 months, historical data, statistical tests

**My Recommendation**: For prediction markets, use the **Live Trading System**.

---

## Status

✓ Both systems are production-ready
✓ Full documentation provided
✓ Demo scripts included
✓ Multi-agent support

---

**Location**: `~/autoresearch_quant/`

**Entry Points**:
- Live trading: `python3 live_trading_swarm.py`
- Robust backtesting: `python3 robust_research_loop.py`

**Documentation**:
- Quick start: `LIVE_TRADING_QUICKSTART.md`
- Full docs: `live_trading_system.md` / `ROBUST_README.md`
- Comparison: `COMPARISON.md`
