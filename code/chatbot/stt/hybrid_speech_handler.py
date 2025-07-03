import datetime
import whisper
import numpy as np
import sounddevice as sd

class WhisperSpeechHandler:
    """Handles speech recognition using OpenAI Whisper locally."""
    
    def __init__(self, model_name="base", microphone_device_index=None, sample_rate=16000):
        """
        Initialize the Whisper speech handler.
        
        Args:
            model_name: Whisper model to use (tiny, base, small, medium, large)
            microphone_device_index: Microphone device index to use (None for default)
            sample_rate: Audio sample rate (Whisper default is 16000)
        """
        self.model_name = model_name
        self.microphone_device_index = microphone_device_index
        self.sample_rate = sample_rate
        print(f"[SYSTEM] Loading Whisper model '{model_name}'...")
        self.model = whisper.load_model(model_name)
        print("[SYSTEM] Whisper model loaded.")

    def listen_and_transcribe(self, current_question_for_context=None, conversation_log=None, short_term_memory=None, is_follow_up=False, duration=8):
        """
        Listens from the microphone and transcribes speech using Whisper.
        Returns the transcribed text, or None if nothing recognized.
        """
        print(f"[SYSTEM] Listening for up to {duration} seconds...")
        try:
            audio = sd.rec(int(duration * self.sample_rate), samplerate=self.sample_rate, channels=1, dtype='float32', device=self.microphone_device_index)
            sd.wait()
            audio = np.squeeze(audio)
            print("[SYSTEM] Audio captured, transcribing...")
            result = self.model.transcribe(audio, fp16=False, language='en')
            text = result.get('text', '').strip()
            if conversation_log is not None:
                conversation_log.append(f"[{datetime.datetime.now().isoformat()}] [SYSTEM] Whisper recognition: {text}")
            if text:
                print(f"[SYSTEM] Transcription: {text}")
                return text
            else:
                print("[SYSTEM_WARNING] Whisper did not recognize any speech.")
                return None
        except Exception as e:
            print(f"[SYSTEM_ERROR] Whisper encountered an error: {e}")
            if conversation_log is not None:
                conversation_log.append(f"[{datetime.datetime.now().isoformat()}] [SYSTEM] Whisper error: {e}")
            return None

    def set_preference(self, prefer_offline):
        """No-op for Whisper handler (always offline)."""
        pass

    def get_status(self):
        """Get the status of the Whisper engine."""
        status = {
            'whisper_available': self.model is not None,
            'prefer_offline': True
        }
        return status

    def cleanup(self):
        """No explicit cleanup needed for Whisper."""
        print("[SYSTEM] Whisper speech handler cleaned up.")

    def __del__(self):
        self.cleanup() 