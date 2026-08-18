"""
Lógica del wizard de Evaluación de Pares Lectores (Titulación).
Fase 2: pasos 1-3 (datos del memo, modalidad/subtipo, subida de archivos), sin IA.
"""
import os
import io
import zipfile
import datetime
import re
from werkzeug.utils import secure_filename

from logic.titulacion_db import (
    get_conn,
    get_modalidades,
    get_rubricas_por_modalidad,
    get_rubrica,
    COMPONENTES_INFORME,
)
from logic.titulacion_docgen import generar_informe_docx, generar_rubrica_docx

EXTENSIONES_PERMITIDAS = {'.pdf', '.docx', '.doc'}
UPLOADS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "titulacion_uploads")


def _dias_habiles_desde(fecha_inicio, dias):
    """Suma días hábiles (lun-vie) a una fecha, saltando sábados y domingos."""
    fecha = fecha_inicio
    restantes = dias
    while restantes > 0:
        fecha += datetime.timedelta(days=1)
        if fecha.weekday() < 5:  # 0=lunes .. 4=viernes
            restantes -= 1
    return fecha


def calcular_fecha_limite(fecha_memo_str):
    """Plazo de 5 días hábiles desde la fecha del memo (política 6.1.bb Manual de Titulación)."""
    fecha_memo = datetime.datetime.strptime(fecha_memo_str, '%Y-%m-%d').date()
    fecha_limite = _dias_habiles_desde(fecha_memo, 5)
    return fecha_limite.isoformat()


def listar_modalidades_con_rubricas():
    """Modalidades + sus rúbricas (sin schema completo, solo lo necesario para el selector)."""
    modalidades = get_modalidades()
    for m in modalidades:
        rubricas = get_rubricas_por_modalidad(m['id'])
        m['rubricas'] = [
            {"id": r['id'], "slug": r['slug'], "subtipo": r['subtipo']}
            for r in rubricas
        ]
    return modalidades


def crear_evaluacion(datos):
    """Crea una evaluación en estado 'borrador' con los datos del paso 1 y 2 del wizard."""
    fecha_memo = datos.get('fecha_memo', '').strip()
    fecha_limite = calcular_fecha_limite(fecha_memo) if fecha_memo else None

    conn = get_conn()
    cur = conn.execute("""
        INSERT INTO evaluaciones (
            numero_memo, fecha_memo, fecha_limite, facultad, carrera,
            opcion_titulacion, titulo_trabajo, estudiante, tutor,
            evaluador_nombre, evaluador_correo, modalidad_id, rubrica_id, estado
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'borrador')
    """, (
        datos.get('numero_memo', ''),
        fecha_memo,
        fecha_limite,
        datos.get('facultad', ''),
        datos.get('carrera', ''),
        datos.get('opcion_titulacion', ''),
        datos.get('titulo_trabajo', ''),
        datos.get('estudiante', ''),
        datos.get('tutor', ''),
        datos.get('evaluador_nombre', ''),
        datos.get('evaluador_correo', ''),
        datos.get('modalidad_id') or None,
        datos.get('rubrica_id') or None,
    ))
    conn.commit()
    evaluacion_id = cur.lastrowid

    # Precarga fila de observaciones (tabla 2 del Informe) con los componentes fijos.
    for componente in COMPONENTES_INFORME['formales']:
        conn.execute(
            "INSERT INTO evaluacion_observaciones (evaluacion_id, seccion, componente) VALUES (?, 'formal', ?)",
            (evaluacion_id, componente)
        )
    for componente in COMPONENTES_INFORME['fondo']:
        conn.execute(
            "INSERT INTO evaluacion_observaciones (evaluacion_id, seccion, componente) VALUES (?, 'fondo', ?)",
            (evaluacion_id, componente)
        )
    conn.commit()
    conn.close()
    return evaluacion_id


def actualizar_modalidad(evaluacion_id, modalidad_id, rubrica_id):
    """Paso 2 del wizard: fija modalidad y rúbrica (según subtipo elegido si aplica)."""
    conn = get_conn()
    conn.execute(
        "UPDATE evaluaciones SET modalidad_id = ?, rubrica_id = ?, actualizado_en = datetime('now') WHERE id = ?",
        (modalidad_id, rubrica_id, evaluacion_id)
    )
    conn.commit()
    conn.close()


