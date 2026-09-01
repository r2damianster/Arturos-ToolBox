/**
 * Migración de Neon para el módulo de Pares Lectores.
 * Equivalente a logic/titulacion_db.py: init_titulacion_db() + _seed_catalogo().
 * Uso: npx tsx --env-file=.env.local scripts/migrate-neon.ts
 */
import { neon } from "@neondatabase/serverless";
import {
  schemaTefl,
  schemaArticuloNoPublicado,
  schemaArticuloPublicado,
} from "./rubricas-seed-data";

const sql = neon(process.env.DATABASE_URL!);

const DOCENTES_INICIALES: Array<[string, string, string, string, string, boolean]> = [
  ["Lic.", "María Basantes Robalino", "Mg.", "Docente", "Pedagogía de los Idiomas Nacionales y Extranjeros", false],
  ["Lic.", "Gabriel Bazurto Alcívar", "Mg.", "Docente", "Pedagogía de los Idiomas Nacionales y Extranjeros", false],
  ["Dr.", "Germán Carrera Moreno", "PhD.", "Director de carrera", "Pedagogía de los Idiomas Nacionales y Extranjeros", true],
  ["Lic.", "Verónica Chávez Zambrano", "Mg.", "Docente", "Pedagogía de los Idiomas Nacionales y Extranjeros", false],
  ["Lic.", "Jorge Corral Joniaux", "Mg.", "Docente", "Pedagogía de los Idiomas Nacionales y Extranjeros", false],
  ["Lic.", "Gonzalo Farfán Corrales", "Mg.", "Docente", "Pedagogía de los Idiomas Nacionales y Extranjeros", false],
  ["Lic.", "Laura Mena Sánchez", "Mg.", "Docente", "Pedagogía de los Idiomas Nacionales y Extranjeros", false],
  ["Dr.", "Arturo Rodríguez Zambrano", "PhD.", "Docente", "Pedagogía de los Idiomas Nacionales y Extranjeros", false],
  ["Dr.", "Jhonny Villafuerte Holguín", "PhD.", "Docente", "Pedagogía de los Idiomas Nacionales y Extranjeros", false],
  ["Lic.", "Cintya Zambrano Zambrano", "Mg.", "Docente", "Pedagogía de los Idiomas Nacionales y Extranjeros", false],
  ["Dr.", "Pedro Quijije Anchundia", "PhD.", "Decano", "Facultad de Educación y Turismo", false],
  ["Lic.", "Klever Alfredo Delgado Reyes", "Mg.", "Director", "Dirección de Investigación, Publicaciones y Servicio Bibliográficos - ULEAM", false],
  ["Dra.", "Jackeline Terranova Ruiz", "PhD.", "Vicerrectora Académica", "ULEAM", false],
];

