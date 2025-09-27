"""
Claims Engine - Track all agent assertions with verifiable evidence
Phase 3 of TermNet validation system: "No False Claims"
"""

import hashlib
import json
import sqlite3
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class ClaimStatus(Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    FAILED = "failed"
    EVIDENCE_MISSING = "evidence_missing"


class ClaimSeverity(Enum):
    CRITICAL = "critical"  # Build/deploy claims
    HIGH = "high"  # Test/feature claims
    MEDIUM = "medium"  # Performance/quality claims
    LOW = "low"  # Documentation/style claims
    INFO = "info"  # Status/progress claims


@dataclass
class Evidence:
    """Evidence artifact for a claim"""

    path: str
    type: str  # "log", "screenshot", "artifact", "transcript", "output"
    hash: str
    size: int
    created_at: str
    description: Optional[str] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class Claim:
    """A claim made by an agent with evidence"""

    id: str
    what: str  # What was claimed
    agent: str  # Which agent made the claim
    command: str  # Command that was executed
    status: ClaimStatus
    severity: ClaimSeverity
    evidence: List[Evidence]
    verifier: Optional[str] = None  # Tool/script that verified
    error_message: Optional[str] = None
    created_at: str = ""
    verified_at: Optional[str] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.id:
            self.id = self._generate_id()

    def _generate_id(self) -> str:
        """Generate unique claim ID"""
        content = f"{self.what}:{self.agent}:{self.command}:{self.created_at}"
        return hashlib.md5(content.encode()).hexdigest()[:12]


class EvidenceCollector:
    """Collects and manages evidence artifacts"""

    def __init__(self, base_path: str = "artifacts"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)

        # Create subdirectories
        (self.base_path / "logs").mkdir(exist_ok=True)
        (self.base_path / "transcripts").mkdir(exist_ok=True)
        (self.base_path / "evidence").mkdir(exist_ok=True)
        (self.base_path / "screenshots").mkdir(exist_ok=True)

    def collect_file(
        self,
        file_path: str,
        evidence_type: str = "artifact",
        description: Optional[str] = None,
    ) -> Evidence:
        """Collect a file as evidence"""
        source_path = Path(file_path)
        if not source_path.exists():
            raise FileNotFoundError(f"Evidence file not found: {file_path}")

        # Calculate hash
        file_hash = self._hash_file(source_path)
        file_size = source_path.stat().st_size

        # Copy to evidence directory with timestamp
        timestamp = int(time.time())
        evidence_name = f"{timestamp}_{source_path.name}"
        evidence_path = self.base_path / "evidence" / evidence_name

        # Copy file
        import shutil

        shutil.copy2(source_path, evidence_path)

        return Evidence(
            path=str(evidence_path),
            type=evidence_type,
            hash=file_hash,
            size=file_size,
            created_at=datetime.now().isoformat(),
            description=description,
        )

    def collect_command_output(
        self,
        command: str,
        output: str,
        exit_code: int,
        description: Optional[str] = None,
    ) -> Evidence:
        """Collect command output as evidence"""
        timestamp = int(time.time())
        log_file = self.base_path / "logs" / f"{timestamp}_command.log"

        # Write structured log
        log_data = {
            "command": command,
            "output": output,
            "exit_code": exit_code,
            "timestamp": datetime.now().isoformat(),
            "description": description,
        }

        with open(log_file, "w") as f:
            json.dump(log_data, f, indent=2)

        file_hash = self._hash_file(log_file)

        return Evidence(
            path=str(log_file),
            type="log",
            hash=file_hash,
            size=log_file.stat().st_size,
            created_at=log_data["timestamp"],
            description=f"Command: {command}",
        )

    def collect_transcript(
        self, transcript_content: str, description: Optional[str] = None
    ) -> Evidence:
        """Collect terminal transcript as evidence"""
        timestamp = int(time.time())
        transcript_file = self.base_path / "transcripts" / f"{timestamp}_session.txt"

        with open(transcript_file, "w") as f:
            f.write(transcript_content)

        file_hash = self._hash_file(transcript_file)

        return Evidence(
            path=str(transcript_file),
            type="transcript",
            hash=file_hash,
            size=transcript_file.stat().st_size,
            created_at=datetime.now().isoformat(),
            description=description or "Terminal transcript",
        )

    def collect_test_results(
        self, results_data: Dict[str, Any], description: Optional[str] = None
    ) -> Evidence:
        """Collect test results as evidence"""
        timestamp = int(time.time())
        results_file = self.base_path / "logs" / f"{timestamp}_tests.json"

        with open(results_file, "w") as f:
            json.dump(results_data, f, indent=2)

        file_hash = self._hash_file(results_file)

        return Evidence(
            path=str(results_file),
            type="test_results",
            hash=file_hash,
            size=results_file.stat().st_size,
            created_at=datetime.now().isoformat(),
            description=description or "Test results",
        )

    def _hash_file(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()


class ClaimsEngine:
    """Main claims tracking and verification engine"""

    def __init__(self, db_path: str = "termnet_claims.db"):
        self.db_path = db_path
        self.evidence_collector = EvidenceCollector()
        self.claims: List[Claim] = []
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for claims storage"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS claims (
                    id TEXT PRIMARY KEY,
                    what TEXT NOT NULL,
                    agent TEXT NOT NULL,
                    command TEXT NOT NULL,
                    status TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    verifier TEXT,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    verified_at TEXT
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS evidence (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    claim_id TEXT NOT NULL,
                    path TEXT NOT NULL,
                    type TEXT NOT NULL,
                    hash TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    description TEXT,
                    FOREIGN KEY (claim_id) REFERENCES claims (id)
                )
            """
            )
            conn.commit()

    def make_claim(
        self,
        what: str,
        agent: str,
        command: str = "",
        severity: ClaimSeverity = ClaimSeverity.MEDIUM,
    ) -> Claim:
        """Create a new claim"""
        claim = Claim(
            id="",  # Will be generated
            what=what,
            agent=agent,
            command=command,
            status=ClaimStatus.PENDING,
            severity=severity,
            evidence=[],
        )

        self.claims.append(claim)
        print(f"📋 Claim created: {claim.what} (ID: {claim.id})")
        return claim

    def add_evidence(self, claim: Claim, evidence: Evidence) -> bool:
        """Add evidence to a claim"""
        claim.evidence.append(evidence)
        print(
            f"📎 Evidence added to claim {claim.id}: {evidence.type} - {evidence.path}"
        )

        # Auto-verify if evidence meets criteria
        return self._try_auto_verify(claim)

    def add_evidence_from_file(
        self,
        claim: Claim,
        file_path: str,
        evidence_type: str = "artifact",
        description: Optional[str] = None,
    ) -> bool:
        """Add file evidence to claim"""
        try:
            evidence = self.evidence_collector.collect_file(
                file_path, evidence_type, description
            )
            return self.add_evidence(claim, evidence)
        except Exception as e:
            print(f"❌ Failed to collect evidence from {file_path}: {e}")
            return False

    def add_command_evidence(
        self,
        claim: Claim,
        command: str,
        output: str,
        exit_code: int,
        description: Optional[str] = None,
    ) -> bool:
        """Add command execution evidence to claim"""
        try:
            evidence = self.evidence_collector.collect_command_output(
                command, output, exit_code, description
            )
            return self.add_evidence(claim, evidence)
        except Exception as e:
            print(f"❌ Failed to collect command evidence: {e}")
            return False

    def verify_claim(self, claim: Claim, verifier: str = "manual") -> bool:
        """Manually verify a claim"""
        if not claim.evidence:
            claim.status = ClaimStatus.EVIDENCE_MISSING
            claim.error_message = "No evidence provided"
            print(f"❌ Claim {claim.id} failed: No evidence")
            return False

        # Check all evidence files exist and hashes match
        for evidence in claim.evidence:
            if not Path(evidence.path).exists():
                claim.status = ClaimStatus.FAILED
                claim.error_message = f"Evidence file missing: {evidence.path}"
                print(f"❌ Claim {claim.id} failed: Missing evidence file")
                return False

            # Verify hash
            current_hash = self.evidence_collector._hash_file(Path(evidence.path))
            if current_hash != evidence.hash:
                claim.status = ClaimStatus.FAILED
                claim.error_message = f"Evidence file modified: {evidence.path}"
                print(f"❌ Claim {claim.id} failed: Evidence tampered")
                return False

        claim.status = ClaimStatus.VERIFIED
        claim.verifier = verifier
        claim.verified_at = datetime.now().isoformat()
        print(f"✅ Claim {claim.id} verified by {verifier}")

        self._store_claim(claim)
        return True

    def _try_auto_verify(self, claim: Claim) -> bool:
        """Attempt automatic verification based on evidence"""
        # Auto-verify if we have sufficient evidence types
        evidence_types = {e.type for e in claim.evidence}

        # Different verification criteria based on claim type
        if "test" in claim.what.lower() and "test_results" in evidence_types:
            return self.verify_claim(claim, "auto_test_results")

        if "build" in claim.what.lower() and "log" in evidence_types:
            return self.verify_claim(claim, "auto_build_log")

        if len(claim.evidence) >= 2:  # Multiple evidence pieces
            return self.verify_claim(claim, "auto_multi_evidence")

        return False

    def _store_claim(self, claim: Claim):
        """Store claim in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Store claim
                conn.execute(
                    """
                    INSERT OR REPLACE INTO claims
                    (id, what, agent, command, status, severity, verifier, error_message, created_at, verified_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        claim.id,
                        claim.what,
                        claim.agent,
                        claim.command,
                        claim.status.value,
                        claim.severity.value,
                        claim.verifier,
                        claim.error_message,
                        claim.created_at,
                        claim.verified_at,
                    ),
                )

                # Store evidence
                for evidence in claim.evidence:
                    conn.execute(
                        """
                        INSERT INTO evidence
                        (claim_id, path, type, hash, size, created_at, description)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            claim.id,
                            evidence.path,
                            evidence.type,
                            evidence.hash,
                            evidence.size,
                            evidence.created_at,
                            evidence.description,
                        ),
                    )

                conn.commit()
        except Exception as e:
            print(f"❌ Failed to store claim {claim.id}: {e}")

    def get_claims(
        self,
        status: Optional[ClaimStatus] = None,
        agent: Optional[str] = None,
        limit: int = 100,
    ) -> List[Claim]:
        """Get claims from database"""
        query = "SELECT * FROM claims"
        params = []

        conditions = []
        if status:
            conditions.append("status = ?")
            params.append(status.value)
        if agent:
            conditions.append("agent = ?")
            params.append(agent)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        claims = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                for row in conn.execute(query, params):
                    claim_data = dict(row)

                    # Load evidence
                    evidence_rows = conn.execute(
                        "SELECT * FROM evidence WHERE claim_id = ?", (claim_data["id"],)
                    ).fetchall()

                    evidence_list = []
                    for ev_row in evidence_rows:
                        evidence_list.append(
                            Evidence(
                                path=ev_row["path"],
                                type=ev_row["type"],
                                hash=ev_row["hash"],
                                size=ev_row["size"],
                                created_at=ev_row["created_at"],
                                description=ev_row["description"],
                            )
                        )

                    claim = Claim(
                        id=claim_data["id"],
                        what=claim_data["what"],
                        agent=claim_data["agent"],
                        command=claim_data["command"],
                        status=ClaimStatus(claim_data["status"]),
                        severity=ClaimSeverity(claim_data["severity"]),
                        evidence=evidence_list,
                        verifier=claim_data["verifier"],
                        error_message=claim_data["error_message"],
                        created_at=claim_data["created_at"],
                        verified_at=claim_data["verified_at"],
                    )
                    claims.append(claim)
        except Exception as e:
            print(f"❌ Failed to get claims: {e}")

        return claims

    def get_statistics(self) -> Dict[str, Any]:
        """Get claims statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT
                        status,
                        COUNT(*) as count
                    FROM claims
                    GROUP BY status
                """
                )
                status_counts = {row[0]: row[1] for row in cursor}

                cursor = conn.execute("SELECT COUNT(*) FROM claims")
                total_claims = cursor.fetchone()[0]

                cursor = conn.execute(
                    """
                    SELECT COUNT(*) FROM claims
                    WHERE status = 'verified' AND created_at >= datetime('now', '-24 hours')
                """
                )
                verified_today = cursor.fetchone()[0]

                return {
                    "total_claims": total_claims,
                    "status_breakdown": status_counts,
                    "verified_today": verified_today,
                    "verification_rate": status_counts.get("verified", 0)
                    / max(total_claims, 1)
                    * 100,
                }
        except Exception as e:
            print(f"❌ Failed to get statistics: {e}")
            return {}

    def export_claims_jsonl(self, output_path: str = "artifacts/claims.jsonl"):
        """Export all claims to JSONL format"""
        claims = self.get_claims()

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            for claim in claims:
                claim_dict = asdict(claim)
                # Convert enums to strings
                claim_dict["status"] = claim.status.value
                claim_dict["severity"] = claim.severity.value
                f.write(json.dumps(claim_dict) + "\n")

        print(f"📄 Exported {len(claims)} claims to {output_path}")
        return output_path


