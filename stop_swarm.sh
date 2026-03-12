#!/bin/bash

# Stop all running AutoResearch agents

echo "Stopping AutoResearch agents..."

# Kill all background processes
for pid_file in logs/*.pid; do
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
pkill -f "autoresearch_loop.py" || true

echo "All agents stopped."
