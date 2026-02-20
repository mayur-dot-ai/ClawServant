#!/usr/bin/env python3
"""
ClawServant — CLI-first specialist agent for OpenClaw.

A lean, self-contained AI employee that:
- Thinks continuously (5-second cycles)
- Persists memory across restarts
- Processes tasks from files or CLI
- Outputs structured results (JSON/markdown)
- Supports any LLM provider (Bedrock, Anthropic, OpenAI, Ollama)

V2 Changes:
- XML delimiter-based tool detection (<tool>...</tool>)
- Multi-tool loop within think() for tool chaining
- Reliable tool execution without regex fragility

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
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List
import re

from providers import ProviderManager

# Try to import tool manager (optional)
try:
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from tools.tool_manager import ToolManager
    TOOLS_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    TOOLS_AVAILABLE = False
    ToolManager = None

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("clawservant")

def get_work_dir() -> Path:
    """Get work directory (defaults to current working directory).
    
    All work folders (brain/, tasks/, results/) are relative to cwd.
    This ensures portability and allows multiple instances to run simultaneously.
    
    Supports CLAWSERVANT_WORK_DIR override for alternative locations.
    """
    # Default: current working directory (where the user ran the script from)
    return Path(os.getenv("CLAWSERVANT_WORK_DIR", "."))

def get_paths():
    """Get all paths dynamically to support runtime overrides."""
    work_dir = get_work_dir()
    return {
        "work_dir": work_dir,
        "memory": work_dir / "memory.jsonl",
        "state": work_dir / "state.json",
        "tasks": work_dir / "tasks",
        "results": work_dir / "results",
        "brain": work_dir / "brain",
        "personality": work_dir / "personality",
        "rules": work_dir / "rules",
    }

# Initialize paths at startup
PATHS = get_paths()
WORK_DIR = PATHS["work_dir"]
MEMORY_FILE = PATHS["memory"]
STATE_FILE = PATHS["state"]
TASKS_DIR = PATHS["tasks"]
RESULTS_DIR = PATHS["results"]
BRAIN_DIR = PATHS["brain"]
PERSONALITY_DIR = PATHS["personality"]
RULES_DIR = PATHS["rules"]

# Ensure directories exist
for d in [WORK_DIR, TASKS_DIR, RESULTS_DIR, BRAIN_DIR, PERSONALITY_DIR, RULES_DIR]:
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
            "timestamp": datetime.now(timezone.utc).isoformat(),
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
    """Specialist agent powered by flexible LLM providers and tools."""
    
    def __init__(self, name: str = "Developer", use_tools: bool = True):
        self.name = name
        self.memory = Memory()
        self.state = self._load_state()
        self.personality = self._load_personality()
        self.rules = self._load_rules()
        self.brain = self._load_brain()
        self.brain_mtime = self._get_brain_mtime()
        self.current_task = None
        
        # Initialize tool manager if available
        self.tool_manager = None
        if use_tools and TOOLS_AVAILABLE:
            try:
                self.tool_manager = ToolManager(WORK_DIR / "tools")
                logger.info(f"Tool manager initialized: {len(self.tool_manager.tools)} tools available")
            except Exception as e:
                logger.warning(f"Failed to initialize tool manager: {e}")
        
        logger.info(f"ClawServant ({self.name}) initialized")
    
    def _load_state(self) -> Dict[str, Any]:
        """Load state from file."""
        if STATE_FILE.exists():
            with open(STATE_FILE) as f:
                return json.load(f)
        return {
            "name": self.name,
            "started": datetime.now(timezone.utc).isoformat(),
            "cycles": 0,
            "tasks_completed": 0,
        }
    
    def _load_personality(self) -> str:
        """Load personality file from personality/ folder."""
        personality_file = WORK_DIR / "personality" / "personality.md"
        if personality_file.exists():
            with open(personality_file) as f:
                logger.info("Loaded personality from personality/personality.md")
                return f.read()
        return ""
    
    def _load_rules(self) -> str:
        """Load rules file (if/then behavior guidelines)."""
        rules_file = WORK_DIR / "rules" / "rules.md"
        if rules_file.exists():
            with open(rules_file) as f:
                logger.info("Loaded rules from rules/rules.md")
                return f.read()
        return ""
    
    def _get_brain_mtime(self) -> float:
        """Get the latest modification time in brain folder."""
        if not BRAIN_DIR.exists():
            return 0
        
        brain_files = list(BRAIN_DIR.glob("*.md")) + list(BRAIN_DIR.glob("*.txt"))
        if not brain_files:
            return 0
        
        # Return the most recent mtime
        return max(f.stat().st_mtime for f in brain_files)
    
    def _load_brain(self) -> str:
        """Load all brain files from brain/ folder in alphabetical order."""
        brain_content = ""
        
        if not BRAIN_DIR.exists():
            return brain_content
        
        # Get all .md and .txt files, sorted alphabetically
        brain_files = sorted(list(BRAIN_DIR.glob("*.md")) + list(BRAIN_DIR.glob("*.txt")))
        if brain_files:
            logger.info(f"Loaded {len(brain_files)} brain files in alphabetical order")
            for brain_file in brain_files:
                if brain_file.name.startswith("_"):
                    continue  # Skip readme files
                with open(brain_file) as f:
                    brain_content += f"\n\n## {brain_file.stem}\n{f.read()}"
        
        return brain_content
    
    def _check_brain_updated(self) -> bool:
        """Check if brain files have been updated since last load."""
        current_mtime = self._get_brain_mtime()
        if current_mtime > self.brain_mtime:
            logger.info("Brain files updated, reloading...")
            self.brain = self._load_brain()
            self.brain_mtime = current_mtime
            return True
        return False
    
    def _save_state(self):
        """Save state to file."""
        self.state["cycles"] += 1
        self.state["last_cycle"] = datetime.now(timezone.utc).isoformat()
        with open(STATE_FILE, "w") as f:
            json.dump(self.state, f, indent=2)
    
    def _extract_tool_calls(self, text: str) -> List[Dict[str, Any]]:
        """Extract tool calls from LLM response using XML delimiters.
        
        Looks for: <tool>{"tool": "name", "params": {...}}</tool>
        
        Returns list of parsed tool call dicts.
        """
        tool_calls = []
        pattern = r'<tool>(.*?)</tool>'
        matches = re.findall(pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                # Clean up the JSON (strip whitespace, handle newlines)
                json_str = match.strip()
                tool_call = json.loads(json_str)
                
                # Validate structure
                if "tool" in tool_call and "params" in tool_call:
                    tool_calls.append(tool_call)
                    logger.debug(f"Parsed tool call: {tool_call['tool']}")
                else:
                    logger.warning(f"Invalid tool call structure: {tool_call}")
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse tool call JSON: {e}")
                logger.debug(f"Raw content: {match[:100]}")
        
        return tool_calls
    
    async def think(self, prompt: str, allow_tools: bool = True, max_tool_iterations: int = 10) -> str:
        """Call LLM via provider manager, with multi-tool support.
        
        V2 Change: Now loops until LLM stops requesting tools or max_tool_iterations reached.
        This allows: read file → analyze → post comment in ONE think() call.
        """
        # Build system prompt
        system_prompt = f"""You are {self.name}, a specialist AI agent.

