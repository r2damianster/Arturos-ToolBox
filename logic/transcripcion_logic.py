import os
import io
import json as _json
from groq import Groq

# Configuración de Groq
_groq_client = Groq(api_key=os.environ.get('GROQ_API_KEY', '')) if os.environ.get('GROQ_API_KEY') else None
_GROQ_MODEL_LLM = "llama-3.3-70b-versatile"
_GROQ_MODEL_WHISPER = "whisper-large-v3"


def _guardar_audio_tmp(audio_file):
    """Guarda FileStorage en un archivo temporal. Retorna la ruta."""
    import tempfile
    suffix = os.path.splitext(audio_file.filename)[1] or '.mp3'
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    audio_file.save(tmp.name)
    tmp.close()
    return tmp.name


# ── Transcripción de reunión ─────────────────────────────────────────────────

def submit_transcripcion(audio_file, speaker_names: dict, titulo: str) -> str:
    """
    Transcribe audio con Groq Whisper (síncrono, retorna transcript directo).
    Retorna un ID fake para compatibilidad con el flujo actual.
    """
    import tempfile
    import uuid

    if not _groq_client:
        raise Exception("Groq API key no configurada.")

    tmp_path = _guardar_audio_tmp(audio_file)
    try:
        filename = os.path.basename(tmp_path)
        with open(tmp_path, "rb") as f:
            audio_bytes = f.read()

        transcript = _groq_client.audio.transcriptions.create(
            file=(filename, audio_bytes),
            model=_GROQ_MODEL_WHISPER,
            response_format="verbose_json",
            timestamp_granularities=["segment"],
        )

        transcript_id = str(uuid.uuid4())
        text = transcript.text or ""
        segments = transcript.segments or []

        # Guardar datos para luego
        ctx_path = os.path.join(tempfile.gettempdir(), f"txn_{transcript_id}.json")
        data = {
            "text": text,
            "segments": [{"start": s.get("start", 0), "text": s.get("text", "")} for s in segments],
            "language": transcript.language or "es",
            "duration": transcript.duration or 0,
            "speaker_names": speaker_names,
            "titulo": titulo,
        }
        with open(ctx_path, 'w', encoding='utf-8') as f:
            _json.dump(data, f)

        return transcript_id
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def get_transcript_status(transcript_id: str) -> dict:
    """
    Groq es síncrono: siempre retorna 'completed' o 'error'.
    """
    import tempfile
    ctx_path = os.path.join(tempfile.gettempdir(), f"txn_{transcript_id}.json")
    if os.path.exists(ctx_path):
        return {"status": "completed", "error": ""}
    return {"status": "error", "error": "Transcript no encontrado."}


def finalizar_transcripcion(transcript_id: str) -> dict:
    """
    Genera resumen con Groq LLM a partir de la transcripción de Groq Whisper.
    """
    import tempfile
    ctx_path = os.path.join(tempfile.gettempdir(), f"txn_{transcript_id}.json")

    if not os.path.exists(ctx_path):
        raise Exception("Datos de transcripción no encontrados.")

    with open(ctx_path, encoding='utf-8') as f:
        data = _json.load(f)

    try:
        os.unlink(ctx_path)
    except OSError:
        pass

    text = data.get("text", "")
    segments = data.get("segments", [])
    idioma_label = data.get("language", "es")
    duracion = data.get("duration", 0)
    speaker_names = data.get("speaker_names", {})
    titulo = data.get("titulo", "")

    if not text:
        raise Exception("Transcripción vacía.")

    word_count = len(text.split())

    # ── Formatear transcript con timestamps ──────────────────────────────────
    lineas = []
    for seg in segments:
        start_ms = seg.get("start", 0)
        s = int(start_ms)
        mins, secs = divmod(s, 60)
        lineas.append(f"[{mins:02d}:{secs:02d}] {seg['text']}")
    transcript_formateado = "\n".join(lineas) if lineas else text

    # ── Resumen con Groq LLM ─────────────────────────────────────────────────
    target_words = max(250, int(word_count * 0.15))

    resumen = ""
    if _groq_client and text:
        try:
            prompt = f"""Eres un secretario académico experto en redactar actas y resúmenes de reuniones.
Analiza la siguiente transcripción y genera un resumen estructurado en el idioma del audio (código: {idioma_label}).
No se detectaron hablantes individuales. Usa 'Habla X' o 'Participante X' si se pueden diferenciar.
El resumen debe tener aproximadamente {target_words} palabras (mínimo 250).

Usa EXACTAMENTE esta estructura:

PUNTOS TRATADOS
(Lista numerada de los temas principales discutidos)

DESARROLLO DE LA REUNIÓN
(Narrativo en tercera persona. Menciona quién dijo qué si es posible identificar participantes.)

ACUERDOS Y COMPROMISOS
(Lista de decisiones tomadas. Si no hay, escribe: "No se registraron acuerdos formales.")

No agregues texto fuera de estas tres secciones.

TRANSCRIPCIÓN:
{text[:8000]}"""

            resp = _groq_client.chat.completions.create(
                model=_GROQ_MODEL_LLM,
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
        "duracion_seg": duracion,
        "word_count": word_count,
        "titulo": titulo,
    }


# ── Acta técnica ─────────────────────────────────────────────────────────────

def submit_audio_acta(audio_file) -> str:
    """
    Transcribe audio de acta con Groq Whisper (síncrono).
    """
    import tempfile
    import uuid

    if not _groq_client:
        raise Exception("Groq API key no configurada.")

    tmp_path = _guardar_audio_tmp(audio_file)
    try:
        # Groq necesita filename + contenido como tuple
        filename = os.path.basename(tmp_path)
        with open(tmp_path, "rb") as f:
            audio_bytes = f.read()

        transcript = _groq_client.audio.transcriptions.create(
            file=(filename, audio_bytes),
            model=_GROQ_MODEL_WHISPER,
            response_format="verbose_json",
        )

        transcript_id = str(uuid.uuid4())
        text = transcript.text or ""
        idioma = transcript.language or "es"

        ctx_path = os.path.join(tempfile.gettempdir(), f"txn_{transcript_id}.json")
        with open(ctx_path, 'w', encoding='utf-8') as f:
            _json.dump({"text": text, "language": idioma}, f)

        return transcript_id
    except Exception as e:
        raise Exception(f"Error al transcribir con Groq: {str(e)}")
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def finalizar_acta(transcript_id: str) -> dict:
    """
    Usa Groq LLM para extraer las notas del Acta Técnica.
    """
    import tempfile
    ctx_path = os.path.join(tempfile.gettempdir(), f"txn_{transcript_id}.json")

    if not os.path.exists(ctx_path):
        raise Exception("Datos de transcripción no encontrados.")

    with open(ctx_path, encoding='utf-8') as f:
        data = _json.load(f)

    texto = data.get("text", "")
    idioma_label = data.get("language", "es")

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
            model=_GROQ_MODEL_LLM,
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
        "TRANSCRIPCIÓN DE REUNIÓN",
        "=" * 60,
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
