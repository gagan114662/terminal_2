"""
Task Complexity Analyzer for BMAD Agent Selection
Determines optimal agent workflow based on task complexity
"""

from enum import Enum


class TaskComplexity(Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    ENTERPRISE = "enterprise"


class TaskAnalyzer:
    """Analyzes task complexity to determine optimal BMAD agent workflow"""

    def __init__(self):
        # Keywords that indicate complexity levels
        self.complexity_indicators = {
            TaskComplexity.SIMPLE: [
                "fix bug",
                "update",
                "small change",
                "quick",
                "simple",
                "single file",
                "typo",
                "minor",
                "hotfix",
            ],
            TaskComplexity.MODERATE: [
                "add feature",
                "implement",
                "create",
                "build",
                "develop",
                "new functionality",
                "api",
                "database",
                "integration",
            ],
            TaskComplexity.COMPLEX: [
                "system",
                "architecture",
                "redesign",
                "refactor",
                "microservices",
                "multi-component",
                "performance",
                "scalability",
                "security",
            ],
            TaskComplexity.ENTERPRISE: [
                "enterprise",
                "production",
                "deployment",
                "ci/cd",
                "monitoring",
                "full stack",
                "multi-team",
                "infrastructure",
                "cloud",
            ],
        }

        # Agent workflows by complexity
        self.workflows = {
            TaskComplexity.SIMPLE: ["developer", "validator"],
            TaskComplexity.MODERATE: ["analyst", "developer", "qa", "validator"],
            TaskComplexity.COMPLEX: [
                "analyst",
                "pm",
                "architect",
                "developer",
                "qa",
                "validator",
            ],
            TaskComplexity.ENTERPRISE: [
                "analyst",
                "pm",
                "architect",
                "developer",
                "qa",
                "validator",
            ],
        }

    def analyze_task(self, task_description: str) -> tuple[TaskComplexity, list[str]]:
        """Analyze task and return complexity + recommended agent workflow"""
        task_lower = task_description.lower()

        # Score each complexity level
        scores = {}
        for complexity, indicators in self.complexity_indicators.items():
            score = sum(1 for indicator in indicators if indicator in task_lower)
            scores[complexity] = score

        # Determine highest scoring complexity
        max_complexity = max(scores, key=scores.get)

        # If no clear indicators, default to moderate
        if scores[max_complexity] == 0:
            max_complexity = TaskComplexity.MODERATE

        # Get recommended workflow
        workflow = self.workflows[max_complexity]

        return max_complexity, workflow

    def get_terminal_commands(self, task_description: str) -> list[str]:
        """Generate terminal commands to verify task analysis"""
        complexity, workflow = self.analyze_task(task_description)

        commands = [
            f"echo 'Task: {task_description}'",
            f"echo 'Complexity: {complexity.value}'",
            f"echo 'Recommended workflow: {' -> '.join(workflow)}'",
        ]

        return commands

    def should_use_react(self, task_description: str) -> bool:
        """Determine if task requires ReAct reasoning framework"""
        complexity, _ = self.analyze_task(task_description)

        # Use ReAct for complex and enterprise tasks
        return complexity in [TaskComplexity.COMPLEX, TaskComplexity.ENTERPRISE]
