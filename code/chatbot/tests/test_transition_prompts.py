import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the parent directory to the path so we can import prompts
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from prompts.transition_prompts import get_ollama_transition_on_no_reply


class TestGetOllamaTransitionOnNoReply:
    """Test cases for the get_ollama_transition_on_no_reply function."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.current_question = "What's a moment when you felt truly surprised by something unexpected?"
        self.sample_memory = [
            {"role": "assistant", "type": "question", "content": self.current_question}
        ]
        self.conversation_log = []

    @patch('prompts.transition_prompts.make_ollama_request')
    def test_successful_transition_generation(self, mock_ollama_request):
        """Test successful transition phrase generation."""
        mock_ollama_request.return_value = "No worries at all! Sometimes the best stories take a moment to surface. How about we explore something else?"
        
        result = get_ollama_transition_on_no_reply(
            self.current_question,
            self.sample_memory,
            self.conversation_log
        )
        
        expected = "No worries at all! Sometimes the best stories take a moment to surface. How about we explore something else?"
        assert result == expected
        
        # Check that logging occurred
        assert len(self.conversation_log) >= 2  # At least system process log and raw response log

    @patch('prompts.transition_prompts.make_ollama_request')
    def test_long_question_truncation_in_log(self, mock_ollama_request):
        """Test that long questions are truncated in the log message."""
        long_question = "This is a very long question that should be truncated in the logging message because it exceeds fifty characters and goes on and on"
        mock_ollama_request.return_value = "That's quite all right! Let's try a different theme."
        
        result = get_ollama_transition_on_no_reply(
            long_question,
            self.sample_memory,
            self.conversation_log
        )
        
        # Check that the log contains the truncated question (first 50 chars)
        process_logs = [log for log in self.conversation_log if "[SYSTEM_PROCESS]" in log]
        assert len(process_logs) >= 1
        
        # The log should contain the first 50 characters followed by "..."
        truncated_part = long_question[:50]
        assert any(truncated_part in log for log in process_logs)

    @patch('prompts.transition_prompts.make_ollama_request')
    def test_empty_memory_context(self, mock_ollama_request):
        """Test transition generation with empty memory context."""
        mock_ollama_request.return_value = "All good! We can always come back to that. Let's see what other adventures we can talk about!"
        
        result = get_ollama_transition_on_no_reply(
            self.current_question,
            [],  # Empty memory
            self.conversation_log
        )
        
        expected = "All good! We can always come back to that. Let's see what other adventures we can talk about!"
        assert result == expected

    @patch('prompts.transition_prompts.make_ollama_request')
    def test_complex_memory_context(self, mock_ollama_request):
        """Test transition generation with complex memory context."""
        complex_memory = [
            {"role": "assistant", "type": "question", "content": "Previous question?"},
            {"role": "user", "type": "answer", "content": "Previous answer"},
            {"role": "assistant", "type": "comment", "content": "That's interesting!"},
            {"role": "assistant", "type": "question", "content": self.current_question}
        ]
        
        mock_ollama_request.return_value = "That's perfectly fine! Sometimes a different angle helps. Let's try something new."
        
        result = get_ollama_transition_on_no_reply(
            self.current_question,
            complex_memory,
            self.conversation_log
        )
        
        assert result == "That's perfectly fine! Sometimes a different angle helps. Let's try something new."
        
        # Verify that make_ollama_request was called with the right parameters
        mock_ollama_request.assert_called_once()
        call_args = mock_ollama_request.call_args[0]
        prompt = call_args[0]
        
        # The prompt should contain the formatted memory context
        assert "Previous question?" in prompt
        assert "Previous answer" in prompt
        assert "That's interesting!" in prompt
        assert self.current_question in prompt

    @patch('prompts.transition_prompts.make_ollama_request')
    def test_prompt_contains_question(self, mock_ollama_request):
        """Test that the generated prompt contains the current question."""
        mock_ollama_request.return_value = "No problem! Let's explore a different story."
        
        custom_question = "Tell me about a time you overcame a challenge?"
        result = get_ollama_transition_on_no_reply(
            custom_question,
            self.sample_memory,
            self.conversation_log
        )
        
        mock_ollama_request.assert_called_once()
        call_args = mock_ollama_request.call_args[0]
        prompt = call_args[0]
        
        # The prompt should contain the current question
        assert custom_question in prompt

    @patch('prompts.transition_prompts.make_ollama_request')
    def test_ollama_request_failure(self, mock_ollama_request):
        """Test handling when Ollama request fails."""
        mock_ollama_request.return_value = None
        
        result = get_ollama_transition_on_no_reply(
            self.current_question,
            self.sample_memory,
            self.conversation_log
        )
        
        assert result is None
        assert any("[OLLAMA_ERROR]" in log for log in self.conversation_log)

    @patch('prompts.transition_prompts.make_ollama_request')
    def test_request_parameters(self, mock_ollama_request):
        """Test that the request is made with correct parameters."""
        mock_ollama_request.return_value = "That's okay! Let's try something else."
        
        result = get_ollama_transition_on_no_reply(
            self.current_question,
            self.sample_memory,
            self.conversation_log
        )
        
        # Verify that make_ollama_request was called with correct parameters
        mock_ollama_request.assert_called_once()
        call_args = mock_ollama_request.call_args
        
        # First argument is the prompt
        assert len(call_args[0]) == 1  # One positional argument (the prompt)
        
        # Check keyword arguments for temperature and timeout
        kwargs = call_args[1]
        assert kwargs.get('temperature') == 0.7
        assert kwargs.get('timeout') == 60

    @patch('prompts.transition_prompts.make_ollama_request')
    def test_logging_behavior(self, mock_ollama_request):
        """Test that proper logging occurs during transition generation."""
        mock_ollama_request.return_value = "No worries! Let's move on to something else."
        
        result = get_ollama_transition_on_no_reply(
            self.current_question,
            self.sample_memory,
            self.conversation_log
        )
        
        # Check that system process logging occurred
        process_logs = [log for log in self.conversation_log if "[SYSTEM_PROCESS]" in log]
        assert len(process_logs) >= 1
        
        # Check that prompt logging occurred
        prompt_logs = [log for log in self.conversation_log if "[OLLAMA_PROMPT_FOR_NO_REPLY_TRANSITION]" in log]
        assert len(prompt_logs) >= 1
        
        # Check that raw response logging occurred
        response_logs = [log for log in self.conversation_log if "[OLLAMA_RAW_TRANSITION_PHRASE]" in log]
        assert len(response_logs) >= 1

    @patch('prompts.transition_prompts.make_ollama_request')
    def test_whitespace_handling(self, mock_ollama_request):
        """Test that whitespace in responses is handled correctly."""
        mock_ollama_request.return_value = "   That's perfectly fine! Let's try something new.   "
        
        result = get_ollama_transition_on_no_reply(
            self.current_question,
            self.sample_memory,
            self.conversation_log
        )
        
        # Result should have whitespace stripped
        assert result == "That's perfectly fine! Let's try something new."

    @patch('prompts.transition_prompts.make_ollama_request')
    def test_empty_response(self, mock_ollama_request):
        """Test handling of empty response from Ollama."""
        mock_ollama_request.return_value = ""
        
        result = get_ollama_transition_on_no_reply(
            self.current_question,
            self.sample_memory,
            self.conversation_log
        )
        
        assert result is None
        assert any("[OLLAMA_ERROR]" in log for log in self.conversation_log)

    @patch('prompts.transition_prompts.make_ollama_request')
    def test_prompt_structure(self, mock_ollama_request):
        """Test that the prompt has the expected structure and content."""
        mock_ollama_request.return_value = "Test transition phrase"
        
        result = get_ollama_transition_on_no_reply(
            self.current_question,
            self.sample_memory,
            self.conversation_log
        )
        
        mock_ollama_request.assert_called_once()
        call_args = mock_ollama_request.call_args[0]
        prompt = call_args[0]
        
        # Check that prompt contains expected elements
        assert "friendly, patient, and understanding AI Story Guide" in prompt
        assert "didn't reply or wasn't sure what to say" in prompt
        assert "that's perfectly okay" in prompt
        assert "Do NOT ask a question" in prompt
        assert "Examples:" in prompt

    def test_function_signature_compatibility(self):
        """Test that the function signature matches expected interface."""
        with patch('prompts.transition_prompts.make_ollama_request') as mock_request:
            mock_request.return_value = "Test transition"
            
            # Test that all required parameters can be passed
            result = get_ollama_transition_on_no_reply(
                current_question_asked="test question",
                memory_context=[],
                conversation_log=[]
            )
            
            assert result == "Test transition"

    @patch('prompts.transition_prompts.make_ollama_request')
    def test_various_transition_examples(self, mock_ollama_request):
        """Test various types of transition phrases."""
        transition_phrases = [
            "No worries at all! Sometimes the best stories take a moment to surface.",
            "That's quite all right! Perhaps a different theme will spark an idea?",
            "All good! We can always come back to that.",
            "Perfectly fine! Let's explore something else together."
        ]
        
        for phrase in transition_phrases:
            # Reset the conversation log for each test
            self.conversation_log.clear()
            
            mock_ollama_request.return_value = phrase
            
            result = get_ollama_transition_on_no_reply(
                self.current_question,
                self.sample_memory,
                self.conversation_log
            )
            
            assert result == phrase 