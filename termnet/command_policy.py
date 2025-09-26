"""
Command Policy - Advanced command allowlisting and security policies
Phase 3 of TermNet validation system: Intelligent command filtering and approval
"""

import json
import re
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from termnet.claims_engine import ClaimsEngine, ClaimSeverity


class PolicyDecision(Enum):
    ALLOW = "allow"
    BLOCK = "block"
    REQUIRE_EVIDENCE = "require_evidence"
    REQUIRE_APPROVAL = "require_approval"
    SANDBOX_ONLY = "sandbox_only"


class CommandCategory(Enum):
    FILE_OPERATIONS = "file_operations"
    NETWORK_OPERATIONS = "network_operations"
    SYSTEM_OPERATIONS = "system_operations"
    DEVELOPMENT_TOOLS = "development_tools"
    PACKAGE_MANAGEMENT = "package_management"
    GIT_OPERATIONS = "git_operations"
    BUILD_TOOLS = "build_tools"
    TESTING_TOOLS = "testing_tools"
    CONTAINER_TOOLS = "container_tools"
    DANGEROUS_OPERATIONS = "dangerous_operations"


@dataclass
class PolicyRule:
    """Individual policy rule for command matching"""

    name: str
    pattern: str  # Regex pattern to match
    category: CommandCategory
    decision: PolicyDecision
    reason: str
    severity: ClaimSeverity = ClaimSeverity.MEDIUM
    evidence_required: List[str] = None  # Types of evidence required
    conditions: Dict[str, Any] = None  # Additional conditions
    exceptions: List[str] = None  # Exception patterns

    def __post_init__(self):
        if self.evidence_required is None:
            self.evidence_required = []
        if self.conditions is None:
            self.conditions = {}
        if self.exceptions is None:
            self.exceptions = []


@dataclass
class PolicyEvaluation:
    """Result of policy evaluation for a command"""

    command: str
    agent: str
    decision: PolicyDecision
    matched_rules: List[PolicyRule]
    reason: str
    severity: ClaimSeverity
    evidence_required: List[str]
    suggested_alternatives: List[str]
    risk_score: int  # 0-100
    can_override: bool
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class AgentPolicy:
    """Agent-specific command policies"""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.allowed_categories: Set[CommandCategory] = set()
        self.blocked_categories: Set[CommandCategory] = set()
        self.custom_rules: List[PolicyRule] = []
        self.evidence_requirements: Dict[CommandCategory, List[str]] = {}

        # Set default policies based on agent type
        self._set_default_policies()

    def _set_default_policies(self):
        """Set default policies based on agent type"""
        if self.agent_name == "analyst":
            # Analyst can read files and run analysis tools
            self.allowed_categories.update(
                [
                    CommandCategory.FILE_OPERATIONS,
                    CommandCategory.GIT_OPERATIONS,
                    CommandCategory.TESTING_TOOLS,
                    CommandCategory.DEVELOPMENT_TOOLS,
                ]
            )
            self.blocked_categories.add(CommandCategory.DANGEROUS_OPERATIONS)

        elif self.agent_name == "developer":
            # Developer has broader access but with evidence requirements
            self.allowed_categories.update(
                [
                    CommandCategory.FILE_OPERATIONS,
                    CommandCategory.DEVELOPMENT_TOOLS,
                    CommandCategory.PACKAGE_MANAGEMENT,
                    CommandCategory.GIT_OPERATIONS,
                    CommandCategory.BUILD_TOOLS,
                    CommandCategory.TESTING_TOOLS,
                    CommandCategory.CONTAINER_TOOLS,
                ]
            )
            self.evidence_requirements[CommandCategory.PACKAGE_MANAGEMENT] = [
                "command_output",
                "log",
            ]
            self.evidence_requirements[CommandCategory.BUILD_TOOLS] = [
                "build_log",
                "artifacts",
            ]

        elif self.agent_name == "qa":
            # QA focuses on testing and validation
            self.allowed_categories.update(
                [
                    CommandCategory.TESTING_TOOLS,
                    CommandCategory.FILE_OPERATIONS,
                    CommandCategory.GIT_OPERATIONS,
                    CommandCategory.DEVELOPMENT_TOOLS,
                ]
            )

        elif self.agent_name == "validator":
            # Validator needs access to verification tools
            self.allowed_categories.update(
                [
                    CommandCategory.TESTING_TOOLS,
                    CommandCategory.FILE_OPERATIONS,
                    CommandCategory.DEVELOPMENT_TOOLS,
                    CommandCategory.BUILD_TOOLS,
                ]
            )

        else:
            # Default: very restricted access
            self.allowed_categories.add(CommandCategory.FILE_OPERATIONS)
            self.blocked_categories.update(
                [
                    CommandCategory.DANGEROUS_OPERATIONS,
                    CommandCategory.SYSTEM_OPERATIONS,
                    CommandCategory.NETWORK_OPERATIONS,
                ]
            )


