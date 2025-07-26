import datetime
import os
import platform

class SimpleAudioManager:
    """Simple audio manager that provides text-to-speech functionality without complex dependencies."""
    
    def __init__(self):
        """Initialize the simple audio manager."""
        self.system_tts_available = self._check_system_tts()
        print(f"[SYSTEM] Initializing Simple TTS Manager...")
        if self.system_tts_available:
            print(f"[SYSTEM] System TTS available on {platform.system()}")
        else:
            print(f"[SYSTEM] System TTS not available, will use text-only mode")
    
    def _check_system_tts(self):
        """Check if system TTS is available."""
        try:
            if platform.system() == "Darwin":  # macOS
                return True
            elif platform.system() == "Windows":
                return True
            elif platform.system() == "Linux":
                # Check if espeak is available
                return os.system("which espeak > /dev/null 2>&1") == 0
            return False
        except:
            return False
    
    def speak(self, text_to_speak, conversation_log):
        """Speaks text using system TTS, with console fallback."""
        clean_text = self._clean_text_for_tts(text_to_speak)
        
        if self.system_tts_available:
            try:
                if platform.system() == "Darwin":  # macOS
                    os.system(f'say "{clean_text}"')
                elif platform.system() == "Windows":
                    os.system(f'echo "{clean_text}" | espeak')
                elif platform.system() == "Linux":
                    os.system(f'espeak "{clean_text}"')
            except Exception as e:
                print(f"[TTS FALLBACK] System TTS failed: {e}")
                print(f"[TTS FALLBACK] {text_to_speak}")
        else:
            print(f"[TTS FALLBACK] {text_to_speak}")
    
    def _clean_text_for_tts(self, text):
        """Clean text for TTS by removing problematic characters."""
        # Remove special characters that might cause issues with system TTS
        text = text.replace('"', "'")
        text = text.replace('`', "'")
        text = text.replace('\\', "")
        # Remove system message prefixes for speaking
        prefixes_to_remove = [
            "[SYSTEM]", "[ASSISTANT_COMMENT]", "[ASSISTANT_QUESTION]", 
            "[OLLAMA_COMMENT]", "[OLLAMA_FORMULATED_QUESTION]"
        ]
        for prefix in prefixes_to_remove:
            if text.startswith(prefix):
                text = text.replace(prefix, "").strip()
        return text
    
    def speak_and_log(self, message, conversation_log, is_question_from_ollama=False, is_ollama_response=False, is_system_message=False):
        """Helper to speak message (if appropriate), log it, and print to console."""
        log_entry_message = message
        speak_message_content = message
        
        # Determine log prefix and whether to speak
        log_prefix_for_entry = "[UNDEFINED]"
        should_speak_this_message = False
        
        if is_question_from_ollama:
            log_prefix_for_entry = "[ASSISTANT_QUESTION]"
            should_speak_this_message = True
        elif is_ollama_response:
            log_prefix_for_entry = "[ASSISTANT_COMMENT]"
            should_speak_this_message = True
        elif is_system_message:
            # Determine system message type
            if message.startswith("[SYSTEM_PROMPT]"): 
                log_prefix_for_entry = "[SYSTEM_PROMPT]"
            elif message.startswith("[SYSTEM_PROCESS]"): 
                log_prefix_for_entry = "[SYSTEM_PROCESS]"
            elif message.startswith("[SYSTEM_FALLBACK]"): 
                log_prefix_for_entry = "[SYSTEM_FALLBACK]"
            elif message.startswith("[SYSTEM_ERROR]"): 
                log_prefix_for_entry = "[SYSTEM_ERROR]"
            elif message.startswith("[SYSTEM_FEEDBACK]"): 
                log_prefix_for_entry = "[SYSTEM_FEEDBACK]"
            elif message.startswith("[SYSTEM]"): 
                log_prefix_for_entry = "[SYSTEM]"
            else: 
                log_prefix_for_entry = "[SYSTEM]"
            # System messages are generally not spoken
            should_speak_this_message = False
        else:
            log_prefix_for_entry = "[UNHANDLED_MESSAGE_TYPE]"
            should_speak_this_message = True
        
        # Print to console
        console_message = speak_message_content
        if console_message.startswith("[") and "]" in console_message.split(" ", 1)[0]:
            if not console_message.startswith(log_prefix_for_entry):
                print(f"{log_prefix_for_entry} {console_message}")
            else:
                print(console_message)
        else:
            print(f"{log_prefix_for_entry} {console_message}")
        
        # Speak the message if appropriate
        if should_speak_this_message:
            self.speak(speak_message_content, conversation_log)
        
        # Log the message
        if log_entry_message.startswith("[") and "]" in log_entry_message.split(" ", 1)[0] and log_entry_message.split(" ",1)[0] == log_prefix_for_entry:
            conversation_log.append(f"[{datetime.datetime.now().isoformat()}] {log_entry_message}")
        else:
            conversation_log.append(f"[{datetime.datetime.now().isoformat()}] {log_prefix_for_entry} {log_entry_message.replace(log_prefix_for_entry, '').strip()}")
    
    def cleanup(self):
        """Cleanup method for compatibility."""
        print("[SYSTEM] Simple TTS cleanup completed.") 