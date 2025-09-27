import json
import pathlib
from typing import Any, Dict, List, Tuple

DATA_FILE = pathlib.Path(__file__).parent / "scratchpad.json"


class Scratchpad:
    def __init__(self):
        self._notes: List[str] = []
        self._load_notes()

    def _load_notes(self):
        """Load notes from disk if the file exists"""
        if DATA_FILE.exists():
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self._notes = json.load(f)
            except Exception:
                # If the file is corrupted or unreadable, reset
                self._notes = []

    def _save_notes(self):
        """Save notes to disk"""
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self._notes, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Failed to save scratchpad: {e}")

    async def start(self) -> bool:
        return True

    async def stop(self):
        return

    async def run(self, action: str, content: str = "") -> Tuple[str, int, bool]:
        # Normalize action names
        action = action.strip().lower().replace(" ", "_")

        if action == "write":
            self._notes.append(content)
            self._save_notes()
            return f'📝 Note added: "{content}"', 0, True

        elif action in ("read_all", "read", "read_all_notes"):
            if not self._notes:
                return "📖 Scratchpad is empty.", 0, True
            notes_text = "\n".join(f"{i + 1}. {n}" for i, n in enumerate(self._notes))
            return f"📖 Scratchpad contents:\n{notes_text}", 0, True

        elif action == "clear":
            self._notes.clear()
            self._save_notes()
            return "🗑️ Scratchpad cleared.", 0, True

        else:
            return f"❌ Unknown action: {action}", 1, False

    # ✅ Alias so TermNetAgent can find a method named "scratchpad"
    async def scratchpad(self, **kwargs):
        return await self.run(**kwargs)

    def get_context_info(self) -> Dict[str, Any]:
        return {
            "notes_count": len(self._notes),
            "last_note": self._notes[-1] if self._notes else None,
        }


class ScratchpadTool:
    """Test-compatible wrapper for scratchpad functionality"""

    def __init__(self):
        self._notes_dict: Dict[str, str] = {}

    @property
    def notes(self) -> Dict[str, str]:
        """Notes dictionary for test compatibility"""
        return self._notes_dict

    def write(self, key: str, content: str) -> str:
        """Write a note with key-value pair"""
        self._notes_dict[key] = content
        return f"Saved note '{key}'"

    def read(self, key: str) -> str:
        """Read a note by key"""
        if key in self._notes_dict:
            return self._notes_dict[key]
        return f"Note '{key}' not found"

    def list(self) -> str:
        """List all notes"""
        if not self._notes_dict:
            return "No notes available"

        notes_list = []
        for key, content in self._notes_dict.items():
            # Truncate long content for listing
            display_content = content[:50] + "..." if len(content) > 50 else content
            notes_list.append(f"  {key}: {display_content}")

        return "Notes:\n" + "\n".join(notes_list)

    def run(self, key: str, content: str) -> dict:
        """Store note and return dict result for compatibility"""
        self._notes_dict[key] = content
        return {"status": "success", "message": f"Stored note '{key}'"}

    def append(self, key: str, content: str) -> dict:
        """Append content to existing note or create new one"""
        if key in self._notes_dict:
            self._notes_dict[key] += "\n" + content
            return {"status": "success", "message": f"Appended to note '{key}'"}
        else:
            self._notes_dict[key] = content
            return {"status": "success", "message": f"Created new note '{key}'"}

    def delete(self, key: str) -> dict:
        """Delete a note by key"""
        if key in self._notes_dict:
            del self._notes_dict[key]
            return {"status": "success", "message": f"Deleted note '{key}'"}
        else:
            return {"status": "error", "message": f"Note '{key}' not found"}

    def clear(self) -> dict:
        """Clear all notes"""
        count = len(self._notes_dict)
        self._notes_dict.clear()
        return {"status": "success", "message": f"Cleared {count} notes"}

    def search(self, query: str) -> list:
        """Search notes by content or key"""
        results = []
        query_lower = query.lower()

        for key, content in self._notes_dict.items():
            if query_lower in key.lower() or query_lower in content.lower():
                results.append(
                    {
                        "key": key,
                        "content": content,
                        "match_type": (
                            "key" if query_lower in key.lower() else "content"
                        ),
                    }
                )

        return results

    def get_definition(self) -> dict:
        """Get tool definition for registration"""
        return {
            "name": "scratchpad",
            "description": "Store, retrieve, and manage freeform notes",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "write",
                            "read",
                            "list",
                            "delete",
                            "clear",
                            "search",
                            "append",
                        ],
                        "description": "Action to perform",
                    },
                    "key": {"type": "string", "description": "Note key/identifier"},
                    "content": {"type": "string", "description": "Note content"},
                    "query": {"type": "string", "description": "Search query"},
                },
                "required": ["action"],
            },
        }
