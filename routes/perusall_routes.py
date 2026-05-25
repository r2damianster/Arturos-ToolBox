from flask import Blueprint, request, jsonify, send_file, redirect
from logic.perusall_logic import procesar_archivos_perusall, obtener_archivo_resultado
import traceback

perusall_bp = Blueprint('perusall', __name__, url_prefix='/perusall')


@perusall_bp.route('/procesar', methods=['POST'])
def procesar():
    try:
        archivos = request.files.getlist('archivos_perusall')
        max_score_raw = request.form.get('max_score', '').strip()
        max_score = float(max_score_raw) if max_score_raw else None

        if not archivos or all(f.filename == '' for f in archivos):
            return jsonify({'error': 'No se subieron archivos'}), 400

        resultado = procesar_archivos_perusall(archivos, max_score=max_score)
        return jsonify(resultado)

    except Exception as e:
        return jsonify({'error': str(e), 'detalle': traceback.format_exc()}), 500


@perusall_bp.route('/descargar/<timestamp>/<filename>', methods=['GET'])
def descargar(timestamp, filename):
    try:
        path = obtener_archivo_resultado(timestamp, filename)
        return send_file(str(path), as_attachment=True)
    except FileNotFoundError:
        return 'Archivo no encontrado', 404
