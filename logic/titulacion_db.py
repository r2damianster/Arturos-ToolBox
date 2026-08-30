"""
Modelo de datos para el módulo de Evaluación de Pares Lectores (Titulación).
Ver Proyecto_Titulacion/PLAN-EVALUACION-PARES-LECTORES.md para el diseño completo.

Catálogo data-driven: cada rúbrica guarda su estructura (tablas, criterios,
pesos, escala) en `schema_json`. El wizard y el generador de documentos leen
ese JSON en vez de tener lógica por modalidad hardcodeada.
"""
import sqlite3
import os
import json

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "docentes.db")

# Componentes fijos del Informe de Criterios Observados (plantilla única,
# agnóstica de modalidad — igual en TEFL y Artículo).
COMPONENTES_INFORME = {
    "formales": [
        "Uso de normas APA",
        "Carátula",
        "Tamaño del papel",
        "Marginado",
        "Interlineado",
        "Tipo de letra",
        "Uso de negrilla",
        "Uso de citas",
        "Bibliografía",
        "Certificado del tutor/a",
        "Otros… (de acuerdo con la guía de la modalidad)",
    ],
    "fondo": [
        "Definición y formulación del contexto de Investigación",
        "Planteamientos de objetivos",
        "Diseño Metodológico",
        "Otros…",
    ],
}

NIVELES_4 = [
    {"pct": 0, "label": "No adecuado"},
    {"pct": 35, "label": "Poco adecuado"},
    {"pct": 70, "label": "Adecuado"},
    {"pct": 100, "label": "Totalmente adecuado"},
]


