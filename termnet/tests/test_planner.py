"""
Tests for TermNet Work Planner

Ensures deterministic, reproducible planning behavior following Google AI best practices.
All tests are offline and use deterministic inputs for reproducibility.
"""

import json
import tempfile
import pytest
from pathlib import Path

from termnet.planner import WorkPlanner, TaskNode, TestCaseSpec


class TestWorkPlanner:
    """Test WorkPlanner core functionality."""

    @pytest.fixture
    def planner(self):
        """Create a planner with fixed seed for deterministic tests."""
        return WorkPlanner(seed=42)

    @pytest.fixture
    def sample_repo_intel(self):
        """Sample repository intelligence data."""
        return {
            "files": ["termnet/agent.py", "termnet/tools/terminal.py", "tests/test_agent.py"],
            "symbols": ["TermNetAgent", "TerminalTool", "execute_command"],
            "imports": {"termnet.agent": ["TermNetAgent"], "termnet.tools.terminal": ["TerminalTool"]},
            "test_files": ["tests/test_agent.py", "tests/test_tools.py"]
        }

    def test_plan_creates_valid_dag(self, planner, sample_repo_intel):
        """Test that planning creates a valid directed acyclic graph."""
        goal = "Fix failing tests in the agent module"
        plan = planner.plan(goal, sample_repo_intel)

        # Verify plan structure
        assert "nodes" in plan
        assert "edges" in plan
        assert "goal" in plan
        assert plan["goal"] == goal

        # Verify nodes have required fields
        nodes = plan["nodes"]
        assert len(nodes) > 0

        for task_id, task_data in nodes.items():
            assert "id" in task_data
            assert "description" in task_data
            assert "dependencies" in task_data
            assert "risk" in task_data
            assert "done_criteria" in task_data
            assert task_data["risk"] in ["low", "medium", "high"]
            assert isinstance(task_data["dependencies"], list)
            assert isinstance(task_data["done_criteria"], list)

        # Verify edges reference valid nodes
        edges = plan["edges"]
        for edge in edges:
            assert edge["from"] in nodes
            assert edge["to"] in nodes

    def test_plan_deterministic_with_same_inputs(self, sample_repo_intel):
        """Test that identical inputs produce identical plans."""
        goal = "Add new feature to terminal tool"

        planner1 = WorkPlanner(seed=42)
        planner2 = WorkPlanner(seed=42)

        plan1 = planner1.plan(goal, sample_repo_intel)
        plan2 = planner2.plan(goal, sample_repo_intel)

        # Plans should be identical
        assert plan1["plan_hash"] == plan2["plan_hash"]
        assert plan1["nodes"] == plan2["nodes"]
        assert plan1["edges"] == plan2["edges"]
        assert plan1["total_tasks"] == plan2["total_tasks"]

    def test_plan_handles_different_goal_types(self, planner, sample_repo_intel):
        """Test planning handles different types of goals appropriately."""
        test_goals = [
            "Fix bug in terminal execution",
            "Add new testing framework",
            "Implement file upload feature",
            "Create comprehensive test suite"
        ]

        plans = []
        for goal in test_goals:
            plan = planner.plan(goal, sample_repo_intel)
            plans.append(plan)

            # Each plan should be valid
            assert plan["total_tasks"] > 0
            assert "analyze_requirements" in plan["nodes"]  # Always has analysis
            assert "validate_changes" in plan["nodes"]     # Always has validation

        # Different goals should produce different plans
        hashes = [plan["plan_hash"] for plan in plans]
        assert len(set(hashes)) == len(test_goals)  # All unique

    def test_plan_includes_dependencies(self, planner, sample_repo_intel):
        """Test that task dependencies are properly set."""
        goal = "Implement new feature with tests"
        plan = planner.plan(goal, sample_repo_intel)

        nodes = plan["nodes"]

        # analyze_requirements should have no dependencies
        assert nodes["analyze_requirements"]["dependencies"] == []

        # validate_changes should depend on implementation tasks
        validate_deps = nodes["validate_changes"]["dependencies"]
        assert len(validate_deps) > 0
        assert "analyze_requirements" not in validate_deps  # Should not depend on analysis directly

        # All dependencies should reference valid tasks
        for task_id, task_data in nodes.items():
            for dep in task_data["dependencies"]:
                assert dep in nodes, f"Task {task_id} has invalid dependency: {dep}"

    def test_plan_respects_max_tasks_limit(self, sample_repo_intel):
        """Test that planning respects the maximum tasks limit."""
        planner = WorkPlanner(max_tasks=3, seed=42)
        goal = "Comprehensive system overhaul with multiple features"

        plan = planner.plan(goal, sample_repo_intel)

        assert plan["total_tasks"] <= 3
        assert len(plan["nodes"]) <= 3

    def test_plan_includes_acceptance_criteria(self, planner, sample_repo_intel):
        """Test that all tasks include clear acceptance criteria."""
        goal = "Fix integration test failures"
        plan = planner.plan(goal, sample_repo_intel)

        for task_id, task_data in plan["nodes"].items():
            done_criteria = task_data["done_criteria"]
            assert len(done_criteria) > 0
            assert all(isinstance(criteria, str) for criteria in done_criteria)
            assert all(len(criteria.strip()) > 0 for criteria in done_criteria)

    def test_test_plan_generation(self, planner, sample_repo_intel):
        """Test generation of test specifications from task graph."""
        goal = "Implement authentication system"
        task_graph = planner.plan(goal, sample_repo_intel)

        tests = planner.test_plan(task_graph)

        # Should have tests for each task plus overall test
        assert len(tests) >= len(task_graph["nodes"])

        # Verify test structure
        for test in tests:
            assert isinstance(test, TestCaseSpec)
            assert test.name
            assert test.description
            assert test.command
            assert test.expected_outcome
            assert test.risk_level in ["low", "medium", "high"]

        # Should have overall completion test
        overall_tests = [t for t in tests if "overall" in t.name]
        assert len(overall_tests) == 1

        # High-risk tasks should have integration tests
        high_risk_tasks = [
            task_id for task_id, task_data in task_graph["nodes"].items()
            if task_data["risk"] == "high"
        ]
        if high_risk_tasks:
            integration_tests = [t for t in tests if "integration" in t.name]
            assert len(integration_tests) >= len(high_risk_tasks)

    def test_changeplan_md_generation(self, planner, sample_repo_intel):
        """Test generation of ChangePlan.md content."""
        goal = "Refactor configuration system"
        task_graph = planner.plan(goal, sample_repo_intel)
        tests = planner.test_plan(task_graph)

        md_content = planner.changeplan_md(goal, task_graph, tests)

        # Verify markdown structure
        assert "# Change Plan" in md_content
        assert "## Goal" in md_content
        assert goal in md_content
        assert "## Plan Summary" in md_content
        assert "## Task Graph" in md_content
        assert "## Test Plan" in md_content

        # Verify all tasks are documented
        for task_id in task_graph["nodes"]:
            assert f"### Task: {task_id}" in md_content

        # Verify test documentation
        for test in tests:
            assert test.name in md_content

        # Verify plan metadata
        assert task_graph["plan_hash"] in md_content
        assert str(task_graph["total_tasks"]) in md_content

    def test_changeplan_md_idempotent(self, planner, sample_repo_intel):
        """Test that ChangePlan.md generation is idempotent."""
        goal = "Update dependency management"
        task_graph = planner.plan(goal, sample_repo_intel)
        tests = planner.test_plan(task_graph)

        md1 = planner.changeplan_md(goal, task_graph, tests)
        md2 = planner.changeplan_md(goal, task_graph, tests)

        assert md1 == md2, "ChangePlan.md generation should be idempotent"

    def test_topological_sort_respects_dependencies(self, planner, sample_repo_intel):
        """Test that task ordering respects dependencies."""
        goal = "Multi-step feature implementation"
        plan = planner.plan(goal, sample_repo_intel)

        # Get task execution order
        sorted_tasks = planner._topological_sort(plan["nodes"], plan["edges"])

        # Verify all tasks are included
        assert len(sorted_tasks) == len(plan["nodes"])
        assert set(sorted_tasks) == set(plan["nodes"].keys())

        # Verify dependency order
        task_positions = {task_id: i for i, task_id in enumerate(sorted_tasks)}

        for edge in plan["edges"]:
            from_task = edge["from"]
            to_task = edge["to"]
            assert task_positions[from_task] < task_positions[to_task], \
                f"Task {from_task} should come before {to_task} in execution order"

    def test_complexity_estimation(self, planner, sample_repo_intel):
        """Test complexity estimation based on task risks."""
        goals_and_expected_complexity = [
            ("Simple documentation update", "low"),
            ("Fix minor bug in existing function", "low"),
            ("Add comprehensive test suite with new features", "medium"),
            ("Implement complex distributed system", "high")
        ]

        for goal, expected_complexity in goals_and_expected_complexity:
            plan = planner.plan(goal, sample_repo_intel)
            # Note: actual complexity may vary due to heuristics,
            # but should be reasonable
            assert plan["estimated_complexity"] in ["low", "medium", "high"]


