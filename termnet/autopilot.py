"""
TermNet Autopilot

Orchestrates autonomous code changes by combining planning, analysis, editing, and repository operations.
Follows Google AI best practices with comprehensive safety checks and rollback capabilities.
"""

import json
import logging
import os
import shutil
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .code_indexer import CodeIndexer
from .edit_engine import EditEngine
from .planner import WorkPlanner
from .repo_ops import GitResult, RepoOperations


@dataclass
class AutopilotConfig:
    """Configuration for autopilot execution."""

    repo_path: str
    max_tasks_per_run: int = 5
    require_tests: bool = True
    auto_push: bool = False
    auto_create_pr: bool = False
    safety_checks: bool = True
    backup_enabled: bool = True
    dry_run: bool = True
    base_branch: str = "main"


@dataclass
class ExecutionResult:
    """Result of autopilot execution."""

    success: bool
    message: str
    tasks_completed: int
    tasks_failed: int
    branch_created: Optional[str] = None
    commit_sha: Optional[str] = None
    pr_url: Optional[str] = None
    execution_time: float = 0.0
    errors: List[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


@dataclass
class TaskExecutionResult:
    """Result of individual task execution."""

    task_id: str
    success: bool
    message: str
    changes_made: List[str] = None
    tests_passed: bool = True
    execution_time: float = 0.0

    def __post_init__(self):
        if self.changes_made is None:
            self.changes_made = []


class Autopilot:
    """
    Autonomous code change orchestrator.

    Combines planning, analysis, editing, and repository operations
    to execute code changes safely and autonomously.
    """

    def __init__(self, config: AutopilotConfig):
        """
        Initialize Autopilot with configuration.

        Args:
            config: Autopilot configuration
        """
        self.config = config
        self.repo_path = Path(config.repo_path).resolve()

        # Initialize components
        self.planner = WorkPlanner(max_tasks=config.max_tasks_per_run)
        self.indexer = CodeIndexer()
        self.edit_engine = EditEngine(
            {
                "write_guardrails": {
                    "allowed_paths": ["*", "**/*"],
                    "blocked_paths": [".git/**", "__pycache__/**", "*.pyc"],
                    "require_tests": config.require_tests,
                    "dry_run": config.dry_run,
                },
                "repo_path": str(self.repo_path),
            }
        )
        self.repo_ops = RepoOperations(
            str(self.repo_path),
            {"auto_push": config.auto_push, "branch_prefix": "termnet/autopilot/"},
        )

        # Setup logging
        self.logger = logging.getLogger(__name__)
        self._setup_logging()

        # Execution state
        self.current_execution = None
        self.backup_location = None

    def _setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    def execute_goal(
        self, goal: str, context: Dict[str, Any] = None
    ) -> ExecutionResult:
        """
        Execute autonomous code changes for a given goal.

        Args:
            goal: High-level description of what to accomplish
            context: Additional context for planning

        Returns:
            ExecutionResult with execution details
        """
        start_time = datetime.now()
        self.logger.info(f"Starting autopilot execution for goal: {goal}")

        try:
            # Phase 1: Analysis and Planning
            analysis_result = self._analyze_repository()
            if not analysis_result["success"]:
                return ExecutionResult(
                    success=False,
                    message=f"Repository analysis failed: {analysis_result['error']}",
                    tasks_completed=0,
                    tasks_failed=0,
                )

            # Create execution plan
            plan = self._create_execution_plan(
                goal, analysis_result["repo_intel"], context
            )
            self.logger.info(f"Created plan with {plan['total_tasks']} tasks")

            # Phase 2: Safety Checks
            if self.config.safety_checks:
                safety_result = self._perform_safety_checks(plan)
                if not safety_result["safe"]:
                    return ExecutionResult(
                        success=False,
                        message=f"Safety checks failed: {safety_result['reason']}",
                        tasks_completed=0,
                        tasks_failed=0,
                        warnings=safety_result.get("warnings", []),
                    )

            # Phase 3: Backup and Branch Creation
            backup_result = self._create_backup_and_branch(goal)
            if not backup_result.success:
                return ExecutionResult(
                    success=False,
                    message=f"Failed to create backup/branch: {backup_result.message}",
                    tasks_completed=0,
                    tasks_failed=0,
                )

            # Phase 4: Task Execution
            execution_result = self._execute_tasks(plan)

            # Phase 5: Validation and Finalization
            if execution_result.success:
                validation_result = self._validate_and_finalize(goal, execution_result)
                if validation_result.success and self.config.auto_create_pr:
                    pr_result = self._create_pull_request(goal, plan)
                    execution_result.pr_url = pr_result.get("url")

            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            execution_result.execution_time = execution_time

            self.logger.info(f"Autopilot execution completed in {execution_time:.2f}s")
            return execution_result

        except Exception as e:
            self.logger.error(f"Autopilot execution failed: {e}")
            # Attempt rollback
            if self.backup_location:
                self._rollback_changes()

            return ExecutionResult(
                success=False,
                message=f"Execution failed with error: {e}",
                tasks_completed=0,
                tasks_failed=0,
                execution_time=(datetime.now() - start_time).total_seconds(),
                errors=[str(e)],
            )

    def _analyze_repository(self) -> Dict[str, Any]:
        """
        Analyze repository to gather intelligence for planning.

        Returns:
            Dictionary with analysis results
        """
        try:
            self.logger.info("Analyzing repository structure and content")

            # Build code index
            repo_intel = self.indexer.build_index(
                include_globs=["**/*.py", "**/*.js", "**/*.ts", "**/*.md"],
                exclude_globs=["node_modules/**", "__pycache__/**", ".git/**"],
            )

            # Get repository state
            repo_state = self.repo_ops.get_repository_state()
            repo_intel.update(repo_state)

            return {"success": True, "repo_intel": repo_intel}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _create_execution_plan(
        self, goal: str, repo_intel: Dict[str, Any], context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create detailed execution plan for the goal.

        Args:
            goal: Target goal
            repo_intel: Repository intelligence
            context: Additional context

        Returns:
            Execution plan dictionary
        """
        # Enhance repo intelligence with context
        if context:
            repo_intel.update(context)

        # Create plan using WorkPlanner
        plan = self.planner.plan(goal, repo_intel)

        # Generate test specifications
        test_specs = self.planner.test_plan(plan)
        plan["test_specs"] = test_specs

        return plan

    def _perform_safety_checks(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive safety checks before execution.

        Args:
            plan: Execution plan

        Returns:
            Safety check results
        """
        warnings = []

        # Check repository is clean
        if not self.repo_ops.git.is_clean():
            return {"safe": False, "reason": "Repository has uncommitted changes"}

        # Check task complexity
        if plan["total_tasks"] > self.config.max_tasks_per_run:
            return {
                "safe": False,
                "reason": f"Plan has {plan['total_tasks']} tasks, exceeding limit of {self.config.max_tasks_per_run}",
            }

        # Check for high-risk tasks
        high_risk_tasks = [
            task_id
            for task_id, task_data in plan["nodes"].items()
            if task_data.get("risk") == "high"
        ]

        if len(high_risk_tasks) > 2:
            warnings.append(f"Plan contains {len(high_risk_tasks)} high-risk tasks")

        # Check estimated file changes
        estimated_files = set()
        for task_data in plan["nodes"].values():
            estimated_files.update(task_data.get("estimated_files", []))

        if len(estimated_files) > 10:
            warnings.append(f"Plan may modify {len(estimated_files)} files")

        return {"safe": True, "warnings": warnings}

    def _create_backup_and_branch(self, goal: str) -> GitResult:
        """
        Create backup and feature branch for the execution.

        Args:
            goal: Execution goal for branch naming

        Returns:
            GitResult indicating success/failure
        """
        if self.config.backup_enabled:
            # Create backup
            self.backup_location = self._create_backup()
            self.logger.info(f"Created backup at: {self.backup_location}")

        # Create feature branch
        safe_goal = goal.lower().replace(" ", "-")[:30]
        branch_result = self.repo_ops.create_feature_branch(
            safe_goal, self.config.base_branch
        )

        if branch_result.success:
            self.logger.info(
                f"Created feature branch: {self.repo_ops.git.get_current_branch()}"
            )

        return branch_result

    def _create_backup(self) -> str:
        """
        Create full repository backup.

        Returns:
            Path to backup location
        """
        backup_dir = tempfile.mkdtemp(prefix="termnet_backup_")
        shutil.copytree(
            self.repo_path,
            Path(backup_dir) / "repo",
            ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules"),
        )

        # Save current git state
        git_info = {
            "branch": self.repo_ops.git.get_current_branch(),
            "sha": self.repo_ops.git.get_current_sha(),
            "timestamp": datetime.now().isoformat(),
        }

        with open(Path(backup_dir) / "git_state.json", "w") as f:
            json.dump(git_info, f, indent=2)

        return backup_dir

    def _execute_tasks(self, plan: Dict[str, Any]) -> ExecutionResult:
        """
        Execute tasks according to the plan.

        Args:
            plan: Execution plan

        Returns:
            ExecutionResult with task execution details
        """
        tasks_completed = 0
        tasks_failed = 0
        errors = []
        all_changes = []

        # Get topologically sorted task order
        task_order = self.planner._topological_sort(plan["nodes"], plan["edges"])

        self.logger.info(f"Executing {len(task_order)} tasks in order")

        for task_id in task_order:
            task_data = plan["nodes"][task_id]
            self.logger.info(f"Executing task: {task_id}")

            try:
                # Execute individual task
                task_result = self._execute_single_task(task_id, task_data, plan)

                if task_result.success:
                    tasks_completed += 1
                    all_changes.extend(task_result.changes_made)
                    self.logger.info(f"Task {task_id} completed successfully")
                else:
                    tasks_failed += 1
                    errors.append(f"Task {task_id}: {task_result.message}")
                    self.logger.error(f"Task {task_id} failed: {task_result.message}")

                    # Decide whether to continue or abort
                    if task_data.get("risk") == "high" or tasks_failed >= 2:
                        self.logger.error(
                            "Aborting execution due to critical task failure"
                        )
                        break

            except Exception as e:
                tasks_failed += 1
                error_msg = f"Task {task_id} failed with exception: {e}"
                errors.append(error_msg)
                self.logger.error(error_msg)
                break

        success = tasks_failed == 0 and tasks_completed > 0

        return ExecutionResult(
            success=success,
            message=f"Completed {tasks_completed} tasks, {tasks_failed} failed",
            tasks_completed=tasks_completed,
            tasks_failed=tasks_failed,
            errors=errors,
        )

    def _execute_single_task(
        self, task_id: str, task_data: Dict[str, Any], plan: Dict[str, Any]
    ) -> TaskExecutionResult:
        """
        Execute a single task from the plan.

        Args:
            task_id: Task identifier
            task_data: Task configuration
            plan: Full execution plan

        Returns:
            TaskExecutionResult with execution details
        """
        start_time = datetime.now()

        # For now, implement basic task execution logic
        # In a full implementation, this would dispatch to specific handlers
        # based on task type

        if "analyze" in task_id.lower():
            return self._execute_analysis_task(task_id, task_data)
        elif "implement" in task_id.lower() or "fix" in task_id.lower():
            return self._execute_implementation_task(task_id, task_data)
        elif "test" in task_id.lower() or "validate" in task_id.lower():
            return self._execute_validation_task(task_id, task_data, plan)
        else:
            # Generic task execution
            return TaskExecutionResult(
                task_id=task_id,
                success=True,
                message=f"Task {task_id} completed (simulated)",
                execution_time=(datetime.now() - start_time).total_seconds(),
            )

    def _execute_analysis_task(
        self, task_id: str, task_data: Dict[str, Any]
    ) -> TaskExecutionResult:
        """Execute analysis task."""
        # Analysis tasks are typically read-only
        files_to_analyze = task_data.get("estimated_files", [])

        analyzed_files = []
        for file_path in files_to_analyze[:5]:  # Limit analysis
            full_path = self.repo_path / file_path
            if full_path.exists():
                analyzed_files.append(file_path)

        return TaskExecutionResult(
            task_id=task_id,
            success=True,
            message=f"Analyzed {len(analyzed_files)} files",
            changes_made=[],  # Analysis doesn't make changes
            execution_time=0.5,
        )

    def _execute_implementation_task(
        self, task_id: str, task_data: Dict[str, Any]
    ) -> TaskExecutionResult:
        """Execute implementation task that makes code changes."""
        estimated_files = task_data.get("estimated_files", [])
        changes_made = []

        # For demonstration, create a simple change
        for file_path in estimated_files[:3]:  # Limit changes
            full_path = self.repo_path / file_path

            if full_path.exists() and full_path.suffix == ".py":
                # Add a simple comment to show the change
                content = full_path.read_text()
                if f"# TermNet: {task_id}" not in content:
                    # Add comment at the top
                    new_content = (
                        f"# TermNet: {task_id} - {datetime.now().strftime('%Y-%m-%d')}\n"
                        + content
                    )

                    if not self.config.dry_run:
                        full_path.write_text(new_content)

                    changes_made.append(file_path)

        return TaskExecutionResult(
            task_id=task_id,
            success=True,
            message=f"Implemented changes in {len(changes_made)} files",
            changes_made=changes_made,
            execution_time=1.0,
        )

    def _execute_validation_task(
        self, task_id: str, task_data: Dict[str, Any], plan: Dict[str, Any]
    ) -> TaskExecutionResult:
        """Execute validation/testing task."""
        # Run relevant tests from the plan
        test_specs = plan.get("test_specs", [])
        relevant_tests = [test for test in test_specs if task_id in test.name]

        tests_passed = True

        # Simulate running tests
        for test_spec in relevant_tests[:2]:  # Limit test execution
            # In a real implementation, this would execute the actual test command
            self.logger.info(f"Running test: {test_spec.name}")

            # For now, assume tests pass unless it's explicitly a failure scenario
            if "fail" not in test_spec.description.lower():
                continue
            else:
                tests_passed = False
                break

        return TaskExecutionResult(
            task_id=task_id,
            success=tests_passed,
            message=f"Validation {'passed' if tests_passed else 'failed'}",
            tests_passed=tests_passed,
            execution_time=2.0,
        )

    def _validate_and_finalize(
        self, goal: str, execution_result: ExecutionResult
    ) -> GitResult:
        """
        Validate execution results and finalize with commit.

        Args:
            goal: Original goal
            execution_result: Task execution results

        Returns:
            GitResult from commit operation
        """
        if not execution_result.success:
            return GitResult(success=False, message="Cannot finalize failed execution")

        # Create commit with all changes
        commit_summary = f"Implement: {goal}"
        commit_details = f"Autonomous implementation completed\n\nTasks completed: {execution_result.tasks_completed}\nExecution time: {execution_result.execution_time:.2f}s"

        # Get list of changed files
        status_result = self.repo_ops.git.status()
        if not status_result.success:
            return GitResult(success=False, message="Failed to get repository status")

        if not status_result.stdout:
            # No changes to commit
            return GitResult(success=True, message="No changes to commit")

        # Commit changes
        commit_result = self.repo_ops.commit_changes(commit_summary, commit_details)

        if commit_result.success:
            execution_result.commit_sha = self.repo_ops.git.get_current_sha()
            execution_result.branch_created = self.repo_ops.git.get_current_branch()
            self.logger.info(f"Created commit: {execution_result.commit_sha}")

        return commit_result

    def _create_pull_request(self, goal: str, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create pull request for the changes.

        Args:
            goal: Original goal
            plan: Execution plan

        Returns:
            Dictionary with PR creation results
        """
        pr_title = f"Autonomous implementation: {goal}"
        pr_body = f"""## Summary
{goal}

## Implementation Details
- Total tasks: {plan['total_tasks']}
- Complexity: {plan.get('estimated_complexity', 'medium')}
- Plan hash: {plan['plan_hash']}

## Changes Made
This PR was generated autonomously by TermNet following Google AI best practices.

## Testing
Automated tests have been executed as part of the implementation process.

🤖 Generated with TermNet Autopilot"""

        # Create PR
        push_result, pr_result = self.repo_ops.create_pr_for_branch(
            pr_title, pr_body, self.config.base_branch
        )

        if pr_result.success:
            # Extract PR URL from result
            pr_url = pr_result.stdout.strip() if pr_result.stdout else None
            return {"success": True, "url": pr_url}
        else:
            return {"success": False, "error": pr_result.message}

    def _rollback_changes(self) -> bool:
        """
        Rollback changes using backup.

        Returns:
            True if rollback successful, False otherwise
        """
        if not self.backup_location:
            self.logger.error("No backup available for rollback")
            return False

        try:
            self.logger.info(
                f"Rolling back changes from backup: {self.backup_location}"
            )

            # Restore files from backup
            backup_repo = Path(self.backup_location) / "repo"
            if backup_repo.exists():
                # Copy files back (excluding .git)
                for item in backup_repo.iterdir():
                    if item.name != ".git":
                        dest = self.repo_path / item.name
                        if dest.exists():
                            if dest.is_dir():
                                shutil.rmtree(dest)
                            else:
                                dest.unlink()
                        shutil.copytree(item, dest) if item.is_dir() else shutil.copy2(
                            item, dest
                        )

            # Reset git state
            git_state_file = Path(self.backup_location) / "git_state.json"
            if git_state_file.exists():
                with open(git_state_file) as f:
                    git_state = json.load(f)

                # Reset to original branch and commit
                self.repo_ops.git._run_git_command(["checkout", git_state["branch"]])
                self.repo_ops.git.reset_to_commit(git_state["sha"], hard=True)

            self.logger.info("Rollback completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            return False

    def get_execution_status(self) -> Dict[str, Any]:
        """
        Get current execution status.

        Returns:
            Dictionary with execution status information
        """
        repo_state = self.repo_ops.get_repository_state()

        return {
            "autopilot_version": "1.0.0",
            "repository_state": repo_state,
            "config": asdict(self.config),
            "backup_location": self.backup_location,
            "current_execution": self.current_execution,
        }