def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_titulacion_db():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS modalidades_titulacion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT NOT NULL UNIQUE,
            nombre TEXT NOT NULL,
            requiere_subtipo INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS rubricas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            modalidad_id INTEGER NOT NULL REFERENCES modalidades_titulacion(id),
            slug TEXT NOT NULL UNIQUE,
            subtipo TEXT,
            plantilla_docx TEXT NOT NULL,
            schema_json TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS evaluaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_memo TEXT,
            fecha_memo TEXT,
            fecha_limite TEXT,
            facultad TEXT,
            carrera TEXT,
            opcion_titulacion TEXT,
            titulo_trabajo TEXT,
            estudiante TEXT,
            tutor TEXT,
            evaluador_nombre TEXT,
            evaluador_correo TEXT,
            modalidad_id INTEGER REFERENCES modalidades_titulacion(id),
            rubrica_id INTEGER REFERENCES rubricas(id),
            archivo_memo TEXT,
            archivo_trabajo TEXT,
            estado TEXT NOT NULL DEFAULT 'borrador',
            creado_en TEXT NOT NULL DEFAULT (datetime('now')),
            actualizado_en TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS evaluacion_observaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evaluacion_id INTEGER NOT NULL REFERENCES evaluaciones(id),
            seccion TEXT NOT NULL CHECK (seccion IN ('formal', 'fondo')),
            componente TEXT NOT NULL,
            observacion TEXT NOT NULL DEFAULT ''
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS evaluacion_indicadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evaluacion_id INTEGER NOT NULL REFERENCES evaluaciones(id),
            tabla_idx INTEGER NOT NULL,
            criterio_idx INTEGER NOT NULL,
            criterio_texto TEXT NOT NULL,
            peso REAL NOT NULL DEFAULT 0,
            respuesta TEXT,
            calificacion REAL,
            comentario TEXT NOT NULL DEFAULT '',
            sugerencia_ia TEXT
        )
    """)
    conn.commit()

    _seed_catalogo(conn)
    conn.close()


def _seed_catalogo(conn):
    """Carga o actualiza modalidades + rúbricas iniciales (TEFL, Artículo publicado/no publicado)."""
    conn.execute(
        "INSERT OR IGNORE INTO modalidades_titulacion (slug, nombre, requiere_subtipo) VALUES (?, ?, ?)",
        ("tefl", "TEFL Application Process", 0)
    )
    tefl_id = conn.execute("SELECT id FROM modalidades_titulacion WHERE slug = 'tefl'").fetchone()[0]

    conn.execute(
        "INSERT OR IGNORE INTO modalidades_titulacion (slug, nombre, requiere_subtipo) VALUES (?, ?, ?)",
        ("articulo", "Artículo Científico / Capítulo de Libro", 1)
    )
    articulo_id = conn.execute("SELECT id FROM modalidades_titulacion WHERE slug = 'articulo'").fetchone()[0]

    conn.execute(
        """INSERT OR REPLACE INTO rubricas (modalidad_id, slug, subtipo, plantilla_docx, schema_json)
           VALUES (?, ?, ?, ?, ?)""",
        (tefl_id, "tefl_completa", None,
         "Rubrica Trabajo Escrito General Portafolio TEFL 2026 1.docx",
         json.dumps(_schema_tefl(), ensure_ascii=False))
    )
    conn.execute(
        """INSERT OR REPLACE INTO rubricas (modalidad_id, slug, subtipo, plantilla_docx, schema_json)
           VALUES (?, ?, ?, ?, ?)""",
        (articulo_id, "articulo_no_publicado", "no_publicado",
         "2.-ANEXO 2 RUBRICA PARA ARTICULO Y CAPITULOS DE LIBROS -NO- PUBLICADOS ESCRITO.docx",
         json.dumps(_schema_articulo_no_publicado(), ensure_ascii=False))
    )
    conn.execute(
        """INSERT OR REPLACE INTO rubricas (modalidad_id, slug, subtipo, plantilla_docx, schema_json)
           VALUES (?, ?, ?, ?, ?)""",
        (articulo_id, "articulo_published", "publicado",
         "3.-ANEXO 2 RUBRICA PARA ARTICULO Y CAPITULOS DE LIBROS PUBLICADOS ESCRITO .docx",
         json.dumps(_schema_articulo_publicado(), ensure_ascii=False))
    )
    conn.commit()


# ── Schemas (extraídos de los .docx originales con python-docx) ──────────

def _schema_tefl():
    return {
        "escala_total": 5,
        "tabla_total_idx": 0,
        "tablas": [
            {
                "nombre": "Rúbrica para el Trabajo Escrito",
                "escala": "peso_si_no",
                "header_rows": 1,
                "criterios": [
                    {"no": 1, "texto": "Presentación  Anillado carátula índice", "peso": 0.25},
                    {"no": 2, "texto": "Introducción", "peso": 0.50},
                    {"no": 3, "texto": "Módulo 1  Journal (bibliografía) FMU", "peso": 0.75},
                    {"no": 4, "texto": "Módulo 2  Journal (bibliografía) Speaking Lesson Plan (ECRIF) Anexos (Actividades para los estudiantes)", "peso": 0.75},
                    {"no": 5, "texto": "Módulo 3 Journal (bibliografía) Listening Lesson Plan (PDP) Anexos (Actividades para los estudiantes)", "peso": 0.75},
                    {"no": 6, "texto": "Módulo 4 Journal (bibliografía) Reading Lesson Plan (PDP) Anexos (Actividades para los estudiantes)", "peso": 0.75},
                    {"no": 7, "texto": "Módulo 5 Journal (bibliografía) Writing Lesson Plan (Preparation, Drafting, Revise, Editing, Extension) Anexos (Actividades para los estudiantes)", "peso": 0.75},
                    {"no": 8, "texto": "Conclusiones y Recomendaciones", "peso": 0.50},
                ],
            }
        ],
    }


def _schema_articulo_no_publicado():
    return {
        "escala_total": 10,
        "tabla_total_idx": 0,
        "tablas": [
            {
                "nombre": "Rúbrica — Artículo/Capítulo NO publicado",
                "escala": "niveles_4",
                "niveles": NIVELES_4,
                "criterios": [
                    {
                        "no": 1, "texto": "Título y resumen", "peso": 1.00,
                        "descriptores": {
                            "0": "El título no describe el proyecto de investigación/ intervención /implementación ejecutada.\n\nEl resumen no presenta los elementos objetivo, metodología, resultados y conclusiones.",
                            "35": "El título describe escasamente el proyecto de investigación/ intervención /implementación ejecutada.\n\nEl resumen presenta escasamente los elementos objetivo, metodología, resultados y conclusiones.",
                            "70": "El título describe de manera aceptable el proyecto de investigación/ intervención /implementación ejecutada.\n\nEl resumen presenta de manera aceptable los elementos objetivo, metodología, resultados y conclusiones.",
                            "100": "El título describe bien el proyecto de investigación/ intervención /implementación ejecutada.\n\nEl resumen presenta adecuadamente los elementos objetivo, metodología, resultados y conclusiones.",
                        },
                    },
                    {
                        "no": 2, "texto": "Introducción", "peso": 1.50,
                        "descriptores": {
                            "0": "La introducción no presenta la problemática estudiada, ni las motivaciones de los autores. Presenta otros diferentes a los generalmente utilizados.",
                            "35": "La introducción presenta escasamente la problemática estudiada, motivaciones de los autores, el contexto y otros elementos utilizados.",
                            "70": "La introducción presenta de manera aceptable la problemática estudiada, motivaciones de los autores, el contexto y otros elementos utilizados.",
                            "100": "La introducción presenta la problemática estudiada, motivaciones de los autores, el contexto y otros elementos generalmente utilizados.",
                        },
                    },
                    {
                        "no": 3, "texto": "Metodología", "peso": 2.50,
                        "descriptores": {
                            "0": "La metodología no es apropiada para el tipo de manuscrito. No se describen correctamente la muestra o participantes y los instrumentos utilizados no son pertinentes.",
                            "35": "La metodología es presentada de forma apropiada para el tipo de manuscrito. No se describen correctamente la muestra o participantes y los instrumentos utilizados.",
                            "70": "La metodología es apropiada para el tipo de manuscrito. Se observan debilidades al describir la muestra o participantes y los instrumentos utilizados.",
                            "100": "La metodología es clara y apropiada para el tipo de manuscrito. Se describen correctamente la muestra o participantes y los instrumentos utilizados.",
                        },
                    },
                    {
                        "no": 4, "texto": "Desarrollo (body)", "peso": 2.00,
                        "descriptores": {
                            "0": "La revisión literaria no es actualizada ni pertinente.\nNo ha sido redactada adecuadamente y presenta fallas en las citas bibliográficas.\nAplica errores de Norma APA 7 Edición.",
                            "35": "La revisión literaria es actualizada, pertinente, pero no ha sido redactada adecuadamente y presenta fallas en las citas bibliográficas.\nAplica errores de Norma APA 7 Edición.",
                            "70": "La revisión literaria es actualizada, pertinente, pero no ha sido redactada adecuadamente. Las citas son realizadas correctamente.\nAplica correctamente las normas APA 7 Edición.",
                            "100": "La revisión literaria es actualizada, pertinente y redactada adecuadamente. Las citas son realizadas correctamente.\nAplica correctamente las normas APA 7 Edición.",
                        },
                    },
                    {
                        "no": 5, "texto": "Discusión y conclusiones o reflexiones finales", "peso": 2.00,
                        "descriptores": {
                            "0": "La argumentación no se elabora de manera clara y no se hace contraste de los hallazgos con las teorías. No se añade información respeto a los hallazgos.\n\nLa conclusión o reflexiones finales no contrastan a los objetivos propuestos. No es contundente y no hace uso eficiente del texto.",
                            "35": "La argumentación se elabora de manera poco clara, pero si elabora contrastes de los hallazgos con las teorías. Se añade poca información respeto a los hallazgos.\nLa conclusión o reflexiones finales hacen poco contraste a los objetivos propuestos. Es poco contundente.",
                            "70": "La argumentación se elabora de manera clara, pero presenta escaso contrastes de los hallazgos con las teorías. Se añade poca información respeto a los hallazgos.\n\nLa conclusión o reflexiones finales contrastan escasamente a los objetivos propuestos. Es contundente.",
                            "100": "La argumentación se elabora de manera clara y con contrastes de los hallazgos con las teorías. Se añade información respeto a los hallazgos.\n\nLa conclusión o reflexiones finales contrastan a los objetivos propuestos. Es contundente y hace uso eficiente del texto.",
                        },
                    },
                    {
                        "no": 6, "texto": "Cohesión, coherencia y estilo", "peso": 1.00,
                        "descriptores": {
                            "0": "No apropiados para el tipo de manuscrito",
                            "35": "Débil para el tipo de manuscrito",
                            "70": "Aceptable para el tipo de manuscrito",
                            "100": "Muy apropiados para el tipo de manuscrito",
                        },
                    },
                ],
            },
        ],
    }


def _schema_articulo_publicado():
    return {
        "escala_total": 10,
        "tabla_total_idx": 0,
        "tablas": [
            {
                "nombre": "Rúbrica — Artículo/Capítulo publicado",
                "escala": "niveles_especial",
                "criterios": [
                    {
                        "no": 1, "texto": "Artículo científico o capítulo de libro publicado", "peso": 7,
                        "niveles": {"0": "N/A", "35": "N/A", "70": "N/A", "100": "Publicado"},
                        "guia": "La carta de aceptación para publicación de la revista científica o editorial puede ser usada para evidenciar el requisito para aplicar este procedimiento.",
                    },
                    {
                        "no": 2, "texto": "Evidencias del proceso de evaluación de los lectores pares ciegos o editores de la revista científica o editorial", "peso": 3,
                        "niveles": {"0": "N/A", "35": "N/A", "70": "1 lector par ciego", "100": "2 lectores pares ciegos"},
                        "guia": "Se acepta como evidencia los correos electrónicos indicando las mejoras solicitadas por editores o revistas científicas.",
                    },
                ],
            },
        ],
    }


# ── Acceso a catálogo ──────────────────────────────────────────────────

def get_modalidades():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM modalidades_titulacion ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_rubricas_por_modalidad(modalidad_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM rubricas WHERE modalidad_id = ? ORDER BY id", (modalidad_id,)
    ).fetchall()
    conn.close()
    resultado = []
    for r in rows:
        d = dict(r)
        d["schema"] = json.loads(d["schema_json"])
        resultado.append(d)
    return resultado


def get_rubrica(rubrica_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM rubricas WHERE id = ?", (rubrica_id,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["schema"] = json.loads(d["schema_json"])
    return d


# ── Alta de modalidades/rúbricas sin tocar código (ver scripts/titulacion_admin.py) ──

def upsert_modalidad(slug, nombre, requiere_subtipo=False):
    """Inserta o actualiza una modalidad por su slug. El wizard la lee automáticamente."""
    conn = get_conn()
    fila = conn.execute("SELECT id FROM modalidades_titulacion WHERE slug = ?", (slug,)).fetchone()
    if fila:
        conn.execute(
            "UPDATE modalidades_titulacion SET nombre = ?, requiere_subtipo = ? WHERE id = ?",
            (nombre, int(requiere_subtipo), fila["id"])
        )
        modalidad_id = fila["id"]
    else:
        cur = conn.execute(
            "INSERT INTO modalidades_titulacion (slug, nombre, requiere_subtipo) VALUES (?, ?, ?)",
            (slug, nombre, int(requiere_subtipo))
        )
        modalidad_id = cur.lastrowid
    conn.commit()
    conn.close()
    return modalidad_id


def upsert_rubrica(modalidad_id, slug, subtipo, plantilla_docx, schema):
    """Inserta o actualiza una rúbrica por su slug. schema es el dict (no JSON-string)."""
    conn = get_conn()
    schema_json = json.dumps(schema, ensure_ascii=False)
    fila = conn.execute("SELECT id FROM rubricas WHERE slug = ?", (slug,)).fetchone()
    if fila:
        conn.execute(
            "UPDATE rubricas SET modalidad_id = ?, subtipo = ?, plantilla_docx = ?, schema_json = ? WHERE id = ?",
            (modalidad_id, subtipo, plantilla_docx, schema_json, fila["id"])
        )
        rubrica_id = fila["id"]
    else:
        cur = conn.execute(
            "INSERT INTO rubricas (modalidad_id, slug, subtipo, plantilla_docx, schema_json) VALUES (?, ?, ?, ?, ?)",
            (modalidad_id, slug, subtipo, plantilla_docx, schema_json)
        )
        rubrica_id = cur.lastrowid
    conn.commit()
    conn.close()
    return rubrica_id
