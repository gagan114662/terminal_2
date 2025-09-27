"""
TermNet Work Planning Module

Implements task planning and decomposition for autonomous code changes.
Follows Google AI systems best practices: deterministic, testable, clear contracts.
"""

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any


@dataclass
class TestCaseSpec:
    """Specification for a test case to validate task completion."""

    name: str
    description: str
    command: str
    expected_outcome: str
    risk_level: str = "low"


@dataclass
class TaskNode:
    """A single task in the execution plan."""

    id: str
    description: str
    dependencies: list[str]
    risk: str  # "low", "medium", "high"
    done_criteria: list[str]
    estimated_files: list[str] = None

    def __post_init__(self):
        if self.estimated_files is None:
            self.estimated_files = []


class WorkPlanner:
    """
    Plans and decomposes work for autonomous code changes.

    Produces deterministic task graphs with clear dependencies and acceptance criteria.
    Designed to be predictable and testable without external dependencies.
    """

    def __init__(self, max_tasks: int = 20, seed: int = None):
        """
        Initialize the work planner.

        Args:
            max_tasks: Maximum number of tasks to generate (safety limit)
            seed: Random seed for deterministic planning (test reproducibility)
        """
        self.max_tasks = max_tasks
        self.seed = seed or 42

    def plan(self, goal: str, repo_intel: dict[str, Any]) -> dict[str, Any]:
        """
        Create a task execution plan for the given goal.

        Args:
            goal: Natural language description of what to achieve
            repo_intel: Repository analysis data (file structure, symbols, etc.)

        Returns:
            Task graph with nodes, dependencies, and metadata
        """
        # Hash inputs for deterministic planning
        plan_hash = self._hash_inputs(goal, repo_intel)

        # Analyze goal and decompose into tasks
        tasks = self._decompose_goal(goal, repo_intel, plan_hash)

        # Build dependency graph
        task_graph = self._build_task_graph(tasks)

        # Add metadata
        task_graph.update(
            {
                "goal": goal,
                "plan_hash": plan_hash,
                "created_at": datetime.utcnow().isoformat(),
                "estimated_complexity": self._estimate_complexity(tasks),
                "total_tasks": len(tasks),
            }
        )

        return task_graph

    def test_plan(self, task_graph: dict[str, Any]) -> list[TestCaseSpec]:
        """
        Generate test cases to validate task completion.

        Args:
            task_graph: Task graph from plan()

        Returns:
            List of test specifications
        """
        tests = []
        nodes = task_graph.get("nodes", {})

        # Generate acceptance tests for each task
        for task_id, task_data in nodes.items():
            task = TaskNode(**task_data)

            # Basic functionality test
            tests.append(
                TestCaseSpec(
                    name=f"test_{task_id}_completion",
                    description=f"Verify {task.description} is completed",
                    command=self._generate_test_command(task),
                    expected_outcome="success",
                    risk_level=task.risk,
                )
            )

            # Integration test for high-risk tasks
            if task.risk == "high":
                tests.append(
                    TestCaseSpec(
                        name=f"test_{task_id}_integration",
                        description=f"Integration test for {task.description}",
                        command="python -m pytest tests/ -k integration",
                        expected_outcome="all_pass",
                        risk_level="high",
                    )
                )

        # Overall system test
        tests.append(
            TestCaseSpec(
                name="test_overall_goal_completion",
                description=f"Verify overall goal is achieved: {task_graph['goal']}",
                command="python -m pytest tests/ -q",
                expected_outcome="all_pass",
                risk_level="medium",
            )
        )

        return tests

    def changeplan_md(
        self, goal: str, task_graph: dict[str, Any], tests: list[TestCaseSpec]
    ) -> str:
        """
        Generate markdown documentation for the change plan.

        Args:
            goal: Original goal
            task_graph: Planned task graph
            tests: Test specifications

        Returns:
            Markdown content for ChangePlan.md
        """
        md_content = f"""# Change Plan

## Goal
{goal}

## Plan Summary
- **Total Tasks**: {task_graph['total_tasks']}
- **Estimated Complexity**: {task_graph['estimated_complexity']}
- **Plan Hash**: `{task_graph['plan_hash']}`
- **Created**: {task_graph['created_at']}

## Task Graph

"""

        # Add task details
        nodes = task_graph.get("nodes", {})
        edges = task_graph.get("edges", [])

        for task_id in self._topological_sort(nodes, edges):
            task_data = nodes[task_id]
            task = TaskNode(**task_data)

            md_content += f"""### Task: {task_id}
**Description**: {task.description}
**Risk Level**: {task.risk}
**Dependencies**: {', '.join(task.dependencies) if task.dependencies else 'None'}
**Estimated Files**: {', '.join(task.estimated_files) if task.estimated_files else 'TBD'}

**Done Criteria**:
"""
            for criteria in task.done_criteria:
                md_content += f"- {criteria}\n"
            md_content += "\n"

        # Add test plan
        md_content += "## Test Plan\n\n"
        for test in tests:
            md_content += f"""### {test.name}
- **Description**: {test.description}
- **Command**: `{test.command}`
- **Expected**: {test.expected_outcome}
- **Risk**: {test.risk_level}

"""

        md_content += """## Execution Notes
- Tasks will be executed in dependency order
- Each task must pass its done criteria before proceeding
- High-risk tasks require additional integration testing
- Plan can be re-generated with same inputs for consistency

"""

        return md_content

    def _hash_inputs(self, goal: str, repo_intel: dict[str, Any]) -> str:
        """Generate deterministic hash of planning inputs."""
        # Create stable representation for hashing
        stable_input = {
            "goal": goal,
            "seed": self.seed,
            "repo_files": sorted(repo_intel.get("files", [])),
            "repo_symbols": sorted(repo_intel.get("symbols", [])),
        }

        input_str = json.dumps(stable_input, sort_keys=True)
        return hashlib.sha256(input_str.encode()).hexdigest()[:12]

    def _decompose_goal(
        self, goal: str, repo_intel: dict[str, Any], plan_hash: str
    ) -> list[TaskNode]:
        """Decompose goal into executable tasks."""
        tasks = []

        # Simple heuristic-based decomposition (deterministic)
        goal_lower = goal.lower()

        # Always start with analysis task
        tasks.append(
            TaskNode(
                id="analyze_requirements",
                description="Analyze requirements and existing codebase",
                dependencies=[],
                risk="low",
                done_criteria=[
                    "Requirements clearly understood",
                    "Existing code analyzed",
                    "Change scope identified",
                ],
                estimated_files=["docs/analysis.md"],
            )
        )

        # Determine task type based on goal keywords
        if any(word in goal_lower for word in ["test", "testing", "spec"]):
            tasks.append(
                TaskNode(
                    id="implement_tests",
                    description="Implement or update test cases",
                    dependencies=["analyze_requirements"],
                    risk="low",
                    done_criteria=[
                        "Test cases written",
                        "Tests initially failing (red)",
                        "Test coverage adequate",
                    ],
                    estimated_files=["tests/"],
                )
            )

        if any(word in goal_lower for word in ["fix", "bug", "error", "issue"]):
            tasks.append(
                TaskNode(
                    id="fix_implementation",
                    description="Fix identified issues in implementation",
                    dependencies=["analyze_requirements"],
                    risk="medium",
                    done_criteria=[
                        "Root cause identified",
                        "Fix implemented",
                        "No regressions introduced",
                    ],
                    estimated_files=repo_intel.get("files", [])[
                        :3
                    ],  # Estimate top files
                )
            )

        if any(word in goal_lower for word in ["add", "implement", "create", "new"]):
            tasks.append(
                TaskNode(
                    id="implement_feature",
                    description="Implement new functionality",
                    dependencies=["analyze_requirements"],
                    risk="high",
                    done_criteria=[
                        "Core functionality implemented",
                        "API contracts maintained",
                        "Integration points working",
                    ],
                    estimated_files=["termnet/", "tests/"],
                )
            )

        # Always end with validation
        tasks.append(
            TaskNode(
                id="validate_changes",
                description="Validate all changes work together",
                dependencies=[
                    task.id for task in tasks[1:]
                ],  # Depends on all implementation tasks
                risk="medium",
                done_criteria=[
                    "All tests passing",
                    "No breaking changes",
                    "Documentation updated",
                    "Ready for review",
                ],
                estimated_files=["docs/", "tests/"],
            )
        )

        return tasks[: self.max_tasks]  # Enforce safety limit

    def _build_task_graph(self, tasks: list[TaskNode]) -> dict[str, Any]:
        """Build task graph data structure."""
        nodes = {task.id: asdict(task) for task in tasks}

        # Build edges from dependencies
        edges = []
        for task in tasks:
            for dep in task.dependencies:
                edges.append({"from": dep, "to": task.id})

        return {"nodes": nodes, "edges": edges}

    def _estimate_complexity(self, tasks: list[TaskNode]) -> str:
        """Estimate overall complexity of the plan."""
        risk_scores = {"low": 1, "medium": 3, "high": 5}
        total_score = sum(risk_scores.get(task.risk, 1) for task in tasks)

        if total_score <= 5:
            return "low"
        elif total_score <= 15:
            return "medium"
        else:
            return "high"

    def _generate_test_command(self, task: TaskNode) -> str:
        """Generate appropriate test command for a task."""
        if "test" in task.id:
            return f"python -m pytest tests/ -k {task.id}"
        elif "implement" in task.id:
            return "python -m pytest tests/ --tb=short"
        else:
            return "python -c 'print(\"Task validation placeholder\")'"

    def _topological_sort(
        self, nodes: dict[str, Any], edges: list[dict[str, str]]
    ) -> list[str]:
        """Return tasks in dependency-safe execution order."""
        # Build adjacency list
        graph = {node_id: [] for node_id in nodes}
        in_degree = {node_id: 0 for node_id in nodes}

        for edge in edges:
            graph[edge["from"]].append(edge["to"])
            in_degree[edge["to"]] += 1

        # Kahn's algorithm
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            current = queue.pop(0)
            result.append(current)

            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return result
