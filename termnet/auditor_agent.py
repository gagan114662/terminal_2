"""
Auditor Agent - 7th BMAD Agent for Claims Verification
Continuously monitors and verifies all agent claims with evidence
"""

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

from termnet.claims_engine import Claim, ClaimsEngine, ClaimSeverity, ClaimStatus
from termnet.sandbox import SandboxManager
from termnet.validation_engine import ValidationEngine, ValidationStatus


class AuditSeverity(Enum):
    CRITICAL = "critical"  # System integrity issues
    HIGH = "high"  # False claims detected
    MEDIUM = "medium"  # Evidence inconsistencies
    LOW = "low"  # Minor discrepancies
    INFO = "info"  # Status updates


@dataclass
class AuditFinding:
    """A finding from the audit process"""

    id: str
    claim_id: str
    severity: AuditSeverity
    category: str  # "false_claim", "missing_evidence", "evidence_tampered", "success_token_mismatch"
    description: str
    details: dict[str, Any]
    recommendation: str
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.id:
            import hashlib

            content = f"{self.claim_id}:{self.category}:{self.created_at}"
            self.id = hashlib.md5(content.encode()).hexdigest()[:8]


class ClaimAuditor:
    """Core auditing logic for claims verification"""

    def __init__(
        self,
        claims_engine: ClaimsEngine,
        validation_engine: ValidationEngine | None = None,
    ):
        self.claims_engine = claims_engine
        self.validation_engine = validation_engine
        self.sandbox_manager = SandboxManager()

    async def audit_claim(self, claim: Claim) -> list[AuditFinding]:
        """Perform comprehensive audit of a single claim"""
        findings = []

        # 1. Evidence Integrity Check
        findings.extend(await self._audit_evidence_integrity(claim))

        # 2. Success Token Verification
        findings.extend(await self._audit_success_tokens(claim))

        # 3. Command Repeatability Test
        findings.extend(await self._audit_repeatability(claim))

        # 4. Cross-Reference Validation
        findings.extend(await self._audit_cross_references(claim))

        # 5. Timeline Consistency
        findings.extend(await self._audit_timeline_consistency(claim))

        return findings

    async def _audit_evidence_integrity(self, claim: Claim) -> list[AuditFinding]:
        """Verify that all evidence files exist and haven't been tampered with"""
        findings = []

        if not claim.evidence:
            findings.append(
                AuditFinding(
                    id="",
                    claim_id=claim.id,
                    severity=AuditSeverity.HIGH,
                    category="missing_evidence",
                    description=f"Claim '{claim.what}' has no supporting evidence",
                    details={"evidence_count": 0},
                    recommendation="Collect evidence before marking claim as verified",
                )
            )
            return findings

        for evidence in claim.evidence:
            evidence_path = Path(evidence.path)

            # Check file exists
            if not evidence_path.exists():
                findings.append(
                    AuditFinding(
                        id="",
                        claim_id=claim.id,
                        severity=AuditSeverity.CRITICAL,
                        category="evidence_tampered",
                        description=f"Evidence file missing: {evidence.path}",
                        details={
                            "evidence_path": evidence.path,
                            "evidence_type": evidence.type,
                        },
                        recommendation="Investigate evidence file deletion or relocation",
                    )
                )
                continue

            # Verify hash integrity
            try:
                current_hash = self.claims_engine.evidence_collector._hash_file(
                    evidence_path
                )
                if current_hash != evidence.hash:
                    findings.append(
                        AuditFinding(
                            id="",
                            claim_id=claim.id,
                            severity=AuditSeverity.CRITICAL,
                            category="evidence_tampered",
                            description=f"Evidence file modified: {evidence.path}",
                            details={
                                "expected_hash": evidence.hash,
                                "actual_hash": current_hash,
                                "evidence_type": evidence.type,
                            },
                            recommendation="Re-collect evidence or mark claim as unverified",
                        )
                    )
            except Exception as e:
                findings.append(
                    AuditFinding(
                        id="",
                        claim_id=claim.id,
                        severity=AuditSeverity.MEDIUM,
                        category="evidence_tampered",
                        description=f"Cannot verify evidence hash: {evidence.path}",
                        details={"error": str(e), "evidence_type": evidence.type},
                        recommendation="Investigate evidence file accessibility",
                    )
                )

        return findings

    async def _audit_success_tokens(self, claim: Claim) -> list[AuditFinding]:
        """Verify success tokens in command outputs match claimed results"""
        findings = []

        # Look for success tokens in evidence
        success_indicators = {
            "build": ["BUILD SUCCESSFUL", "completed successfully", "Done in"],
            "test": ["passed", "OK", "All tests passed", "✓"],
            "install": ["Successfully installed", "Package installed", "added"],
            "deployment": ["deployed successfully", "deployment complete", "live at"],
        }

        claim_lower = claim.what.lower()
        expected_tokens = []

        for category, tokens in success_indicators.items():
            if category in claim_lower:
                expected_tokens.extend(tokens)

        if expected_tokens:
            found_tokens = []
            for evidence in claim.evidence:
                if evidence.type in ["log", "output"]:
                    try:
                        with open(evidence.path) as f:
                            content = f.read()
                            for token in expected_tokens:
                                if token.lower() in content.lower():
                                    found_tokens.append(token)
                    except Exception:
                        continue

            if not found_tokens:
                findings.append(
                    AuditFinding(
                        id="",
                        claim_id=claim.id,
                        severity=AuditSeverity.HIGH,
                        category="success_token_mismatch",
                        description=f"No success tokens found for claim: {claim.what}",
                        details={
                            "expected_tokens": expected_tokens,
                            "found_tokens": found_tokens,
                        },
                        recommendation="Verify command actually completed successfully",
                    )
                )

        return findings

    async def _audit_repeatability(self, claim: Claim) -> list[AuditFinding]:
        """Test if claimed command can be repeated with same results"""
        findings = []

        # Only audit deterministic commands
        deterministic_commands = ["python -c", "echo", "cat", "ls", "pwd"]

        if not any(cmd in claim.command for cmd in deterministic_commands):
            return findings  # Skip non-deterministic commands

        if claim.severity == ClaimSeverity.CRITICAL:
            # For critical claims, attempt to repeat the command in sandbox
            try:
                result = await self.sandbox_manager.execute_command(
                    command=claim.command, working_directory="/tmp", timeout=30
                )

                if result.exit_code != 0:
                    findings.append(
                        AuditFinding(
                            id="",
                            claim_id=claim.id,
                            severity=AuditSeverity.HIGH,
                            category="false_claim",
                            description=f"Command fails when repeated: {claim.command}",
                            details={
                                "original_exit_code": 0,
                                "repeat_exit_code": result.exit_code,
                                "repeat_output": result.output[:500],
                            },
                            recommendation="Investigate why command cannot be repeated",
                        )
                    )

            except Exception as e:
                findings.append(
                    AuditFinding(
                        id="",
                        claim_id=claim.id,
                        severity=AuditSeverity.MEDIUM,
                        category="false_claim",
                        description=f"Cannot repeat command for verification: {claim.command}",
                        details={"error": str(e)},
                        recommendation="Manual verification required",
                    )
                )

        return findings

    async def _audit_cross_references(self, claim: Claim) -> list[AuditFinding]:
        """Cross-reference claim with other validation systems"""
        findings = []

        if self.validation_engine and claim.status == ClaimStatus.VERIFIED:
            try:
                # Check if validation engine has contradictory results
                validation_history = self.validation_engine.get_validation_history(
                    limit=50
                )

                for validation in validation_history:
                    if (
                        validation.get("command") == claim.command
                        and validation.get("status") == ValidationStatus.FAILED.value
                    ):
                        # Found contradictory validation result
                        findings.append(
                            AuditFinding(
                                id="",
                                claim_id=claim.id,
                                severity=AuditSeverity.HIGH,
                                category="false_claim",
                                description="Claim conflicts with validation system",
                                details={
                                    "validation_status": validation.get("status"),
                                    "validation_message": validation.get("message", ""),
                                    "validation_timestamp": validation.get("timestamp"),
                                },
                                recommendation="Reconcile claim with validation system results",
                            )
                        )

            except Exception:
                # Non-critical - just log for debugging
                pass

        return findings

    async def _audit_timeline_consistency(self, claim: Claim) -> list[AuditFinding]:
        """Check for timeline inconsistencies in evidence"""
        findings = []

        if len(claim.evidence) < 2:
            return findings

        # Parse timestamps and check chronological order
        timestamps = []
        for evidence in claim.evidence:
            try:
                ts = datetime.fromisoformat(evidence.created_at.replace("Z", "+00:00"))
                timestamps.append((evidence.path, ts))
            except:
                continue

        timestamps.sort(key=lambda x: x[1])

        # Check for evidence created before claim
        claim_time = datetime.fromisoformat(claim.created_at.replace("Z", "+00:00"))

        for evidence_path, evidence_time in timestamps:
            if evidence_time < claim_time - timedelta(seconds=60):  # 1 minute tolerance
                findings.append(
                    AuditFinding(
                        id="",
                        claim_id=claim.id,
                        severity=AuditSeverity.MEDIUM,
                        category="timeline_inconsistency",
                        description="Evidence predates claim by more than 1 minute",
                        details={
                            "evidence_path": evidence_path,
                            "evidence_time": evidence_time.isoformat(),
                            "claim_time": claim_time.isoformat(),
                        },
                        recommendation="Verify evidence collection timing",
                    )
                )

        return findings


