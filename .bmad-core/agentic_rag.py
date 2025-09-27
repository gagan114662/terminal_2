"""
Agentic RAG - Active Reasoning and Retrieval System
Implements intelligent search and analysis for autonomous development
"""

import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class CodeSearchResult:
    """Result from code search operation"""

    file_path: str
    content: str
    relevance_score: float
    context_type: str  # "class", "function", "import", "comment", etc.
    line_numbers: tuple[int, int]  # start, end


@dataclass
class RAGQuery:
    """Structured query for RAG system"""

    query: str
    intent: str  # "find_implementation", "understand_pattern", "locate_dependencies"
    scope: str  # "local", "project", "dependencies"
    filters: dict[str, Any]


class CodeSearchEngine:
    """File-based semantic code search engine"""

    def __init__(self, project_path: str = "."):
        self.project_path = project_path
        self.file_index = {}
        self.pattern_cache = {}
        self._build_index()

    def _build_index(self):
        """Build searchable index of project files"""
        for root, dirs, files in os.walk(self.project_path):
            # Skip common ignore patterns
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".")
                and d not in ["__pycache__", "node_modules", "venv"]
            ]

            for file in files:
                if file.endswith((".py", ".js", ".ts", ".java", ".go", ".rs")):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, self.project_path)

                    try:
                        with open(file_path, encoding="utf-8") as f:
                            content = f.read()
                            self.file_index[relative_path] = {
                                "content": content,
                                "lines": content.split("\n"),
                                "size": len(content),
                                "modified": os.path.getmtime(file_path),
                            }
                    except Exception:
                        continue

    def search_implementations(
        self, query: str, file_types: list[str] = None
    ) -> list[CodeSearchResult]:
        """Search for code implementations matching query"""
        results = []
        search_terms = query.lower().split()

        for file_path, file_data in self.file_index.items():
            if file_types and not any(file_path.endswith(ft) for ft in file_types):
                continue

            content = file_data["content"]
            lines = file_data["lines"]

            # Search for class definitions
            class_matches = self._find_classes(lines, search_terms)
            results.extend(
                [
                    CodeSearchResult(
                        file_path=file_path,
                        content=match["content"],
                        relevance_score=match["score"],
                        context_type="class",
                        line_numbers=(match["start"], match["end"]),
                    )
                    for match in class_matches
                ]
            )

            # Search for function definitions
            func_matches = self._find_functions(lines, search_terms)
            results.extend(
                [
                    CodeSearchResult(
                        file_path=file_path,
                        content=match["content"],
                        relevance_score=match["score"],
                        context_type="function",
                        line_numbers=(match["start"], match["end"]),
                    )
                    for match in func_matches
                ]
            )

            # Search for imports/dependencies
            import_matches = self._find_imports(lines, search_terms)
            results.extend(
                [
                    CodeSearchResult(
                        file_path=file_path,
                        content=match["content"],
                        relevance_score=match["score"],
                        context_type="import",
                        line_numbers=(match["line"], match["line"]),
                    )
                    for match in import_matches
                ]
            )

        # Sort by relevance score
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:20]  # Return top 20 results

    def _find_classes(self, lines: list[str], search_terms: list[str]) -> list[dict]:
        """Find class definitions matching search terms"""
        matches = []

        for i, line in enumerate(lines):
            if re.match(r"^\s*class\s+\w+", line):
                # Calculate relevance score
                score = 0
                line_lower = line.lower()
                for term in search_terms:
                    if term in line_lower:
                        score += 1

                if score > 0:
                    # Get class body (basic implementation)
                    end_line = min(i + 10, len(lines))  # Get next 10 lines as context
                    content = "\n".join(lines[i:end_line])

                    matches.append(
                        {
                            "content": content,
                            "score": score,
                            "start": i + 1,
                            "end": end_line,
                        }
                    )

        return matches

    def _find_functions(self, lines: list[str], search_terms: list[str]) -> list[dict]:
        """Find function definitions matching search terms"""
        matches = []

        for i, line in enumerate(lines):
            if re.match(r"^\s*(def|function|func)\s+\w+", line):
                score = 0
                line_lower = line.lower()
                for term in search_terms:
                    if term in line_lower:
                        score += 1

                if score > 0:
                    end_line = min(i + 5, len(lines))
                    content = "\n".join(lines[i:end_line])

                    matches.append(
                        {
                            "content": content,
                            "score": score,
                            "start": i + 1,
                            "end": end_line,
                        }
                    )

        return matches

    def _find_imports(self, lines: list[str], search_terms: list[str]) -> list[dict]:
        """Find import statements matching search terms"""
        matches = []

        for i, line in enumerate(lines):
            if re.match(r"^\s*(import|from)\s+", line):
                score = 0
                line_lower = line.lower()
                for term in search_terms:
                    if term in line_lower:
                        score += 1

                if score > 0:
                    matches.append(
                        {"content": line.strip(), "score": score, "line": i + 1}
                    )

        return matches


