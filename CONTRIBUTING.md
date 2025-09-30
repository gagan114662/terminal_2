# Contributing to TermNet

## Branch/PR Flow

### Quick Start
```bash
git checkout main && git pull
git checkout -b feature/your-feature-name
# Make changes

# Development workflow
pre-commit run --all-files  # Run twice - first may format, second should exit 0
pre-commit run --all-files
make verify                 # Generate artifacts/verify_summary.json
pytest -q                   # All tests should pass

# Commit and push
git add . && git commit -m "feat: your change description"
git push -u origin feature/your-feature-name
# Create PR via GitHub
```

### Branch Naming
- `feature/` - New functionality
- `fix/` - Bug fixes
- `refactor/` - Code improvements
- `test/` - Test-only changes
- `docs/` - Documentation updates

### PR Requirements
- [ ] Core tests pass: `pytest -q tests/test_safety.py tests/test_toolloader.py`
- [ ] Verification script passes: `python verify_all_fixes.py`
- [ ] No breaking changes to tool contracts
- [ ] SafetyChecker returns empty string for safe operations (test contract)
- [ ] New tools follow the pattern in `termnet/tools/`

### Testing Strategy
1. **Unit Tests First**: Add to appropriate `tests/test_*.py`
2. **Integration Check**: Run `verify_all_fixes.py`
3. **Smoke Test**: Use canonical trajectory prompt (see `smoke_test_trajectory.md`)
4. **Python 3.13**: The xfail in `conftest.py` handles the MagicMock quirk

### Code Style
- Follow existing patterns in the codebase
- Add docstrings for public methods
- Use type hints where beneficial
- Keep tool contracts consistent (return dicts with status/output)

### Tool Development
- New tools go in `termnet/tools/your_tool.py`
- Implement offline mode for testing: `set_offline_mode()`
- Add to `ACTION_NAME_BY_MODULE` in `toolloader.py`
- Follow the pattern in `terminal.py` or `browsersearch.py`

### Safety & Security
- All commands go through SafetyChecker
- No secrets in code - use environment variables
- URL validation for external calls
- Path restrictions for file operations

### Review Process
1. Automated checks (pytest, verification script)
2. Code review focusing on:
   - Tool contract compliance
   - Safety checker integration
   - Test coverage
   - Documentation clarity

### Release Notes
Update relevant sections:
- New tools/features
- Breaking changes (avoid if possible)
- Performance improvements
- Bug fixes

### Questions?
Check existing patterns in:
- `termnet/tools/terminal.py` - Complex tool with offline mode
- `tests/test_toolloader.py` - Mock-friendly testing
- `termnet/safety.py` - Safety validation patterns
