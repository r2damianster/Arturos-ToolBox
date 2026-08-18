"""
Generador de los 2 documentos de salida del par lector (Titulación):
1) Informe de Criterios Observados (plantilla única, agnóstica de modalidad)
2) Rúbrica de calificación (data-driven desde schema_json — sirve para TEFL y Artículo)

Se generan desde cero con python-docx: los .docx originales en Proyecto_Titulacion/
tienen celdas fusionadas de forma inconsistente (verificado con python-docx) y no
tienen membrete/logo que preservar, así que replicar su estructura a mano es más
confiable que editar el archivo original celda por celda.
"""
import io
import datetime
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH


def _fecha_larga(fecha=None):
    fecha = fecha or datetime.date.today()
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
             "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    return f"{fecha.day} de {meses[fecha.month - 1]} de {fecha.year}"


def _indicadores_por_clave(indicadores):
    return {(i['tabla_idx'], i['criterio_idx']): i for i in indicadores}


# ── Documento 1: Informe de Criterios Observados ──────────────────────────

def generar_informe_docx(evaluacion):
    doc = Document()
    style = doc.styles['Normal']
    style.font.size = Pt(10.5)

    doc.add_paragraph(f"MEMORANDUM No. {evaluacion.get('numero_memo') or '—'}").runs[0].bold = True
    doc.add_paragraph("PARA: Miembros de Comisión Académica")
    doc.add_paragraph("ASUNTO: Criterios observados en el trabajo de integración curricular y/o examen complexivo")
    doc.add_paragraph(f"FECHA: Manta, {_fecha_larga()}")
    doc.add_paragraph()

    tutor = evaluacion.get('tutor') or '__________________'
    doc.add_paragraph(
        "En cumplimiento a lo que dispone el Reglamento de Régimen Académico Interno sobre el "
        "proceso de titulación, una vez que se ha revisado el trabajo de integración curricular "
        f"y/o examen complexivo para el cual fue designado/a en dirigir {tutor}, de acuerdo al "
        "siguiente detalle:"
    )

    tabla1 = doc.add_table(rows=2, cols=4)
    tabla1.style = 'Table Grid'
    encabezados1 = ["Facultad y/o Extensión", "Carrera", "Opción de Titulación", "Título"]
    valores1 = [
        evaluacion.get('facultad') or '',
        evaluacion.get('carrera') or '',
        evaluacion.get('opcion_titulacion') or '',
        evaluacion.get('titulo_trabajo') or '',
    ]
    for celda, texto in zip(tabla1.rows[0].cells, encabezados1):
        celda.paragraphs[0].add_run(texto).bold = True
    for celda, texto in zip(tabla1.rows[1].cells, valores1):
        celda.text = texto

    doc.add_paragraph()
    opcion = evaluacion.get('opcion_titulacion') or 'Trabajo de Integración Curricular o Examen Complexivo'
    doc.add_paragraph(
        "Luego de haber realizado el análisis en cada uno de los componentes que forman parte del "
        "trabajo escrito y en concordancia con una de las competencias otorgadas al tribunal de "
        "titulación —que consiste en que, luego de la revisión del trabajo, éste deberá emitir un "
        "informe con las observaciones de forma y contenido sobre el documento presentado, el mismo "
        "que deberá ser conocido por el tutor/a quien direccionará al estudiante para que realice las "
        f"correcciones necesarias— se detallan los criterios del {opcion} que fueron observados:"
    )

    observaciones = evaluacion.get('observaciones') or []
    formales = [o for o in observaciones if o['seccion'] == 'formal']
    fondo = [o for o in observaciones if o['seccion'] == 'fondo']

    tabla2 = doc.add_table(rows=1, cols=2)
    tabla2.style = 'Table Grid'
    tabla2.rows[0].cells[0].paragraphs[0].add_run("Componentes").bold = True
    tabla2.rows[0].cells[1].paragraphs[0].add_run("Observaciones").bold = True

    def _agregar_seccion(titulo, filas):
        fila = tabla2.add_row()
        fila.cells[0].paragraphs[0].add_run(titulo).bold = True
        for obs in filas:
            fila = tabla2.add_row()
            fila.cells[0].text = obs['componente']
            fila.cells[1].text = obs.get('observacion') or ''

    _agregar_seccion("Aspectos formales:", formales)
    _agregar_seccion("Aspectos de fondo:", fondo)

    doc.add_paragraph()
    doc.add_paragraph("Particular que se informa para los fines consiguientes.")
    doc.add_paragraph()
    doc.add_paragraph("Atentamente,")
    doc.add_paragraph()
    doc.add_paragraph()
    doc.add_paragraph(evaluacion.get('evaluador_nombre') or '__________________')
    doc.add_paragraph("Miembro del Tribunal Calificador")
    doc.add_paragraph(f"Correo Electrónico Institucional: {evaluacion.get('evaluador_correo') or ''}")

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


