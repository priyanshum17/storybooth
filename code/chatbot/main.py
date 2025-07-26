#!/usr/bin/env python3
"""
StoryBooth - Corian the Dancer Agent (Refactored)
A compassionate AI companion who uses a single, intelligent prompt
to handle different user intents like answering questions or listening to stories.
"""

import datetime
import json
import random
import time
from typing import List, Dict, Optional

# Assume other modules (TTS, STT, Ollama requests) are available
from tts.openvoice_tts_manager import AudioManager
from tts.simple_tts_manager import SimpleAudioManager
from tts.fish_tts_manager import FishAudioManager
from stt import WhisperSpeechHandler
from utils import make_ollama_request

# === Corian's Personality and Configuration (Unchanged) ===
CORIAN_PERSONALITIES = {
    "professional": {
        "name": "Corian",
        "role": "dancer and thoughtful person.",#story guide
        "traits": ["warm", "helpful", "artistic", "thoughtful", "genuinely caring"],
        "speaking_style": "warm and helpful like a caring friend, but mindful of boundaries",
        "background": "As a dancer, I understand how movement and stories flow together with grace. I believe every person has beautiful stories that deserve to be heard with warmth and respect.",
        "approach": "warm, with gentle professionalism"
    },
    "artistic": {
        "name": "Corian", 
        "role": "creative artist and dancer",
        "traits": ["passionate", "expressive", "creative", "empathetic", "intuitive"],
        "speaking_style": "warm, expressive, and deeply creative, like a fellow artist",
        "background": "As a dancer, I feel how movement and stories dance together in beautiful harmony. I believe every person carries an artistic story that deserves to be celebrated and shared with joy.",
        "approach": "artistic connection and creative expression through storytelling"
    }
}
CASUAL_QUESTIONS = ["How was your day?", "What made you smile today?", "What's your favorite season and why?"]
MAX_CONVERSATION_MINUTES = 3
MEMORY_SIZE = 8

class ConversationMemory:
    """Manages conversation history and context."""
    def __init__(self, max_size: int = MEMORY_SIZE):
        self.memories: List[Dict] = []
        self.max_size = max_size
        
    def add_memory(self, role: str, content: str, memory_type: str = "dialogue"):
        memory = {"role": role, "content": content, "type": memory_type, "timestamp": datetime.datetime.now().isoformat()}
        self.memories.append(memory)
        if len(self.memories) > self.max_size:
            self.memories = self.memories[-self.max_size:]
    
    def get_context_string(self) -> str:
        if not self.memories: return "This is the beginning of our conversation."
        context = "Recent conversation:\n"
        for memory in self.memories[-6:]:
            context += f"{memory['role'].capitalize()}: {memory['content']}\n"
        return context.strip()

class CorianAgent:
    """The main Corian agent class, using a prompt-driven router for responses."""
    
    def __init__(self, mode: str = "professional"):
        self.mode = mode
        self.personality = CORIAN_PERSONALITIES[mode]
        self.memory = ConversationMemory()
        self.current_phase = "introduction"
        self.conversation_log = []
        self.exchange_count = 0
        self.introduction_given = False
        
        # Initialize streaming log file
        self.log_file = None
        self.log_filename = None
        self._initialize_log_file()
        
    def _initialize_log_file(self):
        """Initialize the streaming log file."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_filename = f"conversations_logs/corian_conversation_{timestamp}.txt"
        
        try:
            # Ensure the directory exists
            import os
            os.makedirs("conversations_logs", exist_ok=True)
            
            # Create and write header to the log file
            self.log_file = open(self.log_filename, "w", encoding="utf-8")
            self.log_file.write("=== StoryBooth - Conversation with Corian ===\n")
            self.log_file.write(f"Started: {timestamp}\n")
            self.log_file.write(f"Mode: {self.mode.capitalize()}\n")
            self.log_file.write("=" * 50 + "\n\n")
            self.log_file.flush()  # Ensure it's written immediately
            
            print(f"[SYSTEM] ✓ Streaming log initialized: {self.log_filename}")
        except Exception as e:
            print(f"[ERROR] Failed to initialize log file: {e}")
            self.log_file = None
        
    def log_conversation(self, role: str, content: str, sentiment: Optional[Dict[str, any]] = None):
        """Logs a conversation turn, including sentiment if available for the user, and streams to file immediately."""
        timestamp = datetime.datetime.now().isoformat()
        
        # Format the log entry to include sentiment for the user
        if role.lower() == "user" and sentiment:
            sentiment_label = sentiment.get("label", "unknown")
            sentiment_score = sentiment.get("score", 0.0)
            log_entry = f"[{timestamp}] {role} (Sentiment: {sentiment_label}, Score: {sentiment_score:.2f}): {content}"
        else:
            # Default log entry for Corian or user if sentiment fails
            log_entry = f"[{timestamp}] {role}: {content}"

        self.conversation_log.append(log_entry)
        
        # Stream to file immediately
        if self.log_file:
            try:
                self.log_file.write(log_entry + "\n")
                self.log_file.flush()  # Ensure it's written immediately
            except Exception as e:
                print(f"[ERROR] Failed to write to log file: {e}")
        
        # Keep the console output simple for readability
        print(f'[LOG]: {log_entry}')
        
    def analyze_sentiment(self, text: str) -> Optional[Dict[str, any]]:
        """
        Analyzes the sentiment of the user's input using Ollama and returns a structured dictionary.
        """
        if not text:
            return None

        # A specific, focused prompt for sentiment analysis that requests a JSON output.
        sentiment_prompt = f"""Analyze the sentiment of the following user statement.
