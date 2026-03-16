#!/usr/bin/env python3
"""Unified validation entrypoint for GPTTalker.

Runs lint and tests in sequence. Exits with code 1 if any step fails.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and report results."""
    print(f"\n{'=' * 60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'=' * 60}\n")

    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    return result.returncode == 0


def main() -> int:
    """Run full validation: lint + tests."""
    print("GPTTalker Validation Runner")
    print("=" * 40)

    # Run lint
    lint_ok = run_command(
        ["python", "-m", "ruff", "check", "src/", "tests/", "scripts/"], "Linting (ruff check)"
    )

    if not lint_ok:
        print("\n❌ LINTING FAILED")
        return 1

    # Run format check
    format_ok = run_command(
        ["python", "-m", "ruff", "format", "--check", "src/", "tests/", "scripts/"],
        "Format check (ruff format)",
    )

    if not format_ok:
        print("\n❌ FORMAT CHECK FAILED")
        return 1

    # Run tests
    test_ok = run_command(["python", "-m", "pytest", "tests/", "-v"], "Test suite (pytest)")

    if not test_ok:
        print("\n❌ TESTS FAILED")
        return 1

    print("\n" + "=" * 40)
    print("✅ ALL VALIDATION PASSED")
    print("=" * 40)
    return 0


if __name__ == "__main__":
    sys.exit(main())
