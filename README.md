# TermNet

TermNet is an **AI-powered terminal assistant** that connects a Large Language Model (LLM) with shell command execution, browser search, and dynamically loaded tools.
It streams responses in real-time, executes tools one at a time, and maintains conversational memory across steps.

⚠️ **Disclaimer:** This project is experimental. **Use at your own risk.**

⚠️ **Note:** This has only been tested with GPT-OSS Models. **Your models may behave differently.**

---

## ✨ Features

- 🖥️ **Terminal integration**
  Safely execute shell commands with sandboxed handling, timeout control, and a built-in safety filter that blocks destructive commands (`rm -rf /`, `shutdown`, etc.).

- 🔧 **Dynamic tool loading**
  Easily extend functionality by editing `toolregistry.json`. No need to modify core files — tools are auto-discovered.

- 🌐 **Browser search**
  Use Playwright-powered search and page scraping to fetch information dynamically from the web.

- 🧠 **Memory system**
  Tracks the agent's planning, actions, observations, reflections, and errors across multiple steps.

- ⚡ **Streaming LLM output**
  Integrates with [Ollama](https://ollama.ai) for real-time streaming chat responses.

- 🛡️ **Safety layer**
  Risky commands (e.g., `rm`, `chmod`, `mv`) are not blocked, but the agent provides clear warnings before running them.

- 🚫 **Phase 3: No False Claims Enhancement** *(NEW)*
  Advanced claim verification system with evidence tracking, 6-stage command lifecycle, sandbox security, policy engine, and auditor agent to prevent AI hallucinations and false claims.

- 📊 **Trajectory Logging** *(NEW)*
  Comprehensive trajectory logging system that captures reasoning, action, and observation phases in structured JSONL format for analysis and debugging.

- 🔀 **BMAD Stream Integration** *(NEW)*
  Bridge component that translates BMAD/METHOD stream events into trajectory steps with phase mapping and secure argument redaction.

- 🎯 **SLO Monitoring** *(NEW)*
  Service Level Objective monitoring with configurable latency thresholds and regression detection for performance tracking.

- 🔧 **Offline Mode Support** *(NEW)*
  All tools support offline mode for deterministic testing without external dependencies or file I/O operations.

- ✅ **Comprehensive Test Suite** *(NEW)*
  High-leverage test categories including trajectory logging, BMAD bridge mapping, tool contracts, safety regression edges, and end-to-end agent functionality.

---

## 📂 Project Structure

~~~~
termnet/
├── agent.py                    # Core TermNetAgent: manages chat loop, tool calls, and LLM streaming
├── main.py                     # CLI entrypoint for running the agent
├── config.py                   # Loads configuration from config.json
├── config.json                 # Model and runtime configuration
├── memory.py                   # Memory system for reasoning steps
├── safety.py                   # Safety checker for shell commands
├── toolloader.py               # Dynamic tool importer based on toolregistry.json
├── toolregistry.json           # Registered tools & their schemas
├── browsersearch.py            # Browser search & scraping tool (Playwright + BeautifulSoup)
├── scratchpad.py               # Note-taking / planning scratchpad
├── terminal.py                 # Terminal session wrapper with safety & timeout handling
├── trajectory_logger.py        # NEW: Trajectory logging with JSONL output
├── bmad_trajectory_bridge.py   # NEW: BMAD stream event bridge with phase mapping
├── trend_analysis.py           # NEW: SLO monitoring and trend analysis
├── claims_engine.py            # Phase 3: Claims & evidence tracking system (477 lines)
├── command_lifecycle.py        # Phase 3: 6-stage command execution pipeline (769 lines)
├── sandbox.py                  # Phase 3: Advanced sandboxing & security (748 lines)
├── command_policy.py           # Phase 3: Policy engine with 26+ rules (720 lines)
├── auditor_agent.py            # Phase 3: 7th BMAD agent for claim auditing (530 lines)
├── tools/
│   ├── terminal.py             # Phase 3: Enhanced terminal with validation layer (330 lines)
│   ├── scratchpad.py           # Enhanced scratchpad with offline mode support
│   └── browsersearch.py        # Enhanced browser search with offline mode
├── scripts/
│   └── slo_check.py            # NEW: SLO regression monitoring script
├── tests/                      # NEW: Comprehensive test suite
│   ├── test_trajectory_logger.py        # Trajectory logging unit tests
│   ├── test_bmad_bridge.py              # BMAD bridge mapping tests
│   ├── test_scratchpad_offline.py       # Scratchpad offline mode tests
│   ├── test_tool_contracts.py           # Tool contract invariant tests
│   ├── test_safety_regression_edges.py  # Safety edge case regression tests
│   ├── test_slo_guard_pytest.py         # SLO guard pytest integration
│   └── test_minimal_agent_smoke.py      # End-to-end agent smoke tests
└── artifacts/
    └── last_run/
        └── trajectory.jsonl    # NEW: Trajectory logs in JSONL format
~~~~

**Phase 3 Enhancement:** 3,244+ lines of code implementing a comprehensive "No False Claims" system.

**NEW Enhancements:** Trajectory logging, BMAD stream integration, SLO monitoring, offline mode support, and comprehensive test suite with 8 high-leverage test categories covering edge cases, contracts, and end-to-end functionality.

---

## ⚙️ Installation

### Requirements

- Python **3.9+** (tested with Python 3.13)
- [Ollama](https://ollama.ai) running locally or accessible via API
- Chromium (installed automatically by Playwright)
- pytest (for running the comprehensive test suite)

### Setup

1. Clone the repository:

   ~~~~bash
   git clone https://github.com/RawdodReverend/TermNet.git
   cd termnet
   ~~~~

2. Create and activate virtual environment:

   ~~~~bash
   python3 -m venv venv_openrouter
   source venv_openrouter/bin/activate  # On Windows: venv_openrouter\Scripts\activate
   ~~~~

3. Install dependencies:

   ~~~~bash
   pip install -r requirements.txt
   pip install psutil  # Required for Phase 3 sandbox system
   ~~~~

4. Install Playwright browser binaries:

   ~~~~bash
   playwright install chromium
   ~~~~

5. Verify Phase 3 installation:

   ~~~~bash
   ./verify_phase3_build.sh
   ~~~~

6. Run the comprehensive test suite:

   ~~~~bash
   python -m pytest tests/ -v
   ~~~~

7. Check SLO performance:

   ~~~~bash
   python scripts/slo_check.py
   ~~~~

---

## 🚀 Usage

You can start TermNet in two ways:

### Directly with Python

~~~~bash
python -m termnet.main
~~~~

or (depending on your system):

~~~~bash
python3 -m termnet.main
~~~~

### With the provided script

On Linux/macOS:

~~~~bash
./run.sh
~~~~

On Windows:

~~~~bat
run.bat
~~~~

### Chatting

- Type natural language queries.
- TermNet may:
  - Suggest and run safe terminal commands
  - Search the web via `browser_search`
  - Use custom tools defined in `toolregistry.json`
- Exit at any time with:

~~~~bash
exit
~~~~

---

## ⚙️ Configuration

Configuration is stored in `config.json`.

| Key                | Description                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| `OLLAMA_URL`       | Base URL for the Ollama server (default: `http://127.0.0.1:11434`)          |
| `MODEL_NAME`       | The model name/tag to use (e.g., `gpt-oss:20b`)                             |
| `LLM_TEMPERATURE`  | Randomness in responses (0 = deterministic, 1 = creative)                   |
| `MAX_AI_STEPS`     | Maximum reasoning/tool-execution steps per user query                       |
| `COMMAND_TIMEOUT`  | Max seconds allowed for a terminal command before being killed              |
| `MAX_OUTPUT_LENGTH`| Maximum number of characters per LLM response                               |
| `MEMORY_WINDOW`    | Number of past interactions kept in context                                 |
| `MEMORY_SUMMARY_LIMIT` | Max characters when summarizing memory                                  |
| `CACHE_TTL_SEC`    | Time-to-live for cached tool results                                        |
| `STREAM_CHUNK_DELAY` | Delay between streamed chunks of LLM output                               |

To change models or API endpoints, edit this file and restart TermNet.

---

## 🛠️ Adding Tools

Tools are defined in `toolregistry.json` and implemented in `termnet/tools/`.

### 1. Register the tool
Add a new JSON entry in `toolregistry.json`:

~~~~json
{
  "type": "function",
  "function": {
    "name": "my_custom_tool",
    "description": "Describe what this tool does",
    "module": "mytool",
    "class": "MyTool",
    "method": "run",
    "parameters": {
      "type": "object",
      "properties": {
        "arg1": { "type": "string" }
      },
      "required": ["arg1"]
    }
  }
}
~~~~

### 2. Implement the tool
Create `termnet/tools/mytool.py`:

~~~~python
class MyTool:
    async def run(self, arg1: str):
        return f"Tool executed with arg1={arg1}"
~~~~

### 3. Run TermNet
The tool will auto-load at startup:

~~~~bash
python -m termnet.main
~~~~

✅ No need to edit the agent itself — tools are discovered dynamically.

---

## ⚠️ Safety Notes

- Dangerous commands (like `rm -rf /`) are **blocked**.
- Risky commands (like `rm`, `mv`, `chmod`) are **allowed with warnings**.
- Always review what the agent suggests before execution.

### Phase 3 Security Features

- **Claims Engine**: Tracks and verifies all AI assertions with evidence
- **6-Stage Lifecycle**: Pre-validation → Execution → Post-validation → Evidence → Audit → Archive
- **Sandbox System**: Isolated execution environments with resource monitoring
- **Policy Engine**: 26+ security rules governing command execution
- **Auditor Agent**: 7th BMAD agent that audits claims for accuracy
- **Evidence Tracking**: Automatic collection of logs, screenshots, and transcripts

### Phase 3 Databases

- `termnet_claims.db` - Claims and evidence tracking
- `termnet_validation.db` - Command validation results
- `termnet_audit_findings.db` - Audit findings and reports
- `artifacts/` - Evidence collection directory
- `artifacts/last_run/trajectory.jsonl` - Trajectory logs in structured JSONL format

### Testing & Quality Assurance

The project includes a comprehensive test suite with 8 high-leverage test categories:

1. **Trajectory Logging Tests** - Unit tests for JSONL trajectory capture
2. **BMAD Bridge Tests** - Stream event processing and phase mapping
3. **Scratchpad Offline Tests** - Deterministic offline mode functionality
4. **Tool Contract Tests** - Contract invariants for all tools
5. **Safety Regression Tests** - Edge cases like command substitution, unicode attacks, path traversal
6. **SLO Guard Integration** - Performance monitoring and regression detection
7. **Agent Smoke Tests** - End-to-end functionality validation
8. **Safety Edge Cases** - Advanced attack patterns and evasion techniques

Run specific test categories:

~~~~bash
# Trajectory logging tests
python -m pytest tests/test_trajectory_logger.py -v

# Safety regression edge cases
python -m pytest tests/test_safety_regression_edges.py -v

# SLO monitoring integration
python -m pytest tests/test_slo_guard_pytest.py -v

# End-to-end agent functionality
python -m pytest tests/test_minimal_agent_smoke.py -v
~~~~

### Performance Monitoring

Monitor system performance with SLO thresholds:

~~~~bash
# Check current trajectory latencies
python scripts/slo_check.py

# Run with custom trajectory file
python scripts/slo_check.py /path/to/trajectory.jsonl

# Enable SLO enforcement during tests
TERMNET_ENFORCE_SLO=true python -m pytest tests/test_slo_guard_pytest.py
~~~~

---

## 📜 License

This project is licensed under the MIT License.
See LICENSE for details.
