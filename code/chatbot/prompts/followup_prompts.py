from typing import List, Dict, Optional
from .base_prompts import format_memory_for_prompt, make_ollama_request, log_conversation

def get_ollama_follow_up(main_theme_question_context: str, user_answer: str, 
                        memory_context: List[Dict[str, str]], conversation_log: List[str],
                        add_to_memory_func) -> Dict[str, str]:
    """
    Asks Ollama to provide a follow-up, guiding the conversation.
    Returns a dictionary: {"type": "question" or "comment", "content": "Ollama's text"}
    """
    
    log_conversation(conversation_log, "[SYSTEM_PROCESS]", 
                    f"Asking Ollama for a follow-up or comment, considering our chat...")

    history_for_prompt = list(memory_context)
    formatted_history = format_memory_for_prompt(history_for_prompt[:-1])

    prompt = f"""You are a warm, playful, and deeply curious AI Story Guide. You're doing a wonderful job helping me (the user) share my story!
Here's the context of our conversation so far:
{formatted_history}

You (the AI Story Guide) most recently asked me (the User) something related to the theme of: "{main_theme_question_context}"
And I (the User) just responded:
"{user_answer}"

Now, let's keep the story flowing! Based on my response:

1.  **Spark More Detail (Follow-Up Question):** If my answer has a juicy detail, a feeling, or a hint of something more, ask a warm, open-ended follow-up question that invites me to expand on *that specific part*. Make it sound like you're genuinely intrigued and eager to hear more. For example, if I said "I felt nervous", you might ask "Oh, nervous! What was going through your mind at that exact moment that made your heart race?" Prefix with "QUESTION: ".
2.  **Playfully Nudge or Clarify (Guiding Question):** If my answer is a little off-topic from the main theme ("{main_theme_question_context}") or a bit vague, playfully and gently try to connect it back or ask for a bit more clarity related to that theme. You could say something like, "That's fascinating! And how did that experience tie into [mention part of the main theme idea] for you?" This is still a "QUESTION: ".
3.  **Warm Acknowledgment & Transition (Empathetic Comment):** If my answer feels like a good place to pause that particular thread of the story, or if we've explored it a bit, offer a warm, empathetic comment (1-2 sentences). Show you've been listening and appreciate what I've shared. This comment can also be a soft signal that we might explore something new next. Prefix with "COMMENT: ".

Choose only ONE option. Be creative and keep the tone light, supportive, and engaging! Remember your goal is to help me tell my story.
"""

    log_conversation(conversation_log, "[OLLAMA_PROMPT_FOR_FOLLOW_UP]", prompt)
    
    ollama_output_text = make_ollama_request(prompt, temperature=0.8, top_p=0.9, timeout=120)

    if ollama_output_text:
        log_conversation(conversation_log, "[OLLAMA_RAW_FOLLOW_UP_RESPONSE]", ollama_output_text)

        if ollama_output_text.upper().startswith("QUESTION:"):
            follow_up_question = ollama_output_text[len("QUESTION:"):].strip()
            if not follow_up_question.endswith('?'): 
                follow_up_question += "?"
            add_to_memory_func(role="assistant", type="question", content=follow_up_question)
            return {"type": "question", "content": follow_up_question}
        elif ollama_output_text.upper().startswith("COMMENT:"):
            comment_text = ollama_output_text[len("COMMENT:"):].strip()
            add_to_memory_func(role="assistant", type="comment", content=comment_text)
            return {"type": "comment", "content": comment_text}
        else:
            log_conversation(conversation_log, "[OLLAMA_WARNING]", 
                           f"Follow-up response did not have expected prefix. Treating as comment: {ollama_output_text}")
            add_to_memory_func(role="assistant", type="comment", content=ollama_output_text)
            return {"type": "comment", "content": ollama_output_text}
    else:
        error_msg = "Ollama did not return a valid follow-up/comment."
        log_conversation(conversation_log, "[OLLAMA_ERROR]", error_msg)
        return {"type": "comment", "content": "That's interesting. Let's try exploring something else."} 