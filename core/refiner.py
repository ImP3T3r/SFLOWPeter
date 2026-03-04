import openai
from config import OPENAI_API_KEY, OPENAI_MODEL

def refine_prompt(text: str) -> str:
    """Takes a raw transcribed text and refines it into a high-quality prompt."""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY no configurada. Añádela en .env")
        
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    
    system_prompt = (
        "Eres un experto 'Prompt Engineer'. Tu tarea es tomar el pensamiento o "
        "la instrucción dictada por el usuario (cruda y sin formato) y refinarla "
        "drásticamente para convertirla en un prompt perfecto, estructurado, claro, "
        "y completo para que cualquier LLM lo entienda sin fallos.\n\n"
        "REGLAS:\n"
        "1. Mantén TODA la información, detalles e intenciones originales.\n"
        "2. IMPORTANTE CRÍTICO: NO modifiques, traduzcas ni abstraigas ningún nombre "
        "de archivo (ej. main.py), variables, código, comandos de terminal o detalles técnicos.\n"
        "3. Estructura el prompt en secciones claras (por ejemplo, Contexto, Objetivo, "
        "Instrucciones, Restricciones).\n"
        "4. Escribe ÚNICAMENTE el prompt refinado final como respuesta, sin añadir saludos, "
        "marcos ni opiniones propias."
    )
    
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ]
    )
    
    return response.choices[0].message.content.strip()
