# Balanced Iteration System - Quick Start

## What We Built

**Balanced iteration system: TRUE research with proper skill assessment.**

Not 2 seconds (no analysis), not weeks (too slow). **Just right: 30 minutes - 2 hours.**

## The Innovation

```
Each Iteration (30 min - 2 hours):

1. ANALYZE (5-15 min)
   - Fetch recent data
   - Analyze patterns
   - Identify inefficiencies

2. DEVELOP (10-45 min)
   - LLM generates NEW strategy (not just tweaking)
   - Write new code
   - Design new features
   - Create new model architecture

3. TEST (10-60 min)
   - Train model
   - Test on live data
   - Calculate performance

4. EVALUATE (5-15 min)
   - Assess predictive skill
   - Statistical significance testing
   - Calculate skill score
   - Decide: Keep or Discard

TOTAL: 30 minutes - 2 hours
```

## Key Difference: NEW Method Each Time

### Old Fast System (Wrong)
```
Iteration 1: Train model A → Test
Iteration 2: Use model A → Test (same model)
Iteration 3: Use model A → Test (same model)

Problem: No new methods, just fast inference
```

### New Balanced System (Correct)
```
Iteration 1: Analyze → Develop Strategy A → Test → Evaluate
Iteration 2: Analyze → Develop Strategy B → Test → Evaluate (NEW!)
Iteration 3: Analyze → Develop Strategy C → Test → Evaluate (NEW!)

Advantage: True research, adaptive, skill assessment
```

## Predictive Skill Assessment

### What We Measure

1. **Win Rate** (40% weight)
   - Percentage of correct predictions
   - Threshold: >55% (better than random)

2. **Statistical Significance** (20% weight)
   - T-test on returns
   - P-value < 0.05
   - Minimum 30 predictions

3. **Information Coefficient** (20% weight)
   - Correlation between prediction and outcome
   - Range: 0-1, higher is better
   - Threshold: >0.1

4. **Consistency** (10% weight)
   - Performance across time
   - Stability of predictions

5. **Calibration** (10% weight)
   - How well do predicted probabilities match outcomes?
   - Brier score (lower is better)

### Skill Scoring

```
Skill Score = Weighted combination:
  Win Rate (40%) + Significance (20%) + IC (20%) + Consistency (10%) + Calibration (10%)

Range: 0-1, higher is better
Threshold: >0.4 to deploy
```

## Iteration Timing Options

### Conservative (30 minutes)
```
Analyze:     5 minutes
Develop:     10 minutes
Test:         10 minutes
Evaluate:     5 minutes
TOTAL:        30 minutes

Iterations/day: 48
Good for: Rapid exploration
```

### Balanced (1 hour) ⭐ **RECOMMENDED**
```
Analyze:     10 minutes
Develop:     20 minutes
Test:         20 minutes
Evaluate:     10 minutes
TOTAL:        1 hour

Iterations/day: 24
Good for: Balance of exploration and thoroughness
```

### Thorough (2 hours)
```
Analyze:     15 minutes
Develop:     45 minutes
Test:         45 minutes
Evaluate:     15 minutes
TOTAL:        2 hours

Iterations/day: 12
Good for: Deep research on complex strategies
```

## Preventing Stagnation

### The Problem
```
If agent finds one good strategy:
Iteration 1: Strategy A (good)
Iteration 2: Strategy A (same)
Iteration 3: Strategy A (same)

Agent stops improving
```

### The Solution

1. **Enforce NEW methods**
   - Agent MUST try something new each iteration
   - Can't just use same strategy
   - Penalize similarity to previous strategies

2. **Strategy diversity**
   - Track strategy types used
   - Enforce diversity
   - Can't use 5 XGBoost strategies in a row

3. **Performance-based exploration**
   - Explore untried strategy types
   - Balance exploitation (use best) with exploration (try new)
   - Multi-armed bandit approach

## Quick Start

```bash
cd ~/autoresearch_quant
pip install -r requirements.txt

# Run balanced agent (1 hour iterations)
python3 balanced_iteration_agent.py
```

## What You'll See

