"""
Agent Loader - Dynamic loading and management of BMAD agents
Part of BMAD-METHOD autonomous development system
"""

import importlib.util
import os
from typing import Any, Dict, List, Optional


class AgentLoader:
    def __init__(self, agents_dir: str = ".bmad-core/agents"):
        self.agents_dir = agents_dir
        self.agents: Dict[str, Any] = {}
        self.agent_instances: Dict[str, Any] = {}
        self.load_all_agents()

    def load_all_agents(self):
        """Load all agent classes from the agents directory"""
        if not os.path.exists(self.agents_dir):
            print(f"⚠️  Agents directory not found: {self.agents_dir}")
            return

        for filename in os.listdir(self.agents_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                agent_name = filename[:-3]  # Remove .py extension
                self.load_agent(agent_name, filename)

    def load_agent(self, agent_name: str, filename: str):
        """Load a specific agent class"""
        try:
            file_path = os.path.join(self.agents_dir, filename)
            spec = importlib.util.spec_from_file_location(agent_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find the agent class (should be {AgentName}Agent)
            # Handle special cases for PM and QA (uppercase)
            if agent_name == "pm":
                class_name = "PMAgent"
            elif agent_name == "qa":
                class_name = "QAAgent"
            else:
                class_name = f"{agent_name.title()}Agent"
            if hasattr(module, class_name):
                agent_class = getattr(module, class_name)
                self.agents[agent_name] = agent_class
                self.agent_instances[agent_name] = agent_class()
                print(f"✅ Loaded agent: {agent_name}")
            else:
                print(f"⚠️  Agent class {class_name} not found in {filename}")

        except Exception as e:
            print(f"❌ Failed to load agent {agent_name}: {e}")

    def get_agent(self, agent_name: str) -> Optional[Any]:
        """Get an agent instance by name"""
        return self.agent_instances.get(agent_name.lower())

    def list_agents(self) -> List[str]:
        """List all loaded agents"""
        return list(self.agent_instances.keys())

    def get_agent_commands(self, agent_name: str) -> List[str]:
        """Get supported commands for an agent"""
        agent = self.get_agent(agent_name)
        if agent and hasattr(agent, "supports_commands"):
            return agent.supports_commands()
        return []

    def get_all_commands(self) -> Dict[str, List[str]]:
        """Get all commands from all agents"""
        all_commands = {}
        for agent_name in self.agent_instances.keys():
            all_commands[agent_name] = self.get_agent_commands(agent_name)
        return all_commands

    def is_agent_command(self, text: str) -> tuple[bool, Optional[str]]:
        """Check if text starts with an agent command (/agent-name)"""
        if text.startswith("/"):
            parts = text.split(" ", 1)
            command = parts[0][1:]  # Remove the /
            if command in self.agent_instances:
                return True, command
        return False, None