class CommandPolicyEngine:
    """Main policy engine for command evaluation and approval"""

    def __init__(self, claims_engine: Optional[ClaimsEngine] = None):
        self.claims_engine = claims_engine or ClaimsEngine()
        self.rules: List[PolicyRule] = []
        self.agent_policies: Dict[str, AgentPolicy] = {}
        self.evaluation_history: List[PolicyEvaluation] = []

        # Load default rules
        self._load_default_rules()
        self._load_agent_policies()

        print("🛡️ Command Policy Engine initialized with security rules")

    def _load_default_rules(self):
        """Load default security rules"""

        # DANGEROUS OPERATIONS - Always block
        self.rules.extend(
            [
                PolicyRule(
                    name="destructive_rm",
                    pattern=r"rm\s+(-rf?|--recursive|--force).*/",
                    category=CommandCategory.DANGEROUS_OPERATIONS,
                    decision=PolicyDecision.BLOCK,
                    reason="Potentially destructive recursive delete",
                    severity=ClaimSeverity.CRITICAL,
                ),
                PolicyRule(
                    name="system_root_access",
                    pattern=r"sudo\s+(rm|mv|cp|chmod|chown).*/(etc|usr|var|sys|proc|dev)",
                    category=CommandCategory.DANGEROUS_OPERATIONS,
                    decision=PolicyDecision.BLOCK,
                    reason="System directory modification with sudo",
                    severity=ClaimSeverity.CRITICAL,
                ),
                PolicyRule(
                    name="pipe_to_shell",
                    pattern=r"(curl|wget).*\|\s*(bash|sh|zsh|fish)",
                    category=CommandCategory.DANGEROUS_OPERATIONS,
                    decision=PolicyDecision.BLOCK,
                    reason="Piping remote content to shell",
                    severity=ClaimSeverity.CRITICAL,
                ),
                PolicyRule(
                    name="device_manipulation",
                    pattern=r"(dd|fdisk|mkfs|mount).*/(dev|sys)",
                    category=CommandCategory.DANGEROUS_OPERATIONS,
                    decision=PolicyDecision.BLOCK,
                    reason="Direct device manipulation",
                    severity=ClaimSeverity.CRITICAL,
                ),
                PolicyRule(
                    name="privilege_escalation",
                    pattern=r"(sudo su|su -|setuid|chmod.*4755)",
                    category=CommandCategory.DANGEROUS_OPERATIONS,
                    decision=PolicyDecision.BLOCK,
                    reason="Privilege escalation attempt",
                    severity=ClaimSeverity.CRITICAL,
                ),
            ]
        )

        # FILE OPERATIONS - Allow with conditions
        self.rules.extend(
            [
                PolicyRule(
                    name="safe_file_read",
                    pattern=r"^(cat|less|more|head|tail|grep|find|ls|pwd|file)\b",
                    category=CommandCategory.FILE_OPERATIONS,
                    decision=PolicyDecision.ALLOW,
                    reason="Safe file reading operations",
                    severity=ClaimSeverity.LOW,
                ),
                PolicyRule(
                    name="file_copy_move",
                    pattern=r"^(cp|mv)\s+(?!.*/(etc|usr|var|sys))",
                    category=CommandCategory.FILE_OPERATIONS,
                    decision=PolicyDecision.REQUIRE_EVIDENCE,
                    reason="File copy/move operations require evidence",
                    severity=ClaimSeverity.MEDIUM,
                    evidence_required=["command_output", "file_checksum"],
                ),
                PolicyRule(
                    name="directory_operations",
                    pattern=r"^(mkdir|rmdir|touch)\s+(?!.*/(etc|usr|var|sys))",
                    category=CommandCategory.FILE_OPERATIONS,
                    decision=PolicyDecision.ALLOW,
                    reason="Safe directory operations",
                    severity=ClaimSeverity.LOW,
                ),
            ]
        )

        # DEVELOPMENT TOOLS - Allow with evidence
        self.rules.extend(
            [
                PolicyRule(
                    name="python_execution",
                    pattern=r"^python[0-9]*(\.[0-9]+)*\s+",
                    category=CommandCategory.DEVELOPMENT_TOOLS,
                    decision=PolicyDecision.REQUIRE_EVIDENCE,
                    reason="Python script execution requires verification",
                    severity=ClaimSeverity.MEDIUM,
                    evidence_required=["script_output", "success_token"],
                ),
                PolicyRule(
                    name="node_execution",
                    pattern=r"^node\s+",
                    category=CommandCategory.DEVELOPMENT_TOOLS,
                    decision=PolicyDecision.REQUIRE_EVIDENCE,
                    reason="Node.js script execution requires verification",
                    severity=ClaimSeverity.MEDIUM,
                    evidence_required=["script_output", "success_token"],
                ),
                PolicyRule(
                    name="code_linting",
                    pattern=r"^(pylint|flake8|eslint|tslint|black|prettier)\b",
                    category=CommandCategory.DEVELOPMENT_TOOLS,
                    decision=PolicyDecision.ALLOW,
                    reason="Code linting and formatting tools",
                    severity=ClaimSeverity.LOW,
                ),
            ]
        )

        # PACKAGE MANAGEMENT - Require evidence
        self.rules.extend(
            [
                PolicyRule(
                    name="npm_install",
                    pattern=r"^npm\s+(install|i|ci)\b",
                    category=CommandCategory.PACKAGE_MANAGEMENT,
                    decision=PolicyDecision.REQUIRE_EVIDENCE,
                    reason="Package installation requires verification",
                    severity=ClaimSeverity.HIGH,
                    evidence_required=["package_lock", "install_log", "success_token"],
                ),
                PolicyRule(
                    name="pip_install",
                    pattern=r"^pip[0-9]*\s+install\b",
                    category=CommandCategory.PACKAGE_MANAGEMENT,
                    decision=PolicyDecision.REQUIRE_EVIDENCE,
                    reason="Python package installation requires verification",
                    severity=ClaimSeverity.HIGH,
                    evidence_required=[
                        "requirements_freeze",
                        "install_log",
                        "success_token",
                    ],
                ),
                PolicyRule(
                    name="package_info",
                    pattern=r"^(npm\s+(list|ls|info|show)|pip[0-9]*\s+(list|show|freeze))\b",
                    category=CommandCategory.PACKAGE_MANAGEMENT,
                    decision=PolicyDecision.ALLOW,
                    reason="Package information queries are safe",
                    severity=ClaimSeverity.LOW,
                ),
            ]
        )

        # GIT OPERATIONS - Categorized by risk
        self.rules.extend(
            [
                PolicyRule(
                    name="git_read_operations",
                    pattern=r"^git\s+(status|log|diff|show|branch|tag)\b",
                    category=CommandCategory.GIT_OPERATIONS,
                    decision=PolicyDecision.ALLOW,
                    reason="Safe git read operations",
                    severity=ClaimSeverity.LOW,
                ),
                PolicyRule(
                    name="git_local_changes",
                    pattern=r"^git\s+(add|commit|reset|checkout|stash)\b",
                    category=CommandCategory.GIT_OPERATIONS,
                    decision=PolicyDecision.REQUIRE_EVIDENCE,
                    reason="Git local changes require verification",
                    severity=ClaimSeverity.MEDIUM,
                    evidence_required=["git_status", "commit_hash"],
                ),
                PolicyRule(
                    name="git_remote_operations",
                    pattern=r"^git\s+(push|pull|fetch|clone)\b",
                    category=CommandCategory.GIT_OPERATIONS,
                    decision=PolicyDecision.REQUIRE_EVIDENCE,
                    reason="Git remote operations require verification",
                    severity=ClaimSeverity.HIGH,
                    evidence_required=["git_log", "remote_status", "success_token"],
                ),
            ]
        )

        # BUILD TOOLS - Evidence required
        self.rules.extend(
            [
                PolicyRule(
                    name="build_systems",
                    pattern=r"^(make|cmake|gradle|maven|cargo|go\s+build)\b",
                    category=CommandCategory.BUILD_TOOLS,
                    decision=PolicyDecision.REQUIRE_EVIDENCE,
                    reason="Build operations require verification",
                    severity=ClaimSeverity.HIGH,
                    evidence_required=["build_log", "artifacts", "success_token"],
                ),
                PolicyRule(
                    name="npm_scripts",
                    pattern=r"^npm\s+run\s+",
                    category=CommandCategory.BUILD_TOOLS,
                    decision=PolicyDecision.REQUIRE_EVIDENCE,
                    reason="NPM script execution requires verification",
                    severity=ClaimSeverity.MEDIUM,
                    evidence_required=["script_output", "success_token"],
                ),
            ]
        )

        # TESTING TOOLS - Allow with evidence
        self.rules.extend(
            [
                PolicyRule(
                    name="testing_frameworks",
                    pattern=r"^(pytest|jest|mocha|jasmine|phpunit|rspec)\b",
                    category=CommandCategory.TESTING_TOOLS,
                    decision=PolicyDecision.REQUIRE_EVIDENCE,
                    reason="Test execution requires verification of results",
                    severity=ClaimSeverity.MEDIUM,
                    evidence_required=[
                        "test_results",
                        "coverage_report",
                        "success_token",
                    ],
                ),
                PolicyRule(
                    name="test_coverage",
                    pattern=r"^(coverage|nyc|istanbul)\b",
                    category=CommandCategory.TESTING_TOOLS,
                    decision=PolicyDecision.ALLOW,
                    reason="Coverage analysis tools are safe",
                    severity=ClaimSeverity.LOW,
                ),
            ]
        )

        # CONTAINER TOOLS - Sandboxed execution
        self.rules.extend(
            [
                PolicyRule(
                    name="docker_build",
                    pattern=r"^docker\s+build\b",
                    category=CommandCategory.CONTAINER_TOOLS,
                    decision=PolicyDecision.SANDBOX_ONLY,
                    reason="Docker builds should run in sandbox",
                    severity=ClaimSeverity.HIGH,
                    evidence_required=["build_log", "image_id"],
                ),
                PolicyRule(
                    name="docker_run_safe",
                    pattern=r"^docker\s+run.*--rm\b",
                    category=CommandCategory.CONTAINER_TOOLS,
                    decision=PolicyDecision.SANDBOX_ONLY,
                    reason="Docker run with auto-remove",
                    severity=ClaimSeverity.MEDIUM,
                    evidence_required=["container_log"],
                ),
                PolicyRule(
                    name="docker_info",
                    pattern=r"^docker\s+(ps|images|version|info)\b",
                    category=CommandCategory.CONTAINER_TOOLS,
                    decision=PolicyDecision.ALLOW,
                    reason="Docker information commands are safe",
                    severity=ClaimSeverity.LOW,
                ),
            ]
        )

        # NETWORK OPERATIONS - Restricted
        self.rules.extend(
            [
                PolicyRule(
                    name="network_download",
                    pattern=r"^(curl|wget)\s+(?!.*\|)",
                    category=CommandCategory.NETWORK_OPERATIONS,
                    decision=PolicyDecision.REQUIRE_EVIDENCE,
                    reason="Network downloads require verification",
                    severity=ClaimSeverity.HIGH,
                    evidence_required=["download_log", "file_checksum"],
                    exceptions=[r".*\|\s*(bash|sh)"],  # Block if piped to shell
                ),
                PolicyRule(
                    name="network_servers",
                    pattern=r"^(nc|netcat|ncat)\s+-l",
                    category=CommandCategory.NETWORK_OPERATIONS,
                    decision=PolicyDecision.BLOCK,
                    reason="Network servers not allowed",
                    severity=ClaimSeverity.HIGH,
                ),
            ]
        )

        print(f"📋 Loaded {len(self.rules)} default policy rules")

    def _load_agent_policies(self):
        """Load agent-specific policies"""
        default_agents = [
            "analyst",
            "pm",
            "architect",
            "developer",
            "qa",
            "validator",
            "auditor",
        ]

        for agent in default_agents:
            self.agent_policies[agent] = AgentPolicy(agent)

        print(f"👥 Loaded policies for {len(self.agent_policies)} agents")

    def evaluate_command(
        self, command: str, agent: str = "unknown"
    ) -> PolicyEvaluation:
        """Evaluate command against policies"""

        matched_rules = []
        decision = PolicyDecision.BLOCK  # Default to block
        reason = "No matching policy rule"
        severity = ClaimSeverity.HIGH
        evidence_required = []
        suggested_alternatives = []
        risk_score = 100  # Maximum risk by default

        # Get agent policy
        agent_policy = self.agent_policies.get(agent, AgentPolicy("unknown"))

        # Evaluate against rules
        for rule in self.rules:
            if self._rule_matches(rule, command):
                matched_rules.append(rule)

                # Check if agent is allowed to use this category
                if rule.category in agent_policy.blocked_categories:
                    decision = PolicyDecision.BLOCK
                    reason = f"Agent {agent} blocked from {rule.category.value}"
                    severity = ClaimSeverity.CRITICAL
                    break

                # Update decision based on rule (more permissive wins)
                if rule.decision.value in ["allow", "require_evidence", "sandbox_only"]:
                    if decision == PolicyDecision.BLOCK:
                        decision = rule.decision
                        reason = rule.reason
                        severity = rule.severity
                        evidence_required = rule.evidence_required.copy()

                        # Add agent-specific evidence requirements
                        if rule.category in agent_policy.evidence_requirements:
                            evidence_required.extend(
                                agent_policy.evidence_requirements[rule.category]
                            )

                # Calculate risk score (lower is better)
                rule_risk = self._calculate_rule_risk(rule)
                if rule_risk < risk_score:
                    risk_score = rule_risk

        # If no rules matched but agent has custom rules, check those
        if not matched_rules:
            for rule in agent_policy.custom_rules:
                if self._rule_matches(rule, command):
                    matched_rules.append(rule)
                    decision = rule.decision
                    reason = rule.reason
                    severity = rule.severity
                    evidence_required = rule.evidence_required.copy()
                    break

        # Generate suggestions for blocked commands
        if decision == PolicyDecision.BLOCK:
            suggested_alternatives = self._suggest_alternatives(command)

        # Determine if override is possible
        can_override = decision != PolicyDecision.BLOCK or any(
            rule.category != CommandCategory.DANGEROUS_OPERATIONS
            for rule in matched_rules
        )

        evaluation = PolicyEvaluation(
            command=command,
            agent=agent,
            decision=decision,
            matched_rules=matched_rules,
            reason=reason,
            severity=severity,
            evidence_required=list(set(evidence_required)),  # Remove duplicates
            suggested_alternatives=suggested_alternatives,
            risk_score=risk_score,
            can_override=can_override,
        )

        # Store evaluation in history
        self.evaluation_history.append(evaluation)

        # Log the evaluation
        decision_emoji = {
            PolicyDecision.ALLOW: "✅",
            PolicyDecision.BLOCK: "🚫",
            PolicyDecision.REQUIRE_EVIDENCE: "📎",
            PolicyDecision.REQUIRE_APPROVAL: "⚠️",
            PolicyDecision.SANDBOX_ONLY: "📦",
        }

        emoji = decision_emoji.get(decision, "❓")
        print(f"{emoji} Policy: {command} -> {decision.value} (Risk: {risk_score})")

        return evaluation

    def _rule_matches(self, rule: PolicyRule, command: str) -> bool:
        """Check if a rule matches the command"""
        try:
            # Check main pattern
            if not re.search(rule.pattern, command, re.IGNORECASE):
                return False

            # Check exceptions
            for exception in rule.exceptions:
                if re.search(exception, command, re.IGNORECASE):
                    return False

            return True

        except re.error as e:
            print(f"⚠️ Invalid regex pattern in rule {rule.name}: {e}")
            return False

    def _calculate_rule_risk(self, rule: PolicyRule) -> int:
        """Calculate risk score for a rule (0-100)"""
        base_risk = {
            CommandCategory.DANGEROUS_OPERATIONS: 100,
            CommandCategory.SYSTEM_OPERATIONS: 80,
            CommandCategory.NETWORK_OPERATIONS: 70,
            CommandCategory.CONTAINER_TOOLS: 60,
            CommandCategory.PACKAGE_MANAGEMENT: 50,
            CommandCategory.BUILD_TOOLS: 40,
            CommandCategory.GIT_OPERATIONS: 30,
            CommandCategory.DEVELOPMENT_TOOLS: 20,
            CommandCategory.TESTING_TOOLS: 10,
            CommandCategory.FILE_OPERATIONS: 5,
        }.get(rule.category, 50)

        # Adjust based on severity
        severity_multiplier = {
            ClaimSeverity.CRITICAL: 1.0,
            ClaimSeverity.HIGH: 0.8,
            ClaimSeverity.MEDIUM: 0.6,
            ClaimSeverity.LOW: 0.4,
            ClaimSeverity.INFO: 0.2,
        }.get(rule.severity, 0.6)

        return int(base_risk * severity_multiplier)

    def _suggest_alternatives(self, command: str) -> List[str]:
        """Suggest safer alternatives for blocked commands"""
        suggestions = []

        if "rm -rf" in command:
            suggestions.extend(
                [
                    "Use 'rm -i' for interactive deletion",
                    "Move files to trash instead of deleting",
                    "Use git clean for repository cleanup",
                ]
            )

        if "sudo" in command and any(
            dangerous in command for dangerous in ["rm", "mv", "chmod"]
        ):
            suggestions.extend(
                [
                    "Run commands without sudo if possible",
                    "Use specific file paths instead of wildcards",
                    "Test commands with --dry-run first",
                ]
            )

        if re.search(r"curl.*\|.*bash", command):
            suggestions.extend(
                [
                    "Download script first, then review before executing",
                    "Use package managers instead of remote scripts",
                    "Verify script signatures before execution",
                ]
            )

        if "docker run" in command and "--rm" not in command:
            suggestions.extend(
                [
                    "Add --rm flag for automatic cleanup",
                    "Use specific tags instead of 'latest'",
                    "Limit resources with --memory and --cpus",
                ]
            )

        return suggestions

    def add_custom_rule(self, agent: str, rule: PolicyRule):
        """Add custom rule for specific agent"""
        if agent not in self.agent_policies:
            self.agent_policies[agent] = AgentPolicy(agent)

        self.agent_policies[agent].custom_rules.append(rule)
        print(f"📝 Added custom rule '{rule.name}' for agent {agent}")

    def get_policy_summary(self) -> Dict[str, Any]:
        """Get summary of policy configuration"""
        rule_counts = {}
        for rule in self.rules:
            category = rule.category.value
            rule_counts[category] = rule_counts.get(category, 0) + 1

        decision_counts = {}
        for evaluation in self.evaluation_history[-100:]:  # Last 100 evaluations
            decision = evaluation.decision.value
            decision_counts[decision] = decision_counts.get(decision, 0) + 1

        return {
            "total_rules": len(self.rules),
            "rules_by_category": rule_counts,
            "agent_policies": len(self.agent_policies),
            "recent_decisions": decision_counts,
            "evaluation_history_count": len(self.evaluation_history),
        }

    def export_policy(self, file_path: str):
        """Export policy configuration to JSON"""
        policy_data = {
            "rules": [
                {
                    "name": rule.name,
                    "pattern": rule.pattern,
                    "category": rule.category.value,
                    "decision": rule.decision.value,
                    "reason": rule.reason,
                    "severity": rule.severity.value,
                    "evidence_required": rule.evidence_required,
                    "conditions": rule.conditions,
                    "exceptions": rule.exceptions,
                }
                for rule in self.rules
            ],
            "agent_policies": {
                agent: {
                    "allowed_categories": [
                        cat.value for cat in policy.allowed_categories
                    ],
                    "blocked_categories": [
                        cat.value for cat in policy.blocked_categories
                    ],
                    "evidence_requirements": {
                        cat.value: reqs
                        for cat, reqs in policy.evidence_requirements.items()
                    },
                }
                for agent, policy in self.agent_policies.items()
            },
            "exported_at": datetime.now().isoformat(),
        }

        with open(file_path, "w") as f:
            json.dump(policy_data, f, indent=2)

        print(f"📄 Policy exported to {file_path}")

    def create_evidence_claim(self, evaluation: PolicyEvaluation) -> Optional[str]:
        """Create a claim for commands requiring evidence"""
        if evaluation.decision != PolicyDecision.REQUIRE_EVIDENCE:
            return None

        claim = self.claims_engine.make_claim(
            what=f"Command execution: {evaluation.command}",
            agent=evaluation.agent,
            command=evaluation.command,
            severity=evaluation.severity,
        )

        # Add metadata about required evidence
        claim_id = claim.id

        # Store evaluation reference
        evaluation_file = Path("artifacts/evaluations") / f"{claim_id}_evaluation.json"
        evaluation_file.parent.mkdir(parents=True, exist_ok=True)

        evaluation_data = {
            "claim_id": claim_id,
            "command": evaluation.command,
            "agent": evaluation.agent,
            "decision": evaluation.decision.value,
            "evidence_required": evaluation.evidence_required,
            "risk_score": evaluation.risk_score,
            "matched_rules": [rule.name for rule in evaluation.matched_rules],
            "timestamp": evaluation.timestamp,
        }

        with open(evaluation_file, "w") as f:
            json.dump(evaluation_data, f, indent=2)

        print(f"📋 Created claim {claim_id} for evidence-required command")
        return claim_id
