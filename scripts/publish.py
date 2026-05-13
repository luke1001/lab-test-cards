#!/usr/bin/env python3
"""Build, validate, commit, and push the Lab Test Cards site."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(args: list[str]) -> str:
    result = subprocess.run(args, cwd=ROOT, check=True, text=True, capture_output=True)
    return result.stdout.strip()


def main() -> None:
    status = run(["git", "status", "--short"])
    if status:
        allowed = all(
            line[0:2] in {"??", " M", "M ", "A ", "AM", "MM"}
            and (
                line[2:].strip().startswith("data/")
                or line[2:].strip().startswith("docs/")
                or line[2:].strip().startswith("scripts/")
                or line[2:].strip() in {".gitignore", "README.md"}
            )
            for line in status.splitlines()
        )
        if not allowed:
            raise SystemExit("refusing to publish: unrelated dirty changes are present")

    run([sys.executable, "scripts/build_site.py"])
    run([sys.executable, "scripts/validate_site.py"])
    run(["git", "add", "."])
    post_add = run(["git", "status", "--short"])
    if not post_add:
        print("nothing to publish")
        return
    run(["git", "commit", "-m", "Update lab test cards site"])
    run(["git", "push", "-u", "origin", "main"])
    print("published lab test cards site")


if __name__ == "__main__":
    main()
