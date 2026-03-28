import os
import io
from docxtpl import DocxTemplate

def generar_documento_pat03(datos):
    base_path = os.path.dirname(os.path.abspath(__file__))
    plantilla_path = os.path.join(base_path, "..", "..", "resources", "PAT-03-G-001-F-003.docx")

    contexto = {
        "articulo": datos["articulo"],
        "nombre": datos["nombre"],
        "MAESTRIA": datos["MAESTRIA"]
    }
    for i in range(9):
        contexto[f"t{i+1}"] = datos["temas"][i]

    try:
        doc = DocxTemplate(plantilla_path)
        doc.render(contexto)
        
        # CAMBIO: Guardar en buffer de memoria
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer
    except Exception as e:
        print(f"❌ Error en PAT 03: {e}")
        return None