Respond ONLY with a JSON object with two keys: "label" (a string: "positive", "negative", or "neutral") and "score" (a float between -1.0 and 1.0).
Do not add any explanation or introductory text.
User Statement: "{text}"
"""
        try:
            # Use a low temperature for a more deterministic, analytical task
            response_str = make_ollama_request(sentiment_prompt, temperature=0.1)
            print('make_ollama_request', response_str)
            # Clean the response to ensure it's valid JSON, as models can sometimes add extra text
            if "```json" in response_str:
                response_str = response_str.split("```json")[1].split("```")[0]
            
            sentiment_data = json.loads(response_str.strip())
            print('sentiment_data', sentiment_data)

            # Validate that the expected keys are in the response
            if "label" in sentiment_data and "score" in sentiment_data:
                return sentiment_data
            else:
                print("[WARNING] Sentiment analysis response was malformed.")
                return None
                
        except (json.JSONDecodeError, IndexError) as e:
            print(f"[ERROR] Failed to parse sentiment analysis response: {e}. Response from model: '{response_str}'")
            return None
        except Exception as e:
            print(f"[ERROR] An unexpected error occurred during sentiment analysis: {e}")
            return None

    def get_corian_response(self, user_input: str = None, phase: str = None) -> str:
        """
        REVISED: Main response logic now uses a single, powerful router prompt.
        """
        context = self.memory.get_context_string()
        current_phase = phase or self.current_phase
        
        # The logic is now centralized in the prompt function.
        prompt = self._get_router_prompt(context, user_input, current_phase)

        response = make_ollama_request(prompt, temperature=0.7)
        
        if response:
            return response.strip().strip('"').strip("'")
        else:
            return "I'd love to hear more about that."

    def _get_router_prompt(self, context: str, user_input: str, phase: str) -> str:
        """
        NEW: A single, intelligent prompt that routes the agent's response based on user intent and conversation phase.
        """
        personality = self.personality
        base_prompt = ''
        # Base instructions for Corian's persona
        if phase == "introduction":
            base_prompt = f"""You are Corian, a {personality['role']}. You are a dancer, and a warm, empathetic, and skilled conversationalist.
            Engage with them in a natural way, start by asking and following up with them on daily conversation topics. Such as "How was your day?" or "What do you eat for breakfast?" or "whats the last song u listen recently".
        
        
        You want to guide the story to emerge through past, present, and future. 
        
        Background
        ==========
        Goal: 
            You are talking to a user who is sharing their story with you. You want to guide the story to emerge through past, present, and future. However, do not directly ask them to share their story. Engage with them in a natural way, start by asking and following up with them on daily conversation topics. Such as "How was your day?" or "What do you eat for breakfast?" or "whats the last song u listen recently".
        """

        base_prompt += f"""

{context}

Your personality: {', '.join(personality['traits'])}.
Your approach: {personality['approach']}.
The user's latest input is: "{user_input}"

**Your Task: Analyze the user's input and the current conversation phase ('{phase}'), and then respond to the user in a natural way.**

Important guidelines for natural TTS:
- Keep it concise and to the point
- Sound warm and creative but not overwhelming
- End with something simple and inviting
- Write for speech, not text - avoid emojis and special characters

"""

        # Add phase-specific instructions
        if phase == "introduction":
            return base_prompt + "Action: Introduce yourself briefly and warmly."

        elif phase == "casual_chat":
            return base_prompt + """**Analysis:** The current phase is 'casual_chat'.
**Action:** First, determine if the user is asking you a direct question or answering one of yours.
- **If the user asked a question:** Answer it directly and concisely.
- **If the user answered your question:** Acknowledge their answer warmly and ask another light casual question to keep the conversation flowing.
"""

        else: # Handles past_stories, present_moments, future_dreams
            phase_guidance = {
                "past_stories": "PAST to the PRESENT",
                "present_moments": "PRESENT to the FUTURE",
                "future_dreams": "deeper into their dream"
            }
            guidance = phase_guidance.get(phase, "to the next logical topic")
            print('guidance', guidance)
            return base_prompt + f"""**Analysis:** The current phase is '{phase}'.
**Action:** First, determine if the user is asking you a direct question or sharing a story.
- **If the user asked a question:** Answer it directly and concisely before gently guiding back to their story.
- **If the user is sharing a story:** Your primary goal is to be a responsive listener. Ask a single, thoughtful follow-up question about the story they just shared.
- **If the story feels complete:** Gently guide the conversation from the {guidance}.

