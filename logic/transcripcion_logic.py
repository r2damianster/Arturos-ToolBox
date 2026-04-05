import os
import tempfile
import json as _json
import assemblyai as aai

# Configuración de API
aai.settings.api_key = os.environ.get('ASSEMBLYAI_API_KEY', '')


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


def _config_transcripcion():
    return aai.TranscriptionConfig(
        speech_model="best",
        speaker_labels=True,
        language_detection=True,
        redact_pii=True,
        redact_pii_policies=[
            aai.PIIRedactionPolicy.email_address,
            aai.PIIRedactionPolicy.phone_number,
            aai.PIIRedactionPolicy.us_social_security_number,
            aai.PIIRedactionPolicy.banking_information,
            aai.PIIRedactionPolicy.credit_card_number,
        ],
        redact_pii_sub=aai.PIISubstitutionPolicy.hash,
    )


def _config_acta():
    return aai.TranscriptionConfig(
        speech_model="best",
        speaker_labels=True,
        language_detection=True,
        redact_pii=True,
        redact_pii_policies=[
            aai.PIIRedactionPolicy.email_address,
            aai.PIIRedactionPolicy.phone_number,
        ],
        redact_pii_sub=aai.PIISubstitutionPolicy.hash,
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
        transcript = transcriber.submit(tmp_path, config=_config_transcripcion())

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
    Recupera contexto, formatea el transcript y llama LeMUR.
    Retorna dict con resumen, transcript, idioma, duración, etc.
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

    # ── Formatear transcript ─────────────────────────────────────────────────
    lineas = []
    for utt in (transcript.utterances or []):
        nombre = _nombre_hablante(utt.speaker, speaker_names)
        lineas.append(f"{_ts(utt.start)} {nombre}:\n{utt.text}")
    transcript_formateado = "\n\n".join(lineas)

    # ── LeMUR ────────────────────────────────────────────────────────────────
    hablantes = sorted(set(u.speaker for u in (transcript.utterances or [])))
    mapeo_str = ", ".join(
        f"Hablante {sp} = {_nombre_hablante(sp, speaker_names)}"
        for sp in hablantes
    )
    word_count = len(transcript.text.split()) if transcript.text else 0
    target_words = max(250, int(word_count * 0.15))
    idioma_label = transcript.language_code or "es"

    prompt = f"""Eres un secretario académico experto en redactar actas y resúmenes de reuniones.
Analiza la siguiente transcripción de reunión y genera un resumen estructurado en el mismo idioma del audio (código: {idioma_label}).

Mapeo de hablantes: {mapeo_str}

El resumen debe tener aproximadamente {target_words} palabras (mínimo 250 palabras).

Usa EXACTAMENTE esta estructura con estos encabezados:

PUNTOS TRATADOS
(Lista numerada de los temas principales discutidos en la reunión)

DESARROLLO DE LA REUNIÓN
(Narrativo fluido en tercera persona. Menciona explícitamente quién dijo qué usando el nombre real del hablante. Ejemplo: "Arturo mencionó que...", "Germán señaló que...", "Se discutió entre los participantes...". Resume el contenido esencial sin transcribir literalmente.)

ACUERDOS Y COMPROMISOS
(Lista de decisiones tomadas y compromisos asumidos durante la reunión. Si no hay acuerdos explícitos, indica "No se registraron acuerdos formales.")

No agregues introducciones, conclusiones ni texto fuera de estas tres secciones."""

    try:
        lemur_result = transcript.lemur.task(
            prompt=prompt,
            final_model=aai.LemurModel.claude3_5_sonnet,
        )
        resumen = lemur_result.response.strip()
    except Exception as e:
        resumen = f"ADVERTENCIA: No se pudo generar el resumen automático (LeMUR no disponible en esta cuenta).\nError: {str(e)}"

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
        transcript = transcriber.submit(tmp_path, config=_config_acta())
        return transcript.id
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def finalizar_acta(transcript_id: str) -> dict:
    """
    Asume que el transcript está completado.
    Corre LeMUR y retorna las notas para el Acta Técnica.
    """
    transcript = aai.Transcript.get_by_id(transcript_id)

    if transcript.status == aai.TranscriptStatus.error:
        raise Exception(f"AssemblyAI error: {transcript.error}")

    idioma_label = transcript.language_code or "es"

    prompt = f"""Eres un asistente experto en redactar actas institucionales.
A partir de la transcripción de reunión provista, extrae la información necesaria para completar un Acta Técnica.

Responde ÚNICAMENTE con un objeto JSON válido con exactamente estas 3 claves:

{{
  "aspectos": "Lista de los puntos del orden del día tratados, separados por comas.",
  "desarrollo": "Resumen breve en 3-5 oraciones de lo que sucedió en la reunión, en tercera persona.",
  "compromisos": "Lista de los acuerdos y compromisos asumidos. Si no hubo, escribe: No se registraron acuerdos formales."
}}

Redacta en el mismo idioma del audio (código: {idioma_label})."""

    try:
        lemur_result = transcript.lemur.task(
            prompt=prompt,
            final_model=aai.LemurModel.claude3_5_sonnet,
        )
        raw = lemur_result.response.strip()
        if raw.startswith('```'):
            raw = raw.split('\n', 1)[1] if '\n' in raw else raw[3:]
            raw = raw.rsplit('```', 1)[0].strip()
        data = _json.loads(raw)
    except Exception:
        data = {
            "aspectos": "Error: Acceso a LeMUR denegado o JSON inválido.",
            "desarrollo": "No se pudo procesar el análisis por restricciones de la cuenta API.",
            "compromisos": "No disponible."
        }

    return {
        "aspectos": data.get("aspectos", "").strip(),
        "desarrollo": data.get("desarrollo", "").strip(),
        "compromisos": data.get("compromisos", "").strip(),
    }


# ── Helpers de salida ─────────────────────────────────────────────────────────

def construir_txt(titulo: str, resultado: dict) -> str:
    """Arma el archivo TXT final con resumen + transcript."""
    dur = resultado["duracion_seg"]
    mins, segs = divmod(int(dur), 60)
    separador = "═" * 60

    return f"""TRANSCRIPCIÓN DE REUNIÓN
{'=' * 60}
Título    : {titulo or 'Sin título'}
Idioma    : {resultado['idioma'].upper()}
Duración  : {mins}m {segs}s
Palabras  : {resultado['word_count']}
{separador}

{resultado['resumen_estructurado']}

{separador}
TRANSCRIPCIÓN COMPLETA
{separador}

{resultado['transcript_formateado']}
"""
