# TermNet Testing Documentation

## Overview
This document provides comprehensive information about TermNet's testing infrastructure, including test organization, running tests, and maintaining code quality.

## Test Structure

```
tests/
├── __init__.py
├── test_agent.py           # Core agent functionality tests
├── test_toolloader.py      # Tool loading system tests
├── test_safety.py          # Safety checker tests
├── test_memory.py          # Conversation memory tests
├── test_tools.py           # Individual tool tests
└── test_integration.py     # End-to-end integration tests
```

## Quick Start

### Install Testing Dependencies
```bash
pip install -r requirements-dev.txt
playwright install chromium
```

### Run All Tests
```bash
make test
```

### Run Specific Test Categories
```bash
# Unit tests only
make test-unit

# Integration tests only
make test-integration

# Specific test file
pytest tests/test_agent.py -v

# Specific test function
pytest tests/test_agent.py::TestTermNetAgent::test_agent_initialization -v
```

## Test Categories

### Unit Tests
- **test_agent.py**: Tests for TermNetAgent class
  - Agent initialization
  - Tool execution
  - GPT-OSS parsing
  - BMAD command handling
  - Conversation management

- **test_toolloader.py**: Tests for dynamic tool loading
  - Tool discovery
  - Module loading
  - Tool registration
  - Error handling

- **test_safety.py**: Tests for SafetyChecker
  - Command validation
  - Path restrictions
  - URL validation
  - Output sanitization

- **test_memory.py**: Tests for ConversationMemory
  - Message storage
  - Context retrieval
  - Persistence
  - Search functionality

- **test_tools.py**: Tests for individual tools
  - TerminalTool execution
  - BrowserSearchTool functionality
  - ScratchpadTool operations

### Integration Tests
- **test_integration.py**: End-to-end workflow tests
  - Multi-tool execution flows
  - GPT-OSS integration
  - BMAD workflow integration
  - Memory persistence across sessions
  - Error recovery scenarios

## Coverage Reports

### Generate Coverage Report
```bash
make coverage
```

### View Coverage Report
- Terminal: Coverage summary is displayed after test run
- HTML: Open `htmlcov/index.html` in browser
- XML: `coverage.xml` for CI/CD integration

### Current Coverage Goals
- Overall: > 80%
- Core modules: > 90%
- Safety-critical code: 100%

## Code Quality

### Run All Linters
```bash
make lint
```

### Individual Linters

#### Flake8 (Style Guide)
```bash
flake8 termnet/ tests/ --max-line-length=100
```

#### Black (Code Formatting)
```bash
# Check formatting
black termnet/ tests/ --check

# Auto-format
black termnet/ tests/
```

#### isort (Import Sorting)
```bash
# Check imports
isort termnet/ tests/ --check-only

# Auto-fix imports
isort termnet/ tests/
```

#### MyPy (Type Checking)
```bash
mypy termnet/ --ignore-missing-imports
```

#### Pylint (Code Analysis)
```bash
pylint termnet/ tests/
```

## Full QA Suite

Run complete quality assurance:
```bash
make qa
```

This runs:
1. Code formatting (black, isort)
2. Linting (flake8, pylint, mypy)
3. All tests
4. Coverage report generation

## Continuous Integration

GitHub Actions workflow runs on:
- Push to main/develop branches
- Pull requests to main

CI Pipeline includes:
- Multi-OS testing (Ubuntu, macOS)
- Multiple Python versions (3.9-3.12)
- Linting and formatting checks
- Type checking
- Test execution with coverage
- Security vulnerability scanning
- Build artifact generation

## Writing New Tests

### Test Conventions
1. Use pytest fixtures for setup
2. Mock external dependencies
3. Use descriptive test names
4. Group related tests in classes
5. Mark slow/integration tests appropriately

### Example Test Structure
```python
import pytest
from unittest.mock import MagicMock, patch

class TestNewFeature:
    @pytest.fixture
    def setup(self):
        # Setup code
        return test_object

    def test_feature_success_case(self, setup):
        # Arrange
        expected = "expected_result"

        # Act
        result = setup.method_under_test()

        # Assert
        assert result == expected

    @pytest.mark.asyncio
    async def test_async_feature(self, setup):
        # Test async methods
        result = await setup.async_method()
        assert result is not None
```

### Mocking Guidelines
1. Mock external APIs and services
2. Mock file system operations when possible
3. Use AsyncMock for async methods
4. Patch at the usage point, not definition

## Debugging Tests

### Run with verbose output
```bash
pytest tests/ -vv
```

### Run with print statements visible
```bash
pytest tests/ -s
```

### Run with debugger on failure
```bash
pytest tests/ --pdb
```

### Run specific test with extra info
```bash
pytest tests/test_agent.py::TestTermNetAgent::test_agent_initialization -vvs
```

## Test Data and Fixtures

### Common Fixtures
- `mock_terminal`: Mocked terminal for agent tests
- `agent`: Pre-configured TermNetAgent instance
- `tool_loader`: Initialized ToolLoader
- `safety_checker`: SafetyChecker instance

### Test Data Location
- Mock responses: Defined inline in tests
- Configuration: Patched CONFIG dictionary
- File operations: Use mock_open and tempfile

## Performance Testing

### Run with timeout
```bash
pytest tests/ --timeout=30
```

### Profile test execution
```bash
pytest tests/ --profile
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure termnet is in PYTHONPATH
   - Check virtual environment activation

2. **Async Test Failures**
   - Verify pytest-asyncio is installed
   - Check asyncio_mode in pytest.ini

3. **Browser Tests Failing**
   - Run `playwright install chromium`
   - Check headless mode compatibility

4. **Coverage Not Generated**
   - Install coverage[toml]
   - Check pytest-cov configuration

## Maintenance

### Regular Tasks
1. Update test dependencies monthly
2. Review and update test coverage targets
3. Refactor tests when implementation changes
4. Add tests for bug fixes
5. Remove obsolete tests

### Test Review Checklist
- [ ] All new features have tests
- [ ] Edge cases are covered
- [ ] Error paths are tested
- [ ] Mocks are properly configured
- [ ] Tests are isolated and independent
- [ ] Documentation is updated

## Contact

For testing questions or issues:
- Check existing test examples
- Review pytest documentation
- Consult team lead for complex scenarios
