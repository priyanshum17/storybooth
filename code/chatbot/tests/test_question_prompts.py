import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the parent directory to the path so we can import prompts
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from prompts.question_prompts import get_ollama_to_formulate_question


class TestGetOllamaToFormulateQuestion:
    """Test cases for the get_ollama_to_formulate_question function."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.sample_theme = "A time you experienced a particularly strong emotion"
        self.sample_memory = [
            {"role": "assistant", "type": "comment", "content": "Welcome! Let's start our conversation."}
        ]
        self.conversation_log = []
        self.memory_entries = []
        
        def mock_add_to_memory(role, type, content):
            self.memory_entries.append({"role": role, "type": type, "content": content})
        
        self.add_to_memory_func = mock_add_to_memory

    @patch('prompts.question_prompts.make_ollama_request')
    def test_successful_question_formulation(self, mock_ollama_request):
        """Test successful question formulation."""
        mock_ollama_request.return_value = "What's a moment when you felt truly surprised by something unexpected?"
        
        result = get_ollama_to_formulate_question(
            self.sample_theme,
            self.sample_memory,
            self.conversation_log,
            self.add_to_memory_func
        )
        
        assert result == "What's a moment when you felt truly surprised by something unexpected?"
        assert len(self.memory_entries) == 1
        assert self.memory_entries[0]["role"] == "assistant"
        assert self.memory_entries[0]["type"] == "question"
        assert self.memory_entries[0]["content"] == "What's a moment when you felt truly surprised by something unexpected?"
        
        # Check that logging occurred
        assert len(self.conversation_log) >= 2  # At least system process log and raw response log

    @patch('prompts.question_prompts.make_ollama_request')
    def test_question_without_question_mark(self, mock_ollama_request):
        """Test that questions without question marks get one added."""
        mock_ollama_request.return_value = "Tell me about a time you felt joy"
        
        result = get_ollama_to_formulate_question(
            self.sample_theme,
            self.sample_memory,
            self.conversation_log,
            self.add_to_memory_func
        )
        
        assert result == "Tell me about a time you felt joy?"
        assert self.memory_entries[0]["content"] == "Tell me about a time you felt joy?"

    @patch('prompts.question_prompts.make_ollama_request')
    def test_question_with_period_becomes_question_mark(self, mock_ollama_request):
        """Test that questions ending with periods get converted to question marks."""
        mock_ollama_request.return_value = "What made you feel that way."
        
        result = get_ollama_to_formulate_question(
            self.sample_theme,
            self.sample_memory,
            self.conversation_log,
            self.add_to_memory_func
        )
        
        assert result == "What made you feel that way?"

    @patch('prompts.question_prompts.make_ollama_request')
    def test_question_with_comma_becomes_question_mark(self, mock_ollama_request):
        """Test that questions ending with commas get converted to question marks."""
        mock_ollama_request.return_value = "Can you share that story,"
        
        result = get_ollama_to_formulate_question(
            self.sample_theme,
            self.sample_memory,
            self.conversation_log,
            self.add_to_memory_func
        )
        
        assert result == "Can you share that story?"

    @patch('prompts.question_prompts.make_ollama_request')
    def test_ollama_request_failure(self, mock_ollama_request):
        """Test handling when Ollama request fails."""
        mock_ollama_request.return_value = None
        
        result = get_ollama_to_formulate_question(
            self.sample_theme,
            self.sample_memory,
            self.conversation_log,
            self.add_to_memory_func
        )
        
        assert result is None
        assert len(self.memory_entries) == 0  # No memory should be added on failure
        assert any("[OLLAMA_ERROR]" in log for log in self.conversation_log)

    @patch('prompts.question_prompts.make_ollama_request')
    def test_empty_memory_context(self, mock_ollama_request):
        """Test question formulation with empty memory context."""
        mock_ollama_request.return_value = "What's something that brought you joy recently?"
        
        result = get_ollama_to_formulate_question(
            self.sample_theme,
            [],  # Empty memory
            self.conversation_log,
            self.add_to_memory_func
        )
        
        assert result == "What's something that brought you joy recently?"
        assert len(self.memory_entries) == 1

    @patch('prompts.question_prompts.make_ollama_request')
    def test_complex_memory_context(self, mock_ollama_request):
        """Test question formulation with complex memory context."""
        complex_memory = [
            {"role": "assistant", "type": "question", "content": "Previous question?"},
            {"role": "user", "type": "answer", "content": "Previous answer"},
            {"role": "assistant", "type": "comment", "content": "That's interesting!"}
        ]
        mock_ollama_request.return_value = "Building on that, what's another experience you'd like to share?"
        
        result = get_ollama_to_formulate_question(
            self.sample_theme,
            complex_memory,
            self.conversation_log,
            self.add_to_memory_func
        )
        
        assert result == "Building on that, what's another experience you'd like to share?"
        
        # Verify that make_ollama_request was called with the right parameters
        mock_ollama_request.assert_called_once()
        call_args = mock_ollama_request.call_args[0]
        prompt = call_args[0]
        
        # The prompt should contain the formatted memory context
        assert "Previous question?" in prompt
        assert "Previous answer" in prompt
        assert "That's interesting!" in prompt

    @patch('prompts.question_prompts.make_ollama_request')
    def test_prompt_contains_theme(self, mock_ollama_request):
        """Test that the generated prompt contains the provided theme."""
        mock_ollama_request.return_value = "What's a challenge you've overcome?"
        
        custom_theme = "A unique challenge you faced and conquered"
        result = get_ollama_to_formulate_question(
            custom_theme,
            self.sample_memory,
            self.conversation_log,
            self.add_to_memory_func
        )
        
        mock_ollama_request.assert_called_once()
        call_args = mock_ollama_request.call_args[0]
        prompt = call_args[0]
        
        # The prompt should contain the theme
        assert custom_theme in prompt

    @patch('prompts.question_prompts.make_ollama_request')
    def test_logging_behavior(self, mock_ollama_request):
        """Test that proper logging occurs during question formulation."""
        mock_ollama_request.return_value = "What's your story?"
        
        result = get_ollama_to_formulate_question(
            self.sample_theme,
            self.sample_memory,
            self.conversation_log,
            self.add_to_memory_func
        )
        
        # Check that system process logging occurred
        process_logs = [log for log in self.conversation_log if "[SYSTEM_PROCESS]" in log]
        assert len(process_logs) >= 1
        
        # Check that prompt logging occurred
        prompt_logs = [log for log in self.conversation_log if "[OLLAMA_PROMPT_FOR_INITIAL_QUESTION]" in log]
        assert len(prompt_logs) >= 1
        
        # Check that raw response logging occurred
        response_logs = [log for log in self.conversation_log if "[OLLAMA_RAW_FORMULATED_QUESTION_RESPONSE]" in log]
        assert len(response_logs) >= 1

    @patch('prompts.question_prompts.make_ollama_request')
    def test_question_already_has_question_mark(self, mock_ollama_request):
        """Test that questions already ending with question marks are not modified."""
        mock_ollama_request.return_value = "What's your favorite memory?"
        
        result = get_ollama_to_formulate_question(
            self.sample_theme,
            self.sample_memory,
            self.conversation_log,
            self.add_to_memory_func
        )
        
        assert result == "What's your favorite memory?"  # Should remain unchanged

    def test_function_signature_compatibility(self):
        """Test that the function signature matches expected interface."""
        # This test ensures the function can be called with the expected parameters
        # without actually making an Ollama request
        
        with patch('prompts.question_prompts.make_ollama_request') as mock_request:
            mock_request.return_value = "Test question?"
            
            # Test that all required parameters can be passed
            result = get_ollama_to_formulate_question(
                question_theme="test theme",
                memory_context=[],
                conversation_log=[],
                add_to_memory_func=lambda role, type, content: None
            )
            
            assert result == "Test question?" 