def obtener_evaluacion(evaluacion_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM evaluaciones WHERE id = ?", (evaluacion_id,)).fetchone()
    conn.close()
    if not row:
        return None
    evaluacion = dict(row)
    if evaluacion.get('rubrica_id'):
        evaluacion['rubrica'] = get_rubrica(evaluacion['rubrica_id'])
    return evaluacion


def guardar_archivo(evaluacion_id, file_storage, tipo):
    """Guarda el memo o el trabajo del estudiante (paso 3) en disco y registra la ruta.

    tipo: 'memo' | 'trabajo'
    """
    if tipo not in ('memo', 'trabajo'):
        raise ValueError("tipo debe ser 'memo' o 'trabajo'")

    nombre_original = file_storage.filename or ''
    extension = os.path.splitext(nombre_original)[1].lower()
    if extension not in EXTENSIONES_PERMITIDAS:
        raise ValueError(f"Extensión no permitida: {extension}. Use PDF o Word.")

    carpeta_evaluacion = os.path.join(UPLOADS_DIR, str(evaluacion_id))
    os.makedirs(carpeta_evaluacion, exist_ok=True)

    nombre_seguro = secure_filename(nombre_original) or f"{tipo}{extension}"
    ruta_relativa = os.path.join(str(evaluacion_id), f"{tipo}_{nombre_seguro}")
    ruta_absoluta = os.path.join(UPLOADS_DIR, ruta_relativa)
    file_storage.save(ruta_absoluta)

    columna = 'archivo_memo' if tipo == 'memo' else 'archivo_trabajo'
    conn = get_conn()
    conn.execute(
        f"UPDATE evaluaciones SET {columna} = ?, actualizado_en = datetime('now') WHERE id = ?",
        (ruta_relativa, evaluacion_id)
    )
    conn.commit()
    conn.close()
    return ruta_relativa


# ── Fase 3: rúbrica interactiva + observaciones ───────────────────────────

def obtener_detalle_evaluacion(evaluacion_id):
    """Evaluación + rúbrica (schema) + indicadores y observaciones ya guardados, para renderizar el paso 4."""
    evaluacion = obtener_evaluacion(evaluacion_id)
    if not evaluacion:
        return None

    conn = get_conn()
    indicadores = [dict(r) for r in conn.execute(
        "SELECT * FROM evaluacion_indicadores WHERE evaluacion_id = ? ORDER BY tabla_idx, criterio_idx",
        (evaluacion_id,)
    ).fetchall()]
    observaciones = [dict(r) for r in conn.execute(
        "SELECT * FROM evaluacion_observaciones WHERE evaluacion_id = ? ORDER BY id",
        (evaluacion_id,)
    ).fetchall()]
    conn.close()

    evaluacion['indicadores'] = indicadores
    evaluacion['observaciones'] = observaciones
    if evaluacion.get('rubrica'):
        evaluacion['puntaje_total'] = calcular_puntaje_total(evaluacion['rubrica']['schema'], indicadores)
    return evaluacion


def calcular_puntaje_total(schema, indicadores):
    """Suma las calificaciones de la tabla que representa el /10 (schema['tabla_total_idx'])."""
    tabla_total_idx = schema.get('tabla_total_idx', 0)
    total = 0.0
    for indicador in indicadores:
        if indicador.get('tabla_idx') != tabla_total_idx:
            continue
        if indicador.get('calificacion') is not None:
            total += float(indicador['calificacion'])
    return round(total, 2)


def guardar_indicadores(evaluacion_id, indicadores):
    """Reemplaza todos los indicadores de la evaluación (guardado explícito, no autosave por keystroke)."""
    conn = get_conn()
    conn.execute("DELETE FROM evaluacion_indicadores WHERE evaluacion_id = ?", (evaluacion_id,))
    for ind in indicadores:
        conn.execute("""
            INSERT INTO evaluacion_indicadores (
                evaluacion_id, tabla_idx, criterio_idx, criterio_texto, peso,
                respuesta, calificacion, comentario, sugerencia_ia
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            evaluacion_id,
            ind.get('tabla_idx'),
            ind.get('criterio_idx'),
            ind.get('criterio_texto', ''),
            ind.get('peso') or 0,
            ind.get('respuesta'),
            ind.get('calificacion'),
            ind.get('comentario', ''),
            ind.get('sugerencia_ia'),
        ))
    conn.commit()
    conn.close()


# ── Fase 4: generación de documentos ───────────────────────────────────────

def generar_documentos_zip(evaluacion_id):
    """Genera Informe + Rúbrica en .docx y los entrega en un .zip. Marca la evaluación como finalizada."""
    evaluacion = obtener_detalle_evaluacion(evaluacion_id)
    if not evaluacion:
        raise ValueError("Evaluación no encontrada")
    if not evaluacion.get('rubrica'):
        raise ValueError("Falta seleccionar la modalidad/rúbrica antes de generar los documentos.")

    informe_buffer = generar_informe_docx(evaluacion)
    rubrica_buffer = generar_rubrica_docx(evaluacion)

    slug_titulo = re.sub(r'[^A-Za-z0-9]+', '_', (evaluacion.get('titulo_trabajo') or 'evaluacion')).strip('_')[:40]

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"Informe_Criterios_Observados_{slug_titulo}.docx", informe_buffer.getvalue())
        zf.writestr(f"Rubrica_{slug_titulo}.docx", rubrica_buffer.getvalue())
    zip_buffer.seek(0)

    conn = get_conn()
    conn.execute(
        "UPDATE evaluaciones SET estado = 'finalizada', actualizado_en = datetime('now') WHERE id = ?",
        (evaluacion_id,)
    )
    conn.commit()
    conn.close()

    return zip_buffer, slug_titulo


def guardar_observaciones(evaluacion_id, observaciones):
    """Actualiza el texto de observación de cada componente (formal/fondo) ya precargado."""
    conn = get_conn()
    for obs in observaciones:
        obs_id = obs.get('id')
        if not obs_id:
            continue
        conn.execute(
            "UPDATE evaluacion_observaciones SET observacion = ? WHERE id = ? AND evaluacion_id = ?",
            (obs.get('observacion', ''), obs_id, evaluacion_id)
        )
    conn.commit()
    conn.close()
