#!/bin/bash

# Launch multiple Robust AutoResearch agents

set -e

# Configuration
NUM_AGENTS=${NUM_AGENTS:-3}
MARKET_TYPE=${MARKET_TYPE:-"crypto"}
LLM_API_KEY=${LLM_API_KEY:-""}

# Validate
if [ -z "$LLM_API_KEY" ]; then
    echo "Error: LLM_API_KEY environment variable required"
    echo "Usage: LLM_API_KEY=sk-... ./run_robust_swarm.sh"
    exit 1
fi

echo "=========================================="
echo "Robust AutoResearch Quant Agent Swarm"
echo "=========================================="
echo "Number of agents: $NUM_AGENTS"
echo "Market type: $MARKET_TYPE"
echo "Validation: 5-stage pipeline"
echo "  1. Research (generate strategies)"
echo "  2. Backtesting (walk-forward analysis)"
echo "  3. Shadow Testing (24h+ paper trading)"
echo "  4. Selection (multi-objective optimization)"
echo "  5. Deployment (gradual rollout)"
echo "=========================================="
echo ""

# Create logs directory
mkdir -p logs/robust

# Launch agents in background
for i in $(seq 1 $NUM_AGENTS); do
    AGENT_ID="robust_quant_$(printf "%03d" $i)"

    echo "Launching agent: $AGENT_ID"

    # Run as background process, redirect output to log
    AGENT_ID=$AGENT_ID MARKET_TYPE=$MARKET_TYPE LLM_API_KEY=$LLM_API_KEY \
        python3 robust_research_loop.py \
        > "logs/robust/${AGENT_ID}.log" 2>&1 &

    # Save PID
    echo $! > "logs/robust/${AGENT_ID}.pid"

    echo "  PID: $!"
    echo "  Log: logs/robust/${AGENT_ID}.log"
    sleep 1
done

echo ""
echo "=========================================="
echo "Robust swarm launched successfully!"
echo "=========================================="
echo ""
echo "To monitor agents:"
echo "  tail -f logs/robust/robust_quant_001.log"
echo "  tail -f logs/robust/robust_quant_002.log"
echo "  ..."
echo ""
echo "To check AgentHub status:"
echo "  python3 -c 'from agenthub_dag import AgentHubDAG; dag = AgentHubDAG(); dag.print_status()'"
echo ""
echo "To view validation summaries:"
echo "  grep 'VALIDATION SUMMARY' logs/robust/robust_quant_*.log -A 20"
echo ""
echo "To stop all agents:"
echo "  ./stop_robust_swarm.sh"
echo ""