class AuditorAgent:
    """7th BMAD Agent: Continuous claims auditing and verification"""

    def __init__(
        self,
        claims_engine: ClaimsEngine,
        validation_engine: ValidationEngine | None = None,
    ):
        self.claims_engine = claims_engine
        self.validation_engine = validation_engine
        self.auditor = ClaimAuditor(claims_engine, validation_engine)
        self.findings: list[AuditFinding] = []
        self.is_running = False
        self.audit_interval = 300  # 5 minutes
        self.last_audit = None

        # Initialize findings database
        self._init_findings_db()

    def _init_findings_db(self):
        """Initialize SQLite database for audit findings"""
        import sqlite3

        db_path = "termnet_audit_findings.db"
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_findings (
                    id TEXT PRIMARY KEY,
                    claim_id TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT NOT NULL,
                    details TEXT NOT NULL,
                    recommendation TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    resolved BOOLEAN DEFAULT FALSE
                )
            """
            )
            conn.commit()

    async def start_continuous_audit(self):
        """Start continuous auditing process"""
        self.is_running = True
        print("🕵️ Auditor Agent started - monitoring claims and evidence")

        while self.is_running:
            try:
                await self._perform_audit_cycle()
                await asyncio.sleep(self.audit_interval)
            except Exception as e:
                print(f"❌ Auditor Agent error: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    async def stop_continuous_audit(self):
        """Stop continuous auditing process"""
        self.is_running = False
        print("🛑 Auditor Agent stopped")

    async def _perform_audit_cycle(self):
        """Perform one complete audit cycle"""
        print("🔍 Starting audit cycle...")

        # Get recent claims to audit
        recent_claims = self.claims_engine.get_claims(limit=50)
        new_findings = []

        for claim in recent_claims:
            claim_findings = await self.auditor.audit_claim(claim)
            new_findings.extend(claim_findings)

        # Store new findings
        if new_findings:
            await self._store_findings(new_findings)
            self.findings.extend(new_findings)

            # Report critical findings immediately
            critical_findings = [
                f for f in new_findings if f.severity == AuditSeverity.CRITICAL
            ]
            if critical_findings:
                await self._report_critical_findings(critical_findings)

        self.last_audit = datetime.now()
        print(f"✅ Audit cycle completed - {len(new_findings)} new findings")

    async def _store_findings(self, findings: list[AuditFinding]):
        """Store findings in database"""
        import sqlite3

        db_path = "termnet_audit_findings.db"
        try:
            with sqlite3.connect(db_path) as conn:
                for finding in findings:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO audit_findings
                        (id, claim_id, severity, category, description, details, recommendation, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            finding.id,
                            finding.claim_id,
                            finding.severity.value,
                            finding.category,
                            finding.description,
                            json.dumps(finding.details),
                            finding.recommendation,
                            finding.created_at,
                        ),
                    )
                conn.commit()
        except Exception as e:
            print(f"❌ Failed to store audit findings: {e}")

    async def _report_critical_findings(self, findings: list[AuditFinding]):
        """Report critical findings immediately"""
        print(f"🚨 CRITICAL AUDIT FINDINGS ({len(findings)}):")
        for finding in findings:
            print(f"  • {finding.description}")
            print(f"    Recommendation: {finding.recommendation}")

            # Update claim status if evidence tampering detected
            if finding.category == "evidence_tampered":
                claim = next(
                    (
                        c
                        for c in self.claims_engine.get_claims()
                        if c.id == finding.claim_id
                    ),
                    None,
                )
                if claim:
                    claim.status = ClaimStatus.FAILED
                    claim.error_message = finding.description
                    print(f"    → Claim {finding.claim_id} marked as FAILED")

    def get_audit_summary(self) -> dict[str, Any]:
        """Get summary of audit status and findings"""

        # Count findings by severity and category
        severity_counts = {}
        category_counts = {}

        for finding in self.findings:
            severity_counts[finding.severity.value] = (
                severity_counts.get(finding.severity.value, 0) + 1
            )
            category_counts[finding.category] = (
                category_counts.get(finding.category, 0) + 1
            )

        return {
            "auditor_status": "running" if self.is_running else "stopped",
            "last_audit": self.last_audit.isoformat() if self.last_audit else None,
            "total_findings": len(self.findings),
            "severity_breakdown": severity_counts,
            "category_breakdown": category_counts,
            "audit_interval_minutes": self.audit_interval / 60,
            "findings_db": "termnet_audit_findings.db",
        }

    async def audit_specific_claim(self, claim_id: str) -> list[AuditFinding]:
        """Audit a specific claim on demand"""
        claims = self.claims_engine.get_claims()
        claim = next((c for c in claims if c.id == claim_id), None)

        if not claim:
            print(f"❌ Claim {claim_id} not found")
            return []

        print(f"🔍 Auditing claim: {claim.what}")
        findings = await self.auditor.audit_claim(claim)

        if findings:
            await self._store_findings(findings)
            print(f"📋 Found {len(findings)} audit findings")
            for finding in findings:
                print(f"  • [{finding.severity.value}] {finding.description}")
        else:
            print("✅ No issues found with claim")

        return findings

    def export_findings_report(
        self, output_path: str = "artifacts/audit_report.json"
    ) -> str:
        """Export comprehensive audit findings report"""

        # Group findings by category and severity
        report = {
            "generated_at": datetime.now().isoformat(),
            "audit_summary": self.get_audit_summary(),
            "findings_by_severity": {},
            "findings_by_category": {},
            "recommendations": [],
            "all_findings": [],
        }

        for finding in self.findings:
            # Group by severity
            if finding.severity.value not in report["findings_by_severity"]:
                report["findings_by_severity"][finding.severity.value] = []
            report["findings_by_severity"][finding.severity.value].append(
                {
                    "id": finding.id,
                    "claim_id": finding.claim_id,
                    "description": finding.description,
                    "recommendation": finding.recommendation,
                }
            )

            # Group by category
            if finding.category not in report["findings_by_category"]:
                report["findings_by_category"][finding.category] = []
            report["findings_by_category"][finding.category].append(
                {
                    "id": finding.id,
                    "claim_id": finding.claim_id,
                    "severity": finding.severity.value,
                    "description": finding.description,
                }
            )

            # Collect unique recommendations
            if finding.recommendation not in report["recommendations"]:
                report["recommendations"].append(finding.recommendation)

            # Add to all findings
            report["all_findings"].append(
                {
                    "id": finding.id,
                    "claim_id": finding.claim_id,
                    "severity": finding.severity.value,
                    "category": finding.category,
                    "description": finding.description,
                    "details": finding.details,
                    "recommendation": finding.recommendation,
                    "created_at": finding.created_at,
                }
            )

        # Write report
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)

        print(f"📄 Audit report exported to {output_path}")
        return output_path
