# Testing Suite for AI Story Guide Prompts

This directory contains comprehensive unit and integration tests for the modularized prompts system.

## 🏗️ Test Structure

```
tests/
├── __init__.py              # Makes tests a Python package
├── conftest.py              # Shared fixtures and configuration
├── test_base_prompts.py     # Tests for base utilities
├── test_question_prompts.py # Tests for initial question generation
├── test_followup_prompts.py # Tests for follow-up questions and comments
├── test_transition_prompts.py # Tests for no-reply transitions
├── test_integration.py      # Integration tests
└── README.md               # This documentation
```

## 🧪 Test Categories

### Unit Tests

**`test_base_prompts.py`**
- Tests `format_memory_for_prompt()` with various memory scenarios
- Tests `make_ollama_request()` with mocked API calls
- Tests `log_conversation()` functionality
- Tests constants and error handling

**`test_question_prompts.py`**
- Tests initial question formulation
- Tests question mark handling
- Tests theme integration
- Tests error scenarios

**`test_followup_prompts.py`**
- Tests follow-up question generation
- Tests comment generation
- Tests prefix handling (QUESTION:/COMMENT:)
- Tests memory context processing

**`test_transition_prompts.py`**
- Tests transition phrase generation
- Tests no-reply scenarios
- Tests question truncation in logs
- Tests various transition examples

### Integration Tests

**`test_integration.py`**
- Tests complete conversation flows
- Tests memory consistency across functions
- Tests error handling consistency
- Tests realistic conversation scenarios

## 🚀 Running Tests

### Prerequisites

Install test dependencies:
```bash
pip install -r requirements-test.txt
```

Or use the Makefile:
```bash
make install-test-deps
```

### Running All Tests

```bash
# Using pytest directly (from clean/ directory)
pytest tests/ -v

# Using Makefile (from clean/ directory)
make test
```

### Running Specific Test Categories

```bash
# Base prompts tests
make test-base

# Question prompts tests  
make test-question

# Follow-up prompts tests
make test-followup

# Transition prompts tests
make test-transition

# Integration tests
make test-integration
```

### Running with Coverage

```bash
# Generate coverage report (from clean/ directory)
make test-coverage

# This creates both terminal output and HTML report in htmlcov/
```

### Verbose Output

```bash
# See detailed test output (from clean/ directory)
make test-verbose
```

## 🔧 Test Features

### Mocking Strategy

- **Ollama API calls** are mocked to avoid external dependencies
- **DateTime** is mocked for consistent logging tests
- **Requests** library is mocked for network isolation

### Fixtures (conftest.py)

- `sample_memory_context`: Standard conversation history
- `empty_conversation_log`: Clean log for tests
- `mock_add_to_memory_func`: Mock function for memory management
- `sample_themes`: Predefined story themes
- `sample_user_answers`: Sample user responses

### Test Coverage Areas

✅ **Happy Path Testing**
- Successful API responses
- Proper memory handling
- Correct logging behavior

✅ **Edge Case Testing**
- Empty/None inputs
- Malformed responses
- Network errors

✅ **Error Handling**
- API failures
- Invalid responses
- Timeout scenarios

✅ **Integration Testing**
- Multi-function workflows
- Memory consistency
- Realistic conversation flows

## 📊 Example Test Run

```bash
# From the clean/ directory:
$ make test

Running all tests...
python3 -m pytest tests -v

========================= test session starts =========================
collected 64 items

tests/test_base_prompts.py::TestFormatMemoryForPrompt::test_empty_memory_list PASSED
tests/test_base_prompts.py::TestFormatMemoryForPrompt::test_complete_conversation_flow PASSED
tests/test_base_prompts.py::TestMakeOllamaRequest::test_successful_request PASSED
tests/test_question_prompts.py::TestGetOllamaToFormulateQuestion::test_successful_question_formulation PASSED
tests/test_followup_prompts.py::TestGetOllamaFollowUp::test_question_response PASSED
tests/test_transition_prompts.py::TestGetOllamaTransitionOnNoReply::test_successful_transition_generation PASSED
tests/test_integration.py::TestPromptsIntegration::test_complete_conversation_flow PASSED

========================= 64 passed in 2.34s =========================
```

## 🐛 Debugging Tests

### Running Individual Tests

```bash
# Run a specific test class
pytest tests/test_base_prompts.py::TestFormatMemoryForPrompt -v

# Run a specific test method
pytest tests/test_base_prompts.py::TestFormatMemoryForPrompt::test_empty_memory_list -v
```

### Debugging with Print Statements

```bash
# Run tests with output capture disabled
pytest tests/ -v -s
```

### Adding New Tests

1. **Follow naming convention**: `test_*.py` for files, `test_*` for methods
2. **Use descriptive names**: Test names should clearly indicate what's being tested
3. **Include docstrings**: Explain what each test verifies
4. **Use appropriate fixtures**: Leverage existing fixtures from `conftest.py`
5. **Mock external dependencies**: Keep tests isolated and fast

### Test Patterns

```python
@patch('prompts.module.make_ollama_request')
def test_function_behavior(self, mock_ollama_request):
    """Test description of what this verifies."""
    # Arrange
    mock_ollama_request.return_value = "Expected response"
    
    # Act
    result = function_under_test(parameters)
    
    # Assert
    assert result == expected_result
    mock_ollama_request.assert_called_once()
```

## 🔍 Quality Metrics

- **Test Coverage**: Aim for >90% code coverage
- **Test Speed**: All tests should complete in <5 seconds
- **Test Isolation**: Tests should not depend on each other
- **Mocking**: External dependencies should be mocked
- **Assertions**: Each test should have clear, specific assertions

## 🛠️ Maintenance

### Adding New Prompt Functions

When adding new functions to the prompts module:

1. Create corresponding test file: `test_new_module.py`
2. Add unit tests for all function paths
3. Add integration tests if the function interacts with others
4. Update this README with new test information
5. Add new Makefile targets if needed

### Updating Tests

When modifying existing prompt functions:

1. Update corresponding tests
2. Ensure all test scenarios still pass
3. Add new test cases for new functionality
4. Verify integration tests still work

This testing suite ensures the reliability and maintainability of the AI Story Guide prompts system! 🎯 