# Speech Recognition Module

This module provides multiple speech recognition engines with automatic fallback capabilities.

## Available Handlers

### 1. SpeechHandler (Google-based)
- Uses Google Web Speech API
- Requires internet connection
- High accuracy
- Uses `speech_recognition` library

### 2. VoskSpeechHandler (Offline)
- Uses Vosk offline speech recognition
- No internet required
- Good accuracy with proper models
- Completely private (no data sent to cloud)

### 3. HybridSpeechHandler (Best of Both)
- Automatically switches between Google and Vosk
- Configurable primary preference (online vs offline)
- Automatic fallback if primary fails

## Installation

### Basic Dependencies
```bash
pip install speech_recognition pyaudio
```

### For Vosk Support
```bash
pip install -r requirements-vosk.txt
```

### Download Vosk Model
1. Visit https://alphacephei.com/vosk/models
2. Download a model (recommended: `vosk-model-en-us-0.22` or `vosk-model-small-en-us-0.15`)
3. Extract to your project directory

## Usage Examples

### Using Google Speech Recognition Only
```python
from clean.stt import SpeechHandler

handler = SpeechHandler()
result = handler.listen_and_transcribe("What's your name?", [], [], False)
print(f"You said: {result}")
```

### Using Vosk Offline Recognition Only
```python
from clean.stt import VoskSpeechHandler

handler = VoskSpeechHandler(model_path="models/vosk-model-en-us-0.22")
result = handler.listen_and_transcribe("What's your name?", [], [], False)
print(f"You said: {result}")
```

### Using Hybrid Handler (Recommended)
```python
from clean.stt import HybridSpeechHandler

# Default: Google first, Vosk as backup
handler = HybridSpeechHandler(vosk_model_path="models/vosk-model-en-us-0.22")

# Or prefer offline first
handler = HybridSpeechHandler(
    vosk_model_path="models/vosk-model-en-us-0.22",
    prefer_offline=True
)

result = handler.listen_and_transcribe("What's your name?", [], [], False)
print(f"You said: {result}")

# Check status
status = handler.get_status()
print(f"Google available: {status['google_available']}")
print(f"Vosk available: {status['vosk_available']}")

# Change preference at runtime
handler.set_preference(prefer_offline=True)
```

### Integration with Existing Code
Replace your existing SpeechHandler with HybridSpeechHandler for automatic fallback:

```python
# Before
from clean.stt import SpeechHandler
speech_handler = SpeechHandler()

# After
from clean.stt import HybridSpeechHandler
speech_handler = HybridSpeechHandler(vosk_model_path="models/vosk-model-en-us-0.22")
```

## Model Recommendations

### For Best Quality (if you have space)
- **vosk-model-en-us-0.22** (~1.8GB)
- Best accuracy for English
- Good for production use

### For Quick Testing/Development
- **vosk-model-small-en-us-0.15** (~40MB)
- Faster loading and processing
- Lower memory usage
- Acceptable accuracy for testing

### For Other Languages
Visit https://alphacephei.com/vosk/models for models in other languages.

## Features

### All Handlers Support
- Microphone device selection
- Timeout handling
- Command detection ("repeat question", "skip question")
- Short-term memory management
- Comprehensive error handling
- Conversation logging

### Special Commands
- "repeat question" or "repeat that" → Returns `__REPEAT__`
- "skip question" or "next question" → Returns `__SKIP__`

### Error Handling
- Network connectivity issues (Google)
- Microphone access problems
- Model loading failures (Vosk)
- Audio processing errors

## Troubleshooting

### Common Issues

1. **"No microphones found"**
   - Check microphone connection
   - Verify audio drivers
   - Test microphone in other applications

2. **"Vosk model not found"**
   - Download and extract a Vosk model
   - Verify the model path is correct
   - Check file permissions

3. **"PyAudio installation failed"**
   - macOS: `brew install portaudio && pip install pyaudio`
   - Ubuntu: `sudo apt-get install portaudio19-dev && pip install pyaudio`
   - Windows: Download precompiled wheel

4. **"Google Speech API errors"**
   - Check internet connection
   - Verify microphone permissions
   - Try Vosk as alternative

### Performance Tips

1. **For Offline Use**: Use VoskSpeechHandler or set HybridSpeechHandler to prefer_offline=True
2. **For Best Accuracy**: Use HybridSpeechHandler with Google as primary
3. **For Privacy**: Use VoskSpeechHandler only
4. **For Reliability**: Use HybridSpeechHandler for automatic fallback 