import os
import io
import tempfile
import assemblyai as aai

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


def transcribir_y_resumir(audio_file, speaker_names: dict) -> dict:
    """
    Recibe un FileStorage de Flask y un dict {A: 'Arturo', B: 'German', ...}
    Devuelve dict con: resumen_estructurado, transcript_formateado, idioma, duracion_seg
    """
    # ── 1. Guardar en archivo temporal ──────────────────────────────────────
    suffix = os.path.splitext(audio_file.filename)[1] or '.mp3'
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        audio_file.save(tmp.name)
        tmp.close()

        # ── 2. Configurar y transcribir ──────────────────────────────────────
        # speech_model="universal-2" es requerido para language_detection (SDK ≥ 0.30)
        config = aai.TranscriptionConfig(
            speech_model        = "universal-2",
            speaker_labels      = True,
            language_detection  = True,
            redact_pii          = True,
            redact_pii_policies = [
                aai.PIIRedactionPolicy.email_address,
                aai.PIIRedactionPolicy.phone_number,
                aai.PIIRedactionPolicy.us_social_security_number,
                aai.PIIRedactionPolicy.banking_information,
                aai.PIIRedactionPolicy.credit_card_number,
            ],
            redact_pii_sub = aai.PIISubstitutionPolicy.hash,
        )

        transcriber = aai.Transcriber()
        transcript  = transcriber.transcribe(tmp.name, config=config)

        if transcript.status == aai.TranscriptStatus.error:
            raise Exception(f"AssemblyAI error: {transcript.error}")

        # ── 3. Formatear transcript con timestamps y hablantes ───────────────
        lineas_transcript = []
        for utt in (transcript.utterances or []):
            nombre = _nombre_hablante(utt.speaker, speaker_names)
            lineas_transcript.append(
                f"{_ts(utt.start)} {nombre}:\n{utt.text}"
            )
        transcript_formateado = "\n\n".join(lineas_transcript)

        # ── 4. Mapeo de hablantes para el prompt ─────────────────────────────
        hablantes_detectados = sorted(set(
            u.speaker for u in (transcript.utterances or [])
        ))
        mapeo_str = ", ".join(
            f"Hablante {sp} = {_nombre_hablante(sp, speaker_names)}"
            for sp in hablantes_detectados
        )

        # ── 5. LeMUR: resumen estructurado ───────────────────────────────────
        word_count   = len(transcript.text.split())
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

        lemur_result = transcript.lemur.task(
            prompt      = prompt,
            final_model = aai.LemurModel.claude3_5_sonnet,
        )
        resumen = lemur_result.response.strip()

        # ── 6. Duración ──────────────────────────────────────────────────────
        duracion_seg = (transcript.audio_duration or 0)

        return {
            "resumen_estructurado": resumen,
            "transcript_formateado": transcript_formateado,
            "idioma": idioma_label,
            "duracion_seg": duracion_seg,
            "word_count": word_count,
        }

    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass


def extraer_notas_desde_audio(audio_file) -> dict:
    """
    Transcribe el audio y extrae las 3 secciones para el Acta Técnica.
    Devuelve dict con claves: aspectos, desarrollo, compromisos.
    """
    import json as _json

    suffix = os.path.splitext(audio_file.filename)[1] or '.mp3'
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        audio_file.save(tmp.name)
        tmp.close()

        config = aai.TranscriptionConfig(
            speech_model       = "universal-2",
            speaker_labels     = True,
            language_detection = True,
            redact_pii         = True,
            redact_pii_policies = [
                aai.PIIRedactionPolicy.email_address,
                aai.PIIRedactionPolicy.phone_number,
            ],
            redact_pii_sub = aai.PIISubstitutionPolicy.hash,
        )

        transcriber = aai.Transcriber()
        transcript  = transcriber.transcribe(tmp.name, config=config)

        if transcript.status == aai.TranscriptStatus.error:
            raise Exception(f"AssemblyAI error: {transcript.error}")

        idioma_label = transcript.language_code or "es"

        prompt = f"""Eres un asistente experto en redactar actas institucionales.
A partir de la transcripción de reunión provista, extrae la información necesaria para completar un Acta Técnica.

Responde ÚNICAMENTE con un objeto JSON válido con exactamente estas 3 claves (sin texto adicional, sin markdown, sin bloques de código):

{{
  "aspectos": "Lista de los puntos del orden del día tratados, separados por comas.",
  "desarrollo": "Resumen breve en 3-5 oraciones de lo que sucedió en la reunión, en tercera persona.",
  "compromisos": "Lista de los acuerdos y compromisos asumidos. Si no hubo, escribe: No se registraron acuerdos formales."
}}

Redacta en el mismo idioma del audio (código: {idioma_label})."""

        lemur_result = transcript.lemur.task(
            prompt      = prompt,
            final_model = aai.LemurModel.claude3_5_sonnet,
        )

        raw = lemur_result.response.strip()
        # Limpiar bloques de código markdown si los hubiera
        if raw.startswith('```'):
            raw = raw.split('\n', 1)[1] if '\n' in raw else raw[3:]
            raw = raw.rsplit('```', 1)[0].strip()

        data = _json.loads(raw)
        return {
            "aspectos":     data.get("aspectos", "").strip(),
            "desarrollo":   data.get("desarrollo", "").strip(),
            "compromisos":  data.get("compromisos", "").strip(),
        }

    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass


def construir_txt(titulo: str, resultado: dict) -> str:
    """Arma el archivo TXT final con resumen + transcript."""
    dur = resultado["duracion_seg"]
    mins, segs = divmod(int(dur), 60)

    separador = "═" * 60

    txt = f"""TRANSCRIPCIÓN DE REUNIÓN
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
    return txt
