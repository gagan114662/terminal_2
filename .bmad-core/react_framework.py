"""
ReAct Framework for BMAD Agents
Implements Reasoning + Acting pattern for autonomous development tasks
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional


class ReActStep:
    """Individual step in ReAct reasoning chain"""

    def __init__(self, step_type: str, content: str, result: str = ""):
        self.step_type = step_type  # "thought", "action", "observation"
        self.content = content
        self.result = result
        self.timestamp = datetime.now().isoformat()


class ReActFramework:
    """ReAct (Reasoning + Acting) framework for BMAD agents"""

    def __init__(self):
        self.steps: List[ReActStep] = []
        self.current_goal = ""
        self.context = {}

    def set_goal(self, goal: str):
        """Set the current goal for the reasoning chain"""
        self.current_goal = goal
        self.steps = []

    def add_thought(self, thought: str) -> ReActStep:
        """Add a reasoning step"""
        step = ReActStep("thought", thought)
        self.steps.append(step)
        return step

    def add_action(self, action: str, terminal_cmd: str = "") -> ReActStep:
        """Add an action step with optional terminal command"""
        action_content = f"{action}"
        if terminal_cmd:
            action_content += f"\nTerminal Command: {terminal_cmd}"
        step = ReActStep("action", action_content)
        self.steps.append(step)
        return step

    def add_observation(self, observation: str) -> ReActStep:
        """Add an observation from action results"""
        step = ReActStep("observation", observation)
        self.steps.append(step)
        return step

    def get_reasoning_chain(self) -> str:
        """Get formatted reasoning chain for prompt"""
        chain = f"Goal: {self.current_goal}\n\n"

        for i, step in enumerate(self.steps, 1):
            chain += f"Step {i} - {step.step_type.upper()}:\n"
            chain += f"{step.content}\n"
            if step.result:
                chain += f"Result: {step.result}\n"
            chain += "\n"

        return chain

    def should_continue(self) -> bool:
        """Determine if reasoning chain should continue"""
        if len(self.steps) == 0:
            return True

        # Stop if last step was successful observation
        last_step = self.steps[-1]
        if (
            last_step.step_type == "observation"
            and "completed" in last_step.content.lower()
        ):
            return False

        # Stop if too many steps (prevent infinite loops)
        if len(self.steps) > 10:
            return False

        return True

    def save_chain(self, filename: str):
        """Save reasoning chain to file"""
        chain_data = {
            "goal": self.current_goal,
            "steps": [
                {
                    "type": step.step_type,
                    "content": step.content,
                    "result": step.result,
                    "timestamp": step.timestamp,
                }
                for step in self.steps
            ],
            "context": self.context,
        }

        with open(f".bmad-core/{filename}", "w") as f:
            json.dump(chain_data, f, indent=2)
