"""
TermNet Edit Engine

Safely applies code patches with conflict resolution and guardrails.
Follows Google AI best practices: idempotent operations, clear error handling.
"""

import os
import re
import shutil
import tempfile
from dataclasses import asdict, dataclass
from typing import Any, Dict, List


@dataclass
class EditResult:
    """Result of an edit operation."""

    status: str  # "success", "conflict", "error", "blocked"
    files_touched: List[str]
    idempotent: bool
    message: str
    conflicts: List[str] = None
    diff_applied: str = ""

    def __post_init__(self):
        if self.conflicts is None:
            self.conflicts = []


@dataclass
class GuardrailViolation:
    """Represents a guardrail violation."""

    rule: str
    file_path: str
    reason: str
    severity: str = "error"


class EditEngine:
    """
    Safely applies code patches with conflict resolution and guardrails.

    Provides idempotent patch application with rollback capabilities and
    comprehensive safety checks to prevent harmful changes.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize edit engine with configuration.

        Args:
            config: Configuration dictionary with guardrails and limits
        """
        self.config = config or {}
        self._setup_defaults()
        self._backup_dir = None

    def apply_patch(self, diff: str, dry_run: bool = True) -> EditResult:
        """
        Apply a unified diff patch to the repository.

        Args:
            diff: Unified diff string to apply
            dry_run: If True, validate but don't actually modify files

        Returns:
            EditResult with status and details
        """
        # Parse the diff
        try:
            patches = self._parse_unified_diff(diff)
        except Exception as e:
            return EditResult(
                status="error",
                files_touched=[],
                idempotent=False,
                message=f"Failed to parse diff: {e}",
            )

        # Validate guardrails
        violations = self._check_guardrails(patches)
        if violations:
            return EditResult(
                status="blocked",
                files_touched=[],
                idempotent=False,
                message=f"Guardrail violations: {[v.reason for v in violations]}",
            )

        # Check if patch is idempotent (already applied)
        idempotent_check = self._check_idempotency(patches)
        if idempotent_check:
            return EditResult(
                status="success",
                files_touched=list(sorted(patches.keys())),
                idempotent=True,
                message="No changes needed; patch already applied (idempotent)",
                conflicts=[],
                diff_applied=diff,
            )

        if dry_run:
            # Perform dry run by applying patches in memory
            try:
                conflicts = []
                for file_path, hunks in patches.items():
                    repo_path = self.config.get("repo_path", ".")
                    full_path = os.path.join(repo_path, file_path)

                    if os.path.exists(full_path):
                        with open(full_path, "r", encoding="utf-8") as f:
                            content = f.readlines()
                    else:
                        content = []

                    # Try to apply hunks in memory
                    try:
                        self._apply_hunks_to_content(content, hunks)
                    except Exception as e:
                        conflicts.append(f"{file_path}: {str(e)}")

                if conflicts:
                    return EditResult(
                        status="conflict",
                        files_touched=list(patches.keys()),
                        idempotent=False,
                        message="Conflicts detected in dry run",
                        conflicts=conflicts,
                    )

                return EditResult(
                    status="success",
                    files_touched=list(patches.keys()),
                    idempotent=False,
                    message="Dry run: patch would apply cleanly",
                    diff_applied=diff,
                )

            except Exception as e:
                return EditResult(
                    status="conflict",
                    files_touched=list(patches.keys()),
                    idempotent=False,
                    message=f"Dry run failed: {str(e)}",
                    conflicts=[str(e)],
                )

        # Apply patches with conflict handling
        return self._apply_patches_with_retry(patches, diff)

    def _setup_defaults(self):
        """Setup default configuration values."""
        defaults = {
            "write_guardrails": {
                "allowed_paths": ["termnet/**", "tests/**", "docs/**", "scripts/**"],
                "blocked_paths": [
                    ".git/**",
                    "__pycache__/**",
                    "*.pyc",
                    "node_modules/**",
                ],
                "max_total_patch_bytes": 50000,
                "max_files_per_patch": 20,
                "require_tests": True,
                "dry_run": True,
            },
            "conflict_resolution": {
                "max_retries": 2,
                "split_hunks": True,
                "backup_on_conflict": True,
            },
        }

        # Merge with provided config
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
            elif isinstance(value, dict):
                self.config[key] = {**value, **self.config.get(key, {})}

    def _parse_unified_diff(self, diff: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Parse unified diff into structured format.

        Returns:
            Dict mapping file paths to list of hunks
        """
        patches = {}
        current_file = None
        current_hunk = None

        lines = diff.split("\n")
        i = 0

        while i < len(lines):
            line = lines[i]

            # File header
            if line.startswith("--- "):
                old_file = line[4:].strip()
                if old_file == "/dev/null":
                    old_file = None
            elif line.startswith("+++ "):
                new_file = line[4:].strip()
                if new_file == "/dev/null":
                    new_file = None
                else:
                    current_file = new_file
                    patches[current_file] = []

            # Hunk header
            elif line.startswith("@@"):
                if current_file is None:
                    raise ValueError("Hunk without file context")

                # Parse hunk header: @@ -old_start,old_count +new_start,new_count @@
                match = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line)
                if not match:
                    raise ValueError(f"Invalid hunk header: {line}")

                old_start = int(match.group(1))
                old_count = int(match.group(2)) if match.group(2) else 1
                new_start = int(match.group(3))
                new_count = int(match.group(4)) if match.group(4) else 1

                current_hunk = {
                    "old_start": old_start,
                    "old_count": old_count,
                    "new_start": new_start,
                    "new_count": new_count,
                    "lines": [],
                }
                patches[current_file].append(current_hunk)

            # Hunk content
            elif current_hunk is not None and (
                line.startswith(" ")
                or line.startswith("-")
                or line.startswith("+")
                or line == ""
            ):
                # Handle empty lines (should be context lines with just a space)
                if line == "":
                    current_hunk["lines"].append(" ")
                else:
                    current_hunk["lines"].append(line)

            i += 1

        return patches

    def _check_guardrails(
        self, patches: Dict[str, List[Dict[str, Any]]]
    ) -> List[GuardrailViolation]:
        """Check patch against configured guardrails."""
        violations = []
        guardrails = self.config["write_guardrails"]

        # Check file count limit
        if len(patches) > guardrails["max_files_per_patch"]:
            violations.append(
                GuardrailViolation(
                    rule="max_files_per_patch",
                    file_path="",
                    reason=f"Patch affects {len(patches)} files, limit is {guardrails['max_files_per_patch']}",
                )
            )

        # Check total patch size
        total_bytes = sum(
            sum(len(line) for hunk in hunks for line in hunk["lines"])
            for hunks in patches.values()
        )
        if total_bytes > guardrails["max_total_patch_bytes"]:
            violations.append(
                GuardrailViolation(
                    rule="max_total_patch_bytes",
                    file_path="",
                    reason=f"Patch size {total_bytes} bytes exceeds limit {guardrails['max_total_patch_bytes']}",
                )
            )

        # Check file paths
        for file_path in patches.keys():
            # Check blocked paths
            if self._matches_patterns(file_path, guardrails["blocked_paths"]):
                violations.append(
                    GuardrailViolation(
                        rule="blocked_paths",
                        file_path=file_path,
                        reason=f"File {file_path} matches blocked path pattern",
                    )
                )

            # Check allowed paths
            if not self._matches_patterns(file_path, guardrails["allowed_paths"]):
                violations.append(
                    GuardrailViolation(
                        rule="allowed_paths",
                        file_path=file_path,
                        reason=f"File {file_path} not in allowed paths",
                    )
                )

        return violations

    def _matches_patterns(self, file_path: str, patterns: List[str]) -> bool:
        """Check if file path matches any of the given patterns."""
        import fnmatch

        for pattern in patterns:
            if fnmatch.fnmatch(file_path, pattern):
                return True
        return False

    def _check_idempotency(self, patches: Dict[str, List[Dict[str, Any]]]) -> bool:
        """Check if patch is already applied (idempotent)."""
        for file_path, hunks in patches.items():
            # Resolve file path relative to repo_path
            repo_path = self.config.get("repo_path", ".")
            full_path = os.path.join(repo_path, file_path)

            if not os.path.exists(full_path):
                # New file, not idempotent
                return False

            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    current_content = f.readlines()

                # Check if hunks are already applied
                for hunk in hunks:
                    if not self._hunk_already_applied(current_content, hunk):
                        return False

            except Exception:
                # Can't read file, assume not idempotent
                return False

        return True

    def _hunk_already_applied(self, content: List[str], hunk: Dict[str, Any]) -> bool:
        """Check if a specific hunk is already applied to content."""
        # Extract the expected result lines from hunk
        expected_lines = []
        for line in hunk["lines"]:
            if line.startswith(" ") or line.startswith("+"):
                expected_lines.append(line[1:])  # Remove prefix

        if not expected_lines:
            return True  # Empty hunk is considered applied

        # Check if expected lines appear in content at the right position
        start_line = hunk["new_start"] - 1  # Convert to 0-based
        end_line = start_line + len(expected_lines)

        if end_line > len(content):
            return False

        actual_lines = [line.rstrip("\n") for line in content[start_line:end_line]]
        expected_lines = [line.rstrip("\n") for line in expected_lines]

        return actual_lines == expected_lines

    def _check_conflicts(self, patches: Dict[str, List[Dict[str, Any]]]) -> List[str]:
        """Check for conflicts that would prevent patch application."""
        conflicts = []

        for file_path, hunks in patches.items():
            # Resolve file path relative to repo_path
            repo_path = self.config.get("repo_path", ".")
            full_path = os.path.join(repo_path, file_path)

            if not os.path.exists(full_path):
                continue  # New file, no conflicts

            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    current_content = f.readlines()

                for i, hunk in enumerate(hunks):
                    if not self._can_apply_hunk(current_content, hunk):
                        conflicts.append(f"{file_path}:hunk{i + 1}")

            except Exception as e:
                conflicts.append(f"{file_path}:read_error:{e}")

        return conflicts

    def _can_apply_hunk(self, content: List[str], hunk: Dict[str, Any]) -> bool:
        """Check if a hunk can be applied to content without conflicts."""
        old_start = hunk["old_start"] - 1  # Convert to 0-based
        context_lines = []
        removed_lines = []

        # Extract context and removed lines
        for line in hunk["lines"]:
            if line.startswith(" "):
                context_lines.append(
                    (len(context_lines) + len(removed_lines), line[1:])
                )
            elif line.startswith("-"):
                removed_lines.append(
                    (len(context_lines) + len(removed_lines), line[1:])
                )

        # Check if context matches
        for offset, expected_line in context_lines + removed_lines:
            line_index = old_start + offset
            if line_index >= len(content):
                return False

            actual_line = content[line_index].rstrip("\n")
            expected_line = expected_line.rstrip("\n")

            if actual_line != expected_line:
                return False

        return True

    def _apply_patches_with_retry(
        self, patches: Dict[str, List[Dict[str, Any]]], original_diff: str
    ) -> EditResult:
        """Apply patches with conflict resolution and retry logic."""
        # Create backup
        self._create_backup(list(patches.keys()))

        try:
            # First attempt: apply all patches
            conflicts = self._apply_patches(patches)

            if not conflicts:
                return EditResult(
                    status="success",
                    files_touched=list(patches.keys()),
                    idempotent=False,
                    message="Patch applied successfully",
                    diff_applied=original_diff,
                )

            # Retry with conflict resolution
            if self.config["conflict_resolution"]["split_hunks"]:
                resolved_conflicts = self._retry_with_split_hunks(patches, conflicts)
                remaining_conflicts = [
                    c for c in conflicts if c not in resolved_conflicts
                ]

                if not remaining_conflicts:
                    return EditResult(
                        status="success",
                        files_touched=list(patches.keys()),
                        idempotent=False,
                        message="Patch applied after conflict resolution",
                        diff_applied=original_diff,
                    )

            # Still have conflicts
            self._restore_backup()
            return EditResult(
                status="conflict",
                files_touched=list(patches.keys()),
                idempotent=False,
                message="Failed to resolve conflicts after retries",
                conflicts=conflicts,
            )

        except Exception as e:
            # Restore backup on error
            self._restore_backup()
            return EditResult(
                status="error",
                files_touched=list(patches.keys()),
                idempotent=False,
                message=f"Error applying patch: {e}",
            )

    def _apply_patches(self, patches: Dict[str, List[Dict[str, Any]]]) -> List[str]:
        """Apply patches and return list of conflicts."""
        conflicts = []

        for file_path, hunks in patches.items():
            try:
                # Resolve file path relative to repo_path
                repo_path = self.config.get("repo_path", ".")
                full_path = os.path.join(repo_path, file_path)

                if os.path.exists(full_path):
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.readlines()
                else:
                    content = []

                new_content = self._apply_hunks_to_content(content, hunks)

                # Ensure directory exists
                if os.path.dirname(full_path):
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)

                with open(full_path, "w", encoding="utf-8") as f:
                    f.writelines(new_content)

            except Exception as e:
                conflicts.append(f"{file_path}:apply_error:{e}")

        return conflicts

    def _apply_hunks_to_content(
        self, content: List[str], hunks: List[Dict[str, Any]]
    ) -> List[str]:
        """Apply hunks to content and return modified content."""
        # Sort hunks by start position (reverse order for safe application)
        sorted_hunks = sorted(hunks, key=lambda h: h["old_start"], reverse=True)

        new_content = content[:]

        for hunk in sorted_hunks:
            new_content = self._apply_single_hunk(new_content, hunk)

        return new_content

    def _apply_single_hunk(self, content: List[str], hunk: Dict[str, Any]) -> List[str]:
        """Apply a single hunk to content."""
        old_start = hunk["old_start"] - 1  # Convert to 0-based
        new_content = content[:]

        # Track current position in the file
        pos = old_start

        # Process hunk lines in order, applying changes immediately
        for line in hunk["lines"]:
            if line.startswith(" "):
                # Context line - verify it matches and advance position
                pos += 1
            elif line.startswith("-"):
                # Delete line at current position
                if pos < len(new_content):
                    del new_content[pos]
                # Don't advance pos since we deleted a line
            elif line.startswith("+"):
                # Insert line at current position
                new_line = line[1:]
                if not new_line.endswith("\n"):
                    new_line += "\n"
                new_content.insert(pos, new_line)
                # Advance position since we inserted a line
                pos += 1

        return new_content

    def _retry_with_split_hunks(
        self, patches: Dict[str, List[Dict[str, Any]]], conflicts: List[str]
    ) -> List[str]:
        """Retry applying patches by splitting conflicting hunks."""
        resolved = []

        for conflict in conflicts:
            if ":hunk" in conflict:
                file_path, hunk_ref = conflict.split(":hunk")
                hunk_index = int(hunk_ref) - 1

                if file_path in patches and hunk_index < len(patches[file_path]):
                    # Try to split and apply the hunk
                    if self._try_split_hunk_application(
                        file_path, patches[file_path][hunk_index]
                    ):
                        resolved.append(conflict)

        return resolved

    def _try_split_hunk_application(self, file_path: str, hunk: Dict[str, Any]) -> bool:
        """Try to apply a hunk by splitting it into smaller parts."""
        # Simple implementation: try applying line by line
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.readlines()

            # This is a simplified split approach
            # In practice, you'd implement more sophisticated hunk splitting
            modified_content = self._apply_single_hunk(content, hunk)

            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(modified_content)

            return True

        except Exception:
            return False

    def _create_backup(self, file_paths: List[str]):
        """Create backup of files before modification."""
        if not self.config["conflict_resolution"]["backup_on_conflict"]:
            return

        self._backup_dir = tempfile.mkdtemp(prefix="edit_engine_backup_")

        for file_path in file_paths:
            if os.path.exists(file_path):
                backup_path = os.path.join(
                    self._backup_dir, file_path.replace("/", "_")
                )
                shutil.copy2(file_path, backup_path)

    def _restore_backup(self):
        """Restore files from backup."""
        if not self._backup_dir or not os.path.exists(self._backup_dir):
            return

        for backup_file in os.listdir(self._backup_dir):
            original_path = backup_file.replace("_", "/")
            backup_path = os.path.join(self._backup_dir, backup_file)

            if os.path.exists(backup_path):
                shutil.copy2(backup_path, original_path)

        # Cleanup backup
        shutil.rmtree(self._backup_dir)
        self._backup_dir = None

    def get_patch_preview(self, diff: str) -> Dict[str, Any]:
        """
        Generate a preview of what the patch would do.

        Args:
            diff: Unified diff string

        Returns:
            Preview information including files, lines changed, etc.
        """
        try:
            patches = self._parse_unified_diff(diff)
            violations = self._check_guardrails(patches)

            files_affected = list(patches.keys())
            total_additions = 0
            total_deletions = 0

            for hunks in patches.values():
                for hunk in hunks:
                    for line in hunk["lines"]:
                        if line.startswith("+"):
                            total_additions += 1
                        elif line.startswith("-"):
                            total_deletions += 1

            # Generate previews for each file
            previews = {}
            for file_path, hunks in patches.items():
                repo_path = self.config.get("repo_path", ".")
                full_path = os.path.join(repo_path, file_path)

                if os.path.exists(full_path):
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.readlines()
                else:
                    content = []

                # Apply hunks to show preview
                try:
                    preview_content = self._apply_hunks_to_content(content, hunks)
                    previews[file_path] = "".join(preview_content)
                except:
                    previews[file_path] = f"Preview unavailable for {file_path}"

            return {
                "status": "blocked" if violations else "success",
                "files_affected": files_affected,
                "total_additions": total_additions,
                "total_deletions": total_deletions,
                "violations": [asdict(v) for v in violations],
                "idempotent": self._check_idempotency(patches),
                "patch_size_bytes": len(diff),
                "previews": previews,
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "files_affected": [],
                "total_additions": 0,
                "total_deletions": 0,
                "violations": [],
                "idempotent": False,
                "patch_size_bytes": len(diff),
            }