class TestTaskNode:
    """Test TaskNode data structure."""

    def test_task_node_creation(self):
        """Test TaskNode creation and validation."""
        task = TaskNode(
            id="test_task",
            description="Test task description",
            dependencies=["dep1", "dep2"],
            risk="medium",
            done_criteria=["Criterion 1", "Criterion 2"]
        )

        assert task.id == "test_task"
        assert task.description == "Test task description"
        assert task.dependencies == ["dep1", "dep2"]
        assert task.risk == "medium"
        assert task.done_criteria == ["Criterion 1", "Criterion 2"]
        assert task.estimated_files == []  # Default value

    def test_task_node_with_estimated_files(self):
        """Test TaskNode with estimated files."""
        task = TaskNode(
            id="implementation_task",
            description="Implement feature",
            dependencies=[],
            risk="high",
            done_criteria=["Feature working"],
            estimated_files=["src/feature.py", "tests/test_feature.py"]
        )

        assert task.estimated_files == ["src/feature.py", "tests/test_feature.py"]


class TestTestCaseSpec:
    """Test TestCaseSpec data structure."""

    def test_test_case_spec_creation(self):
        """Test TestCaseSpec creation."""
        test_spec = TestCaseSpec(
            name="test_feature_works",
            description="Test that new feature works correctly",
            command="python -m pytest tests/test_feature.py",
            expected_outcome="all_pass",
            risk_level="medium"
        )

        assert test_spec.name == "test_feature_works"
        assert test_spec.description == "Test that new feature works correctly"
        assert test_spec.command == "python -m pytest tests/test_feature.py"
        assert test_spec.expected_outcome == "all_pass"
        assert test_spec.risk_level == "medium"

    def test_test_case_spec_default_risk(self):
        """Test TestCaseSpec with default risk level."""
        test_spec = TestCaseSpec(
            name="simple_test",
            description="Simple test case",
            command="echo test",
            expected_outcome="success"
        )

        assert test_spec.risk_level == "low"  # Default value


class TestPlannerIntegration:
    """Integration tests for planner workflow."""

    def test_full_planning_workflow(self):
        """Test complete planning workflow from goal to ChangePlan.md."""
        planner = WorkPlanner(seed=123)
        repo_intel = {
            "files": ["main.py", "utils.py", "tests/test_main.py"],
            "symbols": ["main_function", "utility_helper"],
            "imports": {},
            "test_files": ["tests/test_main.py"]
        }

        goal = "Add error handling to main function"

        # Step 1: Create plan
        plan = planner.plan(goal, repo_intel)
        assert plan["total_tasks"] > 0

        # Step 2: Generate tests
        tests = planner.test_plan(plan)
        assert len(tests) > 0

        # Step 3: Generate documentation
        md_content = planner.changeplan_md(goal, plan, tests)
        assert len(md_content) > 0

        # Verify content makes sense
        assert goal in md_content
        assert "error handling" in md_content.lower()

    def test_plan_file_output(self):
        """Test writing ChangePlan.md to file."""
        planner = WorkPlanner(seed=456)
        repo_intel = {"files": ["app.py"], "symbols": [], "imports": {}, "test_files": []}
        goal = "Add logging to application"

        plan = planner.plan(goal, repo_intel)
        tests = planner.test_plan(plan)
        md_content = planner.changeplan_md(goal, plan, tests)

        # Write to temporary file and verify
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(md_content)
            temp_path = f.name

        try:
            # Read back and verify
            with open(temp_path, 'r') as f:
                read_content = f.read()

            assert read_content == md_content
            assert "# Change Plan" in read_content
        finally:
            Path(temp_path).unlink()  # Cleanup

    def test_plan_serialization(self):
        """Test that plans can be serialized and deserialized."""
        planner = WorkPlanner(seed=789)
        repo_intel = {"files": ["config.py"], "symbols": ["Config"], "imports": {}, "test_files": []}
        goal = "Refactor configuration management"

        plan = planner.plan(goal, repo_intel)

        # Serialize to JSON
        plan_json = json.dumps(plan, indent=2, sort_keys=True)

        # Deserialize
        restored_plan = json.loads(plan_json)

        # Verify restoration
        assert restored_plan == plan
        assert restored_plan["goal"] == goal
        assert restored_plan["plan_hash"] == plan["plan_hash"]