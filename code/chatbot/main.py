# pip install SpeechRecognition
# pip install playsound
# For Vosk offline backup: pip install -r requirements-vosk.txt
# speech_to_ollama_interactive_qa_v3.py # Filename kept for consistency
#
# This script:
# 1. Acts as a playful and interactive AI Story Guide.
# 2. Uses predefined story themes.
# 3. Asks Ollama to formulate an initial engaging question based on a theme and recent conversation.
# 4. After the user answers, asks Ollama to either ask a relevant follow-up question to dig deeper (guiding if needed) or make an empathetic comment.
# 5. If user doesn't reply, Ollama provides a graceful transition.
# 6. Speaks Ollama's questions, comments, and transitions via TTS using OpenVoice.
# 7. Listens to user's answers using smart speech recognition initialization.
#    - Tries Google Speech Recognition first (if online)
#    - Falls back to Vosk offline recognition if Google is not available
#    - Supports "repeat" and "skip" commands for the main questions
# 8. Logs the entire conversation.
# System messages are printed to console and logged, but not spoken.

import requests
import json
import time
import datetime
import os # For file operations

# import pyttsx3 # No longer needed
import torch
from tts.openvoice_instance import OpenVoiceTTS, OPENVOICE_OUTPUT_AUDIO_PATH
from stt import initialize_speech_handler, AudioManager

# Import prompt functions from the new modular structure
from prompts import (
    get_ollama_to_formulate_question,
    get_ollama_follow_up,
    get_ollama_transition_on_no_reply
)
from prompts.base_prompts import OLLAMA_MODEL

# --- Configuration ---
MICROPHONE_DEVICE_INDEX = None
MAX_SHORT_TERM_MEMORY_TURNS = 4
MAX_FOLLOW_UPS_PER_THEME = 3

# Speech Recognition Configuration
VOSK_MODEL_PATH = None  # Set to specific path, or None to auto-detect

PREDEFINED_STORY_THEMES = [
    # "Tell me about a time you felt truly alive.",
    "A time you experienced a particularly strong emotion (like joy, surprise, or even a bit of fear) and what led to it.",
    "A significant learning experience or a piece of wisdom you gained, and the story behind it.",
    # "A challenge you faced and how you navigated through it, focusing on a key moment or decision.",
    # "Something you're truly looking forward to, and the story or dream connected to that anticipation.",
    # "A favorite way you like to unwind or a special place you go to recharge, and what makes it meaningful to you."
]

# --- Global Variables ---
tts_engine = OpenVoiceTTS() # Will hold the initialized OpenVoice TTS model
CONVERSATION_LOG = []
SHORT_TERM_MEMORY = []

# --- Memory Management ---
def add_to_short_term_memory(role, type, content):
    """Adds an entry to short-term memory and manages its size."""
    global SHORT_TERM_MEMORY
    if content:
        SHORT_TERM_MEMORY.append({"role": role, "type": type, "content": content})
        if len(SHORT_TERM_MEMORY) > MAX_SHORT_TERM_MEMORY_TURNS * 3:
            SHORT_TERM_MEMORY = SHORT_TERM_MEMORY[-(MAX_SHORT_TERM_MEMORY_TURNS * 3):]





# --- Conversation Log Saving --- (No changes needed here)
def save_conversation_log():
    if not CONVERSATION_LOG: return
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"conversations_logs/conversation_log_{timestamp}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            for entry in CONVERSATION_LOG: f.write(entry + "\n")
        print(f"\n[SYSTEM] Conversation log saved to {filename}")
    except Exception as e: print(f"[SYSTEM] Error saving conversation log: {e}")

