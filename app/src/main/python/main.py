import threading
from core.brain import Brain

_brain = None
_lock = threading.RLock()

def initialize():
    global _brain
    with _lock:
        if _brain is None:
            _brain = Brain()
        return "REDTEAM AI conectada"

def ask(question):
    if not isinstance(question, str) or not question.strip():
        return "Digite uma pergunta."
    with _lock:
        if _brain is None:
            initialize()
        return _brain.ask(question.strip())
