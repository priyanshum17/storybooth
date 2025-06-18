import datetime
import os
import torch
from pathlib import Path
import playsound
import time

# --- OpenVoice Specific Imports ---
try:
    import sys
    # Add the tts directory to the path so we can import OpenVoice
    tts_dir = Path(__file__).parent.parent / 'tts'
    sys.path.insert(0, str(tts_dir))
    from OpenVoice.openvoice.api import BaseSpeakerTTS, ToneColorConverter
except ImportError:
    print("[SYSTEM_ERROR] OpenVoice libraries not found. Please ensure OpenVoice is installed correctly.")
    print("See: https://github.com/myshell-ai/OpenVoice")
    exit()

# --- OpenVoice Configuration ---
CURRENT_DIR = Path(__file__).parent.parent.absolute()  # Go up to clean/ directory
OPENVOICE_CHECKPOINT_DIR = os.path.join(CURRENT_DIR, 'tts', 'openvoice_models_downloaded', 'checkpoints')
OPENVOICE_OUTPUT_AUDIO_PATH = "temp_tts_output.wav"  # Temporary file for generated speech
OPENVOICE_DEVICE = "cuda:0" if torch.cuda.is_available() else "cpu"
OPENVOICE_SPEED = 1.0  # Adjust speech speed (1.0 is normal)


