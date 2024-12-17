import os
import json

def carica_knowledge_base(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def rispondi_a_domanda(domanda, knowledge):
    domanda_lower = domanda.lower()
    if knowledge and domanda_lower in knowledge:
        return knowledge[domanda_lower]
    else:
        return "Non ho capito bene..."
