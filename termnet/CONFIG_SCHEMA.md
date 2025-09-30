# Claude Code Configuration Schema

This document defines the configuration schema for Claude Code settings used in the TermNet project.

## Configuration Structure

### 1. Model Configuration (`model_config`)
```json
{
  "model": "claude-3.5-sonnet",        // LLM model identifier
  "temperature": 0.7,                  // Randomness in responses (0.0-1.0)
  "top_p": 0.95,                       // Nucleus sampling threshold
  "max_output_tokens": 4096,           // Maximum tokens per response
  "reasoning_tokens_budget": 8192      // Token budget for reasoning in long edits
}
```

### 2. Timeout Configuration (`timeout_config`)
```json
{
  "per_call_timeout_ms": 30000,        // LLM request timeout (30s)
  "tool_timeout_ms": 15000,            // Tool execution timeout (15s)
  "session_timeout_ms": 600000         // End-to-end task cap (10min)
}
```

### 3. Retry & Rate Limits (`retry_limits`)
```json
{
  "max_retries": 3,                    // Maximum retry attempts
  "retry_backoff_ms": 1000,            // Exponential backoff base (ms)
  "global_qps_limit": 10,              // Queries per second limit
  "concurrency_limit": 5,              // Max concurrent operations
  "daily_token_budget": 500000         // Daily token soft cap
}
```

### 4. Context Configuration (`context_config`)
Defines codebase scope and context window management:
- `context_include_globs`: File patterns to include in context
- `context_exclude_globs`: File patterns to exclude from context
- `max_context_files`: Maximum files to include (100)
- `max_file_size_kb`: Maximum size per file (512KB)
- `embedding_index_enabled`: Enable pre-indexing (true/false)
- `embedding_index_size`: Size of embedding index

### 5. Write Guardrails (`write_guardrails`)
Controls where and how files can be modified:
- `write_allowlist_paths`: Paths where edits are allowed
- `write_blocklist_paths`: Paths where edits are forbidden
- `max_files_per_change`: Maximum files per change operation
- `max_total_patch_bytes`: Maximum total patch size
- `dry_run`: Generate patches without applying
- `require_safe_mode`: Block dangerous shell commands

### 6. Git/PR Policy (`git_pr_policy`)
```json
{
  "branch_prefix": "feature/",         // Branch naming prefix
  "commit_style": "conventional",      // Commit message format
  "max_lines_per_commit": 500,        // Line limit per commit
  "squash_commits": false,            // Auto-squash commits
  "pr_autocreate": false,             // Auto-create PRs
  "required_status_checks": [...]     // Required CI checks
}
```

### 7. Review & Checks (`review_checks`)
```json
{
  "coderabbit_ci_required": false,    // Require CodeRabbit CI
  "coderabbit_fail_on": {             // Failure thresholds
    "security": "high",
    "style": "off",
    "complexity": "medium"
  },
  "block_merge_on_review_fail": true  // Block merge on failure
}
```

### 8. Safety Configuration (`safety_config`)
- `allowed_tools`: List of permitted tools
- `blocked_commands`: Dangerous commands to block
- `secrets_redaction`: Enable/disable secret redaction
- `secrets_patterns`: Regex patterns for detecting secrets
- `network_egress_policy`: Network access policy
- `allowed_domains`: Whitelisted domains for network access

### 9. Tracing & Artifacts (`tracing_artifacts`)
```json
{
  "trace_enabled": true,               // Enable tracing
  "trace_sample_rate": 1.0,           // Sampling rate (0.0-1.0)
  "artifacts_dir": "artifacts/last_run", // Artifact storage location
  "store_diffs": true,                // Store code diffs
  "store_trajectory": true,           // Store execution trajectory
  "log_level": "info"                 // Logging verbosity
}
```

## Environment Variables

Sensitive values can be configured via environment variables (see `.env.example`):

- `CLAUDE_API_KEY`: Claude API authentication key
- `GITHUB_TOKEN`: GitHub personal access token
- `DAILY_TOKEN_BUDGET`: Override daily token limit
- `SESSION_TIMEOUT_MS`: Override session timeout
- `REQUIRE_SAFE_MODE`: Force safe mode
- `TRACE_ENABLED`: Enable/disable tracing
- `LOG_LEVEL`: Set logging level

## Usage

1. Copy `config.json` to customize settings
2. Create `.env` from `.env.example` for sensitive values
3. TermNet will automatically load and merge configurations

## Safety Notes

- Never commit `.env` files with real credentials
- Use `write_blocklist_paths` to protect system directories
- Enable `require_safe_mode` in production environments
- Configure `secrets_patterns` to catch common secret formats
- Set `network_egress_policy` to "deny_all" unless required

## Integration with TermNet

TermNet's agent and safety layers will:
1. Load `config.json` on initialization
2. Override with environment variables from `.env`
3. Apply safety guardrails before tool execution
4. Enforce rate limits and timeouts
5. Log traces to `artifacts_dir` when enabled