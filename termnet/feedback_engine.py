"""
TermNet Feedback Engine

Ingests and processes review feedback to improve autonomous code generation.
Learns from code review comments, test failures, and user corrections to enhance
future planning and implementation decisions.
"""

import hashlib
import json
import logging
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class FeedbackType(Enum):
    """Types of feedback that can be ingested."""

    CODE_REVIEW = "code_review"
    TEST_FAILURE = "test_failure"
    USER_CORRECTION = "user_correction"
    PERFORMANCE_ISSUE = "performance_issue"
    SECURITY_CONCERN = "security_concern"
    STYLE_VIOLATION = "style_violation"
    DESIGN_FEEDBACK = "design_feedback"


class FeedbackSeverity(Enum):
    """Severity levels for feedback."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class FeedbackItem:
    """Individual piece of feedback about code."""

    id: str
    type: FeedbackType
    severity: FeedbackSeverity
    title: str
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    suggested_fix: Optional[str] = None
    reviewer: Optional[str] = None
    timestamp: str = None
    tags: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}
        if self.id is None:
            # Generate ID from content hash
            content = (
                f"{self.title}{self.description}{self.file_path}{self.line_number}"
            )
            self.id = hashlib.md5(content.encode()).hexdigest()[:8]


@dataclass
class FeedbackPattern:
    """Pattern learned from feedback."""

    pattern_id: str
    pattern_type: str
    description: str
    conditions: List[str]
    recommendations: List[str]
    confidence_score: float
    occurrences: int
    last_seen: str
    examples: List[str] = None

    def __post_init__(self):
        if self.examples is None:
            self.examples = []


@dataclass
class FeedbackSummary:
    """Summary of feedback analysis."""

    total_feedback_items: int
    feedback_by_type: Dict[str, int]
    feedback_by_severity: Dict[str, int]
    top_patterns: List[FeedbackPattern]
    improvement_suggestions: List[str]
    analysis_timestamp: str
    confidence_score: float


class FeedbackParser:
    """Parses feedback from various sources."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def parse_github_review(self, review_data: Dict[str, Any]) -> List[FeedbackItem]:
        """Parse GitHub review comments into feedback items."""
        feedback_items = []

        # Parse review comments
        for comment in review_data.get("comments", []):
            feedback_item = FeedbackItem(
                id=None,  # Will be generated
                type=self._categorize_github_comment(comment.get("body", "")),
                severity=self._assess_severity(comment.get("body", "")),
                title=f"Review comment on {comment.get('path', 'unknown')}",
                description=comment.get("body", ""),
                file_path=comment.get("path"),
                line_number=comment.get("line"),
                code_snippet=comment.get("diff_hunk"),
                reviewer=comment.get("user", {}).get("login"),
                timestamp=comment.get("created_at"),
                tags=self._extract_tags(comment.get("body", "")),
                metadata={
                    "review_id": review_data.get("id"),
                    "pr_number": review_data.get("pull_request_url", "").split("/")[-1],
                    "commit_id": comment.get("commit_id"),
                    "review_state": review_data.get("state"),
                },
            )
            feedback_items.append(feedback_item)

        return feedback_items

    def parse_test_failures(self, test_results: Dict[str, Any]) -> List[FeedbackItem]:
        """Parse test failure results into feedback items."""
        feedback_items = []

        for test_case in test_results.get("test_cases", []):
            if test_case.get("status") == "failed":
                feedback_item = FeedbackItem(
                    id=None,
                    type=FeedbackType.TEST_FAILURE,
                    severity=FeedbackSeverity.HIGH,
                    title=f"Test failure: {test_case.get('name')}",
                    description=test_case.get("failure_message", ""),
                    file_path=test_case.get("file"),
                    line_number=test_case.get("line"),
                    code_snippet=test_case.get("code"),
                    timestamp=test_results.get("timestamp"),
                    tags=["test", "failure", test_case.get("category", "unknown")],
                    metadata={
                        "test_suite": test_results.get("test_suite"),
                        "execution_time": test_case.get("execution_time"),
                        "error_type": test_case.get("error_type"),
                    },
                )
                feedback_items.append(feedback_item)

        return feedback_items

    def parse_user_corrections(
        self, corrections: List[Dict[str, Any]]
    ) -> List[FeedbackItem]:
        """Parse user corrections into feedback items."""
        feedback_items = []

        for correction in corrections:
            feedback_item = FeedbackItem(
                id=None,
                type=FeedbackType.USER_CORRECTION,
                severity=FeedbackSeverity.MEDIUM,
                title=f"User correction: {correction.get('description', 'Code modification')}",
                description=correction.get("rationale", ""),
                file_path=correction.get("file_path"),
                line_number=correction.get("line_number"),
                code_snippet=correction.get("original_code"),
                suggested_fix=correction.get("corrected_code"),
                timestamp=correction.get("timestamp"),
                tags=["user_input", "correction"],
                metadata={
                    "correction_type": correction.get("type"),
                    "automated_suggestion": correction.get("was_automated", False),
                },
            )
            feedback_items.append(feedback_item)

        return feedback_items

    def _categorize_github_comment(self, comment_text: str) -> FeedbackType:
        """Categorize GitHub comment by content."""
        comment_lower = comment_text.lower()

        if any(
            keyword in comment_lower
            for keyword in ["security", "vulnerability", "exploit"]
        ):
            return FeedbackType.SECURITY_CONCERN
        elif any(
            keyword in comment_lower
            for keyword in ["performance", "slow", "optimize", "efficient"]
        ):
            return FeedbackType.PERFORMANCE_ISSUE
        elif any(
            keyword in comment_lower
            for keyword in ["style", "format", "lint", "convention"]
        ):
            return FeedbackType.STYLE_VIOLATION
        elif any(
            keyword in comment_lower
            for keyword in ["design", "architecture", "pattern"]
        ):
            return FeedbackType.DESIGN_FEEDBACK
        else:
            return FeedbackType.CODE_REVIEW

    def _assess_severity(self, comment_text: str) -> FeedbackSeverity:
        """Assess severity of feedback based on content."""
        comment_lower = comment_text.lower()

        if any(
            keyword in comment_lower
            for keyword in ["critical", "blocker", "must fix", "breaking"]
        ):
            return FeedbackSeverity.CRITICAL
        elif any(
            keyword in comment_lower
            for keyword in ["important", "should fix", "high priority"]
        ):
            return FeedbackSeverity.HIGH
        elif any(
            keyword in comment_lower
            for keyword in ["nit", "minor", "suggestion", "consider"]
        ):
            return FeedbackSeverity.LOW
        elif any(keyword in comment_lower for keyword in ["info", "note", "fyi"]):
            return FeedbackSeverity.INFO
        else:
            return FeedbackSeverity.MEDIUM

    def _extract_tags(self, text: str) -> List[str]:
        """Extract tags from text content."""
        tags = []

        # Look for hashtags
        hashtags = re.findall(r"#(\w+)", text)
        tags.extend(hashtags)

        # Look for common keywords
        keywords = {
            "bug": ["bug", "error", "issue"],
            "refactor": ["refactor", "cleanup", "reorganize"],
            "documentation": ["docs", "documentation", "comment"],
            "testing": ["test", "testing", "coverage"],
            "performance": ["performance", "optimize", "speed"],
            "security": ["security", "auth", "permission"],
        }

        text_lower = text.lower()
        for tag, words in keywords.items():
            if any(word in text_lower for word in words):
                tags.append(tag)

        return list(set(tags))  # Remove duplicates


