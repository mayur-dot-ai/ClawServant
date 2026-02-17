#!/usr/bin/env python3
"""
ClawServant — CLI-first specialist agent for OpenClaw.

A lean, self-contained AI employee that:
- Thinks continuously (5-second cycles)
- Persists memory across restarts
- Processes tasks from files or CLI
- Outputs structured results (JSON/markdown)
- Supports any LLM provider (Bedrock, Anthropic, OpenAI, Ollama)

Usage:
    python3 clawservant.py                 # Start continuous thinking loop
    python3 clawservant.py --task <text>   # Process single task
    python3 clawservant.py --memory        # Query memory
    python3 clawservant.py --status        # Show state
"""

import json
import os
import sys
import time
import argparse
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from providers import ProviderManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("clawservant")

# Configuration
WORK_DIR = Path.home() / ".clawservant" / "workspace"
MEMORY_FILE = WORK_DIR / "memory.jsonl"
STATE_FILE = WORK_DIR / "state.json"
TASKS_DIR = WORK_DIR / "tasks"
RESULTS_DIR = WORK_DIR / "results"

# Ensure directories exist
for d in [WORK_DIR, TASKS_DIR, RESULTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Provider manager (global, initialized at startup)
provider_manager = None


class Memory:
    """Persistent memory store for agent."""
    
    def __init__(self):
        self.memories: List[Dict[str, Any]] = []
        self.load()
    
    def load(self):
        """Load memories from file."""
        if MEMORY_FILE.exists():
            with open(MEMORY_FILE) as f:
                for line in f:
                    if line.strip():
                        self.memories.append(json.loads(line))
            logger.info(f"Loaded {len(self.memories)} memories")
    
    def add(self, kind: str, content: str, importance: int = 1):
        """Add a memory (thought, observation, learning, etc)."""
        memory = {
            "timestamp": datetime.utcnow().isoformat(),
            "kind": kind,
            "content": content,
            "importance": importance,
        }
        self.memories.append(memory)
        
        # Persist to file
        with open(MEMORY_FILE, "a") as f:
            f.write(json.dumps(memory) + "\n")
    
    def recent(self, n: int = 10, kind: Optional[str] = None) -> List[Dict]:
        """Get recent memories, optionally filtered by kind."""
        filtered = self.memories if kind is None else [m for m in self.memories if m["kind"] == kind]
        return filtered[-n:]


class ClawServant:
    """Specialist agent powered by flexible LLM providers."""
    
    def __init__(self, name: str = "Researcher"):
        self.name = name
        self.memory = Memory()
        self.state = self._load_state()
        self.current_task = None
        logger.info(f"ClawServant ({self.name}) initialized")
    
    def _load_state(self) -> Dict[str, Any]:
        """Load state from file."""
        if STATE_FILE.exists():
            with open(STATE_FILE) as f:
                return json.load(f)
        return {
            "name": self.name,
            "started": datetime.utcnow().isoformat(),
            "cycles": 0,
            "tasks_completed": 0,
        }
    
    def _save_state(self):
        """Save state to file."""
        self.state["cycles"] += 1
        self.state["last_cycle"] = datetime.utcnow().isoformat()
        with open(STATE_FILE, "w") as f:
            json.dump(self.state, f, indent=2)
    
    async def think(self, prompt: str) -> str:
        """Call LLM via provider manager (auto-selects available provider)."""
        # Build system prompt
        system_prompt = f"""You are {self.name}, a specialist AI agent working for mayur.ai.

Your role:
- Think deeply about problems
- Remember previous insights (you have access to your memory)
- Complete tasks methodically
- Output clear, actionable results

Current time: {datetime.utcnow().isoformat()}
Cycle: {self.state['cycles']}
Tasks completed: {self.state['tasks_completed']}

Recent memories:
"""
        recent = self.memory.recent(n=5)
        for mem in recent:
            system_prompt += f"\n- [{mem['kind']}] {mem['content'][:100]}..."
        
        # Call LLM via provider manager
        try:
            thought, provider_used = await provider_manager.call(
                system_prompt, prompt, max_tokens=500
            )
            if self.state['cycles'] == 0:  # Log on first cycle
                logger.info(f"Using provider: {provider_used}")
            return thought
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return f"[ERROR] Failed to think: {e}"
    
    async def process_task(self, task_text: str) -> Dict[str, Any]:
        """Process a single task."""
        logger.info(f"Processing task: {task_text[:60]}...")
        self.current_task = task_text
        self.memory.add("task", task_text, importance=3)
        
        # Think about the task
        prompt = f"Task for you:\n\n{task_text}\n\nThink step-by-step and provide a solution."
        
        result_text = await self.think(prompt)
        
        # Record result
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "task": task_text,
            "result": result_text,
        }
        
        # Save result
        result_file = RESULTS_DIR / f"task_{int(time.time())}.json"
        with open(result_file, "w") as f:
            json.dump(result, f, indent=2)
        
        self.memory.add("result", result_text[:200], importance=2)
        self.state["tasks_completed"] += 1
        self._save_state()
        
        logger.info(f"Task completed: {result_file}")
        return result
    
    async def continuous_thinking(self, interval: int = 5, duration: Optional[int] = None):
        """Run continuous thinking loop."""
        logger.info(f"Starting continuous thinking (interval={interval}s)")
        self.memory.add("observation", f"Starting continuous thinking cycle", importance=1)
        
        start_time = time.time()
        while True:
            # Check if duration exceeded
            if duration and (time.time() - start_time) > duration:
                logger.info("Duration limit reached, stopping")
                break
            
            # Check for new tasks
            task_files = list(TASKS_DIR.glob("*.md"))
            if task_files:
                for task_file in task_files:
                    with open(task_file) as f:
                        task_text = f.read()
                    await self.process_task(task_text)
                    task_file.unlink()  # Delete after processing
            
            # Continuous thought
            thought_prompt = "What should you be thinking about right now? Reflect on your goals, recent tasks, and what you're learning."
            thought = await self.think(thought_prompt)
            
            self.memory.add("thought", thought, importance=1)
            self._save_state()
            
            # Log thought (first 100 chars)
            logger.info(f"[thought] {thought[:100]}...")
            
            # Wait before next cycle
            await asyncio.sleep(interval)
    
    def show_memory(self, n: int = 10):
        """Display recent memories."""
        recent = self.memory.recent(n=n)
        print(f"\n=== Last {len(recent)} Memories ===")
        for mem in recent:
            kind_color = {"thought": "💭", "task": "📋", "result": "✅", "observation": "👁️"}.get(mem["kind"], "•")
            print(f"{kind_color} [{mem['kind']}] {mem['content'][:80]}")
        print()
    
    def show_status(self):
        """Display agent status."""
        print(f"\n=== {self.name} Status ===")
        print(f"Started: {self.state['started']}")
        print(f"Cycles: {self.state['cycles']}")
        print(f"Tasks Completed: {self.state['tasks_completed']}")
        print(f"Memories: {len(self.memory.memories)}")
        print(f"Work Dir: {WORK_DIR}")
        print()