# ── Documento 2: Rúbrica (data-driven desde schema_json) ──────────────────

def generar_rubrica_docx(evaluacion):
    rubrica = evaluacion.get('rubrica')
    if not rubrica:
        raise ValueError("La evaluación no tiene una rúbrica asignada.")
    schema = rubrica['schema']
    indicadores = _indicadores_por_clave(evaluacion.get('indicadores') or [])
    puntaje_total = evaluacion.get('puntaje_total', 0)

    doc = Document()
    style = doc.styles['Normal']
    style.font.size = Pt(10.5)

    titulo = doc.add_paragraph(f"Rúbrica de Evaluación — {evaluacion.get('titulo_trabajo') or ''}")
    titulo.runs[0].bold = True
    titulo.runs[0].font.size = Pt(13)

    encabezado = doc.add_paragraph()
    encabezado.add_run(f"Estudiante: {evaluacion.get('estudiante') or ''}\t\t").bold = False
    encabezado.add_run(f"Evaluador: {evaluacion.get('evaluador_nombre') or ''}")
    doc.add_paragraph(f"Fecha: {_fecha_larga()}")
    total_p = doc.add_paragraph()
    total_p.add_run(f"Calificación Total: {puntaje_total} / {schema.get('escala_total', 10)}").bold = True

    for tabla_idx, tabla in enumerate(schema['tablas']):
        doc.add_paragraph()
        encabezado_tabla = doc.add_paragraph(tabla['nombre'])
        encabezado_tabla.runs[0].bold = True

        escala = tabla['escala']
        con_peso = escala in ('peso_si_no', 'niveles_4', 'niveles_especial')
        columnas = ["Criterio"]
        if con_peso:
            columnas.append("Peso")
        if escala in ('peso_si_no', 'si_no'):
            columnas += ["YES", "NO"]
        else:
            columnas += ["Nivel asignado", "Calificación"]
        columnas.append("Comentario")

        docx_tabla = doc.add_table(rows=1, cols=len(columnas))
        docx_tabla.style = 'Table Grid'
        for celda, texto in zip(docx_tabla.rows[0].cells, columnas):
            celda.paragraphs[0].add_run(texto).bold = True

        for criterio_idx, criterio in enumerate(tabla['criterios']):
            indicador = indicadores.get((tabla_idx, criterio_idx), {})
            fila = docx_tabla.add_row()
            col = 0

            texto_criterio = criterio['texto']
            if criterio.get('etapa'):
                texto_criterio = f"[{criterio['etapa']}] {texto_criterio}"
            fila.cells[col].text = texto_criterio
            col += 1

            if con_peso:
                fila.cells[col].text = str(criterio.get('peso', ''))
                col += 1

            if escala in ('peso_si_no', 'si_no'):
                respuesta = indicador.get('respuesta')
                fila.cells[col].text = 'X' if respuesta == 'YES' else ''
                fila.cells[col + 1].text = 'X' if respuesta == 'NO' else ''
                col += 2
            else:
                respuesta = indicador.get('respuesta')
                etiqueta_nivel = ''
                if escala == 'niveles_4' and respuesta is not None:
                    nivel = next((n for n in tabla.get('niveles', []) if str(n['pct']) == str(respuesta)), None)
                    etiqueta_nivel = f"{nivel['label']} ({nivel['pct']}%)" if nivel else respuesta
                elif escala == 'niveles_especial' and respuesta is not None:
                    etiqueta_nivel = criterio.get('niveles', {}).get(str(respuesta), respuesta)
                fila.cells[col].text = etiqueta_nivel
                col += 1
                calificacion = indicador.get('calificacion')
                fila.cells[col].text = str(calificacion) if calificacion is not None else ''
                col += 1

            fila.cells[col].text = indicador.get('comentario') or ''

        if tabla_idx != schema.get('tabla_total_idx', 0):
            subtotal = sum(
                float(i['calificacion']) for (t_idx, _), i in indicadores.items()
                if t_idx == tabla_idx and i.get('calificacion') is not None
            )
            p = doc.add_paragraph(f"Subtotal: {round(subtotal, 2)}")
            p.runs[0].bold = True
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    doc.add_paragraph()
    doc.add_paragraph("_" * 40)
    doc.add_paragraph("Firma del evaluador/a")

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer
