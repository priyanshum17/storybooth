# StoryBooth - Corian the Dancer Agent

A compassionate AI companion who uses intelligent prompts to handle different user intents like answering questions or listening to stories.

## 📚 Documentation & Resources

### 📊 Slide Presentation
- [Project Presentation Slides](https://docs.google.com/presentation/d/1SxZjJx1N_6fK0sHNbuoauzoheEp4yl7d6XLb4w3-XGk/edit?usp=drive_link)
  - System architecture overview
  - Technical implementation details
  - Challenges and design choices
  - Future directions

### 🎥 Demo Video
- [Demo Video](https://drive.google.com/file/d/1fbZ7Dnw6v8pus9snCE2EXohsXhZ4CvX1/view?usp=sharing
)
  - Live demonstration of StoryBooth
  - Conversation flow examples
  - Voice interaction showcase

## 🏗️ System Architecture
StoryBooth consists of several modular components:
1. speech-to-text:
    1. [Whispher (best performance, offline)](https://github.com/openai/whisper)
2. text-to-speech:
    1. [Openvoice](https://github.com/myshell-ai/OpenVoice/tree/main)
3. Lightweight LLM models with ollama

## 🎭 Corian's Personality

Corian is designed as a warm, empathetic conversational agent with two modes:
- **Professional:** Thoughtful and caring
- **Artistic:** Creative and expressive

## 🔧 Technical Features

- **Multi-backend TTS:** Support for different voice synthesis approaches
- **Context Memory:** Rolling conversation history
- **Phase-based Dialogue:** Structured conversation flow
- **Real-time Logging:** Streaming conversation logs
- **Modular Design:** Easy component swapping and extension

## 🚀 Setup & Quick Start

### Prerequisites
- Python 3.11
- Ollama (for LLM inference)
- Microphone and speakers

### Installation
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

### Running the Application
```bash
python main.py
```

## 📁 Project Structure
```
chatbot/
├── README.md
├── main.py                   # Main application entry point
├── requirements.txt          # Main dependencies
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

## 🤝 Contributing

This project was developed for CS 7470 - Mobile & Ubiquitous Computing at Georgia Tech.
