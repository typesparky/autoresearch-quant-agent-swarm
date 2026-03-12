#!/bin/bash

# AutoResearch Quant Agent Swarm - Run Script

set -e

# Configuration
AGENT_ID=${AGENT_ID:-"quant_001"}
MARKET_TYPE=${MARKET_TYPE:-"crypto"}
LLM_API_KEY=${LLM_API_KEY:-""}

# Validate
if [ -z "$LLM_API_KEY" ]; then
    echo "Error: LLM_API_KEY environment variable required"
    echo "Usage: LLM_API_KEY=sk-... ./run.sh"
    exit 1
fi

# Set environment variables
export AGENT_ID=$AGENT_ID
export MARKET_TYPE=$MARKET_TYPE
export LLM_API_KEY=$LLM_API_KEY

echo "=========================================="
echo "AutoResearch Quant Agent Swarm"
echo "=========================================="
echo "Agent ID:     $AGENT_ID"
echo "Market Type:  $MARKET_TYPE"
echo "=========================================="
echo ""

# Run the AutoResearch loop
python3 autoresearch_loop.py
