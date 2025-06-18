# AI prompting Agent
The current setup are separating into 3 modules:
1. speech-to-text:
    Hybrid way of using 
    1. google speech recognition (online usage)
    2. Vosk (offline usage)
2. text-to-speech:
    1. [Openvoice](https://github.com/myshell-ai/OpenVoice/tree/main)
3. Lightweight LLM models with ollama

# Setup
Use Python 3.11
1. Download the openvoice model following readme in `openvoice_models_downloaded/`
2. Install Openvoice
    ```
    cd tts/
    git clone git@github.com:myshell-ai/OpenVoice.git
    cd OpenVoice
    pip install -e .
    ```
3. Install ollama, following installation step here: https://ollama.com/
4. Run ollama with `ollama run gemma3`
5. Create environment and install requirements with `pip install -r requirements.txt`
6. `python main.py`

# File Structure
```
chatbot/
├── README.md
├── main.py                   # Main application entry point
├── requirements.txt          # Main dependencies
├── requirements-test.txt     # Test dependencies
├── TESTING.md               # Testing documentation
├── conversations_logs/       # Conversation history
│   └── placeholder.txt
├── prompts/                 # Prompt management
│   ├── __init__.py
│   ├── base_prompts.py
│   ├── followup_prompts.py
│   ├── question_prompts.py
│   └── README.md
├── stt/                     # Speech-to-Text module
│   ├── __init__.py
│   ├── audio_manager.py
│   ├── hybrid_speech_handler.py
│   ├── speech_handler.py
│   └── README.md
├── tts/                     # Text-to-Speech module
│   ├── __init__.py
│   ├── openvoice_instance.py
│   ├── OpenVoice/           # Submodule
│   └── openvoice_models_downloaded/
└── tests/                   # Testing suite
    ├── __init__.py
    ├── conftest.py
    ├── test_base_prompts.py
    ├── test_followup_prompts.py
    └── README.md
```

# 