class AudioManager:
    """Manages audio output (Text-to-Speech) functionality and speech logging."""
    
    def __init__(self):
        """Initializes the audio manager with OpenVoice TTS engine."""
        self.tts_engine = None
        self._initialize_openvoice()
    
    def _initialize_openvoice(self):
        """Initializes the OpenVoice TTS engine."""
        print(f"\n[SYSTEM] Initializing OpenVoice Text-to-Speech Engine...")
        
        try:
            # Check if the checkpoint directory exists and has the necessary files
            required_files = ['converter.pth', 'config.json']
            converter_model_dir = os.path.join(OPENVOICE_CHECKPOINT_DIR, 'converter')
            if not os.path.isdir(converter_model_dir) or \
            not all(os.path.exists(os.path.join(converter_model_dir, f)) for f in required_files):
                print(f"[SYSTEM_WARNING] OpenVoice 'converter' model files might be missing in {converter_model_dir}.")
                print(f"Ensure you have run 'python -m openvoice.launcher --prepare_models'.")
            
            self.tts_engine = BaseSpeakerTTS(
                config_path=os.path.join(OPENVOICE_CHECKPOINT_DIR, 'base_speakers', 'EN', 'config.json'),
                device=OPENVOICE_DEVICE
            )
            
            self.tts_engine.load_ckpt(os.path.join(OPENVOICE_CHECKPOINT_DIR, 'base_speakers', 'EN', 'checkpoint.pth'))
            
            print(f"[SYSTEM] OpenVoice TTS initialized successfully using device: {OPENVOICE_DEVICE}.")
            
        except Exception as e:
            print(f"[SYSTEM_ERROR] Error initializing OpenVoice TTS engine: {e}")
            self.tts_engine = None
    
    def speak(self, text_to_speak, conversation_log):
        """Speaks text using OpenVoice TTS, with console fallback."""
        if self.tts_engine:
            try:
                # Generate speech
                self.tts_engine.tts(
                    text=text_to_speak,
                    output_path=OPENVOICE_OUTPUT_AUDIO_PATH,
                    speaker='default',
                    language='English',
                    speed=OPENVOICE_SPEED
                )
                # Play the generated audio file
                playsound.playsound(OPENVOICE_OUTPUT_AUDIO_PATH, True)  # True makes it blocking
                time.sleep(0.1)  # Small pause after speaking
            except Exception as e:
                fallback_message = f"[TTS FALLBACK (OpenVoice speak error)] {text_to_speak}"
                print(fallback_message)
                print(f"OpenVoice TTS Error details: Could not speak text. {e}")
                conversation_log.append(f"[{datetime.datetime.now().isoformat()}] [TTS Error] {fallback_message}. Details: {e}")
            finally:
                # Clean up the temporary audio file
                if os.path.exists(OPENVOICE_OUTPUT_AUDIO_PATH):
                    try:
                        os.remove(OPENVOICE_OUTPUT_AUDIO_PATH)
                    except Exception as e_rem:
                        print(f"[SYSTEM_WARNING] Could not remove temporary audio file {OPENVOICE_OUTPUT_AUDIO_PATH}: {e_rem}")
                        conversation_log.append(f"[{datetime.datetime.now().isoformat()}] [SYSTEM_WARNING] Failed to remove {OPENVOICE_OUTPUT_AUDIO_PATH}: {e_rem}")
        else:
            fallback_message = f"[TTS FALLBACK (OpenVoice not available)] {text_to_speak}"
            print(fallback_message)
    
    def speak_and_log(self, message, conversation_log, is_question_from_ollama=False, is_ollama_response=False, is_system_message=False):
        """Helper to speak message (if not system & intended for speech), log it, and print to console."""
        log_entry_message = message
        speak_message_content = message  # This will be spoken if conditions met
        
        log_prefix_for_entry = "[UNDEFINED]"
        should_speak_this_message = False  # Control whether to call speak()
        
        if is_question_from_ollama:
            log_prefix_for_entry = "[ASSISTANT_QUESTION]"
            if message.startswith("[OLLAMA_FORMULATED_QUESTION]"):  # Your old internal prefix
                speak_message_content = message.replace("[OLLAMA_FORMULATED_QUESTION] ", "", 1)
            should_speak_this_message = True
        elif is_ollama_response:  # Typically comments or transitions
            log_prefix_for_entry = "[ASSISTANT_COMMENT]"
            if message.startswith("[OLLAMA_COMMENT]"):  # Your old internal prefix
                speak_message_content = message.replace("[OLLAMA_COMMENT] ", "", 1)
            should_speak_this_message = True
        elif is_system_message:
            # Determine prefix for logging
            if message.startswith("[SYSTEM_PROMPT]"): log_prefix_for_entry = "[SYSTEM_PROMPT]"
            elif message.startswith("[SYSTEM_PROCESS]"): log_prefix_for_entry = "[SYSTEM_PROCESS]"
            elif message.startswith("[SYSTEM_FALLBACK]"): log_prefix_for_entry = "[SYSTEM_FALLBACK]"
            elif message.startswith("[SYSTEM_ERROR]"): log_prefix_for_entry = "[SYSTEM_ERROR]"
            elif message.startswith("[SYSTEM_FEEDBACK]"): log_prefix_for_entry = "[SYSTEM_FEEDBACK]"
            elif message.startswith("[SYSTEM]"): log_prefix_for_entry = "[SYSTEM]"
            else: log_prefix_for_entry = "[SYSTEM]"
            # System messages are generally not spoken, but printed.
            # If you want certain system messages spoken, add a condition here or a new flag.
            # For example, to speak errors:
            # if log_prefix_for_entry == "[SYSTEM_ERROR]": should_speak_this_message = True
        else:
            log_prefix_for_entry = "[UNHANDLED_MESSAGE_TYPE]"
            should_speak_this_message = True  # Speak if type is unknown but not explicitly system
        
        # Print to console (all messages for dev visibility)
        # Strip internal prefixes for cleaner console output if they were just for logic
        console_message = speak_message_content
        if console_message.startswith("[") and "]" in console_message.split(" ", 1)[0]:
            # If message still has a prefix like [SYSTEM_PROCESS], print it.
            # Otherwise, use the determined log_prefix_for_entry
            if not console_message.startswith(log_prefix_for_entry):
                print(f"{log_prefix_for_entry} {console_message}")
            else:
                print(console_message)  # It already contains its own descriptive prefix
        else:
            print(f"{log_prefix_for_entry} {console_message}")
        
        # Speak the message if it's intended for TTS
        if should_speak_this_message:
            self.speak(speak_message_content, conversation_log)
        
        # Log the message with its original form or the processed speak_message_content
        # Ensuring logs have the timestamp and the determined prefix
        if log_entry_message.startswith("[") and "]" in log_entry_message.split(" ", 1)[0] and log_entry_message.split(" ",1)[0] == log_prefix_for_entry:
            conversation_log.append(f"[{datetime.datetime.now().isoformat()}] {log_entry_message}")
        else:
            conversation_log.append(f"[{datetime.datetime.now().isoformat()}] {log_prefix_for_entry} {log_entry_message.replace(log_prefix_for_entry, '').strip()}")
    
    def cleanup(self):
        """Clean up any temporary files."""
        if os.path.exists(OPENVOICE_OUTPUT_AUDIO_PATH):
            try:
                os.remove(OPENVOICE_OUTPUT_AUDIO_PATH)
                print(f"[SYSTEM] Cleaned up temporary audio file: {OPENVOICE_OUTPUT_AUDIO_PATH}")
            except Exception as e_rem:
                print(f"[SYSTEM_WARNING] Could not remove temporary audio file {OPENVOICE_OUTPUT_AUDIO_PATH} on exit: {e_rem}") 