# Module Dependencies Map

## Core TermNet Modules

### termnet/agent.py
**Purpose**: Core agent orchestration
**Dependencies**:
- `termnet/memory.py` - Memory management
- `termnet/config.py` - Configuration loading
- `termnet/toolloader.py` - Dynamic tool loading
- `termnet/claims_engine.py` - Claims tracking
- `termnet/command_lifecycle.py` - Command execution
- External: `ollama`, `asyncio`, `json`

### termnet/main.py
**Purpose**: CLI entry point
**Dependencies**:
- `termnet/agent.py` - Main agent class
- `termnet/config.py` - Configuration
- External: `asyncio`, `argparse`

### termnet/config.py
**Purpose**: Configuration management
**Dependencies**:
- `termnet/config.json` - Configuration file
- External: `json`, `os`

### termnet/memory.py
**Purpose**: Conversation memory tracking
**Dependencies**:
- External: `collections.deque`, `json`

### termnet/toolloader.py
**Purpose**: Dynamic tool loading system
**Dependencies**:
- `termnet/toolregistry.json` - Tool definitions
- `termnet/tools/*` - Tool implementations
- External: `importlib`, `json`

## Phase 3 Security Modules

### termnet/claims_engine.py
**Purpose**: Claims and evidence tracking
**Dependencies**:
- `termnet/validation_engine.py` - Validation system
- External: `sqlite3`, `datetime`, `json`

### termnet/command_lifecycle.py
**Purpose**: 6-stage command execution pipeline
**Dependencies**:
- `termnet/sandbox.py` - Sandboxing
- `termnet/command_policy.py` - Policy engine
- `termnet/validation_engine.py` - Validation
- `termnet/claims_engine.py` - Claims tracking
- External: `asyncio`, `logging`

### termnet/sandbox.py
**Purpose**: Secure execution environment
**Dependencies**:
- `termnet/security_validation.py` - Security checks
- External: `subprocess`, `psutil`, `os`, `tempfile`

### termnet/command_policy.py
**Purpose**: Policy rule engine
**Dependencies**:
- `termnet/validation_rules.py` - Rule definitions
- External: `re`, `json`

### termnet/auditor_agent.py
**Purpose**: Claim auditing agent
**Dependencies**:
- `termnet/claims_engine.py` - Claims data
- `termnet/validation_engine.py` - Validation results
- `termnet/bmad_integration.py` - BMAD system
- External: `sqlite3`, `logging`

### termnet/validation_engine.py
**Purpose**: Core validation system
**Dependencies**:
- `termnet/validation_rules.py` - Validation rules
- `termnet/validation_monitor.py` - Monitoring
- External: `sqlite3`, `asyncio`

### termnet/validation_monitor.py
**Purpose**: Validation monitoring
**Dependencies**:
- `termnet/validation_engine.py` - Validation data
- External: `logging`, `datetime`

### termnet/security_validation.py
**Purpose**: Security validation layer
**Dependencies**:
- `termnet/command_policy.py` - Policy rules
- External: `re`, `os`

## Tool Modules

### termnet/tools/terminal.py
**Purpose**: Terminal command execution
**Dependencies**:
- `termnet/sandbox.py` - Sandboxed execution
- `termnet/validation_engine.py` - Command validation
- External: `subprocess`, `asyncio`, `shlex`

### termnet/tools/browsersearch.py
**Purpose**: Web search and scraping
**Dependencies**:
- External: `playwright`, `beautifulsoup4`, `asyncio`

### termnet/tools/scratchpad.py
**Purpose**: Planning and note-taking
**Dependencies**:
- `termnet/tools/scratchpad.json` - Scratchpad data
- External: `json`, `datetime`

## Integration Modules

### termnet/bmad_integration.py
**Purpose**: BMAD system integration
**Dependencies**:
- `termnet/auditor_agent.py` - Auditor functionality
- External: `asyncio`, `logging`

### termnet/claude_code_client.py
**Purpose**: Claude API integration
**Dependencies**:
- External: `httpx`, `asyncio`, `json`

