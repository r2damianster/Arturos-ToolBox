"""
Fase 5: precarga de datos del memo por IA + sugerencias de comentario por criterio.
Reutiliza el motor Groq y el rate-limit compartido de logic.ia_enriquecer.
Toda sugerencia de IA queda como texto editable — nunca se autoaplica.
"""
import os
import io
import json
import fitz  # PyMuPDF
from docx import Document
from groq import Groq

from logic.titulacion_logic import UPLOADS_DIR
from logic.titulacion_db import get_conn

GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
MODELO = "openai/gpt-oss-120b"

CAMPOS_MEMO = [
    'numero_memo', 'fecha_memo', 'facultad', 'carrera',
    'opcion_titulacion', 'titulo_trabajo', 'estudiante', 'tutor',
]


def extraer_texto(nombre, contenido_bytes):
    """Extrae texto plano de un PDF o DOCX (bytes en memoria)."""
    nombre = (nombre or '').lower()
    if nombre.endswith('.pdf'):
        pdf = fitz.open(stream=contenido_bytes, filetype='pdf')
        try:
            return "\n".join(pagina.get_text() for pagina in pdf)
        finally:
            pdf.close()
    if nombre.endswith('.docx'):
        doc = Document(io.BytesIO(contenido_bytes))
        return "\n".join(p.text for p in doc.paragraphs)
    raise ValueError("Formato no soportado para extracción de texto (use PDF o DOCX).")


def obtener_texto_trabajo(evaluacion_id):
    """Lee y extrae el texto del trabajo del estudiante ya subido (paso 3)."""
    conn = get_conn()
    row = conn.execute(
        "SELECT archivo_trabajo FROM evaluaciones WHERE id = ?", (evaluacion_id,)
    ).fetchone()
    conn.close()
    if not row or not row['archivo_trabajo']:
        raise ValueError("Esta evaluación no tiene un archivo de trabajo subido todavía.")

    ruta = os.path.join(UPLOADS_DIR, row['archivo_trabajo'])
    if not os.path.exists(ruta):
        raise ValueError("El archivo del trabajo no se encuentra en el servidor.")

    with open(ruta, 'rb') as f:
        contenido = f.read()
    return extraer_texto(row['archivo_trabajo'], contenido)


def precargar_datos_memo(texto_memo):
    """Pide a la IA que extraiga los campos del memo en JSON. Siempre editable después."""
    if not GROQ_API_KEY:
        return None, "IA no configurada (GROQ_API_KEY no definida)"

    texto_memo = (texto_memo or '').strip()[:6000]
    if len(texto_memo) < 20:
        return None, "El archivo no tiene suficiente texto para extraer datos."

    client = Groq(api_key=GROQ_API_KEY)
    instruction = (
        "Extrae del siguiente memo de Comisión Académica (ULEAM, proceso de titulación) estos "
        "campos, en JSON estricto y sin texto adicional:\n"
        '{"numero_memo": "", "fecha_memo": "YYYY-MM-DD", "facultad": "", "carrera": "", '
        '"opcion_titulacion": "", "titulo_trabajo": "", "estudiante": "", "tutor": ""}\n'
        "Si un campo no aparece en el texto, déjalo como cadena vacía. No inventes datos."
    )
    try:
        completion = client.chat.completions.create(
            model=MODELO,
            messages=[
                {"role": "system", "content": "Eres un asistente que extrae datos estructurados de memorandos universitarios. Respondes solo JSON válido."},
                {"role": "user", "content": f"{instruction}\n\nTEXTO DEL MEMO:\n{texto_memo}"},
            ],
            max_tokens=400,
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        datos = json.loads(completion.choices[0].message.content.strip())
        return {campo: datos.get(campo, '') or '' for campo in CAMPOS_MEMO}, None
    except json.JSONDecodeError:
        return None, "La IA no devolvió datos válidos. Completa el formulario manualmente."
    except Exception as e:
        return None, f"Error de IA: {str(e)}"


def sugerir_comentario_criterio(criterio_texto, texto_trabajo):
    """Sugerencia breve de observación para un criterio de la rúbrica, a partir del trabajo del estudiante."""
    if not GROQ_API_KEY:
        return None, "IA no configurada (GROQ_API_KEY no definida)"

    fragmento = (texto_trabajo or '').strip()[:4000]
    if len(fragmento) < 20:
        return None, "No hay texto suficiente del trabajo del estudiante para sugerir."

    client = Groq(api_key=GROQ_API_KEY)
    instruction = (
        "Eres un par lector evaluando un trabajo de titulación universitario. Evalúa exclusivamente "
        f"el siguiente criterio de la rúbrica: \"{criterio_texto}\".\n"
        "Con base en el fragmento del trabajo del estudiante, escribe un comentario breve (máximo 40 "
        "palabras) en español indicando si el criterio se cumple y por qué. Es solo una sugerencia para "
        "el evaluador, no decides la calificación. No inventes contenido que no esté en el fragmento."
    )
    try:
        completion = client.chat.completions.create(
            model=MODELO,
            messages=[
                {"role": "system", "content": "Eres un asistente que redacta observaciones breves para evaluadores universitarios."},
                {"role": "user", "content": f"{instruction}\n\nFRAGMENTO DEL TRABAJO:\n{fragmento}"},
            ],
            max_tokens=120,
            temperature=0.3,
        )
        return completion.choices[0].message.content.strip(), None
    except Exception as e:
        return None, f"Error de IA: {str(e)}"
