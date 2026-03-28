from flask import Blueprint, request, send_file
from logic.menor import ReportGeneratorLogic

reportes_bp = Blueprint('reportes', __name__)

@reportes_bp.route('/util/informe_notas', methods=['POST'])
def generate_report():
    try:
        parcial_id = request.form.get('parcial_seleccionado')
        excel_file = request.files.get('excel_file')

        datos = {
            "fecha":                            request.form.get('fecha'),
            "titulo_academico_destinatario":    request.form.get('titulo_academico_destinatario'),
            "nombres_apellidos_destinatario":   request.form.get('nombres_apellidos_destinatario'),
            "facultad_extension_destinatario":  request.form.get('facultad_extension_destinatario'),
            "titulo_academico_emisor":          request.form.get('titulo_academico_emisor'),
            "nombres_apellidos_emisor":         request.form.get('nombres_apellidos_emisor'),
            "titulo_academico_cc":              request.form.get('titulo_academico_cc'),
            "nombres_apellidos_cc":             request.form.get('nombres_apellidos_cc'),
            "asignatura":                       "ASIGNATURA"
        }

        logic = ReportGeneratorLogic()
        if excel_file and excel_file.filename:
            datos["asignatura"] = logic._extract_subject_from_filename(excel_file.filename)

        estudiantes, info_parcial = logic.process_excel_data(excel_file, parcial_id)
        buffer = logic.generate_report(datos, estudiantes, info_parcial)

        return send_file(buffer, as_attachment=True, download_name=f"Informe_Notas_P{parcial_id}.docx")
    except Exception as e:
        return f"Error: {str(e)}", 500
