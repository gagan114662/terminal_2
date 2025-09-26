"""
Advanced Code Analysis Tools for Agentic RAG
Semantic analysis, dependency mapping, and pattern recognition
"""

import ast
import json
import os
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class CodeEntity:
    """Represents a code entity (class, function, variable, etc.)"""

    name: str
    type: str  # 'class', 'function', 'variable', 'import'
    file_path: str
    line_number: int
    dependencies: List[str]
    docstring: Optional[str] = None
    complexity: int = 0


@dataclass
class DependencyMap:
    """Maps dependencies between code entities"""

    imports: Dict[str, List[str]]  # file -> [imported modules]
    functions: Dict[str, List[str]]  # file -> [function names]
    classes: Dict[str, List[str]]  # file -> [class names]
    cross_references: Dict[str, List[str]]  # entity -> [entities that use it]


class CodeAnalyzer:
    """Advanced code analysis for semantic understanding"""

    def __init__(self, project_path: str = "."):
        self.project_path = project_path
        self.entities: List[CodeEntity] = []
        self.dependency_map = DependencyMap({}, {}, {}, {})
        self.file_metrics = {}

    def analyze_project(self) -> Dict[str, Any]:
        """Perform comprehensive project analysis"""
        analysis_results = {
            "files_analyzed": 0,
            "entities_found": 0,
            "dependency_graph": {},
            "complexity_metrics": {},
            "patterns_identified": [],
            "potential_issues": [],
        }

        # Analyze Python files
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".")
                and d not in ["__pycache__", "node_modules", "venv"]
            ]

            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, self.project_path)

                    try:
                        file_analysis = self._analyze_python_file(
                            file_path, relative_path
                        )
                        analysis_results["files_analyzed"] += 1
                        analysis_results["entities_found"] += len(
                            file_analysis["entities"]
                        )

                        # Update dependency map
                        if file_analysis["imports"]:
                            self.dependency_map.imports[relative_path] = file_analysis[
                                "imports"
                            ]
                        if file_analysis["functions"]:
                            self.dependency_map.functions[
                                relative_path
                            ] = file_analysis["functions"]
                        if file_analysis["classes"]:
                            self.dependency_map.classes[relative_path] = file_analysis[
                                "classes"
                            ]

                    except Exception as e:
                        analysis_results["potential_issues"].append(
                            f"Error analyzing {relative_path}: {str(e)}"
                        )

        # Build cross-references
        self._build_cross_references()

        # Identify patterns
        analysis_results["patterns_identified"] = self._identify_patterns()

        # Calculate complexity metrics
        analysis_results["complexity_metrics"] = self._calculate_complexity_metrics()

        return analysis_results

    def _analyze_python_file(
        self, file_path: str, relative_path: str
    ) -> Dict[str, Any]:
        """Analyze a single Python file using AST"""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        try:
            tree = ast.parse(content, filename=relative_path)
        except SyntaxError:
            return {"entities": [], "imports": [], "functions": [], "classes": []}

        analysis = {"entities": [], "imports": [], "functions": [], "classes": []}

        # Walk the AST
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    analysis["imports"].append(alias.name)
                    entity = CodeEntity(
                        name=alias.name,
                        type="import",
                        file_path=relative_path,
                        line_number=node.lineno,
                        dependencies=[],
                    )
                    analysis["entities"].append(entity)

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    analysis["imports"].append(node.module)
                    for alias in node.names:
                        entity = CodeEntity(
                            name=f"{node.module}.{alias.name}",
                            type="import",
                            file_path=relative_path,
                            line_number=node.lineno,
                            dependencies=[],
                        )
                        analysis["entities"].append(entity)

            elif isinstance(node, ast.FunctionDef):
                analysis["functions"].append(node.name)
                docstring = ast.get_docstring(node)

                # Calculate basic complexity (number of nodes)
                complexity = len(list(ast.walk(node)))

                entity = CodeEntity(
                    name=node.name,
                    type="function",
                    file_path=relative_path,
                    line_number=node.lineno,
                    dependencies=self._extract_function_dependencies(node),
                    docstring=docstring,
                    complexity=complexity,
                )
                analysis["entities"].append(entity)

            elif isinstance(node, ast.ClassDef):
                analysis["classes"].append(node.name)
                docstring = ast.get_docstring(node)

                # Calculate class complexity
                complexity = len(list(ast.walk(node)))

                entity = CodeEntity(
                    name=node.name,
                    type="class",
                    file_path=relative_path,
                    line_number=node.lineno,
                    dependencies=self._extract_class_dependencies(node),
                    docstring=docstring,
                    complexity=complexity,
                )
                analysis["entities"].append(entity)

        self.entities.extend(analysis["entities"])
        return analysis

    def _extract_function_dependencies(self, func_node: ast.FunctionDef) -> List[str]:
        """Extract dependencies from function node"""
        dependencies = []

        for node in ast.walk(func_node):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                # This is a variable being used
                if node.id not in ["self", "cls"] and not node.id.startswith("__"):
                    dependencies.append(node.id)
            elif isinstance(node, ast.Attribute):
                # This is an attribute access like obj.method
                if isinstance(node.value, ast.Name):
                    dependencies.append(f"{node.value.id}.{node.attr}")

        return list(set(dependencies))  # Remove duplicates

    def _extract_class_dependencies(self, class_node: ast.ClassDef) -> List[str]:
        """Extract dependencies from class node"""
        dependencies = []

        # Base classes
        for base in class_node.bases:
            if isinstance(base, ast.Name):
                dependencies.append(base.id)

        # Dependencies from methods
        for node in ast.walk(class_node):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                if node.id not in ["self", "cls"] and not node.id.startswith("__"):
                    dependencies.append(node.id)

        return list(set(dependencies))

    def _build_cross_references(self):
        """Build cross-reference map of entity usage"""
        cross_refs = defaultdict(list)

        for entity in self.entities:
            for dep in entity.dependencies:
                # Find entities that match this dependency
                matching_entities = [
                    e
                    for e in self.entities
                    if e.name == dep or e.name.endswith(f".{dep}")
                ]
                for match in matching_entities:
                    cross_refs[match.name].append(entity.name)

        self.dependency_map.cross_references = dict(cross_refs)

    def _identify_patterns(self) -> List[Dict[str, Any]]:
        """Identify common code patterns"""
        patterns = []

        # Pattern 1: Classes with many dependencies (potential refactoring candidates)
        high_dependency_classes = [
            e for e in self.entities if e.type == "class" and len(e.dependencies) > 10
        ]
        if high_dependency_classes:
            patterns.append(
                {
                    "type": "high_coupling",
                    "description": "Classes with high dependencies",
                    "entities": [e.name for e in high_dependency_classes],
                    "severity": "medium",
                }
            )

        # Pattern 2: Functions with high complexity
        complex_functions = [
            e for e in self.entities if e.type == "function" and e.complexity > 100
        ]
        if complex_functions:
            patterns.append(
                {
                    "type": "high_complexity",
                    "description": "Functions with high complexity",
                    "entities": [e.name for e in complex_functions],
                    "severity": "high",
                }
            )

        # Pattern 3: Common import patterns
        import_counts = defaultdict(int)
        for entity in self.entities:
            if entity.type == "import":
                base_module = entity.name.split(".")[0]
                import_counts[base_module] += 1

        common_imports = [
            (module, count) for module, count in import_counts.items() if count > 3
        ]
        if common_imports:
            patterns.append(
                {
                    "type": "common_dependencies",
                    "description": "Frequently used modules",
                    "entities": dict(common_imports),
                    "severity": "info",
                }
            )

        return patterns

    def _calculate_complexity_metrics(self) -> Dict[str, Any]:
        """Calculate various complexity metrics"""
        metrics = {
            "total_entities": len(self.entities),
            "avg_function_complexity": 0,
            "avg_class_complexity": 0,
            "max_dependencies": 0,
            "files_with_high_complexity": [],
        }

        functions = [e for e in self.entities if e.type == "function"]
        classes = [e for e in self.entities if e.type == "class"]

        if functions:
            metrics["avg_function_complexity"] = sum(
                e.complexity for e in functions
            ) / len(functions)

        if classes:
            metrics["avg_class_complexity"] = sum(e.complexity for e in classes) / len(
                classes
            )

        if self.entities:
            metrics["max_dependencies"] = max(
                len(e.dependencies) for e in self.entities
            )

        # Identify files with high complexity
        file_complexity = defaultdict(int)
        for entity in self.entities:
            file_complexity[entity.file_path] += entity.complexity

        high_complexity_files = [(f, c) for f, c in file_complexity.items() if c > 500]
        metrics["files_with_high_complexity"] = high_complexity_files

        return metrics

    def semantic_search(
        self, query: str, entity_types: List[str] = None
    ) -> List[CodeEntity]:
        """Perform semantic search across analyzed entities"""
        query_terms = query.lower().split()
        results = []

        for entity in self.entities:
            if entity_types and entity.type not in entity_types:
                continue

            # Calculate relevance score
            score = 0

            # Name matching
            entity_name_lower = entity.name.lower()
            for term in query_terms:
                if term in entity_name_lower:
                    score += 2

            # Docstring matching
            if entity.docstring:
                docstring_lower = entity.docstring.lower()
                for term in query_terms:
                    if term in docstring_lower:
                        score += 1

            # Dependency matching
            for dep in entity.dependencies:
                dep_lower = dep.lower()
                for term in query_terms:
                    if term in dep_lower:
                        score += 0.5

            if score > 0:
                # Add score as attribute for sorting
                entity.search_score = score
                results.append(entity)

        # Sort by relevance score
        results.sort(key=lambda x: x.search_score, reverse=True)
        return results[:20]  # Return top 20

    def get_verification_commands(self) -> List[str]:
        """Get terminal commands to verify code analyzer"""
        return [
            "echo '📊 Testing Code Analyzer'",
            "python3 -c \"import sys; sys.path.insert(0,'.bmad-core'); from code_analyzer import CodeAnalyzer; ca=CodeAnalyzer(); print('✅ Code Analyzer initialized')\"",
            "python3 -c \"import sys; sys.path.insert(0,'.bmad-core'); from code_analyzer import CodeAnalyzer; ca=CodeAnalyzer(); results=ca.analyze_project(); print('📈 Analysis:', results['files_analyzed'], 'files,', results['entities_found'], 'entities')\"",
            "python3 -c \"import sys; sys.path.insert(0,'.bmad-core'); from code_analyzer import CodeAnalyzer; ca=CodeAnalyzer(); ca.analyze_project(); results=ca.semantic_search('authentication class'); print('🔍 Semantic search:', len(results), 'relevant entities')\"",
        ]
