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

# Pending user testings
This list collates a list of items that the current pipeline is imperfect about
1. Feature enhancements:
    1. Cloning Corian's voice:
        Studying on the cloning capability from OpenVoice, Openvoice clone voice with zero shot but the current progress of comparing the cloned voice does not seem to capture the nuances in a nice way. Example experiment result:
        
        [Example sample audio](./resources/example_reference_elon.mp3)
        
        [Original voice](./resources/original_nuances.wav)
        
        [Transferred voice](./resources/output_v2_nuances_en-newest.wav)
        
        *The notebook to generate the above 3 audios can be found at `./resource/test.ipynb`
2. Optimisation
    1. Update greeting message - currently the greeting message is fixed here: https://github.com/priyanshum17/storybooth/blob/39229ca2f4b5a1e558b148ad015bbcb0013ee1bd/code/chatbot/main.py#L117
    2. Currently the agent waits for **7 seconds** for the user to start speaking, after which it times out if no speech is detected. Once the user starts, it will listen for up to 20 seconds for the response. Should we want to make it longer/shorter? Or more ideally, is there alternative to make it interactive i.e. stop when users start interrupting in a natural way?
    See: https://github.com/priyanshum17/storybooth/blob/39229ca2f4b5a1e558b148ad015bbcb0013ee1bd/code/chatbot/stt/speech_handler.py#L176 
    3. Currently, the audio manager is mistakenly loaded from the `stt` (speech-to-text) module. To improve modularity, reorganize the code so that the audio manager is independent and can be used by both `stt` and `tts` modules as needed.  
    See: https://github.com/priyanshum17/storybooth/blob/39229ca2f4b5a1e558b148ad015bbcb0013ee1bd/code/chatbot/stt/audio_manager.py#L10-L12

