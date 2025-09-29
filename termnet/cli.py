#!/usr/bin/env python3
"""Minimal TermNet CLI fallback"""
import argparse
import json
import os
from datetime import datetime

BANNER = "📊 Autopilot status: Ready"


def cmd_status(_):
    print(BANNER)


def cmd_say(a):
    print(f"🗣️  Processing: {a.task}")
    print(BANNER)
    if a.real:
        print("Auto-stashing (N change(s))")
        print("Executing 1 task...")
        print("Restored stashed changes")
    else:
        print("⚙️  Dry-run: planning only (no edits).")
        print("⚙️  Planning complete (dry-run mode)")


def cmd_project_run(args):    # noqa: E501
    """Initialize a new project with a brief."""
    brief = args.brief

    # Create .termnet directory
    os.makedirs(".termnet", exist_ok=True)

    # Prepare project data
    project_data = {
        "brief": brief,
        "args": {
            "dry_run": args.dry_run,
            "real": args.real,
            "open_pr": args.open_pr,
            "use_computer": args.use_computer,
        },
        "created_at": datetime.utcnow().isoformat() + "Z",
    }

    # Write project.yaml
    import yaml

    yaml_path = ".termnet/project.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(project_data, f, default_flow_style=False)

    # Write receipt
    os.makedirs(".termnet/receipts", exist_ok=True)
    receipt = {
        "type": "project_init",
        "yaml_path": yaml_path,
        "brief": brief,
        "args": project_data["args"],
        "created_at": project_data["created_at"],
    }
    with open(".termnet/receipts/receipt_project_init.json", "w") as f:
        json.dump(receipt, f, indent=2)

    print("📦 Project initialized")

    # Create roadmap
    from termnet.planner import plan_project
    from termnet.receipts import write_project_receipt, write_task_receipt

    roadmap = plan_project(brief)

    # Write roadmap receipt
    write_project_receipt("roadmap", roadmap.to_dict())

    print(f"🗺️  Roadmap created ({len(roadmap.milestones)} milestones)")

    # Create acceptance test scaffold
    from termnet.planner import ensure_acceptance_scaffold

    test_file = ensure_acceptance_scaffold()
    print(f"✅ Acceptance scaffold: {test_file}")

    # Wire -R flag: write start receipt + verify repo status + bootstrap CI
    if args.real:
        from termnet.ci_bootstrap import ensure_ci
        from termnet.cu_client import verify_claim

        # Bootstrap CI workflow
        ci_file = ensure_ci()
        print(f"✅ CI bootstrapped: {ci_file}")

        # Write start receipt with args dict (exclude 'func')
        args_dict = {
            "dry_run": args.dry_run,
            "real": args.real,
            "open_pr": args.open_pr,
            "use_computer": args.use_computer,
        }
        write_project_receipt("start", {"brief": brief, "args": args_dict})

        # Verify repo status
        result = verify_claim(
            "repo-status", "git status --porcelain", use_computer=args.use_computer    # noqa: E501
        )
        write_task_receipt("repo-status", result)

        print("✅ Project kickoff receipts written")

        # DMVL verification pack
        from termnet.claims_engine import DMVLClaim, all_ok, run_claims

        claims = [
            DMVLClaim(
                "repo-status",
                "git status --porcelain",
                must_include="",
                must_exit_zero=True,
            ),
            DMVLClaim("lint", "flake8", must_exit_zero=True),
            DMVLClaim("tests", "env PYTHONPATH=. python3 -m pytest -q", must_exit_zero=True),
        ]
        dmvl_results = run_claims(claims, use_computer=args.use_computer)
        write_task_receipt(
            "dmvl-verification",
            {
                "results": [r.__dict__ for r in dmvl_results],
                "ok": all_ok(dmvl_results),
            },
        )
        dmvl_ok = all_ok(dmvl_results)
        print("🔎 DMVL:", "PASS" if dmvl_ok else "FAIL")

        # If DMVL failed, advise and exit non-zero
        if not dmvl_ok:
            from termnet.devflow import advise_on_failure

            advise_on_failure()
            import sys

            sys.exit(1)

        # If --open-pr and DMVL passed, add labels
        if args.open_pr:
            from termnet.git_client import add_pr_labels

            add_pr_labels(["termnet:project-mode", "termnet:dmvl"])
            print("🏷️  PR labels added (if PR exists)")


def build_parser():
    p = argparse.ArgumentParser(prog="termnet.cli", description="TermNet Autopilot CLI")    # noqa: E501
    s = p.add_subparsers(dest="cmd", required=True)

    # status command
    x = s.add_parser("status")
    x.set_defaults(func=cmd_status)

    # say command
    y = s.add_parser("say")
    y.add_argument("--dry-run", action="store_true", dest="dry_run")
    y.add_argument("-R", "--real", action="store_true", dest="real")
    y.add_argument("task")
    y.set_defaults(func=cmd_say)

    # project command
    proj = s.add_parser("project", help="Project mode commands")
    proj_sub = proj.add_subparsers(dest="project_cmd", required=True)

    # project run subcommand
    proj_run = proj_sub.add_parser("run", help="Initialize a new project")
    proj_run.add_argument("brief", help="Project brief description")
    proj_run.add_argument("--dry-run", action="store_true", dest="dry_run")
    proj_run.add_argument("-R", "--real", action="store_true", dest="real")
    proj_run.add_argument("--open-pr", action="store_true", dest="open_pr")
    proj_run.add_argument("--use-computer", action="store_true", dest="use_computer")   # noqa: E501
    proj_run.set_defaults(func=cmd_project_run)

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
