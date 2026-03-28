import os
import io
from docxtpl import DocxTemplate
from datetime import timedelta

def generar_documento_pat06(datos):
    base_path = os.path.dirname(os.path.abspath(__file__))
    plantilla_path = os.path.join(base_path, "..", "..", "resources", "PAT-03-G-001-F-006.docx")
    
    fecha_carta_dt = datos["fecha_final"] + timedelta(days=1)
    meses = {1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
             7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"}
    
    contexto = {
        "FechaCarta": f"{fecha_carta_dt.day} de {meses[fecha_carta_dt.month]} del {fecha_carta_dt.year}",
        "Responsable": datos["responsable"], "MAESTRIA": datos["MAESTRIA"],
        "Oficio": datos["oficio"], "NOMBRE": datos["nombre"], "Articulo": datos["articulo"],
        "TutorFirma": "Dr. Rodríguez Zambrano Arturo Damián, PhD"
    }

    try:
        doc = DocxTemplate(plantilla_path)
        doc.render(contexto)
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer
    except Exception as e:
        print(f"❌ Error PAT 06: {e}")
        return None