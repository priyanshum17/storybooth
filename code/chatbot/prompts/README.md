# Prompts Module

This module contains all the prompt-related functionality for the AI Story Guide application, organized into focused submodules for better maintainability and clarity.

## Module Structure

```
prompts/
├── __init__.py           # Main exports for the prompts package
├── base_prompts.py       # Common utilities and API handling
├── question_prompts.py   # Initial question formulation
├── followup_prompts.py   # Follow-up questions and comments
├── transition_prompts.py # Transition phrases for no-reply scenarios
└── README.md            # This documentation
```

## Files Overview

### `base_prompts.py`
Contains shared utilities and configuration:
- `OLLAMA_API_URL` and `OLLAMA_MODEL` constants
- `format_memory_for_prompt()` - Formats conversation history
- `make_ollama_request()` - Generic Ollama API interaction
- `log_conversation()` - Helper for logging with timestamps

### `question_prompts.py`
Handles initial question formulation:
- `get_ollama_to_formulate_question()` - Creates engaging opening questions based on themes

### `followup_prompts.py`
Manages follow-up interactions:
- `get_ollama_follow_up()` - Generates follow-up questions or empathetic comments

### `transition_prompts.py`
Handles graceful transitions:
- `get_ollama_transition_on_no_reply()` - Creates gentle transitions when users don't respond

## Usage

Import the functions from the main package:

```python
from prompts import (
    get_ollama_to_formulate_question,
    get_ollama_follow_up,
    get_ollama_transition_on_no_reply
)
from prompts.base_prompts import OLLAMA_MODEL
```

## Function Signatures

### `get_ollama_to_formulate_question(question_theme, memory_context, conversation_log, add_to_memory_func)`
- `question_theme`: Theme string for the question
- `memory_context`: List of conversation history
- `conversation_log`: List to append logging entries
- `add_to_memory_func`: Function to add entries to short-term memory
- Returns: Formulated question string or None

### `get_ollama_follow_up(main_theme_question_context, user_answer, memory_context, conversation_log, add_to_memory_func)`
- `main_theme_question_context`: Context of the main theme
- `user_answer`: User's response to previous question
- `memory_context`: List of conversation history
- `conversation_log`: List to append logging entries
- `add_to_memory_func`: Function to add entries to short-term memory
- Returns: Dict with "type" ("question" or "comment") and "content"

### `get_ollama_transition_on_no_reply(current_question_asked, memory_context, conversation_log)`
- `current_question_asked`: The question that received no response
- `memory_context`: List of conversation history
- `conversation_log`: List to append logging entries
- Returns: Transition phrase string or None
