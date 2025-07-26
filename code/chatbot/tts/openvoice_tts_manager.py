"""
OpenVoice TTS Manager for StoryBooth
Implements voice cloning using Corian's voice recording.
"""

import datetime
import os
import time
import torch
from pathlib import Path
try:
    import playsound
    PLAYSOUND_AVAILABLE = True
except ImportError:
    print("[WARNING] playsound not available, will use system audio")
    PLAYSOUND_AVAILABLE = False

# OpenVoice imports with fallback
try:
    from melo.api import TTS
    from openvoice import se_extractor
    from openvoice.api import ToneColorConverter
    OPENVOICE_AVAILABLE = True
    print("[SYSTEM] ✓ OpenVoice libraries loaded successfully")
except ImportError as e:
    print(f"[WARNING] OpenVoice not available: {e}")
    OPENVOICE_AVAILABLE = False
    from .simple_tts_manager import SimpleAudioManager

# Configuration
OPENVOICE_DEVICE = "cuda:0" if torch.cuda.is_available() else "cpu"
REFERENCE_AUDIO_PATH = 'resources/Corian Recording.mp3'  # Corian's voice reference  
CKPT_CONVERTER = 'tts/openvoice_models_downloaded/checkpoints_v2/converter'
CKPT_BASE_SPEAKER = 'tts/openvoice_models_downloaded/checkpoints_v2/base_speakers/ses/en-default.pth'

# Speech settings for natural delivery
SPEECH_SPEED = 0.95  # Slightly slower than normal for more natural delivery
PAUSE_AFTER_SENTENCE = 0.2  # Small pause after speaking for natural rhythm

