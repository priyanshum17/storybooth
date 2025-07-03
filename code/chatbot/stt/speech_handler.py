# import speech_recognition as sr
import datetime


def test_google_speech_availability(microphone_device_index=None):
    """Test if Google Speech Recognition is available (online)."""
    try:
        print("[SYSTEM] Testing Google Speech Recognition availability...")
        
        # First check if microphone is available
        try:
            mic_list = sr.Microphone.list_microphone_names()
            if not mic_list:
                print("[SYSTEM] No microphones found")
                return False
            
            # Test microphone access
            selected_mic_index = microphone_device_index
            if selected_mic_index is not None and (selected_mic_index < 0 or selected_mic_index >= len(mic_list)):
                selected_mic_index = None  # Use default
            
            microphone = sr.Microphone(device_index=selected_mic_index)
        except Exception as e:
            print(f"[SYSTEM] Microphone not available: {e}")
            return False
        
        # Test Google API connectivity with a very short audio sample
        recognizer = sr.Recognizer()
        
        print("[SYSTEM] Testing Google API connectivity...")
        
        # Create a minimal audio sample for testing (silence)
        import io
        import wave
        import audioop
        
        # Create a very short silence audio sample (0.1 seconds, 16kHz, mono)
        sample_rate = 16000
        duration = 0.1  # Very short test
        frames = int(sample_rate * duration)
        silence_data = b'\x00' * (frames * 2)  # 16-bit samples
        
        # Create AudioData object
        test_audio = sr.AudioData(silence_data, sample_rate, 2)
        
        # Try to send this to Google API with a very short timeout
        try:
            # This will fail if there's no internet or Google API is unreachable
            recognizer.recognize_google(test_audio)
        except sr.UnknownValueError:
            # This is expected for silence - means API is reachable
            print("[SYSTEM] Google Speech Recognition API is reachable")
            return True
        except sr.RequestError as e:
            # This means API is not reachable (no internet, DNS issues, etc.)
            print(f"[SYSTEM] Google Speech API not reachable: {e}")
            return False
        except Exception as e:
            print(f"[SYSTEM] Unexpected error testing Google API: {e}")
            return False
        
        # If we get here, API responded (shouldn't happen with silence, but just in case)
        print("[SYSTEM] Google Speech Recognition API is reachable")
        return True
        
    except Exception as e:
        print(f"[SYSTEM] Google Speech Recognition test failed: {e}")
        return False


def initialize_speech_handler(microphone_device_index=None, vosk_model_path=None):
    """
    Initialize speech handler, trying Google first, then Vosk if Google is not available.
    
    Args:
        microphone_device_index: Microphone device index to use
        vosk_model_path: Path to Vosk model (if None, will try to find default)
    
    Returns:
        tuple: (speech_handler, engine_type) where engine_type is "google" or "vosk"
    """
    from .vosk_speech_handler import VoskSpeechHandler
    
    # First try Google Speech Recognition
    if test_google_speech_availability(microphone_device_index):
        try:
            print("[SYSTEM] Initializing Google Speech Recognition...")
            speech_handler = SpeechHandler(microphone_device_index=microphone_device_index)
            
            if speech_handler.microphone:
                print("[SYSTEM] ✓ Google Speech Recognition initialized successfully")
                return speech_handler, "google"
            else:
                raise Exception("Microphone initialization failed")
                
        except Exception as e:
            print(f"[SYSTEM] Google Speech Recognition initialization failed: {e}")
    
    # Fall back to Vosk if Google is not available
    print("[SYSTEM] Falling back to Vosk offline speech recognition...")
    
    try:
        speech_handler = VoskSpeechHandler(
            model_path=vosk_model_path,
            microphone_device_index=microphone_device_index
        )
        
        if speech_handler.model:
            print("[SYSTEM] ✓ Vosk Speech Recognition initialized successfully")
            return speech_handler, "vosk"
        else:
            raise Exception("Vosk model initialization failed")
            
    except Exception as e:
        print(f"[SYSTEM] Vosk Speech Recognition initialization failed: {e}")
        return None, None


