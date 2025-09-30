# Terminal 2 Codebase Index

## Project Overview
Terminal 2 is a GPU compute infrastructure project with the TermNet AI assistant system. The project combines GPU acceleration scripts, SSH connectivity, and an advanced AI-powered terminal assistant with comprehensive security and validation features.

## Directory Structure

### Root Directory (`/`)
- **GPU Compute Scripts**
  - `gpu_access.py` - GPU access management
  - `gpu_compute_example.py` - Example GPU computation implementation
  - `gpu_monitor.py` - GPU monitoring utilities
  - `run_gpt_gpu.py` - GPT GPU execution runner

- **GPT OSS Integration**
  - `Modelfile.gpt-oss-optimized` - Optimized GPT-OSS model configuration
  - `fix_gpt_oss.py` - GPT-OSS fix utilities
  - `gpt_oss_openrouter.py` - OpenRouter integration for GPT-OSS
  - `gpt_oss_*.sh` - Various shell scripts for GPT-OSS operations

- **SSH & Connection Scripts**
  - `connect_ssh_gpu.sh` - SSH GPU connection script
  - `ssh_gpu.sh` - SSH GPU utilities
  - `ssh_gpt_setup.sh` - SSH GPT setup script
  - `ssh_gpt_openrouter.sh` - SSH OpenRouter setup

- **Verification Scripts**
  - `termnet_verify.py` - TermNet verification utilities
  - `verify_termnet_claims.py` - Claims verification script

### TermNet Directory (`/TermNet/`)

#### Core System Components
- **Main Application**
  - `termnet/agent.py` - Core TermNetAgent: manages chat loop, tool calls, and LLM streaming
  - `termnet/main.py` - CLI entrypoint for running the agent
  - `termnet/config.py` - Configuration loader
  - `termnet/config.json` - Model and runtime configuration

- **Memory & State Management**
  - `termnet/memory.py` - Memory system for reasoning steps

- **Tool System**
  - `termnet/toolloader.py` - Dynamic tool importer
  - `termnet/toolregistry.json` - Registered tools & their schemas
  - `termnet/tools/` - Tool implementations directory
    - `terminal.py` - Enhanced terminal with validation (330 lines)
    - `browsersearch.py` - Browser search & scraping (Playwright + BeautifulSoup)
    - `scratchpad.py` - Note-taking/planning scratchpad
    - `scratchpad.json` - Scratchpad configuration

#### Phase 3: No False Claims System (3,244+ lines)
- **Claims & Evidence**
  - `termnet/claims_engine.py` - Claims & evidence tracking (477 lines)
  - `termnet/validation_engine.py` - Validation engine implementation
  - `termnet/validation_rules.py` - Validation rule definitions
  - `termnet/validation_monitor.py` - Validation monitoring system

- **Command Lifecycle & Security**
  - `termnet/command_lifecycle.py` - 6-stage command execution pipeline (769 lines)
  - `termnet/command_policy.py` - Policy engine with 26+ rules (720 lines)
  - `termnet/sandbox.py` - Advanced sandboxing & security (748 lines)
  - `termnet/security_validation.py` - Security validation layer

- **Auditing**
  - `termnet/auditor_agent.py` - 7th BMAD agent for claim auditing (530 lines)

- **Integration**
  - `termnet/bmad_integration.py` - BMAD system integration
  - `termnet/claude_code_client.py` - Claude Code client
  - `termnet/claude_code_client_enhanced.py` - Enhanced Claude Code client
  - `termnet/openrouter_client.py` - OpenRouter API client

#### Test Suite
- **Unit Tests**
  - `test_termnet_agent_tools.py` - Agent tools testing
  - `test_termnet_simple.py` - Simple functionality tests
  - `test_termnet_tools_detailed.py` - Detailed tool testing
  - `test_validation_*.py` - Various validation tests
  - `test_terminal_validation.py` - Terminal validation tests

- **Integration Tests**
  - `test_auth_api.py` - Authentication API tests
  - `test_blog.py` - Blog functionality tests
  - `test_flask_api.py` - Flask API tests
  - `test_web_search.py` - Web search functionality tests

- **OpenRouter Tests**
  - `test_openrouter.py` - OpenRouter integration tests
  - `test_gpt_oss_tool.py` - GPT-OSS tool tests

