import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "docentes.db")

DOCENTES_INICIALES = [
    ("Lic.", "María Basantes Robalino", "Mg.", "Docente", "Pedagogía de los Idiomas Nacionales y Extranjeros", False),
    ("Lic.", "Gabriel Bazurto Alcívar", "Mg.", "Docente", "Pedagogía de los Idiomas Nacionales y Extranjeros", False),
    ("Dr.", "Germán Carrera Moreno", "PhD.", "Director de carrera", "Pedagogía de los Idiomas Nacionales y Extranjeros", True),
    ("Lic.", "Verónica Chávez Zambrano", "Mg.", "Docente", "Pedagogía de los Idiomas Nacionales y Extranjeros", False),
    ("Lic.", "Jorge Corral Joniaux", "Mg.", "Docente", "Pedagogía de los Idiomas Nacionales y Extranjeros", False),
    ("Lic.", "Gonzalo Farfán Corrales", "Mg.", "Docente", "Pedagogía de los Idiomas Nacionales y Extranjeros", False),
    ("Lic.", "Laura Mena Sánchez", "Mg.", "Docente", "Pedagogía de los Idiomas Nacionales y Extranjeros", False),
    ("Dr.", "Arturo Rodríguez Zambrano", "PhD.", "Docente", "Pedagogía de los Idiomas Nacionales y Extranjeros", False),
    ("Dr.", "Jhonny Villafuerte Holguín", "PhD.", "Docente", "Pedagogía de los Idiomas Nacionales y Extranjeros", False),
    ("Lic.", "Cintya Zambrano Zambrano", "Mg.", "Docente", "Pedagogía de los Idiomas Nacionales y Extranjeros", False),
]


def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS docentes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo_grado TEXT NOT NULL,
            nombre TEXT NOT NULL,
            post_grado TEXT NOT NULL,
            cargo TEXT NOT NULL,
            carrera TEXT NOT NULL DEFAULT 'Pedagogía de los Idiomas Nacionales y Extranjeros',
            es_director INTEGER NOT NULL DEFAULT 0
        )
    """)
    # Migration: add carrera column if it doesn't exist (for existing databases)
    try:
        conn.execute("ALTER TABLE docentes ADD COLUMN carrera TEXT NOT NULL DEFAULT 'Pedagogía de los Idiomas Nacionales y Extranjeros'")
        conn.commit()
    except Exception:
        pass  # Column already exists
    # Seed only if table is empty
    count = conn.execute("SELECT COUNT(*) FROM docentes").fetchone()[0]
    if count == 0:
        conn.executemany(
            "INSERT INTO docentes (titulo_grado, nombre, post_grado, cargo, carrera, es_director) VALUES (?, ?, ?, ?, ?, ?)",
            DOCENTES_INICIALES
        )
        conn.commit()
    conn.close()


def get_all_docentes():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM docentes ORDER BY es_director DESC, nombre ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_docente(docente_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM docentes WHERE id = ?", (docente_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def add_docente(titulo_grado, nombre, post_grado, cargo, carrera="Pedagogía de los Idiomas Nacionales y Extranjeros", es_director=False):
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO docentes (titulo_grado, nombre, post_grado, cargo, carrera, es_director) VALUES (?, ?, ?, ?, ?, ?)",
        (titulo_grado, nombre, post_grado, cargo, carrera, int(es_director))
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def update_docente(docente_id, titulo_grado, nombre, post_grado, cargo, carrera="Pedagogía de los Idiomas Nacionales y Extranjeros", es_director=False):
    conn = get_conn()
    conn.execute(
        "UPDATE docentes SET titulo_grado=?, nombre=?, post_grado=?, cargo=?, carrera=?, es_director=? WHERE id=?",
        (titulo_grado, nombre, post_grado, cargo, carrera, int(es_director), docente_id)
    )
    conn.commit()
    conn.close()


def delete_docente(docente_id):
    conn = get_conn()
    conn.execute("DELETE FROM docentes WHERE id = ?", (docente_id,))
    conn.commit()
    conn.close()
