import io
from flask import Blueprint, request, send_file, jsonify
from logic.transcripcion_logic import (
    submit_transcripcion,
    get_transcript_status,
    finalizar_transcripcion,
    construir_txt,
    submit_audio_acta,
    finalizar_acta,
)

transcripcion_bp = Blueprint('transcripcion', __name__)


# ── Transcripción de reunión ─────────────────────────────────────────────────

@transcripcion_bp.route('/util/transcribir/submit', methods=['POST'])
def transcribir_submit():
    """Recibe el audio, lo envía a AssemblyAI y retorna transcript_id inmediatamente."""
    try:
        audio_file = request.files.get('audio_file')
        if not audio_file or not audio_file.filename:
            return jsonify({"error": "No se recibió ningún archivo de audio."}), 400

        titulo = request.form.get('titulo', '').strip()
        speaker_names = {}
        for letra in 'ABCDEFGH':
            nombre = request.form.get(f'speaker_{letra}', '').strip()
            if nombre:
                speaker_names[letra] = nombre

        transcript_id = submit_transcripcion(audio_file, speaker_names, titulo)
        return jsonify({"transcript_id": transcript_id})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@transcripcion_bp.route('/util/transcribir/status/<transcript_id>', methods=['GET'])
def transcribir_status(transcript_id):
    """Consulta el estado del transcript en AssemblyAI."""
    try:
        return jsonify(get_transcript_status(transcript_id))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@transcripcion_bp.route('/util/transcribir/resultado/<transcript_id>', methods=['GET'])
def transcribir_resultado(transcript_id):
    """
    Cuando el transcript está completado, corre LeMUR y retorna el archivo TXT.
    Este endpoint debe llamarse solo una vez, cuando el status sea 'completed'.
    """
    try:
        resultado = finalizar_transcripcion(transcript_id)
        titulo = resultado.get("titulo", "")
        contenido = construir_txt(titulo, resultado)

        buffer = io.BytesIO(contenido.encode('utf-8'))
        buffer.seek(0)
        nombre_archivo = f"Transcripcion_{titulo.replace(' ', '_') or 'reunion'}.txt"

        return send_file(
            buffer,
            mimetype='text/plain; charset=utf-8',
            as_attachment=True,
            download_name=nombre_archivo
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Acta técnica ─────────────────────────────────────────────────────────────

@transcripcion_bp.route('/util/acta_extraer_audio/submit', methods=['POST'])
def acta_submit():
    """Recibe el audio del acta, lo envía a AssemblyAI y retorna transcript_id."""
    try:
        audio_file = request.files.get('audio_acta')
        if not audio_file or not audio_file.filename:
            return jsonify({"error": "No se recibió ningún archivo de audio."}), 400

        transcript_id = submit_audio_acta(audio_file)
        return jsonify({"transcript_id": transcript_id})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@transcripcion_bp.route('/util/acta_extraer_audio/status/<transcript_id>', methods=['GET'])
def acta_status(transcript_id):
    """Consulta el estado del transcript de acta."""
    try:
        return jsonify(get_transcript_status(transcript_id))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@transcripcion_bp.route('/util/acta_extraer_audio/resultado/<transcript_id>', methods=['GET'])
def acta_resultado(transcript_id):
    """Cuando el transcript está completado, corre LeMUR y retorna las notas JSON."""
    try:
        return jsonify(finalizar_acta(transcript_id))
    except Exception as e:
        return jsonify({"error": str(e)}), 500
