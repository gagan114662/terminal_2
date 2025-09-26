"""
BMAD Integration for TermNet
Integrates BMAD-METHOD autonomous development system with TermNet
"""

import os
import sys
from typing import Optional, Tuple

# Add the .bmad-core directory to Python path
sys.path.insert(0, ".bmad-core")

try:
    from orchestrator import BMADOrchestrator
except ImportError:
    print("⚠️  BMAD-METHOD system not found. Run from project root directory.")
    BMADOrchestrator = None


class BMADIntegration:
    def __init__(self):
        self.orchestrator = None
        self.enabled = False
        self.initialize_bmad()

    def initialize_bmad(self):
        """Initialize BMAD orchestrator if available"""
        if BMADOrchestrator and os.path.exists(".bmad-core"):
            try:
                self.orchestrator = BMADOrchestrator()
                self.enabled = True
                print("🚀 BMAD-METHOD integration enabled")
            except Exception as e:
                print(f"⚠️  BMAD initialization failed: {e}")
                self.enabled = False
        else:
            print("⚠️  BMAD-METHOD system not available")
            self.enabled = False

    def is_bmad_command(self, user_input: str) -> bool:
        """Check if input is a BMAD agent command"""
        if not self.enabled or not self.orchestrator:
            return False

        is_cmd, _ = self.orchestrator.agent_loader.is_agent_command(user_input)
        return is_cmd

    def process_bmad_command(self, user_input: str) -> Tuple[bool, str]:
        """Process BMAD agent commands and return specialized prompt"""
        if not self.enabled or not self.orchestrator:
            return False, "BMAD-METHOD not available"

        success, result = self.orchestrator.process_agent_command(user_input)
        return success, result

    async def execute_automated_workflow(
        self, user_input: str, claude_chat_method
    ) -> bool:
        """Execute complete automated BMAD workflow"""
        if not self.enabled or not self.orchestrator:
            return False

        # Extract the project description from agent command
        parts = user_input.split(" ", 1)
        if len(parts) > 1:
            project_description = parts[1]
        else:
            project_description = "General development project"

        return await self.orchestrator.execute_full_workflow(
            project_description, claude_chat_method
        )

    def should_auto_execute(self, user_input: str) -> bool:
        """Check if this should trigger automated workflow"""
        # Trigger automation for analyst commands with descriptions
        if user_input.startswith("/analyst ") and len(user_input.split(" ", 1)) > 1:
            return True
        return False

    def store_agent_response(self, agent_name: str, response: str):
        """Store agent response for workflow continuity"""
        if self.enabled and self.orchestrator:
            self.orchestrator.store_agent_output(agent_name, response)

    def get_workflow_status(self) -> str:
        """Get current workflow status as formatted string"""
        if not self.enabled or not self.orchestrator:
            return "BMAD-METHOD not available"

        status = self.orchestrator.get_workflow_status()

        status_text = "🎯 **BMAD Workflow Status**\n\n"
        status_text += f"**Progress:** {status['workflow_progress']}\n"

        if status["completed_agents"]:
            status_text += f"**Completed:** {', '.join(status['completed_agents'])}\n"

        if status["next_suggested"]:
            status_text += f"**Next Suggested:** /{status['next_suggested']}\n"

        status_text += f"**Available Agents:** {', '.join([f'/{agent}' for agent in status['available_agents']])}\n"

        return status_text

    def get_available_commands(self) -> list:
        """Get all available BMAD agent commands"""
        if not self.enabled or not self.orchestrator:
            return []

        agents = self.orchestrator.agent_loader.list_agents()
        return [f"/{agent}" for agent in agents]

    def save_workflow(self):
        """Save current workflow state"""
        if self.enabled and self.orchestrator:
            self.orchestrator.save_workflow_state()

    def load_workflow(self):
        """Load previous workflow state"""
        if self.enabled and self.orchestrator:
            return self.orchestrator.load_workflow_state()
        return False

    def reset_workflow(self):
        """Reset current workflow"""
        if self.enabled and self.orchestrator:
            self.orchestrator.reset_workflow()

    def get_help_text(self) -> str:
        """Get BMAD help text"""
        if not self.enabled:
            return "BMAD-METHOD not available. Ensure .bmad-core directory exists."

        help_text = """
🎯 **BMAD-METHOD Autonomous Development System**

**Available Agent Commands:**
- `/analyst` - Deep requirements analysis and project discovery
- `/pm` - Strategic planning and PRD creation
- `/architect` - System design and technical architecture
- `/developer` - Code implementation and development
- `/qa` - Quality assurance and code review

**Workflow Commands:**
- `bmad status` - Show current workflow status
- `bmad save` - Save current workflow state
- `bmad load` - Load previous workflow state
- `bmad reset` - Reset workflow state
- `bmad help` - Show this help

**Automated Workflow (Recommended):**
Any detailed project description to `/analyst` triggers full automation:
```
/analyst Create a task management app with real-time collaboration
/analyst Build an e-commerce platform with payment processing
/analyst Develop a REST API for user management with JWT auth
/analyst Create a learning management system with video streaming
```
→ Automatically runs: analyst → pm → architect → developer → qa

**Manual Workflow:**
For step-by-step control, use individual commands:
1. `/analyst [project description]` - Requirements analysis
2. `/pm` - Strategic planning (uses analyst output)
3. `/architect` - System design (uses PM output)
4. `/developer` - Implementation (uses architect output)
5. `/qa` - Quality assurance (validates all above)

**Web Research Integration:**
Agents automatically use web search for:
- Competitive analysis and market research
- Technology recommendations and best practices
- Code examples and documentation lookup
"""
        return help_text
