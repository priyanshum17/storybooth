from typing import List, Dict, Optional
from .base_prompts import format_memory_for_prompt, make_ollama_request, log_conversation

def get_ollama_to_formulate_question(question_theme: str, memory_context: List[Dict[str, str]], 
                                   conversation_log: List[str], 
                                   add_to_memory_func) -> Optional[str]:
    """Asks Ollama to formulate an initial question based on a theme and recent context."""
    
    log_conversation(conversation_log, "[SYSTEM_PROCESS]", 
                    f"Asking Ollama to formulate an initial story question based on the theme: '{question_theme}' and recent chat...")
    
    formatted_history = format_memory_for_prompt(memory_context)

    # Longer questions prompt
    prompt_for_question_formulation = f"""You are a warm, playful, and deeply curious AI Story Guide. Your delight is in helping the user (me) uncover and share their unique stories.
{formatted_history}

Now, to gently start a new story thread, I'd like you to formulate a creative and inviting OPENING question.
This question should be inspired by the following theme: '{question_theme}'
Make it sound like a genuine, friendly invitation to share, perhaps with a touch of wonder or playfulness.
For example, if the theme is "a challenge you faced", instead of just "Tell me about a challenge", you might ask "Was there ever a time you felt like you were in a movie, facing a really tricky situation? I'd love to hear about it!" or "I'm curious, what's a hurdle you've jumped over that made you feel super proud afterwards?"
Connect to our recent chat if it feels natural, otherwise, a fresh and intriguing question on the theme is perfect.
Please output ONLY the question itself. Ensure it ends with a question mark.
"""

    log_conversation(conversation_log, "[OLLAMA_PROMPT_FOR_INITIAL_QUESTION]", prompt_for_question_formulation)
    
    formulated_question = make_ollama_request(prompt_for_question_formulation, temperature=0.85, top_p=0.9, timeout=60)
    
    if formulated_question:
        if not formulated_question.endswith('?'):
            formulated_question = formulated_question.rstrip('.。,') + "?"
        
        log_conversation(conversation_log, "[OLLAMA_RAW_FORMULATED_QUESTION_RESPONSE]", formulated_question)
        add_to_memory_func(role="assistant", type="question", content=formulated_question)
        return formulated_question
    else:
        error_msg = "Ollama did not return a valid question for the theme."
        print(f"[SYSTEM_ERROR] {error_msg}")
        log_conversation(conversation_log, "[OLLAMA_ERROR]", error_msg)
        return None 