class AgenticRAG:
    """Agentic RAG system with active reasoning and retrieval"""

    def __init__(self, project_path: str = "."):
        self.project_path = project_path
        self.search_engine = CodeSearchEngine(project_path)
        self.query_history = []
        self.reasoning_steps = []

    def reason_and_retrieve(
        self, user_query: str, context: dict = None
    ) -> dict[str, Any]:
        """Main agentic RAG process: reason about what to search, then retrieve"""

        # Step 1: Analyze the query and determine search strategy
        rag_query = self._analyze_query(user_query, context)

        # Step 2: Reason about what information is needed
        reasoning = self._generate_reasoning_plan(rag_query)

        # Step 3: Execute search based on reasoning
        search_results = self._execute_search(rag_query, reasoning)

        # Step 4: Synthesize findings
        synthesis = self._synthesize_results(user_query, search_results, reasoning)

        # Store for future reference
        self.query_history.append(
            {
                "query": user_query,
                "rag_query": rag_query,
                "reasoning": reasoning,
                "results_count": len(search_results),
                "synthesis": synthesis,
                "timestamp": datetime.now().isoformat(),
            }
        )

        return {
            "original_query": user_query,
            "reasoning_plan": reasoning,
            "search_results": search_results,
            "synthesis": synthesis,
            "confidence_score": self._calculate_confidence(search_results),
        }

    def _analyze_query(self, query: str, context: dict = None) -> RAGQuery:
        """Analyze user query to determine search intent and parameters"""
        query_lower = query.lower()

        # Determine intent
        if any(word in query_lower for word in ["implement", "create", "build", "add"]):
            intent = "find_implementation"
        elif any(
            word in query_lower for word in ["understand", "explain", "how", "why"]
        ):
            intent = "understand_pattern"
        elif any(
            word in query_lower for word in ["import", "dependency", "require", "use"]
        ):
            intent = "locate_dependencies"
        else:
            intent = "general_search"

        # Determine scope
        if any(word in query_lower for word in ["external", "library", "package"]):
            scope = "dependencies"
        elif any(word in query_lower for word in ["project", "codebase", "system"]):
            scope = "project"
        else:
            scope = "local"

        # Extract filters
        filters = {}
        if "python" in query_lower:
            filters["file_types"] = [".py"]
        elif "javascript" in query_lower or "js" in query_lower:
            filters["file_types"] = [".js", ".ts"]

        return RAGQuery(query=query, intent=intent, scope=scope, filters=filters)

    def _generate_reasoning_plan(self, rag_query: RAGQuery) -> list[str]:
        """Generate reasoning steps for what information to search for"""
        reasoning = []

        reasoning.append(f"Query intent: {rag_query.intent}")
        reasoning.append(f"Search scope: {rag_query.scope}")

        if rag_query.intent == "find_implementation":
            reasoning.extend(
                [
                    "Need to find existing implementations or similar patterns",
                    "Look for class definitions and method implementations",
                    "Check for related utility functions and helpers",
                ]
            )
        elif rag_query.intent == "understand_pattern":
            reasoning.extend(
                [
                    "Need to understand how something works in the codebase",
                    "Look for examples and usage patterns",
                    "Find documentation or comments explaining the pattern",
                ]
            )
        elif rag_query.intent == "locate_dependencies":
            reasoning.extend(
                [
                    "Need to find import statements and dependencies",
                    "Look for package usage and external libraries",
                    "Check configuration files and requirements",
                ]
            )

        return reasoning

    def _execute_search(
        self, rag_query: RAGQuery, reasoning: list[str]
    ) -> list[CodeSearchResult]:
        """Execute search based on query and reasoning"""
        file_types = rag_query.filters.get("file_types")
        return self.search_engine.search_implementations(rag_query.query, file_types)

    def _synthesize_results(
        self, original_query: str, results: list[CodeSearchResult], reasoning: list[str]
    ) -> str:
        """Synthesize search results into actionable insights"""
        if not results:
            return f"No relevant code found for '{original_query}'. Consider implementing from scratch."

        synthesis = (
            f"Found {len(results)} relevant code references for '{original_query}':\n\n"
        )

        # Group by context type
        by_type = {}
        for result in results:
            if result.context_type not in by_type:
                by_type[result.context_type] = []
            by_type[result.context_type].append(result)

        for context_type, type_results in by_type.items():
            synthesis += (
                f"**{context_type.title()} Definitions ({len(type_results)}):**\n"
            )
            for result in type_results[:3]:  # Top 3 per type
                synthesis += f"- {result.file_path}:{result.line_numbers[0]} (score: {result.relevance_score})\n"
            synthesis += "\n"

        return synthesis

    def _calculate_confidence(self, results: list[CodeSearchResult]) -> float:
        """Calculate confidence score for the search results"""
        if not results:
            return 0.0

        # Simple confidence based on number of results and average score
        avg_score = sum(r.relevance_score for r in results) / len(results)
        result_count_factor = min(len(results) / 10.0, 1.0)  # Max factor of 1.0

        return min(avg_score * result_count_factor, 1.0)

    def get_terminal_verification_commands(self) -> list[str]:
        """Get terminal commands to verify RAG system functionality"""
        return [
            "echo '🔍 Testing Agentic RAG System'",
            "python3 -c \"import sys; sys.path.insert(0,'.bmad-core'); from agentic_rag import AgenticRAG; rag=AgenticRAG(); print('✅ RAG system initialized')\"",
            "python3 -c \"import sys; sys.path.insert(0,'.bmad-core'); from agentic_rag import AgenticRAG; rag=AgenticRAG(); print('📁 Files indexed:', len(rag.search_engine.file_index))\"",
            "python3 -c \"import sys; sys.path.insert(0,'.bmad-core'); from agentic_rag import AgenticRAG; rag=AgenticRAG(); result=rag.reason_and_retrieve('find authentication implementation'); print('🔍 Search results:', len(result['search_results']), 'confidence:', result['confidence_score'])\"",
        ]
