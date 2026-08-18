"""
Lógica del wizard de Evaluación de Pares Lectores (Titulación).
Fase 2: pasos 1-3 (datos del memo, modalidad/subtipo, subida de archivos), sin IA.
"""
import os
import datetime
from werkzeug.utils import secure_filename

from logic.titulacion_db import (
    get_conn,
    get_modalidades,
    get_rubricas_por_modalidad,
    get_rubrica,
    COMPONENTES_INFORME,
)

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
