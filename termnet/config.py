"""Robust config loader with deep merge and multi-source priority."""
import json
import os
from pathlib import Path


def _deep_merge(a, b):
    """Deep merge dict b into dict a."""
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(a.get(k), dict):
            _deep_merge(a[k], v)
        else:
            a[k] = v
    return a


def _load_config():
    """Load config from multiple sources with priority order."""
    root = Path(__file__).resolve().parents[1]
    candidates = []

    # Highest priority: TERMNET_CONFIG env var
    env_path = os.environ.get("TERMNET_CONFIG")
    if env_path:
        candidates.append(Path(env_path))

    # Repo root configs
    candidates += [root / ".termnet.json", root / "termnet" / "config.json"]

    # Current working directory fallbacks
    candidates += [Path.cwd() / ".termnet.json", Path.cwd() / "config.json"]

    cfg = {}
    for p in candidates:
        try:
            if p and p.exists():
                data = json.loads(p.read_text())
                _deep_merge(cfg, data)
                cfg["_path"] = str(p)
        except Exception:
            # Ignore corrupt config; continue to next candidate
            pass

    # Set sensible defaults
    cfg.setdefault("audit", {"enabled": False, "min_score": 0.7})
    cfg.setdefault("models", {})
    cfg.setdefault("providers", {})
    cfg.setdefault("USE_CLAUDE_CODE", False)
    cfg.setdefault("USE_CLAUDE", False)
    cfg.setdefault("USE_OPENROUTER", False)
    cfg.setdefault("CLAUDE_CLI_PATH", "")
    cfg.setdefault("CLAUDE_CODE_OAUTH_TOKEN", "")
    cfg.setdefault("CLAUDE_BASE_URL", "https://api.anthropic.com")
    cfg.setdefault("OPENROUTER_API_KEY", "")
    cfg.setdefault("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    cfg.setdefault("OLLAMA_URL", "http://127.0.0.1:11434")
    cfg.setdefault("MODEL_NAME", "claude-3-5-sonnet")
    cfg.setdefault("CLAUDE_MODEL", "")
    cfg.setdefault("LLM_TEMPERATURE", 0.7)
    cfg.setdefault("MAX_AI_STEPS", 20)
    cfg.setdefault("COMMAND_TIMEOUT", 60)
    cfg.setdefault("MAX_OUTPUT_LENGTH", 4000)
    cfg.setdefault("MEMORY_WINDOW", 12)
    cfg.setdefault("MEMORY_SUMMARY_LIMIT", 1000)
    cfg.setdefault("CACHE_TTL_SEC", 60)
    cfg.setdefault("STREAM_CHUNK_DELAY", 0)
    cfg.setdefault("CONVERSATION_MEMORY_SIZE", 10)

    return cfg


CONFIG = _load_config()
