"""JSON serialization helper for custom objects"""
import json
from datetime import datetime
from typing import Any


class TermNetJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for TermNet objects"""

    def default(self, obj: Any) -> Any:
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, "_asdict"):  # namedtuples
            return obj._asdict()
        elif isinstance(obj, set):
            return list(obj)
        elif hasattr(obj, "to_dict"):
            return obj.to_dict()
        return super().default(obj)


def safe_json_dumps(obj: Any, **kwargs) -> str:
    """Safely serialize objects to JSON with fallbacks"""
    return json.dumps(obj, cls=TermNetJSONEncoder, **kwargs)


def safe_json_save(obj: Any, filepath: str, max_size: int = 200000) -> None:
    """Save object to JSON file with size limit"""
    content = safe_json_dumps(obj, indent=2)
    if len(content) > max_size:
        content = content[:max_size] + "...[truncated]"
    with open(filepath, "w") as f:
        f.write(content)
