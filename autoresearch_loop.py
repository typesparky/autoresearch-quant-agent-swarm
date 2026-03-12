#!/usr/bin/env python3
"""
AutoResearch Loop - Core meta-learning framework for autonomous quant agents.

Each agent follows the loop:
1. Goal: Identify mispriced markets
2. Plan: Design model and data strategy
3. Edit: Write/modify code
4. Train: Execute model on live data
5. Evaluate: Measure performance
6. Save: Commit to AgentHub if improved
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import yaml
import subprocess
import hashlib

# LLM Integration for agent reasoning
from agent_model_generator import AgentModelGenerator
from data_pipeline import ZeroLeakagePipeline
from evaluation import PerformanceEvaluator
from agenthub_dag import AgentHubDAG


class AutoResearchLoop:
    """Core AutoResearch loop for autonomous quant research."""

    def __init__(
        self,
        agent_id: str,
        market_type: str,
        llm_api_key: str,
        data_pipeline: ZeroLeakagePipeline,
        max_iterations: int = 100000,  # High limit for 24/7 operation
        patience: int = 100,  # Allow more consecutive failures
    ):
        self.agent_id = agent_id
        self.market_type = market_type
        self.llm = AgentModelGenerator(llm_api_key)
        self.data_pipeline = data_pipeline
        self.evaluator = PerformanceEvaluator()
        self.agenthub = AgentHubDAG()

        self.max_iterations = max_iterations
        self.patience = patience

        # Agent workspace
        self.workspace = Path(f"agents/{agent_id}")
        self.workspace.mkdir(parents=True, exist_ok=True)

        # Initialize configuration
        self.config = self._load_config()
        self.best_metrics = self.config.get("best_metrics", {})

        # Experiment tracking
        self.experiments_dir = self.workspace / "experiments"
        self.experiments_dir.mkdir(exist_ok=True)

        self.iteration = 0
        self.no_improvement_count = 0

        # Track recent failures for learning
        self.recent_failures = []

    def _load_config(self) -> Dict:
        """Load agent configuration from file."""
        config_path = self.workspace / "config.yaml"
        if config_path.exists():
            with open(config_path) as f:
                return yaml.safe_load(f)
        return self._default_config()

    def _default_config(self) -> Dict:
        """Default configuration for new agent."""
        return {
            "agent_id": self.agent_id,
            "market_type": self.market_type,
            "created_at": datetime.now().isoformat(),
            "current_best_model": None,
            "best_metrics": {},
            "total_experiments": 0,
        }

    def _save_config(self):
        """Save agent configuration."""
        config_path = self.workspace / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(self.config, f, default_flow_style=False)

    def _create_experiment_dir(self) -> Path:
        """Create directory for new experiment."""
        exp_id = f"exp_{self.iteration}_{int(time.time())}"
        exp_dir = self.experiments_dir / exp_id
        exp_dir.mkdir(parents=True, exist_ok=True)
        return exp_dir

    def _commit_to_agenthub(
        self,
        experiment_dir: Path,
        metrics: Dict,
        reason: str
    ) -> str:
        """Commit successful experiment to AgentHub DAG."""
        # Create commit metadata
        commit_data = {
            "agent_id": self.agent_id,
            "experiment_dir": str(experiment_dir),
            "metrics": metrics,
            "iteration": self.iteration,
            "timestamp": datetime.now().isoformat(),
            "reason": reason,
        }

        # Calculate commit hash
        commit_hash = hashlib.sha256(
            json.dumps(commit_data, sort_keys=True).encode()
        ).hexdigest()[:12]

        # Save commit to AgentHub
        commit_id = self.agenthub.commit(
            agent_id=self.agent_id,
            commit_hash=commit_hash,
            data=commit_data,
        )

        print(f"[AgentHub] Committed {commit_id}: {reason}")

        return commit_id

    def _get_recent_failures(self) -> List[str]:
        """Get list of recent failures for learning from mistakes."""
        return self.recent_failures[-5:]  # Last 5 failures

    async def goal(self) -> Dict:
        """
        Step 1: Define research goal.

        Returns goal specification for planning phase.
        """
        print(f"\n[Step 1: Goal] Defining research objective")

        goal = {
            "objective": "identify and profit from mispriced markets",
            "market_type": self.market_type,
            "target": "maximize risk-adjusted returns (Sharpe ratio > 1.5)",
            "constraints": {
                "max_drawdown": 0.15,
                "min_win_rate": 0.55,
                "position_size": 0.05,  # 5% of portfolio per trade
            },
        }

        print(f"Goal: {goal['objective']}")
        return goal

    async def plan(self, goal: Dict) -> Dict:
        """
        Step 2: Plan experiment.

        Uses LLM to design model architecture and data strategy.
        """
        print(f"\n[Step 2: Plan] Designing model and data strategy")

        # Get current best as context
        context = {
            "best_metrics": self.best_metrics,
            "iteration": self.iteration,
            "previous_failures": self._get_recent_failures(),
        }

        # LLM generates plan
        plan = await self.llm.generate_research_plan(
            goal=goal,
            context=context,
            market_type=self.market_type,
        )

        print(f"Plan strategy: {plan.get('strategy', 'unknown')}")
        print(f"Model type: {plan.get('model_type', 'unknown')}")

        return plan

    async def edit(self, plan: Dict) -> Tuple[str, Dict]:
        """
        Step 3: Write/modify code.

        LLM generates complete Python code for model training.
        """
        print(f"\n[Step 3: Edit] Writing model code")

        # Generate code based on plan
        code, metadata = await self.llm.generate_model_code(
            plan=plan,
            agent_id=self.agent_id,
            workspace=str(self.workspace),
        )

        # Save generated code
        exp_dir = self._create_experiment_dir()
        code_path = exp_dir / "model.py"
        code_path = code_path.resolve()  # Make it absolute
        with open(code_path, "w") as f:
            f.write(code)

        # Save metadata
        metadata_path = exp_dir / "metadata.yaml"
        with open(metadata_path, "w") as f:
            yaml.dump(metadata, f)

        print(f"Generated code: {code_path}")
        print(f"Lines of code: {len(code.splitlines())}")

        return str(code_path), metadata

    async def train(self, code_path: str) -> Tuple[Dict, str]:
        """
        Step 4: Train model on zero-leakage data.

        Execute generated code in isolated environment.
        """
        print(f"\n[Step 4: Train] Executing model on live data")

        # Get zero-leakage data
        data = await self.data_pipeline.fetch_live_data(
            market_type=self.market_type,
            window_days=7,  # Last 7 days only (day-zero)
        )

        # Validate zero-leakage
        if not data["is_day_zero"]:
            raise ValueError("Data contamination detected - not day-zero!")

        print(f"Data points: {len(data['features'])}")
        print(f"Date range: {data['date_range']}")

        # Execute training script
        result = subprocess.run(
            ["/usr/local/bin/python3", code_path],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            cwd=str(Path(code_path).parent),
            env={"DATA_PATH": json.dumps(data)},
        )

        if result.returncode != 0:
            print(f"Training failed: {result.stderr}")
            return {"status": "failed", "error": result.stderr}, ""

        # Load training results
        results_path = Path(code_path).parent / "results.json"
        with open(results_path) as f:
            metrics = json.load(f)

        model_path = str(Path(code_path).parent / "model.pkl")
        print(f"Training complete. PnL: {metrics.get('total_pnl', 0):.2f}")
        print(f"Sharpe: {metrics.get('sharpe_ratio', 0):.2f}")

        return metrics, model_path

    async def evaluate(self, metrics: Dict) -> Tuple[bool, str]:
        """
        Step 5: Evaluate performance.

        Decide if model is worth saving.
        """
        print(f"\n[Step 5: Evaluate] Assessing performance")

        # Check if improvement
        is_improvement, reason = self.evaluator.is_improvement(
            new_metrics=metrics,
            best_metrics=self.best_metrics,
        )

        print(f"Improvement: {is_improvement}")
        print(f"Reason: {reason}")

        if is_improvement:
            print(f"Previous best Sharpe: {self.best_metrics.get('sharpe_ratio', 0):.2f}")
            print(f"New Sharpe: {metrics.get('sharpe_ratio', 0):.2f}")

        return is_improvement, reason

    async def save(self, experiment_dir: Path, metrics: Dict, model_path: str):
        """
        Step 6: Save to AgentHub if improved.

        Update best configuration and commit to swarm.
        """
        print(f"\n[Step 6: Save] Committing to AgentHub")

        # Update best metrics
        self.best_metrics = metrics
        self.config["best_metrics"] = metrics
        self.config["current_best_model"] = model_path
        self.config["total_experiments"] = self.iteration + 1

        # Commit to AgentHub
        commit_id = self._commit_to_agenthub(
            experiment_dir=experiment_dir,
            metrics=metrics,
            reason=f"Improved Sharpe to {metrics['sharpe_ratio']:.2f}",
        )

        # Save best model to models directory
        models_dir = self.workspace / "models"
        models_dir.mkdir(exist_ok=True)
        best_model_path = models_dir / "best_model.pkl"

        import shutil
        shutil.copy(model_path, best_model_path)

        # Update config
        self._save_config()

        print(f"Saved best model to: {best_model_path}")
        print(f"Commit ID: {commit_id}")

    async def run_one_iteration(self) -> bool:
        """Run complete AutoResearch loop iteration."""
        try:
            # Step 1: Goal
            goal = await self.goal()

            # Step 2: Plan
            plan = await self.plan(goal)

            # Step 3: Edit
            code_path, metadata = await self.edit(plan)

            # Step 4: Train
            metrics, model_path = await self.train(code_path)

            # Step 5: Evaluate
            is_improvement, reason = await self.evaluate(metrics)

            if is_improvement:
                # Step 6: Save
                await self.save(Path(code_path).parent, metrics, model_path)
                self.no_improvement_count = 0
            else:
                self.no_improvement_count += 1

            self.iteration += 1
            print(f"\n{'='*60}")
            print(f"Iteration {self.iteration} complete")
            print(f"Best Sharpe: {self.best_metrics.get('sharpe_ratio', 0):.2f}")
            print(f"No improvement streak: {self.no_improvement_count}")
            print(f"{'='*60}\n")

            return True

        except Exception as e:
            print(f"\n[ERROR] Iteration failed: {e}")
            import traceback
            traceback.print_exc()
            
            # Track failure for learning
            self.recent_failures.append(str(e))
            
            self.no_improvement_count += 1
            return False

    async def run(self):
        """Run continuous AutoResearch loop."""
        print(f"\n{'='*60}")
        print(f"Starting AutoResearch Loop for {self.agent_id}")
        print(f"Market: {self.market_type}")
        print(f"Max iterations: {self.max_iterations}")
        print(f"Patience: {self.patience}")
        print(f"{'='*60}\n")

        while self.iteration < self.max_iterations:
            if self.no_improvement_count >= self.patience:
                print(f"\nPatience exceeded. Stopping.")
                break

            success = await self.run_one_iteration()

            # Brief pause between iterations
            await asyncio.sleep(1)

        print(f"\n{'='*60}")
        print(f"AutoResearch Loop complete")
        print(f"Total iterations: {self.iteration}")
        print(f"Best Sharpe ratio: {self.best_metrics.get('sharpe_ratio', 0):.2f}")
        print(f"{'='*60}\n")


async def main():
    """Run AutoResearch loop for a single agent."""
    import os

    agent_id = os.getenv("AGENT_ID", "quant_001")
    market_type = os.getenv("MARKET_TYPE", "crypto")
    llm_api_key = os.getenv("LLM_API_KEY")

    if not llm_api_key:
        raise ValueError("LLM_API_KEY environment variable required")

    # Initialize data pipeline
    data_pipeline = ZeroLeakagePipeline()

    # Run AutoResearch loop
    loop = AutoResearchLoop(
        agent_id=agent_id,
        market_type=market_type,
        llm_api_key=llm_api_key,
        data_pipeline=data_pipeline,
    )

    await loop.run()


if __name__ == "__main__":
    asyncio.run(main())
