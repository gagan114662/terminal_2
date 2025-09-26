"""
Tests for ConversationMemory (L1 Component Testing)
"""

import pytest

from termnet.memory import ConversationMemory


@pytest.fixture
def memory():
    """Create ConversationMemory instance for testing"""
    return ConversationMemory()


def test_basic_add_and_get(memory):
    """Test basic add and get_history functionality"""
    memory.add("user", "Hello")
    memory.add("assistant", "Hi there")

    history = memory.get_history()

    assert len(history) == 2
    assert history[0] == ("user", "Hello")
    assert history[1] == ("assistant", "Hi there")


def test_get_history_with_limit(memory):
    """Test get_history with limit parameter"""
    # Add multiple entries
    memory.add("user", "Message 1")
    memory.add("assistant", "Response 1")
    memory.add("user", "Message 2")
    memory.add("assistant", "Response 2")
    memory.add("user", "Message 3")

    # Test limit=2 returns last 2 entries
    limited_history = memory.get_history(limit=2)

    assert len(limited_history) == 2
    assert limited_history[0] == ("assistant", "Response 2")
    assert limited_history[1] == ("user", "Message 3")


def test_get_history_limit_larger_than_history(memory):
    """Test get_history when limit is larger than actual history"""
    memory.add("user", "Only message")

    history = memory.get_history(limit=10)

    assert len(history) == 1
    assert history[0] == ("user", "Only message")


def test_get_history_zero_limit(memory):
    """Test get_history with limit=0 returns empty list"""
    memory.add("user", "Message")

    history = memory.get_history(limit=0)

    assert len(history) == 0
    assert history == []


def test_get_history_negative_limit(memory):
    """Test get_history with negative limit returns empty list"""
    memory.add("user", "Message")

    history = memory.get_history(limit=-1)

    assert len(history) == 0
    assert history == []


def test_clear_functionality(memory):
    """Test clear() removes all history"""
    memory.add("user", "Message 1")
    memory.add("assistant", "Response 1")
    memory.add("user", "Message 2")

    assert len(memory.get_history()) == 3

    memory.clear()

    assert len(memory.get_history()) == 0
    assert memory.get_history() == []


def test_empty_memory_get_history(memory):
    """Test get_history on empty memory"""
    history = memory.get_history()

    assert len(history) == 0
    assert history == []


def test_empty_memory_with_limit(memory):
    """Test get_history with limit on empty memory"""
    history = memory.get_history(limit=5)

    assert len(history) == 0
    assert history == []


def test_add_empty_text(memory):
    """Test adding empty text"""
    memory.add("user", "")
    memory.add("assistant", "")

    history = memory.get_history()

    assert len(history) == 2
    assert history[0] == ("user", "")
    assert history[1] == ("assistant", "")


def test_add_multiline_text(memory):
    """Test adding multiline text"""
    multiline_text = "Line 1\nLine 2\nLine 3"
    memory.add("user", multiline_text)

    history = memory.get_history()

    assert len(history) == 1
    assert history[0] == ("user", multiline_text)
    assert "\n" in history[0][1]


def test_get_history_returns_copy(memory):
    """Test that get_history returns a copy, not reference to internal list"""
    memory.add("user", "Original message")

    history1 = memory.get_history()
    history2 = memory.get_history()

    # Modify one history list
    history1.append(("user", "Modified"))

    # Other history list should be unaffected
    assert len(history2) == 1
    assert history2[0] == ("user", "Original message")

    # Original memory should also be unaffected
    original_history = memory.get_history()
    assert len(original_history) == 1
    assert original_history[0] == ("user", "Original message")


def test_conversation_sequence(memory):
    """Test a realistic conversation sequence"""
    # Simulate a conversation
    memory.add("user", "What is 2+2?")
    memory.add("assistant", "2+2 equals 4.")
    memory.add("user", "What about 3+3?")
    memory.add("assistant", "3+3 equals 6.")
    memory.add("user", "Thank you!")
    memory.add("assistant", "You're welcome!")

    # Check full history
    full_history = memory.get_history()
    assert len(full_history) == 6

    # Check recent history (last 3 messages)
    recent_history = memory.get_history(limit=3)
    assert len(recent_history) == 3
    assert recent_history[0] == ("assistant", "3+3 equals 6.")
    assert recent_history[1] == ("user", "Thank you!")
    assert recent_history[2] == ("assistant", "You're welcome!")


def test_memory_persistence_disabled(memory):
    """Test that memory is in-memory only (no file I/O for tests)"""
    memory.add("user", "Test message")

    # ConversationMemory should not create any files
    # It should be purely in-memory for test compatibility
    import os

    # Check current directory doesn't have unexpected database files
    current_files = os.listdir(".")
    db_files = [
        f for f in current_files if f.endswith(".db") and "conversation" in f.lower()
    ]

    # Should not create conversation-related database files
    assert len(db_files) == 0 or all("conversation" not in f.lower() for f in db_files)


def test_role_types(memory):
    """Test different role types"""
    memory.add("user", "User message")
    memory.add("assistant", "Assistant response")
    memory.add("system", "System message")
    memory.add("tool", "Tool output")

    history = memory.get_history()

    assert len(history) == 4
    assert history[0] == ("user", "User message")
    assert history[1] == ("assistant", "Assistant response")
    assert history[2] == ("system", "System message")
    assert history[3] == ("tool", "Tool output")


def test_special_characters(memory):
    """Test handling of special characters in messages"""
    special_message = 'Message with special chars: éñ中文🚀\n\t"quotes"'
    memory.add("user", special_message)

    history = memory.get_history()

    assert len(history) == 1
    assert history[0] == ("user", special_message)
