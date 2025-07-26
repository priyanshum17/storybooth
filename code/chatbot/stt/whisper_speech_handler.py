# pip install webrtcvad
import datetime
import whisper
import numpy as np
import sounddevice as sd
import webrtcvad
import threading
import time

class WhisperSpeechHandler:
    """Handles speech recognition using OpenAI Whisper locally."""
    
    def __init__(self, model_name="tiny", microphone_device_index=None, sample_rate=16000):
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

    def _transcribe_with_timeout(self, audio_np, timeout_seconds=45):
        """Transcribe audio with timeout protection."""
        result = [None]
        exception = [None]
        
        def transcribe_worker():
            try:
                print("[SYSTEM] Processing audio with Whisper...")
                transcription = self.model.transcribe(audio_np, fp16=False, language='en')
                result[0] = transcription
            except Exception as e:
                exception[0] = e
        
        thread = threading.Thread(target=transcribe_worker)
        thread.daemon = True
        thread.start()
        thread.join(timeout=timeout_seconds)
        
        if thread.is_alive():
            print(f"[SYSTEM_WARNING] Whisper transcription timed out after {timeout_seconds}s")
            return None
        
        if exception[0]:
            print(f"[SYSTEM_ERROR] Whisper transcription error: {exception[0]}")
            return None
        
        return result[0]

    def listen_and_transcribe(self, current_question_for_context=None, conversation_log=None, short_term_memory=None, is_follow_up=False, duration=90, vad_silence_ms=2500, vad_aggressiveness=2):
        """
        Listens from the microphone and transcribes speech using Whisper.
        Uses VAD to keep listening as long as the user is talking, and only stops after vad_silence_ms of silence.
        Returns the transcribed text, or None if nothing recognized.
        """
        print(f"[SYSTEM] Listening... (VAD level {vad_aggressiveness}, timeout {duration}s)")
        vad = webrtcvad.Vad(vad_aggressiveness)  # 0-3, 3 is most aggressive
        frame_duration = 30  # ms
        frame_size = int(self.sample_rate * frame_duration / 1000)
        max_frames = int((duration * 1000) / frame_duration)
        silence_ms = 0
        frames = []
        speech_detected = False
        try:
            with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype='int16', device=self.microphone_device_index) as stream:
                total_time_ms = 0
                dots_printed = 0
                max_dots = 100  # Prevent infinite dots
                
                # for frame_num in range(max_frames):
                while True: 
                    audio = stream.read(frame_size)[0].flatten()
                    if len(audio) == 0:
                        continue
                    frames.append(audio)
                    total_time_ms += frame_duration
                    
                    is_speech = vad.is_speech(audio.tobytes(), self.sample_rate)
                    if is_speech:
                        if not speech_detected:  # First time detecting speech
                            print("\n[SYSTEM] Speech detected! Recording...")
                        speech_detected = True
                        silence_ms = 0
                        if dots_printed < max_dots:
                            print(".", end="", flush=True)  # Show activity
                            dots_printed += 1
                        elif dots_printed == max_dots:
                            print(f"\n[SYSTEM] Long speech detected, continuing to listen...")
                            dots_printed += 1
                    else:
                        if speech_detected:  # Only count silence after speech is detected
                            silence_ms += frame_duration
                    
                    # Stop if we've detected speech and then had enough silence
                    if speech_detected and silence_ms > vad_silence_ms:
                        print("\n[SYSTEM] Speech completed.")
                        break
                    
                    # Hard timeout - always stop after duration seconds
                    if total_time_ms >= duration * 1000:
                        print(f"\n[SYSTEM] Maximum duration reached ({duration}s), stopping...")
                        break
                    
                    # Timeout if no speech detected for too long
                    if not speech_detected and total_time_ms > 5000:  # 5 seconds timeout for initial speech detection
                        print(f"\n[SYSTEM] No speech detected after {total_time_ms/1000:.1f}s, timing out...")
                        break
            
            if not frames:
                print("[SYSTEM_WARNING] No audio frames captured.")
                return None
            
            # Always try to transcribe, even if no speech detected by VAD
            audio_np = np.concatenate(frames).astype(np.float32) / 32768.0  # Convert int16 to float32
            print(audio_np)
            
            if not speech_detected:
                print(f"[SYSTEM] No clear speech detected by VAD, but trying to transcribe {len(frames)} frames anyway...")
            else:
                print(f"[SYSTEM] Speech detected! Transcribing {len(frames)} audio frames...")
            
            # Use timeout-protected transcription
            result = self._transcribe_with_timeout(audio_np, timeout_seconds=45)
            
            if result is None:
                print("[SYSTEM_WARNING] Transcription failed or timed out.")
                if conversation_log is not None:
                    conversation_log.append(f"[{datetime.datetime.now().isoformat()}] [SYSTEM] Whisper transcription failed/timed out")
                return None
            
            text = result.get('text', '').strip()
            
            if conversation_log is not None:
                conversation_log.append(f"[{datetime.datetime.now().isoformat()}] [SYSTEM] Whisper recognition: {text}")
            
            if text and len(text) > 3:  # Only accept non-trivial text
                print(f"[SYSTEM] Transcription: {text}")
                return text
            else:
                print(f"[SYSTEM_WARNING] No meaningful speech recognized. Got: '{text}'")
                return ''
                
        except Exception as e:
            print(f"[SYSTEM_ERROR] Whisper encountered an error: {e}")
            if conversation_log is not None:
                conversation_log.append(f"[{datetime.datetime.now().isoformat()}] [SYSTEM] Whisper error: {e}")
            return ''

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