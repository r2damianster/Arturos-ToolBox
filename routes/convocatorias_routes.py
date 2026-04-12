from flask import Blueprint, request, send_file
from logic.convocatorias import ConvocatoriaLogic

convocatorias_bp = Blueprint('convocatorias', __name__)

@convocatorias_bp.route('/util/convocatoria_estudiante', methods=['POST'])
def convocatoria_estudiante():
    try:
        cursos_str = ", ".join(request.form.getlist('cursos'))
        datos = {
            'num_convocatoria':          request.form.get('num_convocatoria'),
            'periodo':                   request.form.get('periodo'),
            'siglas_convocante':         "PINE",
            'ciudad':                    request.form.get('ciudad'),
            'fecha_larga':               request.form.get('fecha_larga'),
            'asunto':                    request.form.get('asunto'),
            'curso':                     cursos_str,
            'descripcion_convocatoria':  request.form.get('descripcion_convocatoria'),
            'fecha_reunion':             request.form.get('fecha_reunion'),
            'hora_reunion':              request.form.get('hora_reunion'),
            'lugar_reunion':             request.form.get('lugar_reunion'),
            'convocante_titulo':         request.form.get('convocante_titulo'),
            'convocante_nombre':         request.form.get('convocante_nombre'),
            'convocante_cargo':          request.form.get('convocante_cargo'),
            'iniciales_elaborador':      request.form.get('iniciales_elaborador')
        }
        logic = ConvocatoriaLogic()
        buffer = logic.generar_docx("estudiante", datos, excel_files=request.files.getlist('excel_files'))
        return send_file(buffer, as_attachment=True, download_name="Convocatoria_Estudiantes.docx")
    except Exception as e:
        return f"Error: {str(e)}", 500

@convocatorias_bp.route('/util/convocatoria_docente', methods=['POST'])
def convocatoria_docente():
    try:
        import json
        modo = request.form.get('modo_docentes', 'carrera')
        docentes_json = request.form.get('docentes_json', '')

        datos = {
            'num_convocatoria':         request.form.get('num_convocatoria'),
            'periodo':                  request.form.get('periodo'),
            'siglas_convocante':        "PINE",
            'ciudad':                   request.form.get('ciudad'),
            'fecha_larga':              request.form.get('fecha_larga'),
            'asunto':                   request.form.get('asunto'),
            'descripcion_convocatoria': request.form.get('descripcion_convocatoria'),
            'fecha_reunion':            request.form.get('fecha_reunion'),
            'hora_reunion':             request.form.get('hora_reunion'),
            'lugar_reunion':            request.form.get('lugar_reunion'),
            'convocante_titulo':        request.form.get('convocante_titulo'),
            'convocante_nombre':        request.form.get('convocante_nombre'),
            'convocante_cargo':         request.form.get('convocante_cargo'),
            'iniciales_elaborador':     request.form.get('iniciales_elaborador')
        }

        # Si es modo manual, pasar los docentes
        docentes_manuales = None
        if modo == 'manual' and docentes_json:
            docentes_manuales = json.loads(docentes_json)

        logic = ConvocatoriaLogic()
        buffer = logic.generar_docx("docente", datos, docentes_manuales=docentes_manuales)
        return send_file(buffer, as_attachment=True, download_name="Convocatoria_Docentes.docx")
    except Exception as e:
        return f"Error: {str(e)}", 500