class SemanticChecker:
    """L3 Outcome/Semantic Evaluation - Deterministic answer quality scoring"""

    def __init__(self, db_path: str = "termnet_claims.db"):
        self.db_path = db_path
        self._init_semantic_schema()

    def _init_semantic_schema(self):
        """Initialize semantic_scores table"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS semantic_scores (
                    request_id TEXT PRIMARY KEY,
                    grounding REAL,
                    consistency REAL,
                    style REAL,
                    final INTEGER,
                    created_at TEXT
                )
            """
            )
            conn.commit()

    def score_answer(self, answer: str, evidence: List[str]) -> Dict[str, Any]:
        """Score answer quality using deterministic heuristics

        Args:
            answer: The agent's final answer
            evidence: List of evidence snippets

        Returns:
            Dict with grounding (0-1), consistency (0-1), style (0-1), final (0-100)
        """
        if not answer or not answer.strip():
            return {"grounding": 0.0, "consistency": 0.0, "style": 0.0, "final": 0}

        answer_lower = answer.lower().strip()
        evidence_text = " ".join(evidence).lower() if evidence else ""

        # 1. Grounding: unique token overlap / (len(answer_terms) or 1)
        grounding_score = self._compute_grounding(answer_lower, evidence_text)

        # 2. Consistency: penalize uncertainty and contradictions
        consistency_score = self._compute_consistency(answer_lower, evidence_text)

        # 3. Style: reward citations and proper length
        style_score = self._compute_style(answer)

        # 4. Final score: weighted combination
        final = round(
            100 * (0.5 * grounding_score + 0.4 * consistency_score + 0.1 * style_score)
        )

        return {
            "grounding": round(grounding_score, 3),
            "consistency": round(consistency_score, 3),
            "style": round(style_score, 3),
            "final": final,
        }

    def _compute_grounding(self, answer: str, evidence: str) -> float:
        """Compute grounding score based on token overlap"""
        if not evidence:
            return 0.0

        answer_tokens = set(self._tokenize(answer))
        evidence_tokens = set(self._tokenize(evidence))

        if not answer_tokens:
            return 0.0

        overlap = answer_tokens.intersection(evidence_tokens)
        return len(overlap) / len(answer_tokens)

    def _compute_consistency(self, answer: str, evidence: str) -> float:
        """Compute consistency score by penalizing uncertainty and contradictions"""
        score = 1.0

        # Penalize uncertainty phrases
        uncertainty_phrases = [
            "i made that up",
            "unsure",
            "not sure",
            "don't know",
            "unclear",
            "might be",
            "could be",
            "possibly",
            "maybe",
            "perhaps",
            "uncertain",
        ]

        for phrase in uncertainty_phrases:
            if phrase in answer:
                score -= 0.2

        # Distinguish contradictions from simple negations
        # Look for explicit contradictions like "but evidence shows" or "however"
        contradiction_patterns = [
            "but evidence shows",
            "however evidence",
            "contradicts",
            "differs from",
            "unlike the evidence",
            "evidence suggests otherwise",
        ]

        for pattern in contradiction_patterns:
            if pattern in answer:
                score -= 0.3

        return max(0.0, score)

    def _compute_style(self, answer: str) -> float:
        """Compute style score based on citations and length"""
        score = 0.0

        # Reward citations
        citation_patterns = [
            "(source)",
            "[ref]",
            "source a",
            "source b",
            "(ref)",
            "according to",
        ]
        has_citations = any(pattern in answer.lower() for pattern in citation_patterns)
        if has_citations:
            score += 0.5

        # Reward ≥2 sentences
        sentence_count = len([s for s in answer.split(".") if s.strip()])
        if sentence_count >= 2:
            score += 0.3

        # Dampen if >300 words
        word_count = len(answer.split())
        if word_count > 300:
            score -= 0.2

        return max(0.0, min(1.0, score))

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization for overlap calculation"""
        import re

        # Remove punctuation and split on whitespace
        text = re.sub(r"[^\w\s]", " ", text)
        return [token.strip() for token in text.split() if len(token.strip()) > 2]

    def save_semantic_score(self, request_id: str, score_dict: Dict[str, Any]):
        """Save semantic score to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO semantic_scores
                (request_id, grounding, consistency, style, final, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    request_id,
                    score_dict["grounding"],
                    score_dict["consistency"],
                    score_dict["style"],
                    score_dict["final"],
                    datetime.now().isoformat(),
                ),
            )
            conn.commit()

    def llm_judge(self, answer: str, rubric: str) -> Optional[Dict[str, Any]]:
        """Stub for future LLM-based evaluation"""
        # TODO: Implement LLM judging with external API
        return None

    def close(self):
        """Close database connections (for test cleanup)"""
        # SemanticChecker uses context managers, so no persistent connections to close
        pass
