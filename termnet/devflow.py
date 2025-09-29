"""DevFlow - Branch and PR workflow automation"""

import re
import subprocess


def slugify(text: str) -> str:
    """Convert text to git-friendly slug.

    Lowercase, replace spaces/invalids with -, trim to ≤40 chars.
    """
    # Convert to lowercase and replace spaces/special chars with dashes
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[-\s]+", "-", slug)
    # Limit length and trim dashes
    slug = slug[:40].strip("-")
    return slug or "feature"


class DevFlow:
    """Automates development workflow: branch → commit → PR creation."""

    def __init__(self, git, echo=print):
        self.git = git
        self.echo = echo

    def start_feature(self, name: str):
        """Create & checkout branch feat/<slug>."""
        slug = slugify(name)
        branch_name = f"feat/{slug}"
        self.git.checkout_new_branch(branch_name)
        return branch_name

    def checkpoint(self, msg: str):
        """git add -A then commit(msg) (conventional commits)."""
        self.git.add_all()
        self.git.commit(msg)

    def push_current_branch(self):
        """Push with --set-upstream if needed."""
        self.git.push_current_branch(set_upstream=True)

    def open_pr(self, title: str, body: str) -> str:
        """Use gh pr create with title and body.

        Return empty string if gh missing.
        """
        try:
            result = subprocess.run(
                ["gh", "pr", "create", "--title", title, "--body", body, "--fill"],
                capture_output=True,
                text=True,
                check=True,
            )

            # Extract PR URL from output
            output = (result.stdout or result.stderr).strip()

            # Look for GitHub PR URL in output
            pr_url_match = re.search(
                r"https://github\.com/[^/]+/[^/]+/pull/\d+", output
            )
            if pr_url_match:
                return pr_url_match.group(0)
            else:
                return output

        except FileNotFoundError:
            self.echo("Note: gh CLI not found. Install with: brew install gh")
            return ""
        except subprocess.CalledProcessError as e:
            self.echo(f"Failed to create PR: {e.stderr}")
            return ""