class PatternLearner:
    """Learns patterns from feedback to improve future code generation."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.patterns: Dict[str, FeedbackPattern] = {}

    def learn_from_feedback(
        self, feedback_items: List[FeedbackItem]
    ) -> List[FeedbackPattern]:
        """Learn patterns from a batch of feedback items."""
        new_patterns = []

        # Group feedback by type and similarity
        grouped_feedback = self._group_similar_feedback(feedback_items)

        for group in grouped_feedback:
            pattern = self._extract_pattern(group)
            if pattern:
                pattern_id = pattern.pattern_id
                if pattern_id in self.patterns:
                    # Update existing pattern
                    self.patterns[pattern_id] = self._merge_patterns(
                        self.patterns[pattern_id], pattern
                    )
                else:
                    # Add new pattern
                    self.patterns[pattern_id] = pattern
                    new_patterns.append(pattern)

        return new_patterns

    def _group_similar_feedback(
        self, feedback_items: List[FeedbackItem]
    ) -> List[List[FeedbackItem]]:
        """Group similar feedback items together."""
        groups = []
        processed = set()

        for i, item in enumerate(feedback_items):
            if i in processed:
                continue

            group = [item]
            processed.add(i)

            # Find similar items
            for j, other_item in enumerate(feedback_items[i + 1 :], i + 1):
                if j in processed:
                    continue

                if self._are_similar(item, other_item):
                    group.append(other_item)
                    processed.add(j)

            if len(group) >= 2:  # Only groups with multiple items
                groups.append(group)

        return groups

    def _are_similar(self, item1: FeedbackItem, item2: FeedbackItem) -> bool:
        """Check if two feedback items are similar."""
        # Same type
        if item1.type != item2.type:
            return False

        # Similar descriptions (simple keyword matching)
        desc1_words = set(item1.description.lower().split())
        desc2_words = set(item2.description.lower().split())
        common_words = desc1_words.intersection(desc2_words)

        # At least 30% overlap in words
        if len(common_words) / max(len(desc1_words), len(desc2_words)) < 0.3:
            return False

        # Similar tags
        tags1 = set(item1.tags)
        tags2 = set(item2.tags)
        if tags1 and tags2:
            tag_overlap = len(tags1.intersection(tags2)) / len(tags1.union(tags2))
            return tag_overlap >= 0.5

        return True

    def _extract_pattern(
        self, feedback_group: List[FeedbackItem]
    ) -> Optional[FeedbackPattern]:
        """Extract a pattern from a group of similar feedback items."""
        if len(feedback_group) < 2:
            return None

        # Generate pattern ID
        pattern_type = feedback_group[0].type.value
        common_words = self._find_common_words(
            [item.description for item in feedback_group]
        )
        pattern_id = f"{pattern_type}_{hash('_'.join(sorted(common_words)))}"

        # Extract conditions and recommendations
        conditions = self._extract_conditions(feedback_group)
        recommendations = self._extract_recommendations(feedback_group)

        # Calculate confidence score
        confidence_score = min(
            len(feedback_group) / 10.0, 1.0
        )  # Max confidence at 10+ occurrences

        # Create pattern
        pattern = FeedbackPattern(
            pattern_id=pattern_id,
            pattern_type=pattern_type,
            description=self._generate_pattern_description(feedback_group),
            conditions=conditions,
            recommendations=recommendations,
            confidence_score=confidence_score,
            occurrences=len(feedback_group),
            last_seen=max(item.timestamp for item in feedback_group),
            examples=[
                item.description for item in feedback_group[:3]
            ],  # First 3 examples
        )

        return pattern

    def _find_common_words(self, texts: List[str]) -> List[str]:
        """Find common words across multiple texts."""
        if not texts:
            return []

        # Get words from all texts
        word_sets = [set(text.lower().split()) for text in texts]

        # Find intersection
        common_words = word_sets[0]
        for word_set in word_sets[1:]:
            common_words = common_words.intersection(word_set)

        # Filter out common English words
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
        }
        return [
            word for word in common_words if word not in stop_words and len(word) > 2
        ]

    def _extract_conditions(self, feedback_group: List[FeedbackItem]) -> List[str]:
        """Extract conditions that trigger this type of feedback."""
        conditions = []

        # Common file patterns
        file_paths = [item.file_path for item in feedback_group if item.file_path]
        if file_paths:
            extensions = set(Path(fp).suffix for fp in file_paths)
            if extensions:
                conditions.append(f"file_extension in {list(extensions)}")

        # Common code patterns (simplified)
        code_snippets = [
            item.code_snippet for item in feedback_group if item.code_snippet
        ]
        if code_snippets:
            common_patterns = self._find_code_patterns(code_snippets)
            conditions.extend(common_patterns)

        # Common tags
        all_tags = []
        for item in feedback_group:
            all_tags.extend(item.tags)

        if all_tags:
            from collections import Counter

            common_tags = [
                tag for tag, count in Counter(all_tags).most_common(3) if count > 1
            ]
            if common_tags:
                conditions.append(f"tags include {common_tags}")

        return conditions

    def _extract_recommendations(self, feedback_group: List[FeedbackItem]) -> List[str]:
        """Extract recommendations from feedback."""
        recommendations = []

        # Look for suggested fixes
        fixes = [item.suggested_fix for item in feedback_group if item.suggested_fix]
        if fixes:
            recommendations.extend(fixes[:3])  # Top 3 suggestions

        # Extract action words from descriptions
        action_patterns = [
            (r"\b(should|must|need to|consider)\s+(\w+(?:\s+\w+){0,3})", r"\2"),
            (r"\b(use|add|remove|change|fix|update)\s+(\w+(?:\s+\w+){0,2})", r"\1 \2"),
            (r"\b(avoid|prevent|ensure)\s+(\w+(?:\s+\w+){0,3})", r"\1 \2"),
        ]

        for item in feedback_group:
            for pattern, replacement in action_patterns:
                matches = re.findall(pattern, item.description, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        recommendation = f"{match[0]} {match[1]}"
                    else:
                        recommendation = match
                    if recommendation not in recommendations:
                        recommendations.append(recommendation)

        return recommendations[:5]  # Top 5 recommendations

    def _find_code_patterns(self, code_snippets: List[str]) -> List[str]:
        """Find common code patterns in snippets."""
        patterns = []

        # Look for common function calls
        function_calls = []
        for snippet in code_snippets:
            matches = re.findall(r"(\w+)\s*\(", snippet)
            function_calls.extend(matches)

        if function_calls:
            from collections import Counter

            common_functions = [
                func
                for func, count in Counter(function_calls).most_common(3)
                if count > 1
            ]
            if common_functions:
                patterns.append(f"function_calls include {common_functions}")

        return patterns

    def _generate_pattern_description(self, feedback_group: List[FeedbackItem]) -> str:
        """Generate a description for the pattern."""
        feedback_type = feedback_group[0].type.value.replace("_", " ").title()
        common_words = self._find_common_words(
            [item.description for item in feedback_group]
        )

        if common_words:
            description = (
                f"{feedback_type} pattern related to {', '.join(common_words[:3])}"
            )
        else:
            description = (
                f"{feedback_type} pattern with {len(feedback_group)} occurrences"
            )

        return description

    def _merge_patterns(
        self, existing: FeedbackPattern, new: FeedbackPattern
    ) -> FeedbackPattern:
        """Merge a new pattern with an existing one."""
        merged = FeedbackPattern(
            pattern_id=existing.pattern_id,
            pattern_type=existing.pattern_type,
            description=existing.description,
            conditions=list(set(existing.conditions + new.conditions)),
            recommendations=list(set(existing.recommendations + new.recommendations)),
            confidence_score=min(
                (existing.confidence_score + new.confidence_score) / 2, 1.0
            ),
            occurrences=existing.occurrences + new.occurrences,
            last_seen=max(existing.last_seen, new.last_seen),
            examples=list(set(existing.examples + new.examples))[
                :5
            ],  # Keep top 5 examples
        )

        return merged

    def get_relevant_patterns(self, context: Dict[str, Any]) -> List[FeedbackPattern]:
        """Get patterns relevant to a given context."""
        relevant_patterns = []

        for pattern in self.patterns.values():
            if self._is_pattern_relevant(pattern, context):
                relevant_patterns.append(pattern)

        # Sort by confidence and recency
        relevant_patterns.sort(
            key=lambda p: (p.confidence_score, p.last_seen), reverse=True
        )

        return relevant_patterns

    def _is_pattern_relevant(
        self, pattern: FeedbackPattern, context: Dict[str, Any]
    ) -> bool:
        """Check if a pattern is relevant to the given context."""
        # Check file extension
        file_path = context.get("file_path")
        if file_path:
            file_ext = Path(file_path).suffix
            for condition in pattern.conditions:
                if "file_extension" in condition and file_ext in condition:
                    return True

        # Check tags
        context_tags = context.get("tags", [])
        if context_tags:
            for condition in pattern.conditions:
                if "tags include" in condition:
                    pattern_tags = eval(condition.split("tags include ")[1])
                    if any(tag in context_tags for tag in pattern_tags):
                        return True

        return False


class FeedbackEngine:
    """Main feedback engine that orchestrates feedback ingestion and learning."""

    def __init__(self, storage_path: str = None):
        """
        Initialize feedback engine.

        Args:
            storage_path: Path to store feedback data and patterns
        """
        self.storage_path = (
            Path(storage_path) if storage_path else Path.cwd() / ".termnet" / "feedback"
        )
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.parser = FeedbackParser()
        self.learner = PatternLearner()
        self.logger = logging.getLogger(__name__)

        # Load existing patterns
        self._load_patterns()

    def ingest_github_review(self, review_data: Dict[str, Any]) -> List[FeedbackItem]:
        """Ingest GitHub review data."""
        self.logger.info(f"Ingesting GitHub review {review_data.get('id')}")

        feedback_items = self.parser.parse_github_review(review_data)
        self._store_feedback(feedback_items)

        # Learn patterns
        new_patterns = self.learner.learn_from_feedback(feedback_items)
        if new_patterns:
            self._store_patterns()
            self.logger.info(f"Learned {len(new_patterns)} new patterns")

        return feedback_items

    def ingest_test_results(self, test_results: Dict[str, Any]) -> List[FeedbackItem]:
        """Ingest test failure results."""
        self.logger.info("Ingesting test results")

        feedback_items = self.parser.parse_test_failures(test_results)
        self._store_feedback(feedback_items)

        # Learn patterns
        new_patterns = self.learner.learn_from_feedback(feedback_items)
        if new_patterns:
            self._store_patterns()
            self.logger.info(f"Learned {len(new_patterns)} new patterns")

        return feedback_items

    def ingest_user_corrections(
        self, corrections: List[Dict[str, Any]]
    ) -> List[FeedbackItem]:
        """Ingest user corrections."""
        self.logger.info(f"Ingesting {len(corrections)} user corrections")

        feedback_items = self.parser.parse_user_corrections(corrections)
        self._store_feedback(feedback_items)

        # Learn patterns
        new_patterns = self.learner.learn_from_feedback(feedback_items)
        if new_patterns:
            self._store_patterns()
            self.logger.info(f"Learned {len(new_patterns)} new patterns")

        return feedback_items

    def get_recommendations(self, context: Dict[str, Any]) -> List[str]:
        """Get recommendations based on learned patterns."""
        relevant_patterns = self.learner.get_relevant_patterns(context)

        recommendations = []
        for pattern in relevant_patterns[:5]:  # Top 5 patterns
            recommendations.extend(pattern.recommendations)

        # Remove duplicates while preserving order
        unique_recommendations = []
        seen = set()
        for rec in recommendations:
            if rec not in seen:
                unique_recommendations.append(rec)
                seen.add(rec)

        return unique_recommendations[:10]  # Top 10 recommendations

    def get_feedback_summary(self, days: int = 30) -> FeedbackSummary:
        """Get summary of feedback from the last N days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_feedback = self._load_recent_feedback(cutoff_date)

        # Count by type and severity
        type_counts = {}
        severity_counts = {}

        for item in recent_feedback:
            type_counts[item.type.value] = type_counts.get(item.type.value, 0) + 1
            severity_counts[item.severity.value] = (
                severity_counts.get(item.severity.value, 0) + 1
            )

        # Get top patterns
        top_patterns = sorted(
            self.learner.patterns.values(),
            key=lambda p: (p.confidence_score, p.occurrences),
            reverse=True,
        )[:10]

        # Generate improvement suggestions
        improvement_suggestions = self._generate_improvement_suggestions(
            recent_feedback, top_patterns
        )

        # Calculate overall confidence
        if top_patterns:
            confidence_score = sum(p.confidence_score for p in top_patterns) / len(
                top_patterns
            )
        else:
            confidence_score = 0.0

        return FeedbackSummary(
            total_feedback_items=len(recent_feedback),
            feedback_by_type=type_counts,
            feedback_by_severity=severity_counts,
            top_patterns=top_patterns,
            improvement_suggestions=improvement_suggestions,
            analysis_timestamp=datetime.now().isoformat(),
            confidence_score=confidence_score,
        )

    def _store_feedback(self, feedback_items: List[FeedbackItem]):
        """Store feedback items to disk."""
        for item in feedback_items:
            file_path = self.storage_path / "feedback" / f"{item.id}.json"
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert enums to strings for JSON serialization
            item_dict = asdict(item)
            item_dict["type"] = item.type.value
            item_dict["severity"] = item.severity.value

            with open(file_path, "w") as f:
                json.dump(item_dict, f, indent=2)

    def _store_patterns(self):
        """Store learned patterns to disk."""
        patterns_file = self.storage_path / "patterns.json"
        patterns_data = {
            pattern_id: asdict(pattern)
            for pattern_id, pattern in self.learner.patterns.items()
        }

        with open(patterns_file, "w") as f:
            json.dump(patterns_data, f, indent=2)

    def _load_patterns(self):
        """Load patterns from disk."""
        patterns_file = self.storage_path / "patterns.json"
        if patterns_file.exists():
            try:
                with open(patterns_file, "r") as f:
                    patterns_data = json.load(f)

                for pattern_id, pattern_dict in patterns_data.items():
                    pattern = FeedbackPattern(**pattern_dict)
                    self.learner.patterns[pattern_id] = pattern

                self.logger.info(f"Loaded {len(self.learner.patterns)} patterns")
            except Exception as e:
                self.logger.warning(f"Failed to load patterns: {e}")

    def _load_recent_feedback(self, cutoff_date: datetime) -> List[FeedbackItem]:
        """Load feedback items from the last N days."""
        feedback_items = []
        feedback_dir = self.storage_path / "feedback"

        if not feedback_dir.exists():
            return feedback_items

        for feedback_file in feedback_dir.glob("*.json"):
            try:
                with open(feedback_file, "r") as f:
                    data = json.load(f)

                # Convert enum strings back to enums
                data["type"] = FeedbackType(data["type"])
                data["severity"] = FeedbackSeverity(data["severity"])

                item = FeedbackItem(**data)
                # Handle timezone-aware/naive datetime comparison
                try:
                    item_timestamp = (
                        item.timestamp.replace("Z", "+00:00")
                        if "Z" in item.timestamp
                        else item.timestamp
                    )
                    item_date = datetime.fromisoformat(item_timestamp)

                    # Make cutoff_date timezone-aware if item_date is timezone-aware
                    if item_date.tzinfo is not None and cutoff_date.tzinfo is None:
                        import datetime as dt

                        cutoff_date = cutoff_date.replace(tzinfo=dt.timezone.utc)
                    elif item_date.tzinfo is None and cutoff_date.tzinfo is not None:
                        cutoff_date = cutoff_date.replace(tzinfo=None)

                except Exception:
                    # If datetime parsing fails, include the item
                    item_date = cutoff_date

                if item_date >= cutoff_date:
                    feedback_items.append(item)

            except Exception as e:
                self.logger.warning(
                    f"Failed to load feedback from {feedback_file}: {e}"
                )

        return feedback_items

    def _generate_improvement_suggestions(
        self, recent_feedback: List[FeedbackItem], top_patterns: List[FeedbackPattern]
    ) -> List[str]:
        """Generate improvement suggestions based on feedback and patterns."""
        suggestions = []

        # Analyze frequent issues
        if recent_feedback:
            type_counts = {}
            for item in recent_feedback:
                type_counts[item.type] = type_counts.get(item.type, 0) + 1

            most_common_type = max(type_counts, key=type_counts.get)
            suggestions.append(
                f"Focus on reducing {most_common_type.value.replace('_', ' ')} issues"
            )

        # Pattern-based suggestions
        for pattern in top_patterns[:3]:
            if pattern.confidence_score > 0.7:
                suggestions.append(f"Consider pattern: {pattern.description}")

        # Generic suggestions based on severity
        high_severity_count = sum(
            1
            for item in recent_feedback
            if item.severity in [FeedbackSeverity.HIGH, FeedbackSeverity.CRITICAL]
        )

        if high_severity_count > 5:
            suggestions.append(
                "Implement additional pre-commit checks to catch high-severity issues"
            )

        return suggestions[:5]  # Top 5 suggestions
