# AI prompting Agent
The current setup are separating into 3 modules:
1. speech-to-text:
    1. Whispher (best performance, offline)
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
├── Dockerfile                # Docker configuration for deployment
├── bot.py                    # (Empty or placeholder for bot logic)
├── conversations_logs/       # Conversation history logs
├── resources/                # Audio and text resources
├── stt/                      # Speech-to-Text module
│   ├── __init__.py
│   ├── README.md
│   └── whisper_speech_handler.py
├── tts/                      # Text-to-Speech module
│   ├── fish_tts_manager.py
│   ├── simple_tts_manager.py
│   └── MeloTTS/              # MeloTTS submodule and related files
├── utils/                    # Utility functions
│   ├── __init__.py
│   └── ollama_utils.py
```

