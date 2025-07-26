# Speech Recognition Module

This module provides multiple speech recognition engines.

## Available Handlers

### 1. WhisperSpeechHandler (Recommended)
- Uses OpenAI Whisper model locally
- No internet required
- High accuracy
- Requires `whisper`, `torch`, and `sounddevice` Python packages

## Installation

### For Whisper Support (Recommended)
```bash
pip install whisper torch sounddevice
```

## Usage Examples

### Using Whisper Speech Recognition (Recommended)
```python
from stt import WhisperSpeechHandler

handler = WhisperSpeechHandler(model_name="base")  # or "small", "medium", "large"
result = handler.listen_and_transcribe("What's your name?", [], [], False)
print(f"You said: {result}")
```

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

- For best accuracy: Use WhisperSpeechHandler with "large" model