# --- Main Execution ---
if __name__ == "__main__":

    # Initialize speech recognition (Google first, then Vosk if offline)
    speech_handler, engine_type = initialize_speech_handler(
        microphone_device_index=MICROPHONE_DEVICE_INDEX,
        vosk_model_path=VOSK_MODEL_PATH
    )
    audio_manager = AudioManager()
    
    # Check if any speech handler was successfully initialized
    if not speech_handler:
        error_msg = "[SYSTEM_ERROR] No speech recognition engines could be initialized. Exiting."
        print(error_msg)
        print("[SYSTEM_ERROR] Please ensure:")
        print("  - Your microphone is connected and working")
        print("  - For Google: You have internet connectivity")
        print("  - For Vosk: You have downloaded a model (see requirements-vosk.txt)")
        CONVERSATION_LOG.append(f"[{datetime.datetime.now().isoformat()}] {error_msg}")
        if audio_manager: 
            audio_manager.speak("No speech recognition engines could be initialized. Please check your setup.", CONVERSATION_LOG)
        save_conversation_log()
        exit()
    
    # Log which engine is being used
    engine_name = "Google Speech Recognition (online)" if engine_type == "google" else "Vosk Speech Recognition (offline)"
    print(f"[SYSTEM] ✓ Using: {engine_name}")
    CONVERSATION_LOG.append(f"[{datetime.datetime.now().isoformat()}] [SYSTEM] Active engine: {engine_name}")
    CONVERSATION_LOG.append(f"[{datetime.datetime.now().isoformat()}] [SYSTEM] Speech recognition initialization complete")

    audio_manager.speak_and_log(f"[SYSTEM] Welcome! I'm your AI Story Guide, using Ollama (model: '{OLLAMA_MODEL}'). Let's explore some stories together.", CONVERSATION_LOG, is_system_message=True) # This system message won't be spoken by default

    ai_greeting = "Hello there! I'm excited to hear some of your stories today. When you're ready, we can start with our first story theme."
    # The flag is_ollama_response=True will make speak_and_log call speak()
    audio_manager.speak_and_log(f"{ai_greeting}", CONVERSATION_LOG, is_ollama_response=True)
    add_to_short_term_memory(role="assistant", type="comment", content=ai_greeting)
    # time.sleep(0.5) # OpenVoice speak is blocking, so explicit sleep might not be needed here

    try:
        for theme_index, current_theme in enumerate(PREDEFINED_STORY_THEMES):
            audio_manager.speak_and_log(f"[SYSTEM_PROCESS] Moving to story theme {theme_index + 1}: {current_theme}", CONVERSATION_LOG, is_system_message=True) # Not spoken by default

            main_question_for_theme = get_ollama_to_formulate_question(current_theme, list(SHORT_TERM_MEMORY), CONVERSATION_LOG, add_to_short_term_memory)

            if not main_question_for_theme:
                fallback_q_text = f"Let's explore this: {current_theme} Could you share a story or thought about that?"
                # This system fallback is an announcement, then the question is asked.
                audio_manager.speak_and_log(f"[SYSTEM_FALLBACK] Ollama couldn't formulate a question, so I'll ask this.", CONVERSATION_LOG, is_system_message=True) # Not spoken
                main_question_for_theme = fallback_q_text
                add_to_short_term_memory(role="assistant", type="question", content=main_question_for_theme)
            else:
                 # Log that Ollama formulated it (already logged inside get_ollama_to_formulate_question)
                 pass

            current_question_to_ask = main_question_for_theme
            audio_manager.speak_and_log(f"{current_question_to_ask}", CONVERSATION_LOG, is_question_from_ollama=True) # This will be spoken

            follow_up_count = 0
            while follow_up_count <= MAX_FOLLOW_UPS_PER_THEME:
                # listen_and_transcribe already prints its own "Listening..." prompt
                user_answer_text = speech_handler.listen_and_transcribe(current_question_to_ask, CONVERSATION_LOG, SHORT_TERM_MEMORY, is_follow_up=(current_question_to_ask != main_question_for_theme))

                if user_answer_text == "__REPEAT__":
                    audio_manager.speak_and_log("[SYSTEM_PROCESS] Understood. Repeating the question.", CONVERSATION_LOG, is_system_message=True) # Not spoken
                    audio_manager.speak_and_log(f"{current_question_to_ask}", CONVERSATION_LOG, is_question_from_ollama=True) # Spoken
                    continue

                if user_answer_text == "__SKIP__":
                    # This system message could be spoken if desired, by changing the flag or logic in speak_and_log
                    audio_manager.speak_and_log("[SYSTEM_PROCESS] Okay, let's move to a new story theme.", CONVERSATION_LOG, is_system_message=True) # Not spoken
                    # Optionally, have the AI say something here like "Alright, skipping that one!"
                    # audio_manager.speak_and_log("Alright, skipping that one!", CONVERSATION_LOG, is_ollama_response=True)
                    break

                if not user_answer_text: # Timeout or couldn't understand
                    ai_transition_phrase = get_ollama_transition_on_no_reply(current_question_to_ask, list(SHORT_TERM_MEMORY), CONVERSATION_LOG)
                    if ai_transition_phrase:
                        audio_manager.speak_and_log(f"{ai_transition_phrase}", CONVERSATION_LOG, is_ollama_response=True) # Spoken
                        add_to_short_term_memory(role="assistant", type="comment", content=ai_transition_phrase)
                    else:
                        # Fallback if Ollama fails to provide a transition
                        audio_manager.speak_and_log("[SYSTEM_FALLBACK] It seems we got a bit quiet there. Let's move to a new story theme.", CONVERSATION_LOG, is_system_message=True) # Not spoken
                        audio_manager.speak_and_log("No worries, let's try a new theme then!", CONVERSATION_LOG, is_ollama_response=True) # Spoken AI fallback
                    break

                ollama_response = get_ollama_follow_up(main_question_for_theme, user_answer_text, list(SHORT_TERM_MEMORY), CONVERSATION_LOG, add_to_short_term_memory)

                if ollama_response["type"] == "question":
                    current_question_to_ask = ollama_response["content"]
                    audio_manager.speak_and_log(f"{current_question_to_ask}", CONVERSATION_LOG, is_question_from_ollama=True) # Spoken
                    follow_up_count += 1
                    if follow_up_count >= MAX_FOLLOW_UPS_PER_THEME:
                        # This system message announces the reason for moving on.
                        audio_manager.speak_and_log("[SYSTEM_PROCESS] We've explored that theme well. Let's move to a new story inspiration!", CONVERSATION_LOG, is_system_message=True) # Not spoken
                        # Optionally, have AI say this.
                        # audio_manager.speak_and_log("That was a great exploration! Let's find a new story inspiration.", CONVERSATION_LOG, is_ollama_response=True)
                        break
                else: # Comment
                    audio_manager.speak_and_log(f"{ollama_response['content']}", CONVERSATION_LOG, is_ollama_response=True) # Spoken
                    # This system message is an internal thought process cue.
                    audio_manager.speak_and_log("[SYSTEM_PROCESS] That was a wonderful part of the story. Let's find a new theme to explore.", CONVERSATION_LOG, is_system_message=True) # Not spoken
                    break # Break from follow-ups, move to next theme

            if theme_index < len(PREDEFINED_STORY_THEMES) - 1:
                 audio_manager.speak_and_log("[SYSTEM_PROCESS] Get ready for a new story theme...", CONVERSATION_LOG, is_system_message=True) # Not spoken
                 # Optionally add a spoken transition by the AI here.
                 # audio_manager.speak_and_log("Let's see what our next theme is!", CONVERSATION_LOG, is_ollama_response=True)
                 time.sleep(1.0) # Give a slight pause before new theme starts
            else:
                 audio_manager.speak_and_log("[SYSTEM] We've explored all our story themes for now. Thank you for sharing your wonderful stories!", CONVERSATION_LOG, is_system_message=True) # Not spoken
                 audio_manager.speak_and_log("We've reached the end of our themes for now! Thank you so much for sharing your stories with me. It was a real pleasure!", CONVERSATION_LOG, is_ollama_response=True) # Spoken

    except KeyboardInterrupt:
        print("\n[SYSTEM] Exiting application as per your request.")
        CONVERSATION_LOG.append(f"[{datetime.datetime.now().isoformat()}] [SYSTEM] KeyboardInterrupt: Exiting application.")
        # Use the speak function directly if audio manager is available
        if audio_manager: audio_manager.speak("Okay, exiting now. It was a pleasure hearing your stories!", CONVERSATION_LOG)
        else: print("[SYSTEM_FEEDBACK] Exiting now. It was a pleasure hearing your stories!") # Fallback if TTS failed to init

    except Exception as e:
        error_msg = f"An unexpected error occurred in the main loop: {e}"
        import traceback
        traceback.print_exc() # Print full traceback for debugging
        print(f"[SYSTEM_ERROR] {error_msg}")
        CONVERSATION_LOG.append(f"[{datetime.datetime.now().isoformat()}] [SYSTEM_ERROR] {error_msg}\n{traceback.format_exc()}")
        if audio_manager: audio_manager.speak("An unexpected error occurred. Ending our storytelling session.", CONVERSATION_LOG)
        else: print("[SYSTEM_ERROR] An unexpected error occurred and TTS is not available. Ending session.")
    finally:
        save_conversation_log()
        # Clean up any temporary files and resources
        if audio_manager:
            audio_manager.cleanup()
        if speech_handler:
            # Vosk handler has cleanup method, Google handler doesn't need it
            if hasattr(speech_handler, 'cleanup'):
                speech_handler.cleanup()