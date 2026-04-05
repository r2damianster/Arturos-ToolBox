import os
import tempfile
import json as _json
import assemblyai as aai
from groq import Groq

# Configuración de APIs
aai.settings.api_key = os.environ.get('ASSEMBLYAI_API_KEY', '')
_groq_client = Groq(api_key=os.environ.get('GROQ_API_KEY', '')) if os.environ.get('GROQ_API_KEY') else None
_GROQ_MODEL = "llama-3.3-70b-versatile"


def _ts(ms):
    """Convierte milisegundos a [MM:SS]."""
    s = ms // 1000
    return f"[{s // 60:02d}:{s % 60:02d}]"


def _nombre_hablante(speaker_letter, speaker_names):
    """Devuelve nombre real si fue mapeado, si no 'Hablante X'."""
    key = speaker_letter.upper()
    if speaker_names and key in speaker_names and speaker_names[key].strip():
        return speaker_names[key].strip()
    return f"Hablante {key}"


def _config_base():
    """Configuración mínima de transcripción (sin funcionalidades de pago)."""
    return aai.TranscriptionConfig(
        speaker_labels=True,
        language_detection=True,
    )


def _guardar_audio_tmp(audio_file):
    """Guarda FileStorage en un archivo temporal. Retorna la ruta."""
    suffix = os.path.splitext(audio_file.filename)[1] or '.mp3'
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    audio_file.save(tmp.name)
    tmp.close()
    return tmp.name


# ── Transcripción de reunión ─────────────────────────────────────────────────

def submit_transcripcion(audio_file, speaker_names: dict, titulo: str) -> str:
    """
    Envía el audio a AssemblyAI sin bloquear.
    Guarda speaker_names y titulo en /tmp para recuperarlos luego.
    Retorna transcript_id.
    """
    tmp_path = _guardar_audio_tmp(audio_file)
    try:
        transcriber = aai.Transcriber()
        transcript = transcriber.submit(tmp_path, config=_config_base())

        ctx_path = os.path.join(tempfile.gettempdir(), f"txn_{transcript.id}.json")
        with open(ctx_path, 'w', encoding='utf-8') as f:
            _json.dump({"speaker_names": speaker_names, "titulo": titulo}, f)

        return transcript.id
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def get_transcript_status(transcript_id: str) -> dict:
    """
    Consulta el estado en AssemblyAI.
    Retorna {"status": "queued|processing|completed|error", "error": "..."}
    """
    t = aai.Transcript.get_by_id(transcript_id)
    status = t.status.value if hasattr(t.status, 'value') else str(t.status)
    return {"status": status, "error": t.error or ""}


def finalizar_transcripcion(transcript_id: str) -> dict:
    """
    Asume que el transcript está completado.
    Formatea el transcript y genera resumen con Groq (gratis).
    """
    ctx_path = os.path.join(tempfile.gettempdir(), f"txn_{transcript_id}.json")
    speaker_names, titulo = {}, ''
    if os.path.exists(ctx_path):
        with open(ctx_path, encoding='utf-8') as f:
            ctx = _json.load(f)
        speaker_names = ctx.get("speaker_names", {})
        titulo = ctx.get("titulo", "")
        try:
            os.unlink(ctx_path)
        except OSError:
            pass

    transcript = aai.Transcript.get_by_id(transcript_id)

    if transcript.status == aai.TranscriptStatus.error:
        raise Exception(f"AssemblyAI error: {transcript.error}")

    # ── Formatear transcript con timestamps y hablantes ──────────────────────
    lineas = []
    for utt in (transcript.utterances or []):
        nombre = _nombre_hablante(utt.speaker, speaker_names)
        lineas.append(f"{_ts(utt.start)} {nombre}:\n{utt.text}")
    transcript_formateado = "\n\n".join(lineas)

    idioma_label = transcript.language_code or "es"
    word_count = len(transcript.text.split()) if transcript.text else 0

    # ── Resumen con Groq ─────────────────────────────────────────────────────
    hablantes = sorted(set(u.speaker for u in (transcript.utterances or [])))
    mapeo_str = ", ".join(
        f"Hablante {sp} = {_nombre_hablante(sp, speaker_names)}"
        for sp in hablantes
    )
    target_words = max(250, int(word_count * 0.15))

    resumen = ""
    if _groq_client and transcript.text:
        try:
            prompt = f"""Eres un secretario académico experto en redactar actas y resúmenes de reuniones.
Analiza la siguiente transcripción y genera un resumen estructurado en el idioma del audio (código: {idioma_label}).
Mapeo de hablantes: {mapeo_str}
El resumen debe tener aproximadamente {target_words} palabras (mínimo 250).

Usa EXACTAMENTE esta estructura:

PUNTOS TRATADOS
(Lista numerada de los temas principales discutidos)

DESARROLLO DE LA REUNIÓN
(Narrativo en tercera persona. Menciona quién dijo qué usando el nombre real. Ejemplo: "Arturo mencionó que...", "Se discutió entre los participantes...")

ACUERDOS Y COMPROMISOS
(Lista de decisiones tomadas. Si no hay, escribe: "No se registraron acuerdos formales.")

No agregues texto fuera de estas tres secciones.

TRANSCRIPCIÓN:
{transcript.text[:8000]}"""

            resp = _groq_client.chat.completions.create(
                model=_GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1500,
            )
            resumen = resp.choices[0].message.content.strip()
        except Exception as e:
            resumen = f"[Resumen no disponible: {str(e)}]"

    return {
        "resumen_estructurado": resumen,
        "transcript_formateado": transcript_formateado,
        "idioma": idioma_label,
        "duracion_seg": transcript.audio_duration or 0,
        "word_count": word_count,
        "titulo": titulo,
    }


