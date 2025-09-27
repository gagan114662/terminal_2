"""
RAG Query Processor with ReAct Integration
Combines reasoning, search, and action for intelligent code analysis
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from typing import Any

from agentic_rag import AgenticRAG, CodeSearchResult
from react_framework import ReActFramework


class RAGProcessor:
    """Processes queries using ReAct reasoning with RAG retrieval"""

    def __init__(self, project_path: str = "."):
        self.rag = AgenticRAG(project_path)
        self.react = ReActFramework()
        self.query_cache = {}

    def process_development_query(
        self, query: str, context: dict = None
    ) -> dict[str, Any]:
        """Process a development query using ReAct + RAG"""

        # Initialize ReAct chain
        self.react.set_goal(f"Research and analyze: {query}")

        # Step 1: Initial reasoning about the query
        self.react.add_thought(
            f"I need to research '{query}' in the codebase. Let me break this down into searchable components."
        )

        # Step 2: Action - analyze query structure
        self.react.add_action("Analyze query intent and scope", f"Analyzing: {query}")

        # Get initial RAG analysis
        rag_result = self.rag.reason_and_retrieve(query, context)

        # Step 3: Observation - what did we find?
        observation = f"Found {len(rag_result['search_results'])} relevant code references. Confidence: {rag_result['confidence_score']:.2f}"
        self.react.add_observation(observation)

        # Step 4: Reasoning about next steps based on findings
        if rag_result["confidence_score"] > 0.7:
            self.react.add_thought(
                "High confidence results found. I should analyze the top findings for patterns and implementation details."
            )
            next_action = "Analyze high-confidence search results"
        elif rag_result["confidence_score"] > 0.3:
            self.react.add_thought(
                "Moderate confidence results. I should broaden the search and look for related patterns."
            )
            next_action = "Broaden search scope and find related patterns"
        else:
            self.react.add_thought(
                "Low confidence results. This might be a new implementation area. I should identify what needs to be created."
            )
            next_action = "Identify implementation requirements for new feature"

        # Step 5: Execute refined search based on reasoning
        refined_results = self._execute_refined_search(query, rag_result, next_action)

        # Step 6: Final synthesis with reasoning chain
        synthesis = self._synthesize_with_reasoning(query, rag_result, refined_results)

        return {
            "original_query": query,
            "reasoning_chain": self.react.get_reasoning_chain(),
            "rag_analysis": rag_result,
            "refined_results": refined_results,
            "final_synthesis": synthesis,
            "actionable_insights": self._generate_actionable_insights(
                query, rag_result, refined_results
            ),
        }

    def _execute_refined_search(
        self, query: str, initial_results: dict, action: str
    ) -> dict[str, Any]:
        """Execute refined search based on initial findings and reasoning"""

        if "high-confidence" in action.lower():
            # Focus on top results and find related implementations
            top_files = set()
            for result in initial_results["search_results"][:5]:
                top_files.add(result.file_path)

            # Search for related patterns in these files
            related_query = self._generate_related_query(
                query, initial_results["search_results"][:3]
            )
            related_results = self.rag.reason_and_retrieve(related_query)

            return {
                "type": "focused_analysis",
                "top_files": list(top_files),
                "related_results": related_results,
                "focus_area": "existing implementations",
            }

        elif "broaden" in action.lower():
            # Broaden search with related terms
            broader_terms = self._extract_broader_terms(query)
            broader_results = []

            for term in broader_terms:
                term_results = self.rag.reason_and_retrieve(term)
                broader_results.extend(term_results["search_results"])

            return {
                "type": "broader_search",
                "search_terms": broader_terms,
                "broader_results": broader_results[:10],
                "focus_area": "related patterns",
            }

        else:
            # New implementation analysis
            dependencies = self._find_potential_dependencies(query)
            similar_implementations = self._find_similar_implementations(query)

            return {
                "type": "new_implementation",
                "potential_dependencies": dependencies,
                "similar_patterns": similar_implementations,
                "focus_area": "requirements analysis",
            }

    def _generate_related_query(
        self, original_query: str, top_results: list[CodeSearchResult]
    ) -> str:
        """Generate related search query based on top results"""
        # Extract key terms from top results
        key_terms = set()
        for result in top_results:
            # Simple extraction of class/function names
            content_lower = result.content.lower()
            if "class" in content_lower:
                key_terms.add("class methods")
            if "def" in content_lower:
                key_terms.add("helper functions")
            if "import" in content_lower:
                key_terms.add("dependencies")

        return f"related to {original_query}: {' '.join(key_terms)}"

    def _extract_broader_terms(self, query: str) -> list[str]:
        """Extract broader search terms from original query"""
        words = query.lower().split()
        broader_terms = []

        # Add individual significant words
        significant_words = [
            w for w in words if len(w) > 3 and w not in ["with", "from", "that", "this"]
        ]
        broader_terms.extend(significant_words)

        # Add common related terms based on context
        if "auth" in query.lower():
            broader_terms.extend(["login", "user", "token", "session"])
        if "api" in query.lower():
            broader_terms.extend(["endpoint", "route", "request", "response"])
        if "database" in query.lower():
            broader_terms.extend(["model", "table", "query", "orm"])

        return broader_terms[:5]  # Limit to 5 terms

    def _find_potential_dependencies(self, query: str) -> list[str]:
        """Find potential dependencies for new implementation"""
        # Search for common patterns that might be dependencies
        dependency_results = self.rag.search_engine.search_implementations(
            "import", [".py"]
        )

        dependencies = []
        for result in dependency_results[:10]:
            if result.context_type == "import":
                dependencies.append(result.content.strip())

        return dependencies

    def _find_similar_implementations(self, query: str) -> list[CodeSearchResult]:
        """Find similar implementations in the codebase"""
        # Extract key concepts and search for similar patterns
        words = query.lower().split()
        for word in words:
            if len(word) > 4:  # Use longer words for similarity search
                results = self.rag.search_engine.search_implementations(word, [".py"])
                if results:
                    return results[:3]

        return []

    def _synthesize_with_reasoning(
        self, query: str, rag_result: dict, refined_results: dict
    ) -> str:
        """Synthesize findings with reasoning chain"""
        synthesis = f"## Analysis of: {query}\n\n"

        synthesis += "**Reasoning Process:**\n"
        synthesis += (
            f"- Initial search found {len(rag_result['search_results'])} results\n"
        )
        synthesis += f"- Confidence level: {rag_result['confidence_score']:.2f}\n"
        synthesis += f"- Refined analysis type: {refined_results['type']}\n\n"

        synthesis += "**Key Findings:**\n"
        if rag_result["search_results"]:
            synthesis += f"- Existing implementations found in {len(set(r.file_path for r in rag_result['search_results']))} files\n"
            synthesis += f"- Primary context types: {', '.join(set(r.context_type for r in rag_result['search_results']))}\n"

        synthesis += "\n**Recommendation:**\n"
        if rag_result["confidence_score"] > 0.7:
            synthesis += "High confidence - use existing patterns as reference for implementation.\n"
        elif rag_result["confidence_score"] > 0.3:
            synthesis += "Moderate confidence - adapt existing patterns or create new implementation.\n"
        else:
            synthesis += (
                "Low confidence - likely needs new implementation from scratch.\n"
            )

        return synthesis

    def _generate_actionable_insights(
        self, query: str, rag_result: dict, refined_results: dict
    ) -> list[str]:
        """Generate actionable insights for developers"""
        insights = []

        if rag_result["search_results"]:
            # Top files to examine
            top_files = list(set(r.file_path for r in rag_result["search_results"][:5]))
            insights.append(
                f"Examine these files for reference: {', '.join(top_files)}"
            )

            # Key patterns found
            context_types = list(
                set(r.context_type for r in rag_result["search_results"])
            )
            insights.append(f"Focus on these code elements: {', '.join(context_types)}")

        if refined_results["type"] == "new_implementation":
            insights.append("Consider these dependencies for new implementation")
            if "potential_dependencies" in refined_results:
                insights.extend(refined_results["potential_dependencies"][:3])

        # Add terminal commands for verification
        insights.append("Verify findings with: grep -r 'key_term' --include='*.py' .")

        return insights

    def get_verification_commands(self) -> list[str]:
        """Get terminal commands to verify RAG processor functionality"""
        return [
            "echo '🧠 Testing RAG Processor with ReAct'",
            "python3 -c \"import sys; sys.path.insert(0,'.bmad-core'); from rag_processor import RAGProcessor; rp=RAGProcessor(); print('✅ RAG Processor initialized')\"",
            "python3 -c \"import sys; sys.path.insert(0,'.bmad-core'); from rag_processor import RAGProcessor; rp=RAGProcessor(); result=rp.process_development_query('implement user authentication'); print('🔍 Reasoning steps:', len(result['reasoning_chain'].split('Step')))\"",
            "python3 -c \"import sys; sys.path.insert(0,'.bmad-core'); from rag_processor import RAGProcessor; rp=RAGProcessor(); result=rp.process_development_query('database models'); print('💡 Insights:', len(result['actionable_insights']))\"",
        ]
