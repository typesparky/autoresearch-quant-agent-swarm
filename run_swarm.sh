#!/bin/bash

# Launch multiple AutoResearch agents as background processes

set -e

# Configuration
NUM_AGENTS=${NUM_AGENTS:-3}
MARKET_TYPE=${MARKET_TYPE:-"crypto"}
LLM_API_KEY=${LLM_API_KEY:-""}

# Validate
if [ -z "$LLM_API_KEY" ]; then
    echo "Error: LLM_API_KEY environment variable required"
    echo "Usage: LLM_API_KEY=sk-... ./run_swarm.sh"
    exit 1
fi

echo "=========================================="
echo "AutoResearch Quant Agent Swarm"
echo "=========================================="
echo "Number of agents: $NUM_AGENTS"
echo "Market type: $MARKET_TYPE"
echo "=========================================="
echo ""

# Create logs directory
mkdir -p logs

# Launch agents in background
for i in $(seq 1 $NUM_AGENTS); do
    AGENT_ID="quant_$(printf "%03d" $i)"

    echo "Launching agent: $AGENT_ID"

    # Run as background process, redirect output to log
    AGENT_ID=$AGENT_ID MARKET_TYPE=$MARKET_TYPE LLM_API_KEY=$LLM_API_KEY \
        python3 autoresearch_loop.py \
        > "logs/${AGENT_ID}.log" 2>&1 &

    # Save PID
    echo $! > "logs/${AGENT_ID}.pid"

    echo "  PID: $!"
    echo "  Log: logs/${AGENT_ID}.log"
    sleep 1
done

echo ""
echo "=========================================="
echo "Swarm launched successfully!"
echo "=========================================="
echo ""
echo "To monitor agents:"
echo "  tail -f logs/quant_001.log"
echo "  tail -f logs/quant_002.log"
echo "  ..."
echo ""
echo "To check AgentHub status:"
echo "  python3 -c 'from agenthub_dag import AgentHubDAG; dag = AgentHubDAG(); dag.print_status()'"
echo ""
echo "To stop all agents:"
echo "  ./stop_swarm.sh"
echo ""