# ── Acta técnica ─────────────────────────────────────────────────────────────

def submit_audio_acta(audio_file) -> str:
    """
    Envía el audio de acta a AssemblyAI sin bloquear.
    Retorna transcript_id.
    """
    tmp_path = _guardar_audio_tmp(audio_file)
    try:
        transcriber = aai.Transcriber()
        transcript = transcriber.submit(tmp_path, config=_config_base())
        return transcript.id
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def finalizar_acta(transcript_id: str) -> dict:
    """
    Asume que el transcript está completado.
    Usa Groq para extraer las notas del Acta Técnica.
    """
    transcript = aai.Transcript.get_by_id(transcript_id)

    if transcript.status == aai.TranscriptStatus.error:
        raise Exception(f"AssemblyAI error: {transcript.error}")

    idioma_label = transcript.language_code or "es"
    texto = transcript.text or ""

    if not _groq_client or not texto:
        return {
            "aspectos": "No se pudo procesar el audio.",
            "desarrollo": "Servicio de IA no configurado o transcripción vacía.",
            "compromisos": "No disponible.",
        }

    try:
        prompt = f"""Eres un asistente experto en redactar actas institucionales.
A partir de esta transcripción, extrae información para un Acta Técnica.
Responde ÚNICAMENTE con un JSON válido con exactamente estas 3 claves:

{{
  "aspectos": "Lista de los puntos del orden del día tratados, separados por comas.",
  "desarrollo": "Resumen breve en 3-5 oraciones de lo sucedido, en tercera persona.",
  "compromisos": "Lista de acuerdos y compromisos. Si no hubo, escribe: No se registraron acuerdos formales."
}}

Idioma del audio: {idioma_label}

TRANSCRIPCIÓN:
{texto[:8000]}"""

        resp = _groq_client.chat.completions.create(
            model=_GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=600,
        )
        raw = resp.choices[0].message.content.strip()
        if raw.startswith('```'):
            raw = raw.split('\n', 1)[1] if '\n' in raw else raw[3:]
            raw = raw.rsplit('```', 1)[0].strip()
        data = _json.loads(raw)
    except Exception as e:
        data = {
            "aspectos": f"Error al procesar: {str(e)}",
            "desarrollo": "No se pudo extraer el desarrollo.",
            "compromisos": "No disponible.",
        }

    return {
        "aspectos": data.get("aspectos", "").strip(),
        "desarrollo": data.get("desarrollo", "").strip(),
        "compromisos": data.get("compromisos", "").strip(),
    }


# ── Helper de salida ──────────────────────────────────────────────────────────

def construir_txt(titulo: str, resultado: dict) -> str:
    """Arma el archivo TXT final con resumen + transcript."""
    dur = resultado["duracion_seg"]
    mins, segs = divmod(int(dur), 60)
    sep = "═" * 60

    partes = [
        f"TRANSCRIPCIÓN DE REUNIÓN",
        f"{'=' * 60}",
        f"Título    : {titulo or 'Sin título'}",
        f"Idioma    : {resultado['idioma'].upper()}",
        f"Duración  : {mins}m {segs}s",
        f"Palabras  : {resultado['word_count']}",
        sep,
    ]

    if resultado.get("resumen_estructurado"):
        partes += ["", resultado["resumen_estructurado"], "", sep]

    partes += [
        "TRANSCRIPCIÓN COMPLETA",
        sep,
        "",
        resultado["transcript_formateado"],
    ]

    return "\n".join(partes)
