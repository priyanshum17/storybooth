import json
import datetime
import pyaudio
import vosk
import sys
import os


class VoskSpeechHandler:
    """Handles speech recognition using Vosk offline engine as backup."""
    
    def __init__(self, model_path=None, microphone_device_index=None):
        """Initialize the Vosk speech handler with model and microphone configuration."""
        self.model_path = model_path or self._find_default_model_path()
        self.microphone_device_index = microphone_device_index
        self.model = None
        self.recognizer = None
        self.audio = None
        self.stream = None
        self._setup_vosk()
        self._setup_microphone()
    
    def _find_default_model_path(self):
        """Try to find a default Vosk model path."""
        common_paths = [
            'models/vosk-model-en-us-0.42-gigaspeech',
            "models/vosk-model-en-us-0.22",
            "models/vosk-model-small-en-us-0.15",
            "../models/vosk-model-en-us-0.22",
            "vosk-model-en-us-0.22",
            "vosk-model-small-en-us-0.15"
        ]
        
        for path in common_paths:
            if os.path.isdir(path):
                return path
                
        print("[SYSTEM_WARNING] No default Vosk model found. Please specify model_path or download a model.")
        print("Download models from: https://alphacephei.com/vosk/models")
        return None
    
    def _setup_vosk(self):
        """Set up the Vosk model and recognizer."""
        try:
            if not self.model_path or not os.path.isdir(self.model_path):
                print(f"[SYSTEM_ERROR] Vosk model path not found: {self.model_path}")
                print("Please download a Vosk model from https://alphacephei.com/vosk/models")
                print("and specify the correct path.")
                return False
            
            print(f"[SYSTEM] Loading Vosk model from: {self.model_path}")
            self.model = vosk.Model(self.model_path)
            self.recognizer = vosk.KaldiRecognizer(self.model, 16000)
            print("[SYSTEM] Vosk model loaded successfully.")
            return True
            
        except Exception as e:
            print(f"[SYSTEM_ERROR] Error initializing Vosk: {e}")
            print("Make sure you have installed vosk: pip install vosk")
            return False
    
    def _setup_microphone(self):
        """Set up the microphone for speech recognition."""
        try:
            self.audio = pyaudio.PyAudio()
            
            # List available devices
            mic_count = self.audio.get_device_count()
            if mic_count == 0:
                print("[SYSTEM_ERROR] No audio devices found!")
                return False
            
            selected_device_index = self.microphone_device_index
            device_name = "default"
            
            if selected_device_index is None:
                # Use default input device
                selected_device_index = self.audio.get_default_input_device_info()['index']
                device_name = self.audio.get_default_input_device_info()['name']
                print(f"\n[SYSTEM] Using default microphone: {device_name} (index {selected_device_index})")
            else:
                if 0 <= selected_device_index < mic_count:
                    device_info = self.audio.get_device_info_by_index(selected_device_index)
                    device_name = device_info['name']
                    print(f"\n[SYSTEM] Using specified microphone: {device_name} (index {selected_device_index})")
                else:
                    print(f"\n[SYSTEM_WARNING] Invalid microphone index {selected_device_index}. Available: 0-{mic_count-1}")
                    selected_device_index = self.audio.get_default_input_device_info()['index']
                    device_name = self.audio.get_default_input_device_info()['name']
                    print(f"[SYSTEM] Falling back to default microphone: {device_name} (index {selected_device_index})")
            
            self.selected_device_index = selected_device_index
            return True
            
        except Exception as e:
            print(f"[SYSTEM_ERROR] Error initializing microphone: {e}")
            return False
    
    def listen_and_transcribe(self, current_question_for_context, conversation_log, short_term_memory, is_follow_up=False):
        """Listens, transcribes using Vosk, handles commands. Adds user answer to short-term memory."""
        if not self.model or not self.recognizer or not self.audio:
            print("[SYSTEM_ERROR] Vosk not properly initialized")
            return None
        
        try:
            # Open audio stream
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                input_device_index=self.selected_device_index,
                frames_per_buffer=8000
            )
            
            print("\n[SYSTEM] Adjusting for ambient noise (using Vosk offline)...")
            skip_repeat_hint = "" if is_follow_up else "You can also say 'repeat question' or 'skip question'."
            print(f"[SYSTEM_PROMPT] Listening for your answer to: \"{current_question_for_context[:70]}...\" {skip_repeat_hint}")
            conversation_log.append(f"[{datetime.datetime.now().isoformat()}] [SYSTEM_PROMPT] Listening for your answer to: \"{current_question_for_context[:70]}...\" {skip_repeat_hint}")
            
            print("[SYSTEM] Listening... (Vosk offline recognition)")
            
            # Listen for audio with timeout
            frames_collected = 0
            max_frames = 16000 * 20  # 20 seconds max
            silence_threshold = 1000  # Adjust based on testing
            consecutive_silence = 0
            max_silence = 16000 * 2  # 2 seconds of silence to stop
            
            while frames_collected < max_frames:
                try:
                    data = self.stream.read(4000, exception_on_overflow=False)
                    frames_collected += 4000
                    
                    if self.recognizer.AcceptWaveform(data):
                        # Got a complete result
                        result = json.loads(self.recognizer.Result())
                        text = result.get('text', '').strip()
                        
                        if text:
                            print("[SYSTEM] Processing your answer...")
                            conversation_log.append(f"[{datetime.datetime.now().isoformat()}] [SYSTEM] Processing answer...")
                            
                            text_lower = text.lower()
                            print(f"You said: \"{text}\"")
                            conversation_log.append(f"[{datetime.datetime.now().isoformat()}] [USER] {text}")
                            self._add_to_short_term_memory(short_term_memory, role="user", type="answer", content=text)
                            
                            if not is_follow_up:
                                if "repeat question" in text_lower or "repeat that" in text_lower:
                                    if short_term_memory and short_term_memory[-1]["content"] == text: 
                                        short_term_memory.pop()
                                    return "__REPEAT__"
                                if "skip question" in text_lower or "skip that" in text_lower or "next question" in text_lower:
                                    if short_term_memory and short_term_memory[-1]["content"] == text: 
                                        short_term_memory.pop()
                                    return "__SKIP__"
                            
                            return text
                    
                    # Check for silence (simple volume-based detection)
                    volume = max(abs(int.from_bytes(data[i:i+2], byteorder='little', signed=True)) for i in range(0, len(data), 2))
                    if volume < silence_threshold:
                        consecutive_silence += 4000
                        if consecutive_silence > max_silence:
                            break
                    else:
                        consecutive_silence = 0
                        
                except Exception as e:
                    print(f"[SYSTEM_ERROR] Error reading audio stream: {e}")
                    break
            
            # Get partial result if no complete result was obtained
            partial_result = json.loads(self.recognizer.PartialResult())
            partial_text = partial_result.get('partial', '').strip()
            
            if partial_text:
                print(f"[SYSTEM] Partial result: \"{partial_text}\"")
                conversation_log.append(f"[{datetime.datetime.now().isoformat()}] [USER] {partial_text}")
                self._add_to_short_term_memory(short_term_memory, role="user", type="answer", content=partial_text)
                return partial_text
            else:
                print("[SYSTEM] No speech detected or recognized")
                conversation_log.append(f"[{datetime.datetime.now().isoformat()}] [SYSTEM] Vosk: No speech recognized")
                return None
                
        except Exception as e:
            print(f"[SYSTEM_ERROR] Vosk recognition error: {e}")
            conversation_log.append(f"[{datetime.datetime.now().isoformat()}] [SYSTEM] Vosk error: {e}")
            return None
        finally:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
    
    def _add_to_short_term_memory(self, short_term_memory, role, type, content):
        """Adds an entry to short-term memory and manages its size."""
        MAX_SHORT_TERM_MEMORY_TURNS = 4  # This could be passed as a parameter if needed
        if content:
            short_term_memory.append({"role": role, "type": type, "content": content})
            if len(short_term_memory) > MAX_SHORT_TERM_MEMORY_TURNS * 3:
                short_term_memory[:] = short_term_memory[-(MAX_SHORT_TERM_MEMORY_TURNS * 3):] 
    
    def cleanup(self):
        """Clean up resources."""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.audio:
            self.audio.terminate()
        print("[SYSTEM] Vosk speech handler cleaned up.")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup() 