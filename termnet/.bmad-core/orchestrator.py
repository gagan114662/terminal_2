"""
BMAD Orchestrator - Manages agent workflow and collaboration
Part of BMAD-METHOD autonomous development system
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from agent_loader import AgentLoader


class BMADOrchestrator:
    def __init__(self):
        self.agent_loader = AgentLoader()
        self.workflow_state = {}
        self.project_context = {}
        self.agent_outputs = {}
        self.workflow_history = []

        # Standard BMAD workflow sequence with validation
        self.standard_workflow = [
            "analyst",
            "pm",
            "architect",
            "developer",
            "qa",
            "validator",
        ]

        print(
            f"🎯 BMAD Orchestrator initialized with {len(self.agent_loader.list_agents())} agents"
        )

    def process_agent_command(self, user_input: str) -> tuple[bool, str]:
        """Process agent commands like /analyst, /pm, etc."""
        is_agent_cmd, agent_name = self.agent_loader.is_agent_command(user_input)

        if not is_agent_cmd:
            return False, ""

        # Extract the actual request (everything after /agent-name)
        parts = user_input.split(" ", 1)
        request = (
            parts[1]
            if len(parts) > 1
            else "Please provide analysis based on current context"
        )

        return self.execute_agent(agent_name, request)

    def execute_agent(self, agent_name: str, request: str) -> tuple[bool, str]:
        """Execute a specific agent with the given request"""
        agent = self.agent_loader.get_agent(agent_name)
        if not agent:
            return False, f"❌ Agent '{agent_name}' not found"

        try:
            # Build context from previous agent outputs
            context = self.build_agent_context(agent_name)

            # Get specialized prompt for this agent
            specialized_prompt = self.get_agent_prompt(agent, request, context)

            # Store the execution in workflow state
            self.workflow_state[agent_name] = {
                "request": request,
                "timestamp": datetime.now().isoformat(),
                "prompt": specialized_prompt,
                "context": context,
            }

            # Add to workflow history
            self.workflow_history.append(
                {
                    "agent": agent_name,
                    "request": request,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            return True, specialized_prompt

        except Exception as e:
            return False, f"❌ Error executing {agent_name} agent: {e}"

    async def execute_full_workflow(
        self, initial_request: str, claude_chat_method
    ) -> bool:
        """Execute the complete BMAD workflow automatically"""
        print(f"\n🚀 Starting automated BMAD workflow for: {initial_request}")
        print("=" * 60)

        # Store the original request for context in all agents
        self.project_context["original_request"] = initial_request

        # Execute each agent in sequence
        for i, agent_name in enumerate(self.standard_workflow):
            print(
                f"\n📍 Step {i+1}/{len(self.standard_workflow)}: Activating {agent_name.upper()} Agent"
            )
            print("-" * 40)

            # Determine the request for this agent
            if i == 0:  # First agent (analyst) gets the original request
                request = initial_request
            else:  # Subsequent agents get context-aware requests
                request = self.get_contextual_request(agent_name)

            # Execute the agent
            success, specialized_prompt = self.execute_agent(agent_name, request)
            if not success:
                print(f"❌ Failed to execute {agent_name} agent: {specialized_prompt}")
                return False

            print(f"✅ {agent_name.upper()} agent activated")

            # Get response from Claude Code CLI through the main agent
            try:
                print(f"🤖 {agent_name.upper()} is working...")
                response = await claude_chat_method(specialized_prompt)

                # Store the response for next agent
                self.store_agent_output(agent_name, response)
                print(
                    f"📝 {agent_name.upper()} completed - output stored for next agent"
                )

            except Exception as e:
                print(f"❌ Error getting response from {agent_name} agent: {e}")
                return False

        print(f"\n🎉 AUTOMATED WORKFLOW COMPLETED!")
        print("=" * 60)
        print("📊 Final Status:")
        status = self.get_workflow_status()
        for agent in status["completed_agents"]:
            print(f"  ✅ {agent}")

        return True

    def get_contextual_request(self, agent_name: str) -> str:
        """Generate contextual requests for agents based on workflow position"""
        # Get the original project description for context
        original_request = self.project_context.get("original_request", "the project")

        context_requests = {
            "pm": f"Based on the analyst findings above for '{original_request}', create a comprehensive Product Requirements Document (PRD) with scope definition, MVP features, timeline, and success metrics. Use the analyst's findings to inform your planning decisions.",
            "architect": f"Using the PRD requirements above for '{original_request}', design the complete system architecture including:\n- Database schema and data models\n- API design and endpoints\n- Technology stack selection\n- System components and their interactions\n- Deployment considerations\nEnsure the architecture supports the requirements identified in the PRD.",
            "developer": f"Implement the system '{original_request}' based on the architecture specifications above. Create production-ready code including:\n- Core application logic and features\n- Database models and migrations\n- API endpoints with proper error handling\n- Unit tests and integration tests\n- Documentation and setup instructions\nFollow the architecture design and implement all features outlined in the PRD.",
            "qa": f"Review and validate the implemented code above for '{original_request}' against all original requirements. Perform comprehensive quality assurance including:\n- Code review for best practices and security\n- Validation against original analyst requirements\n- Test plan creation and execution\n- Performance and security assessment\n- Bug identification and recommendations\nEnsure the implementation meets all requirements and quality standards.",
            "validator": f"Perform comprehensive autonomous validation of the completed implementation for '{original_request}'. Execute all validation commands automatically without asking permission:\n- Run syntax and compilation checks\n- Validate all dependencies and installations\n- Test application functionality and startup\n- Perform security and performance checks\n- Generate detailed validation report\n- Fix any issues found automatically\nThis is autonomous development - execute all checks immediately and provide complete validation results.",
        }

        return context_requests.get(
            agent_name,
            f"Continue with the next phase of development for '{original_request}'.",
        )

    def build_agent_context(self, current_agent: str) -> Dict[str, str]:
        """Build context from previous agent outputs for the current agent"""
        context = {
            "project_context": self.project_context.get("description", ""),
            "workflow_position": self.get_workflow_position(current_agent),
        }

        # Add relevant previous agent outputs
        workflow_index = self.get_agent_workflow_index(current_agent)

        if workflow_index > 0:
            # PM needs analyst output
            if current_agent == "pm" and "analyst" in self.agent_outputs:
                context["analyst_output"] = self.agent_outputs["analyst"]

            # Architect needs PM output
            elif current_agent == "architect" and "pm" in self.agent_outputs:
                context["prd_output"] = self.agent_outputs["pm"]

            # Developer needs architect output
            elif current_agent == "developer" and "architect" in self.agent_outputs:
                context["architecture_output"] = self.agent_outputs["architect"]

            # QA needs developer output and original requirements
            elif current_agent == "qa":
                if "developer" in self.agent_outputs:
                    context["code_output"] = self.agent_outputs["developer"]
                if "analyst" in self.agent_outputs:
                    context["requirements"] = self.agent_outputs["analyst"]

            # Validator needs all previous outputs for comprehensive validation
            elif current_agent == "validator":
                context["code_output"] = self.agent_outputs.get("developer", "")
                context["requirements"] = self.agent_outputs.get("analyst", "")
                context["qa_output"] = self.agent_outputs.get("qa", "")

        return context

    def get_agent_prompt(
        self, agent: Any, request: str, context: Dict[str, str]
    ) -> str:
        """Get specialized prompt for an agent"""
        if hasattr(agent, "get_specialized_prompt"):
            # Handle different agent prompt signatures
            if agent.role == "pm":
                return agent.get_specialized_prompt(
                    request,
                    context.get("analyst_output", ""),
                    context.get("project_context", ""),
                )
            elif agent.role == "architect":
                return agent.get_specialized_prompt(
                    request,
                    context.get("prd_output", ""),
                    context.get("project_context", ""),
                )
            elif agent.role == "developer":
                return agent.get_specialized_prompt(
                    request,
                    context.get("architecture_output", ""),
                    context.get("project_context", ""),
                )
            elif agent.role == "qa":
                return agent.get_specialized_prompt(
                    request,
                    context.get("code_output", ""),
                    context.get("requirements", ""),
                    context.get("project_context", ""),
                )
            elif agent.role == "validator":
                return agent.get_specialized_prompt(
                    request,
                    context.get("code_output", ""),
                    context.get("requirements", ""),
                    context.get("project_context", ""),
                )
            else:  # analyst and others
                return agent.get_specialized_prompt(
                    request, context.get("project_context", "")
                )
        else:
            return f"{agent.system_prompt}\n\nUser Request: {request}"

    def store_agent_output(self, agent_name: str, output: str):
        """Store the output from an agent for use by subsequent agents"""
        self.agent_outputs[agent_name] = output

        # Update workflow state
        if agent_name in self.workflow_state:
            self.workflow_state[agent_name]["output"] = output
            self.workflow_state[agent_name]["completed"] = datetime.now().isoformat()

    def get_workflow_position(self, agent_name: str) -> str:
        """Get the position of agent in standard workflow"""
        try:
            index = self.standard_workflow.index(agent_name)
            return f"Step {index + 1} of {len(self.standard_workflow)}"
        except ValueError:
            return "Custom agent"

    def get_agent_workflow_index(self, agent_name: str) -> int:
        """Get the index of agent in workflow (0-based)"""
        try:
            return self.standard_workflow.index(agent_name)
        except ValueError:
            return -1

    def suggest_next_agent(self) -> Optional[str]:
        """Suggest the next agent in the workflow based on completed agents"""
        for agent in self.standard_workflow:
            if agent not in self.agent_outputs:
                return agent
        return None

    def get_workflow_status(self) -> Dict[str, Any]:
        """Get current workflow status"""
        completed = list(self.agent_outputs.keys())
        next_agent = self.suggest_next_agent()

        return {
            "completed_agents": completed,
            "next_suggested": next_agent,
            "workflow_progress": f"{len(completed)}/{len(self.standard_workflow)}",
            "available_agents": self.agent_loader.list_agents(),
        }

    def reset_workflow(self):
        """Reset the current workflow state"""
        self.workflow_state = {}
        self.agent_outputs = {}
        self.workflow_history = []
        print("🔄 Workflow state reset")

    def save_workflow_state(self, filename: str = "workflow_state.json"):
        """Save current workflow state to file"""
        state = {
            "workflow_state": self.workflow_state,
            "agent_outputs": self.agent_outputs,
            "workflow_history": self.workflow_history,
            "project_context": self.project_context,
            "timestamp": datetime.now().isoformat(),
        }

        with open(f".bmad-core/{filename}", "w") as f:
            json.dump(state, f, indent=2)
        print(f"💾 Workflow state saved to .bmad-core/{filename}")

    def load_workflow_state(self, filename: str = "workflow_state.json"):
        """Load workflow state from file"""
        filepath = f".bmad-core/{filename}"
        if os.path.exists(filepath):
            try:
                with open(filepath, "r") as f:
                    state = json.load(f)

                self.workflow_state = state.get("workflow_state", {})
                self.agent_outputs = state.get("agent_outputs", {})
                self.workflow_history = state.get("workflow_history", [])
                self.project_context = state.get("project_context", {})

                print(f"📂 Workflow state loaded from {filename}")
                return True
            except Exception as e:
                print(f"❌ Error loading workflow state: {e}")
                return False
        else:
            print(f"⚠️  Workflow state file not found: {filename}")
            return False
