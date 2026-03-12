#!/bin/bash
# Check status of AutoResearch Quant Agent Swarm

PID_FILE="pids/agent_swarm.pid"

echo "======================================"
echo "Agent Swarm Status"
echo "======================================"
echo ""

if [ ! -f "$PID_FILE" ]; then
    echo "Status: NOT RUNNING"
    echo "No PID file found"
    echo ""
    echo "To start: ./run_background.sh"
    exit 0
fi

PID=$(cat $PID_FILE)

if ps -p $PID > /dev/null 2>&1; then
    echo "Status: RUNNING"
    echo "PID: $PID"
    echo ""

    # Show process info
    echo "Process Info:"
    ps -p $PID -o pid,ppid,cmd,etime,%mem,%cpu

    echo ""
    echo "Recent logs:"
    echo ""

    # Find and show recent log file
    LOG_FILE=$(ls -t logs/agent_swarm_*.log 2>/dev/null | head -n 1)

    if [ -n "$LOG_FILE" ]; then
        echo "Log file: $LOG_FILE"
        echo ""
        echo "Last 20 lines:"
        echo "--------------------------------------"
        tail -n 20 "$LOG_FILE"
        echo "--------------------------------------"
        echo ""
        echo "View full logs: tail -f $LOG_FILE"
    else
        echo "No log files found"
    fi
else
    echo "Status: NOT RUNNING"
    echo "PID file exists but process is dead"
    echo ""
    echo "To start: ./run_background.sh"
fi

echo ""
