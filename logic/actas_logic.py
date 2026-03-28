import os
import io
from datetime import datetime
from docx import Document
from groq import Groq

# API key desde variable de entorno (nunca hardcodeada)
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')

class ActaTecnicaLogic:
    def __init__(self):
        self.model_id = "llama-3.3-70b-versatile"
        try:
            self.client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
        except Exception as e:
            print(f"Error crítico de inicialización: {e}")
            self.client = None

    def generar_texto_ia(self, tipo, notas_usuario):
        if not notas_usuario or len(notas_usuario.strip()) < 2:
            return "No se registraron detalles adicionales para esta sección."

        if not self.client:
            return f"[IA no configurada] {notas_usuario}"

        if tipo == "aspectos":
            seccion_desc = "Puntos del orden del día"
            instruccion = (
                "TAREA: Organiza los puntos del orden del día.\n"
                "REGLAS: No expandas el texto innecesariamente. Solo corrige ortografía y formaliza levemente el vocabulario.\n"
                "FORMATO: Presenta cada punto precedido por una viñeta (•). No redactes párrafos largos."
            )
            max_tokens = 200
            temperature = 0.2

        elif tipo == "compromisos":
            seccion_desc = "Decisiones y compromisos finales"
            instruccion = (
                "TAREA: Redacta los acuerdos y compromisos institucionales.\n"
                "REGLAS: Sé directo y breve. Mantén la esencia de la nota original sin añadir relleno.\n"
                "FORMATO: Presenta cada compromiso precedido por una viñeta (•). Corrige coherencia y ortografía."
            )
            max_tokens = 200
            temperature = 0.2

        else:  # desarrollo
            seccion_desc = "Desarrollo y deliberaciones de la reunión"
            instruccion = (
                "TAREA: Convierte las notas en un relato académico fluido y profesional.\n"
                "REGLAS: Aquí SÍ puedes expandirte. Conecta los puntos del orden del día con conectores lógicos.\n"
                "FORMATO: Redacta en párrafos narrativos. Usa tono solemne (ej: 'asimismo', 'se procedió a')."
            )
            max_tokens = 600
            temperature = 0.5

        prompt = (
            f"Actúa como un Secretario Académico universitario de alto nivel.\n\n"
            f"SECCIÓN: {seccion_desc}.\n"
            f"{instruccion}\n\n"
            f"NOTAS DEL USUARIO:\n{notas_usuario}"
        )

        try:
            completion = self.client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": "Eres un redactor experto que diferencia entre listas breves y desarrollo narrativo."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            respuesta = completion.choices[0].message.content
            return respuesta.strip().replace('**', '').replace('*', '•')
        except Exception as e:
            return f"Error en la generación de texto: {str(e)}. Notas: {notas_usuario}"

    def formatear_fecha(self, fecha_str):
        try:
            dt = datetime.strptime(fecha_str, '%Y-%m-%d')
            meses = ["enero","febrero","marzo","abril","mayo","junio",
                     "julio","agosto","septiembre","octubre","noviembre","diciembre"]
            return f"{dt.day} de {meses[dt.month - 1]} de {dt.year}"
        except:
            return fecha_str

    def crear_docx(self, form_data):
        convocante_raw = form_data.get('convocante', '')
        partes_conv = convocante_raw.split(',')
        nombre_conv = partes_conv[0] if len(partes_conv) > 0 else "Director de Carrera"
        cargo_conv  = partes_conv[1] if len(partes_conv) > 1 else ""

        titulos   = form_data.getlist('p_titulo[]')
        nombres   = form_data.getlist('p_nombre[]')
        apellidos = form_data.getlist('p_apellido[]')
        lista_p   = [f"{t} {n} {a}".strip() for t, n, a in zip(titulos, nombres, apellidos) if n]

        asp = self.generar_texto_ia("aspectos",    form_data.get('notas_aspectos', ''))
        des = self.generar_texto_ia("desarrollo",  form_data.get('notas_reunion', ''))
        com = self.generar_texto_ia("compromisos", form_data.get('notas_compromisos', ''))

        fecha_larga = self.formatear_fecha(form_data.get('fecha_reunion', ''))

        logic_dir     = os.path.dirname(os.path.abspath(__file__))
        root_dir      = os.path.dirname(logic_dir)
        template_path = os.path.join(root_dir, 'resources', 'Acta_Tecnica.docx')

        doc = Document(template_path)

        reemplazos = {
            "{{numero_acta}}":        form_data.get('num_acta', 'S/N'),
            "{{fecha_larga}}":        fecha_larga,
            "{{lugar}}":              form_data.get('lugar_reunion', 'Instalaciones Institucionales'),
            "{{hora_inicio}}":        form_data.get('hora_inicio', '--:--'),
            "{{hora_fin}}":           form_data.get('hora_fin', '--:--'),
            "{{convocante_nombre}}":  nombre_conv.strip(),
            "{{convocante_cargo}}":   cargo_conv.strip(),
            "{{tabla_participantes}}": "\n".join(lista_p),
            "{{aspectos_ia}}":        asp,
            "{{desarrollo_ia}}":      des,
            "{{compromisos_ia}}":     com
        }

        for p in doc.paragraphs:
            for k, v in reemplazos.items():
                if k in p.text:
                    p.text = p.text.replace(k, str(v))

        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        for k, v in reemplazos.items():
                            if k in paragraph.text:
                                paragraph.text = paragraph.text.replace(k, str(v))

        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer
