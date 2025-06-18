#!/usr/bin/env python3
"""
Test script for speech recognition handlers.
This script demonstrates the usage of Google, Vosk, and Hybrid speech handlers.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from speech_handler import SpeechHandler
from vosk_speech_handler import VoskSpeechHandler
from hybrid_speech_handler import HybridSpeechHandler


def test_google_handler():
    """Test Google Speech Recognition handler."""
    print("\n" + "="*50)
    print("TESTING GOOGLE SPEECH HANDLER")
    print("="*50)
    
    try:
        handler = SpeechHandler()
        conversation_log = []
        short_term_memory = []
        
        print("Say something (e.g., 'Hello, this is a test')...")
        result = handler.listen_and_transcribe(
            "Test question", 
            conversation_log, 
            short_term_memory, 
            False
        )
        
        print(f"Result: {result}")
        print(f"Conversation log entries: {len(conversation_log)}")
        print(f"Short-term memory entries: {len(short_term_memory)}")
        
    except Exception as e:
        print(f"Google handler test failed: {e}")


def test_vosk_handler():
    """Test Vosk offline speech recognition handler."""
    print("\n" + "="*50)
    print("TESTING VOSK SPEECH HANDLER")
    print("="*50)
    
    try:
        # Try to find a Vosk model
        model_paths = [
            "models/vosk-model-en-us-0.22",
            "models/vosk-model-small-en-us-0.15",
            "../models/vosk-model-en-us-0.22",
            "../models/vosk-model-small-en-us-0.15"
        ]
        
        model_path = None
        for path in model_paths:
            if os.path.isdir(path):
                model_path = path
                break
        
        if not model_path:
            print("No Vosk model found. Please download a model from:")
            print("https://alphacephei.com/vosk/models")
            print("Extract it to a 'models' directory")
            return
        
        handler = VoskSpeechHandler(model_path=model_path)
        if not handler.model:
            print("Failed to initialize Vosk handler")
            return
            
        conversation_log = []
        short_term_memory = []
        
        print("Say something (e.g., 'Hello, this is a test')...")
        result = handler.listen_and_transcribe(
            "Test question", 
            conversation_log, 
            short_term_memory, 
            False
        )
        
        print(f"Result: {result}")
        print(f"Conversation log entries: {len(conversation_log)}")
        print(f"Short-term memory entries: {len(short_term_memory)}")
        
        # Cleanup
        handler.cleanup()
        
    except Exception as e:
        print(f"Vosk handler test failed: {e}")


def test_hybrid_handler():
    """Test Hybrid speech recognition handler."""
    print("\n" + "="*50)
    print("TESTING HYBRID SPEECH HANDLER")
    print("="*50)
    
    try:
        handler = HybridSpeechHandler()
        
        # Check status
        status = handler.get_status()
        print(f"Google available: {status['google_available']}")
        print(f"Vosk available: {status['vosk_available']}")
        print(f"Prefer offline: {status['prefer_offline']}")
        
        if not status['google_available'] and not status['vosk_available']:
            print("No speech recognition engines available!")
            return
        
        conversation_log = []
        short_term_memory = []
        
        print("Say something (e.g., 'Hello, this is a test')...")
        result = handler.listen_and_transcribe(
            "Test question", 
            conversation_log, 
            short_term_memory, 
            False
        )
        
        print(f"Result: {result}")
        print(f"Conversation log entries: {len(conversation_log)}")
        print(f"Short-term memory entries: {len(short_term_memory)}")
        
        # Test preference switching
        if status['google_available'] and status['vosk_available']:
            print("\nTesting preference switching...")
            handler.set_preference(prefer_offline=True)
            print("Now preferring offline (Vosk) first")
        
        # Cleanup
        handler.cleanup()
        
    except Exception as e:
        print(f"Hybrid handler test failed: {e}")


def main():
    """Main test function."""
    print("Speech Recognition Handler Test Suite")
    print("Make sure your microphone is working and you have internet connectivity")
    print("For Vosk tests, ensure you have downloaded a Vosk model")
    
    while True:
        print("\n" + "="*60)
        print("Choose test:")
        print("1. Test Google Speech Handler")
        print("2. Test Vosk Speech Handler") 
        print("3. Test Hybrid Speech Handler")
        print("4. Run all tests")
        print("5. Exit")
        print("="*60)
        
        choice = input("Enter your choice (1-5): ").strip()
        
        if choice == '1':
            test_google_handler()
        elif choice == '2':
            test_vosk_handler()
        elif choice == '3':
            test_hybrid_handler()
        elif choice == '4':
            test_google_handler()
            test_vosk_handler()
            test_hybrid_handler()
        elif choice == '5':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main() 