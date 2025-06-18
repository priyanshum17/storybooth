import pytest
import sys
import os

# Add the parent directory to the path so tests can import prompts
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture
def sample_memory_context():
    """Provide a standard memory context for tests."""
    return [
        {"role": "assistant", "type": "comment", "content": "Welcome! Let's start our conversation."},
        {"role": "assistant", "type": "question", "content": "What's your favorite memory?"},
        {"role": "user", "type": "answer", "content": "I love summer vacations with my family."},
        {"role": "assistant", "type": "comment", "content": "That sounds wonderful!"}
    ]


@pytest.fixture
def empty_conversation_log():
    """Provide an empty conversation log for tests."""
    return []


@pytest.fixture
def mock_add_to_memory_func():
    """Provide a mock function for adding to memory."""
    memory_entries = []
    
    def add_to_memory(role, type, content):
        memory_entries.append({"role": role, "type": type, "content": content})
    
    add_to_memory.entries = memory_entries
    return add_to_memory


@pytest.fixture
def sample_themes():
    """Provide sample story themes for testing."""
    return [
        "A time you experienced a particularly strong emotion",
        "A significant learning experience or piece of wisdom you gained",
        "A challenge you faced and how you navigated through it"
    ]


@pytest.fixture
def sample_user_answers():
    """Provide sample user answers for testing."""
    return [
        "I felt really nervous before my first job interview",
        "I learned that persistence pays off when I trained for a marathon",
        "I had to overcome my fear of public speaking for a presentation"
    ] 