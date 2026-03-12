#!/bin/bash
# Run AutoResearch Quant Agent Swarm in Background
# This script starts the agent swarm in the background with logging

set -e

# Configuration
PYTHON_SCRIPT="${1:-agent_specialization.py}"  # Default: agent specialization
LOG_FILE="logs/agent_swarm_$(date +%Y%m%d_%H%M%S).log"
PID_FILE="pids/agent_swarm.pid"

echo "======================================"
echo "AutoResearch Quant Agent Swarm"
echo "Starting in Background"
echo "======================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "ERROR: Virtual environment not found!"
    echo "Run setup_server.sh first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Create log directory
mkdir -p logs

# Create pid directory
mkdir -p pids

# Check if already running
if [ -f "$PID_FILE" ]; then
    if ps -p $(cat $PID_FILE) > /dev/null 2>&1; then
        echo "WARNING: Agent swarm is already running (PID: $(cat $PID_FILE))"
        echo "Use ./stop.sh to stop it first"
        exit 1
    else
        echo "Removing stale PID file"
        rm -f "$PID_FILE"
    fi
fi

# Start in background
echo "Starting $PYTHON_SCRIPT..."
echo "Log file: $LOG_FILE"
echo "PID file: $PID_FILE"
echo ""

nohup python3 $PYTHON_SCRIPT > "$LOG_FILE" 2>&1 &
PID=$!

# Save PID
echo $PID > "$PID_FILE"

echo "======================================"
echo "Started successfully!"
echo "======================================"
echo ""
echo "PID: $PID"
echo "Log: $LOG_FILE"
echo ""
echo "To view logs: tail -f $LOG_FILE"
echo "To stop: ./stop.sh"
echo "To check status: ./status.sh"
echo ""
