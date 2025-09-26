"""
File-Based Knowledge Store for TermNet
Stores and retrieves project knowledge, patterns, and insights
"""

import hashlib
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional


class CodebaseInsight:
    """Represents an insight about the codebase"""

    def __init__(self, insight_type: str, content: str, source_file: str = ""):
        self.id = hashlib.md5(
            f"{insight_type}_{content}_{datetime.now()}".encode()
        ).hexdigest()[:8]
        self.type = insight_type
        self.content = content
        self.source_file = source_file
        self.created_at = datetime.now().isoformat()
        self.tags = []

    def add_tag(self, tag: str):
        """Add a tag to this insight"""
        if tag not in self.tags:
            self.tags.append(tag)


class KnowledgeStore:
    """File-based knowledge management for TermNet/BMAD system"""

    def __init__(self, store_path: str = ".bmad-core/knowledge"):
        self.store_path = store_path
        self.insights: Dict[str, CodebaseInsight] = {}
        self.patterns: Dict[str, Any] = {}
        self.project_metadata = {}

        # Ensure store directory exists
        os.makedirs(self.store_path, exist_ok=True)

        # Load existing knowledge
        self.load_knowledge()

    def add_insight(
        self,
        insight_type: str,
        content: str,
        source_file: str = "",
        tags: List[str] = None,
    ) -> str:
        """Add a new insight to the knowledge store"""
        insight = CodebaseInsight(insight_type, content, source_file)

        if tags:
            for tag in tags:
                insight.add_tag(tag)

        self.insights[insight.id] = insight
        self.save_insights()

        print(f"💡 Added insight: {insight_type} ({insight.id})")
        return insight.id

    def add_pattern(self, pattern_name: str, pattern_data: Dict[str, Any]):
        """Add a code pattern to the store"""
        self.patterns[pattern_name] = {
            "data": pattern_data,
            "created_at": datetime.now().isoformat(),
        }
        self.save_patterns()
        print(f"🔄 Added pattern: {pattern_name}")

    def search_insights(
        self, query: str, insight_type: str = None
    ) -> List[CodebaseInsight]:
        """Search insights by content or type"""
        results = []
        query_lower = query.lower()

        for insight in self.insights.values():
            if insight_type and insight.type != insight_type:
                continue

            if (
                query_lower in insight.content.lower()
                or query_lower in insight.source_file.lower()
                or any(query_lower in tag.lower() for tag in insight.tags)
            ):
                results.append(insight)

        return results

    def get_insights_by_type(self, insight_type: str) -> List[CodebaseInsight]:
        """Get all insights of a specific type"""
        return [
            insight
            for insight in self.insights.values()
            if insight.type == insight_type
        ]

    def analyze_codebase(self, project_path: str) -> Dict[str, Any]:
        """Analyze codebase and extract insights"""
        analysis = {
            "files_analyzed": 0,
            "python_files": 0,
            "total_lines": 0,
            "insights_generated": 0,
        }

        # Analyze Python files in the project
        for root, dirs, files in os.walk(project_path):
            # Skip common ignore directories
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".") and d not in ["__pycache__", "node_modules"]
            ]

            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, project_path)

                    analysis["python_files"] += 1

                    # Simple analysis - count lines and look for patterns
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            lines = content.split("\n")
                            analysis["total_lines"] += len(lines)

                            # Extract simple insights
                            if "class " in content:
                                classes = [
                                    line.strip()
                                    for line in lines
                                    if line.strip().startswith("class ")
                                ]
                                if classes:
                                    self.add_insight(
                                        "class_definition",
                                        f"Classes found: {', '.join(classes[:3])}",
                                        relative_path,
                                        ["python", "classes"],
                                    )
                                    analysis["insights_generated"] += 1

                            if "def " in content and "async def" in content:
                                self.add_insight(
                                    "async_pattern",
                                    f"File uses both sync and async functions",
                                    relative_path,
                                    ["python", "async", "pattern"],
                                )
                                analysis["insights_generated"] += 1

                            if "import " in content:
                                imports = [
                                    line.strip()
                                    for line in lines
                                    if line.strip().startswith("import ")
                                    or line.strip().startswith("from ")
                                ][:5]
                                if imports:
                                    self.add_insight(
                                        "imports",
                                        f"Key imports: {'; '.join(imports)}",
                                        relative_path,
                                        ["python", "dependencies"],
                                    )

                    except Exception as e:
                        continue

                analysis["files_analyzed"] += 1

        print(f"📊 Codebase analysis complete: {analysis}")
        return analysis

    def save_insights(self):
        """Save insights to file"""
        insights_data = {
            insight_id: {
                "type": insight.type,
                "content": insight.content,
                "source_file": insight.source_file,
                "created_at": insight.created_at,
                "tags": insight.tags,
            }
            for insight_id, insight in self.insights.items()
        }

        with open(f"{self.store_path}/insights.json", "w") as f:
            json.dump(insights_data, f, indent=2)

    def save_patterns(self):
        """Save patterns to file"""
        with open(f"{self.store_path}/patterns.json", "w") as f:
            json.dump(self.patterns, f, indent=2)

    def load_knowledge(self):
        """Load existing knowledge from files"""
        # Load insights
        insights_file = f"{self.store_path}/insights.json"
        if os.path.exists(insights_file):
            try:
                with open(insights_file, "r") as f:
                    insights_data = json.load(f)

                for insight_id, data in insights_data.items():
                    insight = CodebaseInsight(
                        data["type"], data["content"], data.get("source_file", "")
                    )
                    insight.id = insight_id
                    insight.created_at = data.get("created_at", "")
                    insight.tags = data.get("tags", [])
                    self.insights[insight_id] = insight

                print(f"📚 Loaded {len(self.insights)} insights")
            except Exception as e:
                print(f"⚠️ Error loading insights: {e}")

        # Load patterns
        patterns_file = f"{self.store_path}/patterns.json"
        if os.path.exists(patterns_file):
            try:
                with open(patterns_file, "r") as f:
                    self.patterns = json.load(f)
                print(f"🔄 Loaded {len(self.patterns)} patterns")
            except Exception as e:
                print(f"⚠️ Error loading patterns: {e}")

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of knowledge store"""
        insight_types = {}
        for insight in self.insights.values():
            insight_types[insight.type] = insight_types.get(insight.type, 0) + 1

        return {
            "total_insights": len(self.insights),
            "insight_types": insight_types,
            "total_patterns": len(self.patterns),
            "store_path": self.store_path,
        }
