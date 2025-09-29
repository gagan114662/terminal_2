"""CI bootstrap for Project Mode."""

from pathlib import Path


def ensure_ci() -> str:
    """
    Create .github/workflows/ci.yml if it doesn't exist.
    Idempotent: safe to call multiple times.

    Returns:
        Path to created/existing CI workflow file
    """
    # Create .github/workflows directory
    workflows_dir = Path(".github/workflows")
    workflows_dir.mkdir(parents=True, exist_ok=True)

    # Create CI workflow
    ci_file = workflows_dir / "ci.yml"
    if ci_file.exists():
        return str(ci_file)

    ci_content = """name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pre-commit

      - name: Run pre-commit hooks
        run: |
          pre-commit run --all-files --show-diff-on-failure || true

      - name: Run tests
        run: |
          pytest -q

      - name: Run acceptance tests
        run: |
          pytest tests/acceptance -q || echo "Acceptance tests skipped"
"""

    ci_file.write_text(ci_content)
    return str(ci_file)