```
================================================================================
BALANCED ITERATION - balanced_agent_001
Iteration: 1
Total time budget: 60 minutes
================================================================================

[Phase 1] ANALYZE complete: 8.2 minutes
[Analyze] Analyzed 50 markets
[Analyze] Avg volume: $3,245
[Analyze] Odds variance: 0.0234

[Phase 2] DEVELOP complete: 18.5 minutes
  Strategy: xgboost_price_momentum_v1
  Model type: xgboost_price_momentum
  Theory: Combining price momentum with liquidity indicators...

[Phase 3] TEST complete: 22.3 minutes
[Test] Testing strategy xgboost_price_momentum_v1...

[Phase 4] EVALUATE complete: 7.1 minutes
  Skill score: 0.567
  Deployable: YES
  Reason: Meets all skill thresholds

================================================================================
ITERATION 1 SUMMARY
Phase times:
  Analyze:   8.2 min
  Develop:    18.5 min
  Test:       22.3 min
  Evaluate:   7.1 min
  Total:      56.1 min

Strategy:
  Name:       xgboost_price_momentum_v1
  Model:      xgboost_price_momentum
  Features:   price_momentum_1h, price_momentum_24h, volume_change_24h...

Performance:
  Skill:      0.567
  Deploy:     YES
  Reason:     Meets all skill thresholds
================================================================================
```

## Strategy Types Generated

Each iteration generates a NEW strategy type:

| Type | Description | Typical Features |
|------|-------------|------------------|
| xgboost_price_momentum | XGBoost with price momentum | Price changes, volume, volatility |
| neural_sentiment_fusion | Neural network with sentiment | Sentiment, news, social data |
| ensemble_weighted_voting | Ensemble of multiple models | Multiple model outputs |
| lstm_time_series | LSTM for time series | Sequential price/volume data |
| random_forest_features | Random forest with features | Engineered features |
| gradient_boosting | Gradient boosting | Tree-based boosting |
| hybrid_ml_fundamental | ML + fundamental analysis | Combined approach |

## Performance Metrics

### Primary
- **Skill Score**: Weighted combination (0-1)
- **Win Rate**: Percentage of correct predictions
- **Sharpe Ratio**: Risk-adjusted returns
- **Statistical Significance**: P-value < 0.05

### Secondary
- **Information Coefficient**: Prediction-outcome correlation
- **Brier Score**: Calibration measure
- **Consistency**: Performance stability

## Success Criteria

For a strategy to be deployable:

| Metric | Threshold |
|--------|-----------|
| Skill Score | >0.4 |
| Win Rate | >55% |
| Sharpe Ratio | >0.5 |
| Statistical Significance | p < 0.05 |
| Minimum Predictions | 30 |

## Comparison

| Aspect | Fast System (2 sec) | Balanced System (1 hr) |
|--------|-------------------|---------------------|
| New methods each iteration | No | **Yes** |
| Analyze data | No | **Yes** |
| Develop strategies | No | **Yes** |
| Test properly | No | **Yes** |
| Assess predictive skill | No | **Yes** |
| Iterations/day | 144 | 24 |
| Quality of research | Low | **High** |
| Adaptive | Low | **High** |

## Key Files

```
balanced_iteration_agent.py ← Main agent (1 hr iterations)
BALANCED_ITERATION_DESIGN.md ← Full design
BALANCED_QUICKSTART.md    ← This file (START HERE)
```

## Next Steps

1. **Run demo**: `python3 balanced_iteration_agent.py`
2. **Read design**: `BALANCED_ITERATION_DESIGN.md`
3. **Adjust timing**: Change `iteration_time_minutes` (30-120 min)
4. **Connect LLM**: Add actual LLM API calls
5. **Deploy**: Use deployable strategies in live trading

## Documentation

- **Quick Start**: `BALANCED_QUICKSTART.md` (this file)
- **Design**: `BALANCED_ITERATION_DESIGN.md`
- **Agent**: `balanced_iteration_agent.py`

## Summary

**You wanted:**
- Time to analyze data ✓
- Come up with new methods each iteration ✓
- Increase iteration time to assess predictive skill ✓
- Not too fast, not too slow ✓

**We built:**
- True research iterations (30 min - 2 hours)
- NEW strategy each time (not same model)
- Proper skill assessment (statistical significance, IC, calibration)
- Balanced approach (enough time, fast enough to adapt)

**This is just right.**

---

**START HERE**: `BALANCED_QUICKSTART.md`
**RUN THIS**: `python3 balanced_iteration_agent.py`
**READ THIS**: `BALANCED_ITERATION_DESIGN.md`
