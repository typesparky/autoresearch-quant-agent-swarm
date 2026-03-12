#!/bin/bash
# Server Setup Script for AutoResearch Quant Agent Swarm
# Run this once on your server to set up the environment

set -e  # Exit on error

echo "======================================"
echo "AutoResearch Quant Agent Swarm Setup"
echo "======================================"
echo ""

# Check if Python 3.9+ is installed
echo "Checking Python version..."
python3 --version

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create log directory
mkdir -p logs

# Create pid directory
mkdir -p pids

echo ""
echo "======================================"
echo "Setup complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Run an agent: python3 agent_specialization.py"
echo "3. Or run in background: ./run_background.sh"
echo ""
echo "Available entry points:"
echo "  - agent_specialization.py (recommended)"
echo "  - balanced_iteration_agent.py"
echo "  - live_trading_swarm.py"
echo "  - agent_tracking.py"
echo ""
