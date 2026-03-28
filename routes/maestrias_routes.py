import io
import zipfile
from flask import Blueprint, request, send_file
from logic.PatsMaestria import PatMaestriaLogic
from logic.PATS.Pat03 import generar_documento_pat03
from logic.PATS.Pat04 import generar_documento_pat04
from logic.PATS.Pat05 import generar_documento_pat05
from logic.PATS.Pat06 import generar_documento_pat06

maestrias_bp = Blueprint('maestrias', __name__)
pats_helper  = PatMaestriaLogic()

@maestrias_bp.route('/util/generar_pat_zip', methods=['POST'])
def generar_pat_zip():
    try:
        datos = pats_helper.preparar_datos_para_pats(request.form)

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            documentos = [
                (generar_documento_pat03(datos), "PAT_003_Cronograma.docx"),
                (generar_documento_pat04(datos), "PAT_004_Oficio.docx"),
                (generar_documento_pat05(datos), "PAT_005_Asistencia.docx"),
                (generar_documento_pat06(datos), "PAT_006_Informe.docx"),
            ]
            for buff, name in documentos:
                if buff:
                    zip_file.writestr(name, buff.getvalue())

        zip_buffer.seek(0)
        nombre_descarga = f"PATS_{datos['nombre'].replace(' ', '_')[:15]}.zip"
        return send_file(zip_buffer, mimetype='application/zip',
                         as_attachment=True, download_name=nombre_descarga)
    except Exception as e:
        return f"Error en el servidor: {str(e)}", 500
