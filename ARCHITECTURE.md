# AutoResearch Quant Agent Swarm - Architecture

## System Overview

A production-ready framework for autonomous LLM-based quant researchers operating in prediction markets. Agents use the AutoResearch meta-learning loop to write, train, and deploy their own ML models on day-zero data.

## Core Components

### 1. AutoResearch Loop (`autoresearch_loop.py`)

**Purpose**: Meta-learning framework that enables continuous autonomous optimization.

**Architecture**:
```
Goal → Plan → Edit → Train → Evaluate → Save
```

**Key Features**:
- Async execution for efficiency
- Automatic experiment tracking
- Intelligent stopping based on patience
- Integration with AgentHub for swarm coordination

**Flow**:
1. Define research goal (identify mispriced markets)
2. Generate research plan using LLM
3. Write Python code for model training
4. Execute on zero-leakage live data
5. Evaluate performance metrics
6. Save to AgentHub if improved

### 2. Zero-Leakage Data Pipeline (`data_pipeline.py`)

**Purpose**: Ensure all training data is day-zero (post-training-cutoff).

**Key Features**:
- Real-time API integration (Coingecko, Binance, News, Sentiment)
- Contamination detection and rejection
- Normalization of heterogeneous data sources
- Feature extraction for ML models

**Data Sources**:
- Crypto: Coingecko, Binance
- News: NewsAPI, CryptoNews
- Sentiment: StockTwits, Twitter

**Validation**:
- Timestamp checks against training cutoff
- Stale data detection
- Source failure handling

### 3. Agent Model Generator (`agent_model_generator.py`)

**Purpose**: LLM-driven code generation for quant research.

**Capabilities**:
- Generate research plans (model architecture, features, training)
- Write complete Python training scripts
- Handle multiple model types (XGBoost, neural networks, ensembles)
- Include risk management logic

**Process**:
1. Receive research goal and context
2. Generate plan using LLM
3. Write functional Python code
4. Return code with metadata

### 4. Market Executor (`market_executor.py`)

**Purpose**: Execute trades based on probability deviation.

**Strategy**:
1. Calculate internal probability from trained model
2. Fetch current market odds
3. Identify mispricing (deviation > threshold)
4. Execute trade with appropriate position size
5. Manage stop-loss and take-profit

**Key Methods**:
- `calculate_internal_probability()`: Model inference
- `check_trade_opportunity()`: Identify profitable trades
- `execute_trade()`: Execute with position sizing
- `manage_positions()`: Risk management

### 5. Performance Evaluator (`evaluation.py`)

**Purpose**: Evaluate model performance and decide on improvements.

**Metrics**:
- Total PnL
- Sharpe ratio
- Win rate
- Maximum drawdown
- Number of trades
- Test accuracy

**Decision Logic**:
- Must exceed minimum thresholds
- Significant improvement required (default: 10%)
- Prefers higher Sharpe with positive PnL

### 6. AgentHub DAG (`agenthub_dag.py`)

**Purpose**: GitHub for agents - swarm coordination via Directed Acyclic Graph.

**Features**:
- Commit system for successful strategies
- Agent-specific commit history
- Global best strategy discovery
- Swarm consensus tracking
- Divergence/polarity measurement

**Key Operations**:
- `commit()`: Save successful model
- `get_best_commits()`: Find top performers
- `get_consensus()`: Aggregate swarm metrics
- `get_divergence()`: Measure disagreement

## Data Flow

```
Live Data Sources
       ↓
Zero-Leakage Pipeline (validation, normalization)
       ↓
Features → Agent Model Generator (LLM)
       ↓
Python Code → Training Script
       ↓
Model Training → Evaluation
       ↓
Performance Metrics → Improvement?
       ↓ (if yes)
AgentHub DAG Commit → Swarm Learning
       ↓
Market Executor → Probability Deviation
       ↓
Trade Execution → PnL
```

## Agent Lifecycle

```
Initialization
    ↓
Load Configuration
    ↓
Start AutoResearch Loop
    ↓
┌─────────────────────────────────┐
│  Iteration Loop (max iterations)│
│  ┌───────────────────────────┐  │
│  │ Goal: Define objective    │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │ Plan: Design strategy     │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │ Edit: Write code          │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │ Train: Execute model      │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │ Evaluate: Check metrics  │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │ Save: Commit if improved  │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
    ↓
Deploy Best Model to Market Executor
    ↓
Continuous Trading Loop
```

## Swarm Intelligence

### Emergent Behaviors

1. **Strategy Discovery**
   - Different agents explore different approaches
   - Natural selection favors profitable strategies

2. **Knowledge Transfer**
   - Successful commits become discoverable
   - Agents can build on each other's work

3. **Risk Balancing**
   - Diverse strategies reduce systemic risk
   - Swarm consensus indicates market confidence

4. **Polarity Detection**
   - High divergence = uncertain market
   - Low divergence = consensus

### Agent Communication

Agents communicate via:
- AgentHub commits (successful strategies)
- Consensus metrics (swarm averages)
- Best commit queries (discover top performers)

## Security & Reliability

### Zero-Leakage Guarantees

- Strict timestamp validation
- Training cutoff enforcement
- Contamination detection
- Source failure handling

### Risk Management

- Position sizing limits (default: 5%)
- Stop-loss (default: 2%)
- Take-profit (default: 5%)
- Maximum drawdown limits

### Error Handling

- Graceful failure handling
- Retry logic for API calls
- Experiment isolation
- Configuration persistence

## Performance Characteristics

### Latency
- Model training: < 5 minutes (experiment)
- Market execution: < 1 second
- Data fetching: < 1 second per source

### Throughput
- Multiple agents: Unlimited (concurrent)
- Experiments per agent: 100+ (configurable)
- Data sources: 10+ (extensible)

### Scalability
- Horizontal scaling via multiple agents
- Stateless design enables distributed deployment
- AgentHub DAG scales with commit count

## Integration Points

### LLM Providers
- OpenAI (GPT-4)
- Anthropic (Claude)
- Any compatible API

### Market APIs
- Polymarket
- Hyperliquid
- Custom prediction markets

### Data Sources
- Cryptocurrency: Coingecko, Binance
- News: NewsAPI, CryptoNews
- Sentiment: StockTwits, Twitter
- Custom: Extensible

## Future Enhancements

1. **Advanced ML Models**
   - Transformers for time series
   - Graph neural networks for market structure
   - Ensemble methods

2. **Better LLM Prompts**
   - Few-shot learning examples
   - Chain-of-thought reasoning
   - Self-correction loops

3. **Sophisticated Features**
   - Technical indicators
   - Network effects
   - Cross-asset correlations

4. **Improved Risk Management**
   - Dynamic position sizing
   - Portfolio-level optimization
   - Correlation-aware hedging

5. **Production Infrastructure**
   - Database backing for AgentHub
   - Distributed job queue
   - Real-time monitoring dashboard

## Conclusion

This architecture enables true autonomous quant research by combining:
- Meta-learning (AutoResearch loop)
- Zero-leakage data validation
- LLM-driven code generation
- Swarm coordination (AgentHub)
- Dynamic market execution

The system is production-ready and extensible, capable of running 24/7 to continuously discover and exploit market inefficiencies.
