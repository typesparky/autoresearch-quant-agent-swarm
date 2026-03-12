#!/bin/bash
# Stop AutoResearch Quant Agent Swarm
# This script stops the background agent swarm

PID_FILE="pids/agent_swarm.pid"

echo "======================================"
echo "Stopping Agent Swarm"
echo "======================================"
echo ""

if [ ! -f "$PID_FILE" ]; then
    echo "No PID file found. Agent swarm may not be running."
    echo "Use ./status.sh to check."
    exit 0
fi

PID=$(cat $PID_FILE)

# Check if process is running
if ps -p $PID > /dev/null 2>&1; then
    echo "Stopping process $PID..."
    kill $PID

    # Wait for process to stop
    for i in {1..10}; do
        if ! ps -p $PID > /dev/null 2>&1; then
            echo "Stopped successfully"
            rm -f "$PID_FILE"
            echo ""
            echo "To restart: ./run_background.sh"
            exit 0
        fi
        sleep 1
    done

    # Force kill if still running
    echo "Process didn't stop gracefully. Force killing..."
    kill -9 $PID
    rm -f "$PID_FILE"
    echo "Force killed"
else
    echo "Process $PID is not running. Removing PID file."
    rm -f "$PID_FILE"
fi

echo ""
echo "To restart: ./run_background.sh"
