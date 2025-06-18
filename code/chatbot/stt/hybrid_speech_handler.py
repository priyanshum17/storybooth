import datetime
from .speech_handler import SpeechHandler
from .vosk_speech_handler import VoskSpeechHandler


class HybridSpeechHandler:
    """Handles speech recognition with automatic fallback from Google to Vosk."""
    
    def __init__(self, microphone_device_index=None, vosk_model_path=None, prefer_offline=False):
        """
        Initialize the hybrid speech handler.
        
        Args:
            microphone_device_index: Microphone device index to use
            vosk_model_path: Path to Vosk model (if None, will try to find default)
            prefer_offline: If True, try Vosk first, then Google. If False, try Google first.
        """
        self.microphone_device_index = microphone_device_index
        self.vosk_model_path = vosk_model_path
        self.prefer_offline = prefer_offline
        
        # Initialize both handlers
        self.google_handler = None
        self.vosk_handler = None
        
        self._initialize_handlers()
    
    def _initialize_handlers(self):
        """Initialize both Google and Vosk speech handlers."""
        print("[SYSTEM] Initializing hybrid speech recognition system...")
        
        # Initialize Google handler
        try:
            self.google_handler = SpeechHandler(microphone_device_index=self.microphone_device_index)
            print("[SYSTEM] Google Speech Recognition initialized successfully.")
        except Exception as e:
            print(f"[SYSTEM_WARNING] Failed to initialize Google Speech Recognition: {e}")
            self.google_handler = None
        
        # Initialize Vosk handler
        try:
            self.vosk_handler = VoskSpeechHandler(
                model_path=self.vosk_model_path,
                microphone_device_index=self.microphone_device_index
            )
            if self.vosk_handler.model:
                print("[SYSTEM] Vosk Speech Recognition initialized successfully.")
            else:
                print("[SYSTEM_WARNING] Vosk Speech Recognition failed to initialize.")
                self.vosk_handler = None
        except Exception as e:
            print(f"[SYSTEM_WARNING] Failed to initialize Vosk Speech Recognition: {e}")
            self.vosk_handler = None
        
        # Check if at least one handler is available
        if not self.google_handler and not self.vosk_handler:
            print("[SYSTEM_ERROR] No speech recognition engines available!")
        elif self.google_handler and self.vosk_handler:
            primary = "Vosk (offline)" if self.prefer_offline else "Google (online)"
            backup = "Google (online)" if self.prefer_offline else "Vosk (offline)"
            print(f"[SYSTEM] Both speech engines available. Primary: {primary}, Backup: {backup}")
        elif self.google_handler:
            print("[SYSTEM] Only Google Speech Recognition available.")
        elif self.vosk_handler:
            print("[SYSTEM] Only Vosk Speech Recognition available.")
    
    def listen_and_transcribe(self, current_question_for_context, conversation_log, short_term_memory, is_follow_up=False):
        """
        Listens and transcribes speech using available engines with automatic fallback.
        
        Returns the transcribed text, special commands (__REPEAT__, __SKIP__), or None.
        """
        if not self.google_handler and not self.vosk_handler:
            print("[SYSTEM_ERROR] No speech recognition engines available")
            return None
        
        # Determine the order of engines to try
        if self.prefer_offline:
            primary_handler = self.vosk_handler
            backup_handler = self.google_handler
            primary_name = "Vosk (offline)"
            backup_name = "Google (online)"
        else:
            primary_handler = self.google_handler
            backup_handler = self.vosk_handler
            primary_name = "Google (online)"
            backup_name = "Vosk (offline)"
        
        # Try primary handler first
        if primary_handler:
            try:
                print(f"[SYSTEM] Attempting speech recognition with {primary_name}...")
                result = primary_handler.listen_and_transcribe(
                    current_question_for_context, 
                    conversation_log, 
                    short_term_memory, 
                    is_follow_up
                )
                
                if result is not None:
                    conversation_log.append(f"[{datetime.datetime.now().isoformat()}] [SYSTEM] Recognition successful using {primary_name}")
                    return result
                else:
                    print(f"[SYSTEM_WARNING] {primary_name} failed to recognize speech")
                    
            except Exception as e:
                print(f"[SYSTEM_WARNING] {primary_name} encountered an error: {e}")
                conversation_log.append(f"[{datetime.datetime.now().isoformat()}] [SYSTEM] {primary_name} error: {e}")
        
        # Try backup handler if primary failed
        if backup_handler:
            try:
                print(f"[SYSTEM] Falling back to {backup_name}...")
                conversation_log.append(f"[{datetime.datetime.now().isoformat()}] [SYSTEM] Falling back to {backup_name}")
                
                result = backup_handler.listen_and_transcribe(
                    current_question_for_context, 
                    conversation_log, 
                    short_term_memory, 
                    is_follow_up
                )
                
                if result is not None:
                    conversation_log.append(f"[{datetime.datetime.now().isoformat()}] [SYSTEM] Recognition successful using {backup_name} (backup)")
                    return result
                else:
                    print(f"[SYSTEM_WARNING] {backup_name} also failed to recognize speech")
                    
            except Exception as e:
                print(f"[SYSTEM_ERROR] {backup_name} backup also failed: {e}")
                conversation_log.append(f"[{datetime.datetime.now().isoformat()}] [SYSTEM] {backup_name} backup error: {e}")
        
        # Both handlers failed
        print("[SYSTEM_ERROR] All speech recognition engines failed")
        conversation_log.append(f"[{datetime.datetime.now().isoformat()}] [SYSTEM] All speech recognition engines failed")
        return None
    
    def set_preference(self, prefer_offline):
        """Change the preference for offline vs online recognition."""
        self.prefer_offline = prefer_offline
        primary = "Vosk (offline)" if prefer_offline else "Google (online)"
        backup = "Google (online)" if prefer_offline else "Vosk (offline)"
        print(f"[SYSTEM] Speech recognition preference updated. Primary: {primary}, Backup: {backup}")
    
    def get_status(self):
        """Get the status of both speech recognition engines."""
        status = {
            'google_available': self.google_handler is not None and self.google_handler.microphone is not None,
            'vosk_available': self.vosk_handler is not None and self.vosk_handler.model is not None,
            'prefer_offline': self.prefer_offline
        }
        return status
    
    def cleanup(self):
        """Clean up resources for both handlers."""
        if self.vosk_handler:
            self.vosk_handler.cleanup()
        # Google handler (SpeechHandler) doesn't need explicit cleanup
        print("[SYSTEM] Hybrid speech handler cleaned up.")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup() 