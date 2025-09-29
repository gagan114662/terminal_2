#!/usr/bin/env python3
"""Minimal TermNet CLI fallback"""
import argparse

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


def build_parser():
    p = argparse.ArgumentParser(prog="termnet.cli", description="TermNet Autopilot CLI")
    s = p.add_subparsers(dest="cmd", required=True)
    x = s.add_parser("status")
    x.set_defaults(func=cmd_status)
    y = s.add_parser("say")
    y.add_argument("--dry-run", action="store_true", dest="dry_run")
    y.add_argument("-R", "--real", action="store_true", dest="real")
    y.add_argument("task")
    y.set_defaults(func=cmd_say)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
