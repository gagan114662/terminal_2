#!/usr/bin/env python3
"""Verify and inspect receipt files."""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Verify receipt files")
    parser.add_argument(
        "--latest", action="store_true", help="Show latest receipts only"
    )
    parser.add_argument("--path", default=".termnet/receipts", help="Receipts directory")
    args = parser.parse_args()

    receipts_dir = Path(args.path)
    if not receipts_dir.exists():
        print(f"❌ Receipts directory not found: {receipts_dir}")
        return 1

    receipt_files = sorted(receipts_dir.glob("receipt_*.json"), key=lambda p: p.stat().st_mtime)

    if not receipt_files:
        print("No receipts found")
        return 0

    if args.latest:
        receipt_files = receipt_files[-5:]

    print(f"📋 Found {len(receipt_files)} receipts:\n")

    for receipt_file in receipt_files:
        print(f"  {receipt_file.name}")
        try:
            with open(receipt_file) as f:
                data = json.load(f)
                if isinstance(data, dict):
                    if "ok" in data:
                        status = "✅ PASS" if data["ok"] else "❌ FAIL"
                        print(f"    Status: {status}")
                    if "results" in data and isinstance(data["results"], list):
                        print(f"    Results: {len(data['results'])} claims")
        except Exception as e:
            print(f"    ⚠️  Error reading: {e}")
        print()

    return 0


if __name__ == "__main__":
    exit(main())