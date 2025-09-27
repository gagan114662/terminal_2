import json
from pathlib import Path

# Default config - hardcoded to avoid file operations issues
DEFAULT_CONFIG = {
    "USE_CLAUDE_CODE": False,
    "USE_CLAUDE": False,
    "USE_OPENROUTER": False,
    "CLAUDE_CLI_PATH": "",
    "CLAUDE_CODE_OAUTH_TOKEN": "",
    "CLAUDE_BASE_URL": "https://api.anthropic.com",
    "OPENROUTER_API_KEY": "",
    "OPENROUTER_BASE_URL": "https://openrouter.ai/api/v1",
    "OLLAMA_URL": "http://127.0.0.1:11434",
    "MODEL_NAME": "claude-3-5-sonnet",
    "CLAUDE_MODEL": "",
    "LLM_TEMPERATURE": 0.7,
    "MAX_AI_STEPS": 20,
    "COMMAND_TIMEOUT": 60,
    "MAX_OUTPUT_LENGTH": 4000,
    "MEMORY_WINDOW": 12,
    "MEMORY_SUMMARY_LIMIT": 1000,
    "CACHE_TTL_SEC": 60,
    "STREAM_CHUNK_DELAY": 0,
    "CONVERSATION_MEMORY_SIZE": 10,
}


def load_config():
    """Load configuration from config.json, falling back to defaults"""
    config = DEFAULT_CONFIG.copy()

    # Try to find config.json in the termnet directory
    config_path = Path(__file__).parent / "config.json"

    try:
        if config_path.exists():
            with open(config_path, "r") as f:
                file_config = json.load(f)
                config.update(file_config)
    except Exception as e:
        print(f"Warning: Could not load config.json: {e}")

    return config


CONFIG = load_config()
