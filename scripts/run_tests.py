#!/usr/bin/env python3
"""Pytest wrapper with environment handling for GPTTalker.

Sets PYTHONPATH to include src/, uses sqlite+aiosqlite:///:memory: test database,
and accepts optional pytest arguments.
"""

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    """Run pytest with proper environment."""
    # Ensure src is in Python path
    repo_root = Path(__file__).parent.parent
    src_path = repo_root / "src"

    # Set PYTHONPATH if not already set
    current_pythonpath = os.environ.get("PYTHONPATH", "")
    if str(src_path) not in current_pythonpath:
        os.environ["PYTHONPATH"] = f"{src_path}:{current_pythonpath}"

    # Set test database URL
    os.environ.setdefault("TEST_DB_URL", "sqlite+aiosqlite:///:memory:")
    os.environ.setdefault("LOG_LEVEL", "WARNING")

    # Build pytest command
    pytest_args = [
        sys.executable,
        "-m",
        "pytest",
        "tests/",
        "-v",
    ]

    # Add any additional arguments passed to this script
    if len(sys.argv) > 1:
        pytest_args.extend(sys.argv[1:])

    print("GPTTalker Test Runner")
    print("=" * 40)
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH')}")
    print(f"TEST_DB_URL: {os.environ.get('TEST_DB_URL')}")
    print(f"Command: {' '.join(pytest_args)}")
    print()

    # Run pytest
    result = subprocess.run(pytest_args, cwd=repo_root)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
