"""
Enhanced BMAD Orchestrator with ReAct Framework Integration
Adds intelligent task analysis and reasoning capabilities
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from typing import Any

from code_analyzer import CodeAnalyzer
from orchestrator import BMADOrchestrator
from rag_processor import RAGProcessor
from react_framework import ReActFramework
from task_analyzer import TaskAnalyzer


class EnhancedBMADOrchestrator(BMADOrchestrator):
    """Enhanced orchestrator with ReAct reasoning and task analysis"""

    def __init__(self):
        super().__init__()
        self.react_framework = ReActFramework()
        self.task_analyzer = TaskAnalyzer()
        self.rag_processor = RAGProcessor()
        self.code_analyzer = CodeAnalyzer()
        self.current_complexity = None
        print("🧠 Enhanced BMAD Orchestrator with ReAct + Agentic RAG initialized")

    def analyze_and_plan(self, task_description: str) -> dict[str, Any]:
        """Analyze task and create execution plan with RAG insights"""
        # Analyze task complexity
        complexity, recommended_workflow = self.task_analyzer.analyze_task(
            task_description
        )
        self.current_complexity = complexity

        # Determine if ReAct reasoning is needed
        use_react = self.task_analyzer.should_use_react(task_description)

        # Get RAG analysis for context
        rag_analysis = self.rag_processor.process_development_query(task_description)

        plan = {
            "task": task_description,
            "complexity": complexity.value,
            "workflow": recommended_workflow,
            "use_react": use_react,
            "estimated_agents": len(recommended_workflow),
            "rag_insights": {
                "confidence": rag_analysis["rag_analysis"]["confidence_score"],
                "search_results_count": len(
                    rag_analysis["rag_analysis"]["search_results"]
                ),
                "actionable_insights": rag_analysis["actionable_insights"],
            },
        }

        print("📋 Enhanced Task Analysis Complete:")
        print(f"   Complexity: {complexity.value}")
        print(f"   Agents needed: {len(recommended_workflow)}")
        print(f"   Workflow: {' → '.join(recommended_workflow)}")
        print(f"   ReAct reasoning: {'Yes' if use_react else 'No'}")
        print(
            f"   RAG confidence: {rag_analysis['rag_analysis']['confidence_score']:.2f}"
        )
        print(
            f"   Code references found: {len(rag_analysis['rag_analysis']['search_results'])}"
        )

        return plan

    def execute_with_reasoning(self, task_description: str) -> tuple[bool, str]:
        """Execute task with ReAct reasoning if needed"""
        # First analyze the task
        plan = self.analyze_and_plan(task_description)

        if plan["use_react"]:
            # Set up ReAct framework
            self.react_framework.set_goal(task_description)

            # Add initial reasoning
            self.react_framework.add_thought(
                f"Task complexity is {plan['complexity']}. "
                f"Need to execute {len(plan['workflow'])} agents in sequence: "
                f"{' → '.join(plan['workflow'])}"
            )

            # Store reasoning chain for agents
            reasoning_chain = self.react_framework.get_reasoning_chain()
            self.project_context["reasoning_chain"] = reasoning_chain

        # Use optimized workflow instead of standard workflow
        self.standard_workflow = plan["workflow"]

        return (
            True,
            f"Ready to execute {plan['complexity']} task with {len(plan['workflow'])} agents",
        )

    async def execute_enhanced_workflow(
        self, task_description: str, claude_chat_method
    ) -> bool:
        """Execute the enhanced workflow with intelligent agent selection"""
        # First analyze and plan
        plan = self.analyze_and_plan(task_description)

        print(f"\n🚀 Starting enhanced workflow: {task_description}")
        print(f"📊 Complexity: {plan['complexity']} | Agents: {len(plan['workflow'])}")
        print("=" * 60)

        # Use the optimized workflow from analysis
        self.standard_workflow = plan["workflow"]

        # Execute using the parent class method with optimized workflow
        return await self.execute_full_workflow(task_description, claude_chat_method)

    def execute_step_by_step(self, task_description: str) -> dict:
        """Execute workflow step by step, returning terminal commands for each step"""
        plan = self.analyze_and_plan(task_description)

        steps = {}
        for i, agent_name in enumerate(plan["workflow"], 1):
            # Generate command for this step
            cmd = f"python3 -c \"import sys; sys.path.insert(0,'.bmad-core'); from enhanced_orchestrator import EnhancedBMADOrchestrator; eo=EnhancedBMADOrchestrator(); success, prompt = eo.execute_agent('{agent_name}', '{task_description}'); print('Step {i}: {agent_name}'); print('Prompt generated:', len(prompt), 'chars')\""

            steps[f"step_{i}_{agent_name}"] = {
                "command": cmd,
                "description": f"Execute {agent_name} agent for: {task_description[:50]}...",
            }

        return steps

    def get_verification_commands(self, task_description: str) -> list:
        """Get terminal commands to verify the orchestrator enhancement"""
        commands = [
            "echo '=== Enhanced Orchestrator Test ==='",
            f"echo 'Testing task: {task_description[:50]}...'",
        ]

        # Add task analyzer commands
        commands.extend(self.task_analyzer.get_terminal_commands(task_description))

        return commands
