#!/usr/bin/env python3
"""Ruff wrapper with output formatting for GPTTalker.

Runs ruff check and ruff format --check on src/, tests/, and scripts/ directories.
"""

import subprocess
import sys
from pathlib import Path


def run_ruff_check() -> bool:
    """Run ruff check."""
    print("Running ruff check...")
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "src/", "tests/", "scripts/"],
        cwd=Path(__file__).parent.parent,
    )
    return result.returncode == 0


def run_ruff_format() -> bool:
    """Run ruff format check."""
    print("Running ruff format check...")
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "format", "--check", "src/", "tests/", "scripts/"],
        cwd=Path(__file__).parent.parent,
    )
    return result.returncode == 0


def main() -> int:
    """Run linting with ruff."""
    print("GPTTalker Lint Runner")
    print("=" * 40)

    check_ok = run_ruff_check()
    if not check_ok:
        print("\n❌ RUFF CHECK FAILED")
        return 1

    format_ok = run_ruff_format()
    if not format_ok:
        print("\n❌ RUFF FORMAT CHECK FAILED")
        return 1

    print("\n" + "=" * 40)
    print("✅ ALL LINT CHECKS PASSED")
    print("=" * 40)
    return 0


if __name__ == "__main__":
    sys.exit(main())
