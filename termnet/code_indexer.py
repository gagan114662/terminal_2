"""
TermNet Code Indexer

Builds searchable index of repository code for autonomous planning and editing.
Follows Google AI best practices: offline-first, deterministic, fast search.
"""

import fnmatch
import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class CodeSymbol:
    """Represents a code symbol (function, class, variable, etc.)."""

    name: str
    type: str  # "function", "class", "variable", "import"
    file_path: str
    line_number: int
    signature: str = ""
    docstring: str = ""


@dataclass
class SearchResult:
    """Result from code search operation."""

    file_path: str
    line_number: int
    snippet: str
    context: str = ""
    relevance_score: float = 0.0


class CodeIndexer:
    """
    Builds and maintains searchable index of repository code.

    Provides fast search capabilities for autonomous agents to understand
    codebase structure and find relevant code sections.
    """

    def __init__(self, max_file_size: int = 1024 * 1024, cache_dir: str = None):
        """
        Initialize code indexer.

        Args:
            max_file_size: Maximum file size to index (bytes)
            cache_dir: Directory for caching index data
        """
        self.max_file_size = max_file_size
        self.cache_dir = cache_dir or ".cache/code_index"
        self._ensure_cache_dir()

        # Index data structures
        self.files: dict[str, dict[str, Any]] = {}
        self.symbols: dict[str, CodeSymbol] = {}
        self.imports: dict[str, list[str]] = defaultdict(list)
        self.word_index: dict[str, set[str]] = defaultdict(set)
        self.line_index: dict[str, list[str]] = {}

        # Pattern matchers
        self._init_patterns()

    def build_index(
        self, include_globs: list[str], exclude_globs: list[str] = None
    ) -> dict[str, Any]:
        """
        Build comprehensive code index for repository.

        Args:
            include_globs: File patterns to include (e.g., ["*.py", "*.md"])
            exclude_globs: File patterns to exclude (e.g., ["__pycache__/*"])

        Returns:
            Repository intelligence dictionary
        """
        exclude_globs = exclude_globs or [
            "__pycache__/*",
            "*.pyc",
            ".git/*",
            "node_modules/*",
            ".cache/*",
            "*.egg-info/*",
            "build/*",
            "dist/*",
        ]

        # Find files to index
        files_to_index = self._find_files(include_globs, exclude_globs)

        # Index each file
        for file_path in files_to_index:
            try:
                self._index_file(file_path)
            except Exception as e:
                # Log error but continue indexing
                print(f"Warning: Failed to index {file_path}: {e}")

        # Build inverted word index
        self._build_word_index()

        # Generate repository intelligence
        repo_intel = self._generate_repo_intel()

        # Cache the index
        self._cache_index(repo_intel)

        return repo_intel

    def code_search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        """
        Search for code matching the query.

        Args:
            query: Search query (can be function name, keyword, etc.)
            max_results: Maximum number of results to return

        Returns:
            List of search results ordered by relevance
        """
        results = []
        query_lower = query.lower()
        query_words = set(re.findall(r"\w+", query_lower))

        # Search in symbols first (high relevance)
        for symbol_name, symbol in self.symbols.items():
            if query_lower in symbol_name.lower():
                snippet = self._get_code_snippet(symbol.file_path, symbol.line_number)
                results.append(
                    SearchResult(
                        file_path=symbol.file_path,
                        line_number=symbol.line_number,
                        snippet=snippet,
                        context=f"{symbol.type}: {symbol.name}",
                        relevance_score=self._calculate_symbol_relevance(query, symbol),
                    )
                )

        # Search in file content (medium relevance)
        for file_path, lines in self.line_index.items():
            for line_num, line in enumerate(lines, 1):
                if query_lower in line.lower():
                    # Skip if we already have this from symbols
                    if any(
                        r.file_path == file_path and abs(r.line_number - line_num) <= 2
                        for r in results
                    ):
                        continue

                    results.append(
                        SearchResult(
                            file_path=file_path,
                            line_number=line_num,
                            snippet=line.strip(),
                            context="content",
                            relevance_score=self._calculate_content_relevance(
                                query_words, line
                            ),
                        )
                    )

        # Sort by relevance and limit results
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:max_results]

    def who_refs(self, symbol: str) -> list[str]:
        """
        Find files that reference the given symbol.

        Args:
            symbol: Symbol name to search for

        Returns:
            List of file paths that reference the symbol
        """
        referencing_files = []

        # Search in imports
        for file_path, imported_symbols in self.imports.items():
            if symbol in imported_symbols:
                referencing_files.append(file_path)

        # Search in code content
        for file_path, lines in self.line_index.items():
            if file_path in referencing_files:
                continue  # Already found via imports

            for line in lines:
                # Look for symbol usage (simple heuristic)
                if re.search(rf"\b{re.escape(symbol)}\b", line):
                    referencing_files.append(file_path)
                    break

        return referencing_files

    def impact(self, surface: list[str]) -> dict[str, Any]:
        """
        Analyze impact of changes to given files or symbols.

        Args:
            surface: List of file paths or symbol names

        Returns:
            Impact analysis summary
        """
        impact_data = {
            "direct_files": [],
            "referencing_files": set(),
            "affected_symbols": set(),
            "risk_assessment": "low",
        }

        for item in surface:
            if item.endswith((".py", ".js", ".ts", ".md")):
                # File path
                impact_data["direct_files"].append(item)

                # Find symbols in this file
                file_symbols = [s for s in self.symbols.values() if s.file_path == item]
                for symbol in file_symbols:
                    impact_data["affected_symbols"].add(symbol.name)

                    # Find references to these symbols
                    refs = self.who_refs(symbol.name)
                    impact_data["referencing_files"].update(refs)
            else:
                # Symbol name
                refs = self.who_refs(item)
                impact_data["referencing_files"].update(refs)
                impact_data["affected_symbols"].add(item)

        # Convert sets to lists for JSON serialization
        impact_data["referencing_files"] = list(impact_data["referencing_files"])
        impact_data["affected_symbols"] = list(impact_data["affected_symbols"])

        # Assess risk level
        total_affected = len(impact_data["referencing_files"]) + len(
            impact_data["direct_files"]
        )
        if total_affected > 10:
            impact_data["risk_assessment"] = "high"
        elif total_affected > 3:
            impact_data["risk_assessment"] = "medium"

        impact_data["summary"] = {
            "total_files_affected": total_affected,
            "symbol_count": len(impact_data["affected_symbols"]),
            "reference_count": len(impact_data["referencing_files"]),
        }

        return impact_data

    def _find_files(
        self, include_globs: list[str], exclude_globs: list[str]
    ) -> list[str]:
        """Find files matching include patterns and not matching exclude patterns."""
        all_files = []

        # Walk directory tree
        for root, dirs, files in os.walk("."):
            # Skip directories that match exclude patterns
            dirs[:] = [
                d
                for d in dirs
                if not any(
                    fnmatch.fnmatch(os.path.join(root, d), pattern)
                    for pattern in exclude_globs
                )
            ]

            for file in files:
                file_path = os.path.join(root, file)
                file_path = file_path.replace("./", "")  # Normalize path

                # Check exclude patterns
                if any(
                    fnmatch.fnmatch(file_path, pattern) for pattern in exclude_globs
                ):
                    continue

                # Check include patterns
                if any(
                    fnmatch.fnmatch(file_path, pattern) for pattern in include_globs
                ):
                    # Check file size
                    try:
                        if os.path.getsize(file_path) <= self.max_file_size:
                            all_files.append(file_path)
                    except OSError:
                        continue

        return sorted(all_files)

    def _index_file(self, file_path: str):
        """Index a single file."""
        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                content = f.read()

            lines = content.splitlines()
            self.line_index[file_path] = lines

            # Store file metadata
            self.files[file_path] = {
                "size": len(content),
                "lines": len(lines),
                "extension": Path(file_path).suffix,
                "last_modified": os.path.getmtime(file_path),
            }

            # Extract symbols based on file type
            if file_path.endswith(".py"):
                self._extract_python_symbols(file_path, content, lines)
            elif file_path.endswith((".js", ".ts")):
                self._extract_js_symbols(file_path, content, lines)

        except Exception as e:
            raise Exception(f"Failed to read {file_path}: {e}")

    def _extract_python_symbols(self, file_path: str, content: str, lines: list[str]):
        """Extract Python symbols using regex patterns."""
        # Extract imports
        import_matches = re.finditer(
            r"^(?:from\s+(\S+)\s+)?import\s+([^#\n]+)", content, re.MULTILINE
        )
        for match in import_matches:
            module = match.group(1) or "builtins"
            imports = [imp.strip() for imp in match.group(2).split(",")]
            self.imports[file_path].extend(imports)

        # Extract functions
        func_matches = re.finditer(
            self.patterns["python_function"], content, re.MULTILINE
        )
        for match in func_matches:
            line_num = content[: match.start()].count("\n") + 1
            func_name = match.group(1)

            self.symbols[f"{file_path}:{func_name}"] = CodeSymbol(
                name=func_name,
                type="function",
                file_path=file_path,
                line_number=line_num,
                signature=match.group(0).strip(),
            )

        # Extract classes
        class_matches = re.finditer(
            self.patterns["python_class"], content, re.MULTILINE
        )
        for match in class_matches:
            line_num = content[: match.start()].count("\n") + 1
            class_name = match.group(1)

            self.symbols[f"{file_path}:{class_name}"] = CodeSymbol(
                name=class_name,
                type="class",
                file_path=file_path,
                line_number=line_num,
                signature=match.group(0).strip(),
            )

    def _extract_js_symbols(self, file_path: str, content: str, lines: list[str]):
        """Extract JavaScript/TypeScript symbols."""
        # Extract function declarations
        func_patterns = [
            r"function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(",
            r"const\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\([^)]*\)\s*=>",
        ]

        for pattern in func_patterns:
            func_matches = re.finditer(pattern, content, re.MULTILINE)
            for match in func_matches:
                line_num = content[: match.start()].count("\n") + 1
                func_name = match.group(1)

                self.symbols[f"{file_path}:{func_name}"] = CodeSymbol(
                    name=func_name,
                    type="function",
                    file_path=file_path,
                    line_number=line_num,
                    signature=match.group(0).strip(),
                )

        # Extract class declarations
        class_matches = re.finditer(
            r"class\s+([a-zA-Z_][a-zA-Z0-9_]*)", content, re.MULTILINE
        )
        for match in class_matches:
            line_num = content[: match.start()].count("\n") + 1
            class_name = match.group(1)

            self.symbols[f"{file_path}:{class_name}"] = CodeSymbol(
                name=class_name,
                type="class",
                file_path=file_path,
                line_number=line_num,
                signature=match.group(0).strip(),
            )

    def _build_word_index(self):
        """Build inverted word index for fast text search."""
        for file_path, lines in self.line_index.items():
            for line in lines:
                words = re.findall(r"\w+", line.lower())
                for word in words:
                    if len(word) >= 3:  # Index words with 3+ characters
                        self.word_index[word].add(file_path)

    def _generate_repo_intel(self) -> dict[str, Any]:
        """Generate repository intelligence summary."""
        return {
            "files": list(self.files.keys()),
            "symbols": [s.name for s in self.symbols.values()],
            "imports": dict(self.imports),
            "test_files": [f for f in self.files.keys() if "test" in f.lower()],
            "file_types": self._analyze_file_types(),
            "symbol_types": self._analyze_symbol_types(),
            "total_lines": sum(f["lines"] for f in self.files.values()),
            "index_timestamp": self._get_index_hash(),
        }

    def _analyze_file_types(self) -> dict[str, int]:
        """Analyze distribution of file types."""
        types = Counter()
        for file_path in self.files:
            ext = Path(file_path).suffix.lower()
            types[ext or "no_extension"] += 1
        return dict(types)

    def _analyze_symbol_types(self) -> dict[str, int]:
        """Analyze distribution of symbol types."""
        types = Counter(s.type for s in self.symbols.values())
        return dict(types)

    def _get_index_hash(self) -> str:
        """Generate hash representing current index state."""
        index_data = {
            "files": sorted(self.files.keys()),
            "symbols": len(self.symbols),
            "imports": len(self.imports),
        }
        return hashlib.md5(json.dumps(index_data, sort_keys=True).encode()).hexdigest()[
            :12
        ]

    def _init_patterns(self):
        """Initialize regex patterns for symbol extraction."""
        self.patterns = {
            "python_function": r"^[ \t]*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(",
            "python_class": r"^[ \t]*class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[:\(]",
            "js_function": r"(?:function\s+([a-zA-Z_][a-zA-Z0-9_]*)|([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*function|([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(?:\([^)]*\)\s*=>|\([^)]*\)\s*{))",
        }

    def _get_code_snippet(
        self, file_path: str, line_number: int, context_lines: int = 2
    ) -> str:
        """Get code snippet around specific line."""
        lines = self.line_index.get(file_path, [])
        if not lines:
            return ""

        start = max(0, line_number - context_lines - 1)
        end = min(len(lines), line_number + context_lines)

        snippet_lines = []
        for i in range(start, end):
            marker = ">>>" if i == line_number - 1 else "   "
            snippet_lines.append(f"{marker} {lines[i]}")

        return "\n".join(snippet_lines)

    def _calculate_symbol_relevance(self, query: str, symbol: CodeSymbol) -> float:
        """Calculate relevance score for symbol match."""
        query_lower = query.lower()
        symbol_name_lower = symbol.name.lower()

        # Exact match gets highest score
        if query_lower == symbol_name_lower:
            return 1.0

        # Substring match
        if query_lower in symbol_name_lower:
            return 0.8

        # Fuzzy match (edit distance heuristic)
        common_chars = set(query_lower) & set(symbol_name_lower)
        if common_chars:
            return (
                0.6 * len(common_chars) / max(len(query_lower), len(symbol_name_lower))
            )

        return 0.1

    def _calculate_content_relevance(self, query_words: set[str], line: str) -> float:
        """Calculate relevance score for content match."""
        line_words = set(re.findall(r"\w+", line.lower()))
        matches = query_words & line_words

        if not query_words:
            return 0.0

        return len(matches) / len(query_words)

    def _ensure_cache_dir(self):
        """Ensure cache directory exists."""
        os.makedirs(self.cache_dir, exist_ok=True)

    def _cache_index(self, repo_intel: dict[str, Any]):
        """Cache index data for faster subsequent loads."""
        cache_file = os.path.join(self.cache_dir, "repo_intel.json")
        try:
            with open(cache_file, "w") as f:
                json.dump(repo_intel, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to cache index: {e}")

    def load_cached_index(self) -> dict[str, Any] | None:
        """Load cached index if available and fresh."""
        cache_file = os.path.join(self.cache_dir, "repo_intel.json")

        if not os.path.exists(cache_file):
            return None

        try:
            with open(cache_file) as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load cached index: {e}")
            return None
