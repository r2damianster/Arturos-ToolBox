import os
import io
from docxtpl import DocxTemplate
from datetime import timedelta

def generar_documento_pat05(datos):
    base_path = os.path.dirname(os.path.abspath(__file__))
    plantilla_path = os.path.join(base_path, "..", "..", "resources", "PAT-03-G-001-F-005.docx")

    fechas = [(datos["fecha_final"] - timedelta(weeks=i)).strftime("%d/%m/%Y") for i in range(8, -1, -1)]
    try:
        h, m = map(int, datos["hora"].split(':'))
        hora_fin = f"{h+2:02d}:{m:02d}"
    except:
        hora_fin = "18:00"

    contexto = {
        "MAESTRIA": datos["MAESTRIA"], "Articulo": datos["articulo"], "NOMBRE": datos["nombre"],
        "FECHA": datos["fecha_final"].strftime("%d/%m/%Y"), "FechaInicio": fechas[0],
        "FechaDesignacion": datos["fecha_designacion"], "HORA": datos["hora"],
        "HoraFin": hora_fin, "Responsable": datos["responsable"]
    }
    for i in range(9):
        contexto[f"n{i+1}"] = i + 1
        contexto[f"f{i+1}"] = fechas[i]
        contexto[f"t{i+1}"] = datos["temas"][i]

    try:
        doc = DocxTemplate(plantilla_path)
        doc.render(contexto)
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer
    except Exception as e:
        print(f"❌ Error PAT 05: {e}")
        return None