from .question_prompts import get_ollama_to_formulate_question
from .followup_prompts import get_ollama_follow_up
from .transition_prompts import get_ollama_transition_on_no_reply

__all__ = [
    'get_ollama_to_formulate_question',
    'get_ollama_follow_up', 
    'get_ollama_transition_on_no_reply'
] 