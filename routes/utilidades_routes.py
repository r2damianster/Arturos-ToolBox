import os
import io
import base64
from flask import Blueprint, request, send_file, jsonify

from logic.utilidades import (
    csv_a_bib,
    generar_qr,
    generar_pptx,
    unir_imagenes_a_pdf,
    unir_imagenes_a_jpg,
    aplanar_archivos,
    generar_excels,
    crear_estructura_carpetas,
    convertir_a_pdf,
    reducir_imagenes,
    analizar_pretest_posttest,
)

utilidades_bp = Blueprint("utilidades", __name__)

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "..", "template.pptx")


@utilidades_bp.route("/util/csv-a-bib", methods=["POST"])
def util_csv_a_bib():
    archivo = request.files.get("csv_file")
    if not archivo:
        return "No se recibió archivo CSV.", 400
    try:
        bib_bytes = csv_a_bib(archivo.read())
        return send_file(io.BytesIO(bib_bytes), as_attachment=True,
                         download_name="referencias.bib", mimetype="text/plain")
    except Exception as e:
        return f"Error: {e}", 500


@utilidades_bp.route("/util/qr", methods=["POST"])
def util_qr():
    texto = request.form.get("texto", "").strip()
    if not texto:
        return "Ingresa un texto o URL.", 400
    try:
        png_bytes = generar_qr(texto)
        b64 = base64.b64encode(png_bytes).decode("utf-8")
        return jsonify({"imagen": b64})
    except Exception as e:
        return f"Error: {e}", 500


@utilidades_bp.route("/util/slides", methods=["POST"])
def util_slides():
    contenido = request.form.get("contenido", "")
    if not contenido.strip():
        return "El contenido está vacío.", 400
    try:
        pptx_bytes = generar_pptx(contenido.splitlines(), template_path=TEMPLATE_PATH)
        return send_file(io.BytesIO(pptx_bytes), as_attachment=True,
                         download_name="presentacion.pptx",
                         mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation")
    except Exception as e:
        return f"Error: {e}", 500


@utilidades_bp.route("/util/unir-imagenes", methods=["POST"])
def util_unir_imagenes():
    archivos = request.files.getlist("imagenes")
    if not archivos or archivos[0].filename == "":
        return "No se recibieron imágenes.", 400
    try:
        pdf_bytes = unir_imagenes_a_pdf(archivos)
        return send_file(io.BytesIO(pdf_bytes), as_attachment=True,
                         download_name="imagenes_unidas.pdf", mimetype="application/pdf")
    except Exception as e:
        return f"Error: {e}", 500


@utilidades_bp.route("/util/unir-imagenes-jpg", methods=["POST"])
def util_unir_imagenes_jpg():
    archivos = request.files.getlist("imagenes")
    if not archivos or archivos[0].filename == "":
        return "No se recibieron imágenes.", 400
    orientacion = request.form.get("orientacion", "vertical")
    try:
        jpg_bytes = unir_imagenes_a_jpg(archivos, orientacion=orientacion)
        return send_file(io.BytesIO(jpg_bytes), as_attachment=True,
                         download_name="imagenes_unidas.jpg", mimetype="image/jpeg")
    except Exception as e:
        return f"Error: {e}", 500


@utilidades_bp.route("/util/copiar-archivos", methods=["POST"])
def util_copiar_archivos():
    archivos = request.files.getlist("archivos")
    if not archivos or archivos[0].filename == "":
        return "No se recibieron archivos.", 400
    try:
        zip_bytes = aplanar_archivos(archivos)
        return send_file(io.BytesIO(zip_bytes), as_attachment=True,
                         download_name="archivos_extraidos.zip", mimetype="application/zip")
    except Exception as e:
        return f"Error: {e}", 500


@utilidades_bp.route("/util/crear-archivos", methods=["POST"])
def util_crear_archivos():
    tipo = request.form.get("tipo", "1")
    try:
        cantidad = max(1, min(int(request.form.get("cantidad", 1)), 50))
    except ValueError:
        return "Cantidad inválida.", 400
    try:
        zip_bytes = generar_excels(tipo, cantidad)
        return send_file(io.BytesIO(zip_bytes), as_attachment=True,
                         download_name="archivos_estadistica.zip", mimetype="application/zip")
    except Exception as e:
        return f"Error: {e}", 500


@utilidades_bp.route("/util/crear-carpetas", methods=["POST"])
def util_crear_carpetas():
    lista = request.form.get("nombres", "")
    nombres = [n.strip() for n in lista.splitlines() if n.strip()]
    if not nombres:
        return "No se ingresaron nombres de carpetas.", 400
    try:
        zip_bytes = crear_estructura_carpetas(nombres)
        return send_file(io.BytesIO(zip_bytes), as_attachment=True,
                         download_name="carpetas.zip", mimetype="application/zip")
    except Exception as e:
        return f"Error: {e}", 500


@utilidades_bp.route("/util/convertir-pdf", methods=["POST"])
def util_convertir_pdf():
    archivos = request.files.getlist("archivos")
    if not archivos or archivos[0].filename == "":
        return "No se recibieron archivos.", 400
    try:
        zip_bytes = convertir_a_pdf(archivos)
        return send_file(io.BytesIO(zip_bytes), as_attachment=True,
                         download_name="archivos_pdf.zip", mimetype="application/zip")
    except Exception as e:
        return f"Error: {e}", 500


@utilidades_bp.route("/util/reducir-imagenes", methods=["POST"])
def util_reducir_imagenes():
    archivos = request.files.getlist("imagenes")
    if not archivos or archivos[0].filename == "":
        return "No se recibieron imágenes.", 400
    try:
        max_px = int(request.form.get("max_px", 1280))
        calidad = int(request.form.get("calidad", 60))
        zip_bytes = reducir_imagenes(archivos, max_px=max_px, calidad=calidad)
        return send_file(io.BytesIO(zip_bytes), as_attachment=True,
                         download_name="imagenes_reducidas.zip", mimetype="application/zip")
    except Exception as e:
        return f"Error: {e}", 500


@utilidades_bp.route("/util/pretest", methods=["POST"])
def util_pretest():
    try:
        raw_pre  = request.form.get("pretest", "")
        raw_post = request.form.get("posttest", "")

        pretest  = [float(x.strip()) for x in raw_pre.split(",")  if x.strip()]
        posttest = [float(x.strip()) for x in raw_post.split(",") if x.strip()]

        if len(pretest) != len(posttest):
            return jsonify({"error": "Pretest y posttest deben tener la misma cantidad de valores."}), 400
        if len(pretest) < 5:
            return jsonify({"error": "Se necesitan al menos 5 pares de datos."}), 400

        resultados = analizar_pretest_posttest(pretest, posttest)
        return jsonify(resultados)

    except ValueError:
        return jsonify({"error": "Solo se aceptan números separados por comas."}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
