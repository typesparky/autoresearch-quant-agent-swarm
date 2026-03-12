# AutoResearch Quant Agent Swarm - Usage Guide

## Overview

This system enables autonomous LLM-based quant researchers to:
1. Write and train their own ML models on day-zero data
2. Execute trades when market odds deviate from their internal probabilities
3. Coordinate with other agents via AgentHub DAG
4. Continuously optimize strategies 24/7

## Quick Start

### 1. Install Dependencies

```bash
cd ~/autoresearch_quant
pip install -r requirements.txt
```

### 2. Run Demo (No API Key Required)

```bash
python3 demo.py
```

This demonstrates all components without requiring actual LLM or market API keys.

### 3. Run Full System

```bash
# Set your LLM API key (OpenAI, Anthropic, etc.)
export LLM_API_KEY="sk-your-api-key-here"

# Run the AutoResearch loop
./run.sh

# Or specify custom agent and market
AGENT_ID=quant_001 MARKET_TYPE=crypto LLM_API_KEY="sk-..." ./run.sh
```

## Architecture

### AutoResearch Loop

The core meta-learning cycle:

```
Goal → Plan → Edit → Train → Evaluate → Save
```

Each agent:
1. **Goal**: Define objective (identify mispriced markets)
2. **Plan**: Design model architecture and data strategy
3. **Edit**: Write Python code for model training
4. **Train**: Execute on zero-leakage live data
5. **Evaluate**: Measure Sharpe, PnL, win rate
6. **Save**: Commit to AgentHub if improved

### Zero-Leakage Data Pipeline

Ensures all data is day-zero (post-training-cutoff):
- Real-time APIs (Coingecko, Binance, News)
- Contamination detection
- Automatic rejection of stale/pre-cutoff data

### Agent Model Generator

LLM-driven code generation:
- Generates research plans
- Writes complete Python training scripts
- Implements model architectures (XGBoost, neural networks)
- Includes risk management logic

### Market Executor

Trade execution based on probability deviation:
1. Calculate internal probability from model
2. Fetch current market odds
3. Trade when deviation exceeds threshold (e.g., 5%)
4. Position sizing based on confidence
5. Stop-loss and take-profit management

### AgentHub DAG

GitHub for agents - swarm coordination:
- Commits successful strategies to DAG
- Agents can query best commits
- Swarm consensus tracking
- Divergence/polarity measurement

## Configuration

### Environment Variables

```bash
AGENT_ID="quant_001"              # Unique agent identifier
MARKET_TYPE="crypto"              # crypto, stocks, sports
LLM_API_KEY="sk-..."              # Your LLM API key
```

### Agent Configuration

Each agent has a `config.yaml` in their workspace:

```yaml
agent_id: quant_001
market_type: crypto
created_at: "2026-03-12T00:00:00"
current_best_model: null
best_metrics:
  total_pnl: 0
  sharpe_ratio: 0
  win_rate: 0
  max_drawdown: 0
total_experiments: 0
```

### Performance Thresholds

In `evaluation.py`:
```python
min_sharpe = 0.5           # Minimum Sharpe ratio
min_win_rate = 0.5         # Minimum win rate (50%)
max_drawdown = 0.2         # Maximum drawdown (20%)
improvement_threshold = 0.1  # 10% improvement required
```

## Running Multiple Agents

### Method 1: Multiple Terminals

```bash
# Terminal 1
AGENT_ID=quant_001 LLM_API_KEY="sk-..." python3 autoresearch_loop.py

# Terminal 2
AGENT_ID=quant_002 LLM_API_KEY="sk-..." python3 autoresearch_loop.py
```

### Method 2: Background Processes

```bash
# Start agents in background
AGENT_ID=quant_001 LLM_API_KEY="sk-..." python3 autoresearch_loop.py &
AGENT_ID=quant_002 LLM_API_KEY="sk-..." python3 autoresearch_loop.py &

# Monitor all
python3 -c "from agenthub_dag import AgentHubDAG; dag = AgentHubDAG(); dag.print_status()"
```

### Method 3: Systemd Service (Production)

Create `/etc/systemd/system/autoresearch@.service`:
```ini
[Unit]
Description=AutoResearch Quant Agent %i
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/home/your-user/autoresearch_quant
Environment=AGENT_ID=%i
Environment=MARKET_TYPE=crypto
Environment=LLM_API_KEY=your-api-key
ExecStart=/usr/bin/python3 autoresearch_loop.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable autoresearch@quant_001
sudo systemctl start autoresearch@quant_001
sudo systemctl start autoresearch@quant_002
```

## Monitoring

### Check AgentHub Status

```python
python3 -c "from agenthub_dag import AgentHubDAG; dag = AgentHubDAG(); dag.print_status()"
```

### View Specific Agent Performance

```bash
python3 evaluation.py --agent-id quant_001
```

### List Best Commits

```python
from agenthub_dag import AgentHubDAG
dag = AgentHubDAG()
best = dag.get_best_commits(metric="sharpe_ratio", limit=5)
for commit in best:
    print(f"{commit['agent_id']}: Sharpe {commit['data']['metrics']['sharpe_ratio']:.2f}")
```

## Extending the System

### Adding New Data Sources

Edit `data_pipeline.py`:

```python
self.sources["crypto"].append("https://your-api.com/endpoint")
```

Implement `_normalize_source_data()` handler for the new format.

### Adding New Market Types

Add to `_get_sources_for_market()`:

```python
elif market_type == "forex":
    return [
        "https://forex-api.com/rates",
        "https://news-api.com/forex",
    ]
```

### Custom Model Architectures

The LLM can generate any model type. Provide guidance in the prompt:

```python
plan["model_type"] = "transformer"  # or "lstm", "ensemble", etc.
```

## Troubleshooting

### Data Pipeline Issues

**Error**: "Data contamination detected"
- Check `training_cutoff_date` matches your LLM's cutoff
- Ensure APIs are returning recent data
- Check `max_data_age_days` setting

### Model Training Failures

**Error**: "Training failed"
- Check generated code in `agents/{id}/experiments/exp_*/model.py`
- Verify data format matches expectations
- Review error logs in experiment directory

### No Improvements

If agent stops due to patience limit:
- Review recent failures in config
- Check if market conditions changed
- Consider increasing `patience` or `improvement_threshold`

## Advanced Topics

### Swarm Intelligence

The system exhibits emergent behavior:
- **Strategy discovery**: Different agents find different profitable approaches
- **Knowledge transfer**: Best strategies propagate via AgentHub
- **Risk balancing**: Diverse strategies reduce systemic risk

### Polarity Detection

High divergence scores indicate:
- Uncertain market conditions
- Multiple valid interpretations
- Potential arbitrage opportunities

### Continuous Optimization

Agents run 24/7, automatically:
- Testing new strategies
- Adapting to market changes
- Building on successful approaches

## Production Deployment

For production use:

1. **Secure API keys**: Use environment variables or secrets management
2. **Monitoring**: Set up logs and alerts
3. **Database**: Replace JSON storage with PostgreSQL for AgentHub
4. **Rate limiting**: Respect API rate limits
5. **Error handling**: Implement retry logic and circuit breakers
6. **Performance**: Optimize data fetching and model training

## Contributing

This is an experimental system. Key areas for improvement:
- Better LLM prompts for code generation
- More sophisticated feature engineering
- Advanced ensemble methods
- Better risk management strategies
- Real-time anomaly detection

## License

Experimental/Research use only. Not financial advice.
