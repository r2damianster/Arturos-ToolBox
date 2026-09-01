import { sql } from "./db";

export const COMPONENTES_INFORME = {
  formales: [
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
  fondo: [
    "Definición y formulación del contexto de Investigación",
    "Planteamientos de objetivos",
    "Diseño Metodológico",
    "Otros…",
  ],
};

export interface Modalidad {
  id: number;
  slug: string;
  nombre: string;
  requiere_subtipo: boolean;
}

export interface Rubrica {
  id: number;
  modalidad_id: number;
  slug: string;
  subtipo: string | null;
  schema_json: unknown;
}

export interface RubricaConSchema extends Rubrica {
  schema: RubricaSchema;
}

export interface CriterioSchema {
  no: number;
  texto: string;
  peso: number;
  descriptores?: Record<string, string>;
  niveles?: Record<string, string>;
  guia?: string;
}

export interface TablaSchema {
  nombre: string;
  escala: "peso_si_no" | "si_no" | "niveles_4" | "niveles_especial";
  header_rows: number;
  criterios: CriterioSchema[];
  niveles?: Array<{ pct: number; label: string }>;
}

export interface RubricaSchema {
  escala_total: number;
  tabla_total_idx: number;
  tablas: TablaSchema[];
}

export async function getModalidades(): Promise<Modalidad[]> {
  const rows = await sql`SELECT * FROM modalidades_titulacion ORDER BY id`;
  return rows as Modalidad[];
}

export async function getRubricasPorModalidad(modalidadId: number): Promise<RubricaConSchema[]> {
  const rows = await sql`SELECT * FROM rubricas WHERE modalidad_id = ${modalidadId} ORDER BY id`;
  return (rows as Rubrica[]).map((r) => ({ ...r, schema: r.schema_json as RubricaSchema }));
}

export async function getRubrica(rubricaId: number): Promise<RubricaConSchema | null> {
  const rows = await sql`SELECT * FROM rubricas WHERE id = ${rubricaId}`;
  const row = (rows as Rubrica[])[0];
  if (!row) return null;
  return { ...row, schema: row.schema_json as RubricaSchema };
}

/** Nombre de la plantilla .docx (en _templates/) para cada rúbrica, por slug. */
export const PLANTILLA_POR_RUBRICA: Record<string, string> = {
  tefl_completa: "Rubrica_TEFL.docx",
  articulo_no_publicado: "Rubrica_Articulo_NoPublicado.docx",
  articulo_publicado: "Rubrica_Articulo_Publicado.docx",
};
