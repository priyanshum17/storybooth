# Speech Recognition Module

This module provides multiple speech recognition engines.

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

### 3. WhisperSpeechHandler (Recommended)
- Uses OpenAI Whisper model locally
- No internet required
- High accuracy
- Requires `whisper`, `torch`, and `sounddevice` Python packages

## Installation

### Basic Dependencies
```bash
pip install speech_recognition pyaudio
```

### For Whisper Support (Recommended)
```bash
pip install whisper torch sounddevice
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

### Using Whisper Speech Recognition (Recommended)
```python
from stt import WhisperSpeechHandler

handler = WhisperSpeechHandler(model_name="base")  # or "small", "medium", "large"
result = handler.listen_and_transcribe("What's your name?", [], [], False)
print(f"You said: {result}")
```

### Using Google Speech Recognition Only
```python
from stt import SpeechHandler

handler = SpeechHandler()
result = handler.listen_and_transcribe("What's your name?", [], [], False)
print(f"You said: {result}")
```

### Using Vosk Offline Recognition Only
```python
from stt import VoskSpeechHandler

handler = VoskSpeechHandler(model_path="models/vosk-model-en-us-0.22")
result = handler.listen_and_transcribe("What's your name?", [], [], False)
print(f"You said: {result}")
```

## Features

- Microphone device selection
- Timeout handling
- Conversation logging
- Comprehensive error handling

## Model Recommendations

### For Best Quality (if you have space)
- **Whisper large** (best accuracy, slowest)
- **Whisper base/small/medium** (faster, less accurate)

### For Quick Testing/Development
- **Whisper tiny/base** (fastest, lowest accuracy)

## Troubleshooting

### Common Issues

1. **"No microphones found"**
   - Check microphone connection
   - Verify audio drivers
   - Test microphone in other applications

2. **"PyAudio or sounddevice installation failed"**
   - macOS: `brew install portaudio && pip install pyaudio`
   - Ubuntu: `sudo apt-get install portaudio19-dev && pip install pyaudio`
   - Windows: Download precompiled wheel

3. **"Torch not installed or GPU not available"**
   - Install torch: `pip install torch`
   - For GPU acceleration, ensure CUDA is installed and torch is built with CUDA support

### Performance Tips

- For offline use: Use WhisperSpeechHandler or VoskSpeechHandler
- For best accuracy: Use WhisperSpeechHandler with "large" model
- For privacy: Use WhisperSpeechHandler or VoskSpeechHandler only

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

1. **For Offline Use**: Use VoskSpeechHandler or set WhisperSpeechHandler to prefer_offline=True
2. **For Best Accuracy**: Use WhisperSpeechHandler with "large" model
3. **For Privacy**: Use VoskSpeechHandler or WhisperSpeechHandler only
4. **For Reliability**: Use WhisperSpeechHandler for automatic fallback 