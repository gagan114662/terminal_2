#!/usr/bin/env python3
"""
Receipts verification system for TermNet autonomous operations.
Truth engine that validates autopilot execution integrity.
"""

import hashlib
import json
import os
import sys
# from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class ReceiptVerifier:
    """Verifies autopilot execution receipts for autonomous operations."""

    def __init__(self, receipts_dir: str = ".termnet/receipts"):
        self.receipts_dir = Path(receipts_dir)
        self.receipts_dir.mkdir(parents=True, exist_ok=True)

    def verify_receipt(self, receipt_path: str) -> Dict:
        """Verify a single receipt file."""
        try:
            with open(receipt_path, "r") as f:
                receipt = json.load(f)

            # Required fields validation
            required_fields = [
                "timestamp",
                "task",
                "mode",
                "result",
                "hash",
                "files_changed",
            ]
            missing_fields = [f for f in required_fields if f not in receipt]
            if missing_fields:
                return {
                    "valid": False,
                    "error": f"Missing required fields: {missing_fields}",
                    "receipt_path": receipt_path,
                }

            # Hash verification
            computed_hash = self._compute_receipt_hash(receipt)
            if computed_hash != receipt["hash"]:
                return {
                    "valid": False,
                    "error": f'Hash mismatch: expected {receipt["hash"]}, got {computed_hash}',
                    "receipt_path": receipt_path,
                }

            # Mode validation
            if receipt["mode"] not in ["dry-run", "real"]:
                return {
                    "valid": False,
                    "error": f'Invalid mode: {receipt["mode"]}',
                    "receipt_path": receipt_path,
                }

            # Result validation
            if receipt["result"] not in ["success", "failure", "planning-only"]:
                return {
                    "valid": False,
                    "error": f'Invalid result: {receipt["result"]}',
                    "receipt_path": receipt_path,
                }

            # Files validation for real runs
            if receipt["mode"] == "real" and receipt["result"] == "success":
                files_exist = self._verify_files_exist(receipt["files_changed"])
                if not files_exist["all_exist"]:
                    return {
                        "valid": False,
                        "error": f'Missing files: {files_exist["missing"]}',
                        "receipt_path": receipt_path,
                    }

            return {
                "valid": True,
                "task": receipt["task"],
                "mode": receipt["mode"],
                "result": receipt["result"],
                "timestamp": receipt["timestamp"],
                "files_changed": receipt["files_changed"],
                "receipt_path": receipt_path,
            }

        except Exception as e:
            return {
                "valid": False,
                "error": f"Failed to parse receipt: {str(e)}",
                "receipt_path": receipt_path,
            }

    def _compute_receipt_hash(self, receipt: Dict) -> str:
        """Compute SHA256 hash of receipt (excluding the hash field)."""
        receipt_copy = receipt.copy()
        receipt_copy.pop("hash", None)  # Remove hash field for computation

        # Create deterministic string representation
        receipt_str = json.dumps(receipt_copy, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(receipt_str.encode("utf-8")).hexdigest()

    def _verify_files_exist(self, files: List[str]) -> Dict:
        """Check if all specified files exist."""
        missing = []
        for file_path in files:
            if not os.path.exists(file_path):
                missing.append(file_path)

        return {"all_exist": len(missing) == 0, "missing": missing}

    def verify_all_receipts(self) -> Dict:
        """Verify all receipts in the receipts directory."""
        receipt_files = list(self.receipts_dir.glob("*.json"))

        if not receipt_files:
            return {
                "total": 0,
                "valid": 0,
                "invalid": 0,
                "results": [],
                "summary": "No receipts found",
            }

        results = []
        valid_count = 0

        for receipt_file in sorted(receipt_files):
            result = self.verify_receipt(str(receipt_file))
            results.append(result)
            if result["valid"]:
                valid_count += 1

        return {
            "total": len(receipt_files),
            "valid": valid_count,
            "invalid": len(receipt_files) - valid_count,
            "results": results,
            "summary": f"{valid_count}/{len(receipt_files)} receipts valid",
        }

    def get_latest_receipt(self) -> Optional[Dict]:
        """Get the most recent valid receipt."""
        verification = self.verify_all_receipts()

        valid_receipts = [r for r in verification["results"] if r["valid"]]
        if not valid_receipts:
            return None

        # Sort by timestamp and return latest
        valid_receipts.sort(key=lambda x: x["timestamp"], reverse=True)
        return valid_receipts[0]


def main():
    """CLI interface for receipt verification."""
    import argparse

    parser = argparse.ArgumentParser(description="Verify TermNet autopilot receipts")
    parser.add_argument(
        "--receipts-dir",
        default=".termnet/receipts",
        help="Directory containing receipt files",
    )
    parser.add_argument("--receipt", help="Verify specific receipt file")
    parser.add_argument(
        "--latest", action="store_true", help="Show latest valid receipt"
    )
    parser.add_argument(
        "--summary", action="store_true", help="Show verification summary"
    )

    args = parser.parse_args()

    verifier = ReceiptVerifier(args.receipts_dir)

    if args.receipt:
        # Verify specific receipt
        result = verifier.verify_receipt(args.receipt)
        print(json.dumps(result, indent=2))
        sys.exit(0 if result["valid"] else 1)

    elif args.latest:
        # Show latest valid receipt
        latest = verifier.get_latest_receipt()
        if latest:
            print(json.dumps(latest, indent=2))
        else:
            print("No valid receipts found")
            sys.exit(1)

    else:
        # Verify all receipts
        verification = verifier.verify_all_receipts()

        if args.summary:
            print(f"📋 {verification['summary']}")
            if verification["invalid"] > 0:
                print(f"❌ {verification['invalid']} invalid receipts")
                for result in verification["results"]:
                    if not result["valid"]:
                        print(f"   {result['receipt_path']}: {result['error']}")
            sys.exit(0 if verification["invalid"] == 0 else 1)
        else:
            print(json.dumps(verification, indent=2))
            sys.exit(0 if verification["invalid"] == 0 else 1)


if __name__ == "__main__":
    main()
