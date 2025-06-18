import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the parent directory to the path so we can import prompts
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from prompts.followup_prompts import get_ollama_follow_up


class TestGetOllamaFollowUp:
    """Test cases for the get_ollama_follow_up function."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.main_theme = "A time you experienced a particularly strong emotion"
        self.user_answer = "I felt really nervous before my first job interview"
        self.sample_memory = [
            {"role": "assistant", "type": "question", "content": "Tell me about a strong emotion you experienced?"},
            {"role": "user", "type": "answer", "content": "I felt really nervous before my first job interview"}
        ]
        self.conversation_log = []
        self.memory_entries = []
        
        def mock_add_to_memory(role, type, content):
            self.memory_entries.append({"role": role, "type": type, "content": content})
        
        self.add_to_memory_func = mock_add_to_memory

    @patch('prompts.followup_prompts.make_ollama_request')
    def test_question_response(self, mock_ollama_request):
        """Test when Ollama returns a follow-up question."""
        mock_ollama_request.return_value = "QUESTION: What was going through your mind right before you walked in?"
        
        result = get_ollama_follow_up(
            self.main_theme,
            self.user_answer,
            self.sample_memory,
            self.conversation_log,
            self.add_to_memory_func
        )
        
        assert result["type"] == "question"
        assert result["content"] == "What was going through your mind right before you walked in?"
        assert len(self.memory_entries) == 1
        assert self.memory_entries[0]["role"] == "assistant"
        assert self.memory_entries[0]["type"] == "question"
        assert self.memory_entries[0]["content"] == "What was going through your mind right before you walked in?"

    @patch('prompts.followup_prompts.make_ollama_request')
    def test_comment_response(self, mock_ollama_request):
        """Test when Ollama returns a comment."""
        mock_ollama_request.return_value = "COMMENT: Job interviews can be really nerve-wracking experiences! That's completely understandable."
        
        result = get_ollama_follow_up(
            self.main_theme,
            self.user_answer,
            self.sample_memory,
            self.conversation_log,
            self.add_to_memory_func
        )
        
        assert result["type"] == "comment"
        assert result["content"] == "Job interviews can be really nerve-wracking experiences! That's completely understandable."
        assert len(self.memory_entries) == 1
        assert self.memory_entries[0]["role"] == "assistant"
        assert self.memory_entries[0]["type"] == "comment"

    @patch('prompts.followup_prompts.make_ollama_request')
    def test_question_without_question_mark(self, mock_ollama_request):
        """Test that questions without question marks get one added."""
        mock_ollama_request.return_value = "QUESTION: What happened next in that situation"
        
        result = get_ollama_follow_up(
            self.main_theme,
            self.user_answer,
            self.sample_memory,
            self.conversation_log,
            self.add_to_memory_func
        )
        
        assert result["type"] == "question"
        assert result["content"] == "What happened next in that situation?"
        assert self.memory_entries[0]["content"] == "What happened next in that situation?"

    @patch('prompts.followup_prompts.make_ollama_request')
    def test_response_without_prefix(self, mock_ollama_request):
        """Test when Ollama returns a response without QUESTION: or COMMENT: prefix."""
        mock_ollama_request.return_value = "That sounds like a challenging experience you went through."
        
        result = get_ollama_follow_up(
            self.main_theme,
            self.user_answer,
            self.sample_memory,
            self.conversation_log,
            self.add_to_memory_func
        )
        
        # Should default to comment type
        assert result["type"] == "comment"
        assert result["content"] == "That sounds like a challenging experience you went through."
        assert len(self.memory_entries) == 1
        assert self.memory_entries[0]["type"] == "comment"
        
        # Should log a warning
        warning_logs = [log for log in self.conversation_log if "[OLLAMA_WARNING]" in log]
        assert len(warning_logs) >= 1

    @patch('prompts.followup_prompts.make_ollama_request')
    def test_case_insensitive_prefixes(self, mock_ollama_request):
        """Test that prefixes work regardless of case."""
        mock_ollama_request.return_value = "question: How did that make you feel?"
        
        result = get_ollama_follow_up(
            self.main_theme,
            self.user_answer,
            self.sample_memory,
            self.conversation_log,
            self.add_to_memory_func
        )
        
        assert result["type"] == "question"
        assert result["content"] == "How did that make you feel?"

    @patch('prompts.followup_prompts.make_ollama_request')
    def test_case_insensitive_comment_prefix(self, mock_ollama_request):
        """Test that comment prefixes work regardless of case."""
        mock_ollama_request.return_value = "comment: That's a very relatable experience."
        
        result = get_ollama_follow_up(
            self.main_theme,
            self.user_answer,
            self.sample_memory,
            self.conversation_log,
            self.add_to_memory_func
        )
        
        assert result["type"] == "comment"
        assert result["content"] == "That's a very relatable experience."

    @patch('prompts.followup_prompts.make_ollama_request')
    def test_ollama_request_failure(self, mock_ollama_request):
        """Test handling when Ollama request fails."""
        mock_ollama_request.return_value = None
        
        result = get_ollama_follow_up(
            self.main_theme,
            self.user_answer,
            self.sample_memory,
            self.conversation_log,
            self.add_to_memory_func
        )
        
        # Should return fallback comment
        assert result["type"] == "comment"
        assert result["content"] == "That's interesting. Let's try exploring something else."
        assert len(self.memory_entries) == 0  # No memory should be added on failure
        assert any("[OLLAMA_ERROR]" in log for log in self.conversation_log)

    @patch('prompts.followup_prompts.make_ollama_request')
    def test_memory_context_processing(self, mock_ollama_request):
        """Test that memory context is properly processed (excluding last entry)."""
        complex_memory = [
            {"role": "assistant", "type": "question", "content": "First question?"},
            {"role": "user", "type": "answer", "content": "First answer"},
            {"role": "assistant", "type": "comment", "content": "Interesting!"},
            {"role": "user", "type": "answer", "content": "Current answer"}  # This should be excluded
        ]
        
        mock_ollama_request.return_value = "QUESTION: Tell me more about that?"
        
        result = get_ollama_follow_up(
            self.main_theme,
            self.user_answer,
            complex_memory,
            self.conversation_log,
            self.add_to_memory_func
        )
        
        # Verify that make_ollama_request was called
        mock_ollama_request.assert_called_once()
        call_args = mock_ollama_request.call_args[0]
        prompt = call_args[0]
        
        # The prompt should contain memory context excluding the last entry
        assert "First question?" in prompt
        assert "First answer" in prompt
        assert "Interesting!" in prompt
        assert "Current answer" not in prompt  # Last entry should be excluded

    @patch('prompts.followup_prompts.make_ollama_request')
    def test_prompt_contains_theme_and_answer(self, mock_ollama_request):
        """Test that the generated prompt contains the theme and user answer."""
        mock_ollama_request.return_value = "COMMENT: That's a powerful story."
        
        custom_theme = "A moment of personal growth"
        custom_answer = "I learned to be more confident"
        
        result = get_ollama_follow_up(
            custom_theme,
            custom_answer,
            self.sample_memory,
            self.conversation_log,
            self.add_to_memory_func
        )
        
        mock_ollama_request.assert_called_once()
        call_args = mock_ollama_request.call_args[0]
        prompt = call_args[0]
        
        # The prompt should contain both the theme and user answer
        assert custom_theme in prompt
        assert custom_answer in prompt

    @patch('prompts.followup_prompts.make_ollama_request')
    def test_logging_behavior(self, mock_ollama_request):
        """Test that proper logging occurs during follow-up generation."""
        mock_ollama_request.return_value = "QUESTION: What happened next?"
        
        result = get_ollama_follow_up(
            self.main_theme,
            self.user_answer,
            self.sample_memory,
            self.conversation_log,
            self.add_to_memory_func
        )
        
        # Check that system process logging occurred
        process_logs = [log for log in self.conversation_log if "[SYSTEM_PROCESS]" in log]
        assert len(process_logs) >= 1
        
        # Check that prompt logging occurred
        prompt_logs = [log for log in self.conversation_log if "[OLLAMA_PROMPT_FOR_FOLLOW_UP]" in log]
        assert len(prompt_logs) >= 1
        
        # Check that raw response logging occurred
        response_logs = [log for log in self.conversation_log if "[OLLAMA_RAW_FOLLOW_UP_RESPONSE]" in log]
        assert len(response_logs) >= 1

    @patch('prompts.followup_prompts.make_ollama_request')
    def test_empty_memory_context(self, mock_ollama_request):
        """Test follow-up generation with empty memory context."""
        mock_ollama_request.return_value = "COMMENT: Thank you for sharing that."
        
        result = get_ollama_follow_up(
            self.main_theme,
            self.user_answer,
            [],  # Empty memory
            self.conversation_log,
            self.add_to_memory_func
        )
        
        assert result["type"] == "comment"
        assert result["content"] == "Thank you for sharing that."

    @patch('prompts.followup_prompts.make_ollama_request')
    def test_whitespace_in_response_content(self, mock_ollama_request):
        """Test handling of whitespace in response content."""
        mock_ollama_request.return_value = "QUESTION:    What made you feel that way?    "
        
        result = get_ollama_follow_up(
            self.main_theme,
            self.user_answer,
            self.sample_memory,
            self.conversation_log,
            self.add_to_memory_func
        )
        
        assert result["type"] == "question"
        assert result["content"] == "What made you feel that way?"  # Whitespace should be stripped

    def test_function_signature_compatibility(self):
        """Test that the function signature matches expected interface."""
        with patch('prompts.followup_prompts.make_ollama_request') as mock_request:
            mock_request.return_value = "COMMENT: Test response"
            
            # Test that all required parameters can be passed
            result = get_ollama_follow_up(
                main_theme_question_context="test theme",
                user_answer="test answer",
                memory_context=[],
                conversation_log=[],
                add_to_memory_func=lambda role, type, content: None
            )
            
            assert result["type"] == "comment"
            assert result["content"] == "Test response"

    @patch('prompts.followup_prompts.make_ollama_request')
    def test_question_with_existing_question_mark(self, mock_ollama_request):
        """Test that questions already ending with question marks are not modified."""
        mock_ollama_request.return_value = "QUESTION: How did that experience change you?"
        
        result = get_ollama_follow_up(
            self.main_theme,
            self.user_answer,
            self.sample_memory,
            self.conversation_log,
            self.add_to_memory_func
        )
        
        assert result["content"] == "How did that experience change you?"  # Should remain unchanged 