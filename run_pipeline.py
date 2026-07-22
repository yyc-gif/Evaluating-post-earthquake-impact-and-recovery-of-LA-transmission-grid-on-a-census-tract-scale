"""Run the complete manuscript workflow from one stable entry point."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent

STEPS = (
    ("topology", "Build topology and tract dependencies", "Topology_and_Weight_expanded.py"),
    ("pga", "Interpolate scenario PGA values", "IDW_expanded.py"),
    ("travel", "Build road travel-time matrices", "build_travel_matrices_osm_expanded.py"),
    ("analysis", "Run damage, recovery, scheduling, GA, and clustering", "C257H_Project_Main_expanded.py"),
    ("figures", "Generate stage figures", "Project_Visualizer_expanded.py"),
    ("composites", "Assemble manuscript figures", "make_manuscript_composites.py"),
)


def parse_args() -> argparse.Namespace:
    """Parse optional bounds for resuming the ordered workflow."""
    step_names = [step[0] for step in STEPS]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--from-step",
        choices=step_names,
        default=step_names[0],
        help="First step to run (default: topology).",
    )
    parser.add_argument(
        "--through-step",
        choices=step_names,
        default=step_names[-1],
        help="Last step to run (default: composites).",
    )
    return parser.parse_args()


def main() -> None:
    """Execute the selected contiguous workflow steps in separate processes."""
    args = parse_args()
    step_names = [step[0] for step in STEPS]
    start = step_names.index(args.from_step)
    stop = step_names.index(args.through_step)
    if start > stop:
        raise SystemExit("--from-step must not come after --through-step")

    selected = STEPS[start : stop + 1]
    for position, (_, description, script_name) in enumerate(selected, start=1):
        script_path = PROJECT_ROOT / script_name
        if not script_path.exists():
            raise FileNotFoundError(f"Workflow script not found: {script_path}")
        print(f"[{position}/{len(selected)}] {description}", flush=True)
        subprocess.run(
            [sys.executable, str(script_path)],
            cwd=PROJECT_ROOT,
            check=True,
        )

    print("Workflow completed successfully.")


if __name__ == "__main__":
    main()