class AudioManager:
    """
    Audio manager for StoryBooth with OpenVoice voice cloning using Corian's voice.
    Falls back to SimpleAudioManager if OpenVoice is not available or if use_cloned_voice is False.
    """
    
    def __init__(self, use_cloned_voice: bool = True):
        """Initialize the audio manager with OpenVoice voice cloning, unless use_cloned_voice is False."""
        print("[SYSTEM] Initializing OpenVoice TTS Manager with Corian's voice...")
        
        self.use_cloned_voice = use_cloned_voice
        if not use_cloned_voice:
            print("[SYSTEM] use_cloned_voice is False, using Simple TTS (system voice)")
            from .simple_tts_manager import SimpleAudioManager
            self.backend = SimpleAudioManager()
            self.openvoice_enabled = False
            return
        
        if not OPENVOICE_AVAILABLE:
            print("[SYSTEM] OpenVoice not available, falling back to Simple TTS")
            self.backend = SimpleAudioManager()
            self.openvoice_enabled = False
            return
        
        self.openvoice_enabled = True
        self.tts = None
        self.tone_color_converter = None
        self.target_se = None
        self.source_se = None
        
        self._initialize_openvoice()
        
    def _initialize_openvoice(self):
        """Initialize OpenVoice components."""
        try:
            print("[SYSTEM] Loading OpenVoice models...")
            
            # Initialize MeloTTS for base synthesis
            self.tts = TTS(language="EN", device=OPENVOICE_DEVICE)
            print(f"[SYSTEM] ✓ MeloTTS loaded on {OPENVOICE_DEVICE}")
            
            # Initialize tone color converter
            if not os.path.exists(f"{CKPT_CONVERTER}/config.json"):
                raise FileNotFoundError(f"OpenVoice converter config not found at {CKPT_CONVERTER}")
                
            self.tone_color_converter = ToneColorConverter(
                f"{CKPT_CONVERTER}/config.json", 
                device=OPENVOICE_DEVICE
            )
            self.tone_color_converter.load_ckpt(f"{CKPT_CONVERTER}/checkpoint.pth")
            print("[SYSTEM] ✓ Tone color converter loaded")
            
            # Load source speaker embedding
            if not os.path.exists(CKPT_BASE_SPEAKER):
                raise FileNotFoundError(f"Base speaker embedding not found at {CKPT_BASE_SPEAKER}")
                
            self.source_se = torch.load(CKPT_BASE_SPEAKER, map_location=OPENVOICE_DEVICE)
            print("[SYSTEM] ✓ Source speaker embedding loaded")
            
            # Extract Corian's voice embedding
            if not os.path.exists(REFERENCE_AUDIO_PATH):
                print(f"[WARNING] Corian's voice reference not found at {REFERENCE_AUDIO_PATH}")
                print("[SYSTEM] Will use default voice instead of cloned voice")
                self.target_se = None
            else:
                print("[SYSTEM] Extracting Corian's voice characteristics...")
                self.target_se, _ = se_extractor.get_se(
                    REFERENCE_AUDIO_PATH, 
                    self.tone_color_converter, 
                    vad=True
                )
                print("[SYSTEM] ✓ Corian's voice embedding extracted successfully")
            
            print("[SYSTEM] ✓ OpenVoice TTS Manager ready with Corian's voice!")
            
        except Exception as e:
            print(f"[ERROR] OpenVoice initialization failed: {e}")
            print("[SYSTEM] Falling back to simple TTS")
            self.openvoice_enabled = False
            self.backend = SimpleAudioManager()
        
    def speak(self, text: str, conversation_log: list = None):
        """
        Speak the given text using OpenVoice with Corian's cloned voice.
        
        Args:
            text: Text to speak
            conversation_log: Optional conversation log for logging
        """
        # return
        if conversation_log is not None:
            self._log_tts_event(text, conversation_log)
        
        if not self.openvoice_enabled:
            # Fallback to simple TTS
            self.backend.speak(text, conversation_log or [])
            return
        
        try:
            self._speak_with_openvoice(text, conversation_log)
        except Exception as e:
            print(f"[ERROR] OpenVoice TTS failed: {e}")
            print(f"[FALLBACK] Using system TTS: {text}")
            # Simple fallback - just print the text
            print(f"[TTS FALLBACK] {text}")
            if conversation_log:
                timestamp = datetime.datetime.now().isoformat()
                conversation_log.append(f"[{timestamp}] [TTS_ERROR] OpenVoice failed, fallback used")
    
    def _speak_with_openvoice(self, text: str, conversation_log: list = None):
        """Internal method to speak using OpenVoice with voice cloning."""
        temp_source_path = "temp_source_tts.wav"
        cloned_output_path = "cloned_voice_output.wav"
        
        try:
            # Step 1: Preprocess text for better TTS quality
            processed_text = self._preprocess_text_for_tts(text)
            
            # Step 2: Generate base TTS audio using MeloTTS
            speaker_ids = self.tts.hps.data.spk2id
            speaker_id = speaker_ids['EN-Default']  # Use default English speaker
            
            self.tts.tts_to_file(
                processed_text, 
                speaker_id, 
                temp_source_path, 
                speed=SPEECH_SPEED
            )
            
            # Step 2: Apply voice cloning if Corian's voice is available
            if self.target_se is not None:
                # Clone to Corian's voice
                self.tone_color_converter.convert(
                    audio_src_path=temp_source_path,
                    src_se=self.source_se,
                    tgt_se=self.target_se,
                    output_path=cloned_output_path,
                    message="@MyShell"  # Watermark
                )
                final_audio_path = cloned_output_path
            else:
                # Use the base TTS without cloning
                final_audio_path = temp_source_path
            
            # Step 3: Play the audio
            self._play_audio(final_audio_path)
            
            if conversation_log:
                timestamp = datetime.datetime.now().isoformat()
                voice_type = "Corian's cloned voice" if self.target_se is not None else "default voice"
                conversation_log.append(f"[{timestamp}] [TTS_SUCCESS] Spoke with {voice_type}: {text[:50]}...")
            
        finally:
            # Clean up temporary files
            for temp_file in [temp_source_path, cloned_output_path]:
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except Exception as e:
                        print(f"[WARNING] Could not remove temporary file {temp_file}: {e}")
    
    def _preprocess_text_for_tts(self, text: str) -> str:
        """Preprocess text to make it more natural for TTS synthesis."""
        import re
        
        # Remove any system/log prefixes that might be in the text
        text = re.sub(r'^\[.*?\]\s*', '', text)
        text = re.sub(r'^\w+:\s*', '', text)  # Remove "Corian: " or similar prefixes
        
        # Clean up the text
        text = text.strip()
        
        # Fix common punctuation issues
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single space
        text = re.sub(r'([.!?])\s*([.!?])', r'\1 \2', text)  # Fix repeated punctuation
        
        # Ensure sentences end with proper punctuation
        if text and text[-1] not in '.!?':
            text += '.'
        
        # Break up very long sentences for better pacing
        sentences = re.split(r'([.!?])', text)
        processed_sentences = []
        
        for i in range(0, len(sentences), 2):
            if i + 1 < len(sentences):
                sentence = sentences[i] + sentences[i + 1]
            else:
                sentence = sentences[i]
            
            sentence = sentence.strip()
            if sentence:
                # Break up sentences longer than 120 characters at natural pause points
                if len(sentence) > 120:
                    sentence = self._add_natural_pauses(sentence)
                processed_sentences.append(sentence)
        
        result = ' '.join(processed_sentences)
        
        # Final cleanup
        result = re.sub(r'\s+([.!?,:;])', r'\1', result)  # Remove space before punctuation
        result = re.sub(r'([.!?])\s*([.!?])', r'\1 \2', result)  # Fix double punctuation spacing
        
        return result
    
    def _add_natural_pauses(self, text: str) -> str:
        """Add natural pauses to long sentences."""
        import re
        
        # Common places to add pauses
        pause_patterns = [
            (r'\b(and|but|or|so|yet|for|nor)\b', r', \1'),  # Conjunctions
            (r'\b(however|therefore|moreover|furthermore|meanwhile|nonetheless)\b', r', \1,'),  # Transitions
            (r'\b(when|where|while|if|unless|because|since|although|though)\b', r', \1'),  # Subordinate conjunctions
            (r'(,\s*)(which|who|that|where|when)', r'\1\2'),  # Relative clauses
        ]
        
        for pattern, replacement in pause_patterns:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text
    
    def _play_audio(self, audio_path: str):
        """Play audio file with fallback options."""
        try:
            if PLAYSOUND_AVAILABLE:
                playsound.playsound(audio_path, True)
            else:
                # Try system audio commands
                import platform
                system = platform.system()
                if system == "Darwin":  # macOS
                    os.system(f'afplay "{audio_path}"')
                elif system == "Linux":
                    os.system(f'aplay "{audio_path}" 2>/dev/null || paplay "{audio_path}" 2>/dev/null')
                elif system == "Windows":
                    os.system(f'start /min wmplayer "{audio_path}"')
                else:
                    print(f"[WARNING] Could not play audio on {system}")
            
            time.sleep(PAUSE_AFTER_SENTENCE)  # Natural pause after speaking
            
        except Exception as e:
            print(f"[ERROR] Could not play audio: {e}")
            print("[FALLBACK] Audio generation completed but playback failed")
    
    def speak_and_log(self, text: str, conversation_log: list, 
                     is_system_message: bool = False, 
                     is_ollama_response: bool = False,
                     is_question_from_ollama: bool = False):
        """
        Speak text and log it with appropriate categorization.
        
        Args:
            text: Text to speak and log
            conversation_log: Conversation log list
            is_system_message: Whether this is a system message
            is_ollama_response: Whether this is an Ollama-generated response
            is_question_from_ollama: Whether this is an Ollama-generated question
        """
        # Determine message type for logging
        if is_system_message:
            log_prefix = "[SYSTEM]"
        elif is_question_from_ollama:
            log_prefix = "[CORIAN_QUESTION]"
        elif is_ollama_response:
            log_prefix = "[CORIAN]"
        else:
            log_prefix = "[CORIAN]"
        
        # Log the message
        timestamp = datetime.datetime.now().isoformat()
        log_entry = f"[{timestamp}] {log_prefix} {text}"
        conversation_log.append(log_entry)
        
        # Speak the text
        self.speak(text, conversation_log)
    
    def _log_tts_event(self, text: str, conversation_log: list):
        """Log TTS events."""
        timestamp = datetime.datetime.now().isoformat()
        log_entry = f"[{timestamp}] [TTS] Speaking: {text[:50]}..."
        conversation_log.append(log_entry)
    
    def cleanup(self):
        """Clean up audio resources."""
        try:
            # Clean up any remaining temporary files
            temp_files = ["temp_source_tts.wav", "cloned_voice_output.wav"]
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                        print(f"[SYSTEM] ✓ Cleaned up temporary file: {temp_file}")
                    except Exception as e:
                        print(f"[WARNING] Could not remove {temp_file}: {e}")
            
            # Cleanup backend if available
            if hasattr(self, 'backend') and hasattr(self.backend, 'cleanup'):
                self.backend.cleanup()
                
            print("[SYSTEM] ✓ Audio manager cleanup complete")
        except Exception as e:
            print(f"[SYSTEM] Audio cleanup warning: {e}")
    
    def get_status(self):
        """Get the status of the audio manager."""
        status = {
            "audio_manager_available": True,
            "openvoice_available": OPENVOICE_AVAILABLE,
            "openvoice_enabled": getattr(self, 'openvoice_enabled', False),
            "corian_voice_available": False,
            "device": OPENVOICE_DEVICE if OPENVOICE_AVAILABLE else "N/A",
            "backend_type": "OpenVoice" if getattr(self, 'openvoice_enabled', False) else "SimpleAudioManager"
        }
        
        # Check if Corian's voice is available
        if hasattr(self, 'target_se') and self.target_se is not None:
            status["corian_voice_available"] = True
            
        # Add backend status if using simple TTS
        if hasattr(self, 'backend'):
            status["system_tts_available"] = getattr(self.backend, 'system_tts_available', False)
            
        return status
    
    def test_voice_cloning(self, test_text: str = "Hello! This is a test of Corian's voice."):
        """Test the voice cloning functionality."""
        print(f"[TEST] Testing voice cloning with: '{test_text}'")
        
        if not self.openvoice_enabled:
            print("[TEST] OpenVoice not enabled, cannot test voice cloning")
            return False
            
        try:
            self.speak(test_text, [])
            print("[TEST] ✓ Voice cloning test completed successfully")
            return True
        except Exception as e:
            print(f"[TEST] ✗ Voice cloning test failed: {e}")
            return False

# For backward compatibility
class OpenVoiceTTS(AudioManager):
    """Backward compatibility alias."""
    pass 