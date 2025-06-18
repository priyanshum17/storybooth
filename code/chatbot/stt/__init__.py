# Speech and Audio Processing Module
# This module handles both Speech-to-Text (STT) and Text-to-Speech (TTS) functionality

from .speech_handler import SpeechHandler, test_google_speech_availability, initialize_speech_handler
from .vosk_speech_handler import VoskSpeechHandler
from .hybrid_speech_handler import HybridSpeechHandler
from .audio_manager import AudioManager

__all__ = ['SpeechHandler', 'VoskSpeechHandler', 'HybridSpeechHandler', 'AudioManager', 
           'test_google_speech_availability', 'initialize_speech_handler'] 