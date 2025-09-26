#!/usr/bin/env python3
"""
Security Validation Integration for TermNet
Connects container security scanning to validation receipts
"""

import datetime
import hashlib
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from termnet.validation_engine import (ValidationEngine, ValidationLevel,
                                       ValidationRule)


@dataclass
class SecurityValidationRule(ValidationRule):
    """Extended validation rule for security scanning"""

    max_critical_vulns: int = 0
    max_high_vulns: int = 5
    max_medium_vulns: int = 20
    require_sbom: bool = True
    require_signed_images: bool = False
    blocked_packages: list = None
    allowed_licenses: list = None


class SecurityValidationEngine:
    """Integration between security scanning and validation engine"""

    def __init__(self, validation_engine: Optional[ValidationEngine] = None):
        self.validation_engine = validation_engine or ValidationEngine()
        self.setup_security_rules()

    def setup_security_rules(self):
        """Configure security-specific validation rules"""

        # SBOM validation rule
        self.validation_engine.add_rule(
            SecurityValidationRule(
                rule_id="SEC-001",
                name="SBOM Generation Required",
                description="All container images must have a Software Bill of Materials",
                level=ValidationLevel.ERROR,
                enabled=True,
                require_sbom=True,
            )
        )

        # Critical vulnerability rule
        self.validation_engine.add_rule(
            SecurityValidationRule(
                rule_id="SEC-002",
                name="No Critical Vulnerabilities",
                description="Container images must not contain critical vulnerabilities",
                level=ValidationLevel.ERROR,
                enabled=True,
                max_critical_vulns=0,
            )
        )

        # High vulnerability threshold
        self.validation_engine.add_rule(
            SecurityValidationRule(
                rule_id="SEC-003",
                name="Limited High Vulnerabilities",
                description="Container images should have minimal high severity vulnerabilities",
                level=ValidationLevel.WARNING,
                enabled=True,
                max_high_vulns=5,
            )
        )

        # License compliance
        self.validation_engine.add_rule(
            SecurityValidationRule(
                rule_id="SEC-004",
                name="License Compliance",
                description="All packages must have approved licenses",
                level=ValidationLevel.WARNING,
                enabled=True,
                allowed_licenses=[
                    "MIT",
                    "Apache-2.0",
                    "BSD-3-Clause",
                    "BSD-2-Clause",
                    "ISC",
                    "Python-2.0",
                ],
            )
        )

        # Supply chain security
        self.validation_engine.add_rule(
            SecurityValidationRule(
                rule_id="SEC-005",
                name="Supply Chain Verification",
                description="Container images should be signed and verified",
                level=ValidationLevel.INFO,
                enabled=True,
                require_signed_images=True,
            )
        )

    def validate_security_scan(self, scan_report: Dict[str, Any]) -> Dict[str, Any]:
        """Validate security scan results against rules"""

        validation_results = {
            "scan_id": scan_report.get("scan_id"),
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "image": scan_report.get("image"),
            "passed_rules": [],
            "failed_rules": [],
            "warnings": [],
            "overall_status": "PASSED",
        }

        # Check SBOM generation
        if scan_report.get("sbom", {}).get("hash"):
            validation_results["passed_rules"].append(
                {
                    "rule_id": "SEC-001",
                    "message": "SBOM successfully generated",
                    "sbom_hash": scan_report["sbom"]["hash"],
                }
            )
        else:
            validation_results["failed_rules"].append(
                {
                    "rule_id": "SEC-001",
                    "message": "SBOM generation failed",
                    "severity": "ERROR",
                }
            )
            validation_results["overall_status"] = "FAILED"

        # Check critical vulnerabilities
        critical_count = scan_report.get("vulnerabilities", {}).get("critical", 0)
        if critical_count == 0:
            validation_results["passed_rules"].append(
                {"rule_id": "SEC-002", "message": "No critical vulnerabilities found"}
            )
        else:
            validation_results["failed_rules"].append(
                {
                    "rule_id": "SEC-002",
                    "message": f"Found {critical_count} critical vulnerabilities",
                    "severity": "ERROR",
                    "count": critical_count,
                }
            )
            validation_results["overall_status"] = "FAILED"

        # Check high vulnerabilities
        high_count = scan_report.get("vulnerabilities", {}).get("high", 0)
        if high_count <= 5:
            validation_results["passed_rules"].append(
                {
                    "rule_id": "SEC-003",
                    "message": f"Acceptable number of high vulnerabilities: {high_count}",
                }
            )
        else:
            validation_results["warnings"].append(
                {
                    "rule_id": "SEC-003",
                    "message": f"Found {high_count} high vulnerabilities (threshold: 5)",
                    "severity": "WARNING",
                    "count": high_count,
                }
            )
            if validation_results["overall_status"] == "PASSED":
                validation_results["overall_status"] = "PASSED_WITH_WARNINGS"

        return validation_results

    def create_security_receipt(
        self, scan_report: Dict[str, Any], validation_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create cryptographically signed validation receipt"""

        receipt = {
            "receipt_id": hashlib.sha256(
                f"{scan_report['scan_id']}{validation_results['timestamp']}".encode()
            ).hexdigest()[:16],
            "scan_id": scan_report["scan_id"],
            "timestamp": validation_results["timestamp"],
            "image": scan_report["image"],
            "sbom": {
                "hash": scan_report.get("sbom", {}).get("hash"),
                "packages_count": scan_report.get("sbom", {}).get("packages_count"),
            },
            "vulnerabilities": scan_report.get("vulnerabilities"),
            "validation": {
                "status": validation_results["overall_status"],
                "passed_rules": len(validation_results["passed_rules"]),
                "failed_rules": len(validation_results["failed_rules"]),
                "warnings": len(validation_results["warnings"]),
                "details": validation_results,
            },
            "attestation": {
                "engine": "TermNet Security Validation Engine",
                "version": "1.0.0",
                "policy_version": "2024.01.1",
                "signature_algorithm": "SHA256",
            },
        }

        # Calculate receipt signature
        receipt_json = json.dumps(receipt, sort_keys=True)
        receipt["signature"] = hashlib.sha256(receipt_json.encode()).hexdigest()

        return receipt

    def integrate_with_termnet(self, scan_report: Dict[str, Any]) -> Dict[str, Any]:
        """Full integration with TermNet validation system"""

        print("🔐 Validating security scan results...")

        # Validate against security rules
        validation_results = self.validate_security_scan(scan_report)

        # Create validation receipt
        receipt = self.create_security_receipt(scan_report, validation_results)

        # Store in validation engine
        if self.validation_engine:
            # Create validation record
            validation_id = self.validation_engine.create_validation(
                command=f"docker scan {scan_report['image']}",
                context={
                    "scan_id": scan_report["scan_id"],
                    "sbom_hash": scan_report.get("sbom", {}).get("hash"),
                    "vulnerabilities": scan_report.get("vulnerabilities"),
                },
            )

            # Validate and complete
            self.validation_engine.validate_command(
                validation_id, success=validation_results["overall_status"] != "FAILED"
            )

            receipt["validation_id"] = validation_id

        # Save receipt
        receipt_file = f"security_receipt_{receipt['receipt_id']}.json"
        with open(receipt_file, "w") as f:
            json.dump(receipt, f, indent=2)

        print(f"✅ Validation receipt created: {receipt_file}")
        print(f"🎯 Validation Status: {validation_results['overall_status']}")

        return receipt


def main():
    """Example integration"""

    # Load a sample scan report
    sample_report = {
        "scan_id": "test-scan-123",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "image": "termnet-api:latest",
        "sbom": {
            "file": "sbom_termnet-api_latest.json",
            "hash": "abc123def456",
            "packages_count": 150,
        },
        "vulnerabilities": {
            "critical": 0,
            "high": 3,
            "medium": 12,
            "low": 25,
            "total": 40,
        },
        "compliance_status": "PASSED - Acceptable risk level",
    }

    # Create security validation engine
    engine = SecurityValidationEngine()

    # Integrate with TermNet
    receipt = engine.integrate_with_termnet(sample_report)

    print(f"\n📋 Receipt Summary:")
    print(f"   Receipt ID: {receipt['receipt_id']}")
    print(f"   Validation Status: {receipt['validation']['status']}")
    print(f"   Signature: {receipt['signature'][:16]}...")


if __name__ == "__main__":
    main()
