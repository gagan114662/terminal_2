# TermNet Complete Architecture & Structure Report

## Executive Summary
TermNet is an AI-powered terminal assistant that integrates multiple LLM providers (Claude Code CLI, OpenRouter, legacy Ollama) with advanced tool capabilities, validation systems, and autonomous workflow orchestration through BMAD-METHOD integration.

## Core Architecture

### 1. Main Agent System (`termnet/agent.py`)
- **TermNetAgent**: Central orchestrator managing conversation flow, tool execution, and LLM interactions
- **Key Features**:
  - Multi-LLM support with priority fallback (Claude Code → OpenRouter → Ollama)
  - Dynamic tool loading and execution
  - BMAD-METHOD integration for autonomous workflows
  - GPT-OSS tool call parsing for specialized models
  - Persistent conversation history management
  - Real-time streaming responses

### 2. Tool System

#### Tool Loader (`termnet/toolloader.py`)
- Dynamic tool registration from `toolregistry.json`
- Runtime module import and instantiation
- Tool definition management for LLM consumption

#### Registered Tools (`termnet/toolregistry.json`)
1. **terminal_execute**: Command execution with safety checks
2. **browser_search**: Web search and result extraction
3. **browser_click_and_collect**: Deep web content extraction
4. **scratchpad**: Persistent note-taking and planning

#### Tool Implementations

##### Terminal Tool (`termnet/tools/terminal.py`)
- Async command execution with timeout control
- Safety validation through SafetyChecker
- Command history tracking
- Working directory management
- Validation engine integration for command verification
- Exit code and output capture

##### Browser Search Tool (`termnet/tools/browsersearch.py`)
- Playwright-based browser automation
- Structured data extraction (links, buttons, forms)
- Content scoring and noise filtering
- Deep content collection from specific URLs
- BeautifulSoup HTML parsing

##### Scratchpad Tool (`termnet/tools/scratchpad.py`)
- Persistent JSON-based storage
- Note management (write, read, clear)
- Context preservation across sessions

### 3. LLM Integration Layer

#### Claude Code Client (`termnet/claude_code_client.py`)
- Direct CLI integration with Claude Code
- OAuth token authentication
- YOLO mode for permission bypass
- Streaming response handling
- System context injection

#### OpenRouter Client (`termnet/openrouter_client.py`)
- Cloud-based LLM API access
- Tool calling support for compatible models
- Streaming with chunk accumulation
- SSL context management
- Error handling and fallback

#### BMAD Integration (`termnet/bmad_integration.py`)
- BMAD-METHOD orchestrator connection
- Agent command detection and routing
- Automated workflow execution
- Workflow state management (save/load)
- Progress tracking and status reporting

### 4. Validation System

#### Validation Engine (`termnet/validation_engine.py`)
- **Core Components**:
  - ValidationRule base class for extensible rules
  - SQLite-based history tracking
  - Batch validation execution
  - Performance metrics collection
  - Multi-severity level support (CRITICAL → INFO)

#### Validation Monitor (`termnet/validation_monitor.py`)
- **Real-time Monitoring**:
  - File system event detection via watchdog
  - Debounced validation triggers
  - Automatic rule application
  - Statistics tracking
  - Queue-based validation processing

#### Validation Rules (`termnet/validation_rules.py`, `validation_rules_advanced.py`)
- **Core Rules**:
  - Python syntax validation
  - Requirements file checking
  - Application startup verification
  - Flask application validation
  - Database schema validation

- **Advanced Rules**:
  - React application validation
  - Docker configuration checks
  - API endpoint testing
  - Security vulnerability scanning
  - Test coverage analysis

### 5. Configuration System

#### Config Management (`termnet/config.py`, `termnet/config.json`)
- Centralized configuration loading
- Provider toggles (Claude/OpenRouter/Ollama)
- API keys and endpoints
- Model selection and parameters
- Timeout and limit settings
- Memory window configuration

### 6. Safety System (`termnet/safety.py`)
- Command pattern matching for dangerous operations
- Risky command warnings
- Destructive operation prevention
- Regex-based pattern detection

## Data Flow Architecture

```
User Input → TermNetAgent
    ↓
    ├── BMAD Command Detection
    │   └── Specialized Agent Routing
    ├── Tool Selection
    │   ├── Terminal Execution
    │   ├── Browser Operations
    │   └── Scratchpad Management
    ├── LLM Processing
    │   ├── Claude Code CLI (Priority 1)
    │   ├── OpenRouter API (Priority 2)
    │   └── Ollama (Legacy)
    └── Validation Pipeline
        ├── Command Safety Check
        ├── Output Validation
        └── History Recording
```

