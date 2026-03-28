from flask import Blueprint, request, send_file
from logic.actas_logic import ActaTecnicaLogic

actas_bp = Blueprint('actas', __name__)
logic_actas = ActaTecnicaLogic()

@actas_bp.route('/util/acta_tecnica', methods=['POST'])
def generar_acta_tecnica():
    try:
        buffer = logic_actas.crear_docx(request.form)
        num = request.form.get('num_acta', '000').replace('/', '-')
        return send_file(
            buffer,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True,
            download_name=f"Acta_{num}.docx"
        )
    except Exception as e:
        return f"Error al generar el acta: {str(e)}", 500
