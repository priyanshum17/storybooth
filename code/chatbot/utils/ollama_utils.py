import requests
import datetime
from typing import Dict, Any, Optional, List

# Configuration constants
OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma3"

def format_memory_for_prompt(memory_list: List[Dict[str, str]]) -> str:
    """Formats the short-term memory for inclusion in an Ollama prompt."""
    if not memory_list:
        return "This is the beginning of our conversation."

    formatted_history = "Here's a summary of our recent conversation:\n"
    for entry in memory_list:
        if entry["role"] == "assistant":
            if entry["type"] == "question":
                formatted_history += f"I (the AI Story Guide) asked you: \"{entry['content']}\"\n"
            elif entry["type"] == "comment":
                 formatted_history += f"I (the AI Story Guide) then said: \"{entry['content']}\"\n"
        elif entry["role"] == "user" and entry["type"] == "answer":
            formatted_history += f"You (the User) responded: \"{entry['content']}\"\n"
    return formatted_history.strip()

def make_ollama_request(prompt: str, temperature: float = 0.8, top_p: float = 0.9, timeout: int = 60) -> Optional[str]:
    """Make a request to Ollama API with the given prompt and parameters."""
    payload = {
        "model": OLLAMA_MODEL, 
        "prompt": prompt, 
        "stream": False, 
        "options": {"temperature": temperature, "top_p": top_p}
    }
    
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=timeout)
        response.raise_for_status()
        response_data = response.json()
        
        if "response" in response_data and response_data["response"].strip():
            return response_data["response"].strip()
        else:
            error_msg = "Ollama did not return a valid response."
            if "error" in response_data:
                error_msg += f" Error: {response_data['error']}"
            print(f"[SYSTEM_ERROR] {error_msg}")
            return None
            
    except Exception as e:
        error_msg = f"Error making Ollama request: {e}"
        print(f"[SYSTEM_ERROR] {error_msg}")
        return None

def log_conversation(conversation_log: List[str], prefix: str, message: str):
    """Helper function to log conversation entries with timestamp."""
    conversation_log.append(f"[{datetime.datetime.now().isoformat()}] {prefix} {message}") 