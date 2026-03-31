import os
from datetime import datetime

# Importaciones de tus generadores existentes
try:
    from .PATS.Pat03 import generar_documento_pat03
    from .PATS.Pat04 import generar_documento_pat04
    from .PATS.Pat05 import generar_documento_pat05
    from .PATS.Pat06 import generar_documento_pat06
except ImportError:
    from .PATS.Pat03 import generar_documento_pat0
    from PATS.Pat04 import generar_documento_pat04
    from PATS.Pat05 import generar_documento_pat05
    from PATS.Pat06 import generar_documento_pat06

class PatMaestriaLogic:
    def __init__(self):
        # Centralizamos aquí toda la información para no repetirla en las rutas
        self.info_maestrias = {
            "1": {
                "nombre": "Maestría en Educación con Mención en Lingüística y Literatura, Cohorte IV – Matriz Manta.",
                "responsable": "Mg. Vargas Parraga Vanessa Monserrate"
            },
            "2": {
                "nombre": "Maestría en Educación con Mención en Innovaciones Pedagógicas, Cohorte IV – sede Matriz.",
                "responsable": "Mg. Delgado Mero Diana Maria"
            },
            "3": {
                "nombre": "Maestría en Pedagogía de los Idiomas Nacionales y Extranjeros Mención Inglés Matriz Manta, Cohorte III.",
                "responsable": "Mg. Bazurto Alcivar Gabriel José"
            }
        }

        self.temas_map = {
            "1": ["Socialización de los PAT (003- 006)", "Selección de revista a publicar", "Delimitación del tema", "Formulación del problema", "Diseño del protocolo", "Búsqueda sistemática", "Análisis y categorización", "Redacción del marco teórico", "Elaboración de discusión"],
            "2": ["Socialización PAT", "Problema de investigación", "Justificación y objetivos", "Marco referencial", "Variables de estudio", "Diseño metodológico", "Población y muestra", "Validación de instrumentos", "Planificación del análisis"],
            "3": ["Socialización PAT", "Planteamiento de hipótesis", "Antecedentes teóricos", "Plan de intervención", "Asignación de grupos", "Pilotaje de instrumentos", "Implementación y recolección", "Aplicación de Pre-test", "Análisis de validación"]
        }

    def preparar_datos_para_pats(self, form_data):
        """
        Toma el formulario de la web y devuelve el diccionario 'datos' 
        listo para ser usado por los generadores de Word.
        """
        m_op = form_data.get('maestria_opcion')
        metod_op = form_data.get('metodologia_opcion', '1')

        # Procesar fechas de forma segura
        try:
            f_sesion = datetime.strptime(form_data.get('fecha_sesion'), '%Y-%m-%d')
            f_desig_dt = datetime.strptime(form_data.get('fecha_designacion'), '%Y-%m-%d')
            f_desig_str = f_desig_dt.strftime('%d/%m/%Y')
        except (ValueError, TypeError):
            f_sesion = datetime.now()
            f_desig_str = datetime.now().strftime('%d/%m/%Y')

        # Retornamos el diccionario unificado
        return {
            "MAESTRIA": self.info_maestrias.get(m_op, {}).get("nombre", "Maestría no encontrada"),
            "responsable": self.info_maestrias.get(m_op, {}).get("responsable", "Responsable no encontrado"),
            "temas": self.temas_map.get(metod_op, self.temas_map["1"]),
            "nombre": form_data.get('nombre_maestrante', '').upper(),
            "articulo": form_data.get('titulo_articulo', ''),
            "oficio": form_data.get('num_oficio', ''),
            "fecha_final": f_sesion,
            "fecha_designacion": f_desig_str,
            "hora": form_data.get('hora_inicio', '16:00')
        }