async function main() {
  await sql`
    CREATE TABLE IF NOT EXISTS docentes (
      id SERIAL PRIMARY KEY,
      titulo_grado TEXT NOT NULL,
      nombre TEXT NOT NULL,
      post_grado TEXT NOT NULL,
      cargo TEXT NOT NULL,
      carrera TEXT NOT NULL DEFAULT 'Pedagogía de los Idiomas Nacionales y Extranjeros',
      es_director BOOLEAN NOT NULL DEFAULT false
    )
  `;

  const [{ count }] = await sql`SELECT COUNT(*)::int AS count FROM docentes`;
  if (count === 0) {
    for (const [titulo_grado, nombre, post_grado, cargo, carrera, es_director] of DOCENTES_INICIALES) {
      await sql`
        INSERT INTO docentes (titulo_grado, nombre, post_grado, cargo, carrera, es_director)
        VALUES (${titulo_grado}, ${nombre}, ${post_grado}, ${cargo}, ${carrera}, ${es_director})
      `;
    }
  }

  await sql`
    CREATE TABLE IF NOT EXISTS modalidades_titulacion (
      id SERIAL PRIMARY KEY,
      slug TEXT NOT NULL UNIQUE,
      nombre TEXT NOT NULL,
      requiere_subtipo BOOLEAN NOT NULL DEFAULT false
    )
  `;

  await sql`
    CREATE TABLE IF NOT EXISTS rubricas (
      id SERIAL PRIMARY KEY,
      modalidad_id INTEGER NOT NULL REFERENCES modalidades_titulacion(id),
      slug TEXT NOT NULL UNIQUE,
      subtipo TEXT,
      schema_json JSONB NOT NULL
    )
  `;

  await sql`
    CREATE TABLE IF NOT EXISTS evaluaciones (
      id SERIAL PRIMARY KEY,
      numero_memo TEXT,
      fecha_memo DATE,
      fecha_limite DATE,
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
      texto_memo TEXT,
      texto_trabajo TEXT,
      estado TEXT NOT NULL DEFAULT 'borrador',
      creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
      actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now()
    )
  `;

  await sql`
    CREATE TABLE IF NOT EXISTS evaluacion_observaciones (
      id SERIAL PRIMARY KEY,
      evaluacion_id INTEGER NOT NULL REFERENCES evaluaciones(id) ON DELETE CASCADE,
      seccion TEXT NOT NULL CHECK (seccion IN ('formal', 'fondo')),
      componente TEXT NOT NULL,
      observacion TEXT NOT NULL DEFAULT ''
    )
  `;

  await sql`
    CREATE TABLE IF NOT EXISTS evaluacion_indicadores (
      id SERIAL PRIMARY KEY,
      evaluacion_id INTEGER NOT NULL REFERENCES evaluaciones(id) ON DELETE CASCADE,
      tabla_idx INTEGER NOT NULL,
      criterio_idx INTEGER NOT NULL,
      criterio_texto TEXT NOT NULL,
      peso REAL NOT NULL DEFAULT 0,
      respuesta TEXT,
      calificacion REAL,
      comentario TEXT NOT NULL DEFAULT '',
      sugerencia_ia TEXT
    )
  `;

  console.log("Tablas listas. Sembrando catálogo...");

  const [tefl] = await sql`
    INSERT INTO modalidades_titulacion (slug, nombre, requiere_subtipo)
    VALUES ('tefl', 'TEFL Application Process', false)
    ON CONFLICT (slug) DO UPDATE SET nombre = EXCLUDED.nombre
    RETURNING id
  `;
  const [articulo] = await sql`
    INSERT INTO modalidades_titulacion (slug, nombre, requiere_subtipo)
    VALUES ('articulo', 'Artículo Científico / Capítulo de Libro', true)
    ON CONFLICT (slug) DO UPDATE SET nombre = EXCLUDED.nombre
    RETURNING id
  `;

  await sql`
    INSERT INTO rubricas (modalidad_id, slug, subtipo, schema_json)
    VALUES (${tefl.id}, 'tefl_completa', NULL, ${JSON.stringify(schemaTefl())}::jsonb)
    ON CONFLICT (slug) DO UPDATE SET schema_json = EXCLUDED.schema_json
  `;
  await sql`
    INSERT INTO rubricas (modalidad_id, slug, subtipo, schema_json)
    VALUES (${articulo.id}, 'articulo_no_publicado', 'no_publicado', ${JSON.stringify(schemaArticuloNoPublicado())}::jsonb)
    ON CONFLICT (slug) DO UPDATE SET schema_json = EXCLUDED.schema_json
  `;
  await sql`
    INSERT INTO rubricas (modalidad_id, slug, subtipo, schema_json)
    VALUES (${articulo.id}, 'articulo_publicado', 'publicado', ${JSON.stringify(schemaArticuloPublicado())}::jsonb)
    ON CONFLICT (slug) DO UPDATE SET schema_json = EXCLUDED.schema_json
  `;

  console.log("Migración + seed completados.");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
