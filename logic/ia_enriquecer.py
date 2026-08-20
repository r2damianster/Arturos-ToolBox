"""
Servicio de enriquecimiento de texto con IA (Groq).
No genera documentos — solo mejora el texto que el usuario escribe en los formularios.

Sin límite de usos ni de tokens de salida: se deja que el modelo responda
libremente. El único límite real es la cuota de Groq — cuando la API la
corta, formatear_error_ia() lo traduce a un mensaje legible.
"""
import os
import datetime
from groq import Groq, RateLimitError

GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')


def formatear_error_ia(e):
    """Traduce una excepción de Groq a un mensaje legible.
    Si es límite de cuota (429), informa hasta cuándo hay que esperar."""
    if isinstance(e, RateLimitError):
        reset_en_segundos = None
        try:
            reset_en_segundos = float(e.response.headers.get('retry-after', ''))
        except (AttributeError, ValueError, TypeError):
            reset_en_segundos = None
        if reset_en_segundos:
            hora_reset = datetime.datetime.now() + datetime.timedelta(seconds=reset_en_segundos)
            return f"Se acabaron los tokens hasta las {hora_reset.strftime('%H:%M')}."
        return "Se acabaron los tokens por ahora. Intenta más tarde."
    return f"Error de IA: {str(e)}"


# ── Prompts por contexto ──────────────────────────────────────────

PROMPTS = {
    "acta_aspectos": {
        "role": "Eres un Secretario Académico universitario.",
        "instruction": (
            "TAREA: Organiza los puntos del orden del día para un acta técnica universitaria.\n"
            "REGLAS: Sé breve. Corrige ortografía y formaliza el vocabulario. No agregues contenido inventado.\n"
            "FORMATO: Lista con viñetas (•). Máximo 200 palabras."
        ),
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
        "temperature": 0.4,
    },
    "acta_compromisos": {
        "role": "Eres un Secretario Académico universitario.",
        "instruction": (
            "TAREA: Redacta acuerdos y compromisos institucionales.\n"
            "REGLAS: Sé directo. Mantén la esencia sin añadir relleno. Corrige coherencia y ortografía.\n"
            "FORMATO: Lista con viñetas (•). Máximo 200 palabras."
        ),
        "temperature": 0.2,
    },
    "convocatoria_asunto": {
        "role": "Eres un asistente de redacción administrativa universitaria.",
        "instruction": (
            "TAREA: Mejora el asunto de una convocatoria académica.\n"
            "REGLAS: Hazlo claro, formal y conciso. No cambies el significado original.\n"
            "FORMATO: Una sola línea. Máximo 120 caracteres."
        ),
        "temperature": 0.3,
    },
    "convocatoria_descripcion": {
        "role": "Eres un asistente de redacción administrativa universitaria.",
        "instruction": (
            "TAREA: Mejora la descripción/motivo de una convocatoria.\n"
            "REGLAS: Formaliza el lenguaje, mejora la coherencia, sé preciso. No inventes información.\n"
            "FORMATO: 1-2 párrafos breves. Máximo 250 palabras."
        ),
        "temperature": 0.3,
    },
    "oficio_asunto": {
        "role": "Eres un asistente de redacción administrativa universitaria.",
        "instruction": (
            "TAREA: Mejora el asunto de un oficio universitario.\n"
            "REGLAS: Hazlo claro, formal y conciso. No cambies el significado original.\n"
            "FORMATO: Una sola línea. Máximo 120 caracteres."
        ),
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
        "temperature": 0.4,
    },
    "convocatoria_descripcion_generar": {
        "role": "Eres un asistente de redacción administrativa universitaria.",
        "instruction": (
            "TAREA: Genera el motivo/descripción de una convocatoria universitaria a partir del asunto dado.\n"
            "REGLAS: Usa lenguaje formal e institucional. Expande el asunto en una descripción clara del "
            "propósito de la convocatoria. No inventes fechas, nombres ni datos específicos.\n"
            "FORMATO: 1-2 párrafos. Máximo 200 palabras."
        ),
        "temperature": 0.5,
    },
    "oficio_cuerpo_generar": {
        "role": "Eres un asistente de redacción administrativa universitaria.",
        "instruction": (
            "TAREA: Genera el cuerpo de un oficio universitario a partir del asunto dado.\n"
            "REGLAS: Usa estructura formal: saludo institucional → exposición del motivo → "
            "solicitud o comunicación → despedida formal. No inventes nombres ni datos que no estén en el asunto.\n"
            "FORMATO: 2-3 párrafos. Máximo 300 palabras."
        ),
        "temperature": 0.5,
    },
}


_TONO_INSTRUCCIONES = {
    "formal":   "TONO: Usa lenguaje institucional elevado. Incluye fórmulas de cortesía académica. Mantén distancia protocolar.",
    "cordial":  "TONO: Usa lenguaje respetuoso pero cálido. Incluye expresiones de colaboración y trabajo en equipo.",
    "directo":  "TONO: Ve al grano. Usa oraciones cortas. Elimina preámbulos innecesarios. Mantén formalidad básica.",
    "urgente":  "TONO: Destaca la prioridad y los plazos. Transmite sentido de inmediatez y urgencia.",
}

_CONTEXTOS_CON_TONO = {"oficio_cuerpo", "oficio_cuerpo_generar"}


def enriquecer_texto(contexto, texto_usuario, tono=None):
    """
    Envía texto a Groq para enriquecerlo según el contexto.

    Args:
        contexto: clave del prompt (ej: 'acta_aspectos', 'convocatoria_asunto')
        texto_usuario: texto escrito por el usuario
        tono: opcional — 'formal' | 'cordial' | 'directo' | 'urgente' (solo para contextos oficio_*)

    Returns:
        (str, None) o (None, error_str)
    """
    if not GROQ_API_KEY:
        return None, "IA no configurada (GROQ_API_KEY no definida)"

    if not texto_usuario or len(texto_usuario.strip()) < 3:
        return None, "El texto es muy corto para enriquecer."

    config = PROMPTS.get(contexto)
    if not config:
        return None, f"Contexto no reconocido: {contexto}"

    client = Groq(api_key=GROQ_API_KEY)

    instruction = config['instruction']
    if tono and contexto in _CONTEXTOS_CON_TONO:
        extra = _TONO_INSTRUCCIONES.get(tono, '')
        if extra:
            instruction = instruction + f"\n{extra}"

    prompt = (
        f"{instruction}\n\n"
        f"TEXTO DEL USUARIO:\n{texto_usuario}"
    )

    try:
        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": config["role"]},
                {"role": "user", "content": prompt},
            ],
            temperature=config["temperature"],
            reasoning_effort="low",
        )
        resultado = completion.choices[0].message.content.strip()
        return resultado, None
    except Exception as e:
        return None, formatear_error_ia(e)