"""
        
        # Add personality if available
        if self.personality:
            system_prompt += f"## Your Personality\n{self.personality}\n\n"
        else:
            system_prompt += f"""Your role:
- Think deeply about problems
- Remember previous insights (you have access to your memory)
- Complete tasks methodically
- Output clear, actionable results

"""
        
        # Add rules (behavior guidelines)
        if self.rules:
            system_prompt += f"## Your Rules\n{self.rules}\n\n"
        
        # Add brain/knowledge files
        if self.brain:
            system_prompt += f"## Your Knowledge\n{self.brain}\n\n"
        
        # Add tools if available
        if allow_tools and self.tool_manager:
            available_tools = await self.tool_manager.available_tools()
            if available_tools:
                system_prompt += f"""## Available Tools

You have access to tools. To call a tool, use XML delimiters:

<tool>{{"tool": "tool_name", "params": {{"param": "value"}}}}</tool>

CRITICAL:
- Wrap the JSON in <tool>...</tool> tags
- Use valid JSON inside the tags
- You can call MULTIPLE tools in one response
- After tool results, you'll get context to continue

Available tools:

"""
                for tool in available_tools:
                    system_prompt += f"### {tool['name']}\n"
                    system_prompt += f"{tool['description']}\n"
                    
                    # Add specific parameter docs for each tool
                    if tool['name'] == 'file-io':
                        system_prompt += """Parameters:
- action: "read" | "write" | "append" | "delete" | "list"
- path: file or directory path
- content: (for write/append) the content to write

Example: <tool>{"tool": "file-io", "params": {"action": "read", "path": "file.txt"}}</tool>

"""
                    elif tool['name'] == 'web-fetch':
                        system_prompt += """Parameters:
- url: the website URL
- action: "fetch" | "extract" | "links" | "metadata"
- format: (for extract) "markdown" or "text"

Example: <tool>{"tool": "web-fetch", "params": {"url": "https://example.com", "action": "extract", "format": "text"}}</tool>

