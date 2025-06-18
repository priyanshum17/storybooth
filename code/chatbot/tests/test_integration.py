import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the parent directory to the path so we can import prompts
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from prompts import (
    get_ollama_to_formulate_question,
    get_ollama_follow_up,
    get_ollama_transition_on_no_reply
)
from prompts.base_prompts import OLLAMA_MODEL, OLLAMA_API_URL


class TestPromptsIntegration:
    """Integration tests for the prompts module components working together."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.conversation_log = []
        self.memory_entries = []
        
        def mock_add_to_memory(role, type, content):
            self.memory_entries.append({"role": role, "type": type, "content": content})
        
        self.add_to_memory_func = mock_add_to_memory

    @patch('prompts.base_prompts.make_ollama_request')
    def test_complete_conversation_flow(self, mock_ollama_request):
        """Test a complete conversation flow using all prompt functions."""
        # Simulate the sequence of calls in a real conversation
        
        # 1. Formulate initial question
        mock_ollama_request.return_value = "What's a moment that made you feel truly alive?"
        
        initial_question = get_ollama_to_formulate_question(
            "A time you experienced a particularly strong emotion",
            [],  # Empty initial memory
            self.conversation_log,
            self.add_to_memory_func
        )
        
        assert initial_question == "What's a moment that made you feel truly alive?"
        assert len(self.memory_entries) == 1
        assert self.memory_entries[0]["type"] == "question"
        
        # 2. Simulate user response and get follow-up
        user_response = "I felt amazing when I climbed my first mountain"
        self.memory_entries.append({"role": "user", "type": "answer", "content": user_response})
        
        mock_ollama_request.return_value = "QUESTION: What was going through your mind when you reached the summit?"
        
        follow_up = get_ollama_follow_up(
            "A time you experienced a particularly strong emotion",
            user_response,
            list(self.memory_entries),
            self.conversation_log,
            self.add_to_memory_func
        )
        
        assert follow_up["type"] == "question"
        assert follow_up["content"] == "What was going through your mind when you reached the summit?"
        assert len(self.memory_entries) == 3  # initial question + user answer + follow-up question
        
        # 3. Simulate no response and get transition
        mock_ollama_request.return_value = "No worries! Sometimes experiences are hard to put into words. Let's explore something else."
        
        transition = get_ollama_transition_on_no_reply(
            follow_up["content"],
            list(self.memory_entries),
            self.conversation_log
        )
        
        assert transition == "No worries! Sometimes experiences are hard to put into words. Let's explore something else."

    @patch('prompts.base_prompts.make_ollama_request')
    def test_memory_context_consistency(self, mock_ollama_request):
        """Test that memory context is consistently formatted across all functions."""
        # Set up initial memory
        initial_memory = [
            {"role": "assistant", "type": "comment", "content": "Hello! Let's chat."},
            {"role": "assistant", "type": "question", "content": "Previous question?"},
            {"role": "user", "type": "answer", "content": "Previous answer"}
        ]
        
        mock_ollama_request.return_value = "What's another story you'd like to share?"
        
        # Test question formulation
        result = get_ollama_to_formulate_question(
            "Test theme",
            initial_memory,
            self.conversation_log,
            self.add_to_memory_func
        )
        
        # Verify the prompt was generated with memory context
        mock_ollama_request.assert_called()
        call_args = mock_ollama_request.call_args[0]
        prompt = call_args[0]
        
        # All memory entries should be in the prompt
        assert "Hello! Let's chat." in prompt
        assert "Previous question?" in prompt
        assert "Previous answer" in prompt

    @patch('prompts.base_prompts.make_ollama_request')
    def test_error_handling_consistency(self, mock_ollama_request):
        """Test that all functions handle Ollama errors consistently."""
        mock_ollama_request.return_value = None  # Simulate Ollama failure
        
        # Test question formulation error handling
        question_result = get_ollama_to_formulate_question(
            "Test theme",
            [],
            self.conversation_log,
            self.add_to_memory_func
        )
        assert question_result is None
        
        # Test follow-up error handling
        follow_up_result = get_ollama_follow_up(
            "Test theme",
            "Test answer",
            [],
            self.conversation_log,
            self.add_to_memory_func
        )
        assert follow_up_result["type"] == "comment"
        assert "interesting" in follow_up_result["content"].lower()
        
        # Test transition error handling
        transition_result = get_ollama_transition_on_no_reply(
            "Test question?",
            [],
            self.conversation_log
        )
        assert transition_result is None
        
        # All should have logged errors
        error_logs = [log for log in self.conversation_log if "[OLLAMA_ERROR]" in log]
        assert len(error_logs) >= 2  # At least from question and transition functions

    def test_function_imports(self):
        """Test that all functions can be imported from the main prompts module."""
        # This test ensures the __init__.py exports are working correctly
        assert callable(get_ollama_to_formulate_question)
        assert callable(get_ollama_follow_up)
        assert callable(get_ollama_transition_on_no_reply)

    def test_constants_accessibility(self):
        """Test that constants are accessible and have expected values."""
        assert OLLAMA_MODEL == "gemma3"
        assert OLLAMA_API_URL == "http://localhost:11434/api/generate"

    @patch('prompts.base_prompts.make_ollama_request')
    def test_logging_consistency(self, mock_ollama_request):
        """Test that logging behavior is consistent across all functions."""
        mock_ollama_request.return_value = "Test response"
        
        # Clear log before test
        self.conversation_log.clear()
        
        # Call question formulation
        get_ollama_to_formulate_question(
            "Test theme",
            [],
            self.conversation_log,
            self.add_to_memory_func
        )
        
        question_logs = len(self.conversation_log)
        assert question_logs > 0
        
        # Call follow-up (should add more logs)
        mock_ollama_request.return_value = "COMMENT: Test comment"
        get_ollama_follow_up(
            "Test theme",
            "Test answer",
            [],
            self.conversation_log,
            self.add_to_memory_func
        )
        
        follow_up_logs = len(self.conversation_log)
        assert follow_up_logs > question_logs
        
        # Call transition (should add more logs)
        mock_ollama_request.return_value = "Test transition"
        get_ollama_transition_on_no_reply(
            "Test question?",
            [],
            self.conversation_log
        )
        
        transition_logs = len(self.conversation_log)
        assert transition_logs > follow_up_logs

    @patch('prompts.base_prompts.make_ollama_request')
    def test_realistic_conversation_scenario(self, mock_ollama_request):
        """Test a realistic conversation scenario with multiple turns."""
        # Mock responses for different stages
        responses = [
            "What's a challenge that taught you something important about yourself?",  # Initial question
            "QUESTION: What was the biggest lesson you learned from that experience?",  # Follow-up
            "COMMENT: That's a powerful insight! Growth often comes through challenges.",  # Comment
            "No worries at all! Sometimes reflecting takes time. Let's explore something else."  # Transition
        ]
        
        mock_ollama_request.side_effect = responses
        
        # 1. Get initial question
        question = get_ollama_to_formulate_question(
            "A challenge you faced and overcame",
            [],
            self.conversation_log,
            self.add_to_memory_func
        )
        
        # Add user response
        self.memory_entries.append({
            "role": "user", 
            "type": "answer", 
            "content": "I had to learn to ask for help when I was struggling in college"
        })
        
        # 2. Get follow-up question
        follow_up = get_ollama_follow_up(
            "A challenge you faced and overcame",
            "I had to learn to ask for help when I was struggling in college",
            list(self.memory_entries),
            self.conversation_log,
            self.add_to_memory_func
        )
        
        # Add another user response
        self.memory_entries.append({
            "role": "user", 
            "type": "answer", 
            "content": "I learned that vulnerability isn't weakness"
        })
        
        # 3. Get empathetic comment
        comment = get_ollama_follow_up(
            "A challenge you faced and overcame",
            "I learned that vulnerability isn't weakness",
            list(self.memory_entries),
            self.conversation_log,
            self.add_to_memory_func
        )
        
        # 4. Get transition for no response
        transition = get_ollama_transition_on_no_reply(
            "Tell me more about that realization?",
            list(self.memory_entries),
            self.conversation_log
        )
        
        # Verify the conversation flow
        assert question == responses[0]
        assert follow_up["type"] == "question"
        assert follow_up["content"] == "What was the biggest lesson you learned from that experience?"
        assert comment["type"] == "comment"
        assert comment["content"] == "That's a powerful insight! Growth often comes through challenges."
        assert transition == responses[3]
        
        # Verify memory was managed correctly
        assert len(self.memory_entries) >= 4  # question + user answer + follow-up + user answer + comment

    def test_module_structure(self):
        """Test that the module structure is properly set up."""
        # Test that we can import from different submodules
        from prompts.base_prompts import format_memory_for_prompt, make_ollama_request
        from prompts.question_prompts import get_ollama_to_formulate_question as question_func
        from prompts.followup_prompts import get_ollama_follow_up as followup_func
        from prompts.transition_prompts import get_ollama_transition_on_no_reply as transition_func
        
        # Verify they're callable
        assert callable(format_memory_for_prompt)
        assert callable(make_ollama_request)
        assert callable(question_func)
        assert callable(followup_func)
        assert callable(transition_func) 