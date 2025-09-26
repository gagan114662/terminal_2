# Planned Tool Stubs - Roadmap

## Next Tools (Keep ToolLoader Contract Steady)

### 1. FileManager Tool
**Module**: `termnet/tools/filemanager.py`
**Action Name**: `file_manage`
**Contract**:
```python
{
    "read": {"path": str} → {"status": "success", "content": str, "encoding": str},
    "write": {"path": str, "content": str} → {"status": "success", "bytes_written": int},
    "list": {"path": str} → {"status": "success", "files": [{"name": str, "type": str, "size": int}]},
    "delete": {"path": str} → {"status": "success", "deleted": bool}
}
```

### 2. WebFetcher Tool
**Module**: `termnet/tools/webfetcher.py`
**Action Name**: `web_fetch`
**Contract**:
```python
{
    "fetch": {"url": str, "method": "GET"} → {"status": "success", "content": str, "headers": dict, "status_code": int},
    "download": {"url": str, "path": str} → {"status": "success", "downloaded": bool, "size": int}
}
```

### 3. CodeAnalyzer Tool
**Module**: `termnet/tools/codeanalyzer.py`
**Action Name**: `code_analyze`
**Contract**:
```python
{
    "parse": {"code": str, "language": str} → {"status": "success", "ast": dict, "errors": []},
    "lint": {"file_path": str} → {"status": "success", "issues": [{"line": int, "message": str, "severity": str}]},
    "format": {"code": str, "language": str} → {"status": "success", "formatted_code": str}
}
```

### 4. DatabaseQuery Tool
**Module**: `termnet/tools/database.py`
**Action Name**: `db_query`
**Contract**:
```python
{
    "query": {"sql": str, "params": list} → {"status": "success", "rows": [], "affected": int},
    "schema": {"table": str} → {"status": "success", "columns": [{"name": str, "type": str}]}
}
```

## Integration Notes

### ToolLoader Updates Required
Add to `ACTION_NAME_BY_MODULE`:
```python
"filemanager": "file_manage",
"webfetcher": "web_fetch",
"codeanalyzer": "code_analyze",
"database": "db_query"
```

### Safety Integration
Each tool needs SafetyChecker integration:
- FileManager: Path validation via `check_file_path()`
- WebFetcher: URL validation via `is_safe_url()`
- CodeAnalyzer: Input sanitization
- DatabaseQuery: SQL injection prevention

### Testing Pattern
Each tool stub should include:
```python
class ToolName:
    def __init__(self):
        self._offline_mode = False

    def set_offline_mode(self, offline=True):
        self._offline_mode = offline

    def get_definition(self):
        return {
            "type": "function",
            "function": {
                "module": "termnet.tools.toolname",
                "class": "ToolName",
                "method": "execute",
                "description": "Tool description"
            }
        }
```

## Timeline
- **Week 1**: FileManager (most commonly needed)
- **Week 2**: WebFetcher (for grounding v1)
- **Week 3**: CodeAnalyzer (development workflows)
- **Week 4**: DatabaseQuery (data operations)

## Backward Compatibility
- Existing tools (terminal, browsersearch, scratchpad) remain unchanged
- ToolLoader will dynamically discover new tools via filesystem scan
- Tests will continue to pass with current 3-tool expectation
- New tools start disabled by default in any registry

## Dependencies to Add
```txt
# requirements.txt additions
requests>=2.31.0          # WebFetcher
beautifulsoup4>=4.12.0    # WebFetcher HTML parsing
black>=23.0.0             # CodeAnalyzer formatting
flake8>=6.0.0             # CodeAnalyzer linting
sqlparse>=0.4.0           # DatabaseQuery SQL parsing
```

This roadmap ensures the ToolLoader contract stays stable while adding focused capabilities incrementally.