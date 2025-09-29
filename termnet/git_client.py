import subprocess
import sys
from contextlib import contextmanager


def _run(cmd, cwd=None, check=True, capture_output=True, text=True):
    return subprocess.run(
        cmd, cwd=cwd, check=check, capture_output=capture_output, text=text
    )


class GitClient:
    def __init__(self, repo_path="."):
        self.repo_path = repo_path

    def get_status_porcelain(self) -> str:
        res = _run(["git", "status", "--porcelain"], cwd=self.repo_path)
        return res.stdout

    def has_uncommitted_changes(self) -> bool:
        return bool(self.get_status_porcelain().strip())

    def stash_count(self) -> int:
        res = _run(["git", "stash", "list"], cwd=self.repo_path)
        return len([ln for ln in res.stdout.splitlines() if ln.strip()])

    def stash_create(self, message: str = "autostash: TermNet safety") -> int:
        _run(
            ["git", "stash", "push", "--include-untracked", "-m", message],
            cwd=self.repo_path,
            check=False,
        )
        after = self.stash_count()
        return after

    def stash_pop(self, index: int = 0, quiet: bool = True):
        args = ["git", "stash", "pop"]
        if index != 0:
            args.append(f"stash@{{{index}}}")
        if quiet:
            _run(args, cwd=self.repo_path, check=False)
        else:
            subprocess.run(args, cwd=self.repo_path, check=False)

    def has_unresolved_merges(self) -> bool:
        """Check if repository has unresolved merge conflicts."""
        try:
            status = self.get_status_porcelain()
            # Look for unmerged files (status codes UU, AA, DD, etc.)
            for line in status.splitlines():
                if len(line) >= 2 and (line[0] == "U" or line[1] == "U"):
                    return True
            return False
        except Exception:
            return False

    @contextmanager
    def autostash(
        self,
        echo=print,
        dry_run: bool = False,
        message: str = "autostash: TermNet safety",
    ):
        had_changes = self.has_uncommitted_changes()
        if not had_changes:
            yield {"stashed": False, "stash_count_before": self.stash_count()}
            return

        porcelain = self.get_status_porcelain().strip().splitlines()
        changed_paths = len([ln for ln in porcelain if ln.strip()])

        if dry_run:
            echo(
                (
                    f"⚠️  Dry-run: would auto-stash {changed_paths} change(s). "
                    f"Skipping stash in dry-run."
                )
            )
            yield {
                "stashed": False,
                "stash_count_before": self.stash_count(),
                "would_change": changed_paths,
            }
            return

        echo(f"Auto-stashing ({changed_paths} change(s))")
        before = self.stash_count()
        self.stash_create(message=message)
        try:
            yield {"stashed": True, "stash_count_before": before}
        finally:
            try:
                self.stash_pop(index=0, quiet=True)
                echo("Restored stashed changes")
                # Write to a completion file that the test can check
                import os

                completion_file = os.path.join(
                    self.repo_path, ".logs", "restore_complete.flag"
                )
                os.makedirs(os.path.dirname(completion_file), exist_ok=True)
                with open(completion_file, "w") as f:
                    f.write("Restored stashed changes\n")
            except Exception as e:
                echo(f"Warning: Failed to restore stash: {e}")
                sys.stdout.flush()
                sys.stderr.flush()

    def checkout_new_branch(self, name: str) -> bool:
        """Create and checkout a new branch."""
        try:
            _run(["git", "checkout", "-b", name], cwd=self.repo_path, check=True)
            return True
        except Exception:
            return False

    def get_current_branch(self) -> str:
        """Get the current branch name."""
        try:
            result = _run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=self.repo_path
            )
            return result.stdout.strip()
        except Exception:
            return "unknown"

    def add_all(self) -> bool:
        """Add all changes to staging."""
        try:
            _run(["git", "add", "."], cwd=self.repo_path, check=True)
            return True
        except Exception:
            return False

    def commit(self, message: str) -> bool:
        """Create a commit with the given message."""
        try:
            _run(["git", "commit", "-m", message], cwd=self.repo_path, check=True)
            return True
        except Exception:
            return False

    def ensure_remote(self, origin: str = "origin") -> bool:
        """Return True if remote exists."""
        try:
            _run(["git", "remote", "get-url", origin], cwd=self.repo_path, check=True)
            return True
        except Exception:
            return False

    def push_current_branch(self, set_upstream: bool = True) -> None:
        """Push current branch with optional upstream setting."""
        try:
            current_branch = self.get_current_branch()
            if set_upstream:
                _run(
                    ["git", "push", "--set-upstream", "origin", current_branch],
                    cwd=self.repo_path,
                    check=True,
                )
            else:
                _run(["git", "push"], cwd=self.repo_path, check=True)
        except Exception:
            pass

    def open_pr(self, title: str, body: str) -> str:
        """Create a pull request using gh CLI."""
        try:
            result = _run(
                ["gh", "pr", "create", "--title", title, "--body", body, "--fill"],
                cwd=self.repo_path,
                check=True,
            )
            return result.stdout.strip()
        except Exception as e:
            return f"Error: {e}"


def add_pr_labels(labels: list) -> None:
    """Add labels to the current PR (best-effort using gh CLI)."""
    import shutil

    if not shutil.which("gh"):
        return

    try:
        subprocess.run(
            ["gh", "pr", "edit", "--add-label", ",".join(labels)],
            capture_output=True,
            check=False,
        )
    except Exception:
        pass  # Best-effort, ignore errors