class SpeechHandler:
    """Handles speech recognition and transcription functionality."""
    
    def __init__(self, microphone_device_index=None):
        """Initialize the speech handler with microphone configuration."""
        self.recognizer = sr.Recognizer()
        self.microphone_device_index = microphone_device_index
        self.microphone = None
        self._setup_microphone()
    
    def _setup_microphone(self):
        """Set up the microphone for speech recognition."""
        try:
            mic_list = sr.Microphone.list_microphone_names()
            if not mic_list:
                error_msg = "[SYSTEM_ERROR] No microphones found! Please ensure a microphone is connected."
                print(error_msg)
                return False
            
            selected_mic_index = self.microphone_device_index
            mic_name_for_log = ""
            
            if selected_mic_index is None:
                mic_name_for_log = f"default microphone (index 0: {mic_list[0] if mic_list else 'N/A'})"
                print(f"\n[SYSTEM] Using {mic_name_for_log}.")
            else:
                if 0 <= selected_mic_index < len(mic_list):
                    mic_name_for_log = f"specified microphone index: {selected_mic_index} ({mic_list[selected_mic_index]})"
                    print(f"\n[SYSTEM] Using {mic_name_for_log}.")
                else:
                    mic_name_for_log = f"default microphone (index 0: {mic_list[0] if mic_list else 'N/A'}) as specified index {selected_mic_index} is invalid."
                    print(f"\n[SYSTEM_WARNING] Invalid microphone index {selected_mic_index}. Available: 0-{len(mic_list)-1}. Using {mic_name_for_log}.")
                    selected_mic_index = None  # Fallback to default
            
            self.microphone = sr.Microphone(device_index=selected_mic_index)
            return True
            
        except Exception as e:
            import traceback
            error_msg = f"Error initializing microphone: {e}"
            print(f"[SYSTEM_ERROR] {error_msg}")
            return False
    
    def listen_and_transcribe(self, current_question_for_context, conversation_log, short_term_memory, is_follow_up=False):
        """Listens, transcribes, handles commands. Adds user answer to short-term memory."""
        if not self.microphone:
            print("[SYSTEM_ERROR] Microphone not available")
            return None
            
        with self.microphone as source:
            print("\n[SYSTEM] Adjusting for ambient noise (for your answer)...")
            try:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.7)
                skip_repeat_hint = "" if is_follow_up else "You can also say 'repeat question' or 'skip question'."
                print(f"[SYSTEM_PROMPT] Listening for your answer to: \"{current_question_for_context[:70]}...\" {skip_repeat_hint}")
                conversation_log.append(f"[{datetime.datetime.now().isoformat()}] [SYSTEM_PROMPT] Listening for your answer to: \"{current_question_for_context[:70]}...\" {skip_repeat_hint}")

                audio_data = self.recognizer.listen(source, timeout=7, phrase_time_limit=20)
                print("[SYSTEM] Processing your answer...")
                conversation_log.append(f"[{datetime.datetime.now().isoformat()}] [SYSTEM] Processing answer...")
                text = self.recognizer.recognize_google(audio_data).lower()

                print(f"You said: \"{text}\"")
                conversation_log.append(f"[{datetime.datetime.now().isoformat()}] [USER] {text}")
                self._add_to_short_term_memory(short_term_memory, role="user", type="answer", content=text)

                if not is_follow_up:
                    if "repeat question" in text or "repeat that" in text:
                        if short_term_memory and short_term_memory[-1]["content"] == text: 
                            short_term_memory.pop()
                        return "__REPEAT__"
                    if "skip question" in text or "skip that" in text or "next question" in text:
                        if short_term_memory and short_term_memory[-1]["content"] == text: 
                            short_term_memory.pop()
                        return "__SKIP__"
                return text
                
            except sr.WaitTimeoutError:
                conversation_log.append(f"[{datetime.datetime.now().isoformat()}] [SYSTEM] Speech recognition timeout.")
            except sr.UnknownValueError:
                conversation_log.append(f"[{datetime.datetime.now().isoformat()}] [SYSTEM] Speech recognition could not understand audio.")
            except sr.RequestError as e:
                print(f"Speech Recognition RequestError details: {e}")
                conversation_log.append(f"[{datetime.datetime.now().isoformat()}] [SYSTEM] Speech Recognition RequestError: {e}")
            except OSError as e:
                print(f"Microphone error: {e}")
                conversation_log.append(f"[{datetime.datetime.now().isoformat()}] [SYSTEM] Microphone error: {e}")
            except Exception as e:
                print(f"An unexpected error occurred during speech recognition: {e}")
                conversation_log.append(f"[{datetime.datetime.now().isoformat()}] [SYSTEM] Unexpected SR error: {e}")
            return None
    
    def _add_to_short_term_memory(self, short_term_memory, role, type, content):
        """Adds an entry to short-term memory and manages its size."""
        MAX_SHORT_TERM_MEMORY_TURNS = 4  # This could be passed as a parameter if needed
        if content:
            short_term_memory.append({"role": role, "type": type, "content": content})
            if len(short_term_memory) > MAX_SHORT_TERM_MEMORY_TURNS * 3:
                short_term_memory[:] = short_term_memory[-(MAX_SHORT_TERM_MEMORY_TURNS * 3):] 