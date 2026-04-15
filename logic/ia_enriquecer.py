"""
Servicio de enriquecimiento de texto con IA (Groq / Llama).
No genera documentos — solo mejora el texto que el usuario escribe en los formularios.
"""
import os
import time
import json
from groq import Groq

GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')

# ── Rate limiting simple (en memoria) ─────────────────────────────
# {ip: timestamp_ultimo_uso}
_rate_limit_store = {}

# Intervalo por defecto: 10 minutos (600 segundos) — mutable
_cooldown_seconds = 600

def set_cooldown_seconds(secs):
    """Configura el cooldown global (en segundos)."""
    global _cooldown_seconds
    _cooldown_seconds = max(10, min(secs, 7200))  # entre 10s y 2h

def get_cooldown_seconds():
    """Lee el cooldown configurado (en segundos)."""
    return _cooldown_seconds


def check_rate_limit(identifier="global"):
    """
    Verifica si el identificador puede usar la IA.
    Retorna (allowed: bool, remaining_seconds: int).
    """
    cooldown = get_cooldown_seconds()
    now = time.time()
    last = _rate_limit_store.get(identifier, 0)
    elapsed = now - last
    if elapsed < cooldown:
        remaining = int(cooldown - elapsed)
        return False, remaining
    return True, 0


def record_usage(identifier="global"):
    """Registra el uso de IA para un identificador."""
    _rate_limit_store[identifier] = time.time()


# ── Prompts por contexto ──────────────────────────────────────────

PROMPTS = {
    "acta_aspectos": {
        "role": "Eres un Secretario Académico universitario.",
        "instruction": (
            "TAREA: Organiza los puntos del orden del día para un acta técnica universitaria.\n"
            "REGLAS: Sé breve. Corrige ortografía y formaliza el vocabulario. No agregues contenido inventado.\n"
            "FORMATO: Lista con viñetas (•). Máximo 200 palabras."
        ),
        "max_tokens": 200,
        "temperature": 0.2,
    },
    "acta_desarrollo": {
        "role": "Eres un Secretario Académico universitario.",
        "instruction": (
            "TAREA: Redacta el desarrollo de una reunión académica a partir de notas breves.\n"
            "REGLAS: Conecta las ideas con conectores lógicos. Usa tono formal y solemne. "
            "No inventes hechos, solo expande y mejora la redacción.\n"
            "FORMATO: 2-3 párrafos narrativos. Máximo 400 palabras."
        ),
        "max_tokens": 400,
        "temperature": 0.4,
    },
    "acta_compromisos": {
        "role": "Eres un Secretario Académico universitario.",
        "instruction": (
            "TAREA: Redacta acuerdos y compromisos institucionales.\n"
            "REGLAS: Sé directo. Mantén la esencia sin añadir relleno. Corrige coherencia y ortografía.\n"
            "FORMATO: Lista con viñetas (•). Máximo 200 palabras."
        ),
        "max_tokens": 200,
        "temperature": 0.2,
    },
    "convocatoria_asunto": {
        "role": "Eres un asistente de redacción administrativa universitaria.",
        "instruction": (
            "TAREA: Mejora el asunto de una convocatoria académica.\n"
            "REGLAS: Hazlo claro, formal y conciso. No cambies el significado original.\n"
            "FORMATO: Una sola línea. Máximo 120 caracteres."
        ),
        "max_tokens": 60,
        "temperature": 0.3,
    },
    "convocatoria_descripcion": {
        "role": "Eres un asistente de redacción administrativa universitaria.",
        "instruction": (
            "TAREA: Mejora la descripción/motivo de una convocatoria.\n"
            "REGLAS: Formaliza el lenguaje, mejora la coherencia, sé preciso. No inventes información.\n"
            "FORMATO: 1-2 párrafos breves. Máximo 250 palabras."
        ),
        "max_tokens": 250,
        "temperature": 0.3,
    },
    "oficio_asunto": {
        "role": "Eres un asistente de redacción administrativa universitaria.",
        "instruction": (
            "TAREA: Mejora el asunto de un oficio universitario.\n"
            "REGLAS: Hazlo claro, formal y conciso. No cambies el significado original.\n"
            "FORMATO: Una sola línea. Máximo 120 caracteres."
        ),
        "max_tokens": 60,
        "temperature": 0.3,
    },
    "oficio_cuerpo": {
        "role": "Eres un asistente de redacción administrativa universitaria.",
        "instruction": (
            "TAREA: Redacta o mejora el cuerpo de un oficio universitario.\n"
            "REGLAS: Formaliza el lenguaje, mejora la coherencia, sé preciso. No inventes información. "
            "Usa estructura: saludo institucional → exposición → solicitud/despedida formal.\n"
            "FORMATO: 2-4 párrafos. Máximo 350 palabras."
        ),
        "max_tokens": 350,
        "temperature": 0.4,
    },
}


def enriquecer_texto(contexto, texto_usuario):
    """
    Envía texto a Groq (Llama) para enriquecerlo según el contexto.
    
    Args:
        contexto: clave del prompt (ej: 'acta_aspectos', 'convocatoria_asunto')
        texto_usuario: texto escrito por el usuario
    
    Returns:
        str: texto enriquecido
    """
    if not GROQ_API_KEY:
        return None, "IA no configurada (GROQ_API_KEY no definida)"
    
    if not texto_usuario or len(texto_usuario.strip()) < 3:
        return None, "El texto es muy corto para enriquecer."
    
    config = PROMPTS.get(contexto)
    if not config:
        return None, f"Contexto no reconocido: {contexto}"
    
    client = Groq(api_key=GROQ_API_KEY)
    
    prompt = (
        f"{config['instruction']}\n\n"
        f"TEXTO DEL USUARIO:\n{texto_usuario}"
    )
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": config["role"]},
                {"role": "user", "content": prompt},
            ],
            max_tokens=config["max_tokens"],
            temperature=config["temperature"],
        )
        resultado = completion.choices[0].message.content.strip()
        return resultado, None
    except Exception as e:
        return None, f"Error de IA: {str(e)}"
