import datetime
import os
import time
import playsound
import torch
from pathlib import Path
from openvoice import se_extractor

# --- OpenVoice Specific Imports ---
try:
    from .OpenVoice.openvoice.api import BaseSpeakerTTS, ToneColorConverter
    
except ImportError:
    print("[SYSTEM_ERROR] OpenVoice libraries not found. Please ensure OpenVoice is installed correctly.")
    print("See: https://github.com/myshell-ai/OpenVoice")
    exit()


# --- OpenVoice Configuration ---
CURRENT_DIR = Path(__file__).parent.absolute()
OPENVOICE_CHECKPOINT_DIR = os.path.join(CURRENT_DIR, 'openvoice_models_downloaded/checkpoints')
OPENVOICE_OUTPUT_AUDIO_PATH = "temp_tts_output.wav" # Temporary file for generated speech
OPENVOICE_DEVICE = "cuda:0" if torch.cuda.is_available() else "cpu"
OPENVOICE_SPEED = 1.0 # Adjust speech speed (1.0 is normal)

class OpenVoiceTTS:
    # --- Text-to-Speech Functions (Using OpenVoice) ---
    def __init__(self):
        """Initializes the OpenVoice TTS engine."""
        global OPENVOICE_MODEL, TONE_COLOR_CONVERTER, SOURCE_SE

        print(f"\n[SYSTEM] Initializing OpenVoice Text-to-Speech Engine...")
        print(f"[{datetime.datetime.now().isoformat()}] [SYSTEM] Initializing OpenVoice TTS Engine.")

        try:
            # Check if the checkpoint directory exists and has the necessary files
            # This is a simplified check; OpenVoice's internal loading will do more thorough checks.
            required_files = ['converter.pth', 'config.json'] # Example files in ToneColorConverter model dir
            converter_model_dir = os.path.join(OPENVOICE_CHECKPOINT_DIR, 'converter')
            if not os.path.isdir(converter_model_dir) or \
            not all(os.path.exists(os.path.join(converter_model_dir, f)) for f in required_files):
                print(f"[SYSTEM_WARNING] OpenVoice 'converter' model files might be missing in {converter_model_dir}.")
                print(f"Ensure you have run 'python -m openvoice.launcher --prepare_models'.")
                # Allow to proceed, OpenVoiceTTS might still load if paths are slightly different but discoverable by OpenVoice

            # Initialize base TTS model
            OPENVOICE_MODEL = BaseSpeakerTTS(config_path=os.path.join(OPENVOICE_CHECKPOINT_DIR, 'base_speakers', 'EN', 'config.json'),
                                        device=OPENVOICE_DEVICE)
            OPENVOICE_MODEL.load_ckpt(os.path.join(OPENVOICE_CHECKPOINT_DIR, 'base_speakers', 'EN', 'checkpoint.pth'))
            
            # Initialize tone color converter for voice transfer
            TONE_COLOR_CONVERTER = ToneColorConverter(
                config_path=os.path.join(OPENVOICE_CHECKPOINT_DIR, 'converter', 'config.json'),
                device=OPENVOICE_DEVICE
            )
            TONE_COLOR_CONVERTER.load_ckpt(os.path.join(OPENVOICE_CHECKPOINT_DIR, 'converter', 'checkpoint.pth'))
            
            # Load source speaker embedding
            SOURCE_SE = torch.load(os.path.join(OPENVOICE_CHECKPOINT_DIR, 'base_speakers', 'EN', 'en_default_se.pth')).to(OPENVOICE_DEVICE)
            
            print(f"[SYSTEM] OpenVoice TTS initialized successfully using device: {OPENVOICE_DEVICE}.")
            print(f"[{datetime.datetime.now().isoformat()}] [SYSTEM] OpenVoice TTS initialized. Device: {OPENVOICE_DEVICE}")
            
        except Exception as e:
            print(f"[SYSTEM_ERROR] Error initializing OpenVoice TTS engine: {e}")
            print(f"[{datetime.datetime.now().isoformat()}] [SYSTEM] Error initializing OpenVoice TTS engine: {e}")
            OPENVOICE_MODEL = None
            TONE_COLOR_CONVERTER = None
            SOURCE_SE = None

    def speak(self, text_to_speak, CONVERSATION_LOG):
        """Speaks text using OpenVoice TTS, with console fallback."""
        global OPENVOICE_MODEL

        if OPENVOICE_MODEL:
            try:
                # Generate speech
                OPENVOICE_MODEL.tts(
                    text=text_to_speak,
                    output_path=OPENVOICE_OUTPUT_AUDIO_PATH,
                    speaker='default',
                    language='English', # Can be 'en', 'es', 'fr', 'zh', 'jp', 'kr'
                    speed=OPENVOICE_SPEED
                )
                # Play the generated audio file
                playsound.playsound(OPENVOICE_OUTPUT_AUDIO_PATH, True) # True makes it blocking
                time.sleep(0.1) # Small pause after speaking
            except Exception as e:
                fallback_message = f"[TTS FALLBACK (OpenVoice speak error)] {text_to_speak}"
                print(fallback_message)
                print(f"OpenVoice TTS Error details: Could not speak text. {e}")
                CONVERSATION_LOG.append(f"[{datetime.datetime.now().isoformat()}] [TTS Error] {fallback_message}. Details: {e}")
            finally:
                # Clean up the temporary audio file
                if os.path.exists(OPENVOICE_OUTPUT_AUDIO_PATH):
                    try:
                        os.remove(OPENVOICE_OUTPUT_AUDIO_PATH)
                    except Exception as e_rem:
                        print(f"[SYSTEM_WARNING] Could not remove temporary audio file {OPENVOICE_OUTPUT_AUDIO_PATH}: {e_rem}")
                        CONVERSATION_LOG.append(f"[{datetime.datetime.now().isoformat()}] [SYSTEM_WARNING] Failed to remove {OPENVOICE_OUTPUT_AUDIO_PATH}: {e_rem}")
        else:
            fallback_message = f"[TTS FALLBACK (OpenVoice not available)] {text_to_speak}"
            print(fallback_message)

    def clone_voice(self, text_to_speak, reference_audio_path, output_path=None, CONVERSATION_LOG=None):
        """Clones a voice from a reference audio file and speaks the given text."""
        global OPENVOICE_MODEL, TONE_COLOR_CONVERTER, SOURCE_SE

        if not all([OPENVOICE_MODEL, TONE_COLOR_CONVERTER, SOURCE_SE]):
            print("[ERROR] OpenVoice models not properly initialized")
            return

        if not os.path.exists(reference_audio_path):
            print(f"[ERROR] Reference audio file not found: {reference_audio_path}")
            return

        try:
            # Extract target speaker embedding from reference audio
            print("Extracting target tone color embedding from reference audio...")
            target_se, _ = se_extractor.get_se(
                reference_audio_path,
                TONE_COLOR_CONVERTER,
                target_dir='processed',
                vad=True
            )
            print("Target tone color embedding extracted.")

            # Generate temporary source audio
            temp_source_path = "temp_source_tts.wav"
            OPENVOICE_MODEL.tts(
                text=text_to_speak,
                output_path=temp_source_path,
                speaker='default',
                language='English',
                speed=OPENVOICE_SPEED
            )

            # Convert voice
            if output_path is None:
                output_path = "cloned_voice_output.wav"

            TONE_COLOR_CONVERTER.convert(
                audio_src_path=temp_source_path,
                src_se=SOURCE_SE,
                tgt_se=target_se,
                output_path=output_path,
                message="@MyShell"  # Optional watermark
            )

            # Play the generated audio
            playsound.playsound(output_path, True)
            time.sleep(0.1)

            if CONVERSATION_LOG is not None:
                CONVERSATION_LOG.append(f"[{datetime.datetime.now().isoformat()}] [Voice Clone] Successfully cloned voice and spoke: {text_to_speak}")

        except Exception as e:
            error_msg = f"[ERROR] Voice cloning failed: {str(e)}"
            print(error_msg)
            if CONVERSATION_LOG is not None:
                CONVERSATION_LOG.append(f"[{datetime.datetime.now().isoformat()}] {error_msg}")
        finally:
            # Clean up temporary files
            for temp_file in [temp_source_path, output_path]:
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except Exception as e:
                        print(f"[WARNING] Could not remove temporary file {temp_file}: {e}")

if __name__ == "__main__":
    # Example usage
    tts_engine = OpenVoiceTTS()
    try:
        # Basic TTS
        tts_engine.speak("Hello, this is a test of the OpenVoice TTS system.", [])
        print("Text spoken successfully.")
        
        # Voice cloning example
        reference_audio = "path/to/your/reference_audio.wav"  # Replace with your reference audio file
        tts_engine.clone_voice(
            "Hello, this is a test of voice cloning.",
            reference_audio,
            "cloned_output.wav",
            []
        )
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Failed to process text using OpenVoice TTS.") 