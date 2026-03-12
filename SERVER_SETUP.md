# Server Setup Guide

AutoResearch Quant Agent Swarm - Server Deployment

---

## Quick Start (SSH into your server)

```bash
# 1. Clone the repository
git clone https://github.com/typesparky/autoresearch-quant-agent-swarm.git
cd autoresearch-quant-agent-swarm

# 2. Run setup script
chmod +x setup_server.sh run_background.sh stop.sh status.sh
./setup_server.sh

# 3. Activate virtual environment
source venv/bin/activate

# 4. Start in background
./run_background.sh
```

---

## Available Scripts

### Setup
```bash
./setup_server.sh  # Initial setup (install dependencies, create venv)
```

### Run
```bash
./run_background.sh                          # Run agent specialization (default)
./run_background.py balanced_iteration_agent.py  # Run balanced iterations
./run_background.py live_trading_swarm.py       # Run live trading
```

### Management
```bash
./status.sh    # Check status, view logs
./stop.sh      # Stop the running agent
```

---

## Available Entry Points

### 1. Agent Specialization (Recommended)
```bash
python3 agent_specialization.py
```
- 30+ market niches
- Specialized agents
- Comprehensive tracking
- Leaderboards

### 2. Balanced Iteration
```bash
python3 balanced_iteration_agent.py
```
- True research iterations
- NEW strategies each time
- Proper skill assessment
- 24 iterations/day

### 3. Live Trading
```bash
python3 live_trading_swarm.py
```
- Real-time market trading
- 7 sectors
- 1-2 week validation

### 4. Agent Tracking
```bash
python3 agent_tracking.py
```
- Performance analytics
- Time-series tracking
- Comprehensive reports

---

## Background Execution

### Start
```bash
# Default: agent_specialization.py
./run_background.sh

# Or specify another script
./run_background.sh balanced_iteration_agent.py
```

### Check Status
```bash
./status.sh
```

Shows:
- Running status
- PID
- Recent logs (last 20 lines)
- Process info (CPU, memory, runtime)

### Stop
```bash
./stop.sh
```

### View Logs
```bash
# Follow logs in real-time
tail -f logs/agent_swarm_YYYYMMDD_HHMMSS.log

# View last 100 lines
tail -n 100 logs/agent_swarm_YYYYMMDD_HHMMSS.log

# Search logs
grep "ERROR" logs/agent_swarm_*.log
grep "PROFIT" logs/agent_swarm_*.log
```

---

## Screen/Tmux Alternative

If you prefer screen/tmux instead of background scripts:

### Using Screen
```bash
# Create screen
screen -S agentswarm

# Activate venv and run
source venv/bin/activate
python3 agent_specialization.py

# Detach: Ctrl+A, then D
# Reattach: screen -r agentswarm
# List screens: screen -ls
```

### Using Tmux
```bash
# Create tmux session
tmux new -s agentswarm

# Activate venv and run
source venv/bin/activate
python3 agent_specialization.py

# Detach: Ctrl+B, then D
# Reattach: tmux attach -t agentswarm
# List sessions: tmux ls
```

---

## Auto-Restart with Cron

To auto-restart on failure or server reboot:

```bash
# Edit crontab
crontab -e

# Add line to check and restart every 5 minutes
*/5 * * * * cd /path/to/autoresearch-quant-agent-swarm && if [ ! -f pids/agent_swarm.pid ] || ! ps -p $(cat pids/agent_swarm.pid) > /dev/null; then ./run_background.sh >> logs/cron_restart.log 2>&1; fi

# Or use @reboot to start on server boot
@reboot cd /path/to/autoresearch-quant-agent-swarm && sleep 60 && ./run_background.sh >> logs/restart.log 2>&1
```

---

## Monitoring

### Disk Space
```bash
df -h  # Check disk space
du -sh logs/  # Check log directory size
```

### Clean old logs (keep last 7 days)
```bash
find logs/ -name "*.log" -mtime +7 -delete
```

### System Resources
```bash
top -p $(cat pids/agent_swarm.pid)  # Monitor specific process
htop  # Overall system monitoring
```

---

## Troubleshooting

### Process won't start
```bash
# Check if another instance is running
./status.sh

# Kill if needed
pkill -f agent_specialization

# Remove stale PID file
rm -f pids/agent_swarm.pid
```

### Out of memory
```bash
# Check memory usage
free -h

# Kill process
./stop.sh

# Restart with smaller batch size
# (edit the Python script to reduce concurrent agents/markets)
```

### Logs not updating
```bash
# Check if process is actually running
ps aux | grep python

# Check disk space
df -h

# Check permissions on logs directory
ls -la logs/
```

### Import errors
```bash
# Reinstall dependencies
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Or recreate venv
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Performance Optimization

### Reduce CPU Usage
- Reduce number of concurrent agents
- Increase iteration time (for balanced iteration)
- Use fewer markets

### Reduce Memory Usage
- Limit number of agents
- Reduce model complexity
- Clear old experiments: `rm -rf agents/*/experiments/*`

### Improve Speed
- Use `fast_parallel_swarm.py` (2-second iterations)
- Reduce data fetching frequency
- Cache data locally

---

## Security

### Protect API Keys
```bash
# Never commit API keys to git!
# Use environment variables or config files

# Add to .gitignore:
echo "*.env" >> .gitignore
echo "api_keys.json" >> .gitignore

# Create environment file
cat > .env << EOF
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
POLYMARKET_API_KEY=your_key_here
EOF

# Load in Python
import os
api_key = os.getenv('OPENAI_API_KEY')
```

### Firewall
```bash
# Allow only necessary ports (if using web interface)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## Updating

### Pull latest changes
```bash
# Stop the agent
./stop.sh

# Pull updates
git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Restart
./run_background.sh
```

---

## System Requirements

### Minimum
- Python 3.9+
- 2 CPU cores
- 2GB RAM
- 10GB disk space

### Recommended
- Python 3.10+
- 4+ CPU cores
- 8GB+ RAM
- 50GB+ disk space (for logs and experiments)

---

## Support

For issues or questions:
- Check logs: `./status.sh`
- Review documentation in the repository
- Check GitHub issues: https://github.com/typesparky/autoresearch-quant-agent-swarm/issues

---

## License

MIT License - See LICENSE file for details.
