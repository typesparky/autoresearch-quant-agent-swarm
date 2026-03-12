#!/usr/bin/env python3
"""
Demo script to showcase the AutoResearch Quant system.

This runs a simplified version without requiring actual LLM API keys.
"""

import asyncio
import json
from pathlib import Path

# Import components
from autoresearch_loop import AutoResearchLoop
from data_pipeline import ZeroLeakagePipeline
from evaluation import PerformanceEvaluator
from agenthub_dag import AgentHubDAG
from market_executor import MarketExecutor


async def demo_autoresearch_loop():
    """Demo the AutoResearch loop."""
    print("\n" + "="*60)
    print("DEMO: AutoResearch Loop")
    print("="*60 + "\n")

    # Create mock API key for demo
    mock_api_key = "demo_key_12345"

    # Initialize components
    data_pipeline = ZeroLeakagePipeline()

    # Run 3 iterations
    loop = AutoResearchLoop(
        agent_id="demo_quant",
        market_type="crypto",
        llm_api_key=mock_api_key,
        data_pipeline=data_pipeline,
        max_iterations=3,
        patience=5,
    )

    await loop.run()

    print("\nDemo complete!")


async def demo_market_executor():
    """Demo the market executor."""
    print("\n" + "="*60)
    print("DEMO: Market Executor")
    print("="*60 + "\n")

    # Create executor
    executor = MarketExecutor(
        agent_id="demo_trader",
        initial_capital=10000,
        max_position_size=0.05,
        min_deviation=0.05,
    )

    # Simulate a trading opportunity
    print("Simulating market opportunity...")
    print("Internal probability: 0.65")
    print("Market odds: 0.52 (YES)")
    print("Deviation: 0.13 (above threshold of 0.05)")
    print()

    # Create mock trade
    trade_details = {
        "side": "YES",
        "internal_prob": 0.65,
        "market_prob": 0.52,
        "deviation": 0.13,
        "expected_edge": 0.13,
        "action": "buy",
    }

    # Execute trade
    await executor.execute_trade("BTC_UP", trade_details)

    # Simulate position close
    print("\nSimulating position close at take-profit...")
    executor.close_position("BTC_UP", 0.57, "take_profit")

    # Show performance
    print("\n" + "-"*60)
    print("Performance Summary:")
    print("-"*60)
    summary = executor.get_performance_summary()
    for key, value in summary.items():
        if isinstance(value, float):
            print(f"{key:20s}: {value:.2f}" if key != "return_pct" else f"{key:20s}: {value:.2%}")
        else:
            print(f"{key:20s}: {value}")


async def demo_agenthub_dag():
    """Demo the AgentHub DAG."""
    print("\n" + "="*60)
    print("DEMO: AgentHub DAG")
    print("="*60 + "\n")

    # Create DAG
    dag = AgentHubDAG(storage_path="demo_dag.json")

    # Simulate multiple agents committing
    agents = ["agent_001", "agent_002", "agent_003"]

    for i, agent_id in enumerate(agents):
        # Simulate commit data
        commit_data = {
            "agent_id": agent_id,
            "metrics": {
                "total_pnl": 1000 + i * 500,
                "sharpe_ratio": 1.2 + i * 0.3,
                "win_rate": 0.55 + i * 0.05,
                "max_drawdown": 0.10 + i * 0.02,
                "num_trades": 100 + i * 50,
            },
            "iteration": i + 1,
            "timestamp": "2026-03-12T00:00:00",
            "reason": f"Improved Sharpe to {1.2 + i * 0.3:.2f}",
        }

        # Commit
        dag.commit(
            agent_id=agent_id,
            commit_hash=f"hash_{i:03d}",
            data=commit_data,
        )

    # Show status
    dag.print_status()

    # Show consensus
    print("\nSwarm Consensus:")
    print("-"*60)
    consensus = dag.get_consensus()
    print(f"Number of agents: {consensus['num_agents']}")
    if consensus['consensus_metrics']:
        metrics = consensus['consensus_metrics']
        if 'sharpe_ratio' in metrics:
            print(f"Mean Sharpe: {metrics['sharpe_ratio']['mean']:.2f}")
        if 'total_pnl' in metrics:
            print(f"Mean PnL: ${metrics['total_pnl']['mean']:.2f}")

    # Show divergence
    print("\nSwarm Divergence:")
    print("-"*60)
    divergence = dag.get_divergence()
    print(f"Divergence Score: {divergence['divergence_score']:.2f}")
    print(f"Polarity: {divergence['polarity']}")

    # Clean up
    Path("demo_dag.json").unlink(missing_ok=True)


async def main():
    """Run all demos."""
    print("\n" + "="*60)
    print("AutoResearch Quant Agent Swarm - DEMO")
    print("="*60)

    print("\nThis demo showcases the core components:")
    print("1. AutoResearch Loop (goal → plan → edit → train → evaluate → save)")
    print("2. Market Executor (probability deviation detection & trading)")
    print("3. AgentHub DAG (swarm coordination and knowledge sharing)")

    choice = input("\nWhich demo would you like to run?\n" +
                   "  1. AutoResearch Loop\n" +
                   "  2. Market Executor\n" +
                   "  3. AgentHub DAG\n" +
                   "  4. All demos\n" +
                   "Choice [1-4]: ")

    if choice == "1":
        await demo_autoresearch_loop()
    elif choice == "2":
        await demo_market_executor()
    elif choice == "3":
        await demo_agenthub_dag()
    elif choice == "4":
        await demo_autoresearch_loop()
        await demo_market_executor()
        await demo_agenthub_dag()
    else:
        print("Invalid choice. Running all demos...")
        await demo_autoresearch_loop()
        await demo_market_executor()
        await demo_agenthub_dag()

    print("\n" + "="*60)
    print("Demo complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
