"""
Context Manager for Enhanced Agent Communication
Manages shared context, memory, and data flow between BMAD agents
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional


class AgentContext:
    """Manages context data for individual agents"""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.inputs = {}
        self.outputs = {}
        self.metadata = {}
        self.created_at = datetime.now().isoformat()

    def add_input(self, key: str, value: Any):
        """Add input data for this agent"""
        self.inputs[key] = value

    def add_output(self, key: str, value: Any):
        """Add output data from this agent"""
        self.outputs[key] = value

    def add_metadata(self, key: str, value: Any):
        """Add metadata for this agent"""
        self.metadata[key] = value


class ContextManager:
    """Enhanced context manager for BMAD agent communication"""

    def __init__(self):
        self.project_context = {}
        self.agent_contexts: Dict[str, AgentContext] = {}
        self.shared_memory = {}
        self.context_file = ".bmad-core/agent_context.json"

    def initialize_project(self, project_data: Dict[str, Any]):
        """Initialize project-wide context"""
        self.project_context.update(project_data)
        self.project_context["initialized_at"] = datetime.now().isoformat()
        print(f"📋 Project context initialized: {project_data.get('name', 'Unnamed')}")

    def get_agent_context(self, agent_name: str) -> AgentContext:
        """Get or create context for an agent"""
        if agent_name not in self.agent_contexts:
            self.agent_contexts[agent_name] = AgentContext(agent_name)
        return self.agent_contexts[agent_name]

    def pass_data_to_agent(
        self, target_agent: str, source_agent: str, data: Dict[str, Any]
    ):
        """Pass data from one agent to another"""
        target_context = self.get_agent_context(target_agent)

        for key, value in data.items():
            target_context.add_input(f"from_{source_agent}_{key}", value)

        print(f"🔄 Data passed: {source_agent} → {target_agent} ({len(data)} items)")

    def store_agent_output(self, agent_name: str, output_data: Dict[str, Any]):
        """Store output from an agent"""
        agent_context = self.get_agent_context(agent_name)

        for key, value in output_data.items():
            agent_context.add_output(key, value)

        # Also store in shared memory for easy access
        self.shared_memory[f"{agent_name}_output"] = output_data
        print(f"💾 Stored output from {agent_name}")

    def get_relevant_context(self, agent_name: str) -> Dict[str, Any]:
        """Get all relevant context for an agent"""
        context = {
            "project": self.project_context,
            "agent_inputs": self.get_agent_context(agent_name).inputs,
            "shared_memory": self.shared_memory,
        }

        # Add outputs from previous agents in typical workflow
        workflow_order = ["analyst", "pm", "architect", "developer", "qa", "validator"]

        try:
            current_index = workflow_order.index(agent_name)
            for i in range(current_index):
                prev_agent = workflow_order[i]
                if f"{prev_agent}_output" in self.shared_memory:
                    context[f"previous_{prev_agent}"] = self.shared_memory[
                        f"{prev_agent}_output"
                    ]
        except ValueError:
            pass  # Agent not in standard workflow

        return context

    def save_context(self):
        """Save context to file"""
        context_data = {
            "project_context": self.project_context,
            "shared_memory": self.shared_memory,
            "agent_contexts": {
                name: {
                    "inputs": ctx.inputs,
                    "outputs": ctx.outputs,
                    "metadata": ctx.metadata,
                    "created_at": ctx.created_at,
                }
                for name, ctx in self.agent_contexts.items()
            },
            "saved_at": datetime.now().isoformat(),
        }

        os.makedirs(".bmad-core", exist_ok=True)
        with open(self.context_file, "w") as f:
            json.dump(context_data, f, indent=2)

        print(f"💾 Context saved to {self.context_file}")

    def load_context(self) -> bool:
        """Load context from file"""
        if not os.path.exists(self.context_file):
            return False

        try:
            with open(self.context_file, "r") as f:
                context_data = json.load(f)

            self.project_context = context_data.get("project_context", {})
            self.shared_memory = context_data.get("shared_memory", {})

            # Reconstruct agent contexts
            for name, ctx_data in context_data.get("agent_contexts", {}).items():
                ctx = AgentContext(name)
                ctx.inputs = ctx_data.get("inputs", {})
                ctx.outputs = ctx_data.get("outputs", {})
                ctx.metadata = ctx_data.get("metadata", {})
                ctx.created_at = ctx_data.get("created_at", datetime.now().isoformat())
                self.agent_contexts[name] = ctx

            print(f"📂 Context loaded from {self.context_file}")
            return True

        except Exception as e:
            print(f"❌ Error loading context: {e}")
            return False

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of current context state"""
        return {
            "project_name": self.project_context.get("name", "Unknown"),
            "active_agents": list(self.agent_contexts.keys()),
            "shared_data_items": len(self.shared_memory),
            "total_inputs": sum(
                len(ctx.inputs) for ctx in self.agent_contexts.values()
            ),
            "total_outputs": sum(
                len(ctx.outputs) for ctx in self.agent_contexts.values()
            ),
        }
