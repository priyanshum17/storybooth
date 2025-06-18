import pytest
import requests
import datetime
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the parent directory to the path so we can import prompts
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from prompts.base_prompts import (
    format_memory_for_prompt,
    make_ollama_request,
    log_conversation,
    OLLAMA_API_URL,
    OLLAMA_MODEL
)


class TestFormatMemoryForPrompt:
    """Test cases for the format_memory_for_prompt function."""

    def test_empty_memory_list(self):
        """Test formatting when memory list is empty."""
        result = format_memory_for_prompt([])
        assert result == "This is the beginning of our conversation."

    def test_none_memory_list(self):
        """Test formatting when memory list is None."""
        result = format_memory_for_prompt(None)
        assert result == "This is the beginning of our conversation."

    def test_single_assistant_question(self):
        """Test formatting with a single assistant question."""
        memory = [
            {"role": "assistant", "type": "question", "content": "What's your favorite color?"}
        ]
        result = format_memory_for_prompt(memory)
        expected = "Here's a summary of our recent conversation:\nI (the AI Story Guide) asked you: \"What's your favorite color?\""
        assert result == expected

    def test_single_assistant_comment(self):
        """Test formatting with a single assistant comment."""
        memory = [
            {"role": "assistant", "type": "comment", "content": "That's wonderful!"}
        ]
        result = format_memory_for_prompt(memory)
        expected = "Here's a summary of our recent conversation:\nI (the AI Story Guide) then said: \"That's wonderful!\""
        assert result == expected

    def test_single_user_answer(self):
        """Test formatting with a single user answer."""
        memory = [
            {"role": "user", "type": "answer", "content": "Blue is my favorite."}
        ]
        result = format_memory_for_prompt(memory)
        expected = "Here's a summary of our recent conversation:\nYou (the User) responded: \"Blue is my favorite.\""
        assert result == expected

    def test_complete_conversation_flow(self):
        """Test formatting with a complete conversation flow."""
        memory = [
            {"role": "assistant", "type": "question", "content": "What's your favorite color?"},
            {"role": "user", "type": "answer", "content": "I love blue."},
            {"role": "assistant", "type": "comment", "content": "Blue is such a calming color!"},
            {"role": "assistant", "type": "question", "content": "What made you drawn to blue?"},
            {"role": "user", "type": "answer", "content": "The ocean and sky inspire me."}
        ]
        result = format_memory_for_prompt(memory)
        
        expected_lines = [
            "Here's a summary of our recent conversation:",
            "I (the AI Story Guide) asked you: \"What's your favorite color?\"",
            "You (the User) responded: \"I love blue.\"",
            "I (the AI Story Guide) then said: \"Blue is such a calming color!\"",
            "I (the AI Story Guide) asked you: \"What made you drawn to blue?\"",
            "You (the User) responded: \"The ocean and sky inspire me.\""
        ]
        expected = "\n".join(expected_lines)
        assert result == expected

    def test_unknown_role_or_type(self):
        """Test that unknown roles or types are handled gracefully."""
        memory = [
            {"role": "unknown", "type": "question", "content": "This shouldn't appear"},
            {"role": "assistant", "type": "unknown", "content": "This shouldn't appear either"},
            {"role": "assistant", "type": "question", "content": "This should appear"}
        ]
        result = format_memory_for_prompt(memory)
        expected = "Here's a summary of our recent conversation:\nI (the AI Story Guide) asked you: \"This should appear\""
        assert result == expected


class TestMakeOllamaRequest:
    """Test cases for the make_ollama_request function."""

    @patch('requests.post')
    def test_successful_request(self, mock_post):
        """Test a successful Ollama API request."""
        # Mock successful response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "response": "This is a test response from Ollama"
        }
        mock_post.return_value = mock_response

        result = make_ollama_request("Test prompt")
        
        assert result == "This is a test response from Ollama"
        mock_post.assert_called_once_with(
            OLLAMA_API_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": "Test prompt",
                "stream": False,
                "options": {"temperature": 0.8, "top_p": 0.9}
            },
            timeout=60
        )

    @patch('requests.post')
    def test_custom_parameters(self, mock_post):
        """Test request with custom temperature, top_p, and timeout."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"response": "Custom response"}
        mock_post.return_value = mock_response

        result = make_ollama_request(
            "Custom prompt", 
            temperature=0.5, 
            top_p=0.7, 
            timeout=120
        )
        
        assert result == "Custom response"
        mock_post.assert_called_once_with(
            OLLAMA_API_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": "Custom prompt",
                "stream": False,
                "options": {"temperature": 0.5, "top_p": 0.7}
            },
            timeout=120
        )

    @patch('requests.post')
    def test_empty_response(self, mock_post):
        """Test handling of empty response from Ollama."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"response": ""}
        mock_post.return_value = mock_response

        result = make_ollama_request("Test prompt")
        assert result is None

    @patch('requests.post')
    def test_no_response_field(self, mock_post):
        """Test handling when response field is missing."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"error": "No response field"}
        mock_post.return_value = mock_response

        result = make_ollama_request("Test prompt")
        assert result is None

    @patch('requests.post')
    def test_request_exception(self, mock_post):
        """Test handling of request exceptions."""
        mock_post.side_effect = requests.RequestException("Connection error")

        result = make_ollama_request("Test prompt")
        assert result is None

    @patch('requests.post')
    def test_http_error(self, mock_post):
        """Test handling of HTTP errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
        mock_post.return_value = mock_response

        result = make_ollama_request("Test prompt")
        assert result is None

    @patch('requests.post')
    def test_whitespace_response(self, mock_post):
        """Test that responses with only whitespace are treated as empty."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"response": "   \n\t   "}
        mock_post.return_value = mock_response

        result = make_ollama_request("Test prompt")
        assert result is None


class TestLogConversation:
    """Test cases for the log_conversation function."""

    @patch('datetime.datetime')
    def test_log_conversation(self, mock_datetime):
        """Test that log_conversation adds properly formatted entries."""
        # Mock datetime
        mock_now = Mock()
        mock_now.isoformat.return_value = "2024-01-01T12:00:00"
        mock_datetime.now.return_value = mock_now

        conversation_log = []
        log_conversation(conversation_log, "[TEST_PREFIX]", "Test message")

        assert len(conversation_log) == 1
        assert conversation_log[0] == "[2024-01-01T12:00:00] [TEST_PREFIX] Test message"

    @patch('datetime.datetime')
    def test_multiple_log_entries(self, mock_datetime):
        """Test multiple log entries are added correctly."""
        mock_now = Mock()
        mock_now.isoformat.return_value = "2024-01-01T12:00:00"
        mock_datetime.now.return_value = mock_now

        conversation_log = []
        log_conversation(conversation_log, "[SYSTEM]", "First message")
        log_conversation(conversation_log, "[USER]", "Second message")
        log_conversation(conversation_log, "[ASSISTANT]", "Third message")

        assert len(conversation_log) == 3
        assert conversation_log[0] == "[2024-01-01T12:00:00] [SYSTEM] First message"
        assert conversation_log[1] == "[2024-01-01T12:00:00] [USER] Second message"
        assert conversation_log[2] == "[2024-01-01T12:00:00] [ASSISTANT] Third message"


class TestConstants:
    """Test that constants are properly defined."""

    def test_ollama_api_url_defined(self):
        """Test that OLLAMA_API_URL is properly defined."""
        assert OLLAMA_API_URL == "http://localhost:11434/api/generate"

    def test_ollama_model_defined(self):
        """Test that OLLAMA_MODEL is properly defined."""
        assert OLLAMA_MODEL == "gemma3" 