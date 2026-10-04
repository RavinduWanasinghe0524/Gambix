"""
CI gate: enforce mutation score > 80% on gambix/symbolic/.

Parses mutmut's result output and fails if the kill rate is below threshold.

Exit 0 = pass, Exit 1 = fail.
"""

from __future__ import annotations

import subprocess
import sys

THRESHOLD = 0.80  # 80% kill rate required


def main() -> None:
    result = subprocess.run(
        ["mutmut", "results"],
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr

    # Parse mutmut summary line, e.g.:
    # "Survived: 5, Killed: 42, Total: 47"
    survived = 0
    killed = 0
    for line in output.splitlines():
        line_lower = line.lower()
        if "survived" in line_lower and "killed" in line_lower:
            parts = line.replace(",", "").split()
            for i, p in enumerate(parts):
                if p.lower() == "survived:":
                    survived = int(parts[i + 1])
                elif p.lower() == "killed:":
                    killed = int(parts[i + 1])

    total = survived + killed
    if total == 0:
        print("[WARN] mutmut returned zero mutants - check paths_to_mutate config.")
        sys.exit(1)

    kill_rate = killed / total
    print(f"Mutation score: {kill_rate:.1%}  ({killed}/{total} killed)")

    if kill_rate < THRESHOLD:
        print(
            f"[FAIL] CI GATE FAILED: mutation score {kill_rate:.1%} < "
            f"required {THRESHOLD:.0%}"
        )
        sys.exit(1)
    else:
        print(f"[PASS] Mutation score gate passed ({kill_rate:.1%} >= {THRESHOLD:.0%})")
        sys.exit(0)


if __name__ == "__main__":
    main()