async def main():
    global provider_manager
    
    parser = argparse.ArgumentParser(description="ClawServant — CLI specialist agent")
    parser.add_argument("--task", type=str, help="Process a single task")
    parser.add_argument("--continuous", action="store_true", help="Run continuous thinking")
    parser.add_argument("--duration", type=int, help="Duration in seconds (for continuous mode)")
    parser.add_argument("--interval", type=int, default=5, help="Thinking interval in seconds")
    parser.add_argument("--memory", action="store_true", help="Show recent memories")
    parser.add_argument("--status", action="store_true", help="Show status")
    parser.add_argument("--name", type=str, default="Researcher", help="Agent name")
    parser.add_argument("--credentials", type=str, help="Path to credentials.json")
    
    args = parser.parse_args()
    
    # Initialize provider manager
    cred_path = Path(args.credentials) if args.credentials else None
    try:
        provider_manager = ProviderManager(cred_path)
    except Exception as e:
        logger.error(f"Failed to initialize provider manager: {e}")
        sys.exit(1)
    
    # Initialize agent
    agent = ClawServant(name=args.name)
    
    # Execute command
    if args.task:
        result = await agent.process_task(args.task)
        print(json.dumps(result, indent=2))
    
    elif args.continuous:
        try:
            await agent.continuous_thinking(
                interval=args.interval,
                duration=args.duration,
            )
        except KeyboardInterrupt:
            logger.info("Stopped by user")
            agent.memory.add("observation", "Continuous thinking stopped", importance=1)
            agent._save_state()
    
    elif args.memory:
        agent.show_memory()
    
    elif args.status:
        agent.show_status()
        print(f"=== LLM Provider Status ===")
        status = provider_manager.status()
        print(f"Active provider: {status['active_provider']}")
        print(f"Available providers: {status['available_providers']}")
        print(f"Credentials file: {status['credentials_file']}\n")
    
    else:
        # Default: show status and memory
        agent.show_status()
        agent.show_memory()
        print(f"=== LLM Providers ===")
        status = provider_manager.status()
        print(f"Available: {status['available_providers']}")
        print(f"Configured at: {status['credentials_file']}")
        print()


if __name__ == "__main__":
    asyncio.run(main())