import os
import re
import logging
import tempfile
import time
try:
    from fish_audio_sdk import Session, TTSRequest, ReferenceAudio
    FISH_SDK_AVAILABLE = True
except ImportError:
    FISH_SDK_AVAILABLE = False
    print('[WARNING] fish_audio_sdk not available. Fish TTS will not work.')

REFERENCE_AUDIO_PATH = 'resources/corian recording short.mp3'  # Path to Corian's reference audio
REFERENCE_TEXT = "Sample reference transcript for Corian's voice."
API_KEY = os.getenv('FISH_AUDIO_API_KEY', 'FISH_API_KEY_HERE')  # Replace with your key or use env var

class FishAudioManager:
    """Audio manager for Fish API voice cloning."""
    def __init__(self):
        if not FISH_SDK_AVAILABLE:
            print('[FISH TTS] fish_audio_sdk not available. Install it to use Fish TTS.')
        self.api_key = API_KEY
        self.reference_audio_path = REFERENCE_AUDIO_PATH
        self.reference_text = REFERENCE_TEXT

    def speak(self, text, conversation_log=None):
        if not FISH_SDK_AVAILABLE:
            print(f"[FISH TTS] {text}")
            return
        if not self.api_key or self.api_key == 'FISH_API_KEY_HERE':
            print('[FISH TTS] API key not set. Set FISH_AUDIO_API_KEY env variable.')
            return
        # Clean and truncate text for API
        text = self._clean_text(text)
        output_path = self._get_temp_output_path()
        try:
            session = Session(self.api_key)
            with open(self.reference_audio_path, "rb") as audio_file:
                with open(output_path, "wb") as f:
                    for chunk in session.tts(TTSRequest(
                        text=text,
                        backend='s1',
                        references=[
                            ReferenceAudio(
                                audio=audio_file.read(),
                                text=self.reference_text,
                            )
                        ]
                    )):
                        f.write(chunk)
            self._play_audio(output_path)
            if conversation_log is not None:
                import datetime
                conversation_log.append(f"[{datetime.datetime.now().isoformat()}] [FISH_TTS] Spoke: {text[:50]}...")
        except Exception as e:
            print(f"[FISH TTS ERROR] {e}")
            print(f"[FISH TTS FALLBACK] {text}")

    def _clean_text(self, text):
        # Remove special words and limit length
        text = re.sub(r'__\\w+__\\s*|_\\w+_\\s*', '', text)
        return text[:450]

    def _get_temp_output_path(self):
        # Use a temp file for output
        fd, path = tempfile.mkstemp(suffix='.mp3', prefix='fish_tts_')
        os.close(fd)
        return path

    def _play_audio(self, audio_path):
        try:
            import platform
            system = platform.system()
            if system == "Darwin":
                os.system(f'afplay "{audio_path}"')
            elif system == "Linux":
                os.system(f'aplay "{audio_path}" 2>/dev/null || paplay "{audio_path}" 2>/dev/null')
            elif system == "Windows":
                os.system(f'start /min wmplayer "{audio_path}"')
            else:
                print(f"[FISH TTS] Could not play audio on {system}")
            time.sleep(0.2)
        except Exception as e:
            print(f"[FISH TTS] Could not play audio: {e}")

    def cleanup(self):
        print("[FISH TTS] Cleanup complete.") 