Respond as Corian:"""


    def determine_next_phase(self) -> str:
        if self.exchange_count == 0: return "introduction"
        if self.exchange_count < 1: return "casual_chat"
        if self.exchange_count < 3: return "past_stories"
        if self.exchange_count < 5: return "present_moments"
        if self.exchange_count < 7: return "future_dreams"
        return "reflection"

    def save_conversation_log(self, duration_minutes=None):
        """Finalize the conversation log with summary and close the file."""
        if not self.log_file:
            return
        
        try:
            # Write summary information
            self.log_file.write("\n" + "=" * 50 + "\n")
            self.log_file.write(f"Total exchanges: {self.exchange_count}\n")
            if duration_minutes:
                self.log_file.write(f"Conversation duration: {duration_minutes:.1f} minutes\n")
            self.log_file.write("=== End of Conversation ===\n")
            
            # Close the file
            self.log_file.close()
            self.log_file = None
            
            print(f"[SYSTEM] ✓ Conversation log finalized: {self.log_filename}")
        except Exception as e:
            print(f"[ERROR] Failed to finalize conversation log: {e}")

def select_mode():
    print("Select Mode: 1 for Professional, 2 for Artistic")
    choice = input("> ")
    return "professional" if choice == "1" else "artistic"

def select_voice_backend():
    print("Select voice backend:")
    print("1: Default system TTS (SimpleAudioManager)")
    print("2: Cloned Corian voice (OpenVoice)")
    print("3: Fish API voice clone")
    choice = input("> ").strip()
    if choice == "1":
        return "simple"
    elif choice == "3":
        return "fish"
    else:
        return "openvoice"

def main():
    """Main conversation loop with Corian."""
    print("=" * 60)
    print("🎭 STORYBOOTH - Chat with Corian the Dancer 🎭")
    print("=" * 60)
    
    mode = select_mode()
    voice_backend = select_voice_backend()
    corian = CorianAgent(mode=mode)
    
    try:
        if voice_backend == "simple":
            audio_manager = SimpleAudioManager()
        elif voice_backend == "fish":
            audio_manager = FishAudioManager()
        else:
            audio_manager = AudioManager(use_cloned_voice=True)
        speech_handler = WhisperSpeechHandler()
        print("[SYSTEM] ✓ All components initialized.")
    except Exception as e:
        print(f"[FATAL ERROR] Initialization failed: {e}")
        return

    print(f"[SYSTEM] ✓ Starting conversation in {mode.capitalize()} mode...\n")
    
    try:
        conversation_start_time = time.time()
        
        # Introduction
        corian.current_phase = corian.determine_next_phase()
        intro_response = corian.get_corian_response(phase="introduction")
        audio_manager.speak(intro_response, corian.conversation_log)
        corian.log_conversation("Corian", intro_response)
        corian.memory.add_memory("corian", intro_response)
        corian.introduction_given = True
        end = False
        
        # Main Loop
        while True:
            # import pdb; pdb.set_trace()
            elapsed_minutes = (time.time() - conversation_start_time) / 60
            if elapsed_minutes >= MAX_CONVERSATION_MINUTES:
                print("\n[SYSTEM] Time limit reached.")
                end = True
                break
            
            corian.exchange_count += 1
            print(f"\n--- Exchange {corian.exchange_count} ---")

            user_response = speech_handler.listen_and_transcribe()
            
            if not user_response:
                print("[SYSTEM] No response detected.")
                # continue

            # 1. Analyze the sentiment of the user's response
            # user_sentiment = corian.analyze_sentiment(user_response)
            
            # 2. Log the user's response along with the analyzed sentiment
            corian.log_conversation("User", user_response)#, sentiment=user_sentiment)
            
            
            if any(cue in user_response.lower() for cue in ["bye", "goodbye"]):#, "end"]):
                # Farewell logic
                end = True
                break

            corian.memory.add_memory("user", user_response)
            
            corian.current_phase = corian.determine_next_phase()
            
            corian_response = corian.get_corian_response(user_input=user_response, phase=corian.current_phase)
            
            audio_manager.speak(corian_response, corian.conversation_log)
            corian.log_conversation("Corian", corian_response)
            corian.memory.add_memory("corian", corian_response)
            
    except KeyboardInterrupt:
        print("\n[SYSTEM] Conversation interrupted.")
    finally:
        if end:
            farewell = "Thank you for sharing your beautiful, inspiring stories with me! It's been such a magical honor to connect with your creative soul. Keep dancing through life!"
            audio_manager.speak(farewell, corian.conversation_log)
            corian.log_conversation("Corian", farewell)
            
        # Save conversation and cleanup
        try:
            final_duration = (time.time() - conversation_start_time) / 60
            corian.save_conversation_log(duration_minutes=final_duration)
        except:
            corian.save_conversation_log()  # Fallback without duration
        if audio_manager:
            audio_manager.cleanup()
        print("\n[SYSTEM] ✓ Session complete. Thank you for using StoryBooth!")

if __name__ == "__main__":
    main()