"""
                    elif tool['name'] == 'headless-browser':
                        system_prompt += """Parameters:
- url: the website URL
- action: "screenshot" | "click" | "type" | "scroll" | "wait_for" | "get_text"
- selector: (for click/type/wait_for) CSS selector
- text: (for type) text to type

Example: <tool>{"tool": "headless-browser", "params": {"url": "https://example.com", "action": "screenshot"}}</tool>

"""
                    elif tool['name'] == 'shell-exec':
                        system_prompt += """Parameters:
- command: shell command to execute
- timeout: (optional) timeout in seconds
- cwd: (optional) working directory

Example: <tool>{"tool": "shell-exec", "params": {"command": "ls -la /tmp"}}</tool>

"""
                    system_prompt += "\n"
        
        # Add context
        system_prompt += f"""## Current Context

Time: {datetime.now(timezone.utc).isoformat()}
Cycle: {self.state['cycles']}
Tasks completed: {self.state['tasks_completed']}

## Recent Memory
"""
        recent = self.memory.recent(n=5)
        for mem in recent:
            system_prompt += f"\n- [{mem['kind']}] {mem['content'][:100]}..."
        
        # Multi-tool loop
        current_prompt = prompt
        tool_iteration = 0
        conversation_history = []
        
        while tool_iteration < max_tool_iterations:
            # Call LLM
            try:
                thought, provider_used = await provider_manager.call(
                    system_prompt, current_prompt, max_tokens=500
                )
                if self.state['cycles'] == 0 and tool_iteration == 0:  # Log on first cycle
                    logger.info(f"Using provider: {provider_used}")
                
                conversation_history.append({"role": "assistant", "content": thought})
                
                # Check for tool calls (if tools enabled)
                if allow_tools and self.tool_manager:
                    tool_calls = self._extract_tool_calls(thought)
                    
                    if tool_calls:
                        logger.info(f"🔧 Found {len(tool_calls)} tool call(s) in iteration {tool_iteration + 1}")
                        
                        # Execute all tool calls
                        tool_results = []
                        for tool_call in tool_calls:
                            tool_name = tool_call["tool"]
                            tool_params = tool_call["params"]
                            
                            logger.info(f"  ✅ Executing: {tool_name}")
                            
                            try:
                                result = await self.tool_manager.call_tool(tool_name, **tool_params)
                                tool_results.append({
                                    "tool": tool_name,
                                    "params": tool_params,
                                    "result": result,
                                    "success": True
                                })
                                self.memory.add("tool_call", f"{tool_name}: {json.dumps(result)[:200]}", importance=2)
                            except Exception as e:
                                logger.error(f"  ❌ Tool execution failed: {e}")
                                tool_results.append({
                                    "tool": tool_name,
                                    "params": tool_params,
                                    "error": str(e),
                                    "success": False
                                })
                        
                        # Build next prompt with tool results
                        results_text = "\n\n".join([
                            f"Tool: {r['tool']}\nResult: {json.dumps(r.get('result') or r.get('error'), indent=2)}"
                            for r in tool_results
                        ])
                        
                        current_prompt = f"Tool results:\n\n{results_text}\n\nContinue with your task. If you need more tools, call them. If done, provide your final response."
                        tool_iteration += 1
                        
                        # Continue loop (call LLM again with tool results)
                        continue
                
                # No tool calls found, we're done
                logger.info(f"✅ No more tool calls, think() complete after {tool_iteration} tool iteration(s)")
                return thought
                
            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                return f"[ERROR] Failed to think: {e}"
        
        # Max tool iterations reached
        logger.warning(f"⚠️ Max tool iterations ({max_tool_iterations}) reached")
        return thought
    
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
            "timestamp": datetime.now(timezone.utc).isoformat(),
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
    

    def parse_task_frontmatter(self, task_text: str) -> tuple:
        """Parse frontmatter from task file. Returns (metadata, content)."""
        import re
        frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
        match = re.match(frontmatter_pattern, task_text, re.DOTALL)
        
        if match:
            # Simple key: value parsing (no yaml dependency)
            metadata = {}
            for line in match.group(1).split('\n'):
                if ':' in line:
                    key, val = line.split(':', 1)
                    metadata[key.strip()] = val.strip()
            content = match.group(2)
            return metadata, content
        
        return {}, task_text

    async def process_task_with_loop(self, task_text: str, max_iterations: int = 10) -> dict:
        """Process task with loop until TASK_DONE or max iterations."""
        metadata, content = self.parse_task_frontmatter(task_text)
        iteration = int(metadata.get('iteration', 1))
        task_id = metadata.get('task_id', f"task_{int(time.time())}")
        
        logger.info(f"Processing task {task_id} with loop (max {max_iterations} iterations)")
        self.current_task = content
        self.memory.add("task", f"[Loop] {content[:100]}...", importance=3)
        
        final_result = None
        result_text = ""
        
        while iteration <= max_iterations:
            logger.info(f"🔄 Loop iteration {iteration}/{max_iterations}")
            
            # Build prompt with iteration context
            prompt = f"""Task for you (Iteration {iteration}/{max_iterations}):