## File Structure

```
TermNet/
├── termnet/
│   ├── __init__.py
│   ├── agent.py                 # Main orchestrator
│   ├── config.py                # Config loader
│   ├── config.json              # Settings
│   ├── toolloader.py            # Dynamic tool loading
│   ├── toolregistry.json        # Tool definitions
│   ├── safety.py                # Command safety
│   ├── memory.py                # Context management
│   ├── validation_engine.py     # Core validation
│   ├── validation_monitor.py    # Real-time monitoring
│   ├── validation_rules.py      # Basic rules
│   ├── validation_rules_advanced.py # Advanced rules
│   ├── claude_code_client.py    # Claude CLI integration
│   ├── openrouter_client.py     # OpenRouter API
│   ├── bmad_integration.py      # BMAD-METHOD bridge
│   └── tools/
│       ├── __init__.py
│       ├── terminal.py          # Command execution
│       ├── browsersearch.py     # Web operations
│       └── scratchpad.py        # Note management
├── tests/
│   ├── test_agent.py
│   ├── test_integration.py
│   ├── test_memory.py
│   ├── test_safety.py
│   ├── test_toolloader.py
│   └── test_tools.py
├── .bmad-core/                  # BMAD-METHOD system
└── run_termnet_openrouter.py    # Main launcher
```

## Key Features

### 1. Multi-Provider LLM Support
- Seamless switching between Claude Code, OpenRouter, and Ollama
- Automatic fallback on provider failure
- Model-specific optimizations (GPT-OSS parsing)

### 2. Advanced Tool Ecosystem
- Runtime tool discovery and loading
- Async execution with timeout control
- Safety validation layer
- Context-aware tool selection

### 3. Validation & Monitoring
- Real-time file change detection
- Automated validation triggers
- Historical performance tracking
- Multi-level severity reporting

### 4. BMAD-METHOD Integration
- Autonomous workflow execution
- Specialized agent routing
- State persistence across sessions
- Progress tracking and reporting

### 5. Security & Safety
- Command pattern filtering
- Destructive operation prevention
- OAuth token management
- SSL context handling

## Configuration Priorities

1. **Claude Code CLI** (Primary)
   - Direct integration with user's Claude subscription
   - OAuth token authentication
   - Full tool support

2. **OpenRouter API** (Secondary)
   - Cloud-based fallback
   - Multiple model support
   - API key authentication

3. **Ollama** (Legacy)
   - Local model execution
   - Limited tool support
   - Deprecated in favor of cloud solutions

## Database Schemas

### Validation Database
- `validation_runs`: Execution metadata
- `validation_results`: Individual rule results
- Performance metrics and history

### Monitor Database
- Real-time validation tracking
- File change events
- Statistical analysis

## Performance Characteristics

- **Command Timeout**: 60 seconds default
- **Max AI Steps**: 20 iterations per conversation
- **Memory Window**: 12 messages retained
- **Cache TTL**: 60 seconds
- **Stream Delay**: 0ms (real-time)
- **Max Output**: 4000 characters

## Security Considerations

- OAuth tokens stored in environment variables
- SSL certificate verification (configurable)
- Command safety validation
- Dangerous pattern detection
- API key encryption recommendations

## Testing Infrastructure

- Unit tests for core components
- Integration tests for tool execution
- Memory management tests
- Safety checker validation
- Tool loader verification

## Future Enhancements

### Planned Features
- Enhanced GPT-OSS model support
- Additional validation rules
- Improved BMAD workflow templates
- Extended browser automation capabilities
- Multi-user session management

### Architecture Improvements
- Plugin-based tool system
- Distributed validation processing
- Enhanced caching strategies
- WebSocket-based streaming
- Container-based isolation

## Dependencies

### Core Requirements
- Python 3.8+
- asyncio for async operations
- aiohttp for HTTP client
- playwright for browser automation
- BeautifulSoup4 for HTML parsing
- watchdog for file monitoring
- SQLite3 for data persistence

### Optional Integrations
- Claude Code CLI
- OpenRouter API access
- BMAD-METHOD system
- Ollama (deprecated)

## Deployment Considerations

- Single-user terminal application
- Local file system access required
- Network connectivity for cloud LLMs
- Browser automation requires display server
- SQLite databases for local storage

---

This architecture enables TermNet to function as a comprehensive AI terminal assistant with advanced capabilities for command execution, web interaction, validation, and autonomous development workflows through BMAD-METHOD integration.
