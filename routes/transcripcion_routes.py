import io
from flask import Blueprint, request, send_file, jsonify
from logic.transcripcion_logic import transcribir_y_resumir, construir_txt

transcripcion_bp = Blueprint('transcripcion', __name__)

@transcripcion_bp.route('/util/transcribir', methods=['POST'])
def transcribir():
    try:
        audio_file = request.files.get('audio_file')
        if not audio_file or not audio_file.filename:
            return jsonify({"error": "No se recibió ningún archivo de audio."}), 400

        titulo = request.form.get('titulo', '').strip()

        # Construir dict de hablantes {A: 'Arturo', B: 'German', ...}
        speaker_names = {}
        for letra in 'ABCDEFGH':
            nombre = request.form.get(f'speaker_{letra}', '').strip()
            if nombre:
                speaker_names[letra] = nombre

        resultado = transcribir_y_resumir(audio_file, speaker_names)
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
