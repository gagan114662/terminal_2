import time
from dataclasses import dataclass, field
from typing import Any


class StepType:
    PLAN = "plan"
    ACTION = "action"
    OBSERVATION = "observation"
    REFLECTION = "reflection"
    ERROR = "error"


@dataclass
class MemoryStep:
    step_type: str
    content: str
    context: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    success: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


class ConversationMemory:
    """Lightweight conversation memory for test compatibility"""

    def __init__(self):
        self.history: list[tuple[str, str]] = []

    def add(self, role: str, text: str) -> None:
        """Add a conversation entry"""
        self.history.append((role, text))

    def get_history(self, limit: int | None = None) -> list[tuple[str, str]]:
        """Get conversation history, optionally limited"""
        if limit is None:
            return self.history.copy()
        return self.history[-limit:] if limit > 0 else []

    def clear(self) -> None:
        """Clear conversation history"""
        self.history.clear()
