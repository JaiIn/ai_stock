"""Run the standard local validation sequence from the repository root."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class CheckStep:
    """One command in the local validation sequence."""

    name: str
    command: tuple[str, ...]
    environment: dict[str, str] | None = None


def _display_command(command: tuple[str, ...]) -> str:
    displayed = ("python", *command[1:]) if command[0] == sys.executable else command
    return subprocess.list2cmdline(displayed)


def _run_step(step: CheckStep) -> bool:
    print(f"\n[RUN] {step.name}: {_display_command(step.command)}", flush=True)
    environment = os.environ.copy()
    if step.environment:
        environment.update(step.environment)

    try:
        result = subprocess.run(
            step.command,
            cwd=REPOSITORY_ROOT,
            env=environment,
            check=False,
        )
    except FileNotFoundError as error:
        print(f"[FAIL] {step.name}: {error}", flush=True)
        return False

    if result.returncode == 0:
        print(f"[PASS] {step.name}", flush=True)
        return True

    print(f"[FAIL] {step.name}: exit code {result.returncode}", flush=True)
    return False


def main() -> int:
    """Execute every local check and return non-zero when any check fails."""

    checks = (
        CheckStep(
            "compileall",
            (sys.executable, "-m", "compileall", "-q", "src", "tests"),
        ),
        CheckStep(
            "unittest",
            (sys.executable, "-m", "unittest", "discover", "-s", "tests"),
        ),
        CheckStep(
            "pytest",
            (sys.executable, "-m", "pytest"),
            {"PYTEST_ADDOPTS": "-p no:cacheprovider"},
        ),
        CheckStep("git diff check", ("git", "diff", "--check")),
    )

    failed = [step.name for step in checks if not _run_step(step)]
    if failed:
        print(f"\n[FAIL] dev check failed: {', '.join(failed)}", flush=True)
        return 1

    print("\n[PASS] all local checks passed", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