{content}

IMPORTANT: When you have fully completed ALL steps of the task, include TASK_DONE in your response.
If you need to do more work, continue without TASK_DONE."""
            
            # Think and get result (multi-tool support within each iteration)
            result_text = await self.think(prompt)
            
            # Check for completion signal
            if "TASK_DONE" in result_text:
                logger.info(f"✅ TASK_DONE signal received at iteration {iteration}")
                final_result = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "task_id": task_id,
                    "task": content,
                    "result": result_text,
                    "iterations": iteration,
                    "status": "complete"
                }
                break
            
            # Not done yet
            logger.info(f"⏳ No TASK_DONE signal, iteration {iteration} complete")
            self.memory.add("iteration", f"Iter {iteration}: {result_text[:100]}...", importance=2)
            iteration += 1
        
        # Max iterations reached without completion
        if final_result is None:
            logger.warning(f"⚠️ Max iterations ({max_iterations}) reached without TASK_DONE")
            final_result = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "task_id": task_id,
                "task": content,
                "result": result_text,
                "iterations": iteration - 1,
                "status": "max_iterations_reached"
            }
        
        # Save result
        result_file = RESULTS_DIR / f"{task_id}.json"
        with open(result_file, "w") as f:
            json.dump(final_result, f, indent=2)
        
        self.memory.add("result", f"Task {task_id}: {final_result['status']} in {final_result['iterations']} iterations", importance=2)
        self.state["tasks_completed"] += 1
        self._save_state()
        
        logger.info(f"Task completed: {result_file} (status: {final_result['status']})")
        return final_result

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
            
            # Check for brain file updates
            self._check_brain_updated()
            
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
        print(f"  brain/: {list(BRAIN_DIR.glob('*')) if BRAIN_DIR.exists() else 'empty'}")
        print(f"  tasks/: {list(TASKS_DIR.glob('*')) if TASKS_DIR.exists() else 'empty'}")
        
        # Show tool status if available
        if self.tool_manager:
            tool_status = self.tool_manager.status()
            print(f"\n=== Tools ===")
            print(f"Tools Available: {tool_status['tools_available']}")
            print(f"Tools: {', '.join(tool_status['tool_names']) if tool_status['tool_names'] else 'none'}")
            print(f"Total Tool Calls: {tool_status['total_calls']}")
            print(f"Total Tool Cost: ${tool_status['total_cost']:.4f}")
        print()


async def main():
    global provider_manager, PATHS, WORK_DIR, MEMORY_FILE, STATE_FILE, TASKS_DIR, RESULTS_DIR, BRAIN_DIR
    
    # Re-initialize paths to support runtime CLAWSERVANT_WORK_DIR override
    PATHS = get_paths()
    WORK_DIR = PATHS["work_dir"]
    MEMORY_FILE = PATHS["memory"]
    STATE_FILE = PATHS["state"]
    TASKS_DIR = PATHS["tasks"]
    RESULTS_DIR = PATHS["results"]
    BRAIN_DIR = PATHS["brain"]
    
    # Ensure directories exist
    for d in [WORK_DIR, TASKS_DIR, RESULTS_DIR, BRAIN_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    
    parser = argparse.ArgumentParser(description="ClawServant — CLI specialist agent")
    parser.add_argument("--task", type=str, help="Process a single task")
    parser.add_argument("--continuous", action="store_true", help="Run continuous thinking")
    parser.add_argument("--duration", type=int, help="Duration in seconds (for continuous mode)")
    parser.add_argument("--interval", type=int, default=5, help="Thinking interval in seconds")
    parser.add_argument("--memory", action="store_true", help="Show recent memories")
    parser.add_argument("--status", action="store_true", help="Show status")
    parser.add_argument("--name", type=str, default="Developer", help="Agent name")
    parser.add_argument("--loop", action="store_true", help="Enable loop mode (iterate until TASK_DONE)")
    parser.add_argument("--max-iterations", type=int, default=10, help="Max iterations in loop mode")
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
        if args.loop:
            result = await agent.process_task_with_loop(args.task, max_iterations=args.max_iterations)
        else:
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