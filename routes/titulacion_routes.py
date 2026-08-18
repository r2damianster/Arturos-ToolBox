from flask import Blueprint, request, jsonify
from logic.titulacion_logic import (
    listar_modalidades_con_rubricas,
    crear_evaluacion,
    actualizar_modalidad,
    obtener_evaluacion,
    guardar_archivo,
)

titulacion_bp = Blueprint('titulacion', __name__)


@titulacion_bp.route('/util/titulacion/modalidades', methods=['GET'])
def titulacion_modalidades():
    """Catálogo de modalidades + rúbricas disponibles (paso 2 del wizard)."""
    try:
        return jsonify(listar_modalidades_con_rubricas())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@titulacion_bp.route('/util/titulacion/evaluacion', methods=['POST'])
def titulacion_crear_evaluacion():
    """Paso 1: crea la evaluación con los datos del memo."""
    try:
        datos = request.get_json(silent=True) or request.form
        evaluacion_id = crear_evaluacion(datos)
        return jsonify({"evaluacion_id": evaluacion_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@titulacion_bp.route('/util/titulacion/evaluacion/<int:evaluacion_id>', methods=['GET'])
def titulacion_obtener_evaluacion(evaluacion_id):
    try:
        evaluacion = obtener_evaluacion(evaluacion_id)
        if not evaluacion:
            return jsonify({"error": "Evaluación no encontrada"}), 404
        return jsonify(evaluacion)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@titulacion_bp.route('/util/titulacion/evaluacion/<int:evaluacion_id>/modalidad', methods=['POST'])
def titulacion_actualizar_modalidad(evaluacion_id):
    """Paso 2: fija modalidad + rúbrica (subtipo si aplica)."""
    try:
        datos = request.get_json(silent=True) or request.form
        modalidad_id = datos.get('modalidad_id')
        rubrica_id = datos.get('rubrica_id')
        if not modalidad_id or not rubrica_id:
            return jsonify({"error": "modalidad_id y rubrica_id son requeridos"}), 400
        actualizar_modalidad(evaluacion_id, modalidad_id, rubrica_id)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@titulacion_bp.route('/util/titulacion/evaluacion/<int:evaluacion_id>/archivo', methods=['POST'])
def titulacion_subir_archivo(evaluacion_id):
    """Paso 3: sube el PDF del memo o el trabajo del estudiante (.pdf/.docx)."""
    try:
        tipo = request.form.get('tipo', '')
        archivo = request.files.get('archivo')
        if not archivo or not archivo.filename:
            return jsonify({"error": "No se recibió ningún archivo."}), 400
        ruta = guardar_archivo(evaluacion_id, archivo, tipo)
        return jsonify({"ok": True, "ruta": ruta})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
