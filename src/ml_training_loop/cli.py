"""Minimal bootstrap/status CLI; hosts construct model-family adapters."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .skills import BundledSkillBootstrapper, FOUNDATION_SKILLS
from .stores import JsonRunStore


PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_BUNDLE = PACKAGE_ROOT / "bundled_skills"
DEFAULT_STATE = Path(".ml-training-loop/runs")


def main() -> int:
    parser = argparse.ArgumentParser(prog="ml-training-loop")
    subparsers = parser.add_subparsers(dest="command", required=True)
    bootstrap = subparsers.add_parser("bootstrap-skills")
    bootstrap.add_argument("skills", nargs="*")
    bootstrap.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    status = subparsers.add_parser("status")
    status.add_argument("run_id")
    status.add_argument("--state-root", type=Path, default=DEFAULT_STATE)
    args = parser.parse_args()

    if args.command == "bootstrap-skills":
        required = tuple(args.skills) or FOUNDATION_SKILLS
        receipt = BundledSkillBootstrapper(args.bundle).ensure(required)
        print(json.dumps({
            "ready": receipt.ready,
            "skills": [item.__dict__ for item in receipt.statuses],
        }, indent=2, sort_keys=True))
        return 0 if receipt.ready else 2

    state = JsonRunStore(args.state_root).load(args.run_id)
    if state is None:
        print(json.dumps({"run_id": args.run_id, "status": "not_found"}))
        return 1
    print(json.dumps({
        "run_id": state.run_id,
        "phase": state.phase.value,
        "stage_index": state.stage_index,
        "attempts": state.attempts,
        "message": state.message,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
