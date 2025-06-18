from typing import List, Dict, Optional
from .base_prompts import format_memory_for_prompt, make_ollama_request, log_conversation

def get_ollama_transition_on_no_reply(current_question_asked: str, memory_context: List[Dict[str, str]], 
                                     conversation_log: List[str]) -> Optional[str]:
    """Asks Ollama for a gentle transition phrase when the user doesn't reply."""
    
    log_conversation(conversation_log, "[SYSTEM_PROCESS]", 
                    f"User did not reply to '{current_question_asked[:50]}...'. Asking Ollama for a transition.")
    
    formatted_history = format_memory_for_prompt(memory_context)

    prompt = f"""You are a friendly, patient, and understanding AI Story Guide.
{formatted_history}

I (the AI Story Guide) just asked the User:
"{current_question_asked}"

It seems the User didn't reply or wasn't sure what to say, and that's perfectly okay!
Your task is to offer a short, warm, and gentle transitional phrase (1-2 sentences). This should make the User feel comfortable and smoothly signal that we can try a different path or a new story idea.
Avoid making it sound like there was a problem. Keep it light and encouraging.
Do NOT ask a question.
Examples:
- "No worries at all! Sometimes the best stories take a moment to surface. How about we explore something else?"
- "That's quite all right! Perhaps a different theme will spark an idea? Let's try another one."
- "All good! We can always come back to that. Let's see what other adventures we can talk about!"

Please provide ONLY the transitional phrase.
"""

    log_conversation(conversation_log, "[OLLAMA_PROMPT_FOR_NO_REPLY_TRANSITION]", prompt)
    
    transition_phrase = make_ollama_request(prompt, temperature=0.7, timeout=60)
    
    if transition_phrase:
        log_conversation(conversation_log, "[OLLAMA_RAW_TRANSITION_PHRASE]", transition_phrase)
        return transition_phrase
    else:
        error_msg = "Ollama did not return a valid transition phrase."
        print(f"[SYSTEM_ERROR] {error_msg}")
        log_conversation(conversation_log, "[OLLAMA_ERROR]", error_msg)
        return None 