### termnet/claude_code_client_enhanced.py
**Purpose**: Enhanced Claude integration
**Dependencies**:
- `termnet/claude_code_client.py` - Base client
- External: `httpx`, `asyncio`

### termnet/openrouter_client.py
**Purpose**: OpenRouter API client
**Dependencies**:
- External: `httpx`, `asyncio`, `json`

## Application Modules

### auth_api.py
**Purpose**: Authentication API
**Dependencies**:
- External: `flask`, `flask_sqlalchemy`, `flask_jwt_extended`, `bcrypt`

### blog_app.py
**Purpose**: Blog application
**Dependencies**:
- External: `flask`, `flask_sqlalchemy`, `datetime`

### todo_app.py
**Purpose**: Todo list application
**Dependencies**:
- External: `flask`, `sqlite3`, `datetime`

### user_management_api.py
**Purpose**: User management system
**Dependencies**:
- External: `flask`, `flask_sqlalchemy`, `flask_restful`

## Test Modules

### test_termnet_agent_tools.py
**Dependencies**:
- `termnet/agent.py`
- `termnet/toolloader.py`
- External: `pytest`, `asyncio`

### test_validation_system.py
**Dependencies**:
- `termnet/validation_engine.py`
- `termnet/validation_rules.py`
- External: `pytest`, `sqlite3`

### test_claims.py (various)
**Dependencies**:
- `termnet/claims_engine.py`
- External: `pytest`, `sqlite3`

## Utility Scripts

### verify_phase3_build.sh
**Dependencies**:
- System: `bash`, `python3`, `sqlite3`
- Python modules: All Phase 3 modules

### run_termnet_openrouter.py
**Dependencies**:
- `termnet/openrouter_client.py`
- `termnet/agent.py`
- External: `asyncio`

### gpu_monitor.py
**Dependencies**:
- External: `nvidia-ml-py`, `psutil`, `time`

### gpt_oss_openrouter.py
**Dependencies**:
- External: `openai`, `asyncio`, `json`

## Dependency Graph Summary

### Core Flow
```
main.py
  └── agent.py
      ├── config.py
      ├── memory.py
      ├── toolloader.py
      │   └── tools/*
      └── claims_engine.py
          └── command_lifecycle.py
              ├── sandbox.py
              ├── command_policy.py
              └── validation_engine.py
```

### Security Layer
```
command_lifecycle.py
  ├── sandbox.py
  │   └── security_validation.py
  ├── command_policy.py
  │   └── validation_rules.py
  └── validation_engine.py
      └── validation_monitor.py
```

### Audit System
```
auditor_agent.py
  ├── claims_engine.py
  ├── validation_engine.py
  └── bmad_integration.py
```

## External Dependencies

### Python Packages
- **Core**: asyncio, json, logging, os, sys
- **Web**: flask, flask_sqlalchemy, flask_jwt_extended, flask_restful
- **Async**: httpx, aiohttp
- **Database**: sqlite3, sqlalchemy
- **Security**: bcrypt, psutil
- **Web Scraping**: playwright, beautifulsoup4
- **AI/ML**: ollama, openai
- **Testing**: pytest, unittest
- **System**: subprocess, tempfile, shlex

### System Requirements
- Python 3.9+
- Ollama runtime
- Chromium (via Playwright)
- SQLite3
- Bash shell (for scripts)

## Configuration Files
- `termnet/config.json` - Main configuration
- `termnet/toolregistry.json` - Tool definitions
- `termnet/tools/scratchpad.json` - Scratchpad data
- `pytest.ini` - Test configuration
- `.pre-commit-config.yaml` - Pre-commit hooks
- `docker-compose.yml` - Container orchestration

## Database Files
- `termnet_claims.db` - Claims tracking
- `termnet_validation.db` - Validation results
- `termnet_audit_findings.db` - Audit data
- `termnet_trends.db` - Analytics
- `todos.db` - Todo application data
- Various test databases (`test_*.db`)