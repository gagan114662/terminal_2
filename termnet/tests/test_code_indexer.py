"""
Tests for TermNet Code Indexer

Tests are completely offline using fixture files and deterministic behavior.
Follows Google AI best practices for isolated, reproducible testing.
"""

import os
import tempfile
import shutil
import pytest
from pathlib import Path
from unittest.mock import patch

from termnet.code_indexer import CodeIndexer, CodeSymbol, SearchResult


class TestCodeIndexer:
    """Test CodeIndexer functionality with offline fixtures."""

    @pytest.fixture
    def temp_repo(self):
        """Create temporary repository with test files."""
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()

        try:
            os.chdir(temp_dir)

            # Create test Python files
            os.makedirs("src", exist_ok=True)
            os.makedirs("tests", exist_ok=True)
            os.makedirs("docs", exist_ok=True)

            # Main module
            with open("src/main.py", "w") as f:
                f.write('''"""Main module for testing."""
import os
from typing import List, Optional

class DataProcessor:
    """Processes data for the application."""

    def __init__(self, config: dict):
        self.config = config
        self.processed_count = 0

    def process_data(self, data: List[str]) -> Optional[str]:
        """Process input data and return result."""
        if not data:
            return None

        result = []
        for item in data:
            processed_item = self._transform_item(item)
            result.append(processed_item)

        self.processed_count += len(data)
        return "\\n".join(result)

    def _transform_item(self, item: str) -> str:
        """Transform a single item."""
        return item.upper().strip()

def main_function():
    """Main entry point."""
    processor = DataProcessor({"debug": True})
    data = ["hello", "world"]
    result = processor.process_data(data)
    print(result)

if __name__ == "__main__":
    main_function()
''')

            # Utility module
            with open("src/utils.py", "w") as f:
                f.write('''"""Utility functions."""
import json
import re
from pathlib import Path

def read_config(config_path: str) -> dict:
    """Read configuration from file."""
    with open(config_path, 'r') as f:
        return json.load(f)

def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

class ConfigManager:
    """Manages application configuration."""

    def __init__(self):
        self.config_data = {}

    def load_config(self, path: Path):
        """Load configuration from path."""
        self.config_data = read_config(str(path))
''')

            # Test file
            with open("tests/test_main.py", "w") as f:
                f.write('''"""Tests for main module."""
import pytest
from src.main import DataProcessor, main_function

class TestDataProcessor:
    """Test DataProcessor class."""

    def test_process_data_empty(self):
        """Test processing empty data."""
        processor = DataProcessor({})
        result = processor.process_data([])
        assert result is None

    def test_process_data_normal(self):
        """Test normal data processing."""
        processor = DataProcessor({"debug": False})
        result = processor.process_data(["hello", "world"])
        assert result == "HELLO\\nWORLD"

    def test_transform_item(self):
        """Test item transformation."""
        processor = DataProcessor({})
        result = processor._transform_item("  test  ")
        assert result == "TEST"

def test_main_function():
    """Test main function."""
    # This would normally capture stdout
    main_function()
''')

            # Documentation
            with open("docs/README.md", "w") as f:
                f.write('''# Test Project

This is a test project for code indexing.

## Features

- Data processing with `DataProcessor` class
- Configuration management via `ConfigManager`
- Email validation utility
- Comprehensive test suite

## Usage

```python
from src.main import DataProcessor

processor = DataProcessor({"debug": True})
result = processor.process_data(["item1", "item2"])
```

## Testing

Run tests with:
```
pytest tests/
```
''')

            # JavaScript file for multi-language testing
            with open("src/app.js", "w") as f:
                f.write('''// JavaScript application
const express = require('express');

function createApp() {
    const app = express();

    app.get('/', function(req, res) {
        res.send('Hello World');
    });

    return app;
}

const handleError = (error) => {
    console.error('Error occurred:', error);
};

class APIClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }

    async fetchData(endpoint) {
        try {
            const response = await fetch(`${this.baseUrl}/${endpoint}`);
            return await response.json();
        } catch (error) {
            handleError(error);
            return null;
        }
    }
}

module.exports = { createApp, APIClient, handleError };
''')

            yield temp_dir

        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)

    @pytest.fixture
    def indexer(self):
        """Create code indexer instance."""
        return CodeIndexer(cache_dir=".test_cache")

    def test_build_index_finds_files(self, indexer, temp_repo):
        """Test that build_index correctly finds and indexes files."""
        include_globs = ["*.py", "*.md", "*.js"]
        exclude_globs = ["__pycache__/*", ".git/*"]

        repo_intel = indexer.build_index(include_globs, exclude_globs)

        # Verify file discovery
        assert "files" in repo_intel
        files = repo_intel["files"]

        expected_files = ["src/main.py", "src/utils.py", "tests/test_main.py", "docs/README.md", "src/app.js"]
        for expected_file in expected_files:
            assert expected_file in files, f"Expected file {expected_file} not found in index"

        # Verify file type analysis
        file_types = repo_intel["file_types"]
        assert ".py" in file_types
        assert ".md" in file_types
        assert ".js" in file_types
        assert file_types[".py"] == 3  # main.py, utils.py, test_main.py

    def test_extract_python_symbols(self, indexer, temp_repo):
        """Test extraction of Python symbols."""
        repo_intel = indexer.build_index(["*.py"])

        symbols = repo_intel["symbols"]

        # Check for classes
        assert "DataProcessor" in symbols
        assert "ConfigManager" in symbols
        assert "TestDataProcessor" in symbols

        # Check for functions
        assert "main_function" in symbols
        assert "read_config" in symbols
        assert "validate_email" in symbols
        assert "process_data" in symbols

        # Verify symbol details in indexer
        data_processor_symbol = None
        for symbol in indexer.symbols.values():
            if symbol.name == "DataProcessor":
                data_processor_symbol = symbol
                break

        assert data_processor_symbol is not None
        assert data_processor_symbol.type == "class"
        assert data_processor_symbol.file_path == "src/main.py"
        assert data_processor_symbol.line_number > 0

    def test_extract_imports(self, indexer, temp_repo):
        """Test extraction of import statements."""
        repo_intel = indexer.build_index(["*.py"])

        imports = repo_intel["imports"]

        # Check main.py imports
        main_imports = imports.get("src/main.py", [])
        assert "os" in main_imports
        assert "List" in main_imports
        assert "Optional" in main_imports

        # Check utils.py imports
        utils_imports = imports.get("src/utils.py", [])
        assert "json" in utils_imports
        assert "re" in utils_imports
        assert "Path" in utils_imports

    def test_code_search_symbol_names(self, indexer, temp_repo):
        """Test searching for symbols by name."""
        indexer.build_index(["*.py"])

        # Search for exact class name
        results = indexer.code_search("DataProcessor")
        assert len(results) > 0
        assert any("DataProcessor" in r.snippet for r in results)

        # Search for function name
        results = indexer.code_search("validate_email")
        assert len(results) > 0
        assert any("validate_email" in r.snippet for r in results)

        # Verify search result structure
        result = results[0]
        assert isinstance(result, SearchResult)
        assert result.file_path
        assert result.line_number > 0
        assert result.snippet
        assert result.relevance_score > 0

    def test_code_search_content(self, indexer, temp_repo):
        """Test searching within file content."""
        indexer.build_index(["*.py", "*.md"])

        # Search for content in comments/docstrings
        results = indexer.code_search("configuration")
        assert len(results) > 0

        # Search for content in markdown
        results = indexer.code_search("test project")
        assert len(results) > 0
        assert any("README.md" in r.file_path for r in results)

        # Search for code patterns
        results = indexer.code_search("self.config")
        assert len(results) > 0

    def test_who_refs_finds_references(self, indexer, temp_repo):
        """Test finding references to symbols."""
        indexer.build_index(["*.py"])

        # Find references to DataProcessor
        refs = indexer.who_refs("DataProcessor")
        assert "tests/test_main.py" in refs  # Used in import and tests
        assert "src/main.py" in refs  # Defined and used

        # Find references to json (import)
        refs = indexer.who_refs("json")
        assert "src/utils.py" in refs

    def test_impact_analysis_files(self, indexer, temp_repo):
        """Test impact analysis for file changes."""
        indexer.build_index(["*.py"])

        # Analyze impact of changing main.py
        impact = indexer.impact(["src/main.py"])

        assert "src/main.py" in impact["direct_files"]
        assert "tests/test_main.py" in impact["referencing_files"]  # Tests import main
        assert "DataProcessor" in impact["affected_symbols"]
        assert "main_function" in impact["affected_symbols"]

        # Check risk assessment
        assert impact["risk_assessment"] in ["low", "medium", "high"]
        assert "summary" in impact

    def test_impact_analysis_symbols(self, indexer, temp_repo):
        """Test impact analysis for symbol changes."""
        indexer.build_index(["*.py"])

        # Analyze impact of changing DataProcessor
        impact = indexer.impact(["DataProcessor"])

        assert "DataProcessor" in impact["affected_symbols"]
        assert len(impact["referencing_files"]) > 0
        assert impact["summary"]["symbol_count"] >= 1

    def test_exclude_patterns_work(self, indexer, temp_repo):
        """Test that exclude patterns properly filter files."""
        # Create files that should be excluded
        os.makedirs("__pycache__", exist_ok=True)
        with open("__pycache__/test.pyc", "w") as f:
            f.write("binary content")

        os.makedirs("node_modules", exist_ok=True)
        with open("node_modules/package.js", "w") as f:
            f.write("console.log('should be excluded');")

        repo_intel = indexer.build_index(
            ["*.py", "*.js"],
            ["__pycache__/*", "node_modules/*"]
        )

        files = repo_intel["files"]
        assert not any("__pycache__" in f for f in files)
        assert not any("node_modules" in f for f in files)
        assert "src/app.js" in files  # Should include this JS file

    def test_max_file_size_limit(self, indexer, temp_repo):
        """Test that large files are excluded."""
        # Create a large file
        with open("large_file.py", "w") as f:
            f.write("# Large file\n" * 10000)  # Make it large

        # Use small max_file_size
        small_indexer = CodeIndexer(max_file_size=1000)
        repo_intel = small_indexer.build_index(["*.py"])

        # Large file should not be indexed
        assert "large_file.py" not in repo_intel["files"]

    def test_search_relevance_scoring(self, indexer, temp_repo):
        """Test that search results are properly scored and ranked."""
        indexer.build_index(["*.py"])

        # Search for "process" - should find multiple matches
        results = indexer.code_search("process")

        # Results should be sorted by relevance
        assert len(results) > 1
        for i in range(len(results) - 1):
            assert results[i].relevance_score >= results[i + 1].relevance_score

        # Exact matches should score higher than partial matches
        exact_results = indexer.code_search("DataProcessor")
        partial_results = indexer.code_search("Process")

        if exact_results and partial_results:
            assert exact_results[0].relevance_score >= partial_results[0].relevance_score

    def test_javascript_symbol_extraction(self, indexer, temp_repo):
        """Test extraction of JavaScript symbols."""
        repo_intel = indexer.build_index(["*.js"])

        symbols = repo_intel["symbols"]

        # Check for JavaScript functions
        assert "createApp" in symbols
        assert "handleError" in symbols

        # Check for classes
        assert "APIClient" in symbols

    def test_repo_intel_structure(self, indexer, temp_repo):
        """Test that repo_intel has expected structure."""
        repo_intel = indexer.build_index(["*.py", "*.md", "*.js"])

        # Check required fields
        required_fields = [
            "files", "symbols", "imports", "test_files",
            "file_types", "symbol_types", "total_lines", "index_timestamp"
        ]

        for field in required_fields:
            assert field in repo_intel, f"Missing required field: {field}"

        # Check data types
        assert isinstance(repo_intel["files"], list)
        assert isinstance(repo_intel["symbols"], list)
        assert isinstance(repo_intel["imports"], dict)
        assert isinstance(repo_intel["test_files"], list)
        assert isinstance(repo_intel["file_types"], dict)
        assert isinstance(repo_intel["symbol_types"], dict)
        assert isinstance(repo_intel["total_lines"], int)
        assert isinstance(repo_intel["index_timestamp"], str)

        # Check test file detection
        test_files = repo_intel["test_files"]
        assert any("test" in f for f in test_files)

    def test_cache_functionality(self, indexer, temp_repo):
        """Test index caching and loading."""
        # Build index first time
        repo_intel1 = indexer.build_index(["*.py"])

        # Load from cache
        cached_intel = indexer.load_cached_index()

        if cached_intel:  # Cache might not be available in test environment
            assert cached_intel["index_timestamp"] == repo_intel1["index_timestamp"]
            assert len(cached_intel["files"]) == len(repo_intel1["files"])

    def test_error_handling_bad_files(self, indexer, temp_repo):
        """Test error handling for problematic files."""
        # Create a file with encoding issues
        with open("bad_encoding.py", "wb") as f:
            f.write(b"# -*- coding: utf-8 -*-\n")
            f.write(b"print('\xff\xfe bad encoding')\n")

        # Should handle gracefully and continue indexing
        repo_intel = indexer.build_index(["*.py"])

        # Should still index other files
        assert len(repo_intel["files"]) > 0
        assert "src/main.py" in repo_intel["files"]

    def test_word_index_building(self, indexer, temp_repo):
        """Test that word index is built correctly."""
        indexer.build_index(["*.py"])

        # Check that word index is populated
        assert len(indexer.word_index) > 0

        # Check specific words are indexed
        assert "class" in indexer.word_index
        assert "def" in indexer.word_index
        assert "import" in indexer.word_index

        # Words should map to files
        for word, files in indexer.word_index.items():
            assert isinstance(files, set)
            assert len(files) > 0

    def test_line_index_accuracy(self, indexer, temp_repo):
        """Test that line indexing is accurate."""
        indexer.build_index(["*.py"])

        # Check specific file
        main_lines = indexer.line_index.get("src/main.py", [])
        assert len(main_lines) > 0

        # Check that specific content is present
        content = "\n".join(main_lines)
        assert "class DataProcessor:" in content
        assert "def process_data" in content

    def test_empty_repository(self, indexer):
        """Test behavior with empty repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            old_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                repo_intel = indexer.build_index(["*.py"])

                assert repo_intel["files"] == []
                assert repo_intel["symbols"] == []
                assert repo_intel["total_lines"] == 0
                assert len(repo_intel["imports"]) == 0

            finally:
                os.chdir(old_cwd)


class TestCodeSymbol:
    """Test CodeSymbol data structure."""

    def test_code_symbol_creation(self):
        """Test CodeSymbol creation."""
        symbol = CodeSymbol(
            name="test_function",
            type="function",
            file_path="test.py",
            line_number=42,
            signature="def test_function():",
            docstring="Test function docstring"
        )

        assert symbol.name == "test_function"
        assert symbol.type == "function"
        assert symbol.file_path == "test.py"
        assert symbol.line_number == 42
        assert symbol.signature == "def test_function():"
        assert symbol.docstring == "Test function docstring"


class TestSearchResult:
    """Test SearchResult data structure."""

    def test_search_result_creation(self):
        """Test SearchResult creation."""
        result = SearchResult(
            file_path="src/module.py",
            line_number=10,
            snippet="def example_function():",
            context="function definition",
            relevance_score=0.85
        )

        assert result.file_path == "src/module.py"
        assert result.line_number == 10
        assert result.snippet == "def example_function():"
        assert result.context == "function definition"
        assert result.relevance_score == 0.85