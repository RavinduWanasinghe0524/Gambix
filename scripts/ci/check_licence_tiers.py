"""
CI gate: check no Tier C raw data is staged in the release folder.

Reads data/MANIFEST.jsonl and fails if any entry has:
  - licence_tier == "C"
  - AND path starts with data/processed/

Exit 0 = pass, Exit 1 = fail (CI will mark the job as failed).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    manifest_path = Path("data/MANIFEST.jsonl")
    if not manifest_path.exists():
        print("No MANIFEST.jsonl found — skipping licence check.")
        sys.exit(0)

    violations: list[str] = []
    with manifest_path.open() as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as exc:
                print(f"MANIFEST.jsonl line {lineno}: invalid JSON — {exc}")
                sys.exit(1)

            tier = entry.get("licence_tier", "")
            path = entry.get("path", "")
            if tier == "C" and path.startswith("data/processed/"):
                violations.append(
                    f"  Line {lineno}: licence_tier=C found in release folder → {path}"
                )

    if violations:
        print("❌ CI GATE FAILED: Tier C data found in data/processed/ (release folder).")
        print("   Remove the following entries or move them to a non-release path:")
        for v in violations:
            print(v)
        sys.exit(1)
    else:
        print("✅ Licence tier check passed — no Tier C data in release folder.")
        sys.exit(0)


if __name__ == "__main__":
    main()
