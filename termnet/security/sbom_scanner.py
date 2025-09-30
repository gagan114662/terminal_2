#!/usr/bin/env python3
"""
SBOM Generation and Security Scanning Integration
Integrates Syft for SBOM generation and Trivy/Grype for vulnerability scanning
"""

import datetime
import hashlib
import json
import os
import sqlite3
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class SBOMEntry:
    """Software Bill of Materials entry"""

    name: str
    version: str
    type: str
    purl: str  # Package URL
    licenses: List[str]
    cpe: Optional[str] = None


@dataclass
class VulnerabilityReport:
    """Security vulnerability report"""

    vulnerability_id: str
    package: str
    severity: str
    fixed_version: Optional[str]
    description: str
    cvss_score: Optional[float]


@dataclass
class SecurityReceipt:
    """Validation receipt for security scanning"""

    scan_id: str
    timestamp: str
    image_digest: str
    sbom_hash: str
    vulnerabilities_critical: int
    vulnerabilities_high: int
    vulnerabilities_medium: int
    vulnerabilities_low: int
    compliance_status: str
    scanner_versions: Dict[str, str]


class ContainerSecurityScanner:
    """Comprehensive container security scanning with SBOM generation"""

    def __init__(self, db_path: str = "termnet_security.db"):
        self.db_path = db_path
        self.setup_database()

    def setup_database(self):
        """Initialize security scanning database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # SBOM storage
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sbom_entries (
                id INTEGER PRIMARY KEY,
                scan_id TEXT,
                name TEXT,
                version TEXT,
                type TEXT,
                purl TEXT,
                licenses TEXT,
                cpe TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Vulnerability findings
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS vulnerabilities (
                id INTEGER PRIMARY KEY,
                scan_id TEXT,
                vulnerability_id TEXT,
                package TEXT,
                severity TEXT,
                fixed_version TEXT,
                description TEXT,
                cvss_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Security receipts
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS security_receipts (
                id INTEGER PRIMARY KEY,
                scan_id TEXT UNIQUE,
                timestamp TEXT,
                image_digest TEXT,
                sbom_hash TEXT,
                vulnerabilities_critical INTEGER,
                vulnerabilities_high INTEGER,
                vulnerabilities_medium INTEGER,
                vulnerabilities_low INTEGER,
                compliance_status TEXT,
                scanner_versions TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        conn.commit()
        conn.close()

    def generate_sbom_syft(
        self, image_name: str, output_format: str = "spdx-json"
    ) -> Dict[str, Any]:
        """Generate SBOM using Syft"""
        try:
            # Generate SBOM
            output_file = f"sbom_{image_name.replace('/', '_').replace(':', '_')}.json"
            cmd = ["syft", image_name, "-o", output_format, "--file", output_file]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                raise Exception(f"Syft error: {result.stderr}")

            # Parse SBOM
            with open(output_file, "r") as f:
                sbom_data = json.load(f)

            # Calculate SBOM hash
            with open(output_file, "rb") as f:
                sbom_hash = hashlib.sha256(f.read()).hexdigest()

            return {
                "sbom_file": output_file,
                "sbom_hash": sbom_hash,
                "packages_count": len(sbom_data.get("packages", [])),
                "sbom_data": sbom_data,
            }

        except FileNotFoundError:
            return {
                "error": "Syft not installed. Install with: curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin",
                "sbom_file": None,
                "sbom_hash": None,
            }
        except Exception as e:
            return {"error": str(e), "sbom_file": None, "sbom_hash": None}

    def scan_with_trivy(self, image_name: str) -> Dict[str, Any]:
        """Scan container with Trivy"""
        try:
            cmd = [
                "trivy",
                "image",
                "--format",
                "json",
                "--severity",
                "CRITICAL,HIGH,MEDIUM,LOW",
                image_name,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if (
                result.returncode != 0
                and "no vulnerabilities" not in result.stderr.lower()
            ):
                raise Exception(f"Trivy error: {result.stderr}")

            scan_results = (
                json.loads(result.stdout) if result.stdout else {"Results": []}
            )

            # Parse vulnerabilities
            vulnerabilities = []
            severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}

            for target in scan_results.get("Results", []):
                for vuln in target.get("Vulnerabilities", []):
                    vulnerabilities.append(
                        VulnerabilityReport(
                            vulnerability_id=vuln.get("VulnerabilityID", ""),
                            package=vuln.get("PkgName", ""),
                            severity=vuln.get("Severity", "UNKNOWN"),
                            fixed_version=vuln.get("FixedVersion"),
                            description=vuln.get("Description", "")[:500],
                            cvss_score=vuln.get("CVSS", {})
                            .get("nvd", {})
                            .get("V3Score"),
                        )
                    )

                    if vuln.get("Severity") in severity_counts:
                        severity_counts[vuln["Severity"]] += 1

            return {
                "scanner": "trivy",
                "vulnerabilities": vulnerabilities,
                "severity_counts": severity_counts,
                "total_vulnerabilities": len(vulnerabilities),
            }

        except FileNotFoundError:
            return {
                "error": "Trivy not installed. Install with: curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin",
                "vulnerabilities": [],
                "severity_counts": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0},
            }
        except Exception as e:
            return {
                "error": str(e),
                "vulnerabilities": [],
                "severity_counts": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0},
            }

    def scan_with_grype(self, image_name: str) -> Dict[str, Any]:
        """Scan container with Grype"""
        try:
            cmd = ["grype", image_name, "-o", "json"]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if (
                result.returncode != 0
                and "no vulnerabilities" not in result.stderr.lower()
            ):
                raise Exception(f"Grype error: {result.stderr}")

            scan_results = (
                json.loads(result.stdout) if result.stdout else {"matches": []}
            )

            # Parse vulnerabilities
            vulnerabilities = []
            severity_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}

            for match in scan_results.get("matches", []):
                vuln = match.get("vulnerability", {})
                vulnerabilities.append(
                    VulnerabilityReport(
                        vulnerability_id=vuln.get("id", ""),
                        package=match.get("artifact", {}).get("name", ""),
                        severity=vuln.get("severity", "Unknown"),
                        fixed_version=vuln.get("fix", {}).get("versions", [""])[0]
                        if vuln.get("fix")
                        else None,
                        description=vuln.get("description", "")[:500],
                        cvss_score=None,  # Grype doesn't always provide CVSS
                    )
                )

                severity = vuln.get("severity", "").capitalize()
                if severity in severity_counts:
                    severity_counts[severity] += 1

            return {
                "scanner": "grype",
                "vulnerabilities": vulnerabilities,
                "severity_counts": severity_counts,
                "total_vulnerabilities": len(vulnerabilities),
            }

        except FileNotFoundError:
            return {
                "error": "Grype not installed. Install with: curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin",
                "vulnerabilities": [],
                "severity_counts": {"Critical": 0, "High": 0, "Medium": 0, "Low": 0},
            }
        except Exception as e:
            return {
                "error": str(e),
                "vulnerabilities": [],
                "severity_counts": {"Critical": 0, "High": 0, "Medium": 0, "Low": 0},
            }

    def create_validation_receipt(
        self,
        scan_id: str,
        image_name: str,
        sbom_result: Dict,
        trivy_result: Dict,
        grype_result: Dict,
    ) -> SecurityReceipt:
        """Create validation receipt for security scan"""

        # Determine compliance status
        critical_count = trivy_result["severity_counts"].get(
            "CRITICAL", 0
        ) + grype_result["severity_counts"].get("Critical", 0)
        high_count = trivy_result["severity_counts"].get("HIGH", 0) + grype_result[
            "severity_counts"
        ].get("High", 0)

        if critical_count > 0:
            compliance_status = "FAILED - Critical vulnerabilities found"
        elif high_count > 5:
            compliance_status = "WARNING - Multiple high severity vulnerabilities"
        else:
            compliance_status = "PASSED - Acceptable risk level"

        receipt = SecurityReceipt(
            scan_id=scan_id,
            timestamp=datetime.datetime.utcnow().isoformat(),
            image_digest=image_name,
            sbom_hash=sbom_result.get("sbom_hash", ""),
            vulnerabilities_critical=trivy_result["severity_counts"].get("CRITICAL", 0),
            vulnerabilities_high=trivy_result["severity_counts"].get("HIGH", 0),
            vulnerabilities_medium=trivy_result["severity_counts"].get("MEDIUM", 0),
            vulnerabilities_low=trivy_result["severity_counts"].get("LOW", 0),
            compliance_status=compliance_status,
            scanner_versions={
                "syft": self.get_tool_version("syft"),
                "trivy": self.get_tool_version("trivy"),
                "grype": self.get_tool_version("grype"),
            },
        )

        return receipt

    def get_tool_version(self, tool_name: str) -> str:
        """Get version of security scanning tool"""
        try:
            cmd = [tool_name, "version"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.stdout.split("\n")[0] if result.returncode == 0 else "unknown"
        except:
            return "not installed"

    def scan_container(self, image_name: str) -> Dict[str, Any]:
        """Comprehensive container security scan with SBOM generation"""
        import uuid

        scan_id = str(uuid.uuid4())

        print(f"🔍 Starting security scan for {image_name}")
        print(f"📋 Scan ID: {scan_id}")

        # Generate SBOM
        print("📦 Generating SBOM with Syft...")
        sbom_result = self.generate_sbom_syft(image_name)

        # Scan with Trivy
        print("🛡️ Scanning with Trivy...")
        trivy_result = self.scan_with_trivy(image_name)

        # Scan with Grype
        print("🔒 Scanning with Grype...")
        grype_result = self.scan_with_grype(image_name)

        # Create validation receipt
        receipt = self.create_validation_receipt(
            scan_id, image_name, sbom_result, trivy_result, grype_result
        )

        # Store in database
        self.store_scan_results(
            scan_id, sbom_result, trivy_result, grype_result, receipt
        )

        # Generate report
        report = {
            "scan_id": scan_id,
            "timestamp": receipt.timestamp,
            "image": image_name,
            "sbom": {
                "file": sbom_result.get("sbom_file"),
                "hash": sbom_result.get("sbom_hash"),
                "packages_count": sbom_result.get("packages_count", 0),
            },
            "vulnerabilities": {
                "critical": receipt.vulnerabilities_critical,
                "high": receipt.vulnerabilities_high,
                "medium": receipt.vulnerabilities_medium,
                "low": receipt.vulnerabilities_low,
                "total": sum(
                    [
                        receipt.vulnerabilities_critical,
                        receipt.vulnerabilities_high,
                        receipt.vulnerabilities_medium,
                        receipt.vulnerabilities_low,
                    ]
                ),
            },
            "compliance_status": receipt.compliance_status,
            "validation_receipt": asdict(receipt),
        }

        # Save report to file
        report_file = f"security_report_{scan_id}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\n✅ Security scan complete!")
        print(f"📊 Report saved to: {report_file}")
        print(f"🎯 Compliance Status: {receipt.compliance_status}")

        return report

    def store_scan_results(
        self,
        scan_id: str,
        sbom_result: Dict,
        trivy_result: Dict,
        grype_result: Dict,
        receipt: SecurityReceipt,
    ):
        """Store scan results in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Store SBOM entries (simplified for demo)
        if sbom_result.get("sbom_data"):
            for pkg in sbom_result["sbom_data"].get("packages", [])[
                :100
            ]:  # Limit for demo
                cursor.execute(
                    """
                    INSERT INTO sbom_entries
                    (scan_id, name, version, type, purl, licenses, cpe)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        scan_id,
                        pkg.get("name", ""),
                        pkg.get("version", ""),
                        pkg.get("type", ""),
                        pkg.get("purl", ""),
                        json.dumps(pkg.get("licenses", [])),
                        pkg.get("cpe", ""),
                    ),
                )

        # Store vulnerabilities
        all_vulns = trivy_result.get("vulnerabilities", []) + grype_result.get(
            "vulnerabilities", []
        )
        for vuln in all_vulns[:500]:  # Limit for demo
            cursor.execute(
                """
                INSERT INTO vulnerabilities
                (scan_id, vulnerability_id, package, severity, fixed_version, description, cvss_score)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    scan_id,
                    vuln.vulnerability_id,
                    vuln.package,
                    vuln.severity,
                    vuln.fixed_version,
                    vuln.description,
                    vuln.cvss_score,
                ),
            )

        # Store security receipt
        cursor.execute(
            """
            INSERT INTO security_receipts
            (scan_id, timestamp, image_digest, sbom_hash, vulnerabilities_critical,
             vulnerabilities_high, vulnerabilities_medium, vulnerabilities_low,
             compliance_status, scanner_versions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                receipt.scan_id,
                receipt.timestamp,
                receipt.image_digest,
                receipt.sbom_hash,
                receipt.vulnerabilities_critical,
                receipt.vulnerabilities_high,
                receipt.vulnerabilities_medium,
                receipt.vulnerabilities_low,
                receipt.compliance_status,
                json.dumps(receipt.scanner_versions),
            ),
        )

        conn.commit()
        conn.close()


if __name__ == "__main__":
    # Example usage
    scanner = ContainerSecurityScanner()

    # Build Docker image first
    print("🐳 Building Docker image...")
    subprocess.run(["docker", "build", "-t", "termnet-api:latest", "."])

    # Scan the image
    report = scanner.scan_container("termnet-api:latest")

    print(f"\n📈 Vulnerability Summary:")
    print(f"   Critical: {report['vulnerabilities']['critical']}")
    print(f"   High: {report['vulnerabilities']['high']}")
    print(f"   Medium: {report['vulnerabilities']['medium']}")
    print(f"   Low: {report['vulnerabilities']['low']}")
    print(f"   Total: {report['vulnerabilities']['total']}")
