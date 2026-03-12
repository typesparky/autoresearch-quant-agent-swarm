#!/bin/bash

# Stop all running Robust AutoResearch agents

echo "Stopping Robust AutoResearch agents..."

# Kill all background processes by PID
for pid_file in logs/robust/*.pid; do
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "Killing PID $pid"
            kill "$pid"
        fi
        rm "$pid_file"
    fi
done

# Also kill by process name (fallback)
pkill -f "robust_research_loop.py" || true

echo "All agents stopped."