#### Applications & Examples
- **Web Applications**
  - `auth_api.py` - Authentication API implementation
  - `blog_app.py` - Blog application
  - `flask_app.py` - Basic Flask application
  - `flask_app_with_models.py` - Flask app with models
  - `simple_blog.py` - Simple blog implementation
  - `todo_app.py` - Todo application
  - `user_api.py` - User API
  - `user_management_api.py` - User management API

- **Monitoring & Debugging**
  - `cpu_monitor.py` - CPU monitoring
  - `cpu_monitor_logger.py` - CPU monitor with logging
  - `debug_regex.py` - Regex debugging utilities

#### Build & Deployment
- **Docker**
  - `Dockerfile` - Main container configuration
  - `Dockerfile.scanner` - Scanner container configuration
  - `docker-compose.yml` - Docker compose configuration

- **Build System**
  - `Makefile` - Build automation (current)
  - `Makefile.bak` - Makefile backup
  - `test_makefile.mk` - Test makefile

- **CI/CD**
  - `.pre-commit-config.yaml` - Pre-commit hooks configuration
  - `pytest.ini` - Pytest configuration

#### Databases
- `termnet_claims.db` - Claims and evidence tracking
- `termnet_validation.db` - Command validation results
- `termnet_audit_findings.db` - Audit findings and reports
- `termnet_trends.db` - Trends and analytics
- `integration_test.db` - Integration test data
- `todos.db` - Todo application database
- Various test databases (`test_*.db`)

#### Documentation
- `README.md` - Main project documentation
- `README_BLOG.md` - Blog application documentation
- `TERMNET_COMPLETE_STRUCTURE.md` - Complete structure documentation
- `TERMNET_STRUCTURE_REPORT.md` - Structure report
- `TESTING.md` - Testing documentation
- `TEST_RESULTS_SUMMARY.md` - Test results summary
- `OPENROUTER_SETUP.md` - OpenRouter setup guide
- `learn.md` - Learning resources

#### Scripts & Utilities
- **Shell Scripts**
  - `run.sh` - Linux/macOS runner
  - `run.bat` - Windows runner
  - `verify_phase3_build.sh` - Phase 3 build verification

- **Python Scripts**
  - `run_termnet_openrouter.py` - OpenRouter runner
  - `run_validation.py` - Validation runner
  - `quick_validation_example.py` - Quick validation example

#### Dependencies
- `requirements.txt` - Main Python dependencies
- `requirements-dev.txt` - Development dependencies
- `auth_requirements.txt` - Auth module dependencies
- `blog_requirements.txt` - Blog module dependencies
- `requirements_flask.txt` - Flask dependencies
- `todo_requirements.txt` - Todo app dependencies

#### Directories
- `artifacts/` - Evidence collection directory
- `static/` - Static web assets
- `templates/` - HTML templates
- `instance/` - Instance-specific data
- `scripts/` - Utility scripts
- `security/` - Security-related files
- `tests/` - Additional test files
- `.bmad-core/` - BMAD core files
- `venv_openrouter/` - Python virtual environment

## Key Features

### 1. GPU Compute Infrastructure
- GPU access management and monitoring
- SSH connectivity for remote GPU resources
- GPT-OSS model integration and optimization

### 2. TermNet AI Assistant
- **Core Features**
  - Terminal integration with safety controls
  - Dynamic tool loading system
  - Browser search capabilities
  - Memory system for conversation tracking
  - Streaming LLM output via Ollama

### 3. Phase 3 Security Enhancement
- **Claims Verification System**
  - Evidence-based claim tracking
  - 6-stage command lifecycle validation
  - Advanced sandboxing with resource monitoring
  - Policy engine with 26+ security rules
  - Auditor agent for claim verification

### 4. Tool Ecosystem
- Terminal execution with validation
- Web scraping and search
- Scratchpad for planning
- Extensible tool registry

### 5. Applications
- Authentication API
- Blog platform
- Todo application
- User management system
- Flask-based web services

## Database Schema
- Claims tracking database
- Validation results storage
- Audit findings repository
- Trends and analytics data
- Application-specific databases

## Testing Infrastructure
- Comprehensive unit tests
- Integration testing suite
- Validation system tests
- Performance testing
- OpenRouter integration tests

## Build & Deployment
- Docker containerization
- Makefile automation
- Pre-commit hooks
- CI/CD pipeline support

## Configuration
- Centralized config management
- Model configuration
- Tool registry
- Security policies
- Environment-specific settings