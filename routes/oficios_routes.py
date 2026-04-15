from flask import Blueprint, request, send_file, jsonify
from logic.oficios_logic import OficioLogic

oficios_bp = Blueprint('oficios', __name__)


@oficios_bp.route('/util/oficio_generar', methods=['POST'])
def oficio_generar():
    """Genera un oficio en formato .docx."""
    try:
        datos = {
            'num_oficio':            request.form.get('num_oficio', ''),
            'fecha_emision':         request.form.get('fecha_emision', ''),
            'ciudad':                request.form.get('ciudad', 'Manta'),
            'destinatario_nombre':   request.form.get('destinatario_nombre', ''),
            'destinatario_cargo':    request.form.get('destinatario_cargo', ''),
            'destinatario_carrera':  request.form.get('destinatario_carrera', ''),
            'asunto':                request.form.get('asunto', ''),
            'cuerpo':                request.form.get('cuerpo', ''),
            'firmante_titulo':       request.form.get('firmante_titulo', ''),
            'firmante_nombre':       request.form.get('firmante_nombre', ''),
            'firmante_cargo':        request.form.get('firmante_cargo', ''),
            'iniciales':             request.form.get('iniciales', ''),
            'tono':                  request.form.get('tono', 'formal'),
        }

        logic = OficioLogic()
        buffer = logic.generar_docx(datos)
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"Oficio_{datos['num_oficio'] or 'borrador'}.docx"
        )
    except Exception as e:
        return f"Error: {str(e)}", 500


@oficios_bp.route('/util/oficio_carreras', methods=['GET'])
def oficio_carreras():
    """Obtiene lista de carreras/dependencias disponibles."""
    try:
        logic = OficioLogic()
        carreras = logic.obtener_carreras()
        return jsonify(carreras)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@oficios_bp.route('/util/oficio_destinatarios', methods=['GET'])
def oficio_destinatarios():
    """Obtiene destinatarios filtrados por carrera (opcional)."""
    try:
        carrera = request.args.get('carrera')
        logic = OficioLogic()
        destinatarios = logic.obtener_destinatarios(carrera=carrera)
        return jsonify(destinatarios)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
